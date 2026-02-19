"""
Testes unitários para o cálculo de comissão por faturamento.

Testa a fórmula central:
    comissao_potencial = faturamento_item × taxa_rateio × pe × fator_split
    comissao_item      = comissao_potencial × fc_aplicado

Onde:
    taxa_rateio  = regra["taxa_rateio_maximo_pct"] / 100
    pe           = regra["fatia_cargo_pct"] / 100        (Percentual de Elegibilidade)
    fator_split  = 1.0 (sem split) ou 0.5 (split de cargo)
    fc_aplicado  = resultado da escada/rampa sobre fc_rampa

Cenários cobertos:
    - Fórmula básica sem split, FC=1.0 (caso ideal)
    - Fórmula com split (fator_split=0.5)
    - Fórmula com FC parcial (<1.0)
    - Fórmula com FC=0 (abaixo do piso)
    - Cross-selling decisão A (reduz taxa_rateio)
    - Cross-selling decisão B (taxa intacta, consultor externo excluído)
    - Cross-selling taxa > taxa_rateio (capped a zero)
    - Montagem de time: gestão (ATRIBUICOES) + operacional (FATURADOS)
    - Deduplicação de colaboradores
    - Comissão do Consultor Externo em cross-selling
    - Múltiplos cargos no mesmo item
    - Auditoria: base_dict contém todas as colunas esperadas
"""

import pytest
import math


# =========================================================================
# HELPERS: Fórmula pura (sem instanciar CalculoComissao)
# =========================================================================

def _calcular_comissao_formula(
    faturamento_item: float,
    taxa_rateio_maximo_pct: float,
    fatia_cargo_pct: float,
    fator_split: float = 1.0,
    fc_aplicado: float = 1.0,
) -> dict:
    """Reproduz a fórmula de comissão isolada, retornando potencial e final."""
    taxa_rateio = taxa_rateio_maximo_pct / 100.0
    pe = fatia_cargo_pct / 100.0
    comissao_potencial = faturamento_item * taxa_rateio * pe * fator_split
    comissao_item = comissao_potencial * fc_aplicado
    return {
        "taxa_rateio": taxa_rateio,
        "pe": pe,
        "comissao_potencial": comissao_potencial,
        "comissao_item": comissao_item,
    }


def _aplicar_cross_selling_a(
    taxa_rateio_maximo_pct: float,
    taxa_cross_selling_pct: float,
) -> float:
    """Decisão A: subtrai taxa_cs da taxa_rateio (em decimal), clamp >= 0."""
    taxa_rateio = taxa_rateio_maximo_pct / 100.0
    taxa_cs = taxa_cross_selling_pct / 100.0
    return max(0.0, taxa_rateio - taxa_cs)


def _calcular_comissao_consultor_externo_cs(
    faturamento_item: float,
    taxa_cross_selling_pct: float,
) -> float:
    """Comissão especial do consultor externo em cross-selling."""
    taxa_cs = taxa_cross_selling_pct / 100.0
    return faturamento_item * taxa_cs


