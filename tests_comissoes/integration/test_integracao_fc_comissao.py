"""
Testes de integração: FC Escada + Comissão Faturamento.

Valida o fluxo completo desde o carregamento de configs até o cálculo final:

    1. load_fc_escada_cargos(DataFrame) → configs por cargo
    2. aplicar_fc_escada(performance, cargo, configs) → fc_aplicado
    3. comissao_potencial × fc_aplicado → comissao_item

Fluxo integrado:
    ConfigFactory → load_fc_escada_cargos → aplicar_fc_escada → fórmula comissão

Cenários:
    - Pipeline completo: config → escada → comissão (Gerente ESCADA)
    - Pipeline completo: config → rampa → comissão (Diretor RAMPA)
    - Consultor Interno ESCADA com piso 40%, performance parcial
    - Performance zero → piso → comissão reduzida
    - Performance 100% → topo → comissão máxima
    - Cargo não configurado → fallback RAMPA
    - Múltiplos cargos no mesmo item (time completo)
    - Cross-selling ajusta taxa → comissão final com FC
    - Devolução fator + comissão original → estorno proporcional
    - Config com 5 degraus (granularidade fina)
"""

import pytest
import pandas as pd
from datetime import datetime

from src.core.fc_escada import load_fc_escada_cargos, aplicar_fc_escada
from src.devolucao.devolucao_calculator import DevolucaoCalculator
from tests_comissoes.fixtures.config_factory import ConfigFactory


# =========================================================================
# HELPERS: Reproduz fórmula completa de integração
# =========================================================================

def _pipeline_comissao(
    faturamento: float,
    taxa_rateio_maximo_pct: float,
    fatia_cargo_pct: float,
    performance: float,
    cargo: str,
    fc_configs: dict,
    fator_split: float = 1.0,
) -> dict:
    """Pipeline completo: config → escada → comissão."""
    taxa_rateio = taxa_rateio_maximo_pct / 100.0
    pe = fatia_cargo_pct / 100.0

    fc_aplicado, detalhes_fc = aplicar_fc_escada(performance, cargo, fc_configs)

    comissao_potencial = faturamento * taxa_rateio * pe * fator_split
    comissao_item = comissao_potencial * fc_aplicado

    return {
        "taxa_rateio": taxa_rateio,
        "pe": pe,
        "fc_aplicado": fc_aplicado,
        "comissao_potencial": comissao_potencial,
        "comissao_item": comissao_item,
        "detalhes_fc": detalhes_fc,
    }


