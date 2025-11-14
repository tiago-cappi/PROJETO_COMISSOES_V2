"""
Agrega resultados de reconciliações para geração de saída.
"""

from typing import Dict, List

import pandas as pd


class ReconciliacaoAggregator:
    """
    Agrega e formata resultados de reconciliações.
    """

    def __init__(self) -> None:
        """Inicializa o agregador."""

    def criar_dataframe_reconciliacoes(
        self, todas_reconciliacoes: List[Dict]
    ) -> pd.DataFrame:
        """
        Cria DataFrame formatado para a aba RECONCILIACOES.

        Args:
            todas_reconciliacoes: Lista com todas as reconciliações calculadas

        Returns:
            DataFrame formatado
        """
        if not todas_reconciliacoes:
            # Retornar DataFrame vazio com colunas esperadas
            return pd.DataFrame(
                columns=[
                    "processo",
                    "colaborador",
                    "tcmp",
                    "fcmp",
                    "comissao_adiantada_fc_1",
                    "comissao_deveria_fc_real",
                    "diferenca_fc",
                    "ajuste_reconciliacao",
                    "mes_faturamento",
                ]
            )

        df = pd.DataFrame(todas_reconciliacoes)

        # Ordenar por processo e colaborador
        if {"processo", "colaborador"}.issubset(df.columns):
            df = df.sort_values(["processo", "colaborador"])

        # Formatar colunas numéricas (apenas arredondar, sem mudar tipo)
        colunas_numericas = [
            "tcmp",
            "fcmp",
            "comissao_adiantada_fc_1",
            "comissao_deveria_fc_real",
            "diferenca_fc",
            "ajuste_reconciliacao",
        ]
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = df[col].astype(float).round(6)

        return df

    def criar_resumo_por_processo(
        self, todas_reconciliacoes: List[Dict]
    ) -> pd.DataFrame:
        """
        Cria resumo de reconciliações agrupado por processo.

        Args:
            todas_reconciliacoes: Lista com todas as reconciliações

        Returns:
            DataFrame com resumo por processo
        """
        if not todas_reconciliacoes:
            return pd.DataFrame()

        df = pd.DataFrame(todas_reconciliacoes)

        if "processo" not in df.columns:
            return pd.DataFrame()

        # Agrupar por processo
        agregacoes = {
            "comissao_adiantada_fc_1": "sum",
            "comissao_deveria_fc_real": "sum",
            "ajuste_reconciliacao": "sum",
        }
        if "mes_faturamento" in df.columns:
            agregacoes["mes_faturamento"] = "first"

        resumo = df.groupby("processo").agg(agregacoes).reset_index()

        resumo = resumo.rename(
            columns={
                "comissao_adiantada_fc_1": "total_comissoes_adiantadas",
                "comissao_deveria_fc_real": "total_comissoes_ajustadas",
                "ajuste_reconciliacao": "saldo_reconciliacao",
            }
        )

        return resumo


