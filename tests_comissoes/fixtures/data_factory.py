"""
Fábrica de DataFrames de dados de entrada para testes.

Simula os dados de FATURADOS, CONVERSÕES, FATURADOS_YTD,
rentabilidade e devoluções sem depender de arquivos no disco.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class DataFactory:
    """Fábrica de DataFrames de dados de entrada (dados_entrada/)."""

    # ------------------------------------------------------------------
    # ITEM FATURADO (uma linha de FATURADOS.xlsx)
    # ------------------------------------------------------------------
    @staticmethod
    def criar_item_faturado(
        processo: str = "PROC-001",
        valor_realizado: float = 100_000.0,
        valor_orcado: float = 100_000.0,
        linha: str = "Hidrologia",
        grupo: str = "Sonda Serie EXO",
        subgrupo: str = "EXO",
        tipo_mercadoria: str = "Produto",
        consultor_interno: str = "Samanta Silva",
        representante: str = "",
        gerente_comercial_pedido: str = "",
        fabricante: str = "YSI",
        numero_nf: str = "NF-001",
        cliente: str = "Cliente Teste",
        cod_produto: str = "PROD-001",
        descricao: str = "Sonda EXO2 Multiparâmetro",
        **extras,
    ) -> Dict[str, Any]:
        """Cria um dict representando um item faturado."""
        item = {
            "Processo": processo,
            "Valor Realizado": valor_realizado,
            "Valor Orçado": valor_orcado,
            "Negócio": linha,
            "Grupo": grupo,
            "Subgrupo": subgrupo,
            "Tipo de Mercadoria": tipo_mercadoria,
            "Consultor Interno": consultor_interno,
            "Representante-pedido": representante,
            "Gerente Comercial-Pedido": gerente_comercial_pedido,
            "Fabricante": fabricante,
            "Numero NF": numero_nf,
            "Nome Cliente": cliente,
            "Código Produto": cod_produto,
            "Descrição Produto": descricao,
            "Status Processo": "FATURADO",
        }
        item.update(extras)
        return item

    # ------------------------------------------------------------------
    # DataFrame de FATURADOS completo
    # ------------------------------------------------------------------
    @classmethod
    def criar_faturados(
        cls,
        itens: Optional[List[Dict]] = None,
        n_itens: int = 1,
        **defaults,
    ) -> pd.DataFrame:
        """Cria DataFrame simulando FATURADOS.xlsx.

        Args:
            itens: Lista de dicts. Cada dict é passado a criar_item_faturado.
            n_itens: Se itens=None, cria N itens com defaults.
            defaults: Kwargs padrão para todos os itens.
        """
        if itens is None:
            itens = []
            for i in range(n_itens):
                d = {**defaults}
                d.setdefault("processo", f"PROC-{i+1:03d}")
                d.setdefault("numero_nf", f"NF-{i+1:03d}")
                d.setdefault("cod_produto", f"PROD-{i+1:03d}")
                itens.append(d)
        rows = [cls.criar_item_faturado(**item) for item in itens]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # DataFrame de CONVERSÕES
    # ------------------------------------------------------------------
    @staticmethod
    def criar_conversoes(
        itens: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame simulando CONVERSÕES.xlsx."""
        if itens is None:
            itens = [
                {
                    "Processo": "CONV-001",
                    "Valor Orçado": 80_000,
                    "Negócio": "Hidrologia",
                    "Consultor Interno": "Samanta Silva",
                    "Representante-pedido": "",
                    "Status Processo": "PENDENTE",
                },
            ]
        return pd.DataFrame(itens)

    # ------------------------------------------------------------------
    # DataFrame de FATURADOS_YTD
    # ------------------------------------------------------------------
    @staticmethod
    def criar_faturados_ytd(
        itens: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame simulando FATURADOS_YTD.xlsx."""
        if itens is None:
            itens = []
        return pd.DataFrame(itens)

    # ------------------------------------------------------------------
    # REALIZADO (dicionário pronto, como self.realizado)
    # ------------------------------------------------------------------
    @staticmethod
    def criar_realizado(
        faturamento_linha: Optional[Dict[str, float]] = None,
        conversao_linha: Optional[Dict[str, float]] = None,
        faturamento_individual: Optional[Dict[str, float]] = None,
        conversao_individual: Optional[Dict[str, float]] = None,
        rentabilidade: Optional[Dict[tuple, float]] = None,
    ) -> Dict[str, Any]:
        """Cria dict `realizado` para injetar direto em testes de FC.

        Cada chave mapeia para um pd.Series ou dict.
        """
        return {
            "faturamento_linha": pd.Series(faturamento_linha or {}),
            "conversao_linha": pd.Series(conversao_linha or {}),
            "faturamento_individual": pd.Series(faturamento_individual or {}),
            "conversao_individual": pd.Series(conversao_individual or {}),
            "rentabilidade": pd.Series(rentabilidade or {}),
        }

    # ------------------------------------------------------------------
    # DEVOLUÇÕES
    # ------------------------------------------------------------------
    @staticmethod
    def criar_devolucoes(
        itens: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame simulando Devoluções.xlsx."""
        if itens is None:
            itens = []
        return pd.DataFrame(itens)

    # ------------------------------------------------------------------
    # ANÁLISE FINANCEIRA (para recebimento)
    # ------------------------------------------------------------------
    @staticmethod
    def criar_analise_financeira(
        pagamentos: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame simulando Análise Financeira.xlsx."""
        if pagamentos is None:
            pagamentos = []
        return pd.DataFrame(pagamentos)
