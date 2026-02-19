"""
Testes unitários para o módulo de câmbio (currency).

Testa:
    1. RateStorage — armazenamento JSON de taxas cambiais
       - obter_taxa(): recupera taxa por moeda/ano/mês
       - salvar_taxa(): persiste taxa no JSON
       - calcular_media_ano_ate_mes(): fallback com média simples
       - Taxa inexistente retorna None

    2. RateCalculator — operações de alto nível
       - obter_taxas_ytd(): série de taxas de jan até mês
       - calcular_faturamento_convertido_ytd(): soma YTD convertida
       - Meses sem taxa são ignorados
       - mes_final <= 0 retorna vazio/zero
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.currency.rate_storage import RateStorage
from src.currency.rate_calculator import RateCalculator
from tests_comissoes.fixtures.empresa_constants import TAXAS_CAMBIO_TESTE


# =========================================================================
# HELPERS
# =========================================================================

def _criar_storage_em_memoria() -> MagicMock:
    """Cria um mock de RateStorage com taxas de teste em memória."""
    storage = MagicMock(spec=RateStorage)

    def _obter_taxa(moeda: str, ano: int, mes: int):
        moeda_up = str(moeda).upper()
        ano_s = str(ano)
        mes_s = str(mes)
        try:
            return TAXAS_CAMBIO_TESTE[moeda_up][ano_s][mes_s]
        except KeyError:
            return None

    storage.obter_taxa.side_effect = _obter_taxa
    return storage


def _criar_storage_real(tmp_path: Path) -> RateStorage:
    """Cria um RateStorage real com arquivo temporário."""
    json_path = tmp_path / "monthly_avg_rates.json"
    json_path.write_text('{"metadata": {}, "taxas": {}}', encoding="utf-8")
    return RateStorage(json_path)


# =========================================================================
# CLASSE: TestRateStorageObterTaxa
# =========================================================================
@pytest.mark.unit
class TestRateStorageObterTaxa:
    """Testa obter_taxa() do RateStorage."""

    def test_taxa_usd_janeiro(self, tmp_path, audit):
        """Recupera taxa USD de janeiro/2025."""
        audit.set_contexto(modulo="Currency Storage", cenario="USD Jan/2025")

        storage = _criar_storage_real(tmp_path)
        storage.salvar_taxa("USD", 2025, 1, 4.95, "BCB", 20)

        taxa = storage.obter_taxa("USD", 2025, 1)

        audit.verificar(
            descricao="Taxa USD Jan/2025",
            formula="obter_taxa('USD', 2025, 1)",
            entradas={"moeda": "USD", "ano": 2025, "mes": 1},
            esperado=4.95,
            real=taxa,
        )

    def test_taxa_gbp_junho(self, tmp_path, audit):
        """Recupera taxa GBP de junho/2025."""
        audit.set_contexto(modulo="Currency Storage", cenario="GBP Jun/2025")

        storage = _criar_storage_real(tmp_path)
        storage.salvar_taxa("GBP", 2025, 6, 6.32, "BCB", 18)

        taxa = storage.obter_taxa("GBP", 2025, 6)

        audit.verificar(
            descricao="Taxa GBP Jun/2025",
            formula="obter_taxa('GBP', 2025, 6)",
            entradas={"moeda": "GBP", "ano": 2025, "mes": 6},
            esperado=6.32,
            real=taxa,
        )

    def test_taxa_inexistente_retorna_none(self, tmp_path, audit):
        """Moeda/mês não cadastrado retorna None."""
        audit.set_contexto(modulo="Currency Storage", cenario="Taxa inexistente")

        storage = _criar_storage_real(tmp_path)

        taxa = storage.obter_taxa("EUR", 2025, 1)

        audit.verificar(
            descricao="Taxa inexistente retorna None",
            formula="obter_taxa('EUR', 2025, 1)",
            entradas={"moeda": "EUR"},
            esperado=None,
            real=taxa,
        )

    def test_salvar_e_recuperar(self, tmp_path, audit):
        """Salva taxa e recupera com mesmo valor."""
        audit.set_contexto(modulo="Currency Storage", cenario="Salvar e recuperar")

        storage = _criar_storage_real(tmp_path)
        storage.salvar_taxa("USD", 2025, 3, 5.01, "BCB", 22)

        taxa = storage.obter_taxa("USD", 2025, 3)

        audit.verificar(
            descricao="Taxa salva e recuperada corretamente",
            formula="salvar_taxa → obter_taxa",
            entradas={"moeda": "USD", "ano": 2025, "mes": 3, "taxa_salva": 5.01},
            esperado=5.01,
            real=taxa,
        )

    def test_sobrescrever_taxa_existente(self, tmp_path, audit):
        """Salvar taxa no mesmo mês/moeda sobrescreve o valor anterior."""
        audit.set_contexto(modulo="Currency Storage", cenario="Sobrescrever")

        storage = _criar_storage_real(tmp_path)
        storage.salvar_taxa("USD", 2025, 1, 4.50, "BCB", 20)
        storage.salvar_taxa("USD", 2025, 1, 4.95, "BCB", 21)

        taxa = storage.obter_taxa("USD", 2025, 1)

        audit.verificar(
            descricao="Taxa sobrescrita com novo valor",
            formula="salvar_taxa(4.50) → salvar_taxa(4.95) → obter_taxa",
            entradas={"valor_antigo": 4.50, "valor_novo": 4.95},
            esperado=4.95,
            real=taxa,
        )


# =========================================================================
# CLASSE: TestRateStorageMediaAno
# =========================================================================
@pytest.mark.unit
class TestRateStorageMediaAno:
    """Testa calcular_media_ano_ate_mes()."""

    def test_media_3_meses(self, tmp_path, audit):
        """Média de Jan-Mar/2025 USD."""
        audit.set_contexto(modulo="Currency Storage", cenario="Media 3 meses")

        storage = _criar_storage_real(tmp_path)
        storage.salvar_taxa("USD", 2025, 1, 4.95, "BCB", 20)
        storage.salvar_taxa("USD", 2025, 2, 4.98, "BCB", 20)
        storage.salvar_taxa("USD", 2025, 3, 5.01, "BCB", 20)

        media = storage.calcular_media_ano_ate_mes("USD", 2025, 3)
        # (4.95 + 4.98 + 5.01) / 3 = 4.98
        esperado = (4.95 + 4.98 + 5.01) / 3

        audit.verificar(
            descricao="Media USD Jan-Mar/2025",
            formula="(4.95 + 4.98 + 5.01) / 3",
            entradas={"meses": [1, 2, 3], "taxas": [4.95, 4.98, 5.01]},
            esperado=round(esperado, 10),
            real=round(media, 10),
        )

    def test_media_com_meses_faltando(self, tmp_path, audit):
        """Média ignora meses sem taxa."""
        audit.set_contexto(modulo="Currency Storage", cenario="Media meses faltando")

        storage = _criar_storage_real(tmp_path)
        storage.salvar_taxa("USD", 2025, 1, 4.95, "BCB", 20)
        # Mês 2 não cadastrado
        storage.salvar_taxa("USD", 2025, 3, 5.01, "BCB", 20)

        media = storage.calcular_media_ano_ate_mes("USD", 2025, 3)
        # Apenas meses 1 e 3: (4.95 + 5.01) / 2 = 4.98
        esperado = (4.95 + 5.01) / 2

        audit.verificar(
            descricao="Media com mes faltando (somente 1 e 3)",
            formula="(4.95 + 5.01) / 2",
            entradas={"meses_com_taxa": [1, 3]},
            esperado=esperado,
            real=media,
        )

    def test_media_sem_nenhuma_taxa(self, tmp_path, audit):
        """Sem taxas cadastradas retorna None."""
        audit.set_contexto(modulo="Currency Storage", cenario="Sem taxas")

        storage = _criar_storage_real(tmp_path)

        media = storage.calcular_media_ano_ate_mes("USD", 2025, 6)

        audit.verificar(
            descricao="Sem taxas retorna None",
            formula="len(valores) == 0 → None",
            entradas={"moeda": "USD"},
            esperado=None,
            real=media,
        )

    def test_media_mes_limite_zero(self, tmp_path, audit):
        """mes_limite <= 0 retorna None."""
        audit.set_contexto(modulo="Currency Storage", cenario="Mes limite zero")

        storage = _criar_storage_real(tmp_path)

        media = storage.calcular_media_ano_ate_mes("USD", 2025, 0)

        audit.verificar(
            descricao="mes_limite=0 retorna None",
            formula="mes_limite <= 0 → None",
            entradas={"mes_limite": 0},
            esperado=None,
            real=media,
        )


# =========================================================================
# CLASSE: TestRateCalculatorObterTaxasYTD
# =========================================================================
@pytest.mark.unit
class TestRateCalculatorObterTaxasYTD:
    """Testa obter_taxas_ytd() do RateCalculator."""

    def test_ytd_usd_ate_marco(self, audit):
        """Retorna taxas de jan a mar/2025 para USD."""
        audit.set_contexto(modulo="Currency Calculator", cenario="YTD USD ate Mar")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        taxas = calc.obter_taxas_ytd("USD", 2025, 3)

        audit.verificar(
            descricao="Numero de meses retornados (Jan-Mar)",
            formula="len(taxas)",
            entradas={"mes_final": 3},
            esperado=3,
            real=len(taxas),
        )
        audit.verificar(
            descricao="Taxa USD Jan/2025",
            formula="taxas[1]",
            entradas={"moeda": "USD", "mes": 1},
            esperado=4.95,
            real=taxas[1],
        )
        audit.verificar(
            descricao="Taxa USD Mar/2025",
            formula="taxas[3]",
            entradas={"moeda": "USD", "mes": 3},
            esperado=5.01,
            real=taxas[3],
        )

    def test_ytd_gbp_ate_junho(self, audit):
        """Retorna taxas GBP de jan a jun/2025."""
        audit.set_contexto(modulo="Currency Calculator", cenario="YTD GBP ate Jun")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        taxas = calc.obter_taxas_ytd("GBP", 2025, 6)

        audit.verificar(
            descricao="6 meses de GBP",
            formula="len(taxas) == 6",
            entradas={"mes_final": 6},
            esperado=6,
            real=len(taxas),
        )

    def test_ytd_moeda_inexistente(self, audit):
        """Moeda não cadastrada → dicionário vazio."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Moeda inexistente")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        taxas = calc.obter_taxas_ytd("EUR", 2025, 6)

        audit.verificar(
            descricao="Moeda inexistente retorna dict vazio",
            formula="len(taxas) == 0",
            entradas={"moeda": "EUR"},
            esperado=0,
            real=len(taxas),
        )

    def test_ytd_mes_final_zero(self, audit):
        """mes_final <= 0 → dicionário vazio."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Mes final zero")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        taxas = calc.obter_taxas_ytd("USD", 2025, 0)

        audit.verificar(
            descricao="mes_final=0 retorna dict vazio",
            formula="mes_final <= 0 → {}",
            entradas={"mes_final": 0},
            esperado=0,
            real=len(taxas),
        )


# =========================================================================
# CLASSE: TestRateCalculatorFaturamentoConvertido
# =========================================================================
@pytest.mark.unit
class TestRateCalculatorFaturamentoConvertido:
    """Testa calcular_faturamento_convertido_ytd()."""

    def test_conversao_usd_3_meses(self, audit):
        """Converte faturamento BRL→USD para Jan-Mar/2025."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Conversao USD 3 meses")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        faturamento_mensal = {
            1: 100_000.0,  # R$ 100k
            2: 120_000.0,
            3: 80_000.0,
        }

        total = calc.calcular_faturamento_convertido_ytd(
            faturamento_mensal, "USD", 2025, 3
        )

        # Jan: 100000 × 4.95 = 495000
        # Fev: 120000 × 4.98 = 597600
        # Mar: 80000 × 5.01 = 400800
        # Total: 1493400.0
        esperado = 100_000 * 4.95 + 120_000 * 4.98 + 80_000 * 5.01

        audit.verificar(
            descricao="Faturamento convertido YTD USD (3 meses)",
            formula="sum(valor_brl_i × taxa_i)",
            entradas={"faturamento": faturamento_mensal, "taxas": {"1": 4.95, "2": 4.98, "3": 5.01}},
            esperado=esperado,
            real=total,
        )

    def test_conversao_com_meses_sem_taxa(self, audit):
        """Meses sem taxa são ignorados na soma."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Meses sem taxa")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        faturamento_mensal = {
            1: 100_000.0,
            2: 120_000.0,
            3: 80_000.0,
        }

        # EUR não tem taxas cadastradas
        total = calc.calcular_faturamento_convertido_ytd(
            faturamento_mensal, "EUR", 2025, 3
        )

        audit.verificar(
            descricao="Sem taxas → total zero",
            formula="nenhuma taxa disponível → 0.0",
            entradas={"moeda": "EUR"},
            esperado=0.0,
            real=total,
        )

    def test_conversao_mes_alem_do_limite(self, audit):
        """Meses além de mes_final são ignorados."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Mes alem do limite")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        faturamento_mensal = {
            1: 100_000.0,
            2: 120_000.0,
            3: 80_000.0,
            4: 90_000.0,  # Além do limite (mes_final=3)
        }

        total = calc.calcular_faturamento_convertido_ytd(
            faturamento_mensal, "USD", 2025, 3
        )
        # Apenas meses 1-3
        esperado = 100_000 * 4.95 + 120_000 * 4.98 + 80_000 * 5.01

        audit.verificar(
            descricao="Mes 4 ignorado (mes_final=3)",
            formula="sum apenas meses 1-3",
            entradas={"mes_final": 3, "meses_no_dict": [1, 2, 3, 4]},
            esperado=esperado,
            real=total,
        )

    def test_conversao_dict_vazio(self, audit):
        """Faturamento vazio → total zero."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Faturamento vazio")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        total = calc.calcular_faturamento_convertido_ytd({}, "USD", 2025, 6)

        audit.verificar(
            descricao="Faturamento vazio → 0.0",
            formula="sum de dict vazio = 0.0",
            entradas={"faturamento": {}},
            esperado=0.0,
            real=total,
        )

    def test_conversao_gbp_completa(self, audit):
        """Converte faturamento BRL→GBP usando taxas de teste."""
        audit.set_contexto(modulo="Currency Calculator", cenario="Conversao GBP completa")

        storage = _criar_storage_em_memoria()
        calc = RateCalculator(storage)

        faturamento = {1: 50_000.0, 2: 60_000.0}

        total = calc.calcular_faturamento_convertido_ytd(
            faturamento, "GBP", 2025, 2
        )
        # Jan: 50000 × 6.20 = 310000
        # Fev: 60000 × 6.25 = 375000
        esperado = 50_000 * 6.20 + 60_000 * 6.25

        audit.verificar(
            descricao="Faturamento convertido GBP (2 meses)",
            formula="50000×6.20 + 60000×6.25",
            entradas={"jan": 50_000, "fev": 60_000},
            esperado=esperado,
            real=total,
        )
