"""
Testes unitários para DevolucaoCalculator.

Testa:
    1. calcular_fator_devolucao(valor_devolvido, valor_realizado)
       - Fator normal (proporcional)
       - Cap em 1.0 quando devolvido > realizado
       - valor_realizado = 0 → fator = 0
       - valor_realizado negativo → fator = 0
       - Devolução parcial vs total

    2. calcular_estorno_processo(...)
       - Estorno de um único colaborador
       - Estorno de múltiplos colaboradores (agrupamento)
       - Comissões históricas vazias → lista vazia
       - Sinal negativo no comissao_calculada
       - Observação indica parcial/total
       - Fator zero → lista vazia
"""

import pytest
import pandas as pd
from datetime import datetime

from src.devolucao.devolucao_calculator import DevolucaoCalculator


# =========================================================================
# HELPERS
# =========================================================================

def _criar_historicas(registros: list) -> pd.DataFrame:
    """Cria DataFrame de comissões históricas para estorno."""
    return pd.DataFrame(registros)


# =========================================================================
# CLASSE: TestCalcularFatorDevolucao
# =========================================================================
@pytest.mark.unit
@pytest.mark.devolucao
class TestCalcularFatorDevolucao:
    """Testa calcular_fator_devolucao()."""

    def test_devolucao_parcial_50_pct(self, audit):
        """Devolveu metade: fator = 0.5."""
        audit.set_contexto(modulo="Devolucao", cenario="Parcial 50%")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(50_000, 100_000)

        audit.verificar(
            descricao="Fator devolucao parcial 50%",
            formula="50000 / 100000 = 0.5",
            entradas={"valor_devolvido": 50_000, "valor_realizado": 100_000},
            esperado=0.5,
            real=fator,
        )

    def test_devolucao_parcial_30_pct(self, audit):
        """Devolveu 30%: fator = 0.3."""
        audit.set_contexto(modulo="Devolucao", cenario="Parcial 30%")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(30_000, 100_000)

        audit.verificar(
            descricao="Fator devolucao parcial 30%",
            formula="30000 / 100000 = 0.3",
            entradas={"valor_devolvido": 30_000, "valor_realizado": 100_000},
            esperado=0.3,
            real=fator,
        )

    def test_devolucao_total_100_pct(self, audit):
        """Devolveu tudo: fator = 1.0."""
        audit.set_contexto(modulo="Devolucao", cenario="Total 100%")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(100_000, 100_000)

        audit.verificar(
            descricao="Fator devolucao total 100%",
            formula="100000 / 100000 = 1.0",
            entradas={"valor_devolvido": 100_000, "valor_realizado": 100_000},
            esperado=1.0,
            real=fator,
        )

    def test_devolucao_excede_cap_em_1(self, audit):
        """Devolvido > realizado (erro dados): cap em 1.0."""
        audit.set_contexto(modulo="Devolucao", cenario="Cap em 1.0")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(150_000, 100_000)

        audit.verificar(
            descricao="Fator capped em 1.0 (devolvido > realizado)",
            formula="min(150000/100000, 1.0) = 1.0",
            entradas={"valor_devolvido": 150_000, "valor_realizado": 100_000},
            esperado=1.0,
            real=fator,
        )

    def test_valor_realizado_zero(self, audit):
        """Valor realizado = 0 → fator = 0 (evita divisão por zero)."""
        audit.set_contexto(modulo="Devolucao", cenario="Realizado zero")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(50_000, 0)

        audit.verificar(
            descricao="Fator com valor realizado zero",
            formula="realizado <= 0 → fator = 0.0",
            entradas={"valor_devolvido": 50_000, "valor_realizado": 0},
            esperado=0.0,
            real=fator,
        )

    def test_valor_realizado_negativo(self, audit):
        """Valor realizado negativo → fator = 0."""
        audit.set_contexto(modulo="Devolucao", cenario="Realizado negativo")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(50_000, -10_000)

        audit.verificar(
            descricao="Fator com valor realizado negativo",
            formula="realizado <= 0 → fator = 0.0",
            entradas={"valor_devolvido": 50_000, "valor_realizado": -10_000},
            esperado=0.0,
            real=fator,
        )

    def test_devolucao_zero(self, audit):
        """Valor devolvido = 0 → fator = 0."""
        audit.set_contexto(modulo="Devolucao", cenario="Devolvido zero")

        calc = DevolucaoCalculator()
        fator = calc.calcular_fator_devolucao(0, 100_000)

        audit.verificar(
            descricao="Fator com valor devolvido zero",
            formula="0 / 100000 = 0.0",
            entradas={"valor_devolvido": 0, "valor_realizado": 100_000},
            esperado=0.0,
            real=fator,
        )

    def test_aviso_gerado_quando_cap(self, audit):
        """Verifica que um aviso é gerado quando fator > 1.0."""
        audit.set_contexto(modulo="Devolucao", cenario="Aviso no cap")

        calc = DevolucaoCalculator()
        calc.calcular_fator_devolucao(200_000, 100_000)

        audit.verificar(
            descricao="Aviso gerado quando fator excede 1.0",
            formula="len(avisos) > 0",
            entradas={"devolvido": 200_000, "realizado": 100_000},
            esperado=True,
            real=len(calc.get_avisos()) > 0,
        )