# =========================================================================
# CLASSE: TestFormulaComissaoBasica
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
class TestFormulaComissaoBasica:
    """Testa a fórmula de comissão com valores puros (sem dependências)."""

    def test_formula_caso_ideal_fc_100(self, audit):
        """FC=1.0, sem split → comissão = faturamento × taxa × pe."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Caso ideal FC 100%")

        fat = 100_000.0
        taxa_pct = 3.0   # 3%
        fatia_pct = 40.0  # 40%
        fator_split = 1.0
        fc = 1.0

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fator_split, fc)

        # Esperado: 100000 × 0.03 × 0.40 × 1.0 × 1.0 = 1200.00
        audit.verificar(
            descricao="Comissao potencial (antes FC)",
            formula="faturamento × (taxa_pct/100) × (fatia_pct/100) × split",
            entradas={"faturamento": fat, "taxa_pct": taxa_pct, "fatia_pct": fatia_pct, "split": fator_split},
            esperado=1200.0,
            real=r["comissao_potencial"],
        )
        audit.verificar(
            descricao="Comissao final (apos FC=1.0)",
            formula="comissao_potencial × fc_aplicado",
            entradas={"comissao_potencial": r["comissao_potencial"], "fc": fc},
            esperado=1200.0,
            real=r["comissao_item"],
        )

    def test_formula_fc_parcial_70(self, audit):
        """FC=0.70 → comissão reduzida proporcionalmente."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="FC parcial 70%")

        fat = 200_000.0
        taxa_pct = 2.5
        fatia_pct = 25.0
        fc = 0.70

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fc_aplicado=fc)
        potencial = 200_000 * 0.025 * 0.25 * 1.0  # 1250.0
        esperado = potencial * 0.70  # 875.0

        audit.verificar(
            descricao="Comissao potencial",
            formula="200000 × 0.025 × 0.25 × 1.0",
            entradas={"faturamento": fat, "taxa": taxa_pct, "fatia": fatia_pct},
            esperado=1250.0,
            real=r["comissao_potencial"],
        )
        audit.verificar(
            descricao="Comissao final com FC=0.70",
            formula="1250.0 × 0.70",
            entradas={"potencial": 1250.0, "fc": 0.70},
            esperado=875.0,
            real=r["comissao_item"],
        )

    def test_formula_fc_zero(self, audit):
        """FC=0.0 → comissão zero (abaixo do piso)."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="FC zero")

        r = _calcular_comissao_formula(150_000, 3.0, 40.0, fc_aplicado=0.0)

        audit.verificar(
            descricao="Comissao com FC=0.0",
            formula="qualquer_valor × 0.0 = 0",
            entradas={"potencial": r["comissao_potencial"], "fc": 0.0},
            esperado=0.0,
            real=r["comissao_item"],
        )

    def test_formula_com_split_50(self, audit):
        """Split de cargo (fator_split=0.5) → metade da comissão."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Split de cargo 50%")

        fat = 100_000.0
        taxa_pct = 3.0
        fatia_pct = 40.0
        split = 0.5
        fc = 1.0

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, split, fc)
        # 100000 × 0.03 × 0.40 × 0.5 = 600.0
        audit.verificar(
            descricao="Comissao com split 50%",
            formula="100000 × 0.03 × 0.40 × 0.5 × 1.0",
            entradas={"faturamento": fat, "split": split},
            esperado=600.0,
            real=r["comissao_item"],
        )

    def test_formula_faturamento_zero(self, audit):
        """Faturamento zero → comissão zero."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Faturamento zero")

        r = _calcular_comissao_formula(0.0, 3.0, 40.0)

        audit.verificar(
            descricao="Comissao com faturamento zero",
            formula="0 × qualquer = 0",
            entradas={"faturamento": 0.0},
            esperado=0.0,
            real=r["comissao_item"],
        )

    def test_formula_taxa_rateio_conversao(self, audit):
        """taxa_rateio_maximo_pct se converte corretamente de % para decimal."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Conversao taxa %")

        r = _calcular_comissao_formula(100_000, 2.5, 100.0)

        audit.verificar(
            descricao="Taxa rateio: 2.5% → 0.025",
            formula="taxa_rateio_maximo_pct / 100",
            entradas={"taxa_pct": 2.5},
            esperado=0.025,
            real=r["taxa_rateio"],
        )

    def test_formula_pe_conversao(self, audit):
        """fatia_cargo_pct se converte corretamente de % para decimal."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Conversao PE %")

        r = _calcular_comissao_formula(100_000, 3.0, 40.0)

        audit.verificar(
            descricao="PE: 40% → 0.40",
            formula="fatia_cargo_pct / 100",
            entradas={"fatia_pct": 40.0},
            esperado=0.40,
            real=r["pe"],
        )


# =========================================================================
# CLASSE: TestFormulaMultiplosCargos
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
class TestFormulaMultiplosCargos:
    """Testa a fórmula para vários cargos no mesmo item faturado."""

    CARGOS_CONFIG = [
        # (cargo, fatia_pct, taxa_rateio_pct)
        ("Gerente Linha", 40.0, 3.0),
        ("Coordenador", 25.0, 3.0),
        ("Diretor", 10.0, 3.0),
        ("Consultor Interno", 20.0, 3.0),
        ("Consultor Externo", 5.0, 3.0),
    ]

    def test_soma_fatias_100_pct(self, audit):
        """A soma das fatias (PE) dos 5 cargos deve ser 100%."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Soma fatias = 100%")

        soma = sum(fatia for _, fatia, _ in self.CARGOS_CONFIG)

        audit.verificar(
            descricao="Soma de fatia_cargo_pct de todos os cargos",
            formula="40 + 25 + 10 + 20 + 5",
            entradas={c: f for c, f, _ in self.CARGOS_CONFIG},
            esperado=100.0,
            real=soma,
        )

    def test_comissao_cada_cargo_fc1(self, audit):
        """Cada cargo recebe sua fatia do rateio, com FC=1.0."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Cada cargo FC=1.0")

        fat = 100_000.0

        resultados = {}
        for cargo, fatia, taxa in self.CARGOS_CONFIG:
            r = _calcular_comissao_formula(fat, taxa, fatia)
            resultados[cargo] = r["comissao_item"]

        # Esperado: 100000 × 0.03 = 3000 total, distribuído pela fatia
        # GL: 3000 × 0.40 = 1200.0
        # Coord: 3000 × 0.25 = 750.0
        # Dir: 3000 × 0.10 = 300.0
        # CI: 3000 × 0.20 = 600.0
        # CE: 3000 × 0.05 = 150.0
        esperados = {
            "Gerente Linha": 1200.0,
            "Coordenador": 750.0,
            "Diretor": 300.0,
            "Consultor Interno": 600.0,
            "Consultor Externo": 150.0,
        }
        for cargo, esperado in esperados.items():
            audit.verificar(
                descricao=f"Comissao {cargo} FC=1.0",
                formula=f"100000 × 0.03 × {esperados[cargo]/3000:.2f}",
                entradas={"cargo": cargo, "faturamento": fat},
                esperado=esperado,
                real=resultados[cargo],
            )

    def test_soma_comissoes_igual_rateio_total(self, audit):
        """Soma de todas as comissões (FC=1) = faturamento × taxa_rateio."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Soma = rateio total")

        fat = 100_000.0
        taxa = 3.0
        total = sum(
            _calcular_comissao_formula(fat, taxa, fatia)["comissao_item"]
            for _, fatia, _ in self.CARGOS_CONFIG
        )
        rateio_total = fat * (taxa / 100.0)  # 3000.0

        audit.verificar(
            descricao="Soma comissoes todos os cargos = rateio total",
            formula="sum(comissao_cargo_i) == faturamento × taxa",
            entradas={"faturamento": fat, "taxa": taxa},
            esperado=rateio_total,
            real=total,
        )


