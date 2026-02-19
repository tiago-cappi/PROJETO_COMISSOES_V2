"""
Testes de integração: ProcessMapper + ComissaoCalculator.

Valida o fluxo completo do módulo de recebimento:

    1. ProcessMapper.mapear_documento(doc) → tipo + processo
    2. Se ADIANTAMENTO → ComissaoCalculator.calcular_adiantamento()
    3. Se PAGAMENTO_REGULAR → ComissaoCalculator.calcular_regular()

Fluxo integrado:
    Análise Financeira → ProcessMapper → decisão tipo → ComissaoCalculator → resultado

Cenários:
    - COT mapeado → adiantamento calculado corretamente
    - NF mapeada → pagamento regular calculado corretamente
    - Documento não mapeado → nenhuma comissão gerada
    - COT + NF no mesmo lote → adiantamento + regular separados
    - Múltiplos documentos para o mesmo processo
    - COT para processo FATURADO → exceção impede cálculo
    - Pipeline com FCMP fallback (FCMP ausente no regular)
    - Validação de campos de saída consistentes entre tipos
"""

import pytest
import pandas as pd
from datetime import datetime

from src.recebimento.core.process_mapper import ProcessMapper
from src.recebimento.core.comissao_calculator import ComissaoCalculator
from src.recebimento.exceptions import InconsistenciaAdiantamentoError


# =========================================================================
# HELPERS
# =========================================================================

def _criar_df_comercial(itens: list) -> pd.DataFrame:
    """Cria DataFrame simulando Análise Comercial Completa."""
    return pd.DataFrame(itens)


def _processar_documento(
    mapper: ProcessMapper,
    calculator: ComissaoCalculator,
    documento: str,
    valor: float,
    tcmp_dict: dict,
    fcmp_dict: dict = None,
    data_pagamento: datetime = None,
    mes_faturamento: str = None,
) -> dict:
    """Pipeline completo: mapeia documento e calcula comissão.

    Returns:
        Dict com 'mapeamento', 'comissoes', 'tipo'.
    """
    mapeamento = mapper.mapear_documento(documento)

    if not mapeamento.get("mapeado"):
        return {"mapeamento": mapeamento, "comissoes": [], "tipo": None}

    tipo = mapeamento["tipo"]
    processo = mapeamento["processo"]

    if tipo == "ADIANTAMENTO":
        comissoes = calculator.calcular_adiantamento(
            processo=processo,
            valor=valor,
            tcmp_dict=tcmp_dict,
            documento=documento,
            data_pagamento=data_pagamento,
        )
    elif tipo == "PAGAMENTO_REGULAR":
        comissoes = calculator.calcular_regular(
            processo=processo,
            valor=valor,
            tcmp_dict=tcmp_dict,
            fcmp_dict=fcmp_dict or {},
            documento=documento,
            data_pagamento=data_pagamento,
            mes_faturamento=mes_faturamento,
        )
    else:
        comissoes = []

    return {"mapeamento": mapeamento, "comissoes": comissoes, "tipo": tipo}


