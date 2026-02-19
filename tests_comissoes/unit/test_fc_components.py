"""
Testes unitários para os componentes individuais do cálculo do FC.

Testa:
- calcular_atingimento (de src/utils/normalization.py)
- Capping individual (cap_atingimento_max)
- Soma ponderada dos componentes
- Capping total (cap_fc_max)

Cada cenário documenta a fórmula e o cálculo manual esperado.
"""

import pytest

from src.utils.normalization import calcular_atingimento


# =========================================================================
# TESTES: calcular_atingimento
# =========================================================================
class TestCalcularAtingimento:
    """Testes da função utilitária de atingimento de meta."""

    def test_atingimento_normal(self, audit):
        """100k realizado / 200k meta = 0.5 (50%)."""
        audit.set_contexto(modulo="FC Componentes", cenario="Atingimento normal")
        resultado = calcular_atingimento(100_000, 200_000)

        audit.verificar(
            descricao="100k / 200k = 50%",
            formula="atingimento = realizado / meta = 100000 / 200000",
            entradas={"realizado": 100_000, "meta": 200_000},
            esperado=0.5,
            real=resultado,
            tolerancia=0.0001,
        )

    def test_atingimento_100pct(self, audit):
        """200k realizado / 200k meta = 1.0 (100%)."""
        audit.set_contexto(modulo="FC Componentes", cenario="Atingimento 100%")
        resultado = calcular_atingimento(200_000, 200_000)

        audit.verificar(
            descricao="200k / 200k = 100%",
            formula="atingimento = 200000 / 200000",
            entradas={"realizado": 200_000, "meta": 200_000},
            esperado=1.0,
            real=resultado,
            tolerancia=0.0001,
        )

    def test_atingimento_acima_100(self, audit):
        """300k realizado / 200k meta = 1.5 (150%)."""
        audit.set_contexto(modulo="FC Componentes", cenario="Atingimento >100%")
        resultado = calcular_atingimento(300_000, 200_000)

        audit.verificar(
            descricao="300k / 200k = 150% (sem cap, o cap é aplicado depois)",
            formula="atingimento = 300000 / 200000",
            entradas={"realizado": 300_000, "meta": 200_000},
            esperado=1.5,
            real=resultado,
            tolerancia=0.0001,
        )

    def test_meta_zero_realizado_positivo(self, audit):
        """Meta=0, Realizado>0 → 1.0 (superou a meta inexistente)."""
        audit.set_contexto(modulo="FC Componentes", cenario="Meta zero com realizado")
        resultado = calcular_atingimento(50_000, 0)

        audit.verificar(
            descricao="Meta=0, Realizado>0 → retorna 1.0",
            formula="se meta==0 e realizado>0 → 1.0",
            entradas={"realizado": 50_000, "meta": 0},
            esperado=1.0,
            real=resultado,
            tolerancia=0.0001,
        )

    def test_meta_zero_realizado_zero(self, audit):
        """Meta=0, Realizado=0 → 0.0."""
        audit.set_contexto(modulo="FC Componentes", cenario="Meta e realizado zero")
        resultado = calcular_atingimento(0, 0)

        audit.verificar(
            descricao="Meta=0, Realizado=0 → retorna 0.0",
            formula="se meta==0 e realizado==0 → 0.0",
            entradas={"realizado": 0, "meta": 0},
            esperado=0.0,
            real=resultado,
            tolerancia=0.0001,
        )

    def test_realizado_none(self, audit):
        """Realizado=None → tratado como 0."""
        audit.set_contexto(modulo="FC Componentes", cenario="Realizado None")
        resultado = calcular_atingimento(None, 100_000)

        audit.verificar(
            descricao="Realizado=None → 0 / 100000 = 0.0",
            formula="realizado=None → 0.0; atingimento = 0/100000",
            entradas={"realizado": None, "meta": 100_000},
            esperado=0.0,
            real=resultado,
            tolerancia=0.0001,
        )

    def test_meta_none(self, audit):
        """Meta=None → tratado como 0 → mesma regra de meta=0."""
        audit.set_contexto(modulo="FC Componentes", cenario="Meta None")
        resultado = calcular_atingimento(50_000, None)

        audit.verificar(
            descricao="Meta=None → meta=0 → realizado>0 → 1.0",
            formula="meta=None → 0.0; realizado>0 → 1.0",
            entradas={"realizado": 50_000, "meta": None},
            esperado=1.0,
            real=resultado,
            tolerancia=0.0001,
        )


