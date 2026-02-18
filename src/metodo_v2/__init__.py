"""
src.metodo_v2 - Metodologia V2 de Cálculo de Comissões (Hierarquia + Faixas)

Esta metodologia é uma alternativa isolada ao cálculo atual, baseada em:
- Regras de comissão por colaborador (faixas de faturamento absoluto)
- Atribuições de carteira por combinação hierárquica (linha/grupo/subgrupo/tipo/fabricante)
- Sistema de prioridade: regra mais específica vence a mais genérica

Estrutura:
- models_v2.py: Dataclasses (ColaboradorV2, RegraComissao, FaixaComissao, etc.)
- config_loader_v2.py: Carregamento do REGRAS_COMISSOES_V2.xlsx
- regra_matcher_v2.py: Seleção de regra por especificidade
- comissao_calculator_v2.py: Cálculo da comissão por hierarquia
- atribuicao_service_v2.py: Serviço de atribuição de colaboradores por item
- validators_v2.py: Validadores de configuração e dados
- orchestrator_v2.py: Orquestração do fluxo completo
"""

from .models_v2 import (
    FaixaComissao,
    RegraComissao,
    ColaboradorV2,
    ResultadoHierarquia,
    ResultadoColaboradorV2,
)
from .config_loader_v2 import ConfigLoaderV2
from .regra_matcher_v2 import RegraMatcher
from .comissao_calculator_v2 import ComissaoCalculatorV2
from .atribuicao_service_v2 import (
    AtribuicaoServiceV2,
    ColaboradorAtribuido,
    ResultadoAtribuicao,
    criar_servico_atribuicao,
)
from .validators_v2 import (
    ValidadorConfigV2,
    ValidadorAnaliseComercial,
    ResultadoValidacao,
    ErroValidacao,
    validar_ambiente_v2,
)
from .orchestrator_v2 import OrchestratorV2
from .recebimento_v2 import (
    RecebimentoOrchestratorV2,
    AnaliseFinanceiraLoaderV2,
    ProcessMapperV2,
    StateManagerV2,
    ComissaoRecebimentoCalculatorV2,
    ReconciliacaoCalculatorV2,
    OutputGeneratorV2,
)

__all__ = [
    # Models
    "FaixaComissao",
    "RegraComissao",
    "ColaboradorV2",
    "ResultadoHierarquia",
    "ResultadoColaboradorV2",
    # Loaders
    "ConfigLoaderV2",
    # Logic
    "RegraMatcher",
    "ComissaoCalculatorV2",
    # Atribuição
    "AtribuicaoServiceV2",
    "ColaboradorAtribuido",
    "ResultadoAtribuicao",
    "criar_servico_atribuicao",
    # Validação
    "ValidadorConfigV2",
    "ValidadorAnaliseComercial",
    "ResultadoValidacao",
    "ErroValidacao",
    "validar_ambiente_v2",
    # Orchestrator
    "OrchestratorV2",
    # Recebimento V2
    "RecebimentoOrchestratorV2",
    "AnaliseFinanceiraLoaderV2",
    "ProcessMapperV2",
    "StateManagerV2",
    "ComissaoRecebimentoCalculatorV2",
    "ReconciliacaoCalculatorV2",
    "OutputGeneratorV2",
]
