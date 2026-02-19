"""
Testes de integração: Pipeline completo de Reconciliação.

Valida o fluxo end-to-end:

    1. ComissaoCalculator.calcular_adiantamento()  → comissões adiantadas
    2. ComissaoCalculator.calcular_regular()        → comissões com FCMP real
    3. ReconciliacaoCalculator.calcular_reconciliacao_processo() → ajustes
    4. ReconciliacaoValidator.validar_reconciliacao()            → validação
    5. ReconciliacaoAggregator.criar_dataframe_reconciliacoes()  → saída final

Pipeline integrado:
    Adiantamento (FC=1) → NF (FC real) → Reconciliação → Validação → Agregação → DataFrame

Cenários:
    - Pipeline completo: adiantamento → regular → reconcilia → valida → agrega
    - FCMP > 1: colaborador recebe diferença positiva
    - FCMP < 1: colaborador deve devolver parte
    - FCMP = 1: ajuste zero, sem saldo
    - Múltiplos colaboradores com FCMPs distintos
    - Múltiplos processos no mesmo lote → agregação/resumo
    - Validação rejeita dado inconsistente mid-pipeline
    - Saldo total correto (soma algébrica de ajustes)
    - Pipeline com COT+NF mapeados + reconciliação encadeada
    - Resumo por processo com totais corretos
"""

import pytest
import pandas as pd
from datetime import datetime

from src.recebimento.core.comissao_calculator import ComissaoCalculator
from src.recebimento.reconciliacao.reconciliacao_calculator import ReconciliacaoCalculator
from src.recebimento.reconciliacao.reconciliacao_validator import ReconciliacaoValidator
from src.recebimento.reconciliacao.reconciliacao_aggregator import ReconciliacaoAggregator


# =========================================================================
# HELPERS
# =========================================================================

def _adiantar_e_reconciliar(
    valor_cot: float,
    tcmp_dict: dict,
    fcmp_dict: dict,
    processo_id: str = "INT001",
    mes_faturamento: str = "06/2025",
) -> dict:
    """Executa pipeline: adiantamento → reconciliação → validação → agregação.

    Returns:
        Dict com 'adiantamentos', 'reconciliacoes', 'validacoes', 'df', 'saldo'.
    """
    calc = ComissaoCalculator()
    rec_calc = ReconciliacaoCalculator()
    validator = ReconciliacaoValidator()
    aggregator = ReconciliacaoAggregator()

    # 1) Calcular adiantamento (FC = 1.0)
    adiantamentos = calc.calcular_adiantamento(
        processo=processo_id,
        valor=valor_cot,
        tcmp_dict=tcmp_dict,
        documento=f"COT{processo_id}",
        data_pagamento=datetime(2025, 3, 15),
    )

    # Construir dict comissoes_adiantadas para reconciliação
    comissoes_adiantadas = {
        a["nome_colaborador"]: a["comissao_calculada"]
        for a in adiantamentos
    }

    # 2) Calcular reconciliação
    reconciliacoes = rec_calc.calcular_reconciliacao_processo(
        processo_id=processo_id,
        comissoes_adiantadas=comissoes_adiantadas,
        tcmp_dict=tcmp_dict,
        fcmp_dict=fcmp_dict,
        mes_faturamento=mes_faturamento,
    )

    # 3) Validar cada reconciliação
    validacoes = []
    for rec in reconciliacoes:
        valido, msg = validator.validar_reconciliacao(rec)
        validacoes.append({"valido": valido, "mensagem": msg})

    # 4) Agregar em DataFrame
    df = aggregator.criar_dataframe_reconciliacoes(reconciliacoes)

    # 5) Saldo total
    saldo = rec_calc.calcular_saldo_total_processo(reconciliacoes)

    return {
        "adiantamentos": adiantamentos,
        "reconciliacoes": reconciliacoes,
        "validacoes": validacoes,
        "df": df,
        "saldo": saldo,
    }


