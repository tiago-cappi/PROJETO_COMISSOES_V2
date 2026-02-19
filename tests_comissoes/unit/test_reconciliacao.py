"""
Testes unitários para o módulo de Reconciliação.

Testa os 3 componentes principais:

    ReconciliacaoCalculator — Cálculo do ajuste:
        ajuste = comissao_adiantada × (FCMP - 1.0)
        comissao_deveria = comissao_adiantada × FCMP
        saldo_total = sum(ajustes)

    ReconciliacaoValidator — Validação:
        - Campos obrigatórios presentes
        - FCMP na faixa [0, 2.0]
        - Comissão adiantada >= 0
        - Consistência do cálculo (tolerância 0.01)

    ReconciliacaoAggregator — Agregação:
        - DataFrame formatado com colunas esperadas
        - Ordenação por processo + colaborador
        - Resumo agrupado por processo

Cenários cobertos:
    ── Calculator ──
    - Ajuste positivo (FCMP > 1.0 → colaborador recebe mais)
    - Ajuste negativo (FCMP < 1.0 → colaborador deve devolver)
    - Ajuste zero (FCMP = 1.0 → sem reconciliação)
    - Múltiplos colaboradores no mesmo processo
    - Comissão adiantada zero → ignorada
    - Saldo total com valores mistos
    - FCMP default 1.0 quando ausente

    ── Validator ──
    - Dados válidos → (True, "OK")
    - Processo ausente → inválido
    - TCMP ausente → inválido
    - FCMP fora da faixa → inválido
    - Comissão adiantada negativa → inválido
    - Cálculo inconsistente → inválido (tolerância 0.01)
    - Validação em lote

    ── Aggregator ──
    - Lista vazia → DataFrame com colunas esperadas
    - DataFrame ordenado por processo + colaborador
    - Colunas numéricas arredondadas para 6 casas
    - Resumo por processo com totais
"""

import pytest
import pandas as pd

from src.recebimento.reconciliacao.reconciliacao_calculator import ReconciliacaoCalculator
from src.recebimento.reconciliacao.reconciliacao_validator import ReconciliacaoValidator
from src.recebimento.reconciliacao.reconciliacao_aggregator import ReconciliacaoAggregator


# =========================================================================
# HELPERS
# =========================================================================

def _calcular_ajuste_formula(comissao_adiantada: float, fcmp: float) -> dict:
    """Reproduz a fórmula de reconciliação pura."""
    diferenca_fc = fcmp - 1.0
    ajuste = comissao_adiantada * diferenca_fc
    comissao_deveria = comissao_adiantada * fcmp
    return {
        "diferenca_fc": diferenca_fc,
        "ajuste_reconciliacao": ajuste,
        "comissao_deveria_fc_real": comissao_deveria,
    }


def _criar_reconciliacao_valida(**overrides) -> dict:
    """Cria um dict de reconciliação válido para testes do Validator."""
    rec = {
        "processo": "12345",
        "colaborador": "Samanta Silva",
        "tcmp": 0.05,
        "fcmp": 1.2,
        "comissao_adiantada_fc_1": 2500.0,
        "comissao_deveria_fc_real": 3000.0,
        "diferenca_fc": 0.2,
        "ajuste_reconciliacao": 500.0,
        "mes_faturamento": "04/2025",
    }
    rec.update(overrides)
    return rec


