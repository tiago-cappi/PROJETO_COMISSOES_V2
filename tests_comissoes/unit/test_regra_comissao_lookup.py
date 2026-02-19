"""
Testes unitários para _get_regra_comissao.

Testa o lookup hierárquico de 4 níveis que busca a regra de comissão
(taxa_rateio_maximo_pct + fatia_cargo_pct) na aba CONFIG_COMISSAO:

Nível 1: linha + grupo + subgrupo + tipo_mercadoria  (mais específico)
Nível 2: linha + grupo + tipo_mercadoria             (subgrupo NaN/__legacy__)
Nível 3: linha + tipo_mercadoria                     (grupo+subgrupo NaN/__legacy__)
Nível 4: __legacy__ + __legacy__                     (fallback global)

Todos os níveis também filtram por cargo.
"""

import pytest
import pandas as pd
import numpy as np

from calculo_comissoes import CalculoComissao
from tests_comissoes.fixtures.config_factory import ConfigFactory


# =========================================================================
# HELPERS
# =========================================================================

def _calc_minimo(regras: list = None, metas_aplicacao: list = None) -> CalculoComissao:
    """Cria uma instância mínima de CalculoComissao com apenas CONFIG_COMISSAO carregado."""
    calc = CalculoComissao.__new__(CalculoComissao)
    calc.data = {}
    calc.params = {}
    calc.validation_log = []
    calc.cache_regras = {}
    calc.legacy_token = "__legacy__"

    # Precisamos de um ValidationLogger mínimo
    class _MinimalLogger:
        def info(self, *a, **kw): pass
        def aviso(self, *a, **kw): pass
        def erro(self, *a, **kw): pass
        def log(self, *a, **kw): pass

    calc.validation_logger = _MinimalLogger()

    calc.data["CONFIG_COMISSAO"] = ConfigFactory.criar_config_comissao(regras)

    if metas_aplicacao is not None:
        calc.data["METAS_APLICACAO"] = ConfigFactory.criar_metas_aplicacao(metas_aplicacao)

    return calc


def _montar_regras_4_niveis() -> list:
    """Monta regras para testar todos os 4 níveis de fallback."""
    regras = []

    # Nível 1: Mais específico (Hidrologia/Sonda/EXO/Produto)
    for cargo, fatia in [("Gerente Linha", 40), ("Consultor Interno", 20)]:
        regras.append({
            "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
            "subgrupo": "EXO", "tipo_mercadoria": "Produto",
            "cargo": cargo, "taxa_rateio_maximo_pct": 3.0,
            "fatia_cargo_pct": fatia,
        })

    # Nível 2: linha + grupo + tipo (subgrupo NaN)
    for cargo, fatia in [("Gerente Linha", 38), ("Consultor Interno", 22)]:
        regras.append({
            "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
            "subgrupo": np.nan, "tipo_mercadoria": "Produto",
            "cargo": cargo, "taxa_rateio_maximo_pct": 2.8,
            "fatia_cargo_pct": fatia,
        })

    # Nível 3: linha + tipo (grupo e subgrupo NaN)
    for cargo, fatia in [("Gerente Linha", 35), ("Consultor Interno", 25)]:
        regras.append({
            "linha": "Hidrologia", "grupo": np.nan,
            "subgrupo": np.nan, "tipo_mercadoria": "Produto",
            "cargo": cargo, "taxa_rateio_maximo_pct": 2.5,
            "fatia_cargo_pct": fatia,
        })

    # Nível 4: fallback global (__legacy__)
    for cargo, fatia in [("Gerente Linha", 30), ("Consultor Interno", 28)]:
        regras.append({
            "linha": "__legacy__", "grupo": np.nan,
            "subgrupo": np.nan, "tipo_mercadoria": "__legacy__",
            "cargo": cargo, "taxa_rateio_maximo_pct": 2.0,
            "fatia_cargo_pct": fatia,
        })

    return regras


