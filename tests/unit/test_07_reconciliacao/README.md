# test_07_reconciliacao — Reconciliação de Adiantamentos

## Objetivo

Validar a detecção de processos elegíveis para reconciliação e o cálculo correto do ajuste (positivo, negativo ou zero).

## Módulos Testados

- `src/recebimento/reconciliacao/reconciliacao_detector.py` → `ReconciliacaoDetector`
- `src/recebimento/reconciliacao/reconciliacao_calculator.py` → `ReconciliacaoCalculator`

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 8** — Adiantamentos e Reconciliação

## Fórmula

```
Ajuste = Comissão_Adiantada × (FCMP_real - 1.0)

Condições para reconciliação:
1. STATUS_CALCULO_MEDIAS == "CALCULADO"
2. MES_ANO_FATURAMENTO == mês/ano de apuração
3. TOTAL_ANTECIPACOES > 0
4. STATUS_RECONCILIACAO != "CALCULADO"
```

## Testes Planejados

### Grupo A — Detecção de Elegibilidade

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 07.A1 | `test_processo_elegivel` | Métricas calculadas + adiantamento + não reconciliado + faturado no mês | Processo detectado como elegível |
| 07.A2 | `test_nao_elegivel_sem_adiantamento` | TOTAL_ANTECIPACOES = 0 | Não elegível |
| 07.A3 | `test_nao_elegivel_ja_reconciliado` | STATUS_RECONCILIACAO = "CALCULADO" | Não elegível |
| 07.A4 | `test_nao_elegivel_metricas_pendentes` | STATUS_CALCULO_MEDIAS = "PENDENTE" | Não elegível |
| 07.A5 | `test_nao_elegivel_mes_diferente` | MES_ANO_FATURAMENTO ≠ mês de apuração | Não elegível |

### Grupo B — Cálculo do Ajuste

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 07.B1 | `test_reconciliacao_fc_menor_1` | Comissão adiantada=R$500, FCMP=0.85 | Ajuste = 500 × (0.85 - 1.0) = **-R$ 75** |
| 07.B2 | `test_reconciliacao_fc_igual_1` | Comissão adiantada=R$500, FCMP=1.0 | Ajuste = 500 × (1.0 - 1.0) = **R$ 0** |
| 07.B3 | `test_reconciliacao_fc_maior_1` | Comissão adiantada=R$500, FCMP=1.05 | Ajuste = 500 × (1.05 - 1.0) = **+R$ 25** |
| 07.B4 | `test_reconciliacao_multiplos_colaboradores` | 2 colaboradores com adiantamentos diferentes | Ajustes individuais calculados por colaborador |

## Fixtures Necessários (subpasta `fixtures/`)

- `estado_processos.csv` — Estado de processos com campos JSON (TCMP, FCMP, comissões adiantadas)

## Cálculos Manuais

- **07.B1:** `500 × (0.85 - 1.0) = 500 × (-0.15) = -75.00`
- **07.B2:** `500 × (1.0 - 1.0) = 500 × 0.0 = 0.00`
- **07.B3:** `500 × (1.05 - 1.0) = 500 × 0.05 = 25.00`

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
