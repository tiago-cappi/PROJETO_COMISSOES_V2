"""
Testes unitários para ComissaoCalculator (módulo recebimento).

Testa as duas fórmulas centrais de comissão por recebimento:

    Adiantamento (COT):
        comissao = valor × tcmp × 1.0   (FC sempre 1.0)

    Pagamento Regular (pós-faturamento):
        comissao = valor × tcmp × fcmp
        Se fcmp <= 0 → fallback para 1.0

Cenários cobertos:
    ── calcular_adiantamento ──
    - Fórmula básica com um colaborador
    - Múltiplos colaboradores (TCMP distinto por cargo)
    - Colaborador com TCMP <= 0 é ignorado
    - Valor zero → comissão zero
    - FC sempre 1.0 (garantia contratual)
    - tipo_lancamento = 'Adiantamento'
    - Campos de saída completos (processo, documento, etc.)

    ── calcular_regular ──
    - Fórmula básica com FCMP > 0
    - FCMP <= 0 → fallback para 1.0
    - FCMP não encontrado para colaborador → default 0.0 → fallback 1.0
    - Múltiplos colaboradores com FCMP distintos
    - tipo_lancamento = 'Pagamento Regular'
    - Campo mes_faturamento presente
    - TCMP <= 0 é ignorado
    - Valor zero → comissão zero
"""

import pytest
from datetime import datetime

from src.recebimento.core.comissao_calculator import ComissaoCalculator


# =========================================================================
# HELPERS
# =========================================================================

def _calcular_adiantamento_formula(valor: float, tcmp: float) -> float:
    """Fórmula pura: comissao = valor × tcmp × 1.0."""
    return valor * tcmp * 1.0


def _calcular_regular_formula(valor: float, tcmp: float, fcmp: float) -> float:
    """Fórmula pura: comissao = valor × tcmp × fcmp (com fallback)."""
    fcmp_efetivo = fcmp if fcmp > 0 else 1.0
    return valor * tcmp * fcmp_efetivo


