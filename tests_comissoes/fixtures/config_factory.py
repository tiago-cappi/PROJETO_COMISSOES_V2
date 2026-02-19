"""
Fábricas de DataFrames de configuração para testes.

Cria DataFrames in-memory que simulam as abas de REGRAS_COMISSOES.xlsx
sem precisar de arquivo no disco.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from tests_comissoes.fixtures.empresa_constants import (
    COLABORADORES,
    FC_ESCADA_CONFIGS,
    LINHAS,
    PARAMS_DEFAULT,
    PESOS_FC_POR_CARGO,
    TIPOS_MERCADORIA,
)


class ConfigFactory:
    """Fábrica de DataFrames de configuração (abas de REGRAS_COMISSOES.xlsx)."""

    # ------------------------------------------------------------------
    # PARAMS
    # ------------------------------------------------------------------
    @staticmethod
    def criar_params(overrides: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Cria DataFrame da aba PARAMS."""
        params = {**PARAMS_DEFAULT}
        if overrides:
            params.update(overrides)
        rows = [{"parametro": k, "valor": v} for k, v in params.items()]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # COLABORADORES
    # ------------------------------------------------------------------
    @staticmethod
    def criar_colaboradores(
        subset: Optional[List[str]] = None,
        extras: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba COLABORADORES.

        Args:
            subset: Lista de nomes canônicos a incluir. None = todos.
            extras: Dicts adicionais com {nome_colaborador, cargo, ...}.
        """
        rows = []
        source = COLABORADORES
        if subset:
            source = {k: v for k, v in COLABORADORES.items() if k in subset}

        for i, (nome, info) in enumerate(source.items(), start=1):
            rows.append({
                "id_colaborador": i,
                "nome_colaborador": nome,
                "cargo": info["cargo"],
            })

        if extras:
            for j, extra in enumerate(extras, start=len(rows) + 1):
                extra.setdefault("id_colaborador", j)
                rows.append(extra)

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # CARGOS
    # ------------------------------------------------------------------
    @staticmethod
    def criar_cargos(
        cargos: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba CARGOS."""
        if cargos is None:
            cargos = [
                {"nome_cargo": "Gerente Linha", "tipo_cargo": "Gestão"},
                {"nome_cargo": "Coordenador", "tipo_cargo": "Gestão"},
                {"nome_cargo": "Diretor", "tipo_cargo": "Gestão"},
                {"nome_cargo": "Consultor Interno", "tipo_cargo": "Operacional"},
                {"nome_cargo": "Consultor Externo", "tipo_cargo": "Operacional"},
            ]
        return pd.DataFrame(cargos)

    # ------------------------------------------------------------------
    # PESOS_METAS
    # ------------------------------------------------------------------
    @staticmethod
    def criar_pesos_metas(
        overrides_por_cargo: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba PESOS_METAS.

        Args:
            overrides_por_cargo: Dict {cargo: {componente: peso}} para substituir defaults.
        """
        rows = []
        for cargo, pesos in PESOS_FC_POR_CARGO.items():
            row = {"cargo": cargo}
            row.update(pesos)
            if overrides_por_cargo and cargo in overrides_por_cargo:
                row.update(overrides_por_cargo[cargo])
            rows.append(row)
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # CONFIG_COMISSAO
    # ------------------------------------------------------------------
    @staticmethod
    def criar_config_comissao(
        regras: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba CONFIG_COMISSAO.

        Args:
            regras: Lista de dicts com {linha, grupo, subgrupo, tipo_mercadoria,
                    cargo, taxa_rateio_maximo_pct, fatia_cargo_pct}.
                    Se None, cria regras-padrão para Hidrologia/Produto.
        """
        if regras is None:
            regras = []
            # Regra específica: Hidrologia / Sonda Serie EXO / EXO / Produto
            for cargo, fatia in [
                ("Gerente Linha", 40), ("Coordenador", 25),
                ("Diretor", 10), ("Consultor Interno", 20),
                ("Consultor Externo", 5),
            ]:
                regras.append({
                    "linha": "Hidrologia",
                    "grupo": "Sonda Serie EXO",
                    "subgrupo": "EXO",
                    "tipo_mercadoria": "Produto",
                    "cargo": cargo,
                    "taxa_rateio_maximo_pct": 3.0,
                    "fatia_cargo_pct": fatia,
                })
            # Regra fallback global (legacy)
            for cargo, fatia in [
                ("Gerente Linha", 35), ("Coordenador", 25),
                ("Diretor", 10), ("Consultor Interno", 25),
                ("Consultor Externo", 5),
            ]:
                regras.append({
                    "linha": "__legacy__",
                    "grupo": np.nan,
                    "subgrupo": np.nan,
                    "tipo_mercadoria": "__legacy__",
                    "cargo": cargo,
                    "taxa_rateio_maximo_pct": 2.5,
                    "fatia_cargo_pct": fatia,
                })
        return pd.DataFrame(regras)

    # ------------------------------------------------------------------
    # METAS_APLICACAO
    # ------------------------------------------------------------------
    @staticmethod
    def criar_metas_aplicacao(
        metas: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba METAS_APLICACAO."""
        if metas is None:
            metas = [
                {"linha": "Hidrologia", "grupo": "", "subgrupo": "", "tipo_mercadoria": "",
                 "tipo_meta": "faturamento", "valor_meta": 500_000},
                {"linha": "Hidrologia", "grupo": "", "subgrupo": "", "tipo_mercadoria": "",
                 "tipo_meta": "conversao", "valor_meta": 300_000},
                {"linha": "SSO", "grupo": "", "subgrupo": "", "tipo_mercadoria": "",
                 "tipo_meta": "faturamento", "valor_meta": 400_000},
                {"linha": "SSO", "grupo": "", "subgrupo": "", "tipo_mercadoria": "",
                 "tipo_meta": "conversao", "valor_meta": 250_000},
            ]
        return pd.DataFrame(metas)

    # ------------------------------------------------------------------
    # METAS_INDIVIDUAIS
    # ------------------------------------------------------------------
    @staticmethod
    def criar_metas_individuais(
        metas: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba METAS_INDIVIDUAIS."""
        if metas is None:
            metas = [
                {"colaborador": "Samanta Silva", "tipo_meta": "faturamento", "valor_meta": 100_000},
                {"colaborador": "Samanta Silva", "tipo_meta": "conversao", "valor_meta": 80_000},
                {"colaborador": "Rafaela Meirelles", "tipo_meta": "faturamento", "valor_meta": 120_000},
                {"colaborador": "Rafaela Meirelles", "tipo_meta": "conversao", "valor_meta": 90_000},
            ]
        return pd.DataFrame(metas)

    # ------------------------------------------------------------------
    # META_RENTABILIDADE
    # ------------------------------------------------------------------
    @staticmethod
    def criar_meta_rentabilidade(
        metas: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba META_RENTABILIDADE."""
        if metas is None:
            metas = [
                {"linha": "Hidrologia", "grupo": "Sonda Serie EXO", "subgrupo": "EXO",
                 "tipo_mercadoria": "Produto", "meta_rentabilidade_alvo_pct": 0.12},
                {"linha": "SSO", "grupo": "Monitor de Gases Fixo", "subgrupo": "RAE",
                 "tipo_mercadoria": "Produto", "meta_rentabilidade_alvo_pct": 0.15},
            ]
        return pd.DataFrame(metas)

    # ------------------------------------------------------------------
    # METAS_FORNECEDORES
    # ------------------------------------------------------------------
    @staticmethod
    def criar_metas_fornecedores(
        metas: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba METAS_FORNECEDORES."""
        if metas is None:
            metas = [
                {"linha": "Hidrologia", "fornecedor": "YSI", "meta_anual": 200_000, "moeda": "USD"},
                {"linha": "SSO", "fornecedor": "Thermo", "meta_anual": 150_000, "moeda": "USD"},
                {"linha": "SSO", "fornecedor": "ION", "meta_anual": 80_000, "moeda": "GBP"},
            ]
        return pd.DataFrame(metas)

    # ------------------------------------------------------------------
    # ATRIBUICOES (Wide)
    # ------------------------------------------------------------------
    @staticmethod
    def criar_atribuicoes_wide(
        rows: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba ATRIBUICOES em formato Wide.

        Args:
            rows: Lista de dicts com {linha, grupo, subgrupo, tipo_mercadoria,
                  "Gerente Linha 1", "Gerente Linha 2", "Coordenador 1", ...}.
        """
        if rows is None:
            rows = [
                {
                    "linha": "Hidrologia",
                    "grupo": "[Todos os grupos]",
                    "subgrupo": "",
                    "tipo_mercadoria": "",
                    "Gerente Linha 1": "Andrey Andrade",
                    "Gerente Linha 2": None,
                    "Coordenador 1": "Rosana Martins",
                    "Coordenador 2": None,
                    "Diretor": "Carlos Diretor",
                },
                {
                    "linha": "SSO",
                    "grupo": "[Todos os grupos]",
                    "subgrupo": "",
                    "tipo_mercadoria": "",
                    "Gerente Linha 1": "Dener Martins",
                    "Gerente Linha 2": None,
                    "Coordenador 1": "Rosana Martins",
                    "Coordenador 2": None,
                    "Diretor": "Carlos Diretor",
                },
            ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # FC_ESCADA_CARGOS
    # ------------------------------------------------------------------
    @staticmethod
    def criar_fc_escada_cargos(
        overrides: Optional[Dict[str, Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba FC_ESCADA_CARGOS."""
        configs = {**FC_ESCADA_CONFIGS}
        if overrides:
            configs.update(overrides)
        rows = []
        for cargo, cfg in configs.items():
            rows.append({
                "cargo": cargo,
                "modo": cfg["modo"],
                "num_degraus": cfg["num_degraus"],
                "piso_pct": cfg["piso_pct"],
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # ALIASES
    # ------------------------------------------------------------------
    @staticmethod
    def criar_aliases(
        extra: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba ALIASES."""
        from tests_comissoes.fixtures.empresa_constants import ALIASES
        rows = [{"alias": k, "padrao": v} for k, v in ALIASES.items()]
        if extra:
            for alias, padrao in extra.items():
                rows.append({"alias": alias, "padrao": padrao})
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # CROSS_SELLING
    # ------------------------------------------------------------------
    @staticmethod
    def criar_cross_selling(
        consultores: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """Cria DataFrame da aba CROSS_SELLING."""
        if consultores is None:
            consultores = [
                {"colaborador": "André Camargo", "taxa_cross_selling_pct": 1.0},
                {"colaborador": "Leonardo Carmo", "taxa_cross_selling_pct": 0.8},
                {"colaborador": "Mateus Machado", "taxa_cross_selling_pct": 1.2},
            ]
        return pd.DataFrame(consultores)

    # ------------------------------------------------------------------
    # BUNDLE: config completa
    # ------------------------------------------------------------------
    @classmethod
    def criar_config_completa(cls, **kwargs) -> Dict[str, pd.DataFrame]:
        """Cria todas as abas de configuração de uma vez.

        Returns:
            Dict com chaves iguais às do config_loader:
            CONFIG_COMISSAO, COLABORADORES, CARGOS, PESOS_METAS, etc.
        """
        return {
            "CONFIG_COMISSAO": cls.criar_config_comissao(kwargs.get("regras")),
            "COLABORADORES": cls.criar_colaboradores(kwargs.get("subset_colabs")),
            "CARGOS": cls.criar_cargos(kwargs.get("cargos")),
            "PESOS_METAS": cls.criar_pesos_metas(kwargs.get("overrides_pesos")),
            "METAS_APLICACAO": cls.criar_metas_aplicacao(kwargs.get("metas_aplicacao")),
            "METAS_INDIVIDUAIS": cls.criar_metas_individuais(kwargs.get("metas_individuais")),
            "META_RENTABILIDADE": cls.criar_meta_rentabilidade(kwargs.get("meta_rentab")),
            "METAS_FORNECEDORES": cls.criar_metas_fornecedores(kwargs.get("metas_fornecedores")),
            "ATRIBUICOES": cls.criar_atribuicoes_wide(kwargs.get("atribuicoes")),
            "FC_ESCADA_CARGOS": cls.criar_fc_escada_cargos(kwargs.get("escada_overrides")),
            "ALIASES": cls.criar_aliases(kwargs.get("extra_aliases")),
            "CROSS_SELLING": cls.criar_cross_selling(kwargs.get("cross_selling")),
            "PARAMS": cls.criar_params(kwargs.get("params_overrides")),
        }
