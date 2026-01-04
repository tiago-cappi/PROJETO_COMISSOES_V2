"""
Módulo de Processamento de Devoluções.

Este módulo implementa a lógica de cálculo de saldos negativos
para devoluções de itens/processos que já foram comissionados.

Componentes:
- DevolucaoLoader: Carrega e valida arquivo Devoluções.xlsx
- DevolucaoCalculator: Calcula saldos negativos proporcionais
- DevolucaoProcessor: Orquestra o processamento completo
"""

from .devolucao_loader import DevolucaoLoader
from .devolucao_calculator import DevolucaoCalculator
from .devolucao_processor import DevolucaoProcessor

__all__ = [
    "DevolucaoLoader",
    "DevolucaoCalculator", 
    "DevolucaoProcessor",
]
