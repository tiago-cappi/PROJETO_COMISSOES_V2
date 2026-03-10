# test_12_recebimento_e2e — Integração: Recebimento Ponta a Ponta

## Objetivo

Validar o fluxo completo de cálculo de comissões por recebimento, incluindo carregamento da Análise Financeira, mapeamento de documentos, cálculo de métricas (TCMP/FCMP), processamento de adiantamentos e pagamentos regulares, e reconciliação.

## Módulos Integrados

- `src/recebimento/io/analise_financeira_loader.py` (carga)
- `src/recebimento/core/process_mapper.py` (mapeamento)
- `src/recebimento/core/metricas_calculator.py` (TCMP/FCMP)
- `src/recebimento/core/comissao_calculator.py` (comissão)
- `src/recebimento/core/identificador_colaboradores.py` (elegibilidade)
- `src/recebimento/estado/state_manager.py` (persistência)
- `src/recebimento/reconciliacao/reconciliacao_detector.py` (detecção)
- `src/recebimento/reconciliacao/reconciliacao_calculator.py` (ajuste)
- `src/recebimento/recebimento_orchestrator.py` (orquestrador)

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seções 6 e 8** — Recebimento + Reconciliação

## Fluxo Integrado

```
Análise Financeira (filtrada: Tipo Baixa='B', mês/ano)
  → ProcessMapper: COT → Adiantamento | NF → Pagamento Regular
  → State: criar/atualizar processo com valores acumulados
  → MetricasCalculator: TCMP e FCMP quando faturado
  → ComissaoCalculator:
      Adiantamento = V × TCMP × 1.0
      Regular = V × TCMP × FCMP
  → ReconciliacaoDetector + Calculator: 
      Ajuste = Comissão_Adiantada × (FCMP - 1.0)
```

## Testes Planejados

| ID | Teste | Cenário | O que valida |
|----|-------|---------|-------------|
| 12.1 | `test_adiantamento_processo_nao_faturado` | COT para processo não faturado | Comissão com FC=1.0, estado atualizado com TOTAL_ANTECIPACOES |
| 12.2 | `test_pagamento_regular_processo_faturado` | NF para processo FATURADO | Comissão com FCMP real calculado |
| 12.3 | `test_reconciliacao_apos_faturamento` | Processo com adiantamento prévio, agora faturado | Ajuste negativo gerado (FCMP < 1.0) |
| 12.4 | `test_estado_acumulado` | Múltiplos pagamentos no mesmo processo | SALDO_A_RECEBER atualizado corretamente |
| 12.5 | `test_processo_nao_reconciliado_sem_adiantamento` | Processo faturado mas sem COTs | Nenhuma reconciliação gerada |

## Fixtures Necessários (subpasta `fixtures/`)

- `analise_financeira.csv` — Documentos financeiros (COTs + NFs regulares)
- `analise_comercial.csv` — Processos e itens (com status variados)
- `config_params.csv` — Parâmetros (mês/ano apuração)
- `config_colaboradores.csv` — Colaboradores com TIPO_COMISSAO
- `config_cargos.csv` — Cargos com TIPO_COMISSAO="recebimento"
- `config_pesos_metas.csv` — Pesos para cálculo do FC
- `config_metas_aplicacao.csv` — Metas de faturamento/conversão
- `config_comissao.csv` — Regras de comissão (taxa/fatia)
- `config_atribuicoes.csv` — Atribuições

## Cálculos Manuais

Serão detalhados por cenário como parte do protocolo de validação com o usuário.

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
