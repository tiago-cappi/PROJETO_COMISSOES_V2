"""
Testes unitários: Normalização de Texto e Cálculo de Atingimento de Metas.

Módulo testado: src/utils/normalization.py
Lógica de negócio:
  - normalize_text(): padroniza strings como chaves de comparação (sem acentos, maiúsculas,
    sem BOM, sem espaços extras). Retorna string vazia para valores ausentes.
  - calcular_atingimento(): computa atingimento proporcional com validação fail-fast.
    Strings numéricas são aceitas. Entradas inválidas levantam ValueError abortando
    o cálculo de comissões.

Referência: DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md, Seção 5.3.1
Correção aplicada em: 09/Mar/2026 — comportamento alterado de tolerante para fail-fast.
"""

import math

import pandas as pd
import pytest

from src.utils.normalization import calcular_atingimento, normalize_text


# =============================================================================
# normalize_text()
# =============================================================================


class TestNormalizeText:
    """Testes para normalize_text() — padronização de strings para chaves de comparação."""

    def test_normaliza_acentos(self):
        """String com acentos deve ser convertida sem acentos e em maiúsculas."""
        assert normalize_text("José da Silva") == "JOSE DA SILVA"

    def test_normaliza_cedilha_e_til(self):
        """Cedilha e til devem ser removidos na normalização."""
        assert normalize_text("Ação & Reação") == "ACAO & REACAO"

    def test_remove_bom(self):
        """Caractere BOM (\\ufeff) presente em exportações Excel deve ser removido."""
        assert normalize_text("\ufeffNome") == "NOME"

    def test_string_vazia(self):
        """String vazia deve retornar string vazia."""
        assert normalize_text("") == ""

    def test_valor_none(self):
        """None deve retornar string vazia (pd.isna(None) == True)."""
        assert normalize_text(None) == ""

    def test_valor_nan_pandas_na(self):
        """pd.NA deve retornar string vazia."""
        assert normalize_text(pd.NA) == ""

    def test_valor_nan_float(self):
        """float('nan') deve retornar string vazia (pd.isna detecta NaN float)."""
        assert normalize_text(float("nan")) == ""

    def test_ja_normalizado(self):
        """String já em formato normalizado deve permanecer idêntica."""
        assert normalize_text("JOAO") == "JOAO"

    def test_espacos_extras_bordas(self):
        """Espaços nas bordas devem ser removidos via strip()."""
        assert normalize_text("  ANA  ") == "ANA"

    def test_espacos_extras_internos(self):
        """Múltiplos espaços internos devem ser colapsados para um único espaço."""
        assert normalize_text("  Ana   Maria  ") == "ANA MARIA"

    def test_valor_numerico_inteiro(self):
        """Inteiros devem ser convertidos via str() antes da normalização."""
        assert normalize_text(123) == "123"

    def test_valor_numerico_float(self):
        """Floats devem ser convertidos via str() antes da normalização."""
        assert normalize_text(99.5) == "99.5"

    def test_idempotente(self):
        """Aplicar normalize_text duas vezes deve produzir o mesmo resultado."""
        entrada = "Ação & Reação"
        resultado_1 = normalize_text(entrada)
        resultado_2 = normalize_text(resultado_1)
        assert resultado_1 == resultado_2


# =============================================================================
# calcular_atingimento() — casos válidos
# =============================================================================


