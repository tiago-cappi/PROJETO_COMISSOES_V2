"""
Testes unitários para _get_meta (CalculoComissao).

Testa o lookup hierárquico de metas para:
1. faturamento_linha / conversao_linha → METAS_APLICACAO (5 níveis de fallback)
   Nível 1: linha + grupo + subgrupo + tipo_mercadoria  (mais específico)
   Nível 2: linha + grupo + subgrupo + ""
   Nível 3: linha + grupo + "" + ""
   Nível 4: linha + "" + "" + tipo_mercadoria
   Nível 5: linha + "" + "" + ""                        (mais genérico)

2. faturamento_individual / conversao_individual → METAS_INDIVIDUAIS (por colaborador)

3. rentabilidade → META_RENTABILIDADE (por hierarquia completa)
"""

import pytest
import pandas as pd
import numpy as np

from calculo_comissoes import CalculoComissao
from tests_comissoes.fixtures.config_factory import ConfigFactory


# =========================================================================
# HELPERS
# =========================================================================

def _calc_com_metas(
    metas_aplicacao: list = None,
    metas_individuais: list = None,
    meta_rentabilidade: list = None,
) -> CalculoComissao:
    """Cria instância mínima de CalculoComissao com dados de meta."""
    calc = CalculoComissao.__new__(CalculoComissao)
    calc.data = {}
    calc.params = {}
    calc.validation_log = []
    calc.cache_regras = {}
    calc.legacy_token = "__legacy__"

    class _MinimalLogger:
        def info(self, *a, **kw): pass
        def aviso(self, *a, **kw): pass
        def erro(self, *a, **kw): pass
        def log(self, *a, **kw): pass

    calc.validation_logger = _MinimalLogger()

    if metas_aplicacao is not None:
        calc.data["METAS_APLICACAO"] = pd.DataFrame(metas_aplicacao)
    else:
        calc.data["METAS_APLICACAO"] = ConfigFactory.criar_metas_aplicacao()

    if metas_individuais is not None:
        calc.data["METAS_INDIVIDUAIS"] = pd.DataFrame(metas_individuais)
    else:
        calc.data["METAS_INDIVIDUAIS"] = ConfigFactory.criar_metas_individuais()

    if meta_rentabilidade is not None:
        calc.data["META_RENTABILIDADE"] = pd.DataFrame(meta_rentabilidade)
    else:
        calc.data["META_RENTABILIDADE"] = ConfigFactory.criar_meta_rentabilidade()

    return calc


def _montar_metas_5_niveis() -> list:
    """Metas de aplicação com 5 níveis de especificidade para Hidrologia."""
    return [
        # Nível 1: match completo
        {
            "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
            "subgrupo": "EXO", "tipo_mercadoria": "Produto",
            "tipo_meta": "faturamento", "valor_meta": 600_000,
        },
        # Nível 2: linha + grupo + subgrupo (tipo vazio)
        {
            "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
            "subgrupo": "EXO", "tipo_mercadoria": "",
            "tipo_meta": "faturamento", "valor_meta": 550_000,
        },
        # Nível 3: linha + grupo (subgrupo e tipo vazios)
        {
            "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
            "subgrupo": "", "tipo_mercadoria": "",
            "tipo_meta": "faturamento", "valor_meta": 500_000,
        },
        # Nível 4: linha + tipo_mercadoria (grupo e subgrupo vazios)
        {
            "linha": "Hidrologia", "grupo": "",
            "subgrupo": "", "tipo_mercadoria": "Produto",
            "tipo_meta": "faturamento", "valor_meta": 480_000,
        },
        # Nível 5: apenas linha (tudo vazio)
        {
            "linha": "Hidrologia", "grupo": "",
            "subgrupo": "", "tipo_mercadoria": "",
            "tipo_meta": "faturamento", "valor_meta": 450_000,
        },
        # Conversão — apenas nível 5 para simplificar
        {
            "linha": "Hidrologia", "grupo": "",
            "subgrupo": "", "tipo_mercadoria": "",
            "tipo_meta": "conversao", "valor_meta": 300_000,
        },
    ]


