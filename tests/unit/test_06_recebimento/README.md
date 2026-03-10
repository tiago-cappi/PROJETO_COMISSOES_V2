# test_06_recebimento — Comissões por Recebimento

## Objetivo

Validar o mapeamento de documentos financeiros a processos, o cálculo de TCMP e FCMP, e o cálculo de comissões para adiantamentos e pagamentos regulares.

## Módulos Testados

- `src/recebimento/core/process_mapper.py` → `ProcessMapper`
- `src/recebimento/core/comissao_calculator.py` → `ComissaoCalculator`
- `src/recebimento/core/metricas_calculator.py` → `MetricasCalculator`
- `src/recebimento/io/analise_financeira_loader.py` → `AnaliseFinanceiraLoader`

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 6** — Cálculo de Comissões por Recebimento

## Fórmulas

```
TCMP = Σ(taxa_item × valor_item) / Σ(valor_total_itens)
FCMP = Σ(FC_item × valor_item) / Σ(valor_total_itens)

Adiantamento (COT):  comissão = valor_pago × TCMP × 1.0
Pagamento Regular:   comissão = valor_pago × TCMP × FCMP_aplicado
```

## Regras de Mapeamento

- Documento iniciando com `"COT"` → Adiantamento, processo = sufixo numérico
- Demais documentos → Pagamento Regular, match dos 5-6 primeiros dígitos com `Numero NF` na AC
- Somente `Tipo de Baixa = 'B'` entra no cálculo

## Testes Planejados

### Grupo A — Mapeamento de Documentos

| ID | Teste | Entrada | Resultado Esperado |
|----|-------|---------|-------------------|
| 06.A1 | `test_mapeamento_cot_adiantamento` | Documento="COT12345" | tipo=ADIANTAMENTO, processo="12345" |
| 06.A2 | `test_mapeamento_nf_pagamento_regular` | Documento="123456" (match com NF na AC) | tipo=PAGAMENTO_REGULAR, processo correto |
| 06.A3 | `test_mapeamento_documento_sem_match` | Documento="999999" (sem NF correspondente) | Documento ignorado / sem match |
| 06.A4 | `test_filtro_tipo_baixa` | Registros com Tipo de Baixa = 'B' e 'C' | Somente 'B' passa o filtro |

### Grupo B — TCMP e FCMP

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 06.B1 | `test_tcmp_dois_itens` | Item A: V=10000, taxa=5%; Item B: V=5000, taxa=3% | TCMP = (500+150)/15000 = 4.33% |
| 06.B2 | `test_fcmp_processo_faturado` | 2 itens com FC_A=1.0, FC_B=0.85, ponderados por valor | FCMP = (10000×1.0 + 5000×0.85) / 15000 = 0.95 |
| 06.B3 | `test_fcmp_processo_nao_faturado` | Processo com status "Em Andamento" | FCMP = 1.0 (provisório) |

### Grupo C — Cálculo de Comissão

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 06.C1 | `test_comissao_adiantamento` | V=8000, TCMP=0.0433, FC=1.0 | Comissão = 8000 × 0.0433 × 1.0 = R$ 346,40 |
| 06.C2 | `test_comissao_regular` | V=8000, TCMP=0.0433, FCMP=0.95 | Comissão = 8000 × 0.0433 × 0.95 = R$ 329,08 |

## Fixtures Necessários (subpasta `fixtures/`)

- `analise_financeira.csv` — Documentos financeiros (5-6 registros: COTs + NFs + tipo C)
- `analise_comercial.csv` — Processos e itens (2-3 processos com diferentes status)

## Cálculos Manuais

- **TCMP:** `(5% × 10000 + 3% × 5000) / (10000 + 5000) = 650 / 15000 = 0.04333...`
- **FCMP:** `(1.0 × 10000 + 0.85 × 5000) / (10000 + 5000) = 14250 / 15000 = 0.95`
- **Adiantamento:** `8000 × 0.04333 × 1.0 = 346.67` (arredondamento depende da implementação)
- **Regular:** `8000 × 0.04333 × 0.95 = 329.33` (verificar arredondamento)

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
