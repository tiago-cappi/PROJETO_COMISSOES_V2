"""
Módulo para cálculo de comissões por recebimento.
Sistema modular e independente do cálculo de comissões por faturamento.
"""

from .exceptions import RecebimentoError, InconsistenciaAdiantamentoError

__all__ = [
    "RecebimentoError",
    "InconsistenciaAdiantamentoError",
]
