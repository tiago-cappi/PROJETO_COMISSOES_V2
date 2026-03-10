"""
Identifica colaboradores envolvidos em um processo que recebem por recebimento.

Refatorado para usar REGRAS_ATRIBUICAO (formato Long) via engine unificado.
"""

import pandas as pd
from typing import List, Dict, Optional, Set

from src.regras.atribuicao_engine import buscar_regras_item, HIERARCHY_FIELDS


class IdentificadorColaboradores:
    """
    Identifica todos os colaboradores envolvidos em um processo
    que recebem comissão por recebimento.
    """

    def __init__(
        self,
        df_analise_comercial: pd.DataFrame,
        colaboradores_df: pd.DataFrame,
        df_regras_atribuicao: pd.DataFrame,
        recebe_por_recebimento_ids: Set[str],
    ):
        """
        Inicializa o identificador.

        Args:
            df_analise_comercial: DataFrame da Análise Comercial Completa.
            colaboradores_df: DataFrame de colaboradores (com cargo).
            df_regras_atribuicao: DataFrame REGRAS_ATRIBUICAO preprocessado.
            recebe_por_recebimento_ids: Set com nomes de colaboradores que
                recebem por recebimento.
        """
        self.df_comercial = df_analise_comercial
        self.colaboradores_df = colaboradores_df
        self.df_regras = df_regras_atribuicao
        self.recebe_por_recebimento_ids = recebe_por_recebimento_ids

    def identificar_colaboradores(self, processo: str) -> List[Dict[str, str]]:
        """Identifica colaboradores envolvidos num processo que recebem por recebimento.

        Args:
            processo: ID do processo.

        Returns:
            Lista de dicts ``{'nome': str, 'cargo': str}``.
        """
        processo = str(processo).strip()

        # 1. Buscar todos os itens do processo
        if self.df_comercial.empty:
            return []

        proc_col = self._encontrar_coluna(["processo", "Processo", "PROCESSO"])
        if not proc_col:
            return []

        itens = self.df_comercial[
            self.df_comercial[proc_col].astype(str).str.strip() == processo
        ]
        if itens.empty:
            return []

        # 2. Identificar colaboradores operacionais (Consultor Interno, Representante-pedido)
        colaboradores_operacionais: Set[str] = set()

        col_consultor = self._encontrar_coluna_item(
            itens, ["Consultor Interno", "consultor interno", "CONSULTOR INTERNO"]
        )
        col_representante = self._encontrar_coluna_item(
            itens, ["Representante-pedido", "representante-pedido", "REPRESENTANTE-PEDIDO"]
        )

        if col_consultor:
            colaboradores_operacionais.update(
                itens[col_consultor].dropna().astype(str).str.strip().unique()
            )
        if col_representante:
            colaboradores_operacionais.update(
                itens[col_representante].dropna().astype(str).str.strip().unique()
            )

        # 3. Identificar colaboradores de gestão (via REGRAS_ATRIBUICAO — busca por especificidade)
        colaboradores_gestao: Set[str] = set()

        if not self.df_regras.empty and not itens.empty:
            primeiro_item = itens.iloc[0]
            contexto = self._construir_contexto(primeiro_item)

            regras_encontradas = buscar_regras_item(self.df_regras, contexto)
            for entrada in regras_encontradas:
                nome = entrada.get("colaborador", "")
                if nome:
                    colaboradores_gestao.add(nome)

        # 4. Combinar todos os colaboradores
        todos = colaboradores_operacionais.union(colaboradores_gestao)

        # 5. Filtrar apenas os que recebem por recebimento
        colaboradores_filtrados: List[Dict[str, str]] = []
        vistos: Set[tuple] = set()

        for nome in todos:
            if not nome or nome.lower() in ("", "nan", "none"):
                continue

            nome_normalizado = nome.strip()
            if nome_normalizado not in self.recebe_por_recebimento_ids:
                continue

            cargo = self._obter_cargo(nome_normalizado)
            chave = (nome_normalizado.lower(), (cargo or "N/A").lower())
            if chave in vistos:
                continue
            vistos.add(chave)

            colaboradores_filtrados.append(
                {"nome": nome_normalizado, "cargo": cargo or "N/A"}
            )

        return colaboradores_filtrados

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _construir_contexto(item: pd.Series) -> Dict[str, str]:
        """Constrói dict de contexto hierárquico a partir de uma linha da Análise Comercial."""
        col_map = {
            "linha": "Negócio",
            "grupo": "Grupo",
            "subgrupo": "Subgrupo",
            "tipo_mercadoria": "Tipo de Mercadoria",
            "fabricante": "Fabricante",
            "aplicacao": "Aplicação Mat./Serv.",
        }
        return {
            field: str(item.get(col_map[field], "")).strip()
            for field in HIERARCHY_FIELDS
        }

    def _obter_cargo(self, nome: str) -> Optional[str]:
        """Obtém o cargo de um colaborador."""
        if self.colaboradores_df.empty or not nome:
            return None

        mask = (
            self.colaboradores_df["nome_colaborador"].astype(str).str.strip()
            == nome.strip()
        )
        row = self.colaboradores_df[mask]

        if not row.empty and "cargo" in row.columns:
            return str(row.iloc[0]["cargo"]).strip()
        return None

    def _encontrar_coluna(self, nomes_possiveis: List[str]) -> Optional[str]:
        """Encontra uma coluna no DataFrame comercial."""
        if self.df_comercial.empty:
            return None

        colunas_df = {
            col.lower().strip().replace("\ufeff", ""): col
            for col in self.df_comercial.columns
        }
        for nome in nomes_possiveis:
            if nome.lower().strip() in colunas_df:
                return colunas_df[nome.lower().strip()]
        return None

    @staticmethod
    def _encontrar_coluna_item(
        df_item: pd.DataFrame, nomes_possiveis: List[str]
    ) -> Optional[str]:
        """Encontra uma coluna no DataFrame de itens."""
        if df_item.empty:
            return None

        colunas_df = {
            str(col).lower().strip().replace("\ufeff", ""): col
            for col in df_item.columns
        }
        for nome in nomes_possiveis:
            if nome.lower().strip() in colunas_df:
                return colunas_df[nome.lower().strip()]
        return None


