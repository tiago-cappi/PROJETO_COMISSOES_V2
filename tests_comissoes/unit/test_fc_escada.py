"""
Testes unitários para a regra de Escada/Rampa do FC.

Testa diretamente as funções do módulo src/core/fc_escada.py:
- load_fc_escada_cargos: carregamento e normalização de configurações
- aplicar_fc_escada: cálculo do multiplicador em modo RAMPA e ESCADA

Cada cenário documenta a fórmula e o cálculo manual esperado
para que o financeiro possa auditar pelo relatório Excel.
"""

import pytest
import pandas as pd

from src.core.fc_escada import (
    FcEscadaCargoConfig,
    aplicar_fc_escada,
    load_fc_escada_cargos,
)
from tests_comissoes.fixtures.config_factory import ConfigFactory


# =========================================================================
# Helpers: criar configs inline para testes cirúrgicos
# =========================================================================
def _configs_escada(cargo="Gerente Linha", modo="ESCADA", n=4, piso=0.5):
    """Cria um dict de configs com um único cargo para teste isolado."""
    key = cargo.strip().lower()
    return {
        key: FcEscadaCargoConfig(
            cargo=cargo,
            modo=modo,
            num_degraus=n,
            piso=piso,
        )
    }


# =========================================================================
# TESTES: load_fc_escada_cargos
# =========================================================================
class TestLoadFcEscadaCargos:
    """Testes de carregamento e normalização da aba FC_ESCADA_CARGOS."""

    def test_carregamento_basico(self, audit):
        """Deve carregar configurações válidas corretamente."""
        audit.set_contexto(modulo="FC Escada", cenario="Carregamento básico")
        df = ConfigFactory.criar_fc_escada_cargos()
        configs = load_fc_escada_cargos(df)

        audit.verificar(
            descricao="Número de cargos carregados",
            formula="len(configs) == número de linhas no DataFrame",
            entradas={"linhas_df": len(df)},
            esperado=len(df),
            real=len(configs),
        )

    def test_normaliza_cargo_para_lowercase(self, audit):
        """Chaves do dict devem ser lowercase para match case-insensitive."""
        audit.set_contexto(modulo="FC Escada", cenario="Normalização de cargo")
        df = pd.DataFrame([
            {"cargo": "Gerente Linha", "modo": "ESCADA", "num_degraus": 4, "piso_pct": 50},
        ])
        configs = load_fc_escada_cargos(df)

        audit.verificar(
            descricao="Cargo normalizado para lowercase",
            formula="'gerente linha' in configs.keys()",
            entradas={"cargo_original": "Gerente Linha"},
            esperado=True,
            real="gerente linha" in configs,
        )

    def test_piso_pct_como_percentual(self, audit):
        """piso_pct=50 deve virar piso=0.5."""
        audit.set_contexto(modulo="FC Escada", cenario="Conversão piso_pct → piso")
        df = pd.DataFrame([
            {"cargo": "Teste", "modo": "ESCADA", "num_degraus": 4, "piso_pct": 50},
        ])
        configs = load_fc_escada_cargos(df)

        audit.verificar(
            descricao="piso_pct=50 convertido para piso=0.5",
            formula="piso = piso_pct / 100 (se > 1.0)",
            entradas={"piso_pct": 50},
            esperado=0.5,
            real=configs["teste"].piso,
        )

    def test_piso_pct_como_decimal(self, audit):
        """piso_pct=0.5 deve permanecer 0.5 (já é fração)."""
        audit.set_contexto(modulo="FC Escada", cenario="piso_pct já decimal")
        df = pd.DataFrame([
            {"cargo": "Teste", "modo": "ESCADA", "num_degraus": 4, "piso_pct": 0.5},
        ])
        configs = load_fc_escada_cargos(df)

        audit.verificar(
            descricao="piso_pct=0.5 mantido como 0.5",
            formula="se 0 <= piso_pct <= 1 → piso = piso_pct",
            entradas={"piso_pct": 0.5},
            esperado=0.5,
            real=configs["teste"].piso,
        )

    def test_dataframe_vazio(self, audit):
        """DataFrame vazio deve retornar dict vazio."""
        audit.set_contexto(modulo="FC Escada", cenario="DataFrame vazio")
        configs = load_fc_escada_cargos(pd.DataFrame())

        audit.verificar(
            descricao="Retorno é dict vazio para DataFrame vazio",
            formula="load_fc_escada_cargos(DataFrame()) == {}",
            entradas={"df": "vazio"},
            esperado=0,
            real=len(configs),
        )

    def test_dataframe_none(self, audit):
        """None deve retornar dict vazio."""
        audit.set_contexto(modulo="FC Escada", cenario="None como entrada")
        configs = load_fc_escada_cargos(None)

        audit.verificar(
            descricao="Retorno é dict vazio para None",
            formula="load_fc_escada_cargos(None) == {}",
            entradas={"df": "None"},
            esperado=0,
            real=len(configs),
        )

    def test_modo_invalido_fallback_rampa(self, audit):
        """Modo inválido deve fazer fallback para RAMPA."""
        audit.set_contexto(modulo="FC Escada", cenario="Modo inválido → RAMPA")
        df = pd.DataFrame([
            {"cargo": "Teste", "modo": "INVALIDO", "num_degraus": 4, "piso_pct": 50},
        ])
        configs = load_fc_escada_cargos(df)

        audit.verificar(
            descricao="Modo 'INVALIDO' convertido para 'RAMPA'",
            formula="se modo ∉ {RAMPA, ESCADA} → modo = RAMPA",
            entradas={"modo_original": "INVALIDO"},
            esperado="RAMPA",
            real=configs["teste"].modo,
        )

    def test_num_degraus_minimo_2(self, audit):
        """num_degraus < 2 deve ser forçado para 2."""
        audit.set_contexto(modulo="FC Escada", cenario="num_degraus mínimo")
        df = pd.DataFrame([
            {"cargo": "Teste", "modo": "ESCADA", "num_degraus": 1, "piso_pct": 50},
        ])
        configs = load_fc_escada_cargos(df)

        audit.verificar(
            descricao="num_degraus=1 forçado para min=2",
            formula="max(2, num_degraus)",
            entradas={"num_degraus_original": 1},
            esperado=2,
            real=configs["teste"].num_degraus,
        )