# =========================================================================
# CLASSE: TestReconciliacaoCalculator
# =========================================================================
@pytest.mark.unit
@pytest.mark.reconciliacao
class TestReconciliacaoCalculator:
    """Testa ReconciliacaoCalculator."""

    def test_ajuste_positivo_fcmp_maior_que_um(self, audit):
        """FCMP=1.2 → ajuste positivo (colaborador recebe mais)."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Ajuste positivo")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="12345",
            comissoes_adiantadas={"Samanta Silva": 2500.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.2},
            mes_faturamento="04/2025",
        )

        assert len(resultado) == 1
        r = resultado[0]
        esperado = _calcular_ajuste_formula(2500.0, 1.2)

        audit.verificar(
            descricao="Ajuste positivo FCMP=1.2",
            formula="2500 x (1.2 - 1.0) = 500.0",
            entradas={"comissao_adiantada": 2500, "fcmp": 1.2},
            esperado=esperado["ajuste_reconciliacao"],
            real=r["ajuste_reconciliacao"],
        )
        audit.verificar(
            descricao="Comissao deveria com FCMP real",
            formula="2500 x 1.2 = 3000.0",
            entradas={"comissao_adiantada": 2500, "fcmp": 1.2},
            esperado=esperado["comissao_deveria_fc_real"],
            real=r["comissao_deveria_fc_real"],
        )

    def test_ajuste_negativo_fcmp_menor_que_um(self, audit):
        """FCMP=0.8 → ajuste negativo (colaborador deve devolver)."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Ajuste negativo")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="22222",
            comissoes_adiantadas={"Andre Moraes": 3000.0},
            tcmp_dict={"Andre Moraes": 0.04},
            fcmp_dict={"Andre Moraes": 0.8},
            mes_faturamento="05/2025",
        )

        r = resultado[0]
        esperado = _calcular_ajuste_formula(3000.0, 0.8)

        audit.verificar(
            descricao="Ajuste negativo FCMP=0.8",
            formula="3000 x (0.8 - 1.0) = -600.0",
            entradas={"comissao_adiantada": 3000, "fcmp": 0.8},
            esperado=esperado["ajuste_reconciliacao"],
            real=r["ajuste_reconciliacao"],
        )

    def test_ajuste_zero_fcmp_igual_um(self, audit):
        """FCMP=1.0 → ajuste = 0 (sem reconciliação)."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Ajuste zero")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="33333",
            comissoes_adiantadas={"Ney Silva": 1500.0},
            tcmp_dict={"Ney Silva": 0.03},
            fcmp_dict={"Ney Silva": 1.0},
            mes_faturamento="06/2025",
        )

        r = resultado[0]

        audit.verificar(
            descricao="Ajuste zero FCMP=1.0",
            formula="1500 x (1.0 - 1.0) = 0.0",
            entradas={"comissao_adiantada": 1500, "fcmp": 1.0},
            esperado=0.0,
            real=r["ajuste_reconciliacao"],
        )

    def test_multiplos_colaboradores(self, audit):
        """Múltiplos colaboradores com FCMP distintos."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Multi colaboradores")

        calc = ReconciliacaoCalculator()
        comissoes = {"Samanta Silva": 2000.0, "Andre Moraes": 1500.0, "Ney Silva": 1000.0}
        fcmps = {"Samanta Silva": 1.3, "Andre Moraes": 0.7, "Ney Silva": 1.0}
        tcmps = {"Samanta Silva": 0.05, "Andre Moraes": 0.04, "Ney Silva": 0.03}

        resultado = calc.calcular_reconciliacao_processo(
            processo_id="44444",
            comissoes_adiantadas=comissoes,
            tcmp_dict=tcmps,
            fcmp_dict=fcmps,
            mes_faturamento="07/2025",
        )

        assert len(resultado) == 3

        for r in resultado:
            nome = r["colaborador"]
            esperado = _calcular_ajuste_formula(comissoes[nome], fcmps[nome])
            audit.verificar(
                descricao=f"Ajuste {nome}",
                formula=f"{comissoes[nome]} x ({fcmps[nome]} - 1.0)",
                entradas={"comissao": comissoes[nome], "fcmp": fcmps[nome]},
                esperado=esperado["ajuste_reconciliacao"],
                real=r["ajuste_reconciliacao"],
            )

    def test_comissao_adiantada_zero_ignorada(self, audit):
        """Comissão adiantada = 0 → colaborador ignorado."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Adiantada zero")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="55555",
            comissoes_adiantadas={"Samanta Silva": 0.0, "Andre Moraes": 1000.0},
            tcmp_dict={"Samanta Silva": 0.05, "Andre Moraes": 0.04},
            fcmp_dict={"Samanta Silva": 1.2, "Andre Moraes": 1.1},
            mes_faturamento="08/2025",
        )

        assert len(resultado) == 1
        audit.verificar(
            descricao="Adiantada zero ignorada",
            formula="valor_adiantado <= 0 -> skip",
            entradas={"adiantada_samanta": 0.0, "adiantada_andre": 1000.0},
            esperado=1,
            real=len(resultado),
        )

    def test_fcmp_ausente_default_um(self, audit):
        """FCMP não encontrado → default 1.0 → ajuste = 0."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="FCMP ausente default")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="66666",
            comissoes_adiantadas={"Samanta Silva": 2000.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={},  # vazio
            mes_faturamento="09/2025",
        )

        r = resultado[0]
        audit.verificar(
            descricao="FCMP ausente -> default 1.0 -> ajuste 0",
            formula="2000 x (1.0 - 1.0) = 0.0",
            entradas={"comissao_adiantada": 2000, "fcmp_default": 1.0},
            esperado=0.0,
            real=r["ajuste_reconciliacao"],
        )

    def test_saldo_total_processo(self, audit):
        """Saldo total = soma de todos os ajustes."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Saldo total")

        calc = ReconciliacaoCalculator()
        reconciliacoes = [
            {"ajuste_reconciliacao": 500.0},
            {"ajuste_reconciliacao": -300.0},
            {"ajuste_reconciliacao": 200.0},
        ]

        saldo = calc.calcular_saldo_total_processo(reconciliacoes)
        esperado = 500.0 + (-300.0) + 200.0

        audit.verificar(
            descricao="Saldo total processo",
            formula="500 + (-300) + 200 = 400.0",
            entradas={"ajustes": [500, -300, 200]},
            esperado=esperado,
            real=saldo,
        )

    def test_saldo_total_vazio(self, audit):
        """Lista vazia → saldo = 0."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Saldo vazio")

        calc = ReconciliacaoCalculator()
        saldo = calc.calcular_saldo_total_processo([])

        audit.verificar(
            descricao="Saldo total com lista vazia",
            formula="sum([]) = 0.0",
            entradas={},
            esperado=0.0,
            real=saldo,
        )

    def test_campos_saida_reconciliacao(self, audit):
        """Verifica campos obrigatórios no resultado."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Campos saida")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="88888",
            comissoes_adiantadas={"Samanta Silva": 1000.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.1},
            mes_faturamento="10/2025",
        )

        r = resultado[0]
        campos_esperados = [
            "processo", "colaborador", "tcmp", "fcmp",
            "comissao_adiantada_fc_1", "comissao_deveria_fc_real",
            "diferenca_fc", "ajuste_reconciliacao", "mes_faturamento",
        ]

        campos_presentes = [c for c in campos_esperados if c in r]
        audit.verificar(
            descricao="Todos campos obrigatorios presentes",
            formula="len(presentes) == len(esperados)",
            entradas={"campos_esperados": len(campos_esperados)},
            esperado=len(campos_esperados),
            real=len(campos_presentes),
        )

    def test_processo_trimado(self, audit):
        """Processo com espaços é trimado."""
        audit.set_contexto(modulo="Reconciliacao Calculator", cenario="Processo trim")

        calc = ReconciliacaoCalculator()
        resultado = calc.calcular_reconciliacao_processo(
            processo_id="  99999  ",
            comissoes_adiantadas={"Samanta Silva": 1000.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.0},
            mes_faturamento="11/2025",
        )

        audit.verificar(
            descricao="Processo trimado",
            formula="str.strip()",
            entradas={"processo_raw": "  99999  "},
            esperado="99999",
            real=resultado[0]["processo"],
        )


# =========================================================================
# CLASSE: TestReconciliacaoValidator
# =========================================================================
@pytest.mark.unit
@pytest.mark.reconciliacao
class TestReconciliacaoValidator:
    """Testa ReconciliacaoValidator."""

    def test_dados_processo_validos(self, audit):
        """Dados completos → (True, 'OK')."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Dados validos")

        validator = ReconciliacaoValidator()
        valido, msg = validator.validar_dados_processo({
            "processo": "12345",
            "tcmp": {"Samanta Silva": 0.05},
            "fcmp": {"Samanta Silva": 1.2},
            "comissoes_adiantadas": {"Samanta Silva": 2500.0},
            "total_adiantamentos": 2500.0,
        })

        audit.verificar(
            descricao="Dados processo validos",
            formula="Todos campos presentes e validos",
            entradas={"processo": "12345"},
            esperado="True",
            real=str(valido),
        )

    def test_processo_ausente(self, audit):
        """Processo ausente → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Processo ausente")

        validator = ReconciliacaoValidator()
        valido, msg = validator.validar_dados_processo({
            "tcmp": {"Samanta Silva": 0.05},
            "fcmp": {"Samanta Silva": 1.2},
            "comissoes_adiantadas": {"Samanta Silva": 2500.0},
            "total_adiantamentos": 2500.0,
        })

        audit.verificar(
            descricao="Processo ausente -> invalido",
            formula="dados.get('processo') == None",
            entradas={},
            esperado="False",
            real=str(valido),
        )

    def test_tcmp_ausente(self, audit):
        """TCMP ausente → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="TCMP ausente")

        validator = ReconciliacaoValidator()
        valido, msg = validator.validar_dados_processo({
            "processo": "12345",
            "fcmp": {"Samanta Silva": 1.2},
            "comissoes_adiantadas": {"Samanta Silva": 2500.0},
            "total_adiantamentos": 2500.0,
        })

        audit.verificar(
            descricao="TCMP ausente -> invalido",
            formula="dados.get('tcmp') == None",
            entradas={},
            esperado="False",
            real=str(valido),
        )

    def test_fcmp_ausente(self, audit):
        """FCMP ausente → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="FCMP ausente")

        validator = ReconciliacaoValidator()
        valido, msg = validator.validar_dados_processo({
            "processo": "12345",
            "tcmp": {"Samanta Silva": 0.05},
            "comissoes_adiantadas": {"Samanta Silva": 2500.0},
            "total_adiantamentos": 2500.0,
        })

        audit.verificar(
            descricao="FCMP ausente -> invalido",
            formula="dados.get('fcmp') == None",
            entradas={},
            esperado="False",
            real=str(valido),
        )

    def test_total_adiantamentos_zero(self, audit):
        """Total adiantamentos = 0 → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Adiantamentos zero")

        validator = ReconciliacaoValidator()
        valido, msg = validator.validar_dados_processo({
            "processo": "12345",
            "tcmp": {"Samanta Silva": 0.05},
            "fcmp": {"Samanta Silva": 1.2},
            "comissoes_adiantadas": {"Samanta Silva": 2500.0},
            "total_adiantamentos": 0.0,
        })

        audit.verificar(
            descricao="Adiantamentos zero -> invalido",
            formula="total_adiantamentos <= 0",
            entradas={"total_adiantamentos": 0.0},
            esperado="False",
            real=str(valido),
        )

    def test_reconciliacao_valida(self, audit):
        """Reconciliação válida → (True, 'OK')."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Reconciliacao valida")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida()
        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="Reconciliacao valida",
            formula="Todos campos presentes e consistentes",
            entradas={"fcmp": 1.2, "ajuste": 500},
            esperado="True",
            real=str(valido),
        )

    def test_campo_obrigatorio_ausente(self, audit):
        """Campo obrigatório ausente → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Campo ausente")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida()
        del rec["ajuste_reconciliacao"]

        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="Campo obrigatorio ausente -> invalido",
            formula="'ajuste_reconciliacao' not in rec",
            entradas={"campo_removido": "ajuste_reconciliacao"},
            esperado="False",
            real=str(valido),
        )

    def test_fcmp_acima_limite(self, audit):
        """FCMP > 2.0 → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="FCMP acima 2.0")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida(fcmp=2.5, diferenca_fc=1.5, ajuste_reconciliacao=3750.0)
        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="FCMP > 2.0 -> invalido",
            formula="fcmp > 2.0",
            entradas={"fcmp": 2.5},
            esperado="False",
            real=str(valido),
        )

    def test_fcmp_negativo_invalido(self, audit):
        """FCMP < 0 → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="FCMP negativo")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida(fcmp=-0.5, diferenca_fc=-1.5, ajuste_reconciliacao=-3750.0)
        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="FCMP negativo -> invalido",
            formula="fcmp < 0",
            entradas={"fcmp": -0.5},
            esperado="False",
            real=str(valido),
        )

    def test_comissao_adiantada_negativa(self, audit):
        """Comissão adiantada negativa → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Adiantada negativa")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida(comissao_adiantada_fc_1=-100.0)
        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="Comissao adiantada negativa -> invalido",
            formula="comissao_adiantada < 0",
            entradas={"comissao_adiantada": -100.0},
            esperado="False",
            real=str(valido),
        )

    def test_calculo_inconsistente(self, audit):
        """Ajuste não bate com fórmula (diff > 0.01) → inválido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Calculo inconsistente")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida(
            comissao_adiantada_fc_1=2500.0,
            diferenca_fc=0.2,
            ajuste_reconciliacao=600.0,  # deveria ser 500.0
        )
        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="Calculo inconsistente -> invalido",
            formula="abs(600 - (2500 x 0.2)) = 100 > 0.01",
            entradas={"ajuste": 600, "esperado": 500, "tolerancia": 0.01},
            esperado="False",
            real=str(valido),
        )

    def test_calculo_dentro_tolerancia(self, audit):
        """Ajuste dentro da tolerância de 0.01 → válido."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Dentro tolerancia")

        validator = ReconciliacaoValidator()
        rec = _criar_reconciliacao_valida(
            comissao_adiantada_fc_1=2500.0,
            diferenca_fc=0.2,
            ajuste_reconciliacao=500.005,  # diff = 0.005 < 0.01
        )
        valido, msg = validator.validar_reconciliacao(rec)

        audit.verificar(
            descricao="Ajuste dentro tolerancia 0.01 -> valido",
            formula="abs(500.005 - 500.0) = 0.005 <= 0.01",
            entradas={"ajuste": 500.005, "esperado": 500.0},
            esperado="True",
            real=str(valido),
        )

    def test_validar_todas_com_erro(self, audit):
        """Lote com 1 inválido → retorna erros."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Lote com erro")

        validator = ReconciliacaoValidator()
        rec_ok = _criar_reconciliacao_valida()
        rec_bad = _criar_reconciliacao_valida(fcmp=3.0, diferenca_fc=2.0, ajuste_reconciliacao=5000.0)

        valido, erros = validator.validar_todas_reconciliacoes([rec_ok, rec_bad])

        audit.verificar(
            descricao="Lote com 1 erro -> nao valido",
            formula="len(erros) > 0",
            entradas={"total": 2, "invalidos": 1},
            esperado="False",
            real=str(valido),
        )
        audit.verificar(
            descricao="Apenas 1 erro na lista",
            formula="len(erros)",
            entradas={},
            esperado=1,
            real=len(erros),
        )

    def test_validar_todas_ok(self, audit):
        """Lote todo válido → (True, [])."""
        audit.set_contexto(modulo="Reconciliacao Validator", cenario="Lote todo ok")

        validator = ReconciliacaoValidator()
        recs = [_criar_reconciliacao_valida(), _criar_reconciliacao_valida(colaborador="Andre Moraes")]

        valido, erros = validator.validar_todas_reconciliacoes(recs)

        audit.verificar(
            descricao="Lote todo valido",
            formula="len(erros) == 0",
            entradas={"total": 2},
            esperado="True",
            real=str(valido),
        )