# =========================================================================
# TESTES: Capping de atingimento e FC
# =========================================================================
class TestCappingFC:
    """Testes do capping individual e total do FC.

    Simula o que _calcular_fc_para_item faz internamente.
    """

    @staticmethod
    def _calcular_fc_simulado(
        componentes: dict,
        pesos: dict,
        cap_atingimento: float = 1.0,
        cap_fc_max: float = 1.0,
    ) -> dict:
        """Simula o cálculo do FC como faz _calcular_fc_para_item.

        Args:
            componentes: {nome: {"realizado": X, "meta": Y}}
            pesos: {nome: peso_decimal}
            cap_atingimento: cap por componente
            cap_fc_max: cap do FC total

        Returns:
            dict com fc_total, fc_final e detalhes por componente
        """
        detalhes = {}
        fc_total = 0.0

        for nome, dados in componentes.items():
            peso = pesos.get(nome, 0.0)
            if peso == 0:
                continue

            atingimento = calcular_atingimento(dados["realizado"], dados["meta"])
            ating_cap = min(atingimento, cap_atingimento)
            contrib = ating_cap * peso
            fc_total += contrib

            detalhes[nome] = {
                "realizado": dados["realizado"],
                "meta": dados["meta"],
                "atingimento_bruto": atingimento,
                "atingimento_cap": ating_cap,
                "peso": peso,
                "contribuicao": contrib,
            }

        fc_final = min(fc_total, cap_fc_max)
        return {
            "fc_total": fc_total,
            "fc_final": fc_final,
            "detalhes": detalhes,
        }

    def test_fc_completo_abaixo_cap(self, audit):
        """FC com 3 componentes, todos abaixo do cap → soma direta."""
        audit.set_contexto(modulo="FC Componentes", cenario="FC abaixo do cap")

        componentes = {
            "faturamento_linha": {"realizado": 400_000, "meta": 500_000},  # 80%
            "conversao_linha": {"realizado": 180_000, "meta": 300_000},    # 60%
            "rentabilidade": {"realizado": 0.10, "meta": 0.12},           # 83.3%
        }
        pesos = {
            "faturamento_linha": 0.30,
            "conversao_linha": 0.20,
            "rentabilidade": 0.25,
        }

        resultado = self._calcular_fc_simulado(componentes, pesos, cap_atingimento=1.0)

        # FC = (0.80 × 0.30) + (0.60 × 0.20) + (0.8333 × 0.25)
        #    = 0.240 + 0.120 + 0.2083
        #    = 0.5683
        audit.verificar(
            descricao="FC com 3 componentes parciais",
            formula="(0.80×0.30)+(0.60×0.20)+(0.833×0.25) = 0.568",
            entradas={
                "fat_linha": "400k/500k=80%",
                "conv_linha": "180k/300k=60%",
                "rentab": "10%/12%=83.3%",
            },
            esperado=0.5683,
            real=resultado["fc_final"],
            tolerancia=0.01,
        )

    def test_fc_com_cap_atingimento(self, audit):
        """Componente com atingimento >100% é capado antes de pesar."""
        audit.set_contexto(modulo="FC Componentes", cenario="Cap atingimento individual")

        componentes = {
            "faturamento_linha": {"realizado": 700_000, "meta": 500_000},  # 140% → cap 100%
            "conversao_linha": {"realizado": 300_000, "meta": 300_000},    # 100%
        }
        pesos = {
            "faturamento_linha": 0.50,
            "conversao_linha": 0.50,
        }

        resultado = self._calcular_fc_simulado(componentes, pesos, cap_atingimento=1.0)

        # fat_linha: 140% → cap 100%
        # FC = (1.0 × 0.50) + (1.0 × 0.50) = 1.0
        audit.verificar(
            descricao="Atingimento 140% capado em 100% antes de multiplicar pelo peso",
            formula="min(140%, 100%)×0.50 + min(100%, 100%)×0.50 = 1.0",
            entradas={
                "fat_linha_bruto": "700k/500k=140%",
                "cap_atingimento": 1.0,
            },
            esperado=1.0,
            real=resultado["fc_final"],
            tolerancia=0.01,
        )

        # Verificar que o atingimento bruto é > 1 mas o capado é 1
        detalhe = resultado["detalhes"]["faturamento_linha"]
        audit.verificar(
            descricao="Atingimento bruto preservado (1.4) mas capado usado (1.0)",
            formula="ating_bruto=1.4, ating_cap=min(1.4, 1.0)=1.0",
            entradas={"ating_bruto": detalhe["atingimento_bruto"]},
            esperado=1.0,
            real=detalhe["atingimento_cap"],
            tolerancia=0.001,
        )

    def test_fc_com_cap_fc_max(self, audit):
        """FC total > cap_fc_max é capado no final."""
        audit.set_contexto(modulo="FC Componentes", cenario="Cap FC total")

        componentes = {
            "faturamento_linha": {"realizado": 500_000, "meta": 500_000},
            "conversao_linha": {"realizado": 300_000, "meta": 300_000},
        }
        pesos = {
            "faturamento_linha": 0.60,
            "conversao_linha": 0.60,  # Soma > 100% de propósito para testar cap
        }

        resultado = self._calcular_fc_simulado(
            componentes, pesos, cap_atingimento=1.0, cap_fc_max=1.0,
        )

        # FC_total = (1.0 × 0.60) + (1.0 × 0.60) = 1.2
        # FC_final = min(1.2, 1.0) = 1.0
        audit.verificar(
            descricao="FC total 1.2 capado em 1.0 pelo cap_fc_max",
            formula="FC_total = 1.2; FC_final = min(1.2, 1.0) = 1.0",
            entradas={"fc_total": resultado["fc_total"], "cap_fc_max": 1.0},
            esperado=1.0,
            real=resultado["fc_final"],
            tolerancia=0.001,
        )

    def test_fc_componente_peso_zero_ignorado(self, audit):
        """Componente com peso=0 não deve contribuir para o FC."""
        audit.set_contexto(modulo="FC Componentes", cenario="Peso zero ignorado")

        componentes = {
            "faturamento_linha": {"realizado": 500_000, "meta": 500_000},
            "retencao_clientes": {"realizado": 0.9, "meta": 1.0},
        }
        pesos = {
            "faturamento_linha": 0.50,
            "retencao_clientes": 0.0,  # Peso zero
        }

        resultado = self._calcular_fc_simulado(componentes, pesos)

        # FC = (1.0 × 0.50) + (ignorado) = 0.50
        audit.verificar(
            descricao="Componente com peso=0 não contribui para FC",
            formula="(1.0×0.50) + (peso=0 ignorado) = 0.50",
            entradas={"retencao_peso": 0.0},
            esperado=0.50,
            real=resultado["fc_final"],
            tolerancia=0.001,
        )

    def test_fc_todos_zero(self, audit):
        """Todos os realizados = 0 → FC = 0."""
        audit.set_contexto(modulo="FC Componentes", cenario="Tudo zero")

        componentes = {
            "faturamento_linha": {"realizado": 0, "meta": 500_000},
            "conversao_linha": {"realizado": 0, "meta": 300_000},
        }
        pesos = {
            "faturamento_linha": 0.50,
            "conversao_linha": 0.50,
        }

        resultado = self._calcular_fc_simulado(componentes, pesos)

        audit.verificar(
            descricao="Realizado=0 para tudo → FC=0",
            formula="(0/500k×0.50) + (0/300k×0.50) = 0.00",
            entradas={"fat_realizado": 0, "conv_realizado": 0},
            esperado=0.0,
            real=resultado["fc_final"],
            tolerancia=0.001,
        )

    def test_fc_cap_atingimento_personalizado(self, audit):
        """Cap de atingimento = 1.5 permite atingimento acima de 100%."""
        audit.set_contexto(modulo="FC Componentes", cenario="Cap atingimento 150%")

        componentes = {
            "faturamento_linha": {"realizado": 600_000, "meta": 500_000},  # 120%
        }
        pesos = {
            "faturamento_linha": 1.0,
        }

        resultado = self._calcular_fc_simulado(
            componentes, pesos, cap_atingimento=1.5, cap_fc_max=1.5,
        )

        # Atingimento = 120%, cap = 150% → usa 120%
        # FC = 1.20 × 1.0 = 1.20
        audit.verificar(
            descricao="Cap 150% permite atingimento 120% passar",
            formula="min(120%, 150%)=120%; FC=1.20×1.0=1.20",
            entradas={"atingimento": 1.20, "cap": 1.5},
            esperado=1.20,
            real=resultado["fc_final"],
            tolerancia=0.001,
        )

    def test_fc_cenario_realista_gerente_linha(self, audit):
        """Cenário realista: Gerente Linha com todos os componentes aplicáveis."""
        audit.set_contexto(modulo="FC Componentes", cenario="Gerente Linha realista")

        componentes = {
            "faturamento_linha": {"realizado": 400_000, "meta": 500_000},     # 80%
            "conversao_linha": {"realizado": 270_000, "meta": 300_000},       # 90%
            "rentabilidade": {"realizado": 0.108, "meta": 0.12},              # 90%
            "retencao_clientes": {"realizado": 45, "meta": 50},               # 90% (clientes)
            "meta_fornecedor_1": {"realizado": 160_000, "meta": 200_000},     # 80%
            "meta_fornecedor_2": {"realizado": 60_000, "meta": 80_000},       # 75%
        }
        pesos = {
            "faturamento_linha": 0.30,
            "conversao_linha": 0.20,
            "faturamento_individual": 0.0,
            "conversao_individual": 0.0,
            "rentabilidade": 0.25,
            "retencao_clientes": 0.10,
            "meta_fornecedor_1": 0.10,
            "meta_fornecedor_2": 0.05,
        }

        resultado = self._calcular_fc_simulado(componentes, pesos)

        # FC = (0.80×0.30) + (0.90×0.20) + (0.90×0.25) + (0.90×0.10) + (0.80×0.10) + (0.75×0.05)
        #    = 0.240 + 0.180 + 0.225 + 0.090 + 0.080 + 0.0375
        #    = 0.8525
        audit.verificar(
            descricao="Gerente Linha: FC realista com 6 componentes",
            formula=(
                "(0.80×0.30)+(0.90×0.20)+(0.90×0.25)+(0.90×0.10)"
                "+(0.80×0.10)+(0.75×0.05) = 0.8525"
            ),
            entradas={
                "fat_linha": "400k/500k=80%", "conv_linha": "270k/300k=90%",
                "rentab": "10.8%/12%=90%", "retencao": "45/50=90%",
                "fornecedor1": "160k/200k=80%", "fornecedor2": "60k/80k=75%",
            },
            esperado=0.8525,
            real=resultado["fc_final"],
            tolerancia=0.01,
        )

    def test_fc_cenario_realista_consultor_interno(self, audit):
        """Cenário realista: Consultor Interno com componentes individuais."""
        audit.set_contexto(modulo="FC Componentes", cenario="Consultor Interno realista")

        componentes = {
            "faturamento_linha": {"realizado": 450_000, "meta": 500_000},       # 90%
            "conversao_linha": {"realizado": 300_000, "meta": 300_000},         # 100%
            "faturamento_individual": {"realizado": 90_000, "meta": 100_000},   # 90%
            "conversao_individual": {"realizado": 72_000, "meta": 80_000},      # 90%
            "rentabilidade": {"realizado": 0.12, "meta": 0.12},                 # 100%
            "meta_fornecedor_1": {"realizado": 180_000, "meta": 200_000},       # 90%
            "meta_fornecedor_2": {"realizado": 50_000, "meta": 80_000},         # 62.5%
        }
        pesos = {
            "faturamento_linha": 0.15,
            "conversao_linha": 0.10,
            "faturamento_individual": 0.25,
            "conversao_individual": 0.15,
            "rentabilidade": 0.20,
            "retencao_clientes": 0.0,
            "meta_fornecedor_1": 0.10,
            "meta_fornecedor_2": 0.05,
        }

        resultado = self._calcular_fc_simulado(componentes, pesos)

        # FC = (0.90×0.15) + (1.0×0.10) + (0.90×0.25) + (0.90×0.15)
        #    + (1.0×0.20) + (0.90×0.10) + (0.625×0.05)
        #    = 0.135 + 0.10 + 0.225 + 0.135 + 0.20 + 0.09 + 0.03125
        #    = 0.91625
        audit.verificar(
            descricao="Consultor Interno: FC com componentes individuais",
            formula=(
                "(0.90×0.15)+(1.0×0.10)+(0.90×0.25)+(0.90×0.15)"
                "+(1.0×0.20)+(0.90×0.10)+(0.625×0.05) = 0.916"
            ),
            entradas={
                "fat_linha": "90%", "conv_linha": "100%",
                "fat_ind": "90%", "conv_ind": "90%",
                "rentab": "100%", "forn1": "90%", "forn2": "62.5%",
            },
            esperado=0.91625,
            real=resultado["fc_final"],
            tolerancia=0.01,
        )
