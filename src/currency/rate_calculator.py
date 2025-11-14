"""
Utilitários para cálculo de valores convertidos usando as taxas armazenadas.
"""

from __future__ import annotations

from typing import Dict

from .rate_storage import RateStorage


class RateCalculator:
    """
    Fornece operações de alto nível para uso no cálculo de FC dos fornecedores:
    - Obter série de taxas YTD
    - Calcular faturamento convertido YTD a partir de valores em BRL
    """

    def __init__(self, storage: RateStorage) -> None:
        self.storage = storage

    def obter_taxas_ytd(
        self, moeda: str, ano: int, mes_final: int
    ) -> Dict[int, float]:
        """
        Retorna dicionário {mes: taxa_media} de janeiro até `mes_final` (inclusive).
        """
        resultado: Dict[int, float] = {}
        moeda_up = str(moeda).upper()
        if mes_final <= 0:
            return resultado

        for mes in range(1, mes_final + 1):
            taxa = self.storage.obter_taxa(moeda_up, ano, mes)
            if taxa is not None:
                resultado[mes] = taxa
        return resultado

    def calcular_faturamento_convertido_ytd(
        self,
        faturamento_mensal_brl: Dict[int, float],
        moeda: str,
        ano: int,
        mes_final: int,
    ) -> float:
        """
        Converte faturamento em BRL para a moeda alvo, somando YTD.

        Args:
            faturamento_mensal_brl: mapa {mes: valor_em_brl}
            moeda: código da moeda alvo (ex.: 'USD')
            ano: ano de referência
            mes_final: último mês a considerar (1-12)

        Returns:
            Soma YTD convertida.
        """
        taxas = self.obter_taxas_ytd(moeda, ano, mes_final)
        total_convertido = 0.0

        for mes, valor_brl in faturamento_mensal_brl.items():
            if mes > mes_final:
                continue
            taxa = taxas.get(mes)
            if taxa is None:
                continue
            try:
                total_convertido += float(valor_brl) * float(taxa)
            except Exception:
                continue

        return total_convertido