# =========================================================================
# CLASSE: TestReconciliacaoPipelineIntegrado
# =========================================================================
@pytest.mark.integration
@pytest.mark.reconciliacao
@pytest.mark.recebimento
class TestReconciliacaoPipelineIntegrado:
    """Testa Calculator → Validator → Aggregator como pipeline."""

    def test_pipeline_completo_fcmp_positivo(self, audit):
        """FCMP=1.2 → ajuste positivo no pipeline completo."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Pipeline FCMP positivo"
        )

        resultado = _adiantar_e_reconciliar(
            valor_cot=100_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.2},
        )

        # Adiantamento: 100000 * 0.05 * 1.0 = 5000
        ad = resultado["adiantamentos"][0]
        audit.verificar(
            descricao="Adiantamento calculado",
            formula="100000 x 0.05 x 1.0 = 5000",
            entradas={"valor": 100_000, "tcmp": 0.05},
            esperado=5000.0,
            real=ad["comissao_calculada"],
        )

        # Reconciliação: 5000 * (1.2 - 1.0) = 1000
        rec = resultado["reconciliacoes"][0]
        audit.verificar(
            descricao="Ajuste reconciliacao positivo",
            formula="5000 x (1.2 - 1.0) = 1000",
            entradas={"comissao_adiantada": 5000, "fcmp": 1.2},
            esperado=1000.0,
            real=rec["ajuste_reconciliacao"],
        )

        # Comissão deveria: 5000 * 1.2 = 6000
        audit.verificar(
            descricao="Comissao deveria com FC real",
            formula="5000 x 1.2 = 6000",
            entradas={},
            esperado=6000.0,
            real=rec["comissao_deveria_fc_real"],
        )

        # Validação OK
        val = resultado["validacoes"][0]
        audit.verificar(
            descricao="Validacao passou",
            formula="validar_reconciliacao -> True",
            entradas={},
            esperado="True",
            real=str(val["valido"]),
        )

        # DataFrame não vazio
        assert len(resultado["df"]) == 1

        # Saldo total = 1000
        audit.verificar(
            descricao="Saldo total pipeline",
            formula="sum(ajustes) = 1000",
            entradas={},
            esperado=1000.0,
            real=resultado["saldo"],
        )

    def test_pipeline_completo_fcmp_negativo(self, audit):
        """FCMP=0.7 → ajuste negativo (colaborador deve devolver)."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Pipeline FCMP negativo"
        )

        resultado = _adiantar_e_reconciliar(
            valor_cot=80_000.0,
            tcmp_dict={"Andre Moraes": 0.04},
            fcmp_dict={"Andre Moraes": 0.7},
        )

        # Adiantamento: 80000 * 0.04 * 1.0 = 3200
        ad = resultado["adiantamentos"][0]
        audit.verificar(
            descricao="Adiantamento Andre",
            formula="80000 x 0.04 x 1.0 = 3200",
            entradas={"valor": 80_000, "tcmp": 0.04},
            esperado=3200.0,
            real=ad["comissao_calculada"],
        )

        # Reconciliação: 3200 * (0.7 - 1.0) = -960
        rec = resultado["reconciliacoes"][0]
        audit.verificar(
            descricao="Ajuste negativo (devolucao parcial)",
            formula="3200 x (0.7 - 1.0) = -960",
            entradas={"comissao_adiantada": 3200, "fcmp": 0.7},
            esperado=-960.0,
            real=rec["ajuste_reconciliacao"],
        )

        # Saldo negativo
        audit.verificar(
            descricao="Saldo negativo total",
            formula="sum(ajustes) = -960",
            entradas={},
            esperado=-960.0,
            real=resultado["saldo"],
        )

    def test_pipeline_fcmp_um_sem_ajuste(self, audit):
        """FCMP=1.0 → ajuste zero, sem saldo."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="FCMP=1 sem ajuste"
        )

        resultado = _adiantar_e_reconciliar(
            valor_cot=60_000.0,
            tcmp_dict={"Ney Silva": 0.03},
            fcmp_dict={"Ney Silva": 1.0},
        )

        rec = resultado["reconciliacoes"][0]
        audit.verificar(
            descricao="Ajuste zero FCMP=1.0",
            formula="1800 x (1.0 - 1.0) = 0",
            entradas={"comissao_adiantada": 1800, "fcmp": 1.0},
            esperado=0.0,
            real=rec["ajuste_reconciliacao"],
        )
        audit.verificar(
            descricao="Saldo zero",
            formula="sum(0) = 0",
            entradas={},
            esperado=0.0,
            real=resultado["saldo"],
        )

    def test_multiplos_colaboradores_fcmp_distintos(self, audit):
        """3 colaboradores com FCMPs distintos → saldo algébrico correto."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Multi-colab pipeline"
        )

        tcmp = {"Samanta Silva": 0.05, "Andre Moraes": 0.04, "Ney Silva": 0.03}
        fcmp = {"Samanta Silva": 1.3, "Andre Moraes": 0.6, "Ney Silva": 1.0}

        resultado = _adiantar_e_reconciliar(
            valor_cot=200_000.0,
            tcmp_dict=tcmp,
            fcmp_dict=fcmp,
        )

        assert len(resultado["adiantamentos"]) == 3
        assert len(resultado["reconciliacoes"]) == 3

        # Calcular esperados para cada colaborador
        esperados = {}
        for nome in tcmp:
            ad = 200_000.0 * tcmp[nome] * 1.0
            ajuste = ad * (fcmp[nome] - 1.0)
            esperados[nome] = {"adiantamento": ad, "ajuste": ajuste}

        saldo_esperado = sum(e["ajuste"] for e in esperados.values())

        for rec in resultado["reconciliacoes"]:
            nome = rec["colaborador"]
            audit.verificar(
                descricao=f"Ajuste {nome}",
                formula=f"{esperados[nome]['adiantamento']} x ({fcmp[nome]} - 1.0)",
                entradas={"comissao_adiantada": esperados[nome]["adiantamento"], "fcmp": fcmp[nome]},
                esperado=esperados[nome]["ajuste"],
                real=rec["ajuste_reconciliacao"],
            )

        audit.verificar(
            descricao="Saldo total algebrico",
            formula="sum(ajustes positivos + negativos)",
            entradas={"componentes": list(esperados.keys())},
            esperado=saldo_esperado,
            real=resultado["saldo"],
        )

        # Todas validações OK
        todas_validas = all(v["valido"] for v in resultado["validacoes"])
        audit.verificar(
            descricao="Todas validacoes OK",
            formula="all(valido == True)",
            entradas={},
            esperado="True",
            real=str(todas_validas),
        )

    def test_pipeline_dataframe_ordenado(self, audit):
        """DataFrame de saída ordenado por processo + colaborador."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="DF ordenacao"
        )

        tcmp = {"Zezinho": 0.05, "Ana Luz": 0.04}
        fcmp = {"Zezinho": 1.1, "Ana Luz": 0.9}

        resultado = _adiantar_e_reconciliar(
            valor_cot=50_000.0,
            tcmp_dict=tcmp,
            fcmp_dict=fcmp,
            processo_id="ORD001",
        )

        df = resultado["df"]
        assert len(df) == 2

        # Verificar ordenação
        nomes_ordenados = df["colaborador"].tolist()
        audit.verificar(
            descricao="DataFrame ordenado por colaborador",
            formula="sort_values(['processo', 'colaborador'])",
            entradas={"nomes": nomes_ordenados},
            esperado=sorted(nomes_ordenados),
            real=nomes_ordenados,
        )

    def test_validacao_rejeita_dado_corrompido(self, audit):
        """Se dado inconsistente, validação captura mid-pipeline."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Validacao rejeita"
        )

        validator = ReconciliacaoValidator()

        # Reconciliação com cálculo errado (ajuste inconsistente)
        rec_inconsistente = {
            "processo": "ERR001",
            "colaborador": "Teste",
            "tcmp": 0.05,
            "fcmp": 1.2,
            "comissao_adiantada_fc_1": 5000.0,
            "comissao_deveria_fc_real": 6000.0,
            "diferenca_fc": 0.2,
            "ajuste_reconciliacao": 9999.0,  # ERRADO: deveria ser 1000
            "mes_faturamento": "06/2025",
        }

        valido, msg = validator.validar_reconciliacao(rec_inconsistente)

        audit.verificar(
            descricao="Validacao detecta calculo inconsistente",
            formula="ajuste != comissao_adiantada * diferenca_fc -> False",
            entradas={"ajuste_real": 9999, "ajuste_esperado": 1000},
            esperado="False",
            real=str(valido),
        )
        audit.verificar(
            descricao="Mensagem de erro menciona inconsistencia",
            formula="'inconsistente' in msg",
            entradas={"msg": msg},
            esperado="True",
            real=str("inconsistente" in msg.lower()),
        )


