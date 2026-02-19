"""
Testes E2E: Pipeline completo de Comissão por Recebimento.

Simula o fluxo end-to-end do RecebimentoOrchestrator:

    1. Carregar Análise Financeira (pagamentos)
    2. Para cada pagamento:
        a. ProcessMapper.mapear_documento() → tipo + processo
        b. Se COT → calcular_adiantamento (FC=1.0)
        c. Se NF  → calcular_regular (com FCMP real)
    3. Reconciliar processos faturados (adiantamento + ajuste = regular)
    4. Validar todas as reconciliações
    5. Agregar em DataFrames finais (detalhado + resumo)

Pipeline completo:
    Pagamentos → Mapper → Calculator → Reconciliação → Validação → Agregação → Saída

Cenários E2E:
    - Processo simples: COT (adiantamento FC=1) → NF (regular FCMP real) → reconcilia
    - Processo sem COT: NF direto → regular sem reconciliação
    - Múltiplos processos: 2 COTs + 2 NFs no mesmo lote
    - Propriedade matemática: adiantamento + ajuste = regular
    - Consistência: validação + agregação + resumo sem erros
    - Colunas de saída completas para equipe financeira
"""

import pytest
import pandas as pd
from datetime import datetime

from src.recebimento.core.process_mapper import ProcessMapper
from src.recebimento.core.comissao_calculator import ComissaoCalculator
from src.recebimento.reconciliacao.reconciliacao_calculator import ReconciliacaoCalculator
from src.recebimento.reconciliacao.reconciliacao_validator import ReconciliacaoValidator
from src.recebimento.reconciliacao.reconciliacao_aggregator import ReconciliacaoAggregator


# =========================================================================
# HELPERS: Pipeline E2E completo
# =========================================================================

def _criar_df_comercial(itens: list) -> pd.DataFrame:
    """Cria DataFrame simulando Análise Comercial Completa."""
    return pd.DataFrame(itens)


def _pipeline_recebimento_e2e(
    pagamentos: list,
    df_comercial: pd.DataFrame,
    tcmp_dict: dict,
    fcmp_dict: dict,
    mes_faturamento: str = "06/2025",
) -> dict:
    """Executa o pipeline E2E completo de recebimento.

    Args:
        pagamentos: Lista de dicts com {documento, valor, data_pagamento}.
        df_comercial: DataFrame da Análise Comercial.
        tcmp_dict: Dict {colaborador: tcmp} global.
        fcmp_dict: Dict {colaborador: fcmp} global.
        mes_faturamento: Mês/ano referência para regulares.

    Returns:
        Dict com 'adiantamentos', 'regulares', 'reconciliacoes',
        'validacoes', 'df_reconciliacoes', 'resumo', 'nao_mapeados',
        'saldo_total'.
    """
    mapper = ProcessMapper(df_comercial)
    calculator = ComissaoCalculator()
    rec_calc = ReconciliacaoCalculator()
    validator = ReconciliacaoValidator()
    aggregator = ReconciliacaoAggregator()

    adiantamentos = []
    regulares = []
    nao_mapeados = []
    comissoes_adiantadas_por_processo = {}  # {processo: {colab: valor}}

    # 1. Processar cada pagamento
    for pag in pagamentos:
        documento = pag["documento"]
        valor = pag["valor"]
        data_pag = pag.get("data_pagamento")

        try:
            mapeamento = mapper.mapear_documento(documento)
        except Exception:
            nao_mapeados.append({"documento": documento, "motivo": "Erro no mapeamento"})
            continue

        if not mapeamento.get("mapeado"):
            nao_mapeados.append({"documento": documento, "motivo": mapeamento.get("motivo", "N/A")})
            continue

        tipo = mapeamento["tipo"]
        processo = mapeamento["processo"]

        if tipo == "ADIANTAMENTO":
            comissoes = calculator.calcular_adiantamento(
                processo=processo,
                valor=valor,
                tcmp_dict=tcmp_dict,
                documento=documento,
                data_pagamento=data_pag,
            )
            adiantamentos.extend(comissoes)

            # Acumular para reconciliação
            if processo not in comissoes_adiantadas_por_processo:
                comissoes_adiantadas_por_processo[processo] = {}
            for c in comissoes:
                nome = c["nome_colaborador"]
                comissoes_adiantadas_por_processo[processo].setdefault(nome, 0.0)
                comissoes_adiantadas_por_processo[processo][nome] += c["comissao_calculada"]

        elif tipo == "PAGAMENTO_REGULAR":
            comissoes = calculator.calcular_regular(
                processo=processo,
                valor=valor,
                tcmp_dict=tcmp_dict,
                fcmp_dict=fcmp_dict,
                documento=documento,
                data_pagamento=data_pag,
                mes_faturamento=mes_faturamento,
            )
            regulares.extend(comissoes)

    # 2. Reconciliar processos que tiveram adiantamento
    todas_reconciliacoes = []
    for processo, comissoes_ad in comissoes_adiantadas_por_processo.items():
        recs = rec_calc.calcular_reconciliacao_processo(
            processo_id=processo,
            comissoes_adiantadas=comissoes_ad,
            tcmp_dict=tcmp_dict,
            fcmp_dict=fcmp_dict,
            mes_faturamento=mes_faturamento,
        )
        todas_reconciliacoes.extend(recs)

    # 3. Validar
    todas_validas, erros = validator.validar_todas_reconciliacoes(todas_reconciliacoes)

    # 4. Agregar
    df_rec = aggregator.criar_dataframe_reconciliacoes(todas_reconciliacoes)
    resumo = aggregator.criar_resumo_por_processo(todas_reconciliacoes)

    # 5. Saldo total
    saldo = rec_calc.calcular_saldo_total_processo(todas_reconciliacoes)

    return {
        "adiantamentos": adiantamentos,
        "regulares": regulares,
        "reconciliacoes": todas_reconciliacoes,
        "validacoes_ok": todas_validas,
        "validacao_erros": erros,
        "df_reconciliacoes": df_rec,
        "resumo": resumo,
        "nao_mapeados": nao_mapeados,
        "saldo_total": saldo,
        "comissoes_adiantadas_por_processo": comissoes_adiantadas_por_processo,
    }