# =========================================================================
# TESTES: aplicar_fc_escada — MODO RAMPA
# =========================================================================
class TestAplicarFcEscadaRampa:
    """Em modo RAMPA, o multiplicador é igual ao performance (identidade)."""

    @pytest.mark.parametrize("performance, esperado", [
        (0.0, 0.0),
        (0.25, 0.25),
        (0.5, 0.5),
        (0.75, 0.75),
        (1.0, 1.0),
    ])
    def test_rampa_identidade(self, audit, performance, esperado):
        """RAMPA: multiplicador = performance."""
        audit.set_contexto(modulo="FC Escada", cenario=f"RAMPA perf={performance}")
        configs = _configs_escada(modo="RAMPA")
        mult, det = aplicar_fc_escada(performance, "Gerente Linha", configs)

        audit.verificar(
            descricao=f"Multiplicador RAMPA com performance {performance}",
            formula="multiplicador = performance (identidade)",
            entradas={"performance": performance, "modo": "RAMPA"},
            esperado=esperado,
            real=mult,
            tolerancia=0.0001,
        )

    def test_rampa_cargo_nao_configurado(self, audit):
        """Cargo não configurado faz fallback para RAMPA."""
        audit.set_contexto(modulo="FC Escada", cenario="Cargo sem config → RAMPA")
        mult, det = aplicar_fc_escada(0.8, "Cargo Inexistente", {})

        audit.verificar(
            descricao="Cargo sem configuração usa RAMPA",
            formula="se cargo ∉ configs → modo = RAMPA → mult = perf",
            entradas={"performance": 0.8, "cargo": "Cargo Inexistente"},
            esperado=0.8,
            real=mult,
            tolerancia=0.0001,
        )

    def test_rampa_performance_negativa(self, audit):
        """Performance negativa é clampada para 0."""
        audit.set_contexto(modulo="FC Escada", cenario="RAMPA perf negativa")
        mult, det = aplicar_fc_escada(-0.5, "Gerente Linha", _configs_escada(modo="RAMPA"))

        audit.verificar(
            descricao="Performance negativa clampada para 0",
            formula="max(0, performance)",
            entradas={"performance": -0.5},
            esperado=0.0,
            real=mult,
            tolerancia=0.0001,
        )


