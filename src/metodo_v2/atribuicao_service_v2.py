"""
src.metodo_v2.atribuicao_service_v2 - Serviço de Atribuições V2 (Simplificado)

Responsável por identificar quais colaboradores recebem comissão para cada item
da Análise Comercial, usando APENAS a aba REGRAS_COMISSAO_V2.

VERSÃO SIMPLIFICADA - NÃO USA ATRIBUICOES_V2

Lógica de Atribuição:
---------------------
1. OPERACIONAL (Consultor Interno, Consultor Externo):
   - Nome extraído diretamente da Análise Comercial (colunas 'Consultor Interno' e 'Representante-pedido')
   - DEVE ter regra em REGRAS_COMISSAO_V2 para a hierarquia do item
   - Se não tiver regra para aquela hierarquia, gera erro de validação

2. GESTÃO (Gerente Linha, Coordenador, Diretor, Gerente Geral, Supervisor):
   - Encontrado via REGRAS_COMISSAO_V2: quem tem regra aplicável à hierarquia do item
   - Não consulta nome em colunas da AC
   - Aplica fator_split (vem de COLABORADORES_V2)

3. Cargos são classificados como OPERACIONAL ou GESTAO via aba CARGOS_V2 (coluna 'tipo')
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set

import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES - Colunas da Análise Comercial
# =============================================================================
COL_AC_CONSULTOR_INTERNO = "Consultor Interno"
COL_AC_REPRESENTANTE = "Representante-pedido"
COL_AC_LINHA = "Negócio"
COL_AC_GRUPO = "Grupo"
COL_AC_SUBGRUPO = "Subgrupo"
COL_AC_TIPO_MERCADORIA = "Tipo de Mercadoria"
COL_AC_FABRICANTE = "Fabricante"
COL_AC_FATURAMENTO = "Valor Realizado"


# =============================================================================
# CONSTANTES - Colunas REGRAS_COMISSAO_V2
# =============================================================================
HIER_COLS_REGRAS = ["linha", "grupo", "subgrupo", "tipo_mercadoria", "fabricante"]

# Tipos de cargo
TIPO_OPERACIONAL = "OPERACIONAL"
TIPO_GESTAO = "GESTAO"

# Valor especial para "sem atribuição"
NENHUM = "Nenhum"


# =============================================================================
# DATACLASSES
# =============================================================================
@dataclass
class ColaboradorAtribuido:
    """Representa um colaborador atribuído a um item específico."""
    
    nome: str
    cargo: str
    tipo_cargo: str = ""  # OPERACIONAL ou GESTAO
    fator_split: float = 1.0  # 1.0 = 100%
    fonte: str = ""  # "AC" (Análise Comercial) ou "REGRAS_COMISSAO_V2"
    
    def __post_init__(self):
        # Normalizar split para decimal se veio como porcentagem
        if self.fator_split > 1:
            self.fator_split = self.fator_split / 100.0


@dataclass
class ResultadoAtribuicao:
    """Resultado da busca de atribuições para um item."""
    
    colaboradores: List[ColaboradorAtribuido] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    
    @property
    def sucesso(self) -> bool:
        return len(self.erros) == 0
    
    def adicionar_colaborador(self, colab: ColaboradorAtribuido) -> None:
        self.colaboradores.append(colab)
    
    def adicionar_erro(self, msg: str) -> None:
        self.erros.append(msg)
    
    def adicionar_aviso(self, msg: str) -> None:
        self.avisos.append(msg)


# =============================================================================
# SERVIÇO PRINCIPAL (Simplificado - Sem ATRIBUICOES_V2)
# =============================================================================
class AtribuicaoServiceV2:
    """Serviço para resolver atribuições de colaboradores por item da AC.
    
    NOVA VERSÃO: Usa apenas REGRAS_COMISSAO_V2, COLABORADORES_V2 e CARGOS_V2.
    Não depende mais de ATRIBUICOES_V2.
    
    Uso:
        service = AtribuicaoServiceV2(df_regras, df_colaboradores, df_cargos)
        resultado = service.get_colaboradores_para_item(item_ac)
    """

    def __init__(
        self, 
        df_regras: pd.DataFrame,
        df_colaboradores: pd.DataFrame,
        df_cargos: pd.DataFrame
    ):
        """Inicializa o serviço.
        
        Args:
            df_regras: DataFrame da aba REGRAS_COMISSAO_V2
            df_colaboradores: DataFrame da aba COLABORADORES_V2
            df_cargos: DataFrame da aba CARGOS_V2
        """
        self._df_regras = self._normalizar_regras(df_regras)
        self._df_colaboradores = self._normalizar_colaboradores(df_colaboradores)
        self._cargos_tipo = self._build_cargos_tipo(df_cargos)
        
        # Índice de regras por colaborador para busca rápida
        self._regras_por_colaborador = self._build_index_regras()
    
    def _normalizar_regras(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de regras."""
        df = df.copy()
        df.columns = df.columns.str.strip()
        
        # Normalizar valores de hierarquia
        for col in HIER_COLS_REGRAS:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        
        # Normalizar nome do colaborador
        if "colaborador" in df.columns:
            df["colaborador"] = df["colaborador"].fillna("").astype(str).str.strip()
        
        return df
    
    def _normalizar_colaboradores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de colaboradores."""
        df = df.copy()
        df.columns = df.columns.str.strip()
        
        # Identificar coluna de nome
        nome_col = "nome_colaborador" if "nome_colaborador" in df.columns else "colaborador"
        
        if nome_col in df.columns:
            df["nome"] = df[nome_col].fillna("").astype(str).str.strip()
        
        if "cargo" in df.columns:
            df["cargo"] = df["cargo"].fillna("").astype(str).str.strip()
        
        # Normalizar fator_split (default = 100)
        if "fator_split" in df.columns:
            df["fator_split"] = pd.to_numeric(df["fator_split"], errors="coerce").fillna(100)
        else:
            df["fator_split"] = 100
        
        return df
    
    def _build_cargos_tipo(self, df: pd.DataFrame) -> Dict[str, str]:
        """Constrói mapeamento de cargo -> tipo (OPERACIONAL/GESTAO)."""
        df = df.copy()
        df.columns = df.columns.str.strip()
        
        tipo_map = {}
        
        # Identificar coluna de nome do cargo
        nome_col = "nome_cargo" if "nome_cargo" in df.columns else "cargo"
        
        for _, row in df.iterrows():
            cargo = str(row.get(nome_col, "") or "").strip()
            tipo = str(row.get("tipo", "") or "").strip().upper()
            
            if cargo:
                # Se tipo não definido, inferir pelo nome do cargo
                if not tipo:
                    if "consultor" in cargo.lower() or "representante" in cargo.lower():
                        tipo = TIPO_OPERACIONAL
                    else:
                        tipo = TIPO_GESTAO
                
                tipo_map[cargo.lower()] = tipo
        
        logger.debug(f"Mapeamento de cargos: {tipo_map}")
        return tipo_map
    
    def _build_index_regras(self) -> Dict[str, List[pd.Series]]:
        """Constrói índice de regras por colaborador."""
        index = {}
        
        for _, row in self._df_regras.iterrows():
            colaborador = row.get("colaborador", "")
            if colaborador:
                colaborador_lower = colaborador.lower()
                if colaborador_lower not in index:
                    index[colaborador_lower] = []
                index[colaborador_lower].append(row)
        
        logger.debug(f"Índice de regras criado para {len(index)} colaboradores")
        return index
    
    def _get_tipo_cargo(self, cargo: str) -> str:
        """Retorna o tipo do cargo (OPERACIONAL ou GESTAO)."""
        cargo_lower = cargo.lower().strip()
        return self._cargos_tipo.get(cargo_lower, TIPO_GESTAO)
    
    def _get_colaborador_info(self, nome: str) -> Optional[Tuple[str, str, float]]:
        """Retorna informações do colaborador (cargo, tipo, fator_split).
        
        Returns:
            Tupla (cargo, tipo_cargo, fator_split) ou None se não encontrado
        """
        nome_lower = nome.lower().strip()
        
        for _, row in self._df_colaboradores.iterrows():
            colab_nome = str(row.get("nome", "") or "").strip().lower()
            if colab_nome == nome_lower:
                cargo = str(row.get("cargo", "") or "").strip()
                tipo = self._get_tipo_cargo(cargo)
                split = float(row.get("fator_split", 100) or 100)
                return (cargo, tipo, split)
        
        return None
    
    def get_colaboradores_para_item(
        self,
        item: pd.Series,
    ) -> ResultadoAtribuicao:
        """Identifica todos os colaboradores que recebem comissão para um item.
        
        Args:
            item: Linha da Análise Comercial
            
        Returns:
            ResultadoAtribuicao com lista de colaboradores e possíveis erros
        """
        resultado = ResultadoAtribuicao()
        
        # Extrair hierarquia do item
        hierarquia_item = self._extrair_hierarquia_item(item)
        
        # 1. Processar OPERACIONAL (da AC, validado contra REGRAS_COMISSAO_V2)
        self._processar_operacional(item, hierarquia_item, resultado)
        
        # 2. Processar GESTÃO (de REGRAS_COMISSAO_V2)
        self._processar_gestao(hierarquia_item, resultado)
        
        return resultado
    
    def _extrair_hierarquia_item(self, item: pd.Series) -> Tuple[str, ...]:
        """Extrai hierarquia de um item da Análise Comercial.
        
        Returns:
            Tupla (linha, grupo, subgrupo, tipo_mercadoria, fabricante)
        """
        return (
            str(item.get(COL_AC_LINHA, "") or "").strip(),
            str(item.get(COL_AC_GRUPO, "") or "").strip(),
            str(item.get(COL_AC_SUBGRUPO, "") or "").strip(),
            str(item.get(COL_AC_TIPO_MERCADORIA, "") or "").strip(),
            str(item.get(COL_AC_FABRICANTE, "") or "").strip(),
        )
    
    def _colaborador_tem_regra_para_hierarquia(
        self, 
        nome: str, 
        hierarquia: Tuple[str, ...]
    ) -> bool:
        """Verifica se colaborador tem regra aplicável à hierarquia.
        
        Args:
            nome: Nome do colaborador
            hierarquia: (linha, grupo, subgrupo, tipo_mercadoria, fabricante)
            
        Returns:
            True se tem regra aplicável
        """
        nome_lower = nome.lower().strip()
        
        if nome_lower not in self._regras_por_colaborador:
            return False
        
        regras = self._regras_por_colaborador[nome_lower]
        
        for regra in regras:
            if self._regra_aplica_a_hierarquia(regra, hierarquia):
                return True
        
        return False
    
    def _regra_aplica_a_hierarquia(
        self, 
        regra: pd.Series, 
        hierarquia: Tuple[str, ...]
    ) -> bool:
        """Verifica se uma regra se aplica à hierarquia.
        
        Regras:
        - Campo vazio na regra = wildcard (aceita qualquer valor)
        - Campo com placeholder [Todos os ...] = wildcard
        - Campo preenchido deve coincidir com o item
        """
        wildcard_patterns = ["", "[todos", "[todas", "[all"]
        
        for i, col in enumerate(HIER_COLS_REGRAS):
            valor_regra = str(regra.get(col, "") or "").strip()
            valor_item = hierarquia[i]
            
            # Verificar se é wildcard
            is_wildcard = (
                valor_regra == "" or 
                any(valor_regra.lower().startswith(p) for p in wildcard_patterns)
            )
            
            if is_wildcard:
                # Wildcard - aceita qualquer valor
                continue
            elif valor_regra.lower() == valor_item.lower():
                # Match específico
                continue
            else:
                # Incompatível
                return False
        
        return True
    
    def _processar_operacional(
        self,
        item: pd.Series,
        hierarquia: Tuple[str, ...],
        resultado: ResultadoAtribuicao
    ) -> None:
        """Processa colaboradores OPERACIONAL (Consultor Interno/Externo).
        
        - Nome vem da Análise Comercial
        - DEVE ter regra em REGRAS_COMISSAO_V2 para a hierarquia
        """
        # Consultor Interno
        ci_nome = str(item.get(COL_AC_CONSULTOR_INTERNO, "") or "").strip()
        if ci_nome and ci_nome.lower() not in [NENHUM.lower(), "", "nan", "none"]:
            # Pode ter múltiplos separados por ";"
            for nome in ci_nome.split(";"):
                nome = nome.strip()
                if not nome:
                    continue
                
                # Verificar se tem regra para a hierarquia
                if not self._colaborador_tem_regra_para_hierarquia(nome, hierarquia):
                    resultado.adicionar_erro(
                        f"Consultor Interno '{nome}' (da AC) não tem regra em "
                        f"REGRAS_COMISSAO_V2 para hierarquia: {hierarquia}"
                    )
                    continue
                
                # Obter info do colaborador
                info = self._get_colaborador_info(nome)
                if info:
                    cargo, tipo, split = info
                else:
                    cargo = "Consultor Interno"
                    tipo = TIPO_OPERACIONAL
                    split = 100
                
                resultado.adicionar_colaborador(ColaboradorAtribuido(
                    nome=nome,
                    cargo=cargo,
                    tipo_cargo=tipo,
                    fator_split=split,
                    fonte="AC"
                ))
        
        # Consultor Externo (Representante-pedido)
        ce_nome = str(item.get(COL_AC_REPRESENTANTE, "") or "").strip()
        if ce_nome and ce_nome.lower() not in [NENHUM.lower(), "", "nan", "none"]:
            for nome in ce_nome.split(";"):
                nome = nome.strip()
                if not nome:
                    continue
                
                # Verificar se tem regra para a hierarquia
                if not self._colaborador_tem_regra_para_hierarquia(nome, hierarquia):
                    resultado.adicionar_erro(
                        f"Consultor Externo '{nome}' (da AC) não tem regra em "
                        f"REGRAS_COMISSAO_V2 para hierarquia: {hierarquia}"
                    )
                    continue
                
                # Obter info do colaborador
                info = self._get_colaborador_info(nome)
                if info:
                    cargo, tipo, split = info
                else:
                    cargo = "Consultor Externo"
                    tipo = TIPO_OPERACIONAL
                    split = 100
                
                resultado.adicionar_colaborador(ColaboradorAtribuido(
                    nome=nome,
                    cargo=cargo,
                    tipo_cargo=tipo,
                    fator_split=split,
                    fonte="AC"
                ))
    
    def _processar_gestao(
        self,
        hierarquia: Tuple[str, ...],
        resultado: ResultadoAtribuicao
    ) -> None:
        """Processa colaboradores de GESTÃO via REGRAS_COMISSAO_V2.
        
        Busca todos os colaboradores do tipo GESTAO que têm regra aplicável
        à hierarquia do item.
        """
        # Set para evitar duplicatas (nomes de operacionais já adicionados)
        nomes_operacionais: Set[str] = {
            c.nome.lower() for c in resultado.colaboradores if c.tipo_cargo == TIPO_OPERACIONAL
        }
        
        colaboradores_adicionados: Set[str] = set()
        
        # Para cada colaborador em COLABORADORES_V2
        for _, row in self._df_colaboradores.iterrows():
            nome = str(row.get("nome", "") or "").strip()
            cargo = str(row.get("cargo", "") or "").strip()
            split = float(row.get("fator_split", 100) or 100)
            
            if not nome:
                continue
            
            # Verificar se é cargo de GESTÃO
            tipo = self._get_tipo_cargo(cargo)
            if tipo != TIPO_GESTAO:
                continue
            
            # Verificar se já foi adicionado (evitar duplicata)
            if nome.lower() in colaboradores_adicionados:
                continue
            
            # Verificar se tem regra para a hierarquia
            if self._colaborador_tem_regra_para_hierarquia(nome, hierarquia):
                resultado.adicionar_colaborador(ColaboradorAtribuido(
                    nome=nome,
                    cargo=cargo,
                    tipo_cargo=tipo,
                    fator_split=split,
                    fonte="REGRAS_COMISSAO_V2"
                ))
                colaboradores_adicionados.add(nome.lower())
        
        if not any(c.tipo_cargo == TIPO_GESTAO for c in resultado.colaboradores):
            resultado.adicionar_aviso(
                f"Nenhum colaborador de GESTÃO encontrado com regra para hierarquia: {hierarquia}"
            )


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def criar_servico_atribuicao(config_path: str = "config/REGRAS_COMISSOES_V2.xlsx") -> AtribuicaoServiceV2:
    """Factory function para criar serviço de atribuições.
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Instância de AtribuicaoServiceV2
    """
    df_regras = pd.read_excel(config_path, sheet_name="REGRAS_COMISSAO_V2")
    df_colaboradores = pd.read_excel(config_path, sheet_name="COLABORADORES_V2")
    df_cargos = pd.read_excel(config_path, sheet_name="CARGOS_V2")
    
    return AtribuicaoServiceV2(df_regras, df_colaboradores, df_cargos)
