"""
src.metodo_v2.cc_calculator_v2 - Calculador de Comissões por Centro de Custo + Fabricante

Implementa o modo de cálculo V2 baseado em Centro de Custo (+ Fabricante opcional):

Fluxo:
======
1. Para cada item da AC:
   a. Identificar CC e Fabricante do item
   b. Para cada colaborador vinculado ao CC:
      - Buscar regra mais específica (CC+Fab > CC genérica)
      - Determinar chave de agrupamento baseada na regra encontrada
2. Acumular faturamento por colaborador por chave (CC, Fab ou CC+null)
3. Determinar faixa/taxa pela soma total de cada chave
4. Aplicar taxa a cada item individualmente

Especificidade de Regras:
=========================
- Regra com CC + Fabricante: especificidade = 2 (maior prioridade)
- Regra com CC apenas (Fab=null): especificidade = 1 (fallback)

Fórmula:
========
Para item com CC=X, Fab=Y:
  1. R = regra mais específica para (X, Y) ou fallback (X, null)
  2. chave = R.chave_agrupamento  # (X, Y) ou (X, null)
  3. F_total[colab][chave] += faturamento_item
  4. taxa = R.get_taxa_para_faturamento(F_total[colab][chave])
  5. Comissão_item = faturamento_item × taxa × split_efetivo
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

import pandas as pd
import numpy as np

from .models_v2 import ColaboradorV2, RegraCentroCusto, FaixaComissao


logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================
COL_CC = "Centro Custo-pedido"
COL_FABRICANTE = "Fabricante"
COL_CONSULTOR_INTERNO = "Consultor Interno"
COL_REPRESENTANTE = "Representante-pedido"
COL_FATURAMENTO = "Valor Realizado"
COL_PROCESSO = "Processo"

# Cargos que precisam verificação dupla (nome na AC + vínculo CC)
CARGOS_OPERACIONAIS = {"Consultor Interno", "Consultor Externo"}

# Cargos que usam split por regra (CC, Fab) - soma deve ser 100%
CARGOS_COM_SPLIT = {"Gerente Linha", "Coordenador"}


# =============================================================================
# DATACLASSES DE RESULTADO
# =============================================================================
@dataclass
class ResultadoItemCC:
    """Resultado do cálculo para um item da AC no modo Centro de Custo."""
    
    processo: str = ""
    centro_custo: str = ""
    fabricante: str = ""
    faturamento: float = 0.0
    descricao_produto: str = ""
    
    # Comissões calculadas: {nome_colaborador: comissao}
    comissoes_por_colaborador: Dict[str, float] = field(default_factory=dict)
    
    # Detalhes do cálculo por colaborador
    detalhes_por_colaborador: Dict[str, Dict] = field(default_factory=dict)
    
    erros: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)


@dataclass
class ResultadoColaboradorCC:
    """Resultado agregado por colaborador no modo Centro de Custo + Fabricante."""
    
    nome: str
    cargo: str
    centro_custo: str
    fabricante: Optional[str] = None  # None = regra genérica (todos fabs)
    faturamento_total_cc: float = 0.0  # Soma no CC (+Fab)
    comissao_total_cc: float = 0.0
    taxa_aplicada: float = 0.0
    faixa_descricao: str = ""
    qtd_itens: int = 0
    itens: List[Dict] = field(default_factory=list)


# Chave de agrupamento: (centro_custo, fabricante) onde fabricante pode ser None
ChaveAgrupamento = Tuple[str, Optional[str]]


@dataclass
class FaturamentoColaboradorCC:
    """Faturamento acumulado de um colaborador em uma chave (CC, Fabricante)."""
    
    nome: str
    cargo: str
    centro_custo: str
    fabricante: Optional[str] = None  # None = agrupamento genérico
    faturamento_total: float = 0.0
    itens: List[Dict] = field(default_factory=list)  # Lista de itens processados
    fator_split: float = 1.0
    regra: Optional[RegraCentroCusto] = None  # Regra que originou este agrupamento
    
    @property
    def chave(self) -> ChaveAgrupamento:
        """Retorna a chave de agrupamento."""
        return (self.centro_custo, self.fabricante)
    
    def adicionar_item(self, processo: str, faturamento: float, fabricante_item: str) -> None:
        """Adiciona um item ao acumulado."""
        self.itens.append({
            "processo": processo,
            "faturamento": faturamento,
            "fabricante": fabricante_item,
        })
        self.faturamento_total += faturamento


# =============================================================================
# CALCULADOR PRINCIPAL
# =============================================================================
class CCCalculatorV2:
    """Calculador de comissões no modo Centro de Custo.
    
    Uso:
        calculator = CCCalculatorV2(colaboradores, df_cargos)
        resultados = calculator.calcular(df_comercial)
    """

    def __init__(
        self,
        colaboradores: Dict[str, ColaboradorV2],
        df_cargos: pd.DataFrame,
        df_colaboradores: Optional[pd.DataFrame] = None,
    ):
        """Inicializa o calculador.
        
        Args:
            colaboradores: Dict de colaboradores carregados do config.
            df_cargos: DataFrame da aba CARGOS_V2 (cargo -> tipo).
            df_colaboradores: DataFrame da aba COLABORADORES_V2 (para fator_split).
        """
        self._colaboradores = colaboradores
        self._cargos_tipo = self._build_cargos_tipo(df_cargos)
        self._fator_split_map = self._build_fator_split_map(df_colaboradores)
        
        # Resultados
        self._resultados_por_item: List[ResultadoItemCC] = []
        self._resultados_por_colaborador_cc: Dict[str, Dict[str, ResultadoColaboradorCC]] = {}
        self._erros: List[str] = []

    def _build_cargos_tipo(self, df: pd.DataFrame) -> Dict[str, str]:
        """Constrói mapa cargo -> tipo (OPERACIONAL/GESTAO)."""
        cargo_tipo = {}
        if df is None or df.empty:
            return cargo_tipo
        
        df = df.copy()
        df.columns = df.columns.str.strip()
        
        # Coluna de cargo pode ser 'cargo' ou 'nome_cargo'
        cargo_col = None
        for col in ["cargo", "nome_cargo"]:
            if col in df.columns:
                cargo_col = col
                break
        
        tipo_col = "tipo" if "tipo" in df.columns else None
        
        if cargo_col and tipo_col:
            for _, row in df.iterrows():
                cargo = str(row.get(cargo_col, "")).strip()
                tipo = str(row.get(tipo_col, "")).strip().upper()
                if cargo:
                    cargo_tipo[cargo] = tipo
            
            logger.debug(f"Mapa cargo->tipo construído: {cargo_tipo}")
        else:
            logger.warning(f"Colunas cargo/tipo não encontradas em CARGOS_V2. cargo_col={cargo_col}, tipo_col={tipo_col}")
        
        return cargo_tipo

    def _build_fator_split_map(self, df: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Constrói mapa colaborador -> fator_split."""
        split_map = {}
        if df is None or df.empty:
            return split_map
        
        df = df.copy()
        df.columns = df.columns.str.strip()
        
        nome_col = None
        for col in ["nome_colaborador", "colaborador"]:
            if col in df.columns:
                nome_col = col
                break
        
        if nome_col and "fator_split" in df.columns:
            for _, row in df.iterrows():
                nome = str(row.get(nome_col, "")).strip()
                split = row.get("fator_split", 1.0)
                if nome:
                    # Converter porcentagem para decimal se necessário
                    if pd.notna(split):
                        split = float(split)
                        if split > 1:
                            split = split / 100.0
                    else:
                        split = 1.0
                    split_map[nome] = split
        
        return split_map

    def calcular(
        self, 
        df_comercial: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Executa o cálculo de comissões no modo Centro de Custo.
        
        Args:
            df_comercial: DataFrame da Análise Comercial (já filtrado por mês/ano e status).
            
        Returns:
            Tupla (df_resumo, df_detalhes):
            - df_resumo: Agregado por colaborador e CC
            - df_detalhes: Item a item com comissão calculada
        """
        self._resultados_por_item = []
        self._resultados_por_colaborador_cc = {}
        self._erros = []
        
        if df_comercial.empty:
            logger.warning("DataFrame comercial vazio, nenhum cálculo realizado")
            return pd.DataFrame(), pd.DataFrame()
        
        # Verificar coluna Centro Custo-pedido
        if COL_CC not in df_comercial.columns:
            self._erros.append(f"Coluna '{COL_CC}' não encontrada na Análise Comercial")
            logger.error(self._erros[-1])
            return pd.DataFrame(), pd.DataFrame()
        
        # PASSO 1: Acumular faturamento por colaborador por chave (CC, Fabricante)
        faturamentos = self._acumular_faturamentos_por_cc_fab(df_comercial)
        
        # PASSO 2: Determinar taxa por colaborador/chave com base no faturamento total
        taxas_por_colab_chave = self._calcular_taxas(faturamentos)
        
        # PASSO 3: Aplicar taxas a cada item
        self._calcular_comissoes_por_item(df_comercial, taxas_por_colab_chave, faturamentos)
        
        # PASSO 4: Gerar DataFrames de saída
        df_resumo = self._gerar_df_resumo()
        df_detalhes = self._gerar_df_detalhes()
        
        return df_resumo, df_detalhes

    def _acumular_faturamentos_por_cc_fab(
        self, 
        df: pd.DataFrame
    ) -> Dict[ChaveAgrupamento, Dict[str, FaturamentoColaboradorCC]]:
        """Acumula faturamento de cada colaborador por chave (CC, Fabricante).
        
        A chave de agrupamento é determinada pela regra mais específica encontrada:
        - Se existe regra CC+Fab: agrupa em (CC, Fab)
        - Se só existe regra CC genérica: agrupa em (CC, None)
        
        Returns:
            Dict[(cc, fab), Dict[nome_colaborador, FaturamentoColaboradorCC]]
        """
        # Estrutura: {(cc, fab): {nome: FaturamentoColaboradorCC}}
        faturamentos: Dict[ChaveAgrupamento, Dict[str, FaturamentoColaboradorCC]] = {}
        
        for idx, row in df.iterrows():
            centro_custo = str(row.get(COL_CC, "")).strip()
            if not centro_custo:
                continue
            
            fabricante = str(row.get(COL_FABRICANTE, "")).strip() if COL_FABRICANTE in df.columns else ""
            if fabricante.lower() in ["", "nan", "none"]:
                fabricante = ""
            
            faturamento = float(row.get(COL_FATURAMENTO, 0) or 0)
            processo = str(row.get(COL_PROCESSO, "")).strip()
            
            # Identificar colaboradores que devem receber comissão por este item
            colaboradores_item = self._identificar_colaboradores_para_item(row, centro_custo, fabricante)
            
            for colab_info in colaboradores_item:
                nome = colab_info["nome"]
                cargo = colab_info["cargo"]
                fator_split = colab_info["fator_split"]
                regra = colab_info["regra"]
                
                # Chave de agrupamento vem da regra encontrada
                chave = regra.chave_agrupamento
                
                if chave not in faturamentos:
                    faturamentos[chave] = {}
                
                if nome not in faturamentos[chave]:
                    faturamentos[chave][nome] = FaturamentoColaboradorCC(
                        nome=nome,
                        cargo=cargo,
                        centro_custo=chave[0],
                        fabricante=chave[1],
                        fator_split=fator_split,
                        regra=regra,
                    )
                
                faturamentos[chave][nome].adicionar_item(processo, faturamento, fabricante)
        
        return faturamentos

    def _identificar_colaboradores_para_item(
        self, 
        row: pd.Series, 
        centro_custo: str,
        fabricante: str
    ) -> List[Dict]:
        """Identifica quais colaboradores devem receber comissão por um item.
        
        Para OPERACIONAIS: verifica nome na AC + regra para CC (+Fab)
        Para GESTÃO: verifica se tem regra para o CC (+Fab)
        
        IMPORTANTE: Colaboradores com tipo_comissao='recebimento' são EXCLUÍDOS
        pois suas comissões são calculadas via fluxo de recebimento separado.
        
        Busca regra mais específica (CC+Fab) com fallback para genérica (CC).
        
        Returns:
            Lista de dicts: [{"nome": str, "cargo": str, "fator_split": float, "regra": RegraCentroCusto}, ...]
        """
        colaboradores_item = []
        
        # 1. OPERACIONAIS: Verificar nomes das colunas da AC
        consultor_interno = str(row.get(COL_CONSULTOR_INTERNO, "")).strip()
        representante = str(row.get(COL_REPRESENTANTE, "")).strip()
        
        # Consultor Interno
        if consultor_interno and consultor_interno.lower() not in ["", "nan", "none", "nenhum"]:
            colab = self._colaboradores.get(consultor_interno)
            if colab:
                # FILTRO: Pular colaboradores de recebimento
                if colab.recebe_por_recebimento:
                    logger.debug(f"Colaborador '{consultor_interno}' é de recebimento, pulando no cálculo de faturamento")
                else:
                    # Buscar regra mais específica
                    regra = colab.get_regra_cc(centro_custo, fabricante)
                    if regra:
                        colaboradores_item.append({
                            "nome": consultor_interno,
                            "cargo": colab.cargo,
                            "fator_split": self._fator_split_map.get(consultor_interno, 1.0),
                            "regra": regra,
                        })
        
        # Consultor Externo (Representante)
        if representante and representante.lower() not in ["", "nan", "none", "nenhum"]:
            colab = self._colaboradores.get(representante)
            if colab:
                # FILTRO: Pular colaboradores de recebimento
                if colab.recebe_por_recebimento:
                    logger.debug(f"Colaborador '{representante}' é de recebimento, pulando no cálculo de faturamento")
                else:
                    regra = colab.get_regra_cc(centro_custo, fabricante)
                    if regra:
                        colaboradores_item.append({
                            "nome": representante,
                            "cargo": colab.cargo,
                            "fator_split": self._fator_split_map.get(representante, 1.0),
                            "regra": regra,
                        })
        
        # 2. GESTÃO: Verificar todos os colaboradores que têm regra para o CC (+Fab)
        for nome, colab in self._colaboradores.items():
            # Pular se já foi adicionado como operacional
            if any(c["nome"] == nome for c in colaboradores_item):
                continue
            
            # FILTRO: Pular colaboradores de recebimento
            if colab.recebe_por_recebimento:
                continue
            
            # Verificar se é cargo de gestão
            tipo_cargo = self._cargos_tipo.get(colab.cargo, "").upper()
            if tipo_cargo != "GESTAO":
                continue
            
            # Buscar regra mais específica para CC+Fab
            regra = colab.get_regra_cc(centro_custo, fabricante)
            if regra:
                colaboradores_item.append({
                    "nome": nome,
                    "cargo": colab.cargo,
                    "fator_split": self._fator_split_map.get(nome, 1.0),
                    "regra": regra,
                })
        
        return colaboradores_item

    def _calcular_split_efetivo_por_chave(
        self,
        faturamentos: Dict[ChaveAgrupamento, Dict[str, FaturamentoColaboradorCC]]
    ) -> Dict[ChaveAgrupamento, Dict[str, float]]:
        """Calcula o fator de split efetivo para cada colaborador por chave (CC, Fab).
        
        Regras de Negócio:
        - Cargos em CARGOS_COM_SPLIT (Gerente Linha, Coordenador):
          * Se regra.split definido → usar valor da regra / 100
          * Se regra.split = None e único do cargo na regra → 100%
          * Se regra.split = None e múltiplos do cargo → erro de configuração
        - Demais cargos:
          * Se único do cargo na chave → 100%
          * Se múltiplos → usar fator_split do COLABORADORES_V2
        
        Returns:
            Dict[(cc, fab), Dict[nome_colaborador, split_efetivo]]
        """
        splits_efetivos: Dict[ChaveAgrupamento, Dict[str, float]] = {}
        
        for chave, colabs_dict in faturamentos.items():
            splits_efetivos[chave] = {}
            
            # Agrupar colaboradores por cargo nesta chave
            colaboradores_por_cargo: Dict[str, List[str]] = {}
            for nome, fat_info in colabs_dict.items():
                cargo = fat_info.cargo
                if cargo not in colaboradores_por_cargo:
                    colaboradores_por_cargo[cargo] = []
                colaboradores_por_cargo[cargo].append(nome)
            
            # Determinar split efetivo para cada colaborador
            for nome, fat_info in colabs_dict.items():
                cargo = fat_info.cargo
                regra = fat_info.regra
                qtd_mesmo_cargo = len(colaboradores_por_cargo.get(cargo, []))
                
                # ============================================================
                # LÓGICA DE SPLIT ESPECÍFICA PARA GERENTE LINHA / COORDENADOR
                # ============================================================
                if cargo in CARGOS_COM_SPLIT:
                    # Usar split da regra (campo split em REGRAS_COMISSAO_CC_V2)
                    if regra and regra.split is not None:
                        # Split definido na regra
                        split_efetivo = regra.get_split_decimal()
                        logger.debug(
                            f"Split efetivo chave {chave} para '{nome}' ({cargo}): "
                            f"{split_efetivo*100:.0f}% (da regra CC)"
                        )
                    elif qtd_mesmo_cargo == 1:
                        # Único do cargo na regra → 100%
                        split_efetivo = 1.0
                        logger.debug(
                            f"Split efetivo chave {chave} para '{nome}' ({cargo}): "
                            f"100% (único {cargo} na regra)"
                        )
                    else:
                        # Múltiplos sem split definido = ERRO de configuração
                        # Fallback: dividir igualmente e logar warning
                        split_efetivo = 1.0 / qtd_mesmo_cargo
                        logger.warning(
                            f"Split não definido para '{nome}' ({cargo}) em {chave} "
                            f"com {qtd_mesmo_cargo} colaboradores do mesmo cargo. "
                            f"Usando fallback: {split_efetivo*100:.1f}%"
                        )
                else:
                    # Demais cargos: lógica original
                    if qtd_mesmo_cargo == 1:
                        split_efetivo = 1.0
                        logger.debug(
                            f"Split efetivo chave {chave} para '{nome}' ({cargo}): "
                            f"100% (único do cargo)"
                        )
                    else:
                        # Múltiplos do mesmo cargo → usar split de COLABORADORES_V2
                        split_efetivo = fat_info.fator_split
                        logger.debug(
                            f"Split efetivo chave {chave} para '{nome}' ({cargo}): "
                            f"{split_efetivo*100:.0f}% ({qtd_mesmo_cargo} colaboradores)"
                        )
                
                splits_efetivos[chave][nome] = split_efetivo
        
        return splits_efetivos

    def _calcular_faturamento_total_por_cc(
        self,
        faturamentos: Dict[ChaveAgrupamento, Dict[str, FaturamentoColaboradorCC]]
    ) -> Dict[str, Dict[str, float]]:
        """Calcula o faturamento TOTAL por Centro de Custo para cada colaborador.
        
        Para regras genéricas (CC + TODOS), a faixa de comissão deve ser determinada
        pelo faturamento total do CC, incluindo itens de fabricantes específicos.
        
        Returns:
            Dict[centro_custo, Dict[nome_colaborador, faturamento_total_cc]]
        """
        faturamento_total_por_cc: Dict[str, Dict[str, float]] = {}
        
        for chave, colabs_dict in faturamentos.items():
            cc, _fab = chave  # _fab pode ser específico ou None
            
            if cc not in faturamento_total_por_cc:
                faturamento_total_por_cc[cc] = {}
            
            for nome, fat_info in colabs_dict.items():
                if nome not in faturamento_total_por_cc[cc]:
                    faturamento_total_por_cc[cc][nome] = 0.0
                
                # Somar faturamento de todas as chaves (específicas e genéricas) do mesmo CC
                faturamento_total_por_cc[cc][nome] += fat_info.faturamento_total
        
        # Log para debug
        for cc, colabs in faturamento_total_por_cc.items():
            for nome, total in colabs.items():
                logger.debug(f"Faturamento TOTAL no CC '{cc}' para '{nome}': R$ {total:,.2f}")
        
        return faturamento_total_por_cc

    def _calcular_taxas(
        self, 
        faturamentos: Dict[ChaveAgrupamento, Dict[str, FaturamentoColaboradorCC]]
    ) -> Dict[ChaveAgrupamento, Dict[str, Dict]]:
        """Calcula taxa para cada colaborador/chave com base no faturamento total.
        
        REGRA DE NEGÓCIO IMPORTANTE:
        ============================
        - Regra ESPECÍFICA (CC + Fabricante): usa faturamento apenas do par (CC, Fab)
        - Regra GENÉRICA (CC + TODOS/None): usa faturamento TOTAL do CC (todos os fabricantes)
        
        Returns:
            Dict[(cc, fab), Dict[nome, {"taxa": float, "faixa": dict, ...}]]
        """
        taxas: Dict[ChaveAgrupamento, Dict[str, Dict]] = {}
        
        # Calcular splits efetivos (regra: único do cargo na chave = 100%)
        splits_efetivos = self._calcular_split_efetivo_por_chave(faturamentos)
        
        # PRÉ-COMPUTAR: Faturamento total por CC para regras genéricas
        faturamento_total_por_cc = self._calcular_faturamento_total_por_cc(faturamentos)
        
        for chave, colabs_dict in faturamentos.items():
            taxas[chave] = {}
            cc, fab = chave
            
            for nome, fat_info in colabs_dict.items():
                regra = fat_info.regra
                if not regra:
                    continue
                
                # ============================================================
                # REGRA DE NEGÓCIO: Qual faturamento usar para determinar faixa?
                # ============================================================
                # - Regra ESPECÍFICA (fab != None): faturamento do par (CC, Fab)
                # - Regra GENÉRICA (fab == None): faturamento TOTAL do CC
                # ============================================================
                if fab is None:
                    # Regra genérica: usar faturamento TOTAL do CC (todos os fabricantes)
                    faturamento_para_faixa = faturamento_total_por_cc.get(cc, {}).get(nome, 0.0)
                    logger.debug(
                        f"Regra GENÉRICA CC '{cc}' para '{nome}': "
                        f"usando faturamento TOTAL do CC = R$ {faturamento_para_faixa:,.2f}"
                    )
                else:
                    # Regra específica: usar faturamento apenas do par (CC, Fab)
                    faturamento_para_faixa = fat_info.faturamento_total
                    logger.debug(
                        f"Regra ESPECÍFICA CC '{cc}' + Fab '{fab}' para '{nome}': "
                        f"usando faturamento do par = R$ {faturamento_para_faixa:,.2f}"
                    )
                
                # Calcular taxa pela faixa do faturamento determinado
                taxa = regra.get_taxa_para_faturamento(faturamento_para_faixa)
                faixa = regra.get_faixa_para_faturamento(faturamento_para_faixa)
                
                faixa_info = None
                if faixa:
                    limite_sup_str = f"R$ {faixa.limite_superior:,.2f}" if faixa.limite_superior else "∞"
                    faixa_info = {
                        "limite_inferior": faixa.limite_inferior,
                        "limite_superior": faixa.limite_superior,
                        "taxa": faixa.taxa_comissao_pct,
                        "descricao": f"R$ {faixa.limite_inferior:,.2f} até {limite_sup_str}",
                    }
                
                # Usar split efetivo (não o configurado)
                split_efetivo = splits_efetivos.get(chave, {}).get(nome, 1.0)
                
                taxas[chave][nome] = {
                    "taxa": taxa,
                    "faixa": faixa_info,
                    "faturamento_total": faturamento_para_faixa,  # Faturamento usado para faixa
                    "faturamento_itens": fat_info.faturamento_total,  # Faturamento dos itens desta chave
                    "fator_split": split_efetivo,
                    "fator_split_config": fat_info.fator_split,
                    "cargo": fat_info.cargo,
                    "fabricante_regra": regra.fabricante,  # Fabricante da regra (None = genérica)
                    "centro_custo": cc,
                }
                
                fab_str = fab if fab else "TODOS"
                logger.debug(
                    f"Taxa CC '{cc}' Fab '{fab_str}' para '{nome}': "
                    f"Fat.Faixa=R${faturamento_para_faixa:,.2f} → Taxa={taxa}% | Split={split_efetivo*100:.0f}%"
                )
        
        return taxas

    def _calcular_comissoes_por_item(
        self, 
        df: pd.DataFrame,
        taxas_por_colab_chave: Dict[ChaveAgrupamento, Dict[str, Dict]],
        faturamentos: Dict[ChaveAgrupamento, Dict[str, FaturamentoColaboradorCC]]
    ) -> None:
        """Aplica as taxas calculadas a cada item individualmente.
        
        Para cada item:
        1. Extrair CC e Fabricante do item
        2. Para cada colaborador com taxas calculadas, encontrar a chave correspondente:
           - Tentar (CC, Fabricante) primeiro (regra específica)
           - Fallback para (CC, None) se não houver regra específica
        3. Aplicar a comissão usando taxa/split da chave encontrada
        """
        self._resultados_por_item = []
        
        for idx, row in df.iterrows():
            centro_custo = str(row.get(COL_CC, "")).strip()
            fabricante = str(row.get(COL_FABRICANTE, "")).strip() if COL_FABRICANTE in df.columns else ""
            if fabricante.lower() in ["", "nan", "none"]:
                fabricante = None
            
            faturamento = float(row.get(COL_FATURAMENTO, 0) or 0)
            processo = str(row.get(COL_PROCESSO, "")).strip()
            descricao_produto = (
                row.get("descricao_produto")
                or row.get("Descricao_Produto")
                or row.get("DESCRICAO_PRODUTO")
                or row.get("Descrição Produto")
                or row.get("DESCRICAO PRODUTO")
                or ""
            )
            descricao_produto = str(descricao_produto).strip()
            
            resultado = ResultadoItemCC(
                processo=processo,
                centro_custo=centro_custo,
                fabricante=fabricante if fabricante else "",
                faturamento=faturamento,
                descricao_produto=descricao_produto,
            )
            
            if not centro_custo:
                resultado.avisos.append("Item sem CC")
                self._resultados_por_item.append(resultado)
                continue
            
            # Identificar colaboradores que participam deste item e suas chaves
            colabs_item = self._identificar_colaboradores_para_item(row, centro_custo, fabricante)
            
            for info_colab in colabs_item:
                nome = info_colab["nome"]
                regra = info_colab.get("regra")
                
                if not regra:
                    continue
                
                # Determinar a chave de agrupamento baseada na regra encontrada
                chave = regra.chave_agrupamento
                
                # Buscar taxas para esta chave e colaborador
                if chave not in taxas_por_colab_chave:
                    resultado.avisos.append(f"Chave {chave} não encontrada em taxas")
                    continue
                
                if nome not in taxas_por_colab_chave[chave]:
                    resultado.avisos.append(f"Colaborador '{nome}' não encontrado na chave {chave}")
                    continue
                
                info_taxa = taxas_por_colab_chave[chave][nome]
                taxa = info_taxa["taxa"]
                fator_split = info_taxa["fator_split"]
                faixa = info_taxa["faixa"]
                
                # Verificar se este colaborador deve comissionar neste item específico
                # Para operacionais, verificar se é o consultor do processo
                colab = self._colaboradores.get(nome)
                if not colab:
                    continue
                
                tipo_cargo = self._cargos_tipo.get(colab.cargo, "").upper()
                
                # Para operacionais, verificar se é o responsável pelo processo
                if tipo_cargo == "OPERACIONAL":
                    consultor_interno = str(row.get(COL_CONSULTOR_INTERNO, "")).strip()
                    representante = str(row.get(COL_REPRESENTANTE, "")).strip()
                    if nome != consultor_interno and nome != representante:
                        continue
                
                # Calcular comissão: faturamento × taxa × split
                comissao = faturamento * (taxa / 100.0) * fator_split
                
                if comissao > 0:
                    fab_str = chave[1] if chave[1] else "TODOS"
                    resultado.comissoes_por_colaborador[nome] = comissao
                    resultado.detalhes_por_colaborador[nome] = {
                        "taxa": taxa,
                        "fator_split": fator_split,
                        "faixa": faixa,
                        "faturamento_total_cc": info_taxa["faturamento_total"],
                        "cargo": info_taxa["cargo"],
                        "fabricante_regra": info_taxa.get("fabricante_regra"),
                        "chave": chave,
                        "motivo": (
                            f"CC: {centro_custo} | Fab: {fab_str} | "
                            f"Fat.Total: R$ {info_taxa['faturamento_total']:,.2f} | "
                            f"Faixa: {faixa['descricao'] if faixa else 'N/A'} | "
                            f"Taxa: {taxa}%"
                        ),
                    }
            
            self._resultados_por_item.append(resultado)
            
            # Agregar por colaborador/CC/Fabricante
            for nome, comissao in resultado.comissoes_por_colaborador.items():
                detalhes = resultado.detalhes_por_colaborador.get(nome, {})
                chave = detalhes.get("chave", (centro_custo, None))
                
                self._agregar_resultado_colaborador_cc(
                    nome=nome,
                    centro_custo=centro_custo,
                    fabricante=chave[1],  # Fabricante da regra (pode ser None)
                    processo=processo,
                    faturamento=faturamento,
                    comissao=comissao,
                    detalhes=detalhes,
                )

    def _agregar_resultado_colaborador_cc(
        self,
        nome: str,
        centro_custo: str,
        fabricante: Optional[str],
        processo: str,
        faturamento: float,
        comissao: float,
        detalhes: Dict,
    ) -> None:
        """Agrega resultados por colaborador e chave (Centro de Custo + Fabricante).
        
        A chave de agrupamento é (CC, Fabricante) para manter resultados separados
        quando há regras específicas por fabricante.
        """
        chave: ChaveAgrupamento = (centro_custo, fabricante)
        
        if nome not in self._resultados_por_colaborador_cc:
            self._resultados_por_colaborador_cc[nome] = {}
        
        if chave not in self._resultados_por_colaborador_cc[nome]:
            colab = self._colaboradores.get(nome)
            self._resultados_por_colaborador_cc[nome][chave] = ResultadoColaboradorCC(
                nome=nome,
                cargo=colab.cargo if colab else "",
                centro_custo=centro_custo,
                fabricante=fabricante,
                taxa_aplicada=detalhes.get("taxa", 0),
                faixa_descricao=detalhes.get("faixa", {}).get("descricao", "") if detalhes.get("faixa") else "",
            )
        
        res = self._resultados_por_colaborador_cc[nome][chave]
        res.faturamento_total_cc = detalhes.get("faturamento_total_cc", res.faturamento_total_cc)
        res.comissao_total_cc += comissao
        res.qtd_itens += 1
        res.itens.append({
            "processo": processo,
            "faturamento": faturamento,
            "comissao": comissao,
        })

    def _gerar_df_resumo(self) -> pd.DataFrame:
        """Gera DataFrame resumido por colaborador e chave (CC + Fabricante)."""
        rows = []
        
        for nome, chaves_dict in self._resultados_por_colaborador_cc.items():
            for chave, resultado in chaves_dict.items():
                cc, fab = chave
                # Calcular taxa média: (comissão / faturamento) * 100
                faturamento = resultado.faturamento_total_cc
                comissao = resultado.comissao_total_cc
                taxa_media_pct = (comissao / faturamento * 100) if faturamento > 0 else 0.0
                
                rows.append({
                    "colaborador": resultado.nome,
                    "cargo": resultado.cargo,
                    "centro_custo": resultado.centro_custo,
                    "fabricante": resultado.fabricante if resultado.fabricante else "TODOS",
                    "faturamento_total": resultado.faturamento_total_cc,
                    "taxa_aplicada": resultado.taxa_aplicada,
                    "taxa_media_pct": round(taxa_media_pct, 2),
                    "faixa": resultado.faixa_descricao,
                    "comissao_total": resultado.comissao_total_cc,
                    "qtd_itens": resultado.qtd_itens,
                })
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        df = df.sort_values(["colaborador", "centro_custo", "fabricante"])
        return df

    def _gerar_df_detalhes(self) -> pd.DataFrame:
        """Gera DataFrame detalhado item a item."""
        rows = []
        
        for resultado in self._resultados_por_item:
            for nome, comissao in resultado.comissoes_por_colaborador.items():
                detalhes = resultado.detalhes_por_colaborador.get(nome, {})
                chave = detalhes.get("chave", (resultado.centro_custo, None))
                fab_regra = chave[1] if chave else None
                
                rows.append({
                    "colaborador": nome,
                    "cargo": detalhes.get("cargo", ""),
                    "processo": resultado.processo,
                    "centro_custo": resultado.centro_custo,
                    "fabricante_item": resultado.fabricante if resultado.fabricante else "",
                    "fabricante_regra": fab_regra if fab_regra else "TODOS",
                    "faturamento": resultado.faturamento,  # Para compatibilidade
                    "faturamento_item": resultado.faturamento,
                    "descricao_produto": resultado.descricao_produto,
                    "faturamento_total_cc": detalhes.get("faturamento_total_cc", 0),  # Nome esperado pelo frontend
                    "faixa_taxa_pct": detalhes.get("taxa", 0),  # Nome esperado pelo frontend
                    "taxa_aplicada": detalhes.get("taxa", 0),
                    "fator_split": detalhes.get("fator_split", 1.0),
                    "comissao": comissao,
                    "faixa_descricao": detalhes.get("faixa", {}).get("descricao", "") if detalhes.get("faixa") else "",
                    "motivo": detalhes.get("motivo", ""),
                })
        
        if not rows:
            return pd.DataFrame()
        
        return pd.DataFrame(rows)

    @property
    def erros(self) -> List[str]:
        """Retorna lista de erros encontrados."""
        return self._erros