# =========================================================================
# CLASSE: TestE2ERecebimentoSimples
# =========================================================================
@pytest.mark.e2e
@pytest.mark.recebimento
class TestE2ERecebimentoSimples:
    """Pipeline E2E com cenários simples de recebimento."""

    def test_cot_depois_nf_reconcilia(self, audit):
        """COT (adiantamento) + NF (regular) → reconciliação correta.

        Fluxo real: cliente paga COT, depois NF quando faturado.
        """
        audit.set_contexto(modulo="E2E Recebimento", cenario="COT + NF + Reconciliacao")

        df_comercial = _criar_df_comercial([
            {"Processo": "50001", "Numero NF": "700001", "Status Processo": "ORCAMENTO"},
            {"Processo": "50001", "Numero NF": "700001", "Status Processo": "FATURADO"},
        ])

        tcmp = {"Samanta Silva": 0.05, "Andrey Andrade": 0.03}
        fcmp = {"Samanta Silva": 1.2, "Andrey Andrade": 0.9}

        pagamentos = [
            {"documento": "COT50001", "valor": 80_000.0, "data_pagamento": datetime(2025, 3, 10)},
            {"documento": "700001", "valor": 60_000.0, "data_pagamento": datetime(2025, 5, 20)},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, tcmp, fcmp)

        # Adiantamentos calculados
        assert len(resultado["adiantamentos"]) == 2  # Samanta + Andrey

        # Regulares calculados
        assert len(resultado["regulares"]) == 2

        # Reconciliações calculadas
        assert len(resultado["reconciliacoes"]) == 2

        # Validações OK
        audit.verificar(
            descricao="Todas validacoes OK no pipeline E2E",
            formula="validar_todas -> True",
            entradas={},
            esperado="True",
            real=str(resultado["validacoes_ok"]),
        )

        # Verificar adiantamento de Samanta: 80000 * 0.05 * 1.0 = 4000
        ad_samanta = next(a for a in resultado["adiantamentos"] if a["nome_colaborador"] == "Samanta Silva")
        audit.verificar(
            descricao="Adiantamento Samanta",
            formula="80000 x 0.05 x 1.0 = 4000",
            entradas={"valor": 80_000, "tcmp": 0.05},
            esperado=4000.0,
            real=ad_samanta["comissao_calculada"],
        )

        # Verificar reconciliação Samanta: 4000 * (1.2 - 1.0) = 800
        rec_samanta = next(r for r in resultado["reconciliacoes"] if r["colaborador"] == "Samanta Silva")
        audit.verificar(
            descricao="Ajuste reconciliacao Samanta",
            formula="4000 x (1.2 - 1.0) = 800",
            entradas={"adiantado": 4000, "fcmp": 1.2},
            esperado=800.0,
            real=rec_samanta["ajuste_reconciliacao"],
        )

        # Verificar reconciliação Andrey: 2400 * (0.9 - 1.0) = -240
        ad_andrey = next(a for a in resultado["adiantamentos"] if a["nome_colaborador"] == "Andrey Andrade")
        rec_andrey = next(r for r in resultado["reconciliacoes"] if r["colaborador"] == "Andrey Andrade")
        audit.verificar(
            descricao="Ajuste reconciliacao Andrey (negativo)",
            formula=f"{ad_andrey['comissao_calculada']} x (0.9 - 1.0) = {ad_andrey['comissao_calculada'] * -0.1}",
            entradas={"adiantado": ad_andrey["comissao_calculada"], "fcmp": 0.9},
            esperado=ad_andrey["comissao_calculada"] * (0.9 - 1.0),
            real=rec_andrey["ajuste_reconciliacao"],
        )

    def test_nf_direto_sem_reconciliacao(self, audit):
        """NF sem COT prévio → regular calculado, sem reconciliação."""
        audit.set_contexto(modulo="E2E Recebimento", cenario="NF direto sem reconciliacao")

        df_comercial = _criar_df_comercial([
            {"Processo": "60001", "Numero NF": "800001", "Status Processo": "FATURADO"},
        ])

        tcmp = {"Samanta Silva": 0.04}
        fcmp = {"Samanta Silva": 1.15}

        pagamentos = [
            {"documento": "800001", "valor": 50_000.0, "data_pagamento": datetime(2025, 4, 10)},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, tcmp, fcmp)

        # Sem adiantamentos
        audit.verificar(
            descricao="Zero adiantamentos (NF direto)",
            formula="len(adiantamentos) == 0",
            entradas={},
            esperado=0,
            real=len(resultado["adiantamentos"]),
        )

        # 1 regular
        assert len(resultado["regulares"]) == 1
        reg = resultado["regulares"][0]
        esperado = 50_000.0 * 0.04 * 1.15

        audit.verificar(
            descricao="Regular NF direto",
            formula="50000 x 0.04 x 1.15 = 2300",
            entradas={"valor": 50_000, "tcmp": 0.04, "fcmp": 1.15},
            esperado=esperado,
            real=reg["comissao_calculada"],
        )

        # Sem reconciliação (nenhum adiantamento)
        audit.verificar(
            descricao="Zero reconciliacoes (sem COT previo)",
            formula="len(reconciliacoes) == 0",
            entradas={},
            esperado=0,
            real=len(resultado["reconciliacoes"]),
        )

    def test_documento_nao_mapeado_no_pipeline(self, audit):
        """Documento desconhecido → registrado em não mapeados, sem comissão."""
        audit.set_contexto(modulo="E2E Recebimento", cenario="Documento nao mapeado")

        df_comercial = _criar_df_comercial([
            {"Processo": "70001", "Numero NF": "900001", "Status Processo": "FATURADO"},
        ])

        pagamentos = [
            {"documento": "XPTO999", "valor": 30_000.0},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, {"Samanta Silva": 0.05}, {})

        audit.verificar(
            descricao="1 documento nao mapeado",
            formula="len(nao_mapeados) == 1",
            entradas={"doc": "XPTO999"},
            esperado=1,
            real=len(resultado["nao_mapeados"]),
        )
        audit.verificar(
            descricao="Zero comissoes geradas",
            formula="len(ad) + len(reg) == 0",
            entradas={},
            esperado=0,
            real=len(resultado["adiantamentos"]) + len(resultado["regulares"]),
        )