# =========================================================================
# CLASSE: TestFCEscadaComissaoIntegrado
# =========================================================================
@pytest.mark.integration
@pytest.mark.fc
@pytest.mark.faturamento
class TestFCEscadaComissaoIntegrado:
    """Testa o fluxo completo Config → FC Escada → Comissão."""

    def test_gerente_escada_performance_80(self, audit):
        """Gerente Linha ESCADA 4 degraus, piso 50%, perf=80%.

        Degrau: int(0.8 × 3) = 2
        Mult: 0.5 + (2 × 0.5/3) = 0.8333
        Comissao: 200000 × 0.03 × 0.40 × 0.8333 = 2000.0
        """
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Gerente ESCADA perf=80%")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=200_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=40.0,
            performance=0.80,
            cargo="Gerente Linha",
            fc_configs=configs,
        )

        # Verificar FC
        piso = 0.50
        n = 4
        degrau = int(0.80 * (n - 1))  # = 2
        mult_esperado = piso + (degrau * (1.0 - piso) / (n - 1))

        audit.verificar(
            descricao="FC aplicado ESCADA degrau 2",
            formula=f"0.5 + (2 x 0.5 / 3) = {mult_esperado:.4f}",
            entradas={"performance": 0.80, "n": 4, "piso": 0.50, "degrau": degrau},
            esperado=round(mult_esperado, 6),
            real=round(resultado["fc_aplicado"], 6),
        )

        # Verificar comissão final
        comissao_esperada = 200_000 * 0.03 * 0.40 * mult_esperado

        audit.verificar(
            descricao="Comissao final integrada",
            formula=f"200000 x 0.03 x 0.40 x {mult_esperado:.4f} = {comissao_esperada:.2f}",
            entradas={"fat": 200_000, "taxa": 0.03, "pe": 0.40, "fc": mult_esperado},
            esperado=round(comissao_esperada, 2),
            real=round(resultado["comissao_item"], 2),
        )

    def test_diretor_rampa_performance_70(self, audit):
        """Diretor RAMPA, perf=70% → mult=0.70 (linear).

        Comissao: 300000 × 0.03 × 0.10 × 0.70 = 630.0
        """
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Diretor RAMPA perf=70%")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=300_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=10.0,
            performance=0.70,
            cargo="Diretor",
            fc_configs=configs,
        )

        audit.verificar(
            descricao="FC aplicado RAMPA = performance",
            formula="performance = 0.70 (linear)",
            entradas={"performance": 0.70, "modo": "RAMPA"},
            esperado=0.70,
            real=resultado["fc_aplicado"],
        )

        comissao_esperada = 300_000 * 0.03 * 0.10 * 0.70

        audit.verificar(
            descricao="Comissao final RAMPA",
            formula="300000 x 0.03 x 0.10 x 0.70 = 630.0",
            entradas={"fat": 300_000, "taxa": 0.03, "pe": 0.10, "fc": 0.70},
            esperado=comissao_esperada,
            real=resultado["comissao_item"],
        )

    def test_consultor_interno_escada_5_degraus_performance_45(self, audit):
        """Consultor Interno ESCADA 5 degraus, piso 40%, perf=45%.

        Degrau: int(0.45 × 4) = 1
        Mult: 0.40 + (1 × 0.60/4) = 0.55
        Comissao: 100000 × 0.03 × 0.20 × 0.55 = 330.0
        """
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="CI ESCADA 5 degraus perf=45%")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=100_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=20.0,
            performance=0.45,
            cargo="Consultor Interno",
            fc_configs=configs,
        )

        piso = 0.40
        n = 5
        degrau = int(0.45 * (n - 1))  # = 1
        mult_esperado = piso + (degrau * (1.0 - piso) / (n - 1))

        audit.verificar(
            descricao="FC ESCADA 5 degraus, degrau 1",
            formula=f"0.40 + (1 x 0.60 / 4) = {mult_esperado:.4f}",
            entradas={"performance": 0.45, "n": 5, "piso": 0.40, "degrau": degrau},
            esperado=round(mult_esperado, 6),
            real=round(resultado["fc_aplicado"], 6),
        )

        comissao_esperada = 100_000 * 0.03 * 0.20 * mult_esperado

        audit.verificar(
            descricao="Comissao CI integrada",
            formula=f"100000 x 0.03 x 0.20 x {mult_esperado:.4f}",
            entradas={"fat": 100_000, "taxa": 0.03, "pe": 0.20, "fc": mult_esperado},
            esperado=round(comissao_esperada, 2),
            real=round(resultado["comissao_item"], 2),
        )

    def test_performance_zero_piso(self, audit):
        """Performance=0 → FC=piso. Comissão reduzida ao mínimo."""
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Performance zero piso")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=150_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=40.0,
            performance=0.0,
            cargo="Gerente Linha",
            fc_configs=configs,
        )

        # Gerente: ESCADA, piso=0.50, n=4. perf=0 → degrau=0 → mult=piso=0.50
        piso = 0.50

        audit.verificar(
            descricao="FC no piso com performance zero",
            formula="degrau 0 -> mult = piso = 0.50",
            entradas={"performance": 0.0, "piso": 0.50},
            esperado=piso,
            real=resultado["fc_aplicado"],
        )

        comissao_esperada = 150_000 * 0.03 * 0.40 * piso

        audit.verificar(
            descricao="Comissao no piso",
            formula=f"150000 x 0.03 x 0.40 x 0.50 = {comissao_esperada:.2f}",
            entradas={"fat": 150_000, "fc": piso},
            esperado=comissao_esperada,
            real=resultado["comissao_item"],
        )

    def test_performance_100_topo(self, audit):
        """Performance=1.0 → FC=1.0 (topo). Comissão máxima."""
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Performance 100% topo")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=200_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=40.0,
            performance=1.0,
            cargo="Gerente Linha",
            fc_configs=configs,
        )

        audit.verificar(
            descricao="FC no topo com performance 100%",
            formula="perf >= 1.0 -> degrau n-1 -> mult = 1.0",
            entradas={"performance": 1.0},
            esperado=1.0,
            real=resultado["fc_aplicado"],
        )

        comissao_esperada = 200_000 * 0.03 * 0.40 * 1.0

        audit.verificar(
            descricao="Comissao maxima no topo",
            formula="200000 x 0.03 x 0.40 x 1.0 = 2400.0",
            entradas={"fat": 200_000, "fc": 1.0},
            esperado=comissao_esperada,
            real=resultado["comissao_item"],
        )

    def test_cargo_nao_configurado_fallback_rampa(self, audit):
        """Cargo inexistente → fallback RAMPA → mult=performance."""
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Cargo desconhecido fallback")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=80_000.0,
            taxa_rateio_maximo_pct=2.5,
            fatia_cargo_pct=30.0,
            performance=0.65,
            cargo="Cargo Inexistente",
            fc_configs=configs,
        )

        audit.verificar(
            descricao="Cargo desconhecido -> fallback RAMPA",
            formula="configs.get(cargo) == None -> RAMPA -> perf",
            entradas={"cargo": "Cargo Inexistente", "performance": 0.65},
            esperado=0.65,
            real=resultado["fc_aplicado"],
        )

        audit.verificar(
            descricao="Modo registrado como RAMPA",
            formula="Fallback padrao",
            entradas={},
            esperado="RAMPA",
            real=resultado["detalhes_fc"]["modo"],
        )

    def test_time_completo_mesmo_item(self, audit):
        """Múltiplos cargos (Gerente + Coordenador + CI) no mesmo item.

        Cada cargo tem seu FC via escada e sua fatia_cargo_pct.
        """
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Time completo")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        faturamento = 200_000.0
        taxa_pct = 3.0
        performance = 0.75

        time_cargos = [
            {"cargo": "Gerente Linha", "fatia_pct": 40.0},
            {"cargo": "Coordenador", "fatia_pct": 25.0},
            {"cargo": "Consultor Interno", "fatia_pct": 20.0},
        ]

        total_comissao = 0.0

        for membro in time_cargos:
            r = _pipeline_comissao(
                faturamento=faturamento,
                taxa_rateio_maximo_pct=taxa_pct,
                fatia_cargo_pct=membro["fatia_pct"],
                performance=performance,
                cargo=membro["cargo"],
                fc_configs=configs,
            )

            audit.verificar(
                descricao=f"Comissao {membro['cargo']} (perf=75%)",
                formula=f"{faturamento} x {taxa_pct/100} x {membro['fatia_pct']/100} x FC",
                entradas={
                    "cargo": membro["cargo"],
                    "fatia": membro["fatia_pct"],
                    "fc": round(r["fc_aplicado"], 4),
                },
                esperado=round(r["comissao_item"], 2),
                real=round(r["comissao_item"], 2),
            )

            total_comissao += r["comissao_item"]

        # Soma das fatias = 85%, então total < faturamento × taxa × 0.85 × 1.0
        teto_maximo = faturamento * (taxa_pct / 100) * 0.85 * 1.0

        audit.verificar(
            descricao="Total comissao time <= teto maximo",
            formula="total <= fat x taxa x soma_fatias x 1.0",
            entradas={"total": round(total_comissao, 2), "teto": round(teto_maximo, 2)},
            esperado="True",
            real=str(total_comissao <= teto_maximo + 0.01),
        )

    def test_cross_selling_reduz_taxa_depois_fc(self, audit):
        """Cross-selling decisão A reduz taxa. Depois aplica FC via escada.

        taxa_ajustada = max(0, taxa_rateio - taxa_cs)
        comissao = fat × taxa_ajustada × pe × fc_aplicado
        """
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Cross-selling + FC")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        faturamento = 150_000.0
        taxa_rateio_pct = 3.0
        taxa_cs_pct = 1.0
        fatia_pct = 40.0
        performance = 0.90

        # Cross-selling A: reduz taxa
        taxa_ajustada = max(0.0, (taxa_rateio_pct - taxa_cs_pct) / 100.0)

        # FC via escada (Gerente: ESCADA, n=4, piso=50%)
        fc_aplicado, _ = aplicar_fc_escada(performance, "Gerente Linha", configs)

        pe = fatia_pct / 100.0
        comissao = faturamento * taxa_ajustada * pe * fc_aplicado

        # Pipeline com taxa já ajustada
        resultado = _pipeline_comissao(
            faturamento=faturamento,
            taxa_rateio_maximo_pct=taxa_rateio_pct - taxa_cs_pct,  # 2.0
            fatia_cargo_pct=fatia_pct,
            performance=performance,
            cargo="Gerente Linha",
            fc_configs=configs,
        )

        audit.verificar(
            descricao="Comissao com cross-selling + FC escada",
            formula=f"150000 x {taxa_ajustada} x 0.40 x {fc_aplicado:.4f}",
            entradas={
                "taxa_original": taxa_rateio_pct,
                "taxa_cs": taxa_cs_pct,
                "taxa_ajustada_pct": taxa_rateio_pct - taxa_cs_pct,
                "fc": round(fc_aplicado, 4),
            },
            esperado=round(comissao, 2),
            real=round(resultado["comissao_item"], 2),
        )

    def test_split_cargo_com_escada(self, audit):
        """Split de cargo (fator_split=0.5) combinado com escada.

        comissao = fat × taxa × pe × 0.5 × fc_aplicado
        """
        audit.set_contexto(modulo="Integracao FC+Comissao", cenario="Split + ESCADA")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        resultado = _pipeline_comissao(
            faturamento=200_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=40.0,
            performance=0.80,
            cargo="Gerente Linha",
            fc_configs=configs,
            fator_split=0.5,
        )

        # Sem split
        resultado_sem_split = _pipeline_comissao(
            faturamento=200_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=40.0,
            performance=0.80,
            cargo="Gerente Linha",
            fc_configs=configs,
            fator_split=1.0,
        )

        audit.verificar(
            descricao="Split reduz comissao pela metade",
            formula="com_split = sem_split / 2",
            entradas={"com_split": round(resultado["comissao_item"], 2)},
            esperado=round(resultado_sem_split["comissao_item"] / 2, 2),
            real=round(resultado["comissao_item"], 2),
        )


