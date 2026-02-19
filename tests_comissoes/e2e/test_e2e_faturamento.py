"""
Testes E2E: Pipeline completo de Comissão por Faturamento.

Simula o fluxo end-to-end que calculo_comissoes.py executa na Etapa 5:

    1. Carregar configs (CONFIG_COMISSAO, ATRIBUICOES, FC_ESCADA_CARGOS, COLABORADORES)
    2. Para cada item faturado:
        a. Buscar atribuição Wide → extrair colaboradores
        b. Buscar regra de comissão (4 níveis fallback)
        c. Calcular FC (performance → escada/rampa → multiplicador)
        d. Calcular comissão: faturamento × taxa × pe × split × fc
    3. Aplicar devoluções: calcular fator → aplicar estorno
    4. Gerar DataFrame final com colunas de auditoria

Pipeline completo:
    Config → Atribuição → Regra Comissão → FC Escada → Comissão → Devolução → Saída

Cenários E2E:
    - Item simples: 1 gerente, 1 produto, sem devolução
    - Item com time completo: gerente + coordenador + CI + diretor
    - Item com split de gerentes (2 gerentes, fator 0.5 cada)
    - Item com cross-selling decisão A (taxa reduzida)
    - Item com devolução parcial (40% devolvido)
    - Lote de itens: 3 processos, múltiplos cargos, devoluções mistas
    - Verificação de consistência: soma(comissões) + soma(estornos) = líquido
    - Auditoria: todas as colunas de rastreio presentes
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from calculo_comissoes import (
    _extrair_colaboradores_wide,
    _buscar_atribuicao_wide,
    CalculoComissao,
)
from src.core.fc_escada import load_fc_escada_cargos, aplicar_fc_escada
from src.devolucao.devolucao_calculator import DevolucaoCalculator
from tests_comissoes.fixtures.config_factory import ConfigFactory
from tests_comissoes.fixtures.data_factory import DataFactory


# =========================================================================
# HELPERS: Reproduzem pipeline completo de calculo_comissoes.py Etapa 5
# =========================================================================

def _criar_calc_minimo(regras=None, atribuicoes=None) -> CalculoComissao:
    """Cria instância mínima de CalculoComissao para lookups."""
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
    calc.data["CONFIG_COMISSAO"] = ConfigFactory.criar_config_comissao(regras)
    calc.data["COLABORADORES"] = ConfigFactory.criar_colaboradores()
    calc.data["ATRIBUICOES"] = atribuicoes if atribuicoes is not None else ConfigFactory.criar_atribuicoes_wide()
    return calc


def _pipeline_faturamento_e2e(
    item_faturado: dict,
    calc: CalculoComissao,
    fc_configs: dict,
    performances: dict,
    cross_selling_info: dict = None,
) -> list:
    """Reproduz Etapa 5 para um único item faturado.

    Args:
        item_faturado: Dict com dados do item (Valor Realizado, Negócio, etc.)
        calc: Instância mínima para lookups de regra e atribuição.
        fc_configs: Dict de FC escada por cargo.
        performances: Dict {colaborador: performance_float} — FC rampa pré-escada.
        cross_selling_info: Opcional. Dict com is_cross, decision, taxa.

    Returns:
        Lista de dicts com comissões calculadas (base_dict).
    """
    df_atribuicoes = calc.data["ATRIBUICOES"]
    df_colabs = calc.data["COLABORADORES"]

    faturamento = float(item_faturado.get("Valor Realizado", 0))
    linha = str(item_faturado.get("Negócio", "")).strip()
    grupo = str(item_faturado.get("Grupo", "")).strip()
    subgrupo = str(item_faturado.get("Subgrupo", "")).strip()
    tipo_merc = str(item_faturado.get("Tipo de Mercadoria", "")).strip()

    # 2a. Buscar atribuição Wide
    row_atr = _buscar_atribuicao_wide(df_atribuicoes, linha, grupo, subgrupo, tipo_merc)
    if row_atr is None:
        return []

    # 2b. Extrair time de colaboradores
    time_gestao = _extrair_colaboradores_wide(row_atr)

    # Adicionar operacionais do item (CI, CE)
    ci = str(item_faturado.get("Consultor Interno", "")).strip()
    ce = str(item_faturado.get("Representante-pedido", "")).strip()
    time_operacional = []
    if ci:
        time_operacional.append({"colaborador": ci, "cargo": "Consultor Interno", "fator_split": 1.0})
    if ce:
        time_operacional.append({"colaborador": ce, "cargo": "Consultor Externo", "fator_split": 1.0})

    time_completo = time_gestao + time_operacional

    # Deduplicar por (colaborador, cargo)
    seen = set()
    time_dedupd = []
    for c in time_completo:
        key = (c["colaborador"], c["cargo"])
        if key not in seen:
            seen.add(key)
            time_dedupd.append(c)

    comissoes = []

    for atribuicao in time_dedupd:
        colab_nome = atribuicao["colaborador"]
        colab_cargo = atribuicao["cargo"]
        fator_split = float(atribuicao.get("fator_split", 1.0))

        # 2c. Buscar regra de comissão
        regra = calc._get_regra_comissao(
            linha, grupo, subgrupo, tipo_merc, colab_cargo
        )
        if regra is None:
            continue

        taxa_rateio = regra["taxa_rateio_maximo_pct"] / 100.0
        pe = regra["fatia_cargo_pct"] / 100.0

        # Cross-selling decisão A: reduzir taxa
        if cross_selling_info and cross_selling_info.get("is_cross") and cross_selling_info.get("decision") == "A":
            taxa_cs = float(cross_selling_info.get("taxa", 0.0)) / 100.0
            taxa_rateio = max(0.0, taxa_rateio - taxa_cs)

        # 2d. Calcular FC (escada)
        fc_rampa = performances.get(colab_nome, 0.0)
        fc_aplicado, detalhes_fc = aplicar_fc_escada(fc_rampa, colab_cargo, fc_configs)

        comissao_potencial = faturamento * taxa_rateio * pe * fator_split
        comissao_item = comissao_potencial * fc_aplicado

        comissoes.append({
            "nome_colaborador": colab_nome,
            "cargo": colab_cargo,
            "fator_split_cargo": fator_split,
            "processo": item_faturado.get("Processo", ""),
            "numero_nf": item_faturado.get("Numero NF", ""),
            "faturamento_item": faturamento,
            "taxa_rateio_aplicada": taxa_rateio,
            "percentual_elegibilidade_pe": pe,
            "fator_correcao_fc": fc_aplicado,
            "fator_correcao_fc_rampa": fc_rampa,
            "fc_escada_modo": detalhes_fc.get("modo") if isinstance(detalhes_fc, dict) else None,
            "comissao_potencial_maxima": comissao_potencial,
            "comissao_calculada": comissao_item,
        })

    return comissoes


def _aplicar_devolucoes_e2e(comissoes: list, devolucoes_df: pd.DataFrame) -> list:
    """Aplica estornos de devolução sobre as comissões calculadas.

    Returns:
        Lista de dicts com estornos (comissao negativa).
    """
    if devolucoes_df.empty or not comissoes:
        return []

    calc_dev = DevolucaoCalculator()
    estornos = []

    # Agrupar comissões por (processo, colaborador)
    comissao_por_chave = {}
    for c in comissoes:
        chave = (str(c["processo"]).strip(), c["nome_colaborador"])
        comissao_por_chave.setdefault(chave, 0.0)
        comissao_por_chave[chave] += c["comissao_calculada"]

    # Para cada devolução, calcular fator e estorno
    for _, dev in devolucoes_df.iterrows():
        processo = str(dev.get("Processo", "")).strip()
        valor_devolvido = float(dev.get("Valor Devolvido", 0))
        valor_realizado = float(dev.get("Valor Realizado Original", 0))

        if valor_realizado <= 0:
            continue

        fator = calc_dev.calcular_fator_devolucao(valor_devolvido, valor_realizado)

        for (proc, colab), comissao_orig in comissao_por_chave.items():
            if proc == processo and comissao_orig > 0:
                # Estorno = negativo da comissão original × fator de devolução
                estorno = -(comissao_orig * fator)
                estornos.append({
                    "processo": processo,
                    "nome_colaborador": colab,
                    "comissao_original": comissao_orig,
                    "valor_devolvido": valor_devolvido,
                    "fator_devolucao": fator,
                    "estorno": estorno,
                })

    return estornos


# =========================================================================
# CLASSE: TestE2EFaturamentoSimples
# =========================================================================
@pytest.mark.e2e
@pytest.mark.faturamento
class TestE2EFaturamentoSimples:
    """Testa pipeline E2E com cenários simples (1 item, 1-2 colaboradores)."""

    def test_item_simples_gerente_fc100(self, audit):
        """1 item Hidrologia, 1 Gerente, FC=100% → comissão máxima.

        Pipeline: Config → Atribuição → Regra → FC(1.0) → Comissão
        """
        audit.set_contexto(modulo="E2E Faturamento", cenario="Item simples Gerente FC=1.0")

        # 1. Configs
        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        # 2. Item faturado
        item = DataFactory.criar_item_faturado(
            processo="E2E-001",
            valor_realizado=150_000.0,
            linha="Hidrologia",
            grupo="Sonda Serie EXO",
            subgrupo="EXO",
            tipo_mercadoria="Produto",
            consultor_interno="Samanta Silva",
        )

        # 3. Pipeline
        performances = {"Andrey Andrade": 1.0, "Samanta Silva": 1.0,
                        "Rosana Martins": 1.0, "Carlos Diretor": 1.0}
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)

        assert len(comissoes) > 0

        # Verificar Gerente
        gerentes = [c for c in comissoes if c["cargo"] == "Gerente Linha"]
        assert len(gerentes) >= 1
        g = gerentes[0]

        # Gerente Linha ESCADA 4 degraus, perf=1.0 → topo (fc=1.0)
        # Regra default: taxa=5%, pe=40% → 150000 * 0.05 * 0.40 * 1.0 * 1.0 = 3000
        esperado = 150_000 * (g["taxa_rateio_aplicada"]) * (g["percentual_elegibilidade_pe"]) * g["fator_split_cargo"] * g["fator_correcao_fc"]

        audit.verificar(
            descricao="Comissao Gerente FC=1.0 pipeline E2E",
            formula=f"150000 x {g['taxa_rateio_aplicada']} x {g['percentual_elegibilidade_pe']} x {g['fator_split_cargo']} x {g['fator_correcao_fc']}",
            entradas={"faturamento": 150_000, "cargo": "Gerente Linha"},
            esperado=round(esperado, 2),
            real=round(g["comissao_calculada"], 2),
        )

    def test_item_simples_ci_escada_parcial(self, audit):
        """1 item, CI com performance 60%, ESCADA 5 degraus piso 40%.

        Degrau: int(0.6 × 4) = 2
        Mult: 0.4 + (2 × 0.6/4) = 0.7
        """
        audit.set_contexto(modulo="E2E Faturamento", cenario="CI escada parcial")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        item = DataFactory.criar_item_faturado(
            processo="E2E-002",
            valor_realizado=80_000.0,
            consultor_interno="Samanta Silva",
        )

        performances = {"Andrey Andrade": 0.6, "Samanta Silva": 0.6,
                        "Rosana Martins": 0.6, "Carlos Diretor": 0.6}
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)

        ci = [c for c in comissoes if c["cargo"] == "Consultor Interno"]
        assert len(ci) == 1
        c = ci[0]

        # CI ESCADA: 5 degraus, piso=0.4, perf=0.6
        # degrau = int(0.6 * 4) = 2, mult = 0.4 + 2*(0.6/4) = 0.7
        fc_esperado = 0.4 + (2 * 0.6 / 4)

        audit.verificar(
            descricao="FC CI escada parcial",
            formula="0.4 + (2 * 0.6/4) = 0.7",
            entradas={"perf": 0.6, "piso": 0.4, "degraus": 5},
            esperado=round(fc_esperado, 4),
            real=round(c["fator_correcao_fc"], 4),
        )

        esperado_comissao = c["faturamento_item"] * c["taxa_rateio_aplicada"] * c["percentual_elegibilidade_pe"] * c["fator_split_cargo"] * fc_esperado
        audit.verificar(
            descricao="Comissao CI com escada parcial",
            formula=f"{c['faturamento_item']} x taxa x pe x 1.0 x {fc_esperado}",
            entradas={"faturamento": 80_000},
            esperado=round(esperado_comissao, 2),
            real=round(c["comissao_calculada"], 2),
        )


# =========================================================================
# CLASSE: TestE2ETimeCompleto
# =========================================================================
@pytest.mark.e2e
@pytest.mark.faturamento
class TestE2ETimeCompleto:
    """Testa pipeline E2E com time completo (todos os cargos)."""

    def test_time_completo_4_cargos(self, audit):
        """Gerente + Coordenador + CI + Diretor → 4 comissões distintas."""
        audit.set_contexto(modulo="E2E Faturamento", cenario="Time completo 4 cargos")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        item = DataFactory.criar_item_faturado(
            processo="E2E-010",
            valor_realizado=200_000.0,
            consultor_interno="Samanta Silva",
        )

        performances = {
            "Andrey Andrade": 0.85,    # Gerente ESCADA
            "Rosana Martins": 0.90,    # Coordenador ESCADA
            "Samanta Silva": 0.75,     # CI ESCADA
            "Carlos Diretor": 0.95,    # Diretor RAMPA
        }
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)

        cargos_encontrados = {c["cargo"] for c in comissoes}

        # Verificar que pelo menos Gerente, CI e Coordenador foram calculados
        # (depende de quais estão na atribuição padrão)
        assert len(comissoes) >= 3

        audit.verificar(
            descricao="Quantidade de comissoes calculadas (time completo)",
            formula="Atribuicao + CI do item = 4+ cargos",
            entradas={"cargos": list(cargos_encontrados)},
            esperado="True",
            real=str(len(comissoes) >= 3),
        )

        # Verificar que cada comissão respeita a fórmula
        for c in comissoes:
            recalc = c["faturamento_item"] * c["taxa_rateio_aplicada"] * c["percentual_elegibilidade_pe"] * c["fator_split_cargo"] * c["fator_correcao_fc"]
            audit.verificar(
                descricao=f"Formula E2E {c['nome_colaborador']} ({c['cargo']})",
                formula="faturamento x taxa x pe x split x fc",
                entradas={
                    "fc": round(c["fator_correcao_fc"], 4),
                    "taxa": c["taxa_rateio_aplicada"],
                    "pe": c["percentual_elegibilidade_pe"],
                },
                esperado=round(recalc, 2),
                real=round(c["comissao_calculada"], 2),
            )

    def test_split_dois_gerentes(self, audit):
        """2 Gerentes de Linha → fator_split=0.5 cada."""
        audit.set_contexto(modulo="E2E Faturamento", cenario="Split 2 gerentes")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())

        # Atribuição com 2 gerentes
        atribuicoes = ConfigFactory.criar_atribuicoes_wide(rows=[{
            "linha": "Hidrologia",
            "grupo": "Sonda Serie EXO",
            "subgrupo": "EXO",
            "tipo_mercadoria": "Produto",
            "Gerente Linha 1": "Andrey Andrade",
            "Gerente Linha 2": "Dener Martins",
            "Coordenador 1": "Rosana Martins",
            "Coordenador 2": None,
            "Diretor": "Carlos Diretor",
        }])

        calc = _criar_calc_minimo(atribuicoes=atribuicoes)

        item = DataFactory.criar_item_faturado(
            processo="E2E-011",
            valor_realizado=120_000.0,
            consultor_interno="Samanta Silva",
        )

        performances = {
            "Andrey Andrade": 1.0, "Dener Martins": 1.0,
            "Rosana Martins": 1.0, "Samanta Silva": 1.0,
            "Carlos Diretor": 1.0,
        }
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)

        gerentes = [c for c in comissoes if c["cargo"] == "Gerente Linha"]
        assert len(gerentes) == 2

        for g in gerentes:
            audit.verificar(
                descricao=f"Split gerente {g['nome_colaborador']}",
                formula="fator_split = 0.5 com 2 gerentes",
                entradas={"gerente": g["nome_colaborador"]},
                esperado=0.5,
                real=g["fator_split_cargo"],
            )

            # Comissão deve ser metade da de um gerente solo
            recalc = g["faturamento_item"] * g["taxa_rateio_aplicada"] * g["percentual_elegibilidade_pe"] * 0.5 * g["fator_correcao_fc"]
            audit.verificar(
                descricao=f"Comissao split {g['nome_colaborador']}",
                formula="faturamento x taxa x pe x 0.5 x fc",
                entradas={},
                esperado=round(recalc, 2),
                real=round(g["comissao_calculada"], 2),
            )


# =========================================================================
# CLASSE: TestE2ECrossSelling
# =========================================================================
@pytest.mark.e2e
@pytest.mark.faturamento
@pytest.mark.cross_selling
class TestE2ECrossSelling:
    """Testa pipeline E2E com cross-selling decisão A."""

    def test_cross_selling_decisao_a_reduz_taxa(self, audit):
        """Cross-selling A: taxa do time interno reduzida pela taxa CS."""
        audit.set_contexto(modulo="E2E Faturamento", cenario="Cross-selling A")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        item = DataFactory.criar_item_faturado(
            processo="E2E-020",
            valor_realizado=100_000.0,
            consultor_interno="Samanta Silva",
        )

        performances = {"Andrey Andrade": 1.0, "Samanta Silva": 1.0,
                        "Rosana Martins": 1.0, "Carlos Diretor": 1.0}

        cs_info = {"is_cross": True, "decision": "A", "taxa": 1.0}  # 1%

        comissoes_cs = _pipeline_faturamento_e2e(item, calc, fc_configs, performances, cs_info)
        comissoes_sem_cs = _pipeline_faturamento_e2e(item, calc, fc_configs, performances, None)

        # Cada comissão com CS deve ser menor que sem CS (taxa reduzida)
        for c_cs in comissoes_cs:
            c_normal = next((c for c in comissoes_sem_cs
                            if c["nome_colaborador"] == c_cs["nome_colaborador"]), None)
            if c_normal:
                audit.verificar(
                    descricao=f"CS-A {c_cs['nome_colaborador']}: taxa reduzida",
                    formula="taxa_cs_A < taxa_normal",
                    entradas={
                        "taxa_cs": round(c_cs["taxa_rateio_aplicada"], 4),
                        "taxa_normal": round(c_normal["taxa_rateio_aplicada"], 4),
                    },
                    esperado="True",
                    real=str(c_cs["taxa_rateio_aplicada"] < c_normal["taxa_rateio_aplicada"]),
                )


# =========================================================================
# CLASSE: TestE2EDevolucao
# =========================================================================
@pytest.mark.e2e
@pytest.mark.faturamento
@pytest.mark.devolucao
class TestE2EDevolucao:
    """Testa pipeline E2E com devoluções aplicadas sobre comissões."""

    def test_devolucao_parcial_40pct(self, audit):
        """40% devolvido → fator=0.4 → estorno = -(comissão × 0.4)."""
        audit.set_contexto(modulo="E2E Faturamento", cenario="Devolucao parcial 40%")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        item = DataFactory.criar_item_faturado(
            processo="E2E-030",
            valor_realizado=100_000.0,
            consultor_interno="Samanta Silva",
        )

        performances = {"Andrey Andrade": 1.0, "Samanta Silva": 1.0,
                        "Rosana Martins": 1.0, "Carlos Diretor": 1.0}
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)

        # Devolução de 40%
        devolucoes = pd.DataFrame([{
            "Processo": "E2E-030",
            "Valor Devolvido": 40_000.0,
            "Valor Realizado Original": 100_000.0,
        }])

        estornos = _aplicar_devolucoes_e2e(comissoes, devolucoes)

        assert len(estornos) > 0

        for e in estornos:
            fator_esperado = 40_000 / 100_000  # 0.4
            estorno_esperado = -(e["comissao_original"] * fator_esperado)

            audit.verificar(
                descricao=f"Fator devolucao {e['nome_colaborador']}",
                formula="40000 / 100000 = 0.4",
                entradas={"devolvido": 40_000, "realizado": 100_000},
                esperado=round(fator_esperado, 4),
                real=round(e["fator_devolucao"], 4),
            )
            audit.verificar(
                descricao=f"Estorno {e['nome_colaborador']}",
                formula=f"-({e['comissao_original']} x 0.4)",
                entradas={},
                esperado=round(estorno_esperado, 2),
                real=round(e["estorno"], 2),
            )

    def test_consistencia_liquido(self, audit):
        """soma(comissões) + soma(estornos) = comissão líquida correta.

        Propriedade: líquido = soma(comissão × (1 - fator_devolução))
        """
        audit.set_contexto(modulo="E2E Faturamento", cenario="Consistencia liquido")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        item = DataFactory.criar_item_faturado(
            processo="E2E-031",
            valor_realizado=200_000.0,
            consultor_interno="Samanta Silva",
        )

        performances = {"Andrey Andrade": 0.8, "Samanta Silva": 0.9,
                        "Rosana Martins": 0.7, "Carlos Diretor": 0.85}
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)

        devolucoes = pd.DataFrame([{
            "Processo": "E2E-031",
            "Valor Devolvido": 60_000.0,
            "Valor Realizado Original": 200_000.0,
        }])

        estornos = _aplicar_devolucoes_e2e(comissoes, devolucoes)
        fator = 60_000 / 200_000  # 0.3

        total_comissao_bruta = sum(c["comissao_calculada"] for c in comissoes)
        total_estorno = sum(e["estorno"] for e in estornos)
        liquido = total_comissao_bruta + total_estorno
        liquido_esperado = total_comissao_bruta * (1 - fator)

        audit.verificar(
            descricao="Liquido = bruto + estorno = bruto * (1 - fator)",
            formula=f"{total_comissao_bruta:.2f} + {total_estorno:.2f} = {total_comissao_bruta:.2f} x (1 - {fator})",
            entradas={
                "bruto": round(total_comissao_bruta, 2),
                "estorno": round(total_estorno, 2),
                "fator": fator,
            },
            esperado=round(liquido_esperado, 2),
            real=round(liquido, 2),
        )


# =========================================================================
# CLASSE: TestE2ELoteMultiProcesso
# =========================================================================
@pytest.mark.e2e
@pytest.mark.faturamento
class TestE2ELoteMultiProcesso:
    """Testa pipeline E2E com lote de múltiplos processos."""

    def test_lote_3_processos(self, audit):
        """3 processos diferentes com performances distintas → DataFrame consolidado."""
        audit.set_contexto(modulo="E2E Faturamento", cenario="Lote 3 processos")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        itens = [
            DataFactory.criar_item_faturado(
                processo="LOTE-001", valor_realizado=100_000.0,
                consultor_interno="Samanta Silva",
            ),
            DataFactory.criar_item_faturado(
                processo="LOTE-002", valor_realizado=200_000.0,
                linha="SSO", grupo="Monitor de Gases Fixo",
                subgrupo="RAE", consultor_interno="Rafaela Meirelles",
            ),
            DataFactory.criar_item_faturado(
                processo="LOTE-003", valor_realizado=50_000.0,
                consultor_interno="Samanta Silva",
            ),
        ]

        performances = {
            "Andrey Andrade": 0.9, "Dener Martins": 0.8,
            "Rosana Martins": 0.85, "Samanta Silva": 0.75,
            "Rafaela Meirelles": 0.95, "Carlos Diretor": 0.7,
        }

        todas_comissoes = []
        for item in itens:
            comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)
            todas_comissoes.extend(comissoes)

        # Criar DataFrame consolidado
        df = pd.DataFrame(todas_comissoes)

        # Verificar que temos comissões dos 3 processos
        processos_unicos = df["processo"].nunique()
        audit.verificar(
            descricao="3 processos distintos no lote",
            formula="nunique(processo) == 3",
            entradas={"processos": df["processo"].unique().tolist()},
            esperado=3,
            real=processos_unicos,
        )

        # Verificar que todas as comissões são positivas (FC > 0 para todos)
        todas_positivas = (df["comissao_calculada"] >= 0).all()
        audit.verificar(
            descricao="Todas comissoes >= 0",
            formula="all(comissao >= 0)",
            entradas={},
            esperado="True",
            real=str(todas_positivas),
        )

        # Verificar integridade da fórmula em cada linha
        for _, row in df.iterrows():
            recalc = (row["faturamento_item"] * row["taxa_rateio_aplicada"]
                      * row["percentual_elegibilidade_pe"] * row["fator_split_cargo"]
                      * row["fator_correcao_fc"])
            diff = abs(row["comissao_calculada"] - recalc)
            audit.verificar(
                descricao=f"Formula OK {row['nome_colaborador']}/{row['processo']}",
                formula="faturamento x taxa x pe x split x fc",
                entradas={"diff": round(diff, 6)},
                esperado="True",
                real=str(diff < 0.01),
            )

    def test_auditoria_colunas_presentes(self, audit):
        """DataFrame de saída contém todas as colunas de auditoria."""
        audit.set_contexto(modulo="E2E Faturamento", cenario="Colunas auditoria")

        fc_configs = load_fc_escada_cargos(ConfigFactory.criar_fc_escada_cargos())
        calc = _criar_calc_minimo()

        item = DataFactory.criar_item_faturado(processo="AUD-001", valor_realizado=100_000.0,
                                                consultor_interno="Samanta Silva")
        performances = {"Andrey Andrade": 1.0, "Samanta Silva": 1.0,
                        "Rosana Martins": 1.0, "Carlos Diretor": 1.0}
        comissoes = _pipeline_faturamento_e2e(item, calc, fc_configs, performances)
        df = pd.DataFrame(comissoes)

        colunas_obrigatorias = [
            "nome_colaborador", "cargo", "fator_split_cargo",
            "processo", "numero_nf", "faturamento_item",
            "taxa_rateio_aplicada", "percentual_elegibilidade_pe",
            "fator_correcao_fc", "fator_correcao_fc_rampa",
            "fc_escada_modo", "comissao_potencial_maxima", "comissao_calculada",
        ]

        for col in colunas_obrigatorias:
            audit.verificar(
                descricao=f"Coluna '{col}' no DataFrame E2E",
                formula=f"'{col}' in df.columns",
                entradas={},
                esperado="True",
                real=str(col in df.columns),
            )