# =========================================================================
# CLASSE: TestMultiProcessoReconciliacao
# =========================================================================
@pytest.mark.integration
@pytest.mark.reconciliacao
@pytest.mark.recebimento
class TestMultiProcessoReconciliacao:
    """Testa reconciliação com múltiplos processos (lote)."""

    def test_dois_processos_agregados(self, audit):
        """2 processos distintos → resumo por processo com totais."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Multi-processo agregacao"
        )

        rec_calc = ReconciliacaoCalculator()
        aggregator = ReconciliacaoAggregator()

        # Processo 1: Samanta, FCMP=1.2 → ajuste positivo
        recs_p1 = rec_calc.calcular_reconciliacao_processo(
            processo_id="MP001",
            comissoes_adiantadas={"Samanta Silva": 5000.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.2},
            mes_faturamento="04/2025",
        )

        # Processo 2: Andre, FCMP=0.8 → ajuste negativo
        recs_p2 = rec_calc.calcular_reconciliacao_processo(
            processo_id="MP002",
            comissoes_adiantadas={"Andre Moraes": 3000.0},
            tcmp_dict={"Andre Moraes": 0.04},
            fcmp_dict={"Andre Moraes": 0.8},
            mes_faturamento="05/2025",
        )

        todas = recs_p1 + recs_p2

        # DataFrame completo
        df = aggregator.criar_dataframe_reconciliacoes(todas)
        assert len(df) == 2

        # Resumo por processo
        resumo = aggregator.criar_resumo_por_processo(todas)
        assert len(resumo) == 2

        # Verificar totais por processo
        r_mp1 = resumo[resumo["processo"] == "MP001"].iloc[0]
        r_mp2 = resumo[resumo["processo"] == "MP002"].iloc[0]

        audit.verificar(
            descricao="Saldo reconciliacao processo MP001",
            formula="5000 x (1.2 - 1.0) = 1000",
            entradas={"processo": "MP001", "fcmp": 1.2},
            esperado=1000.0,
            real=r_mp1["saldo_reconciliacao"],
        )
        audit.verificar(
            descricao="Saldo reconciliacao processo MP002",
            formula="3000 x (0.8 - 1.0) = -600",
            entradas={"processo": "MP002", "fcmp": 0.8},
            esperado=-600.0,
            real=r_mp2["saldo_reconciliacao"],
        )

    def test_resumo_colunas_renomeadas(self, audit):
        """Resumo por processo tem colunas com nomes de negócio."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Resumo colunas"
        )

        rec_calc = ReconciliacaoCalculator()
        aggregator = ReconciliacaoAggregator()

        recs = rec_calc.calcular_reconciliacao_processo(
            processo_id="COL001",
            comissoes_adiantadas={"Samanta Silva": 4000.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.1},
            mes_faturamento="07/2025",
        )

        resumo = aggregator.criar_resumo_por_processo(recs)

        colunas_esperadas = [
            "processo",
            "total_comissoes_adiantadas",
            "total_comissoes_ajustadas",
            "saldo_reconciliacao",
        ]

        for col in colunas_esperadas:
            audit.verificar(
                descricao=f"Coluna '{col}' presente no resumo",
                formula=f"'{col}' in resumo.columns",
                entradas={},
                esperado="True",
                real=str(col in resumo.columns),
            )

    def test_lote_validacao_todas(self, audit):
        """Validação em lote: todas reconciliações válidas."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Validacao lote"
        )

        rec_calc = ReconciliacaoCalculator()
        validator = ReconciliacaoValidator()

        # 3 processos válidos
        todas_recs = []
        processos = [
            ("L001", {"Samanta Silva": 3000.0}, {"Samanta Silva": 1.1}),
            ("L002", {"Andre Moraes": 2000.0}, {"Andre Moraes": 0.9}),
            ("L003", {"Ney Silva": 1500.0}, {"Ney Silva": 1.0}),
        ]

        for proc_id, comissoes, fcmps in processos:
            tcmps = {k: 0.05 for k in comissoes}
            recs = rec_calc.calcular_reconciliacao_processo(
                processo_id=proc_id,
                comissoes_adiantadas=comissoes,
                tcmp_dict=tcmps,
                fcmp_dict=fcmps,
                mes_faturamento="08/2025",
            )
            todas_recs.extend(recs)

        todas_validas, erros = validator.validar_todas_reconciliacoes(todas_recs)

        audit.verificar(
            descricao="Todas reconciliacoes validas no lote",
            formula="validar_todas -> (True, [])",
            entradas={"num_processos": 3},
            esperado="True",
            real=str(todas_validas),
        )
        audit.verificar(
            descricao="Zero erros na validacao",
            formula="len(erros) == 0",
            entradas={},
            esperado=0,
            real=len(erros),
        )

    def test_saldo_total_multi_processo(self, audit):
        """Saldo total global = soma de saldos individuais."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Saldo total global"
        )

        rec_calc = ReconciliacaoCalculator()

        # P1: ajuste +500, P2: ajuste -300
        recs_p1 = rec_calc.calcular_reconciliacao_processo(
            processo_id="ST001",
            comissoes_adiantadas={"Samanta Silva": 2500.0},
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.2},
            mes_faturamento="09/2025",
        )
        recs_p2 = rec_calc.calcular_reconciliacao_processo(
            processo_id="ST002",
            comissoes_adiantadas={"Andre Moraes": 1500.0},
            tcmp_dict={"Andre Moraes": 0.04},
            fcmp_dict={"Andre Moraes": 0.8},
            mes_faturamento="09/2025",
        )

        todas = recs_p1 + recs_p2
        saldo_global = rec_calc.calcular_saldo_total_processo(todas)

        # P1: 2500*(1.2-1.0) = 500
        # P2: 1500*(0.8-1.0) = -300
        # Total: 200
        audit.verificar(
            descricao="Saldo global multi-processo",
            formula="500 + (-300) = 200",
            entradas={"ajuste_p1": 500, "ajuste_p2": -300},
            esperado=200.0,
            real=saldo_global,
        )


