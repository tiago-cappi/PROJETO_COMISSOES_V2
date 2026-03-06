"""
Routers do Adapter FastAPI.

Este pacote contém os roteadores separados por domínio
para manter o código organizado e modular.
"""

from .monitor_router import router as monitor_router
from .historico_router import router as historico_router
from .comissoes_router import router as comissoes_router

__all__ = ["monitor_router", "historico_router", "comissoes_router"]