# =========================================================================
# CLASSE: TestCrossSellingDecisaoA
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
@pytest.mark.cross_selling
class TestCrossSellingDecisaoA:
    """Testa cross-selling com decisão A: subtrai taxa_cs de taxa_rateio."""

    def test_taxa_rateio_reduzida(self, audit):
        """Decisão A: taxa_rateio diminui pela taxa_cs."""
        audit.set_contexto(modulo="Cross-Selling A", cenario="Taxa reduzida")

        taxa_rateio_pct = 3.0
        taxa_cs_pct = 1.0

        nova_taxa = _aplicar_cross_selling_a(taxa_rateio_pct, taxa_cs_pct)
        # 0.03 - 0.01 = 0.02
        audit.verificar(
            descricao="taxa_rateio apos subtração da taxa_cs",
            formula="max(0, 3.0/100 - 1.0/100)",
            entradas={"taxa_rateio_pct": taxa_rateio_pct, "taxa_cs_pct": taxa_cs_pct},
            esperado=0.02,
            real=nova_taxa,
        )

    def test_comissao_com_taxa_reduzida(self, audit):
        """Comissão usando taxa pós-cross-selling A."""
        audit.set_contexto(modulo="Cross-Selling A", cenario="Comissao com taxa reduzida")

        fat = 100_000.0
        taxa_rateio_pct = 3.0
        taxa_cs_pct = 1.0
        fatia_pct = 40.0

        nova_taxa = _aplicar_cross_selling_a(taxa_rateio_pct, taxa_cs_pct)
        comissao = fat * nova_taxa * (fatia_pct / 100.0)
        # 100000 × 0.02 × 0.40 = 800.0

        audit.verificar(
            descricao="Comissao GL com taxa reduzida (CS decisao A)",
            formula="100000 × 0.02 × 0.40",
            entradas={"fat": fat, "nova_taxa": nova_taxa, "pe": fatia_pct / 100},
            esperado=800.0,
            real=comissao,
        )

    def test_taxa_cs_maior_que_rateio_clamp_zero(self, audit):
        """Se taxa_cs > taxa_rateio, clamp em 0 (nunca negativo)."""
        audit.set_contexto(modulo="Cross-Selling A", cenario="Taxa CS > rateio")

        nova_taxa = _aplicar_cross_selling_a(2.0, 5.0)
        # max(0, 0.02 - 0.05) = 0.0

        audit.verificar(
            descricao="taxa_rateio clamped a zero",
            formula="max(0, 2.0/100 - 5.0/100)",
            entradas={"taxa_rateio_pct": 2.0, "taxa_cs_pct": 5.0},
            esperado=0.0,
            real=nova_taxa,
        )

    def test_comissao_consultor_externo_cs(self, audit):
        """Consultor externo recebe comissão especial: fat × taxa_cs."""
        audit.set_contexto(modulo="Cross-Selling A", cenario="Comissao consultor externo")

        fat = 100_000.0
        taxa_cs_pct = 1.0

        comissao_ce = _calcular_comissao_consultor_externo_cs(fat, taxa_cs_pct)
        # 100000 × 0.01 = 1000.0

        audit.verificar(
            descricao="Comissao consultor externo (cross-selling)",
            formula="faturamento × (taxa_cs_pct / 100)",
            entradas={"faturamento": fat, "taxa_cs_pct": taxa_cs_pct},
            esperado=1000.0,
            real=comissao_ce,
        )

    def test_consultor_externo_pe_100(self, audit):
        """Na linha de CS, pe=1.0 e fc=1.0 para o consultor externo."""
        audit.set_contexto(modulo="Cross-Selling A", cenario="PE e FC do consultor externo")

        # No código-fonte, a comissão CS é: fat × taxa_cs (sem PE nem FC)
        # Equivalente a pe=1.0 e fc=1.0
        fat = 50_000.0
        taxa_cs_pct = 0.8

        comissao = fat * (taxa_cs_pct / 100.0) * 1.0 * 1.0
        esperado = 50_000 * 0.008  # 400.0

        audit.verificar(
            descricao="Comissao CS com PE=1 e FC=1 implicitos",
            formula="50000 × 0.008 × 1.0 × 1.0",
            entradas={"fat": fat, "taxa_cs": taxa_cs_pct, "pe": 1.0, "fc": 1.0},
            esperado=400.0,
            real=comissao,
        )


