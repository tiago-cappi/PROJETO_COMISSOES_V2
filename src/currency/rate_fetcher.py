"""
Módulo responsável por buscar taxas de câmbio médias mensais na API oficial do Banco Central do Brasil.

Estratégia:
- Utiliza exclusivamente a API de Dados Abertos do BCB (PTAX).
- Busca as taxas diárias de venda para o mês solicitado.
- Calcula a média aritmética das taxas diárias.
- Realiza a inversão da taxa (1/PTAX) para adequar ao padrão do sistema (Moeda Estrangeira / BRL).

Observação:
- O objetivo deste módulo é alimentar o JSON persistente de câmbio em
  `data/currency_rates/monthly_avg_rates.json`.
"""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Optional, Tuple

try:
    from src.currency.bcb_client import BCBClient
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False


class RateFetcher:
    """Responsável exclusivamente por buscar taxas na API do BCB."""

    def __init__(self, timeout: float = 60.0, max_retries: int = 2) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        if CLIENT_AVAILABLE:
            self.client = BCBClient(timeout=timeout)
        else:
            self.client = None

    def _log(self, msg: str) -> None:
        print(f"[CAMBIO_API] {msg}")

    def buscar_taxa_media_mensal(
        self, moeda: str, ano: int, mes: int
    ) -> Optional[Tuple[float, str, int]]:
        """
        Busca taxa média mensal para uma moeda específica usando o BCB.

        Returns:
            (taxa_media, fonte_api, dias_utilizados) ou None se falhar.
        """
        if not CLIENT_AVAILABLE or not self.client:
            self._log("Cliente BCB não disponível.")
            return None

        moeda = str(moeda).upper()
        
        # Definir intervalo do mês completo
        primeiro_dia = datetime(ano, mes, 1).date()
        ultimo_dia = datetime(ano, mes, calendar.monthrange(ano, mes)[1]).date()

        self._log(f"Buscando taxas para {moeda} em {ano}-{mes:02d} via BCB...")

        try:
            # Busca taxas diárias (já invertidas pelo client)
            rates = self.client.get_daily_rates(moeda, primeiro_dia, ultimo_dia)
            
            if rates:
                taxa_media = sum(rates) / len(rates)
                self._log(
                    f"Taxa obtida via BCB: {moeda} {ano}-{mes:02d} = {taxa_media:.6f} (dias={len(rates)})"
                )
                return taxa_media, "BCB/PTAX", len(rates)
            else:
                self._log(f"Nenhuma taxa encontrada no BCB para {moeda} em {ano}-{mes:02d}.")
                return None

        except Exception as e:
            self._log(f"Erro ao buscar taxa no BCB: {e}")
            return None


