"""
Módulo responsável por buscar taxas de câmbio médias mensais em APIs externas.

Estratégia:
- Tenta primeiro exchangerate.host/timeseries (média mensal verdadeira)
- Fallback para frankfurter.app (taxa do dia central do mês)
- Fallback final para exchangerate.host/convert (taxa do dia central)

Observação importante:
- O objetivo deste módulo é alimentar o JSON persistente de câmbio em
  `data/currency_rates/monthly_avg_rates.json`. Como essa atualização roda
  poucas vezes (e sempre ANTES do cálculo das comissões), o timeout padrão
  foi configurado para um valor relativamente alto (60 segundos) para cada
  requisição, aceitando um processo um pouco mais demorado em troca de
  maior chance de sucesso nas consultas às APIs.
"""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Optional, Tuple

try:  # Import opcional para facilitar testes offline
    import requests

    REQUESTS_AVAILABLE = True
except Exception:  # pragma: no cover - ambiente sem requests
    REQUESTS_AVAILABLE = False


class RateFetcher:
    """Responsável exclusivamente por buscar taxas nas APIs."""

    def __init__(self, timeout: float = 60.0, max_retries: int = 2) -> None:
        self.timeout = timeout
        self.max_retries = max_retries

    def _log(self, msg: str) -> None:
        # Logs deste módulo sempre com prefixo claro para depuração
        print(f"[CAMBIO_API] {msg}")

    def buscar_taxa_media_mensal(
        self, moeda: str, ano: int, mes: int
    ) -> Optional[Tuple[float, str, int]]:
        """
        Busca taxa média mensal para uma moeda específica.

        Returns:
            (taxa_media, fonte_api, dias_utilizados) ou None se todas as APIs falharem.
        """
        if not REQUESTS_AVAILABLE:
            self._log(
                f"Biblioteca 'requests' não disponível; não é possível buscar taxas para {moeda} {ano}-{mes:02d}."
            )
            return None

        moeda = str(moeda).upper()
        primeiro_dia = datetime(ano, mes, 1).date()
        ultimo_dia = datetime(ano, mes, calendar.monthrange(ano, mes)[1]).date()
        dia_central = min(15, calendar.monthrange(ano, mes)[1])
        data_central = datetime(ano, mes, dia_central).date().isoformat()

        # ------------------------------------------------------------------
        # Estratégia 1: exchangerate.host/timeseries (média mensal real)
        # ------------------------------------------------------------------
        try:
            url = "https://api.exchangerate.host/timeseries"
            params = {
                "start_date": primeiro_dia.isoformat(),
                "end_date": ultimo_dia.isoformat(),
                "base": "BRL",
                "symbols": moeda,
            }
            for attempt in range(1, self.max_retries + 1):
                try:
                    r = requests.get(url, params=params, timeout=self.timeout)
                    if r.status_code == 200:
                        data = r.json()
                        rates = []
                        for _, vals in data.get("rates", {}).items():
                            v = vals.get(moeda)
                            if v is not None:
                                rates.append(float(v))
                        if rates:
                            taxa_media = sum(rates) / len(rates)
                            self._log(
                                f"Taxa obtida via timeseries: {moeda} {ano}-{mes:02d} = {taxa_media:.6f} (dias={len(rates)})"
                            )
                            return taxa_media, "exchangerate.host/timeseries", len(
                                rates
                            )
                except Exception as e:
                    if attempt < self.max_retries:
                        continue
                    self._log(
                        f"Falha timeseries para {moeda} {ano}-{mes:02d} (tentativa {attempt}/{self.max_retries}): {e}"
                    )
        except Exception as e:
            self._log(
                f"Erro inesperado ao chamar timeseries para {moeda} {ano}-{mes:02d}: {e}"
            )

        # ------------------------------------------------------------------
        # Estratégia 2: frankfurter.app (taxa do dia central)
        # ------------------------------------------------------------------
        try:
            url = f"https://api.frankfurter.app/{data_central}"
            params = {"from": "BRL", "to": moeda}
            for attempt in range(1, self.max_retries + 1):
                try:
                    r = requests.get(url, params=params, timeout=self.timeout)
                    if r.status_code == 200:
                        data = r.json()
                        taxa = data.get("rates", {}).get(moeda)
                        if taxa is not None:
                            taxa_f = float(taxa)
                            self._log(
                                f"Taxa obtida via frankfurter: {moeda} {ano}-{mes:02d} = {taxa_f:.6f} (dia={data_central})"
                            )
                            return taxa_f, "frankfurter.app", 1
                except Exception as e:
                    if attempt < self.max_retries:
                        continue
                    self._log(
                        f"Falha frankfurter para {moeda} {ano}-{mes:02d} (tentativa {attempt}/{self.max_retries}): {e}"
                    )
        except Exception as e:
            self._log(
                f"Erro inesperado ao chamar frankfurter para {moeda} {ano}-{mes:02d}: {e}"
            )

        # ------------------------------------------------------------------
        # Estratégia 3: exchangerate.host/convert (taxa do dia central)
        # ------------------------------------------------------------------
        try:
            url = "https://api.exchangerate.host/convert"
            params = {"from": "BRL", "to": moeda, "date": data_central}
            for attempt in range(1, self.max_retries + 1):
                try:
                    r = requests.get(url, params=params, timeout=self.timeout)
                    if r.status_code == 200:
                        data = r.json()
                        taxa = data.get("result") or data.get("info", {}).get("rate")
                        if taxa is not None:
                            taxa_f = float(taxa)
                            self._log(
                                f"Taxa obtida via convert: {moeda} {ano}-{mes:02d} = {taxa_f:.6f} (dia={data_central})"
                            )
                            return taxa_f, "exchangerate.host/convert", 1
                except Exception as e:
                    if attempt < self.max_retries:
                        continue
                    self._log(
                        f"Falha convert para {moeda} {ano}-{mes:02d} (tentativa {attempt}/{self.max_retries}): {e}"
                    )
        except Exception as e:
            self._log(
                f"Erro inesperado ao chamar convert para {moeda} {ano}-{mes:02d}: {e}"
            )

        self._log(
            f"Nenhuma API retornou taxa para {moeda} {ano}-{mes:02d}; retornando None."
        )
        return None