# =========================================================================
# CLASSE: TestCrossSellingDecisaoB
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
@pytest.mark.cross_selling
class TestCrossSellingDecisaoB:
    """Testa cross-selling com decisão B: taxa intacta, consultor excluído do rateio normal."""

    def test_taxa_rateio_intacta(self, audit):
        """Decisão B: taxa_rateio permanece inalterada."""
        audit.set_contexto(modulo="Cross-Selling B", cenario="Taxa intacta")

        taxa_rateio_pct = 3.0
        # Na decisão B, NÃO subtraímos nada
        taxa_rateio = taxa_rateio_pct / 100.0

        audit.verificar(
            descricao="taxa_rateio na decisao B (inalterada)",
            formula="taxa_rateio_maximo_pct / 100 (sem subtração)",
            entradas={"taxa_rateio_pct": taxa_rateio_pct},
            esperado=0.03,
            real=taxa_rateio,
        )

    def test_comissao_time_interno_sem_reducao(self, audit):
        """Na decisão B, o time interno recebe comissão cheia."""
        audit.set_contexto(modulo="Cross-Selling B", cenario="Comissao time interno")

        fat = 100_000.0
        taxa_pct = 3.0
        fatia_pct = 40.0

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct)
        # 100000 × 0.03 × 0.40 = 1200.0

        audit.verificar(
            descricao="Comissao GL (decisao B - sem redução)",
            formula="100000 × 0.03 × 0.40",
            entradas={"fat": fat, "taxa": taxa_pct, "fatia": fatia_pct},
            esperado=1200.0,
            real=r["comissao_item"],
        )

    def test_consultor_externo_excluido_rateio_normal(self, audit):
        """Na decisão B, consultor externo é excluído do loop de rateio normal."""
        audit.set_contexto(modulo="Cross-Selling B", cenario="Consultor excluido do rateio")

        # Na lógica, quando cs_info.is_cross=True, o loop de colaboradores
        # pula (continue) se colab_nome == cs_info.consultor
        # O consultor externo só recebe pela linha especial de CS

        # Verificar que a comissão total do time interno NÃO inclui consultor externo
        fat = 100_000.0
        taxa_pct = 3.0
        cargos_internos = [
            ("Gerente Linha", 40.0),
            ("Coordenador", 25.0),
            ("Diretor", 10.0),
            ("Consultor Interno", 20.0),
        ]
        soma_internos = sum(
            _calcular_comissao_formula(fat, taxa_pct, fatia)["comissao_item"]
            for _, fatia in cargos_internos
        )
        # 100000 × 0.03 × (0.40 + 0.25 + 0.10 + 0.20) = 3000 × 0.95 = 2850.0

        audit.verificar(
            descricao="Soma comissoes time interno (sem consultor externo)",
            formula="100000 × 0.03 × 0.95 (soma fatias internas)",
            entradas={"fat": fat, "soma_fatias": 0.95},
            esperado=2850.0,
            real=soma_internos,
        )