# =========================================================================
# CLASSE: TestReconciliacaoAggregator
# =========================================================================
@pytest.mark.unit
@pytest.mark.reconciliacao
class TestReconciliacaoAggregator:
    """Testa ReconciliacaoAggregator."""

    def test_lista_vazia_retorna_df_com_colunas(self, audit):
        """Lista vazia → DataFrame vazio com colunas esperadas."""
        audit.set_contexto(modulo="Reconciliacao Aggregator", cenario="Lista vazia")

        agg = ReconciliacaoAggregator()
        df = agg.criar_dataframe_reconciliacoes([])

        colunas_esperadas = [
            "processo", "colaborador", "tcmp", "fcmp",
            "comissao_adiantada_fc_1", "comissao_deveria_fc_real",
            "diferenca_fc", "ajuste_reconciliacao", "mes_faturamento",
        ]

        audit.verificar(
            descricao="DF vazio com colunas esperadas",
            formula="len(df) == 0 and colunas corretas",
            entradas={"n_colunas_esperadas": len(colunas_esperadas)},
            esperado=len(colunas_esperadas),
            real=len(df.columns),
        )

    def test_dataframe_ordenado(self, audit):
        """DataFrame ordenado por processo + colaborador."""
        audit.set_contexto(modulo="Reconciliacao Aggregator", cenario="Ordenacao")

        agg = ReconciliacaoAggregator()
        recs = [
            _criar_reconciliacao_valida(processo="99999", colaborador="Zzz"),
            _criar_reconciliacao_valida(processo="11111", colaborador="Bbb"),
            _criar_reconciliacao_valida(processo="11111", colaborador="Aaa"),
            _criar_reconciliacao_valida(processo="99999", colaborador="Aaa"),
        ]
        df = agg.criar_dataframe_reconciliacoes(recs)

        processos = df["processo"].tolist()
        colaboradores = df["colaborador"].tolist()

        audit.verificar(
            descricao="Primeiro processo = 11111",
            formula="sort_values(['processo', 'colaborador'])",
            entradas={"processos": processos},
            esperado="11111",
            real=processos[0],
        )
        audit.verificar(
            descricao="Primeiro colaborador do 11111 = Aaa",
            formula="sort_values(['processo', 'colaborador'])",
            entradas={"colaboradores": colaboradores},
            esperado="Aaa",
            real=colaboradores[0],
        )

    def test_colunas_numericas_arredondadas(self, audit):
        """Colunas numéricas arredondadas para 6 casas."""
        audit.set_contexto(modulo="Reconciliacao Aggregator", cenario="Arredondamento")

        agg = ReconciliacaoAggregator()
        rec = _criar_reconciliacao_valida(
            fcmp=1.123456789,
            diferenca_fc=0.123456789,
            ajuste_reconciliacao=308.641972250,
        )
        df = agg.criar_dataframe_reconciliacoes([rec])

        fcmp_resultado = df["fcmp"].iloc[0]

        audit.verificar(
            descricao="FCMP arredondado para 6 casas",
            formula="round(1.123456789, 6) = 1.123457",
            entradas={"fcmp_raw": 1.123456789},
            esperado=round(1.123456789, 6),
            real=fcmp_resultado,
        )

    def test_resumo_por_processo(self, audit):
        """Resumo agrupado por processo com totais."""
        audit.set_contexto(modulo="Reconciliacao Aggregator", cenario="Resumo por processo")

        agg = ReconciliacaoAggregator()
        recs = [
            _criar_reconciliacao_valida(
                processo="11111", colaborador="Samanta",
                comissao_adiantada_fc_1=2000.0,
                comissao_deveria_fc_real=2400.0,
                ajuste_reconciliacao=400.0,
                mes_faturamento="04/2025",
            ),
            _criar_reconciliacao_valida(
                processo="11111", colaborador="Andre",
                comissao_adiantada_fc_1=1000.0,
                comissao_deveria_fc_real=1200.0,
                ajuste_reconciliacao=200.0,
                mes_faturamento="04/2025",
            ),
            _criar_reconciliacao_valida(
                processo="22222", colaborador="Ney",
                comissao_adiantada_fc_1=3000.0,
                comissao_deveria_fc_real=2400.0,
                ajuste_reconciliacao=-600.0,
                mes_faturamento="05/2025",
            ),
        ]

        resumo = agg.criar_resumo_por_processo(recs)

        # Processo 11111: total_adiantadas=3000, total_ajustadas=3600, saldo=600
        proc_11111 = resumo[resumo["processo"] == "11111"].iloc[0]

        audit.verificar(
            descricao="Total adiantadas processo 11111",
            formula="2000 + 1000 = 3000",
            entradas={"comissoes": [2000, 1000]},
            esperado=3000.0,
            real=proc_11111["total_comissoes_adiantadas"],
        )
        audit.verificar(
            descricao="Total ajustadas processo 11111",
            formula="2400 + 1200 = 3600",
            entradas={"comissoes": [2400, 1200]},
            esperado=3600.0,
            real=proc_11111["total_comissoes_ajustadas"],
        )
        audit.verificar(
            descricao="Saldo reconciliacao processo 11111",
            formula="400 + 200 = 600",
            entradas={"ajustes": [400, 200]},
            esperado=600.0,
            real=proc_11111["saldo_reconciliacao"],
        )

        # Processo 22222: saldo negativo
        proc_22222 = resumo[resumo["processo"] == "22222"].iloc[0]

        audit.verificar(
            descricao="Saldo reconciliacao processo 22222 (negativo)",
            formula="-600.0",
            entradas={"ajustes": [-600]},
            esperado=-600.0,
            real=proc_22222["saldo_reconciliacao"],
        )

    def test_resumo_vazio(self, audit):
        """Lista vazia → resumo DataFrame vazio."""
        audit.set_contexto(modulo="Reconciliacao Aggregator", cenario="Resumo vazio")

        agg = ReconciliacaoAggregator()
        resumo = agg.criar_resumo_por_processo([])

        audit.verificar(
            descricao="Resumo vazio para lista vazia",
            formula="len(resumo) == 0",
            entradas={},
            esperado=0,
            real=len(resumo),
        )

    def test_resumo_mes_faturamento_first(self, audit):
        """Resumo usa 'first' para mes_faturamento."""
        audit.set_contexto(modulo="Reconciliacao Aggregator", cenario="Resumo mes_faturamento")

        agg = ReconciliacaoAggregator()
        recs = [
            _criar_reconciliacao_valida(processo="11111", mes_faturamento="04/2025"),
            _criar_reconciliacao_valida(processo="11111", colaborador="Andre", mes_faturamento="04/2025"),
        ]

        resumo = agg.criar_resumo_por_processo(recs)
        proc = resumo[resumo["processo"] == "11111"].iloc[0]

        audit.verificar(
            descricao="mes_faturamento usa aggregacao 'first'",
            formula="groupby.agg({'mes_faturamento': 'first'})",
            entradas={},
            esperado="04/2025",
            real=proc["mes_faturamento"],
        )