# =========================================================================
# CLASSE: TestMapperCalculatorIntegrado
# =========================================================================
@pytest.mark.integration
@pytest.mark.recebimento
class TestMapperCalculatorIntegrado:
    """Testa ProcessMapper + ComissaoCalculator juntos."""

    def test_cot_adiantamento_pipeline(self, audit):
        """COT12345 → mapeia ADIANTAMENTO → calcula comissão FC=1.0."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="COT pipeline")

        df = _criar_df_comercial([{
            "Processo": "12345", "Numero NF": "", "Status Processo": "ORCAMENTO",
        }])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()

        resultado = _processar_documento(
            mapper=mapper,
            calculator=calculator,
            documento="COT12345",
            valor=80_000.0,
            tcmp_dict={"Samanta Silva": 0.05, "Andrey Andrade": 0.03},
            data_pagamento=datetime(2025, 4, 15),
        )

        assert resultado["tipo"] == "ADIANTAMENTO"
        assert len(resultado["comissoes"]) == 2

        for c in resultado["comissoes"]:
            esperado = 80_000.0 * c["tcmp"] * 1.0
            audit.verificar(
                descricao=f"Adiantamento {c['nome_colaborador']}",
                formula=f"80000 x {c['tcmp']} x 1.0",
                entradas={"doc": "COT12345", "tipo": "ADIANTAMENTO", "valor": 80_000},
                esperado=round(esperado, 2),
                real=round(c["comissao_calculada"], 2),
            )
            audit.verificar(
                descricao=f"tipo_lancamento {c['nome_colaborador']}",
                formula="COT -> Adiantamento",
                entradas={},
                esperado="Adiantamento",
                real=c["tipo_lancamento"],
            )

    def test_nf_regular_pipeline(self, audit):
        """NF123456 → mapeia PAGAMENTO_REGULAR → calcula comissão com FCMP."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="NF pipeline")

        df = _criar_df_comercial([{
            "Processo": "20001", "Numero NF": "123456", "Status Processo": "FATURADO",
        }])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()

        resultado = _processar_documento(
            mapper=mapper,
            calculator=calculator,
            documento="123456",
            valor=60_000.0,
            tcmp_dict={"Samanta Silva": 0.04},
            fcmp_dict={"Samanta Silva": 1.15},
            data_pagamento=datetime(2025, 5, 20),
            mes_faturamento="04/2025",
        )

        assert resultado["tipo"] == "PAGAMENTO_REGULAR"
        assert len(resultado["comissoes"]) == 1

        c = resultado["comissoes"][0]
        esperado = 60_000.0 * 0.04 * 1.15

        audit.verificar(
            descricao="Regular com FCMP=1.15",
            formula="60000 x 0.04 x 1.15",
            entradas={"doc": "123456", "tipo": "PAGAMENTO_REGULAR"},
            esperado=round(esperado, 2),
            real=round(c["comissao_calculada"], 2),
        )
        audit.verificar(
            descricao="tipo_lancamento regular",
            formula="NF -> Pagamento Regular",
            entradas={},
            esperado="Pagamento Regular",
            real=c["tipo_lancamento"],
        )
        audit.verificar(
            descricao="mes_faturamento preservado",
            formula="Passthrough",
            entradas={},
            esperado="04/2025",
            real=c["mes_faturamento"],
        )

    def test_documento_nao_mapeado_sem_comissao(self, audit):
        """Documento sem match → lista vazia de comissões."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="Nao mapeado")

        df = _criar_df_comercial([{
            "Processo": "30001", "Numero NF": "999999", "Status Processo": "ORCAMENTO",
        }])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()

        resultado = _processar_documento(
            mapper=mapper,
            calculator=calculator,
            documento="111111",
            valor=50_000.0,
            tcmp_dict={"Samanta Silva": 0.05},
        )

        audit.verificar(
            descricao="Documento nao mapeado -> sem comissoes",
            formula="mapeado=False -> lista vazia",
            entradas={"documento": "111111"},
            esperado=0,
            real=len(resultado["comissoes"]),
        )

    def test_lote_cot_e_nf_juntos(self, audit):
        """Lote com COT + NF processados no mesmo mapper."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="Lote COT+NF")

        df = _criar_df_comercial([
            {"Processo": "40001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
            {"Processo": "50002", "Numero NF": "654321", "Status Processo": "FATURADO"},
        ])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()
        tcmp = {"Samanta Silva": 0.05}
        fcmp = {"Samanta Silva": 1.1}

        r_cot = _processar_documento(mapper, calculator, "COT40001", 30_000.0, tcmp)
        r_nf = _processar_documento(mapper, calculator, "654321", 50_000.0, tcmp, fcmp, mes_faturamento="06/2025")

        audit.verificar(
            descricao="COT no lote -> ADIANTAMENTO",
            formula="tipo == ADIANTAMENTO",
            entradas={"doc": "COT40001"},
            esperado="ADIANTAMENTO",
            real=r_cot["tipo"],
        )
        audit.verificar(
            descricao="NF no lote -> PAGAMENTO_REGULAR",
            formula="tipo == PAGAMENTO_REGULAR",
            entradas={"doc": "654321"},
            esperado="PAGAMENTO_REGULAR",
            real=r_nf["tipo"],
        )

        # Verificar comissões
        com_cot = r_cot["comissoes"][0]["comissao_calculada"]
        com_nf = r_nf["comissoes"][0]["comissao_calculada"]

        audit.verificar(
            descricao="Comissao COT (FC=1.0)",
            formula="30000 x 0.05 x 1.0 = 1500.0",
            entradas={},
            esperado=1500.0,
            real=com_cot,
        )
        audit.verificar(
            descricao="Comissao NF (FCMP=1.1)",
            formula="50000 x 0.05 x 1.1 = 2750.0",
            entradas={},
            esperado=2750.0,
            real=com_nf,
        )

    def test_cot_faturado_bloqueia_pipeline(self, audit):
        """COT para processo FATURADO → exception antes do cálculo."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="COT FATURADO bloqueio")

        df = _criar_df_comercial([{
            "Processo": "60001", "Numero NF": "", "Status Processo": "FATURADO",
        }])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()

        erro_lancado = False
        try:
            _processar_documento(
                mapper=mapper,
                calculator=calculator,
                documento="COT60001",
                valor=40_000.0,
                tcmp_dict={"Samanta Silva": 0.05},
            )
        except InconsistenciaAdiantamentoError:
            erro_lancado = True

        audit.verificar(
            descricao="COT FATURADO bloqueia pipeline",
            formula="InconsistenciaAdiantamentoError raised",
            entradas={"doc": "COT60001", "status": "FATURADO"},
            esperado="True",
            real=str(erro_lancado),
        )

    def test_fcmp_fallback_no_regular(self, audit):
        """FCMP ausente para colaborador → fallback 1.0 no regular."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="FCMP fallback regular")

        df = _criar_df_comercial([{
            "Processo": "70001", "Numero NF": "777777", "Status Processo": "FATURADO",
        }])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()

        resultado = _processar_documento(
            mapper=mapper,
            calculator=calculator,
            documento="777777",
            valor=45_000.0,
            tcmp_dict={"Samanta Silva": 0.04},
            fcmp_dict={},  # vazio → fallback
            mes_faturamento="07/2025",
        )

        c = resultado["comissoes"][0]
        # FCMP ausente → 0.0 → fallback 1.0
        esperado = 45_000.0 * 0.04 * 1.0

        audit.verificar(
            descricao="FCMP ausente -> fallback 1.0 no pipeline",
            formula="45000 x 0.04 x 1.0 = 1800.0",
            entradas={"fcmp_ausente": True, "fcmp_efetivo": 1.0},
            esperado=esperado,
            real=c["comissao_calculada"],
        )

    def test_campos_consistentes_adiantamento_vs_regular(self, audit):
        """Ambos os tipos têm campos essenciais em comum."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="Campos consistentes")

        df = _criar_df_comercial([
            {"Processo": "80001", "Numero NF": "", "Status Processo": "ORCAMENTO"},
            {"Processo": "80002", "Numero NF": "888888", "Status Processo": "FATURADO"},
        ])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()

        # Adiantamento (COT para processo ORCAMENTO)
        r_ad = _processar_documento(mapper, calculator, "COT80001", 10_000.0,
                                    {"Samanta Silva": 0.05})

        # Regular (NF para processo FATURADO)
        r_reg = _processar_documento(mapper, calculator, "888888", 10_000.0,
                                     {"Samanta Silva": 0.05},
                                     {"Samanta Silva": 1.0},
                                     mes_faturamento="08/2025")

        campos_comuns = ["processo", "documento", "valor_pago", "nome_colaborador",
                         "tcmp", "comissao_calculada", "tipo_lancamento"]

        for campo in campos_comuns:
            ad_tem = campo in r_ad["comissoes"][0]
            reg_tem = campo in r_reg["comissoes"][0]
            audit.verificar(
                descricao=f"Campo '{campo}' presente em ambos tipos",
                formula=f"'{campo}' in resultado",
                entradas={"campo": campo},
                esperado="True",
                real=str(ad_tem and reg_tem),
            )

    def test_multiplos_documentos_mesmo_processo(self, audit):
        """Múltiplos pagamentos para o mesmo processo acumulam comissões."""
        audit.set_contexto(modulo="Integracao Mapper+Calc", cenario="Multi-docs mesmo processo")

        df = _criar_df_comercial([
            {"Processo": "90001", "Numero NF": "901001", "Status Processo": "FATURADO"},
        ])
        mapper = ProcessMapper(df)
        calculator = ComissaoCalculator()
        tcmp = {"Samanta Silva": 0.04}
        fcmp = {"Samanta Silva": 1.2}

        # 2 pagamentos para o mesmo processo
        r1 = _processar_documento(mapper, calculator, "901001", 30_000.0,
                                  tcmp, fcmp, mes_faturamento="09/2025")
        r2 = _processar_documento(mapper, calculator, "901001", 20_000.0,
                                  tcmp, fcmp, mes_faturamento="09/2025")

        total = r1["comissoes"][0]["comissao_calculada"] + r2["comissoes"][0]["comissao_calculada"]
        esperado = (30_000 + 20_000) * 0.04 * 1.2

        audit.verificar(
            descricao="Total comissoes acumuladas mesmo processo",
            formula="(30000 + 20000) x 0.04 x 1.2 = 2400.0",
            entradas={"pagamento_1": 30_000, "pagamento_2": 20_000},
            esperado=esperado,
            real=total,
        )