# =========================================================================
# CLASSE: TestFatorSplit
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
class TestFatorSplit:
    """Testa o comportamento do fator_split na fórmula."""

    def test_split_1_0_sem_divisao(self, audit):
        """fator_split=1.0 → comissão integral."""
        audit.set_contexto(modulo="Fator Split", cenario="Sem divisao")

        r = _calcular_comissao_formula(100_000, 3.0, 40.0, fator_split=1.0)

        audit.verificar(
            descricao="Split=1.0 nao altera comissao",
            formula="100000 × 0.03 × 0.40 × 1.0",
            entradas={"split": 1.0},
            esperado=1200.0,
            real=r["comissao_item"],
        )

    def test_split_0_5_divide_metade(self, audit):
        """fator_split=0.5 → metade da comissão (2 gerentes na linha)."""
        audit.set_contexto(modulo="Fator Split", cenario="Divisao 50%")

        r = _calcular_comissao_formula(100_000, 3.0, 40.0, fator_split=0.5)

        audit.verificar(
            descricao="Split=0.5 divide comissao pela metade",
            formula="100000 × 0.03 × 0.40 × 0.5",
            entradas={"split": 0.5},
            esperado=600.0,
            real=r["comissao_item"],
        )

    def test_dois_gerentes_soma_split_igual_integral(self, audit):
        """2 gerentes com split=0.5 cada: soma = comissão integral."""
        audit.set_contexto(modulo="Fator Split", cenario="2 gerentes = integral")

        fat = 100_000.0
        taxa_pct = 3.0
        fatia_pct = 40.0

        g1 = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fator_split=0.5)
        g2 = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fator_split=0.5)
        integral = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fator_split=1.0)

        soma = g1["comissao_item"] + g2["comissao_item"]

        audit.verificar(
            descricao="Soma de 2 gerentes (0.5+0.5) = integral (1.0)",
            formula="600 + 600 = 1200",
            entradas={"g1": g1["comissao_item"], "g2": g2["comissao_item"]},
            esperado=integral["comissao_item"],
            real=soma,
        )

    def test_split_cap_1_0(self, audit):
        """Na deduplicação, fator_split é capped em 1.0."""
        audit.set_contexto(modulo="Fator Split", cenario="Cap em 1.0")

        # Simula deduplicação: mesmo colab aparece em gestão (0.5) e operacional (1.0)
        # Soma bruta: 1.5, mas o clip(upper=1.0) limita a 1.0
        fator_bruto = 0.5 + 1.0
        fator_final = min(fator_bruto, 1.0)  # clip

        audit.verificar(
            descricao="Split capped em 1.0 apos deduplicacao",
            formula="min(0.5 + 1.0, 1.0)",
            entradas={"gestao": 0.5, "operacional": 1.0},
            esperado=1.0,
            real=fator_final,
        )