# =========================================================================
# CLASSE: TestCalcularEstornoProcesso
# =========================================================================
@pytest.mark.unit
@pytest.mark.devolucao
class TestCalcularEstornoProcesso:
    """Testa calcular_estorno_processo()."""

    def test_estorno_unico_colaborador(self, audit):
        """Estorno de um único colaborador: comissao × fator (negativo)."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Um colaborador")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {
                "Nome_Colaborador": "Samanta Silva",
                "Comissao_Calculada": 1200.0,
                "Cargo": "Consultor Interno",
            }
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-001",
            numero_nf="NF-001",
            valor_devolvido=50_000,
            valor_realizado=100_000,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        assert len(resultado) == 1
        estorno = resultado[0]

        # Fator = 0.5, estorno = -(1200 × 0.5) = -600.0
        audit.verificar(
            descricao="Estorno Samanta Silva (50% devolucao)",
            formula="-(1200 × 0.5) = -600.0",
            entradas={"comissao_original": 1200.0, "fator": 0.5},
            esperado=-600.0,
            real=estorno["comissao_calculada"],
        )

    def test_estorno_sinal_negativo(self, audit):
        """O valor de comissao_calculada deve ser NEGATIVO."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Sinal negativo")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {
                "Nome_Colaborador": "Andrey Andrade",
                "Comissao_Calculada": 3000.0,
                "Cargo": "Gerente Linha",
            }
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-002",
            numero_nf="NF-002",
            valor_devolvido=100_000,
            valor_realizado=100_000,  # Devolução total
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        estorno = resultado[0]

        audit.verificar(
            descricao="Estorno total tem sinal negativo",
            formula="comissao_calculada < 0",
            entradas={"comissao_original": 3000.0, "fator": 1.0},
            esperado=True,
            real=estorno["comissao_calculada"] < 0,
        )
        audit.verificar(
            descricao="Valor absoluto do estorno total",
            formula="-(3000 × 1.0) = -3000.0",
            entradas={"comissao_original": 3000.0},
            esperado=-3000.0,
            real=estorno["comissao_calculada"],
        )

    def test_estorno_multiplos_colaboradores(self, audit):
        """Estorno para vários colaboradores no mesmo processo."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Multiplos colaboradores")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {"Nome_Colaborador": "Andrey Andrade", "Comissao_Calculada": 1200.0, "Cargo": "Gerente Linha"},
            {"Nome_Colaborador": "Rosana Martins", "Comissao_Calculada": 750.0, "Cargo": "Coordenador"},
            {"Nome_Colaborador": "Samanta Silva", "Comissao_Calculada": 600.0, "Cargo": "Consultor Interno"},
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-003",
            numero_nf="NF-003",
            valor_devolvido=40_000,
            valor_realizado=100_000,  # Fator = 0.4
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="Numero de estornos = numero de colaboradores",
            formula="len(resultado) == 3",
            entradas={"colaboradores": 3},
            esperado=3,
            real=len(resultado),
        )

        # Cada estorno: comissao × 0.4 (negativo)
        esperados = {
            "Andrey Andrade": -(1200.0 * 0.4),     # -480.0
            "Rosana Martins": -(750.0 * 0.4),       # -300.0
            "Samanta Silva": -(600.0 * 0.4),        # -240.0
        }

        for e in resultado:
            nome = e["nome_colaborador"]
            if nome in esperados:
                audit.verificar(
                    descricao=f"Estorno {nome} (fator 0.4)",
                    formula=f"-({e['comissao_original']} × 0.4)",
                    entradas={"comissao_original": e["comissao_original"], "fator": 0.4},
                    esperado=esperados[nome],
                    real=e["comissao_calculada"],
                )

    def test_estorno_agrupamento_mesmo_colaborador(self, audit):
        """Múltiplas linhas do mesmo colaborador são somadas antes do estorno."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Agrupamento")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {"Nome_Colaborador": "Samanta Silva", "Comissao_Calculada": 500.0, "Cargo": "Consultor Interno"},
            {"Nome_Colaborador": "Samanta Silva", "Comissao_Calculada": 300.0, "Cargo": "Consultor Interno"},
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-004",
            numero_nf="NF-004",
            valor_devolvido=100_000,
            valor_realizado=100_000,  # Fator = 1.0
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        # Deve ter 1 registro (agrupado)
        audit.verificar(
            descricao="Agrupamento: 2 linhas → 1 registro",
            formula="groupby(Nome_Colaborador).agg(sum)",
            entradas={"linhas_originais": 2},
            esperado=1,
            real=len(resultado),
        )

        # Comissão agrupada: 500 + 300 = 800, estorno: -800 × 1.0 = -800
        audit.verificar(
            descricao="Estorno agrupado (500+300) × fator 1.0",
            formula="-(800 × 1.0) = -800.0",
            entradas={"comissao_agrupada": 800.0, "fator": 1.0},
            esperado=-800.0,
            real=resultado[0]["comissao_calculada"],
        )

    def test_comissoes_historicas_vazias(self, audit):
        """Histórico vazio → lista de estornos vazia."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Historico vazio")

        calc = DevolucaoCalculator()
        historicas = pd.DataFrame(columns=["Nome_Colaborador", "Comissao_Calculada", "Cargo"])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-005",
            numero_nf="NF-005",
            valor_devolvido=50_000,
            valor_realizado=100_000,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="Sem historico → sem estornos",
            formula="len(resultado) == 0",
            entradas={"historico_vazio": True},
            esperado=0,
            real=len(resultado),
        )

    def test_fator_zero_retorna_vazio(self, audit):
        """Valor realizado=0 → fator=0 → nenhum estorno."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Fator zero")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {"Nome_Colaborador": "Andrey Andrade", "Comissao_Calculada": 1000.0, "Cargo": "Gerente Linha"},
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-006",
            numero_nf="NF-006",
            valor_devolvido=50_000,
            valor_realizado=0,  # fator = 0
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="Fator=0 → lista vazia",
            formula="fator == 0 → return []",
            entradas={"valor_realizado": 0},
            esperado=0,
            real=len(resultado),
        )

    def test_tipo_comissao_devolucao(self, audit):
        """O campo tipo_comissao deve ser 'DEVOLUCAO'."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Tipo comissao")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {"Nome_Colaborador": "Samanta Silva", "Comissao_Calculada": 500.0, "Cargo": "Consultor Interno"},
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-007",
            numero_nf="NF-007",
            valor_devolvido=50_000,
            valor_realizado=100_000,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="tipo_comissao = DEVOLUCAO",
            formula="registro['tipo_comissao']",
            entradas={},
            esperado="DEVOLUCAO",
            real=resultado[0]["tipo_comissao"],
        )

    def test_observacao_parcial_vs_total(self, audit):
        """Observação indica 'parcial' ou 'total' conforme fator."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Observacao parcial/total")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {"Nome_Colaborador": "Samanta Silva", "Comissao_Calculada": 1000.0, "Cargo": "Consultor Interno"},
        ])

        # Devolução parcial (fator < 1.0)
        resultado_parcial = calc.calcular_estorno_processo(
            processo="PROC-008A",
            numero_nf="NF-008A",
            valor_devolvido=30_000,
            valor_realizado=100_000,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="Observacao contem 'parcial' para fator < 1.0",
            formula="'parcial' in observacao",
            entradas={"fator": 0.3},
            esperado=True,
            real="parcial" in resultado_parcial[0]["observacao"].lower(),
        )

        # Devolução total (fator = 1.0)
        calc2 = DevolucaoCalculator()
        resultado_total = calc2.calcular_estorno_processo(
            processo="PROC-008B",
            numero_nf="NF-008B",
            valor_devolvido=100_000,
            valor_realizado=100_000,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="Observacao contem 'total' para fator = 1.0",
            formula="'total' in observacao",
            entradas={"fator": 1.0},
            esperado=True,
            real="total" in resultado_total[0]["observacao"].lower(),
        )

    def test_fator_devolucao_registrado_no_estorno(self, audit):
        """O registro de estorno contém o fator_devolucao usado."""
        audit.set_contexto(modulo="Devolucao Estorno", cenario="Fator no registro")

        calc = DevolucaoCalculator()
        historicas = _criar_historicas([
            {"Nome_Colaborador": "Andrey Andrade", "Comissao_Calculada": 2000.0, "Cargo": "Gerente Linha"},
        ])

        resultado = calc.calcular_estorno_processo(
            processo="PROC-009",
            numero_nf="NF-009",
            valor_devolvido=25_000,
            valor_realizado=100_000,  # fator = 0.25
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 6, 15),
            mes_apuracao=6,
            ano_apuracao=2025,
        )

        audit.verificar(
            descricao="fator_devolucao presente no registro",
            formula="registro['fator_devolucao'] == 0.25",
            entradas={"devolvido": 25_000, "realizado": 100_000},
            esperado=0.25,
            real=resultado[0]["fator_devolucao"],
        )

    def test_limpar_logs(self, audit):
        """limpar_logs() reseta erros e avisos."""
        audit.set_contexto(modulo="Devolucao", cenario="Limpar logs")

        calc = DevolucaoCalculator()
        calc.calcular_fator_devolucao(200_000, 100_000)  # gera aviso

        assert len(calc.get_avisos()) > 0
        calc.limpar_logs()

        audit.verificar(
            descricao="Avisos limpos apos limpar_logs()",
            formula="len(avisos) == 0",
            entradas={},
            esperado=0,
            real=len(calc.get_avisos()),
        )