# =========================================================================
# CLASSE: TestCalcularAdiantamento
# =========================================================================
@pytest.mark.unit
@pytest.mark.recebimento
class TestCalcularAdiantamento:
    """Testa ComissaoCalculator.calcular_adiantamento()."""

    def test_formula_basica_um_colaborador(self, audit):
        """Adiantamento simples: comissao = 50000 × 0.05 × 1.0 = 2500."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Adiantamento basico")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="12345",
            valor=50_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            documento="COT12345",
            data_pagamento=datetime(2025, 3, 15),
        )

        assert len(resultado) == 1
        r = resultado[0]
        esperado = _calcular_adiantamento_formula(50_000.0, 0.05)

        audit.verificar(
            descricao="Comissao adiantamento basico",
            formula="50000 x 0.05 x 1.0 = 2500.0",
            entradas={"valor": 50_000, "tcmp": 0.05, "fc": 1.0},
            esperado=esperado,
            real=r["comissao_calculada"],
        )

    def test_multiplos_colaboradores(self, audit):
        """Adiantamento com 3 colaboradores: cada um recebe proporcional ao TCMP."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Adiantamento multi-colab")

        calc = ComissaoCalculator()
        tcmp_dict = {
            "Samanta Silva": 0.05,
            "Andre Moraes": 0.03,
            "Ney Silva": 0.02,
        }
        resultado = calc.calcular_adiantamento(
            processo="99001",
            valor=100_000.0,
            tcmp_dict=tcmp_dict,
            documento="COT99001",
        )

        assert len(resultado) == 3

        for r in resultado:
            nome = r["nome_colaborador"]
            esperado = _calcular_adiantamento_formula(100_000.0, tcmp_dict[nome])
            audit.verificar(
                descricao=f"Adiantamento {nome}",
                formula=f"100000 x {tcmp_dict[nome]} x 1.0",
                entradas={"valor": 100_000, "tcmp": tcmp_dict[nome]},
                esperado=esperado,
                real=r["comissao_calculada"],
            )

    def test_tcmp_zero_e_ignorado(self, audit):
        """Colaborador com TCMP = 0 não gera comissão."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="TCMP zero ignorado")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="11111",
            valor=80_000.0,
            tcmp_dict={"Samanta Silva": 0.05, "Colab Zero": 0.0},
            documento="COT11111",
        )

        assert len(resultado) == 1
        audit.verificar(
            descricao="Apenas 1 comissao (TCMP>0)",
            formula="TCMP <= 0 eh ignorado",
            entradas={"tcmp_samanta": 0.05, "tcmp_zero": 0.0},
            esperado=1,
            real=len(resultado),
        )

    def test_tcmp_negativo_e_ignorado(self, audit):
        """Colaborador com TCMP negativo não gera comissão."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="TCMP negativo ignorado")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="22222",
            valor=50_000.0,
            tcmp_dict={"Colab Neg": -0.03},
            documento="COT22222",
        )

        assert len(resultado) == 0
        audit.verificar(
            descricao="Nenhuma comissao para TCMP negativo",
            formula="TCMP <= 0 -> skip",
            entradas={"tcmp": -0.03},
            esperado=0,
            real=len(resultado),
        )

    def test_valor_zero_gera_comissao_zero(self, audit):
        """Valor do adiantamento = 0 → comissão = 0."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Valor zero")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="33333",
            valor=0.0,
            tcmp_dict={"Samanta Silva": 0.05},
            documento="COT33333",
        )

        assert len(resultado) == 1
        audit.verificar(
            descricao="Comissao com valor zero",
            formula="0 x 0.05 x 1.0 = 0.0",
            entradas={"valor": 0.0, "tcmp": 0.05},
            esperado=0.0,
            real=resultado[0]["comissao_calculada"],
        )

    def test_fc_sempre_um(self, audit):
        """Verifica que FC = 1.0 para todos os adiantamentos."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="FC fixo 1.0")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="44444",
            valor=75_000.0,
            tcmp_dict={"Andre Moraes": 0.04, "Ney Silva": 0.06},
            documento="COT44444",
        )

        for r in resultado:
            audit.verificar(
                descricao=f"FC fixo 1.0 para {r['nome_colaborador']}",
                formula="FC = 1.0 (regra de adiantamento)",
                entradas={"colaborador": r["nome_colaborador"]},
                esperado=1.0,
                real=r["fc"],
            )

    def test_tipo_lancamento_adiantamento(self, audit):
        """tipo_lancamento deve ser 'Adiantamento'."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Tipo lancamento")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="55555",
            valor=10_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            documento="COT55555",
        )

        audit.verificar(
            descricao="tipo_lancamento = Adiantamento",
            formula="Constante",
            entradas={},
            esperado="Adiantamento",
            real=resultado[0]["tipo_lancamento"],
        )

    def test_campos_saida_completos(self, audit):
        """Verifica que todos os campos obrigatórios estão presentes."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Campos saida")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="66666",
            valor=20_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            documento="COT66666",
            data_pagamento=datetime(2025, 6, 1),
        )

        r = resultado[0]
        campos_esperados = [
            "processo", "documento", "data_pagamento", "valor_pago",
            "nome_colaborador", "cargo", "tcmp", "fc", "fcmp",
            "comissao_calculada", "tipo_lancamento", "mes_calculo",
        ]

        campos_presentes = [c for c in campos_esperados if c in r]
        audit.verificar(
            descricao="Todos campos obrigatorios presentes",
            formula="len(campos_presentes) == len(campos_esperados)",
            entradas={"campos_esperados": len(campos_esperados)},
            esperado=len(campos_esperados),
            real=len(campos_presentes),
        )

    def test_processo_e_documento_trimados(self, audit):
        """Processo e documento devem ter strip() aplicado."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Trim campos")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="  12345  ",
            valor=10_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            documento="  COT12345  ",
        )

        r = resultado[0]
        audit.verificar(
            descricao="Processo trimado",
            formula="str.strip()",
            entradas={"processo_raw": "  12345  "},
            esperado="12345",
            real=r["processo"],
        )
        audit.verificar(
            descricao="Documento trimado",
            formula="str.strip()",
            entradas={"documento_raw": "  COT12345  "},
            esperado="COT12345",
            real=r["documento"],
        )

    def test_valor_grande_precisao(self, audit):
        """Testa precisão com valor alto (R$ 1.5M)."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Valor alto")

        calc = ComissaoCalculator()
        resultado = calc.calcular_adiantamento(
            processo="77777",
            valor=1_500_000.0,
            tcmp_dict={"Andre Moraes": 0.035},
            documento="COT77777",
        )

        esperado = _calcular_adiantamento_formula(1_500_000.0, 0.035)
        audit.verificar(
            descricao="Comissao valor alto",
            formula="1500000 x 0.035 x 1.0 = 52500.0",
            entradas={"valor": 1_500_000, "tcmp": 0.035},
            esperado=esperado,
            real=resultado[0]["comissao_calculada"],
        )


