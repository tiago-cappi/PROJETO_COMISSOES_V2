"""
Pacote centralizado para gerenciamento de taxas de câmbio.

Responsável por:
- Buscar taxas médias mensais nas APIs externas
- Armazenar taxas em JSON persistente
- Validar lacunas de dados
- Fornecer utilitários de cálculo usando as taxas armazenadas
"""

from .rate_fetcher import RateFetcher
from .rate_storage import RateStorage
from .rate_validator import RateValidator
from .rate_calculator import RateCalculator

__all__ = ["RateFetcher", "RateStorage", "RateValidator", "RateCalculator"]


