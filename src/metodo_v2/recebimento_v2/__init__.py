"""
src.metodo_v2.recebimento_v2 - Submódulo de Comissões por Recebimento (V2)

Este submódulo implementa a lógica de comissões por RECEBIMENTO para a
Metodologia V2, completamente isolado do método padrão (src/recebimento/).

Fluxo Principal:
================
1. Carregar Análise Financeira (pagamentos com Tipo Baixa = "B")
2. Mapear documentos para processos:
   - COT* → Adiantamento
   - 6 dígitos NF → Pagamento Regular
3. Para Adiantamentos:
   - Aplicar taxa_adiantamento_pct fixa do colaborador
   - Fórmula: Comissão = Valor × Taxa_Fixa × Split
4. Para Pagamentos Regulares:
   - Buscar regra/faixa do colaborador (hierarquia ou CC)
   - Fórmula: Comissão = Valor × Taxa_Faixa × Split
5. Reconciliação:
   - Quando processo é FATURADO, recalcular comissão real
   - Ajuste = Comissão_Real - Comissão_Adiantada

Componentes:
============
- RecebimentoOrchestratorV2: Orquestrador principal
- AnaliseFinanceiraLoaderV2: Carrega dados de pagamentos
- ProcessMapperV2: Mapeia documento → processo
- ComissaoRecebimentoCalculatorV2: Calcula comissões
- StateManagerV2: Estado persistente
- ReconciliacaoCalculatorV2: Cálculo de reconciliação
- OutputGeneratorV2: Gerador de arquivos de saída
"""

from .recebimento_orchestrator_v2 import RecebimentoOrchestratorV2
from .analise_financeira_loader_v2 import AnaliseFinanceiraLoaderV2
from .process_mapper_v2 import ProcessMapperV2
from .comissao_recebimento_calculator_v2 import ComissaoRecebimentoCalculatorV2
from .state_manager_v2 import StateManagerV2
from .reconciliacao_calculator_v2 import ReconciliacaoCalculatorV2
from .output_generator_v2 import OutputGeneratorV2

__all__ = [
    "RecebimentoOrchestratorV2",
    "AnaliseFinanceiraLoaderV2",
    "ProcessMapperV2",
    "ComissaoRecebimentoCalculatorV2",
    "StateManagerV2",
    "ReconciliacaoCalculatorV2",
    "OutputGeneratorV2",
]