# =========================================================================
# TESTES: aplicar_fc_escada — MODO ESCADA
# =========================================================================
class TestAplicarFcEscadaEscada:
    """Testes do modo ESCADA com degraus discretos.

    Fórmula:
        i = floor(performance × (n-1))    se performance < 1.0
        i = n - 1                          se performance >= 1.0
        multiplicador = piso + (i × (1 - piso) / (n - 1))
    """

    # ------------------------------------------------------------------
    # 4 degraus, piso 50%
    # Degraus: 0→0.500, 1→0.667, 2→0.833, 3→1.000
    # Limiares: [0, 0.333), [0.333, 0.667), [0.667, 1.0), [1.0+]
    # ------------------------------------------------------------------
    def test_4degraus_piso50_degrau0(self, audit):
        """Performance 0.20 → degrau 0 → multiplicador 0.500."""
        audit.set_contexto(modulo="FC Escada", cenario="4 degraus, piso 50%")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(0.20, "Gerente Linha", configs)

        # i = floor(0.20 × 3) = floor(0.6) = 0
        # mult = 0.5 + (0 × 0.5 / 3) = 0.5
        audit.verificar(
            descricao="Perf 0.20 → degrau 0 → mult 0.500",
            formula="i=floor(0.20×3)=0; mult=0.5+(0×0.5/3)=0.500",
            entradas={"performance": 0.20, "n": 4, "piso": 0.5},
            esperado=0.500,
            real=mult,
            tolerancia=0.001,
        )
        assert det["degrau_indice"] == 0

    def test_4degraus_piso50_degrau1(self, audit):
        """Performance 0.40 → degrau 1 → multiplicador 0.667."""
        audit.set_contexto(modulo="FC Escada", cenario="4 degraus, piso 50%")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(0.40, "Gerente Linha", configs)

        # i = floor(0.40 × 3) = floor(1.2) = 1
        # mult = 0.5 + (1 × 0.5 / 3) = 0.5 + 0.1667 = 0.6667
        audit.verificar(
            descricao="Perf 0.40 → degrau 1 → mult 0.667",
            formula="i=floor(0.40×3)=1; mult=0.5+(1×0.5/3)=0.667",
            entradas={"performance": 0.40, "n": 4, "piso": 0.5},
            esperado=0.6667,
            real=mult,
            tolerancia=0.001,
        )
        assert det["degrau_indice"] == 1

    def test_4degraus_piso50_degrau2(self, audit):
        """Performance 0.80 → degrau 2 → multiplicador 0.833."""
        audit.set_contexto(modulo="FC Escada", cenario="4 degraus, piso 50%")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(0.80, "Gerente Linha", configs)

        # i = floor(0.80 × 3) = floor(2.4) = 2
        # mult = 0.5 + (2 × 0.5 / 3) = 0.5 + 0.3333 = 0.8333
        audit.verificar(
            descricao="Perf 0.80 → degrau 2 → mult 0.833",
            formula="i=floor(0.80×3)=2; mult=0.5+(2×0.5/3)=0.833",
            entradas={"performance": 0.80, "n": 4, "piso": 0.5},
            esperado=0.8333,
            real=mult,
            tolerancia=0.001,
        )
        assert det["degrau_indice"] == 2

    def test_4degraus_piso50_topo(self, audit):
        """Performance 1.00 → degrau 3 (topo) → multiplicador 1.000."""
        audit.set_contexto(modulo="FC Escada", cenario="4 degraus, piso 50%")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(1.00, "Gerente Linha", configs)

        # perf >= 1.0 → i = n-1 = 3
        # mult = 0.5 + (3 × 0.5 / 3) = 0.5 + 0.5 = 1.0
        audit.verificar(
            descricao="Perf 1.00 → degrau 3 (topo) → mult 1.000",
            formula="perf≥1.0 → i=n-1=3; mult=0.5+(3×0.5/3)=1.000",
            entradas={"performance": 1.00, "n": 4, "piso": 0.5},
            esperado=1.000,
            real=mult,
            tolerancia=0.001,
        )
        assert det["degrau_indice"] == 3

    def test_4degraus_piso50_acima_100pct(self, audit):
        """Performance 1.20 (acima de 100%) → sempre topo."""
        audit.set_contexto(modulo="FC Escada", cenario="4 degraus, acima 100%")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(1.20, "Gerente Linha", configs)

        audit.verificar(
            descricao="Perf 1.20 (>100%) → topo fixo 1.000",
            formula="perf≥1.0 → sempre degrau topo → mult=1.000",
            entradas={"performance": 1.20, "n": 4, "piso": 0.5},
            esperado=1.000,
            real=mult,
            tolerancia=0.001,
        )

    # ------------------------------------------------------------------
    # Limiar exato entre degraus (sem tolerância)
    # ------------------------------------------------------------------
    def test_limiar_exato_sobe_degrau(self, audit):
        """No limiar exato (0.3333...) deve subir de degrau."""
        audit.set_contexto(modulo="FC Escada", cenario="Limiar exato entre degraus")
        configs = _configs_escada(n=4, piso=0.5)
        # Limiar do degrau 1 = 1/3 ≈ 0.33333
        perf = 1.0 / 3.0
        mult, det = aplicar_fc_escada(perf, "Gerente Linha", configs)

        # i = floor(0.3333 × 3) = floor(1.0) = 1
        audit.verificar(
            descricao="Limiar exato 1/3 → floor(1/3 × 3)=1 → degrau 1",
            formula="i=floor(0.333×3)=floor(1.0)=1",
            entradas={"performance": round(perf, 6), "n": 4, "piso": 0.5},
            esperado=1,
            real=det["degrau_indice"],
        )

    def test_logo_abaixo_limiar(self, audit):
        """Logo abaixo do limiar (0.332) deve ficar no degrau anterior."""
        audit.set_contexto(modulo="FC Escada", cenario="Logo abaixo do limiar")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(0.332, "Gerente Linha", configs)

        # i = floor(0.332 × 3) = floor(0.996) = 0
        audit.verificar(
            descricao="Perf 0.332 (abaixo limiar 1/3) → degrau 0",
            formula="i=floor(0.332×3)=floor(0.996)=0",
            entradas={"performance": 0.332, "n": 4, "piso": 0.5},
            esperado=0,
            real=det["degrau_indice"],
        )

    # ------------------------------------------------------------------
    # 3 degraus, piso 60%
    # Degraus: 0→0.600, 1→0.800, 2→1.000
    # Limiares: [0, 0.5), [0.5, 1.0), [1.0+]
    # ------------------------------------------------------------------
    def test_3degraus_piso60_degrau0(self, audit):
        """3 degraus, piso 60%: perf 0.30 → degrau 0."""
        audit.set_contexto(modulo="FC Escada", cenario="3 degraus, piso 60%")
        configs = _configs_escada(n=3, piso=0.6)
        mult, det = aplicar_fc_escada(0.30, "Gerente Linha", configs)

        # i = floor(0.30 × 2) = floor(0.6) = 0
        # mult = 0.6 + (0 × 0.4 / 2) = 0.6
        audit.verificar(
            descricao="Perf 0.30 → degrau 0 → mult 0.600",
            formula="i=floor(0.30×2)=0; mult=0.6+(0×0.4/2)=0.600",
            entradas={"performance": 0.30, "n": 3, "piso": 0.6},
            esperado=0.600,
            real=mult,
            tolerancia=0.001,
        )

    def test_3degraus_piso60_degrau1(self, audit):
        """3 degraus, piso 60%: perf 0.70 → degrau 1."""
        audit.set_contexto(modulo="FC Escada", cenario="3 degraus, piso 60%")
        configs = _configs_escada(n=3, piso=0.6)
        mult, det = aplicar_fc_escada(0.70, "Gerente Linha", configs)

        # i = floor(0.70 × 2) = floor(1.4) = 1
        # mult = 0.6 + (1 × 0.4 / 2) = 0.6 + 0.2 = 0.8
        audit.verificar(
            descricao="Perf 0.70 → degrau 1 → mult 0.800",
            formula="i=floor(0.70×2)=1; mult=0.6+(1×0.4/2)=0.800",
            entradas={"performance": 0.70, "n": 3, "piso": 0.6},
            esperado=0.800,
            real=mult,
            tolerancia=0.001,
        )

    # ------------------------------------------------------------------
    # 2 degraus (mínimo), piso 0%
    # Degraus: 0→0.000, 1→1.000
    # ------------------------------------------------------------------
    def test_2degraus_piso0_baixo(self, audit):
        """2 degraus, piso 0%: perf < 1.0 → degrau 0 → mult 0."""
        audit.set_contexto(modulo="FC Escada", cenario="2 degraus, piso 0%")
        configs = _configs_escada(n=2, piso=0.0)
        mult, det = aplicar_fc_escada(0.99, "Gerente Linha", configs)

        # i = floor(0.99 × 1) = floor(0.99) = 0  (capado em n-2=0)
        # mult = 0 + (0 × 1.0 / 1) = 0
        audit.verificar(
            descricao="Perf 0.99 com 2 degraus piso 0% → mult 0.000",
            formula="i=floor(0.99×1)=0; mult=0+(0×1/1)=0.000",
            entradas={"performance": 0.99, "n": 2, "piso": 0.0},
            esperado=0.0,
            real=mult,
            tolerancia=0.001,
        )

    def test_2degraus_piso0_topo(self, audit):
        """2 degraus, piso 0%: perf >= 1.0 → degrau 1 → mult 1."""
        audit.set_contexto(modulo="FC Escada", cenario="2 degraus, piso 0%")
        configs = _configs_escada(n=2, piso=0.0)
        mult, det = aplicar_fc_escada(1.0, "Gerente Linha", configs)

        # perf >= 1.0 → i = n-1 = 1
        # mult = 0 + (1 × 1.0 / 1) = 1.0
        audit.verificar(
            descricao="Perf 1.00 com 2 degraus piso 0% → topo 1.000",
            formula="perf≥1.0 → i=1; mult=0+(1×1/1)=1.000",
            entradas={"performance": 1.0, "n": 2, "piso": 0.0},
            esperado=1.0,
            real=mult,
            tolerancia=0.001,
        )

    # ------------------------------------------------------------------
    # 5 degraus, piso 40% (Consultor Interno)
    # Degraus: 0→0.400, 1→0.550, 2→0.700, 3→0.850, 4→1.000
    # ------------------------------------------------------------------
    def test_5degraus_piso40_degrau2(self, audit):
        """5 degraus, piso 40%: perf 0.60 → degrau 2."""
        audit.set_contexto(modulo="FC Escada", cenario="5 degraus, piso 40%")
        configs = _configs_escada(cargo="Consultor Interno", n=5, piso=0.4)
        mult, det = aplicar_fc_escada(0.60, "Consultor Interno", configs)

        # i = floor(0.60 × 4) = floor(2.4) = 2
        # mult = 0.4 + (2 × 0.6 / 4) = 0.4 + 0.3 = 0.7
        audit.verificar(
            descricao="Perf 0.60 → degrau 2 → mult 0.700",
            formula="i=floor(0.60×4)=2; mult=0.4+(2×0.6/4)=0.700",
            entradas={"performance": 0.60, "n": 5, "piso": 0.4},
            esperado=0.700,
            real=mult,
            tolerancia=0.001,
        )
        assert det["degrau_indice"] == 2

    def test_5degraus_piso40_degrau3(self, audit):
        """5 degraus, piso 40%: perf 0.85 → degrau 3."""
        audit.set_contexto(modulo="FC Escada", cenario="5 degraus, piso 40%")
        configs = _configs_escada(cargo="Consultor Interno", n=5, piso=0.4)
        mult, det = aplicar_fc_escada(0.85, "Consultor Interno", configs)

        # i = floor(0.85 × 4) = floor(3.4) = 3  (cap em n-2=3)
        # mult = 0.4 + (3 × 0.6 / 4) = 0.4 + 0.45 = 0.85
        audit.verificar(
            descricao="Perf 0.85 → degrau 3 → mult 0.850",
            formula="i=floor(0.85×4)=3; mult=0.4+(3×0.6/4)=0.850",
            entradas={"performance": 0.85, "n": 5, "piso": 0.4},
            esperado=0.850,
            real=mult,
            tolerancia=0.001,
        )
        assert det["degrau_indice"] == 3

    # ------------------------------------------------------------------
    # Performance = 0 (edge case)
    # ------------------------------------------------------------------
    def test_performance_zero_escada(self, audit):
        """Performance 0 → degrau 0 → multiplicador = piso."""
        audit.set_contexto(modulo="FC Escada", cenario="Performance zero")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(0.0, "Gerente Linha", configs)

        audit.verificar(
            descricao="Perf 0 → degrau 0 → mult = piso = 0.500",
            formula="i=floor(0×3)=0; mult=0.5+(0×0.5/3)=0.500",
            entradas={"performance": 0.0, "n": 4, "piso": 0.5},
            esperado=0.500,
            real=mult,
            tolerancia=0.001,
        )

    # ------------------------------------------------------------------
    # Detalhes retornados
    # ------------------------------------------------------------------
    def test_detalhes_escada_completos(self, audit):
        """Detalhes retornados devem conter todos os campos."""
        audit.set_contexto(modulo="FC Escada", cenario="Detalhes retornados")
        configs = _configs_escada(n=4, piso=0.5)
        mult, det = aplicar_fc_escada(0.75, "Gerente Linha", configs)

        campos_obrigatorios = ["modo", "cargo", "performance_rampa", "multiplicador",
                               "num_degraus", "piso", "degrau_indice"]
        for campo in campos_obrigatorios:
            audit.verificar(
                descricao=f"Campo '{campo}' presente nos detalhes",
                formula=f"'{campo}' in detalhes",
                entradas={"performance": 0.75},
                esperado=True,
                real=campo in det,
            )

    def test_detalhes_rampa_campos_none(self, audit):
        """Em RAMPA, piso/num_degraus/degrau_indice devem ser None."""
        audit.set_contexto(modulo="FC Escada", cenario="Detalhes RAMPA = None")
        configs = _configs_escada(modo="RAMPA")
        mult, det = aplicar_fc_escada(0.75, "Gerente Linha", configs)

        for campo in ["piso", "num_degraus", "degrau_indice"]:
            audit.verificar(
                descricao=f"Campo '{campo}' é None em modo RAMPA",
                formula=f"detalhes['{campo}'] is None",
                entradas={"modo": "RAMPA"},
                esperado="None",
                real=str(det[campo]),
            )