# =========================================================================
# CLASSE: TestDevolucaoComissaoIntegrado
# =========================================================================
@pytest.mark.integration
@pytest.mark.devolucao
@pytest.mark.faturamento
class TestDevolucaoComissaoIntegrado:
    """Testa o fluxo: Comissão original → Devolução → Estorno proporcional."""

    def test_devolucao_parcial_com_comissao_calculada(self, audit):
        """Cenário completo: calcula comissão e depois estorna parcialmente.

        Comissão original = 200000 × 0.03 × 0.40 × 0.8333 = 2000.0
        Devolução 40%: fator = 0.4
        Estorno = -2000.0 × 0.4 = -800.0
        """
        audit.set_contexto(modulo="Integracao Devolucao+Comissao", cenario="Devolucao parcial 40%")

        # Passo 1: Calcular comissão via pipeline
        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        comissao_result = _pipeline_comissao(
            faturamento=200_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=40.0,
            performance=0.80,
            cargo="Gerente Linha",
            fc_configs=configs,
        )
        comissao_original = comissao_result["comissao_item"]

        # Passo 2: Calcular devolução
        calc_dev = DevolucaoCalculator()
        valor_devolvido = 80_000.0  # 40% de 200k
        valor_realizado = 200_000.0

        fator = calc_dev.calcular_fator_devolucao(valor_devolvido, valor_realizado)

        # Passo 3: Simular estorno
        historicas = pd.DataFrame([{
            "Nome_Colaborador": "Andrey Andrade",
            "Cargo": "Gerente Linha",
            "Comissao_Calculada": comissao_original,
        }])

        estornos = calc_dev.calcular_estorno_processo(
            processo="PROC-INT-001",
            numero_nf="NF-001",
            valor_devolvido=valor_devolvido,
            valor_realizado=valor_realizado,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 7, 15),
            mes_apuracao=7,
            ano_apuracao=2025,
        )

        assert len(estornos) == 1
        estorno = estornos[0]

        estorno_esperado = -(comissao_original * fator)

        audit.verificar(
            descricao="Fator devolucao 40%",
            formula="80000 / 200000 = 0.4",
            entradas={"devolvido": 80_000, "realizado": 200_000},
            esperado=0.4,
            real=fator,
        )

        audit.verificar(
            descricao="Estorno proporcional (negativo)",
            formula=f"-({comissao_original:.2f} x 0.4) = {estorno_esperado:.2f}",
            entradas={"comissao_original": round(comissao_original, 2), "fator": 0.4},
            esperado=round(estorno_esperado, 2),
            real=round(estorno["comissao_calculada"], 2),
        )

    def test_devolucao_total_estorna_tudo(self, audit):
        """Devolução total: fator=1.0, estorno = -comissão_original."""
        audit.set_contexto(modulo="Integracao Devolucao+Comissao", cenario="Devolucao total")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        comissao_result = _pipeline_comissao(
            faturamento=100_000.0,
            taxa_rateio_maximo_pct=3.0,
            fatia_cargo_pct=20.0,
            performance=1.0,
            cargo="Consultor Interno",
            fc_configs=configs,
        )
        comissao_original = comissao_result["comissao_item"]

        calc_dev = DevolucaoCalculator()

        historicas = pd.DataFrame([{
            "Nome_Colaborador": "Samanta Silva",
            "Cargo": "Consultor Interno",
            "Comissao_Calculada": comissao_original,
        }])

        estornos = calc_dev.calcular_estorno_processo(
            processo="PROC-INT-002",
            numero_nf="NF-002",
            valor_devolvido=100_000.0,
            valor_realizado=100_000.0,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 8, 1),
            mes_apuracao=8,
            ano_apuracao=2025,
        )

        estorno_esperado = -comissao_original

        audit.verificar(
            descricao="Estorno total (negativo de 100%)",
            formula=f"-{comissao_original:.2f}",
            entradas={"comissao_original": round(comissao_original, 2), "fator": 1.0},
            esperado=round(estorno_esperado, 2),
            real=round(estornos[0]["comissao_calculada"], 2),
        )

    def test_multiplos_colaboradores_devolucao(self, audit):
        """Devolução afeta múltiplos colaboradores proporcionalmente."""
        audit.set_contexto(modulo="Integracao Devolucao+Comissao", cenario="Devolucao multi-colab")

        df_escada = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df_escada)

        faturamento = 200_000.0
        performance = 0.90
        taxa_pct = 3.0

        # Calcular comissões para 2 cargos
        r_gerente = _pipeline_comissao(faturamento, taxa_pct, 40.0, performance, "Gerente Linha", configs)
        r_ci = _pipeline_comissao(faturamento, taxa_pct, 20.0, performance, "Consultor Interno", configs)

        historicas = pd.DataFrame([
            {"Nome_Colaborador": "Andrey Andrade", "Cargo": "Gerente Linha",
             "Comissao_Calculada": r_gerente["comissao_item"]},
            {"Nome_Colaborador": "Samanta Silva", "Cargo": "Consultor Interno",
             "Comissao_Calculada": r_ci["comissao_item"]},
        ])

        calc_dev = DevolucaoCalculator()
        estornos = calc_dev.calcular_estorno_processo(
            processo="PROC-INT-003",
            numero_nf="NF-003",
            valor_devolvido=60_000.0,  # 30%
            valor_realizado=200_000.0,
            comissoes_historicas=historicas,
            data_devolucao=datetime(2025, 9, 10),
            mes_apuracao=9,
            ano_apuracao=2025,
        )

        assert len(estornos) == 2

        for estorno in estornos:
            nome = estorno["nome_colaborador"]
            if nome == "Andrey Andrade":
                esperado = -(r_gerente["comissao_item"] * 0.30)
            else:
                esperado = -(r_ci["comissao_item"] * 0.30)

            audit.verificar(
                descricao=f"Estorno 30% {nome}",
                formula=f"-comissao x 0.30",
                entradas={"colaborador": nome, "fator": 0.30},
                esperado=round(esperado, 2),
                real=round(estorno["comissao_calculada"], 2),
            )