# =========================================================================
# TESTES: _get_meta — faturamento_linha / conversao_linha
# =========================================================================
class TestGetMetaAplicacao:
    """Testes do lookup hierárquico de metas de aplicação (linha)."""

    def test_nivel1_match_completo(self, audit):
        """Nível 1: match exato (linha+grupo+subgrupo+tipo) → 600k."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Nível 1 - match completo")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "Sonda Serie EXO", "EXO", "Produto"),
        )

        audit.verificar(
            descricao="Match exato: Hidro+Sonda+EXO+Produto → 600.000",
            formula="filtro nível 1: todos os campos correspondem",
            entradas={
                "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
                "subgrupo": "EXO", "tipo_mercadoria": "Produto",
            },
            esperado=600_000,
            real=valor,
            tolerancia=0,
        )

    def test_nivel2_sem_tipo(self, audit):
        """Nível 2: tipo_mercadoria diferente → fallback grupo+subgrupo."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Nível 2 - sem tipo")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "Sonda Serie EXO", "EXO", "Serviço"),  # Serviço ≠ Produto
        )

        audit.verificar(
            descricao="Tipo 'Serviço' não tem match → fallback nível 2 (subgrupo+'')",
            formula="filtro nível 2: linha+grupo+subgrupo+'' → 550.000",
            entradas={"tipo_buscado": "Serviço"},
            esperado=550_000,
            real=valor,
            tolerancia=0,
        )

    def test_nivel3_sem_subgrupo(self, audit):
        """Nível 3: subgrupo diferente → fallback grupo."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Nível 3 - sem subgrupo")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "Sonda Serie EXO", "EXO3", "Serviço"),  # EXO3 e Serviço
        )

        audit.verificar(
            descricao="Subgrupo 'EXO3' + Tipo 'Serviço' → fallback nível 3 (grupo+''+'') → 500.000",
            formula="filtro nível 3: linha+grupo+''+'' → 500.000",
            entradas={"subgrupo_buscado": "EXO3", "tipo_buscado": "Serviço"},
            esperado=500_000,
            real=valor,
            tolerancia=0,
        )

    def test_nivel4_tipo_sem_grupo(self, audit):
        """Nível 4: grupo diferente mas tipo coincide → fallback linha+tipo."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Nível 4 - tipo sem grupo")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "Medidor de Vazão Fixo", "IQ Standard", "Produto"),
        )

        audit.verificar(
            descricao="Grupo diferente, tipo 'Produto' → fallback nível 4 (linha+tipo) → 480.000",
            formula="filtro nível 4: linha+''+''+'Produto' → 480.000",
            entradas={"grupo_buscado": "Medidor de Vazão Fixo", "tipo": "Produto"},
            esperado=480_000,
            real=valor,
            tolerancia=0,
        )

    def test_nivel5_apenas_linha(self, audit):
        """Nível 5: nada coincide além da linha → meta genérica."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Nível 5 - apenas linha")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "Grupo Inexistente", "Sub Inexistente", "Tipo Inexistente"),
        )

        audit.verificar(
            descricao="Nada coincide → fallback nível 5 (apenas linha) → 450.000",
            formula="filtro nível 5: linha+''+''+ '' → 450.000",
            entradas={"grupo": "inexistente", "subgrupo": "inexistente", "tipo": "inexistente"},
            esperado=450_000,
            real=valor,
            tolerancia=0,
        )

    def test_conversao_linha(self, audit):
        """Conversão de linha usa o mesmo mecanismo de fallback."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Conversão linha")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "conversao_linha",
            ("Hidrologia", "Qualquer", "Qualquer", "Qualquer"),
        )

        audit.verificar(
            descricao="conversao_linha: fallback até nível 5 → 300.000",
            formula="tipo_meta_busca='conversao' → 300.000",
            entradas={"tipo_meta": "conversao_linha"},
            esperado=300_000,
            real=valor,
            tolerancia=0,
        )

    def test_linha_inexistente_retorna_none(self, audit):
        """Linha que não existe em METAS_APLICACAO → None."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Linha inexistente")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor = calc._get_meta(
            "faturamento_linha",
            ("Locação", "Grupo", "Sub", "Tipo"),
        )

        audit.verificar(
            descricao="Linha 'Locação' não existe → None",
            formula="nenhum nível correspondeu",
            entradas={"linha": "Locação"},
            esperado="None",
            real=str(valor),
            tolerancia=0,
        )


# =========================================================================
# TESTES: _get_meta — faturamento_individual / conversao_individual
# =========================================================================
class TestGetMetaIndividual:
    """Testes de metas individuais por colaborador."""

    def test_meta_individual_faturamento(self, audit):
        """Busca meta de faturamento individual por nome do colaborador."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Individual faturamento")
        calc = _calc_com_metas()

        valor = calc._get_meta("faturamento_individual", "Samanta Silva")

        audit.verificar(
            descricao="Meta faturamento individual da Samanta = 100.000",
            formula="METAS_INDIVIDUAIS[colaborador=Samanta, tipo=faturamento]",
            entradas={"colaborador": "Samanta Silva", "tipo_meta": "faturamento"},
            esperado=100_000,
            real=valor,
            tolerancia=0,
        )

    def test_meta_individual_conversao(self, audit):
        """Busca meta de conversão individual."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Individual conversão")
        calc = _calc_com_metas()

        valor = calc._get_meta("conversao_individual", "Rafaela Meirelles")

        audit.verificar(
            descricao="Meta conversão individual da Rafaela = 90.000",
            formula="METAS_INDIVIDUAIS[colaborador=Rafaela, tipo=conversao]",
            entradas={"colaborador": "Rafaela Meirelles", "tipo_meta": "conversao"},
            esperado=90_000,
            real=valor,
            tolerancia=0,
        )

    def test_meta_individual_colaborador_inexistente(self, audit):
        """Colaborador sem meta individual → None (IndexError capturado internamente)."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Individual inexistente")
        calc = _calc_com_metas()

        valor = calc._get_meta("faturamento_individual", "João Ninguém")

        audit.verificar(
            descricao="Colaborador sem meta → None (except IndexError → return None)",
            formula="df filtrado vazio → .iloc[0] IndexError → capturado → None",
            entradas={"colaborador": "João Ninguém"},
            esperado="None",
            real=str(valor),
            tolerancia=0,
        )