# =========================================================================
# CLASSE: TestE2EMultiProcesso
# =========================================================================
@pytest.mark.e2e
@pytest.mark.recebimento
@pytest.mark.reconciliacao
class TestE2EMultiProcesso:
    """Pipeline E2E com múltiplos processos no mesmo lote."""

    def test_dois_processos_com_reconciliacao(self, audit):
        """2 processos com COT+NF → reconciliações distintas, resumo correto."""
        audit.set_contexto(modulo="E2E Recebimento", cenario="Multi-processo")

        df_comercial = _criar_df_comercial([
            {"Processo": "80001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
            {"Processo": "80002", "Numero NF": "", "Status Processo": "ORCAMENTO"},
            {"Processo": "80001", "Numero NF": "800011", "Status Processo": "FATURADO"},
            {"Processo": "80002", "Numero NF": "800021", "Status Processo": "FATURADO"},
        ])

        tcmp = {"Samanta Silva": 0.05}
        fcmp = {"Samanta Silva": 1.3}

        pagamentos = [
            {"documento": "COT80001", "valor": 40_000.0, "data_pagamento": datetime(2025, 2, 1)},
            {"documento": "COT80002", "valor": 60_000.0, "data_pagamento": datetime(2025, 2, 15)},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, tcmp, fcmp)

        # 2 adiantamentos
        assert len(resultado["adiantamentos"]) == 2

        # 2 reconciliações (1 por processo)
        assert len(resultado["reconciliacoes"]) == 2

        # Verificar ajustes
        for rec in resultado["reconciliacoes"]:
            proc_id = rec.get("processo", rec.get("processo_id", ""))
            ad_valor = resultado["comissoes_adiantadas_por_processo"][proc_id]["Samanta Silva"]
            ajuste_esperado = ad_valor * (1.3 - 1.0)
            audit.verificar(
                descricao=f"Ajuste processo {rec['processo']}",
                formula=f"{ad_valor} x (1.3 - 1.0)",
                entradas={"processo": rec["processo"], "adiantado": ad_valor},
                esperado=round(ajuste_esperado, 2),
                real=round(rec["ajuste_reconciliacao"], 2),
            )

        # Resumo por processo
        resumo = resultado["resumo"]
        assert len(resumo) == 2
        audit.verificar(
            descricao="Resumo tem 2 processos",
            formula="len(resumo) == 2",
            entradas={},
            esperado=2,
            real=len(resumo),
        )

    def test_propriedade_adiantamento_mais_ajuste_igual_regular(self, audit):
        """Propriedade matemática: ad + ajuste = ad × FCMP (para cada colaborador).

        Esta é a propriedade fundamental que garante consistência financeira.
        """
        audit.set_contexto(modulo="E2E Recebimento", cenario="Propriedade ad+ajuste=regular")

        df_comercial = _criar_df_comercial([
            {"Processo": "82001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
        ])

        tcmp = {"Samanta Silva": 0.05, "Andrey Andrade": 0.03}
        fcmp = {"Samanta Silva": 1.25, "Andrey Andrade": 0.85}

        pagamentos = [
            {"documento": "COT82001", "valor": 100_000.0, "data_pagamento": datetime(2025, 3, 1)},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, tcmp, fcmp)

        for rec in resultado["reconciliacoes"]:
            colab = rec["colaborador"]
            # Buscar adiantamento do colaborador
            ad = next(a for a in resultado["adiantamentos"] if a["nome_colaborador"] == colab)
            ad_valor = ad["comissao_calculada"]
            ajuste = rec["ajuste_reconciliacao"]
            total = ad_valor + ajuste
            regular_esperado = ad_valor * fcmp[colab]

            audit.verificar(
                descricao=f"ad + ajuste == regular ({colab})",
                formula=f"{ad_valor} + {ajuste} == {ad_valor} x {fcmp[colab]}",
                entradas={"ad": ad_valor, "ajuste": ajuste, "fcmp": fcmp[colab]},
                esperado=round(regular_esperado, 2),
                real=round(total, 2),
            )


# =========================================================================
# CLASSE: TestE2ESaidaFinal
# =========================================================================
@pytest.mark.e2e
@pytest.mark.recebimento
class TestE2ESaidaFinal:
    """Testa que a saída final do pipeline E2E é completa e consistente."""

    def test_dataframe_reconciliacoes_completo(self, audit):
        """DataFrame de reconciliações tem todas as colunas esperadas."""
        audit.set_contexto(modulo="E2E Recebimento", cenario="DataFrame completo")

        df_comercial = _criar_df_comercial([
            {"Processo": "83001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
        ])

        pagamentos = [
            {"documento": "COT83001", "valor": 50_000.0, "data_pagamento": datetime(2025, 4, 1)},
        ]

        resultado = _pipeline_recebimento_e2e(
            pagamentos, df_comercial,
            {"Samanta Silva": 0.05}, {"Samanta Silva": 1.1},
        )

        df = resultado["df_reconciliacoes"]
        colunas_esperadas = [
            "processo", "colaborador", "tcmp", "fcmp",
            "comissao_adiantada_fc_1", "comissao_deveria_fc_real",
            "diferenca_fc", "ajuste_reconciliacao", "mes_faturamento",
        ]

        for col in colunas_esperadas:
            audit.verificar(
                descricao=f"Coluna '{col}' presente",
                formula=f"'{col}' in df.columns",
                entradas={},
                esperado="True",
                real=str(col in df.columns),
            )

    def test_saldo_global_consistente(self, audit):
        """Saldo total = soma algébrica de todos os ajustes."""
        audit.set_contexto(modulo="E2E Recebimento", cenario="Saldo global")

        df_comercial = _criar_df_comercial([
            {"Processo": "81001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
            {"Processo": "81002", "Numero NF": "", "Status Processo": "ORCAMENTO"},
        ])

        tcmp = {"Samanta Silva": 0.05}
        fcmp = {"Samanta Silva": 1.2}  # positivo para ambos

        pagamentos = [
            {"documento": "COT81001", "valor": 40_000.0},
            {"documento": "COT81002", "valor": 30_000.0},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, tcmp, fcmp)

        # Saldo = soma dos ajustes individuais
        soma_ajustes = sum(r["ajuste_reconciliacao"] for r in resultado["reconciliacoes"])

        audit.verificar(
            descricao="Saldo total == soma ajustes",
            formula="saldo_total == sum(ajustes)",
            entradas={"n_reconciliacoes": len(resultado["reconciliacoes"])},
            esperado=round(soma_ajustes, 2),
            real=round(resultado["saldo_total"], 2),
        )

        # Calcular saldo esperado manualmente
        # 81001: 40000*0.05=2000 → 2000*(1.2-1.0)=400
        # 81002: 30000*0.05=1500 → 1500*(1.2-1.0)=300
        # Total: 700
        audit.verificar(
            descricao="Saldo total manual",
            formula="400 + 300 = 700",
            entradas={"ajuste_sg001": 400, "ajuste_sg002": 300},
            esperado=700.0,
            real=resultado["saldo_total"],
        )

    def test_zero_erros_validacao_pipeline_completo(self, audit):
        """Pipeline completo com dados limpos → 0 erros de validação."""
        audit.set_contexto(modulo="E2E Recebimento", cenario="Zero erros validacao")

        df_comercial = _criar_df_comercial([
            {"Processo": "84001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
            {"Processo": "84002", "Numero NF": "840021", "Status Processo": "FATURADO"},
        ])

        tcmp = {"Samanta Silva": 0.05, "Andrey Andrade": 0.04}
        fcmp = {"Samanta Silva": 1.1, "Andrey Andrade": 0.95}

        pagamentos = [
            {"documento": "COT84001", "valor": 70_000.0, "data_pagamento": datetime(2025, 5, 1)},
            {"documento": "840021", "valor": 45_000.0, "data_pagamento": datetime(2025, 5, 15)},
        ]

        resultado = _pipeline_recebimento_e2e(pagamentos, df_comercial, tcmp, fcmp)

        audit.verificar(
            descricao="Zero erros de validacao",
            formula="validacoes_ok == True AND len(erros) == 0",
            entradas={"n_erros": len(resultado["validacao_erros"])},
            esperado="True",
            real=str(resultado["validacoes_ok"]),
        )
        audit.verificar(
            descricao="Lista erros vazia",
            formula="len(erros) == 0",
            entradas={},
            esperado=0,
            real=len(resultado["validacao_erros"]),
        )