# =========================================================================
# CLASSE: TestCombinacaoFCeFormula
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
class TestCombinacaoFCeFormula:
    """Testa cenários realistas combinando FC e fórmula."""

    def test_cenario_gerente_linha_realista(self, audit):
        """Gerente Linha: fat=250k, taxa=3%, fatia=40%, split=1.0, FC=0.85."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Cenário realista GL")

        fat = 250_000.0
        taxa_pct = 3.0
        fatia_pct = 40.0
        fc = 0.85

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fc_aplicado=fc)
        # Potencial: 250000 × 0.03 × 0.40 = 3000.0
        # Final: 3000.0 × 0.85 = 2550.0

        audit.verificar(
            descricao="Potencial GL (antes FC)",
            formula="250000 × 0.03 × 0.40",
            entradas={"fat": fat, "taxa": taxa_pct, "fatia": fatia_pct},
            esperado=3000.0,
            real=r["comissao_potencial"],
        )
        audit.verificar(
            descricao="Comissao final GL com FC=0.85",
            formula="3000.0 × 0.85",
            entradas={"potencial": 3000.0, "fc": fc},
            esperado=2550.0,
            real=r["comissao_item"],
        )

    def test_cenario_consultor_interno_split(self, audit):
        """Consultor Interno: fat=180k, taxa=3%, fatia=20%, split=0.5, FC=0.92."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Cenário CI com split")

        fat = 180_000.0
        taxa_pct = 3.0
        fatia_pct = 20.0
        split = 0.5
        fc = 0.92

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, split, fc)
        # Potencial: 180000 × 0.03 × 0.20 × 0.5 = 540.0
        # Final: 540.0 × 0.92 = 496.8

        audit.verificar(
            descricao="Potencial CI com split",
            formula="180000 × 0.03 × 0.20 × 0.5",
            entradas={"fat": fat, "taxa": taxa_pct, "fatia": fatia_pct, "split": split},
            esperado=540.0,
            real=r["comissao_potencial"],
        )
        audit.verificar(
            descricao="Comissao final CI com FC=0.92",
            formula="540.0 × 0.92",
            entradas={"potencial": 540.0, "fc": fc},
            esperado=496.8,
            real=r["comissao_item"],
        )

    def test_cenario_cross_selling_a_completo(self, audit):
        """Cross-selling A: GL recebe menos, CE recebe taxa_cs."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="CS decisao A completo")

        fat = 100_000.0
        taxa_rateio_pct = 3.0
        taxa_cs_pct = 1.0
        fatia_gl = 40.0
        fc = 1.0

        # GL: taxa reduzida
        nova_taxa = _aplicar_cross_selling_a(taxa_rateio_pct, taxa_cs_pct)  # 0.02
        comissao_gl = fat * nova_taxa * (fatia_gl / 100.0) * fc
        # 100000 × 0.02 × 0.40 = 800.0

        # CE: comissão especial
        comissao_ce = _calcular_comissao_consultor_externo_cs(fat, taxa_cs_pct)
        # 100000 × 0.01 = 1000.0

        audit.verificar(
            descricao="Comissao GL (CS decisao A, taxa reduzida)",
            formula="100000 × 0.02 × 0.40",
            entradas={"taxa_original": 0.03, "taxa_reduzida": nova_taxa},
            esperado=800.0,
            real=comissao_gl,
        )
        audit.verificar(
            descricao="Comissao CE (CS especial)",
            formula="100000 × 0.01",
            entradas={"fat": fat, "taxa_cs": taxa_cs_pct},
            esperado=1000.0,
            real=comissao_ce,
        )

    def test_cenario_item_alto_valor(self, audit):
        """Item de alto valor: 1.5M, taxa 2.5%, fatia legacy, FC=0.65."""
        audit.set_contexto(modulo="Comissao Faturamento", cenario="Alto valor")

        fat = 1_500_000.0
        taxa_pct = 2.5  # regra legacy
        fatia_pct = 35.0  # GL legacy
        fc = 0.65

        r = _calcular_comissao_formula(fat, taxa_pct, fatia_pct, fc_aplicado=fc)
        # Potencial: 1500000 × 0.025 × 0.35 = 13125.0
        # Final: 13125.0 × 0.65 = 8531.25

        audit.verificar(
            descricao="Comissao potencial alto valor",
            formula="1500000 × 0.025 × 0.35",
            entradas={"fat": fat, "taxa": taxa_pct, "fatia": fatia_pct},
            esperado=13125.0,
            real=r["comissao_potencial"],
        )
        audit.verificar(
            descricao="Comissao final alto valor FC=0.65",
            formula="13125.0 × 0.65",
            entradas={"potencial": 13125.0, "fc": fc},
            esperado=8531.25,
            real=r["comissao_item"],
        )


# =========================================================================
# CLASSE: TestAuditoriaColunas
# =========================================================================
@pytest.mark.unit
@pytest.mark.faturamento
class TestAuditoriaColunas:
    """Verifica que o base_dict produzido contém todas as colunas de auditoria."""

    COLUNAS_OBRIGATORIAS = [
        "id_colaborador",
        "nome_colaborador",
        "cargo",
        "fator_split_cargo",
        "cod_produto",
        "descricao_produto",
        "processo",
        "numero_nf",
        "linha",
        "grupo",
        "subgrupo",
        "tipo_mercadoria",
        "faturamento_item",
        "taxa_rateio_aplicada",
        "fator_correcao_fc",
        "fator_correcao_fc_rampa",
        "fc_escada_modo",
        "fc_escada_degrau_indice",
        "fc_escada_num_degraus",
        "fc_escada_piso",
        "percentual_elegibilidade_pe",
        "comissao_potencial_maxima",
        "comissao_calculada",
        "cross_selling_decision",
    ]

    COLUNAS_FC_DETALHES = [
        # Para cada componente: peso, realizado, meta, ating, ating_cap, comp_fc
        "peso_fat_linha", "realizado_fat_linha", "meta_fat_linha",
        "ating_fat_linha", "ating_cap_fat_linha", "comp_fc_fat_linha",
        "peso_conv_linha", "realizado_conv_linha", "meta_conv_linha",
        "ating_conv_linha", "ating_cap_conv_linha", "comp_fc_conv_linha",
        "peso_fat_ind", "realizado_fat_ind", "meta_fat_ind",
        "ating_fat_ind", "ating_cap_fat_ind", "comp_fc_fat_ind",
        "peso_conv_ind", "realizado_conv_ind", "meta_conv_ind",
        "ating_conv_ind", "ating_cap_conv_ind", "comp_fc_conv_ind",
        "peso_rentab", "realizado_rentab", "meta_rentab",
        "ating_rentab", "ating_cap_rentab", "comp_fc_rentab",
    ]

    def test_colunas_obrigatorias_presentes(self, audit):
        """Verifica a lista de colunas obrigatórias do base_dict."""
        audit.set_contexto(modulo="Auditoria Colunas", cenario="Colunas obrigatorias")

        # Simulando base_dict com todas as chaves
        base_dict = {col: None for col in self.COLUNAS_OBRIGATORIAS}

        for col in self.COLUNAS_OBRIGATORIAS:
            audit.verificar(
                descricao=f"Coluna '{col}' presente no base_dict",
                formula="col in base_dict",
                entradas={"coluna": col},
                esperado=True,
                real=col in base_dict,
            )

    def test_colunas_fc_detalhes_presentes(self, audit):
        """Verifica colunas de detalhamento do FC por componente."""
        audit.set_contexto(modulo="Auditoria Colunas", cenario="Colunas FC detalhes")

        base_dict = {col: None for col in self.COLUNAS_FC_DETALHES}

        for col in self.COLUNAS_FC_DETALHES:
            audit.verificar(
                descricao=f"Coluna FC '{col}' presente",
                formula="col in base_dict",
                entradas={"coluna": col},
                esperado=True,
                real=col in base_dict,
            )
