"""
Testes unitários para normalize_text() de src/utils/normalization.py.

Nota: calcular_atingimento() já está testado em test_fc_components.py
(TestCalcularAtingimento — 7 testes).

Cenários de normalize_text():
    - Remoção de acentos (unicode NFKD)
    - Remoção de BOM (\ufeff)
    - Conversão para maiúsculas
    - Normalização de espaços (strip + join)
    - NaN / pd.NA → string vazia
    - None → string vazia
    - Valor numérico → string
    - String já limpa → sem alteração
"""

import pytest
import pandas as pd

from src.utils.normalization import normalize_text


# =========================================================================
# CLASSE: TestNormalizeText
# =========================================================================
@pytest.mark.unit
class TestNormalizeText:
    """Testa normalize_text()."""

    def test_acentos_removidos(self, audit):
        """Acentos são removidos via decomposição unicode."""
        audit.set_contexto(modulo="Normalizacao", cenario="Remocao de acentos")

        resultado = normalize_text("José da Silva")

        audit.verificar(
            descricao="Acentos removidos: 'José da Silva' → 'JOSE DA SILVA'",
            formula="NFKD + encode ASCII",
            entradas={"input": "José da Silva"},
            esperado="JOSE DA SILVA",
            real=resultado,
        )

    def test_bom_removido(self, audit):
        """BOM (Byte Order Mark) é removido."""
        audit.set_contexto(modulo="Normalizacao", cenario="Remocao de BOM")

        resultado = normalize_text("\ufeffTexto com BOM")

        audit.verificar(
            descricao="BOM removido do inicio",
            formula="replace('\\ufeff', '')",
            entradas={"input": "\\ufeffTexto com BOM"},
            esperado="TEXTO COM BOM",
            real=resultado,
        )

    def test_maiusculas(self, audit):
        """Resultado é sempre em maiúsculas."""
        audit.set_contexto(modulo="Normalizacao", cenario="Maiusculas")

        resultado = normalize_text("texto minúsculo")

        audit.verificar(
            descricao="Conversao para maiusculas",
            formula=".upper()",
            entradas={"input": "texto minúsculo"},
            esperado="TEXTO MINUSCULO",
            real=resultado,
        )

    def test_espacos_normalizados(self, audit):
        """Múltiplos espaços são reduzidos a um."""
        audit.set_contexto(modulo="Normalizacao", cenario="Espacos extras")

        resultado = normalize_text("  Andre   Luis   Camargo  ")

        audit.verificar(
            descricao="Espacos extras normalizados",
            formula="' '.join(s.strip().split())",
            entradas={"input": "  Andre   Luis   Camargo  "},
            esperado="ANDRE LUIS CAMARGO",
            real=resultado,
        )

    def test_nan_retorna_vazio(self, audit):
        """pd.NA / NaN retorna string vazia."""
        audit.set_contexto(modulo="Normalizacao", cenario="NaN")

        resultado_na = normalize_text(pd.NA)
        resultado_nan = normalize_text(float("nan"))

        audit.verificar(
            descricao="pd.NA → ''",
            formula="pd.isna(s) → ''",
            entradas={"input": "pd.NA"},
            esperado="",
            real=resultado_na,
        )
        audit.verificar(
            descricao="float('nan') → ''",
            formula="pd.isna(s) → ''",
            entradas={"input": "NaN"},
            esperado="",
            real=resultado_nan,
        )

    def test_none_retorna_vazio(self, audit):
        """None retorna string vazia."""
        audit.set_contexto(modulo="Normalizacao", cenario="None")

        resultado = normalize_text(None)

        audit.verificar(
            descricao="None → ''",
            formula="pd.isna(None) → ''",
            entradas={"input": "None"},
            esperado="",
            real=resultado,
        )

    def test_numero_convertido_para_string(self, audit):
        """Valor numérico é convertido para string."""
        audit.set_contexto(modulo="Normalizacao", cenario="Numero")

        resultado = normalize_text(12345)

        audit.verificar(
            descricao="Numero → string",
            formula="str(12345) → '12345'",
            entradas={"input": 12345},
            esperado="12345",
            real=resultado,
        )

    def test_string_limpa_sem_alteracao(self, audit):
        """String já normalizada não muda."""
        audit.set_contexto(modulo="Normalizacao", cenario="Sem alteracao")

        resultado = normalize_text("ANDRE CAMARGO")

        audit.verificar(
            descricao="String ja normalizada permanece igual",
            formula="normalize_text('ANDRE CAMARGO') == 'ANDRE CAMARGO'",
            entradas={"input": "ANDRE CAMARGO"},
            esperado="ANDRE CAMARGO",
            real=resultado,
        )

    def test_cedilha_removida(self, audit):
        """Cedilha (ç) é removida."""
        audit.set_contexto(modulo="Normalizacao", cenario="Cedilha")

        resultado = normalize_text("Locação")

        audit.verificar(
            descricao="Cedilha removida: 'Locação' → 'LOCACAO'",
            formula="NFKD + encode ASCII",
            entradas={"input": "Locação"},
            esperado="LOCACAO",
            real=resultado,
        )

    def test_til_removido(self, audit):
        """Til (~) em vogais é removido."""
        audit.set_contexto(modulo="Normalizacao", cenario="Til")

        resultado = normalize_text("Remediação")

        audit.verificar(
            descricao="Til removido: 'Remediação' → 'REMEDIACAO'",
            formula="NFKD + encode ASCII",
            entradas={"input": "Remediação"},
            esperado="REMEDIACAO",
            real=resultado,
        )

    def test_string_vazia(self, audit):
        """String vazia retorna string vazia."""
        audit.set_contexto(modulo="Normalizacao", cenario="String vazia")

        resultado = normalize_text("")

        audit.verificar(
            descricao="String vazia → ''",
            formula="normalize_text('') == ''",
            entradas={"input": ""},
            esperado="",
            real=resultado,
        )

    def test_alias_erp_normalizado(self, audit):
        """Simula normalização de alias do ERP."""
        audit.set_contexto(modulo="Normalizacao", cenario="Alias ERP")

        resultado = normalize_text("ANDRÉ LUIS GONCALVES CAMARGO")

        audit.verificar(
            descricao="Alias ERP normalizado",
            formula="normalize_text(alias)",
            entradas={"input": "ANDRÉ LUIS GONCALVES CAMARGO"},
            esperado="ANDRE LUIS GONCALVES CAMARGO",
            real=resultado,
        )