# =========================================================================
# TESTES: _get_meta — rentabilidade
# =========================================================================
class TestGetMetaRentabilidade:
    """Testes de meta de rentabilidade por hierarquia."""

    def test_meta_rentabilidade_encontrada(self, audit):
        """Match exato na META_RENTABILIDADE → retorna pct alvo."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Rentabilidade encontrada")
        calc = _calc_com_metas()

        valor = calc._get_meta(
            "rentabilidade",
            ("Hidrologia", "Sonda Serie EXO", "EXO", "Produto"),
        )

        audit.verificar(
            descricao="Meta rentabilidade Hidro/Sonda/EXO/Produto = 12%",
            formula="META_RENTABILIDADE[hierarquia exata] → 0.12",
            entradas={
                "linha": "Hidrologia", "grupo": "Sonda Serie EXO",
                "subgrupo": "EXO", "tipo_mercadoria": "Produto",
            },
            esperado=0.12,
            real=valor,
            tolerancia=0.001,
        )

    def test_meta_rentabilidade_sso(self, audit):
        """Meta de rentabilidade para SSO → 15%."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Rentabilidade SSO")
        calc = _calc_com_metas()

        valor = calc._get_meta(
            "rentabilidade",
            ("SSO", "Monitor de Gases Fixo", "RAE", "Produto"),
        )

        audit.verificar(
            descricao="Meta rentabilidade SSO/Monitor/RAE/Produto = 15%",
            formula="META_RENTABILIDADE[hierarquia SSO] → 0.15",
            entradas={"linha": "SSO"},
            esperado=0.15,
            real=valor,
            tolerancia=0.001,
        )

    def test_meta_rentabilidade_nao_encontrada(self, audit):
        """Hierarquia sem meta de rentabilidade → None."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Rentabilidade não encontrada")
        calc = _calc_com_metas()

        valor = calc._get_meta(
            "rentabilidade",
            ("Locação", "Grupo Inexistente", "Sub", "Tipo"),
        )

        audit.verificar(
            descricao="Hierarquia sem meta de rentabilidade → None",
            formula="filtro normalizado vazio + filtro original vazio → None",
            entradas={"linha": "Locação"},
            esperado="None",
            real=str(valor),
            tolerancia=0,
        )


# =========================================================================
# TESTES: Prioridade e consistência
# =========================================================================
class TestMetaPrioridade:
    """Testes que garantem que o nível mais específico é sempre preferido."""

    def test_especifico_prevalece_sobre_generico(self, audit):
        """Nível 1 (600k) prevalece sobre nível 5 (450k)."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Prioridade específico")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        valor_especifico = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "Sonda Serie EXO", "EXO", "Produto"),
        )
        valor_generico = calc._get_meta(
            "faturamento_linha",
            ("Hidrologia", "X", "Y", "Z"),
        )

        audit.verificar(
            descricao="Específico (600k) > Genérico (450k): prioridade correta",
            formula="nível1=600k usa match exato; nível5=450k usa fallback",
            entradas={"especifico": valor_especifico, "generico": valor_generico},
            esperado=600_000,
            real=valor_especifico,
            tolerancia=0,
        )
        assert valor_especifico > valor_generico

    def test_meta_diferente_para_faturamento_e_conversao(self, audit):
        """Faturamento e conversão da mesma linha retornam valores diferentes."""
        audit.set_contexto(modulo="Meta Lookup", cenario="Fat vs Conv")
        calc = _calc_com_metas(metas_aplicacao=_montar_metas_5_niveis())

        fat = calc._get_meta("faturamento_linha", ("Hidrologia", "X", "Y", "Z"))
        conv = calc._get_meta("conversao_linha", ("Hidrologia", "X", "Y", "Z"))

        audit.verificar(
            descricao="Faturamento (450k) ≠ Conversão (300k)",
            formula="tipo_meta_busca diferente filtra linhas distintas",
            entradas={"faturamento": fat, "conversao": conv},
            esperado=450_000,
            real=fat,
            tolerancia=0,
        )
        assert fat != conv
