"""
src.metodo_v2.orchestrator_v2 - Orquestrador do Fluxo de Cálculo V2

Nova arquitetura: calcula comissões baseadas em faixas de faturamento.

DOIS MODOS DE CÁLCULO:
======================
1. MODO HIERARQUIA (padrão):
   - Regras por combinação hierárquica (linha + grupo + subgrupo + tipo + fabricante)
   - Taxa determinada por item (faturamento do item → faixa → taxa)
   
2. MODO CENTRO DE CUSTO:
   - Regras por Centro Custo-pedido (ex: "2.5.031 - Hidrologia")
   - Taxa determinada pelo faturamento TOTAL mensal do colaborador no CC
   - Depois aplica essa taxa a cada item individualmente

Fluxo V2 Simplificado (SEM ATRIBUICOES_V2):
===========================================
1. Carregar REGRAS_COMISSOES_V2.xlsx:
   - COLABORADORES_V2: nome + cargo + fator_split
   - CARGOS_V2: cargo + tipo (OPERACIONAL/GESTAO)
   - REGRAS_COMISSAO_V2: faixas de comissão por colaborador e hierarquia
   - REGRAS_COMISSAO_CC_V2: faixas de comissão por colaborador e centro de custo

2. Carregar Análise Comercial (faturamento)

3. Para CADA ITEM da Análise Comercial:
   - OPERACIONAL (Consultor Interno/Externo):
     * Nome vem da Análise Comercial
     * DEVE ter regra em REGRAS_COMISSAO_V2 para essa hierarquia
   - GESTÃO (Gerente Linha, Coordenador, etc.):
     * Encontrado via REGRAS_COMISSAO_V2 (quem tem regra para essa hierarquia)
     * Aplica fator_split (vem de COLABORADORES_V2)
   - Para cada colaborador:
     * Calcular comissão = faturamento × taxa × fator_split

4. Agregar resultados por colaborador

Diferenças do Método Padrão:
- SEM Fator de Correção (FC)
- Comissão direta = faturamento × taxa_faixa × fator_split
- Hierarquia com 5 níveis (inclui fabricante)
- SEM aba ATRIBUICOES_V2 (simplificação)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Literal
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from .config_loader_v2 import ConfigLoaderV2
from .comissao_calculator_v2 import ComissaoCalculatorV2
from .cc_calculator_v2 import CCCalculatorV2
from .models_v2 import ColaboradorV2, ResultadoColaboradorV2, RegraComissao
from .atribuicao_service_v2 import (
    AtribuicaoServiceV2, 
    ColaboradorAtribuido, 
    ResultadoAtribuicao,
    COL_AC_LINHA, COL_AC_GRUPO, COL_AC_SUBGRUPO, 
    COL_AC_TIPO_MERCADORIA, COL_AC_FABRICANTE, COL_AC_FATURAMENTO
)
from .recebimento_v2 import RecebimentoOrchestratorV2


logger = logging.getLogger(__name__)


# Constantes para modo de cálculo
MODO_HIERARQUIA = "hierarquia"
MODO_CENTRO_CUSTO = "centro_custo"


# =============================================================================
# DATACLASS PARA RESULTADO DETALHADO POR ITEM
# =============================================================================
@dataclass
class ResultadoItemAC:
    """Resultado do cálculo para um item da Análise Comercial."""
    
    # Identificador do processo comercial
    processo: str = ""
    
    # Hierarquia do item
    linha: str = ""
    grupo: str = ""
    subgrupo: str = ""
    tipo_mercadoria: str = ""
    fabricante: str = ""
    
    # Valor do item
    faturamento: float = 0.0
    
    # Colaboradores atribuídos e suas comissões
    comissoes_por_colaborador: Dict[str, float] = field(default_factory=dict)
    
    # Informações de regra/faixa aplicada por colaborador
    # Formato: {"nome_colab": {"regra": {...}, "faixa": {...}, "taxa_aplicada": float}}
    detalhes_calculo_por_colaborador: Dict[str, Dict] = field(default_factory=dict)
    
    # Erros/avisos de atribuição
    erros_atribuicao: List[str] = field(default_factory=list)
    avisos_atribuicao: List[str] = field(default_factory=list)


@dataclass
class ResultadoColaboradorAggregado:
    """Resultado agregado por colaborador."""
    
    nome: str
    cargo: str
    faturamento_total: float = 0.0
    comissao_total: float = 0.0
    qtd_itens: int = 0
    detalhes: List[Dict] = field(default_factory=list)


# =============================================================================
# ORQUESTRADOR PRINCIPAL
# =============================================================================
class OrchestratorV2:
    """Orquestrador principal da Metodologia V2.
    
    Exemplo de uso:
        orchestrator = OrchestratorV2()
        df_resumo, df_detalhes = orchestrator.executar(mes=1, ano=2026)
    """

    DEFAULT_CONFIG_PATH = "config/REGRAS_COMISSOES_V2.xlsx"
    DEFAULT_COMERCIAL_PATH = "dados_entrada/Analise_Comercial_Completa.xlsx"

    def __init__(
        self,
        config_path: Optional[str] = None,
        comercial_path: Optional[str] = None,
    ):
        """Inicializa o orquestrador.
        
        Args:
            config_path: Caminho para REGRAS_COMISSOES_V2.xlsx
            comercial_path: Caminho para Análise Comercial
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.comercial_path = comercial_path or self.DEFAULT_COMERCIAL_PATH
        
        # Componentes
        self._config_loader: Optional[ConfigLoaderV2] = None
        self._atribuicao_service: Optional[AtribuicaoServiceV2] = None
        self._comissao_calculator: Optional[ComissaoCalculatorV2] = None
        self._cc_calculator: Optional[CCCalculatorV2] = None
        
        # Cache de dados carregados
        self._colaboradores: Dict[str, ColaboradorV2] = {}
        self._df_regras: Optional[pd.DataFrame] = None
        self._df_colaboradores: Optional[pd.DataFrame] = None
        self._df_cargos: Optional[pd.DataFrame] = None
        self._df_comercial: Optional[pd.DataFrame] = None
        
        # Resultados
        self._resultados_por_item: List[ResultadoItemAC] = []
        self._resultados_por_colaborador: Dict[str, ResultadoColaboradorAggregado] = {}
        self._erros_globais: List[str] = []
        self._modo_calculo: str = MODO_HIERARQUIA

    def executar(
        self, 
        mes: int, 
        ano: int,
        modo_calculo: str = MODO_HIERARQUIA
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Executa o cálculo completo da Metodologia V2.
        
        Args:
            mes: Mês de referência (1-12).
            ano: Ano de referência.
            modo_calculo: "hierarquia" (padrão) ou "centro_custo".
            
        Returns:
            Tupla (df_resumo, df_detalhes)
            - df_resumo: DataFrame com resultado por colaborador
            - df_detalhes: DataFrame com detalhamento por item
        """
        self._modo_calculo = modo_calculo
        mes_ano = f"{ano}-{mes:02d}"
        logger.info(f"=== Iniciando cálculo V2 para {mes_ano} (modo: {modo_calculo}) ===")
        
        start_time = datetime.now()
        self._erros_globais = []
        
        # 1. Carregar configurações (colaboradores + regras)
        self._carregar_configuracoes()
        
        # 2. Carregar dados para serviço de atribuição e criar serviço
        self._carregar_dados_atribuicao()
        
        # 3. Carregar dados comerciais (filtrados por mês/ano e status)
        self._carregar_dados_comerciais(mes, ano)
        
        # BRANCH: Executar cálculo conforme o modo selecionado
        if modo_calculo == MODO_CENTRO_CUSTO:
            return self._executar_modo_centro_custo(mes_ano, start_time)
        else:
            return self._executar_modo_hierarquia(mes_ano, start_time)

    def _executar_modo_hierarquia(
        self, 
        mes_ano: str, 
        start_time: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Executa cálculo no modo Hierarquia (padrão)."""
        # 4. Inicializar calculador
        self._comissao_calculator = ComissaoCalculatorV2()
        
        # 5. Processar cada item da Análise Comercial
        self._processar_itens_ac(mes_ano)
        
        # 6. Agregar resultados por colaborador
        self._agregar_por_colaborador()
        
        # 7. Gerar DataFrames de saída
        df_resumo = self._gerar_df_resumo()
        df_detalhes = self._gerar_df_detalhes()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        n_colabs = len(self._resultados_por_colaborador)
        n_itens = len(self._resultados_por_item)
        logger.info(
            f"=== Cálculo V2 (Hierarquia) concluído em {elapsed:.2f}s === "
            f"({n_itens} itens processados, {n_colabs} colaboradores com comissão)"
        )
        
        if self._erros_globais:
            logger.warning(f"Erros encontrados: {len(self._erros_globais)}")
            for erro in self._erros_globais[:5]:
                logger.warning(f"  - {erro}")
        
        return df_resumo, df_detalhes

    def _executar_modo_centro_custo(
        self, 
        mes_ano: str, 
        start_time: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Executa cálculo no modo Centro de Custo."""
        # Inicializar calculador de Centro de Custo
        self._cc_calculator = CCCalculatorV2(
            colaboradores=self._colaboradores,
            df_cargos=self._df_cargos,
            df_colaboradores=self._df_colaboradores,
        )
        
        # Executar cálculo
        df_resumo, df_detalhes = self._cc_calculator.calcular(self._df_comercial)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        n_colabs = len(df_resumo) if not df_resumo.empty else 0
        n_itens = len(df_detalhes) if not df_detalhes.empty else 0
        logger.info(
            f"=== Cálculo V2 (Centro de Custo) concluído em {elapsed:.2f}s === "
            f"({n_itens} linhas detalhes, {n_colabs} linhas resumo)"
        )
        
        # Coletar erros do calculador CC
        if self._cc_calculator.erros:
            self._erros_globais.extend(self._cc_calculator.erros)
            logger.warning(f"Erros encontrados: {len(self._cc_calculator.erros)}")
            for erro in self._cc_calculator.erros[:5]:
                logger.warning(f"  - {erro}")
        
        return df_resumo, df_detalhes

    def _carregar_configuracoes(self) -> None:
        """Carrega configurações do REGRAS_COMISSOES_V2.xlsx."""
        logger.info(f"Carregando configurações de {self.config_path}")
        
        self._config_loader = ConfigLoaderV2(self.config_path)
        self._colaboradores = self._config_loader.load()
        
        logger.info(f"Carregados {len(self._colaboradores)} colaboradores configurados")

    def _carregar_dados_atribuicao(self) -> None:
        """Carrega dados necessários para o serviço de atribuição.
        
        Carrega REGRAS_COMISSAO_V2, COLABORADORES_V2 e CARGOS_V2 para
        criar o AtribuicaoServiceV2.
        """
        logger.info("Carregando dados para serviço de atribuição...")
        
        try:
            self._df_regras = pd.read_excel(
                self.config_path,
                sheet_name="REGRAS_COMISSAO_V2"
            )
            self._df_colaboradores = pd.read_excel(
                self.config_path,
                sheet_name="COLABORADORES_V2"
            )
            self._df_cargos = pd.read_excel(
                self.config_path,
                sheet_name="CARGOS_V2"
            )
            
            self._atribuicao_service = AtribuicaoServiceV2(
                df_regras=self._df_regras,
                df_colaboradores=self._df_colaboradores,
                df_cargos=self._df_cargos
            )
            
            logger.info(
                f"Serviço de atribuição criado: "
                f"{len(self._df_regras)} regras, "
                f"{len(self._df_colaboradores)} colaboradores, "
                f"{len(self._df_cargos)} cargos"
            )
        except Exception as e:
            logger.error(f"Erro ao criar serviço de atribuição: {e}")
            self._atribuicao_service = None

    def _carregar_dados_comerciais(self, mes: int, ano: int) -> None:
        """Carrega dados da Análise Comercial filtrados por mês/ano e status.
        
        Filtra por:
        - 'Dt Emissão' no mês/ano especificado
        - 'Status Processo' = 'FATURADO'
        """
        logger.info(f"Carregando dados comerciais de {self.comercial_path}")
        
        if not os.path.exists(self.comercial_path):
            # Tentar também com .csv
            csv_path = self.comercial_path.replace(".xlsx", ".csv")
            if os.path.exists(csv_path):
                self._df_comercial = pd.read_csv(csv_path, encoding="utf-8")
                logger.info(f"Carregado CSV alternativo: {csv_path}")
            else:
                raise FileNotFoundError(
                    f"Arquivo de dados comerciais não encontrado: {self.comercial_path}"
                )
        else:
            self._df_comercial = pd.read_excel(self.comercial_path)
        
        total_antes = len(self._df_comercial)
        logger.info(f"Carregados {total_antes} registros comerciais (antes do filtro)")
        
        # Filtrar por Status Processo = 'FATURADO'
        col_status = 'Status Processo'
        if col_status in self._df_comercial.columns:
            self._df_comercial = self._df_comercial[
                self._df_comercial[col_status].astype(str).str.upper().str.strip() == 'FATURADO'
            ]
            logger.info(f"Após filtro Status='FATURADO': {len(self._df_comercial)} registros")
        else:
            logger.warning(f"Coluna '{col_status}' não encontrada - não foi possível filtrar por status")
        
        # Filtrar por Dt Emissão no mês/ano especificado
        col_dt_emissao = 'Dt Emissão'
        if col_dt_emissao in self._df_comercial.columns:
            # Converter para datetime (tentar vários formatos)
            dt_col = self._df_comercial[col_dt_emissao]
            
            # Se já for datetime, usar diretamente
            if not pd.api.types.is_datetime64_any_dtype(dt_col):
                # Tentar conversão automática primeiro (formato ISO YYYY-MM-DD)
                self._df_comercial[col_dt_emissao] = pd.to_datetime(
                    dt_col, 
                    errors='coerce'
                )
            
            # Filtrar pelo mês e ano
            mask = (
                (self._df_comercial[col_dt_emissao].dt.month == mes) &
                (self._df_comercial[col_dt_emissao].dt.year == ano)
            )
            self._df_comercial = self._df_comercial[mask]
            logger.info(f"Após filtro mês={mes:02d}/ano={ano}: {len(self._df_comercial)} registros")
        else:
            logger.warning(f"Coluna '{col_dt_emissao}' não encontrada - não foi possível filtrar por data")
        
        # Verificar colunas necessárias
        required_cols = [
            COL_AC_LINHA, COL_AC_GRUPO, COL_AC_SUBGRUPO,
            COL_AC_TIPO_MERCADORIA, COL_AC_FABRICANTE, COL_AC_FATURAMENTO
        ]
        missing = [c for c in required_cols if c not in self._df_comercial.columns]
        if missing:
            logger.warning(f"Colunas ausentes na Análise Comercial: {missing}")
        
        logger.info(f"Total final: {len(self._df_comercial)} registros para processar (de {total_antes} originais)")

    def _processar_itens_ac(self, mes_ano: str) -> None:
        """Processa cada item da Análise Comercial."""
        if self._df_comercial is None or self._df_comercial.empty:
            logger.warning("Nenhum dado comercial para processar")
            return
        
        if self._atribuicao_service is None:
            logger.error("Serviço de atribuição não inicializado")
            return
        
        self._resultados_por_item = []
        
        for idx, row in self._df_comercial.iterrows():
            resultado_item = self._processar_item_ac(row, idx)
            self._resultados_por_item.append(resultado_item)
        
        logger.info(f"Processados {len(self._resultados_por_item)} itens")

    def _processar_item_ac(
        self, 
        item: pd.Series, 
        idx: int
    ) -> ResultadoItemAC:
        """Processa um único item da Análise Comercial.
        
        Args:
            item: Linha da Análise Comercial
            idx: Índice da linha
            
        Returns:
            ResultadoItemAC com comissões calculadas
        """
        resultado = ResultadoItemAC(
            processo=str(item.get("Processo", "") or "").strip(),
            linha=str(item.get(COL_AC_LINHA, "") or "").strip(),
            grupo=str(item.get(COL_AC_GRUPO, "") or "").strip(),
            subgrupo=str(item.get(COL_AC_SUBGRUPO, "") or "").strip(),
            tipo_mercadoria=str(item.get(COL_AC_TIPO_MERCADORIA, "") or "").strip(),
            fabricante=str(item.get(COL_AC_FABRICANTE, "") or "").strip(),
            faturamento=float(item.get(COL_AC_FATURAMENTO, 0) or 0),
        )
        
        # 1. Obter colaboradores atribuídos para este item
        atrib_result = self._atribuicao_service.get_colaboradores_para_item(item)
        
        # Coletar erros/avisos
        resultado.erros_atribuicao = atrib_result.erros
        resultado.avisos_atribuicao = atrib_result.avisos
        
        if atrib_result.erros:
            for erro in atrib_result.erros:
                self._erros_globais.append(f"Item {idx}: {erro}")
        
        # 2. Para cada colaborador atribuído, calcular comissão
        for colab_atrib in atrib_result.colaboradores:
            comissao, detalhes_calculo = self._calcular_comissao_colaborador(
                nome=colab_atrib.nome,
                cargo=colab_atrib.cargo,
                faturamento=resultado.faturamento,
                fator_split=colab_atrib.fator_split,
                hierarquia=(
                    resultado.linha, 
                    resultado.grupo, 
                    resultado.subgrupo,
                    resultado.tipo_mercadoria,
                    resultado.fabricante
                )
            )
            
            if comissao > 0:
                resultado.comissoes_por_colaborador[colab_atrib.nome] = comissao
                resultado.detalhes_calculo_por_colaborador[colab_atrib.nome] = detalhes_calculo
        
        return resultado

    def _calcular_comissao_colaborador(
        self,
        nome: str,
        cargo: str,
        faturamento: float,
        fator_split: float,
        hierarquia: Tuple[str, str, str, str, str]
    ) -> Tuple[float, Dict]:
        """Calcula comissão de um colaborador para um item específico.
        
        Fórmula V2 (sem FC):
            comissão = faturamento × taxa_faixa × fator_split
        
        Args:
            nome: Nome do colaborador
            cargo: Cargo (para lookup de regras se nome não encontrado)
            faturamento: Valor realizado do item
            fator_split: Fator de divisão (0.0 a 1.0)
            hierarquia: Tupla (linha, grupo, subgrupo, tipo, fabricante)
            
        Returns:
            Tupla (comissão, detalhes_calculo)
            - comissão: Valor da comissão calculada
            - detalhes_calculo: Dict com informações da regra/faixa aplicada
        """
        detalhes_vazio = {
            "regra": None,
            "faixa": None,
            "taxa_aplicada": 0,
            "fator_split": fator_split,
            "motivo": ""
        }
        
        if faturamento <= 0 or fator_split <= 0:
            detalhes_vazio["motivo"] = "Faturamento ou fator_split <= 0"
            return 0.0, detalhes_vazio
        
        # Buscar colaborador nas configurações
        colaborador = self._colaboradores.get(nome)
        
        if colaborador is None:
            detalhes_vazio["motivo"] = f"Colaborador '{nome}' não encontrado em COLABORADORES_V2/REGRAS_COMISSAO_V2"
            logger.debug(detalhes_vazio["motivo"])
            return 0.0, detalhes_vazio
        
        if not colaborador.regras:
            detalhes_vazio["motivo"] = f"Colaborador '{nome}' não possui regras de comissão"
            logger.debug(detalhes_vazio["motivo"])
            return 0.0, detalhes_vazio
        
        # Encontrar regra mais específica para a hierarquia
        regra = self._encontrar_regra_mais_especifica(colaborador.regras, hierarquia)
        
        if regra is None:
            detalhes_vazio["motivo"] = f"Nenhuma regra aplicável para hierarquia: {hierarquia}"
            logger.debug(f"Nenhuma regra aplicável para '{nome}' na hierarquia {hierarquia}")
            return 0.0, detalhes_vazio
        
        # Calcular taxa pela faixa de faturamento
        taxa, faixa_aplicada = self._obter_taxa_faixa_com_detalhes(regra, faturamento)
        
        if taxa <= 0:
            detalhes = {
                "regra": {
                    "linha": regra.linha,
                    "grupo": regra.grupo,
                    "subgrupo": regra.subgrupo,
                    "tipo_mercadoria": regra.tipo_mercadoria,
                    "fabricante": regra.fabricante,
                },
                "faixa": None,
                "taxa_aplicada": 0,
                "fator_split": fator_split,
                "motivo": f"Faturamento R$ {faturamento:.2f} não se encaixa em nenhuma faixa da regra"
            }
            return 0.0, detalhes
        
        # Fórmula V2: comissão = faturamento × taxa × split
        comissao = faturamento * (taxa / 100.0) * fator_split
        
        # Montar detalhes do cálculo
        detalhes = {
            "regra": {
                "linha": regra.linha or "*",
                "grupo": regra.grupo or "*",
                "subgrupo": regra.subgrupo or "*",
                "tipo_mercadoria": regra.tipo_mercadoria or "*",
                "fabricante": regra.fabricante or "*",
            },
            "faixa": faixa_aplicada,
            "taxa_aplicada": taxa,
            "fator_split": fator_split,
            "motivo": f"Regra aplicada: {regra.linha or '*'}/{regra.grupo or '*'} | Faixa: {faixa_aplicada.get('descricao', '')} | Taxa: {taxa}%"
        }
        
        return comissao, detalhes

    def _encontrar_regra_mais_especifica(
        self,
        regras: List[RegraComissao],
        hierarquia: Tuple[str, str, str, str, str]
    ) -> Optional[RegraComissao]:
        """Encontra a regra mais específica que se aplica à hierarquia.
        
        Regra com mais campos preenchidos (não-wildcard) = mais específica.
        
        Args:
            regras: Lista de regras do colaborador
            hierarquia: (linha, grupo, subgrupo, tipo, fabricante) do item
            
        Returns:
            RegraComissao mais específica ou None
        """
        melhor_regra = None
        melhor_score = -1
        
        linha, grupo, subgrupo, tipo_mercadoria, fabricante = hierarquia
        
        for regra in regras:
            score = 0
            match = True
            
            # Verificar cada nível da hierarquia
            # Campo vazio na regra = wildcard (aceita qualquer valor)
            # Campo preenchido deve coincidir
            
            if regra.linha:
                if regra.linha.lower() == linha.lower():
                    score += 1
                else:
                    match = False
                    continue
            
            if regra.grupo:
                if regra.grupo.lower() == grupo.lower():
                    score += 1
                else:
                    match = False
                    continue
            
            if regra.subgrupo:
                if regra.subgrupo.lower() == subgrupo.lower():
                    score += 1
                else:
                    match = False
                    continue
            
            if regra.tipo_mercadoria:
                if regra.tipo_mercadoria.lower() == tipo_mercadoria.lower():
                    score += 1
                else:
                    match = False
                    continue
            
            if regra.fabricante:
                if regra.fabricante.lower() == fabricante.lower():
                    score += 1
                else:
                    match = False
                    continue
            
            if match and score > melhor_score:
                melhor_score = score
                melhor_regra = regra
        
        return melhor_regra

    def _obter_taxa_faixa(self, regra: RegraComissao, faturamento: float) -> float:
        """Obtém a taxa de comissão baseada na faixa de faturamento.
        
        Args:
            regra: Regra de comissão com faixas
            faturamento: Valor a verificar
            
        Returns:
            Taxa em porcentagem (ex: 2.5 = 2.5%)
        """
        if not regra.faixas:
            return 0.0
        
        # Faixas devem estar ordenadas por limite_inferior
        for faixa in sorted(regra.faixas, key=lambda f: f.limite_inferior, reverse=True):
            if faturamento >= faixa.limite_inferior:
                # Verificar limite superior se existir
                if faixa.limite_superior is not None:
                    if faixa.operador_superior == '<=':
                        if faturamento <= faixa.limite_superior:
                            return faixa.taxa_comissao_pct
                    else:  # '<' (padrão)
                        if faturamento < faixa.limite_superior:
                            return faixa.taxa_comissao_pct
                else:
                    return faixa.taxa_comissao_pct
        
        return 0.0

    def _obter_taxa_faixa_com_detalhes(
        self, regra: RegraComissao, faturamento: float
    ) -> Tuple[float, Optional[Dict]]:
        """Obtém a taxa de comissão e detalhes da faixa aplicada.
        
        Args:
            regra: Regra de comissão com faixas
            faturamento: Valor a verificar
            
        Returns:
            Tupla (taxa, faixa_detalhes)
        """
        if not regra.faixas:
            return 0.0, None
        
        # Faixas devem estar ordenadas por limite_inferior
        for faixa in sorted(regra.faixas, key=lambda f: f.limite_inferior, reverse=True):
            if faturamento >= faixa.limite_inferior:
                # Verificar limite superior se existir
                aplica = True
                if faixa.limite_superior is not None:
                    if faixa.operador_superior == '<=':
                        aplica = faturamento <= faixa.limite_superior
                    else:  # '<' (padrão)
                        aplica = faturamento < faixa.limite_superior
                
                if aplica:
                    # Montar descrição da faixa
                    if faixa.limite_superior is not None:
                        descricao = f"R$ {faixa.limite_inferior:,.2f} até R$ {faixa.limite_superior:,.2f}"
                    else:
                        descricao = f"Acima de R$ {faixa.limite_inferior:,.2f}"
                    
                    faixa_detalhes = {
                        "limite_inferior": faixa.limite_inferior,
                        "limite_superior": faixa.limite_superior,
                        "taxa_comissao_pct": faixa.taxa_comissao_pct,
                        "descricao": descricao,
                    }
                    return faixa.taxa_comissao_pct, faixa_detalhes
        
        return 0.0, None

    def _agregar_por_colaborador(self) -> None:
        """Agrega resultados por colaborador."""
        self._resultados_por_colaborador = {}
        
        for item in self._resultados_por_item:
            for nome, comissao in item.comissoes_por_colaborador.items():
                if nome not in self._resultados_por_colaborador:
                    colab = self._colaboradores.get(nome)
                    cargo = colab.cargo if colab else ""
                    self._resultados_por_colaborador[nome] = ResultadoColaboradorAggregado(
                        nome=nome,
                        cargo=cargo
                    )
                
                agg = self._resultados_por_colaborador[nome]
                agg.faturamento_total += item.faturamento
                agg.comissao_total += comissao
                agg.qtd_itens += 1
                
                # Obter detalhes do cálculo para este colaborador
                detalhes_calculo = item.detalhes_calculo_por_colaborador.get(nome, {})
                
                agg.detalhes.append({
                    "processo": item.processo,
                    "linha": item.linha,
                    "grupo": item.grupo,
                    "subgrupo": item.subgrupo,
                    "tipo_mercadoria": item.tipo_mercadoria,
                    "fabricante": item.fabricante,
                    "faturamento": item.faturamento,
                    "comissao": comissao,
                    "detalhes_calculo": detalhes_calculo,
                })

    def _gerar_df_resumo(self) -> pd.DataFrame:
        """Gera DataFrame resumo por colaborador."""
        if not self._resultados_por_colaborador:
            return pd.DataFrame()
        
        registros = []
        for nome, agg in self._resultados_por_colaborador.items():
            taxa_media = (agg.comissao_total / agg.faturamento_total * 100) if agg.faturamento_total > 0 else 0
            registros.append({
                "colaborador": agg.nome,
                "cargo": agg.cargo,
                "faturamento_total": agg.faturamento_total,
                "comissao_total": agg.comissao_total,
                "taxa_media_pct": round(taxa_media, 4),
                "qtd_itens": agg.qtd_itens,
            })
        
        df = pd.DataFrame(registros)
        
        # Ordenar por comissão (maior primeiro)
        df = df.sort_values("comissao_total", ascending=False).reset_index(drop=True)
        
        return df

    def _gerar_df_detalhes(self) -> pd.DataFrame:
        """Gera DataFrame de detalhamento por item."""
        if not self._resultados_por_item:
            return pd.DataFrame()
        
        registros = []
        for item in self._resultados_por_item:
            for nome, comissao in item.comissoes_por_colaborador.items():
                colab = self._colaboradores.get(nome)
                detalhes_calculo = item.detalhes_calculo_por_colaborador.get(nome, {})
                
                # Extrair informações da regra/faixa
                regra_info = detalhes_calculo.get("regra", {}) or {}
                faixa_info = detalhes_calculo.get("faixa", {}) or {}
                
                registros.append({
                    "colaborador": nome,
                    "cargo": colab.cargo if colab else "",
                    "processo": item.processo,
                    "linha": item.linha,
                    "grupo": item.grupo,
                    "subgrupo": item.subgrupo,
                    "tipo_mercadoria": item.tipo_mercadoria,
                    "fabricante": item.fabricante,
                    "faturamento": item.faturamento,
                    "comissao": comissao,
                    # Informações da regra aplicada
                    "regra_linha": regra_info.get("linha", ""),
                    "regra_grupo": regra_info.get("grupo", ""),
                    "regra_subgrupo": regra_info.get("subgrupo", ""),
                    "regra_tipo": regra_info.get("tipo_mercadoria", ""),
                    "regra_fabricante": regra_info.get("fabricante", ""),
                    # Informações da faixa aplicada
                    "faixa_limite_inf": faixa_info.get("limite_inferior", ""),
                    "faixa_limite_sup": faixa_info.get("limite_superior", ""),
                    "faixa_taxa_pct": detalhes_calculo.get("taxa_aplicada", ""),
                    "faixa_descricao": faixa_info.get("descricao", ""),
                    "fator_split": detalhes_calculo.get("fator_split", 1.0),
                    "motivo": detalhes_calculo.get("motivo", ""),
                    "erros": "; ".join(item.erros_atribuicao) if item.erros_atribuicao else "",
                    "avisos": "; ".join(item.avisos_atribuicao) if item.avisos_atribuicao else "",
                })
        
        if not registros:
            return pd.DataFrame()
        
        df = pd.DataFrame(registros)
        return df

    def get_hierarquia_valores_unicos(self) -> Dict[str, List[str]]:
        """Retorna valores únicos por campo da hierarquia.
        
        Útil para popular dropdowns no frontend.
        Carrega da HIERARQUIA_V2.
        
        Returns:
            Dict mapeando campo -> lista de valores únicos.
        """
        try:
            df = pd.read_excel(self.config_path, sheet_name="HIERARQUIA_V2")
        except Exception as e:
            logger.warning(f"Erro ao carregar HIERARQUIA_V2: {e}")
            return {}
        
        campos = ["linha", "grupo", "subgrupo", "tipo_mercadoria", "fabricante"]
        resultado = {}
        
        for campo in campos:
            if campo in df.columns:
                valores = df[campo].dropna().astype(str).str.strip().unique()
                resultado[campo] = sorted([v for v in valores if v])
        
        return resultado

    def salvar_resultados(
        self, output_path: str = "dados_saida/Resultado_Comissoes_V2.xlsx"
    ) -> str:
        """Salva os resultados em arquivo Excel.
        
        Args:
            output_path: Caminho para o arquivo de saída.
            
        Returns:
            Caminho do arquivo salvo.
        """
        # Garantir diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if self._modo_calculo == MODO_CENTRO_CUSTO:
            # Modo Centro de Custo: usar resultados do CCCalculator
            if self._cc_calculator is None:
                logger.warning("Calculador CC não inicializado")
                return ""
            
            df_resumo, df_detalhes = self._cc_calculator.calcular(self._df_comercial)
            
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                if not df_resumo.empty:
                    df_resumo.to_excel(writer, sheet_name="Resumo_CC", index=False)
                if not df_detalhes.empty:
                    df_detalhes.to_excel(writer, sheet_name="Detalhes_Item_CC", index=False)
        else:
            # Modo Hierarquia: usar resultados existentes
            if not self._resultados_por_colaborador:
                logger.warning("Nenhum resultado para salvar")
                return ""
            
            df_resumo = self._gerar_df_resumo()
            df_detalhes = self._gerar_df_detalhes()
            
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
                if not df_detalhes.empty:
                    df_detalhes.to_excel(writer, sheet_name="Detalhes_Item", index=False)
        
        logger.info(f"Resultados salvos em {output_path}")
        return output_path

    @property
    def modo_calculo(self) -> str:
        """Retorna o modo de cálculo atual."""
        return self._modo_calculo

    @property
    def erros_globais(self) -> List[str]:
        """Retorna lista de erros encontrados durante o processamento."""
        return self._erros_globais

    @property
    def colaboradores(self) -> Dict[str, ColaboradorV2]:
        """Retorna colaboradores carregados."""
        return self._colaboradores

    @property
    def resultados_por_colaborador(self) -> Dict[str, ResultadoColaboradorAggregado]:
        """Retorna resultados agregados por colaborador."""
        return self._resultados_por_colaborador

    # =========================================================================
    # INTEGRAÇÃO COM RECEBIMENTO V2
    # =========================================================================
    def processar_recebimento(
        self,
        mes: int,
        ano: int,
        df_margens: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        """Processa comissões por recebimento para colaboradores configurados.
        
        Colaboradores com tipo_comissao='recebimento' em COLABORADORES_V2
        terão suas comissões calculadas via Análise Financeira ao invés
        do faturamento.
        
        Args:
            mes: Mês de apuração (1-12).
            ano: Ano de apuração.
            df_margens: DataFrame com margens por NF (opcional, para reconciliação).
            
        Returns:
            Tupla (df_adiantamentos, df_reconciliacoes, caminho_arquivo)
        """
        logger.info(f"=== Processando Recebimento V2 para {mes:02d}/{ano} ===")
        
        # Inicializar orquestrador de recebimento
        # base_path deve ser a raiz do projeto (pai de config/)
        config_dir = os.path.dirname(self.config_path)
        if config_dir.endswith("config") or config_dir.endswith("config/") or config_dir.endswith("config\\"):
            base_path = os.path.dirname(config_dir) or "."
        else:
            base_path = config_dir or "."
        
        receb_orchestrator = RecebimentoOrchestratorV2(
            base_path=base_path,
            modo_cc=(self._modo_calculo == MODO_CENTRO_CUSTO)
        )
        
        # Executar processamento
        # df_faturamento para reconciliação pode vir de _df_comercial
        adiantamentos, reconciliacoes, output_path = receb_orchestrator.processar_mes(
            mes=mes,
            ano=ano,
            df_faturamento=self._df_comercial,
            df_margens=df_margens
        )
        
        # Converter para DataFrames
        df_adiantamentos = pd.DataFrame([a.to_dict() for a in adiantamentos]) if adiantamentos else pd.DataFrame()
        df_reconciliacoes = pd.DataFrame([r.to_dict() for r in reconciliacoes]) if reconciliacoes else pd.DataFrame()
        
        logger.info(
            f"Recebimento V2 concluído: "
            f"{len(adiantamentos)} adiantamentos, "
            f"{len(reconciliacoes)} reconciliações"
        )
        
        return df_adiantamentos, df_reconciliacoes, output_path

    def obter_colaboradores_por_tipo_comissao(self) -> Dict[str, List[str]]:
        """Retorna colaboradores agrupados por tipo de comissão.
        
        Returns:
            Dict com chaves 'faturamento' e 'recebimento', cada uma
            contendo lista de nomes de colaboradores.
        """
        resultado = {
            "faturamento": [],
            "recebimento": []
        }
        
        for colab in self._colaboradores.values():
            if colab.recebe_por_recebimento:
                resultado["recebimento"].append(colab.nome)
            else:
                resultado["faturamento"].append(colab.nome)
        
        return resultado