# =========================================================================
# CLASSE: TestCalcularRegular
# =========================================================================
@pytest.mark.unit
@pytest.mark.recebimento
class TestCalcularRegular:
    """Testa ComissaoCalculator.calcular_regular()."""

    def test_formula_basica(self, audit):
        """Regular: comissao = 80000 × 0.04 × 1.2 = 3840."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Regular basico")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10001",
            valor=80_000.0,
            tcmp_dict={"Samanta Silva": 0.04},
            fcmp_dict={"Samanta Silva": 1.2},
            documento="NF123456",
            data_pagamento=datetime(2025, 5, 20),
            mes_faturamento="04/2025",
        )

        assert len(resultado) == 1
        r = resultado[0]
        esperado = _calcular_regular_formula(80_000.0, 0.04, 1.2)

        audit.verificar(
            descricao="Comissao regular basica",
            formula="80000 x 0.04 x 1.2 = 3840.0",
            entradas={"valor": 80_000, "tcmp": 0.04, "fcmp": 1.2},
            esperado=esperado,
            real=r["comissao_calculada"],
        )

    def test_fcmp_zero_fallback_um(self, audit):
        """FCMP = 0 → fallback para 1.0."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="FCMP zero fallback")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10002",
            valor=50_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 0.0},
            documento="NF200001",
        )

        r = resultado[0]
        esperado = _calcular_regular_formula(50_000.0, 0.05, 0.0)  # fallback 1.0

        audit.verificar(
            descricao="Comissao com FCMP zero (fallback 1.0)",
            formula="50000 x 0.05 x 1.0 = 2500.0",
            entradas={"valor": 50_000, "tcmp": 0.05, "fcmp_original": 0.0, "fcmp_efetivo": 1.0},
            esperado=esperado,
            real=r["comissao_calculada"],
        )

    def test_fcmp_negativo_fallback_um(self, audit):
        """FCMP negativo → fallback para 1.0."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="FCMP negativo fallback")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10003",
            valor=40_000.0,
            tcmp_dict={"Andre Moraes": 0.06},
            fcmp_dict={"Andre Moraes": -0.5},
            documento="NF300001",
        )

        r = resultado[0]
        esperado = _calcular_regular_formula(40_000.0, 0.06, -0.5)  # fallback 1.0

        audit.verificar(
            descricao="Comissao com FCMP negativo (fallback 1.0)",
            formula="40000 x 0.06 x 1.0 = 2400.0",
            entradas={"valor": 40_000, "tcmp": 0.06, "fcmp_original": -0.5, "fcmp_efetivo": 1.0},
            esperado=esperado,
            real=r["comissao_calculada"],
        )

    def test_fcmp_nao_encontrado_fallback(self, audit):
        """Colaborador sem FCMP no dict → default 0.0 → fallback 1.0."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="FCMP ausente fallback")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10004",
            valor=60_000.0,
            tcmp_dict={"Samanta Silva": 0.04},
            fcmp_dict={},  # vazio — colaborador não encontrado
            documento="NF400001",
        )

        r = resultado[0]
        # dict.get("Samanta Silva", 0.0) → 0.0 → fallback 1.0
        esperado = _calcular_regular_formula(60_000.0, 0.04, 0.0)

        audit.verificar(
            descricao="FCMP ausente -> default 0.0 -> fallback 1.0",
            formula="60000 x 0.04 x 1.0 = 2400.0",
            entradas={"valor": 60_000, "tcmp": 0.04, "fcmp_ausente": True},
            esperado=esperado,
            real=r["comissao_calculada"],
        )

    def test_multiplos_colaboradores_fcmp_distintos(self, audit):
        """3 colaboradores com FCMP diferentes."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Multi-colab FCMP distintos")

        calc = ComissaoCalculator()
        tcmp_dict = {"Samanta Silva": 0.05, "Andre Moraes": 0.03, "Ney Silva": 0.02}
        fcmp_dict = {"Samanta Silva": 1.1, "Andre Moraes": 0.9, "Ney Silva": 1.5}
        resultado = calc.calcular_regular(
            processo="10005",
            valor=100_000.0,
            tcmp_dict=tcmp_dict,
            fcmp_dict=fcmp_dict,
            documento="NF500001",
            mes_faturamento="03/2025",
        )

        assert len(resultado) == 3

        for r in resultado:
            nome = r["nome_colaborador"]
            esperado = _calcular_regular_formula(100_000.0, tcmp_dict[nome], fcmp_dict[nome])
            audit.verificar(
                descricao=f"Regular {nome}",
                formula=f"100000 x {tcmp_dict[nome]} x {fcmp_dict[nome]}",
                entradas={"valor": 100_000, "tcmp": tcmp_dict[nome], "fcmp": fcmp_dict[nome]},
                esperado=esperado,
                real=r["comissao_calculada"],
            )

    def test_tipo_lancamento_regular(self, audit):
        """tipo_lancamento deve ser 'Pagamento Regular'."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Tipo lancamento regular")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10006",
            valor=30_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.0},
            documento="NF600001",
        )

        audit.verificar(
            descricao="tipo_lancamento = Pagamento Regular",
            formula="Constante",
            entradas={},
            esperado="Pagamento Regular",
            real=resultado[0]["tipo_lancamento"],
        )

    def test_campo_mes_faturamento_presente(self, audit):
        """Campo mes_faturamento deve existir no resultado."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Campo mes_faturamento")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10007",
            valor=25_000.0,
            tcmp_dict={"Samanta Silva": 0.04},
            fcmp_dict={"Samanta Silva": 1.0},
            documento="NF700001",
            mes_faturamento="06/2025",
        )

        audit.verificar(
            descricao="mes_faturamento registrado corretamente",
            formula="Passthrough do parametro",
            entradas={"mes_faturamento_input": "06/2025"},
            esperado="06/2025",
            real=resultado[0]["mes_faturamento"],
        )

    def test_tcmp_zero_ignorado_regular(self, audit):
        """TCMP <= 0 é ignorado em pagamento regular."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="TCMP zero regular")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10008",
            valor=50_000.0,
            tcmp_dict={"Colab Zero": 0.0, "Samanta Silva": 0.05},
            fcmp_dict={"Colab Zero": 1.0, "Samanta Silva": 1.0},
            documento="NF800001",
        )

        assert len(resultado) == 1
        audit.verificar(
            descricao="Apenas 1 comissao (TCMP>0) em regular",
            formula="TCMP <= 0 eh ignorado",
            entradas={"tcmp_zero": 0.0, "tcmp_samanta": 0.05},
            esperado=1,
            real=len(resultado),
        )

    def test_valor_zero_regular(self, audit):
        """Valor zero → comissão zero em pagamento regular."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Valor zero regular")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10009",
            valor=0.0,
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.2},
            documento="NF900001",
        )

        assert len(resultado) == 1
        audit.verificar(
            descricao="Comissao regular com valor zero",
            formula="0.0 x 0.05 x 1.2 = 0.0",
            entradas={"valor": 0.0, "tcmp": 0.05, "fcmp": 1.2},
            esperado=0.0,
            real=resultado[0]["comissao_calculada"],
        )

    def test_fcmp_campo_no_resultado(self, audit):
        """FCMP deve aparecer no resultado (não None como em adiantamento)."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="FCMP no resultado")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="10010",
            valor=50_000.0,
            tcmp_dict={"Samanta Silva": 0.04},
            fcmp_dict={"Samanta Silva": 1.3},
            documento="NF100001",
        )

        audit.verificar(
            descricao="FCMP registrado no resultado regular",
            formula="FCMP do dict (ou fallback)",
            entradas={"fcmp_input": 1.3},
            esperado=1.3,
            real=resultado[0]["fcmp"],
        )

    def test_fcmp_adiantamento_none_vs_regular(self, audit):
        """Adiantamento tem fcmp=None; Regular tem fcmp preenchido."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="FCMP None vs preenchido")

        calc = ComissaoCalculator()

        adiant = calc.calcular_adiantamento(
            processo="20001",
            valor=10_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            documento="COT20001",
        )

        regular = calc.calcular_regular(
            processo="20001",
            valor=10_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
            fcmp_dict={"Samanta Silva": 1.1},
            documento="NF200010",
        )

        audit.verificar(
            descricao="FCMP adiantamento = None",
            formula="Regra: adiantamento nao usa FCMP",
            entradas={},
            esperado="None",
            real=str(adiant[0]["fcmp"]),
        )

        audit.verificar(
            descricao="FCMP regular = 1.1",
            formula="Passthrough do dict",
            entradas={"fcmp_input": 1.1},
            esperado=1.1,
            real=regular[0]["fcmp"],
        )

    def test_valor_alto_regular_precisao(self, audit):
        """Testa precisão com valor alto (R$ 2M) e FCMP fracionário."""
        audit.set_contexto(modulo="Recebimento Comissao", cenario="Valor alto regular")

        calc = ComissaoCalculator()
        resultado = calc.calcular_regular(
            processo="30001",
            valor=2_000_000.0,
            tcmp_dict={"Andre Moraes": 0.025},
            fcmp_dict={"Andre Moraes": 1.15},
            documento="NF300010",
            mes_faturamento="05/2025",
        )

        esperado = _calcular_regular_formula(2_000_000.0, 0.025, 1.15)
        audit.verificar(
            descricao="Comissao regular valor alto",
            formula="2000000 x 0.025 x 1.15 = 57500.0",
            entradas={"valor": 2_000_000, "tcmp": 0.025, "fcmp": 1.15},
            esperado=esperado,
            real=resultado[0]["comissao_calculada"],
        )
