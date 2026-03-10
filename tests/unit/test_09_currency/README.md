# test_09_currency — Taxas de Câmbio

## Objetivo

Validar o módulo de taxas de câmbio: identificação de taxas faltantes, leitura/escrita do JSON de taxas, e cálculo do faturamento convertido YTD.

## Módulos Testados

- `src/currency/rate_validator.py` → `RateValidator`
- `src/currency/rate_calculator.py` → `RateCalculator`
- `src/currency/rate_storage.py` → `RateStorage`

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 11** — Taxas de Câmbio

## Fórmulas

```
Faturamento_Convertido_YTD = Σ(valor_brl_mensal × taxa_cambio_mensal)
para meses de janeiro até o mês de apuração.

Meta_YTD = Meta_Anual × (mês_apuração / 12)
```

## Testes Planejados

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 09.1 | `test_identificar_taxas_faltantes` | JSON com Jan-Set preenchido, moeda USD, mês_final=10 | Faltante: `(USD, 2025, 10)` |
| 09.2 | `test_sem_taxas_faltantes` | JSON completo para todos os meses necessários | Lista vazia |
| 09.3 | `test_faturamento_convertido_ytd` | Jan=R$50k×5.0 + Fev=R$60k×5.1 + Mar=R$40k×5.05 | Total = 250000 + 306000 + 202000 = R$ 758.000 (convertido) |
| 09.4 | `test_storage_save_and_load` | Salvar taxa USD/2025/10=5.20 e ler de volta | Leitura retorna 5.20 |
| 09.5 | `test_mes_sem_taxa_pulado` | Mês 3 sem taxa no JSON, meses 1 e 2 com taxa | Soma apenas meses 1 e 2 |

## Fixtures Necessários

Nenhum CSV — usa JSON temporário (criado e destruído pelo teste) e dados inline.

## Cálculos Manuais

- **09.3:** `(50000 × 5.0) + (60000 × 5.1) + (40000 × 5.05) = 250000 + 306000 + 202000 = 758000`

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
