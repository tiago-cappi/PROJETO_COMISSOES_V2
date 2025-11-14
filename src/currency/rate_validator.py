"""
Validação e detecção de lacunas nas taxas de câmbio armazenadas.
"""

from __future__ import annotations

from typing import List, Tuple

from .rate_storage import RateStorage


class RateValidator:
    """
    Responsável por identificar quais (moeda, ano, mês) ainda não possuem
    taxa média registrada no JSON.
    """

    def __init__(self, storage: RateStorage) -> None:
        self.storage = storage

    def identificar_taxas_faltantes(
        self, moedas: List[str], ano: int, mes_final: int
    ) -> List[Tuple[str, int, int]]:
        """
        Identifica taxas faltantes de JAN até `mes_final` (inclusive) para um ano.

        Args:
            moedas: lista de códigos de moeda (ex.: ['USD', 'GBP'])
            ano: ano de referência
            mes_final: último mês fechado (1-12)
        """
        faltantes: List[Tuple[str, int, int]] = []
        if mes_final <= 0:
            return faltantes

        for moeda in moedas:
            moeda_up = str(moeda).upper()
            for mes in range(1, mes_final + 1):
                taxa = self.storage.obter_taxa(moeda_up, ano, mes)
                if taxa is None:
                    faltantes.append((moeda_up, ano, mes))
        return faltantes