# =========================================================================
# CLASSE: TestAdiantamentoReconciliacaoEncadeado
# =========================================================================
@pytest.mark.integration
@pytest.mark.reconciliacao
@pytest.mark.recebimento
class TestAdiantamentoReconciliacaoEncadeado:
    """Testa adiantamento → reconciliação encadeados com verificação cruzada."""

    def test_adiantamento_mais_reconciliacao_igual_regular(self, audit):
        """adiantamento + ajuste_reconciliacao == comissao_com_fcmp_real.

        Propriedade matemática:
            ad = V * T * 1.0
            ajuste = ad * (FCMP - 1.0) = ad * FCMP - ad
            ad + ajuste = ad * FCMP = V * T * FCMP = regular
        """
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Propriedade ad+ajuste=regular"
        )

        valor = 120_000.0
        tcmp = 0.05
        fcmp = 1.35

        resultado = _adiantar_e_reconciliar(
            valor_cot=valor,
            tcmp_dict={"Samanta Silva": tcmp},
            fcmp_dict={"Samanta Silva": fcmp},
        )

        ad_valor = resultado["adiantamentos"][0]["comissao_calculada"]
        ajuste = resultado["reconciliacoes"][0]["ajuste_reconciliacao"]
        total = ad_valor + ajuste
        regular_esperado = valor * tcmp * fcmp

        audit.verificar(
            descricao="ad + ajuste == regular (propriedade matematica)",
            formula=f"{ad_valor} + {ajuste} == {regular_esperado}",
            entradas={"valor": valor, "tcmp": tcmp, "fcmp": fcmp},
            esperado=round(regular_esperado, 2),
            real=round(total, 2),
        )

    def test_reconciliacao_preserva_mes_faturamento(self, audit):
        """Mês de faturamento propagado do cálculo até o DataFrame final."""
        audit.set_contexto(
            modulo="Integracao Reconciliacao", cenario="Mes faturamento preservado"
        )

        resultado = _adiantar_e_reconciliar(
            valor_cot=50_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.1},
            mes_faturamento="11/2025",
        )

        # No dict de reconciliação
        rec = resultado["reconciliacoes"][0]
        audit.verificar(
            descricao="mes_faturamento no dict",
            formula="Passthrough do calcular_reconciliacao_processo",
            entradas={},
            esperado="11/2025",
            real=rec["mes_faturamento"],
        )

        # No DataFrame
        df = resultado["df"]
        valor_df = df.iloc[0]["mes_faturamento"]
        audit.verificar(
            descricao="mes_faturamento no DataFrame",
            formula="Passthrough do aggregator",
            entradas={},
            esperado="11/2025",
            real=valor_df,
        )