class TestCalcularAtingimentoValido:
    """Testes de calcular_atingimento() com entradas válidas — cálculo proporcional."""

    def test_atingimento_normal(self):
        """Caso padrão: realizado abaixo da meta."""
        # 90.000 / 100.000 = 0.9
        assert calcular_atingimento(90_000, 100_000) == pytest.approx(0.9)

    def test_atingimento_superacao(self):
        """Realizado acima da meta: sem cap nesta função (cap é aplicado no FC)."""
        # 120.000 / 100.000 = 1.2
        assert calcular_atingimento(120_000, 100_000) == pytest.approx(1.2)

    def test_atingimento_exatamente_100_pct(self):
        """Realizado exatamente igual à meta retorna 1.0."""
        assert calcular_atingimento(100_000, 100_000) == pytest.approx(1.0)

    def test_meta_zero_realizado_positivo(self):
        """Meta zero com realizado positivo = 100% atingido por definição de negócio."""
        assert calcular_atingimento(50_000, 0) == pytest.approx(1.0)

    def test_string_numerica_valida(self):
        """Strings numéricas inteiras são aceitas e convertidas para float."""
        # "90000" / "100000" = 90000.0 / 100000.0 = 0.9
        assert calcular_atingimento("90000", "100000") == pytest.approx(0.9)

    def test_string_numerica_decimal(self):
        """Strings numéricas com casas decimais são aceitas."""
        assert calcular_atingimento("90000.50", "100000.00") == pytest.approx(0.900005)

    def test_string_numerica_meta_zero(self):
        """String '0' como meta com realizado positivo retorna 1.0."""
        assert calcular_atingimento("50000", "0") == pytest.approx(1.0)

    def test_entrada_float(self):
        """Valores float diretos são aceitos normalmente."""
        assert calcular_atingimento(90_000.0, 100_000.0) == pytest.approx(0.9)


# =============================================================================
# calcular_atingimento() — casos de erro: realizado inválido
# =============================================================================


class TestCalcularAtingimentoRealizadoInvalido:
    """Testes de calcular_atingimento() para entradas inválidas em 'realizado'."""

    def test_realizado_zero_raise(self):
        """Realizado igual a zero deve levantar ValueError com menção a 'realizado'."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento(0, 100_000)

    def test_realizado_zero_string_raise(self):
        """String '0' como realizado deve levantar ValueError."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento("0", 100_000)

    def test_realizado_negativo_raise(self):
        """Realizado negativo deve levantar ValueError com menção a 'realizado'."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento(-1_000, 100_000)

    def test_realizado_negativo_float_raise(self):
        """Realizado negativo como float deve levantar ValueError."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento(-0.01, 100_000)

    def test_realizado_none_raise(self):
        """None como realizado deve levantar ValueError (não é numérico válido)."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento(None, 100_000)

    def test_realizado_string_invalida_raise(self):
        """String não-numérica como realizado deve levantar ValueError."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento("abc", 100_000)

    def test_realizado_nan_float_raise(self):
        """float('nan') como realizado deve levantar ValueError."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento(float("nan"), 100_000)

    def test_realizado_lista_raise(self):
        """Tipo não-numérico (lista) como realizado deve levantar ValueError."""
        with pytest.raises(ValueError, match="realizado"):
            calcular_atingimento([90_000], 100_000)


# =============================================================================
# calcular_atingimento() — casos de erro: meta inválida
# =============================================================================


class TestCalcularAtingimentoMetaInvalida:
    """Testes de calcular_atingimento() para entradas inválidas em 'meta'."""

    def test_meta_negativa_raise(self):
        """Meta negativa deve levantar ValueError com menção a 'meta'."""
        with pytest.raises(ValueError, match="meta"):
            calcular_atingimento(90_000, -100)

    def test_meta_negativa_float_raise(self):
        """Meta negativa como float deve levantar ValueError."""
        with pytest.raises(ValueError, match="meta"):
            calcular_atingimento(90_000, -0.01)

    def test_meta_none_raise(self):
        """None como meta deve levantar ValueError."""
        with pytest.raises(ValueError, match="meta"):
            calcular_atingimento(90_000, None)

    def test_meta_string_invalida_raise(self):
        """String não-numérica como meta deve levantar ValueError."""
        with pytest.raises(ValueError, match="meta"):
            calcular_atingimento(90_000, "abc")

    def test_meta_nan_float_raise(self):
        """float('nan') como meta deve levantar ValueError."""
        with pytest.raises(ValueError, match="meta"):
            calcular_atingimento(90_000, float("nan"))