# =========================================================================
# TESTES: _get_regra_comissao — Hierarquia de Fallback
# =========================================================================
class TestGetRegraComissaoFallback:
    """Testa os 4 níveis de fallback do lookup de regra de comissão."""

    def test_nivel1_match_exato(self, audit):
        """Nível 1: match exato (linha+grupo+subgrupo+tipo) → taxa=3.0, fatia=40."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Nível 1 - match exato")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra = calc._get_regra_comissao(
            "Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Gerente Linha"
        )
        assert regra is not None

        audit.verificar(
            descricao="Nível 1 (específico): taxa_rateio_maximo_pct",
            formula="match: Hidro+Sonda+EXO+Produto → taxa=3.0",
            entradas={
                "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
                "subgrupo": "EXO", "tipo_mercadoria": "Produto",
            },
            esperado=3.0,
            real=regra["taxa_rateio_maximo_pct"],
            tolerancia=0.01,
        )
        audit.verificar(
            descricao="Nível 1 (específico): fatia_cargo_pct para Gerente Linha",
            formula="match exato → fatia=40",
            entradas={"cargo": "Gerente Linha"},
            esperado=40,
            real=regra["fatia_cargo_pct"],
            tolerancia=0,
        )

    def test_nivel2_sem_subgrupo(self, audit):
        """Nível 2: subgrupo diferente cai para regra com subgrupo NaN."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Nível 2 - sem subgrupo")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra = calc._get_regra_comissao(
            "Hidrologia", "Sonda Serie EXO", "EXO3", "Produto", "Gerente Linha"
        )
        assert regra is not None

        audit.verificar(
            descricao="Nível 2 (grupo+tipo): subgrupo EXO3 não encontrou nível 1",
            formula="filtro2: Hidro+Sonda+NaN+Produto → taxa=2.8",
            entradas={"subgrupo_buscado": "EXO3"},
            esperado=2.8,
            real=regra["taxa_rateio_maximo_pct"],
            tolerancia=0.01,
        )

    def test_nivel3_sem_grupo(self, audit):
        """Nível 3: grupo diferente cai para regra com grupo NaN."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Nível 3 - sem grupo")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra = calc._get_regra_comissao(
            "Hidrologia", "Medidor de Vazão Fixo", "IQ Standard", "Produto", "Gerente Linha"
        )
        assert regra is not None

        audit.verificar(
            descricao="Nível 3 (linha+tipo): grupo diferente não encontrou níveis 1-2",
            formula="filtro3: Hidro+NaN+NaN+Produto → taxa=2.5",
            entradas={"grupo_buscado": "Medidor de Vazão Fixo"},
            esperado=2.5,
            real=regra["taxa_rateio_maximo_pct"],
            tolerancia=0.01,
        )

    def test_nivel4_fallback_legacy(self, audit):
        """Nível 4: linha diferente cai para __legacy__ (fallback global)."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Nível 4 - fallback legacy")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra = calc._get_regra_comissao(
            "Saneamento", "Medidor Industrial", "Sub", "Produto", "Gerente Linha"
        )
        assert regra is not None

        audit.verificar(
            descricao="Nível 4 (legacy): linha Saneamento não tem regra → legacy",
            formula="filtro4: __legacy__+__legacy__ → taxa=2.0, fatia=30",
            entradas={"linha_buscada": "Saneamento"},
            esperado=2.0,
            real=regra["taxa_rateio_maximo_pct"],
            tolerancia=0.01,
        )
        audit.verificar(
            descricao="Nível 4 legacy: fatia_cargo_pct",
            formula="legacy fallback → fatia=30",
            entradas={"cargo": "Gerente Linha"},
            esperado=30,
            real=regra["fatia_cargo_pct"],
            tolerancia=0,
        )

    def test_cargo_diferente_mesma_regra(self, audit):
        """Mesmo nível 1, cargos diferentes → fatias diferentes."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Cargos diferentes")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra_gl = calc._get_regra_comissao(
            "Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Gerente Linha"
        )
        regra_ci = calc._get_regra_comissao(
            "Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Consultor Interno"
        )

        audit.verificar(
            descricao="Gerente Linha fatia=40 vs Consultor Interno fatia=20",
            formula="mesmo nível, cargos diferentes → fatias distintas",
            entradas={"cargo_gl": "Gerente Linha", "cargo_ci": "Consultor Interno"},
            esperado=40,
            real=regra_gl["fatia_cargo_pct"],
            tolerancia=0,
        )
        audit.verificar(
            descricao="Consultor Interno fatia=20",
            formula="nível 1 + cargo CI",
            entradas={"cargo": "Consultor Interno"},
            esperado=20,
            real=regra_ci["fatia_cargo_pct"],
            tolerancia=0,
        )

    def test_nenhuma_regra_retorna_none(self, audit):
        """Cargo inexistente → retorna None."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Nenhuma regra encontrada")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra = calc._get_regra_comissao(
            "Saneamento", "Grupo", "Sub", "Produto", "Cargo Inexistente"
        )

        audit.verificar(
            descricao="Cargo inexistente → None (nenhum nível tem match)",
            formula="todos os filtros falharam para cargo='Cargo Inexistente'",
            entradas={"cargo": "Cargo Inexistente"},
            esperado="None",
            real=str(regra),
            tolerancia=0,
        )

    def test_config_comissao_vazia(self, audit):
        """CONFIG_COMISSAO vazio → retorna None."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Config vazia")
        calc = _calc_minimo(regras=[])  # DataFrame vazio

        regra = calc._get_regra_comissao(
            "Hidrologia", "Sonda", "EXO", "Produto", "Gerente Linha"
        )

        audit.verificar(
            descricao="CONFIG_COMISSAO vazio → None",
            formula="df_regras.empty → return None",
            entradas={},
            esperado="None",
            real=str(regra),
            tolerancia=0,
        )


# =========================================================================
# TESTES: Cache de _get_regra_comissao
# =========================================================================
class TestGetRegraComissaoCache:
    """Testa que o cache funciona corretamente."""

    def test_cache_hit(self, audit):
        """Segunda chamada com mesmos args usa cache."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Cache hit")
        calc = _calc_minimo(_montar_regras_4_niveis())

        # Primeira chamada: popula cache
        regra1 = calc._get_regra_comissao(
            "Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Gerente Linha"
        )
        # Verificar que está no cache
        chave = ("Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Gerente Linha")
        assert chave in calc.cache_regras

        # Segunda chamada: deve usar cache
        regra2 = calc._get_regra_comissao(
            "Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Gerente Linha"
        )

        audit.verificar(
            descricao="Cache hit: mesma referência retornada",
            formula="cache_regras[chave] → mesmo objeto",
            entradas={"chave": str(chave)},
            esperado=regra1["taxa_rateio_maximo_pct"],
            real=regra2["taxa_rateio_maximo_pct"],
            tolerancia=0.001,
        )

    def test_cache_miss_chaves_diferentes(self, audit):
        """Chaves diferentes geram entradas de cache separadas."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Cache miss")
        calc = _calc_minimo(_montar_regras_4_niveis())

        calc._get_regra_comissao("Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Gerente Linha")
        calc._get_regra_comissao("Hidrologia", "Sonda Serie EXO", "EXO", "Produto", "Consultor Interno")

        audit.verificar(
            descricao="2 chaves diferentes → 2 entradas no cache",
            formula="len(cache_regras) == 2",
            entradas={},
            esperado=2,
            real=len(calc.cache_regras),
            tolerancia=0,
        )

    def test_cache_none_tambem_cacheia(self, audit):
        """Resultado None também é cacheado (evita re-busca)."""
        audit.set_contexto(modulo="Regra Comissão", cenario="Cache None")
        calc = _calc_minimo(_montar_regras_4_niveis())

        regra = calc._get_regra_comissao(
            "Locação", "Grupo", "Sub", "Tipo", "Cargo Inexistente"
        )
        chave = ("Locação", "Grupo", "Sub", "Tipo", "Cargo Inexistente")

        # None deve estar cacheado
        assert chave in calc.cache_regras

        audit.verificar(
            descricao="None também é cacheado para evitar re-busca",
            formula="cache_regras[chave] = None",
            entradas={"chave": str(chave)},
            esperado="None",
            real=str(calc.cache_regras[chave]),
            tolerancia=0,
        )
