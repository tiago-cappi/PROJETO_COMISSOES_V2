# test_08_devolucao — Devoluções e Estornos Proporcionais

## Objetivo

Validar o carregamento de devoluções, o cálculo do fator de devolução, e a geração correta de estornos negativos proporcionais por colaborador.

## Módulos Testados

- `src/devolucao/devolucao_loader.py` → `DevolucaoLoader`
- `src/devolucao/devolucao_calculator.py` → `DevolucaoCalculator`
- `src/devolucao/devolucao_processor.py` → `DevolucaoProcessor` (parcial)

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 9.2** — Devoluções de Itens

## Fórmulas

```
Fator_Devolução = min(Valor_Devolvido / Valor_Realizado_Processo, 1.0)
Estorno = -(Comissão_Histórica × Fator_Devolução)   →  sempre NEGATIVO
```

## Regra de Proporcionalidade

O estorno é **proporcional ao valor devolvido sobre o valor total do processo**, não específico ao item. Se 25% do valor do processo foi devolvido, 25% da comissão histórica é estornada.

## Testes Planejados

### Grupo A — Carregamento e Filtros

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 08.A1 | `test_registro_sem_nf_ignorado` | Devolução sem `Num docorigem` | Registro ignorado |
| 08.A2 | `test_registro_valor_zero_ignorado` | Devolução com valor = 0 | Registro ignorado |
| 08.A3 | `test_filtro_mes_ano` | Devoluções de meses diferentes | Somente as do mês correto passam |
| 08.A4 | `test_agrupamento_mesma_nf` | NF 123: R$10k + NF 123: R$5k | valor_devolvido_total = R$15k |

### Grupo B — Cálculo do Fator e Estorno

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 08.B1 | `test_fator_devolucao_basico` | devolvido=25000, realizado=100000 | Fator = 0.25 |
| 08.B2 | `test_fator_devolucao_cap_1` | devolvido=150000, realizado=100000 | Fator = 1.0 (cap) |
| 08.B3 | `test_estorno_proporcional_unico` | Vendedor com comissão=R$2000, fator=0.25 | Estorno = -R$ 500 |
| 08.B4 | `test_estorno_multiplos_colaboradores` | Vendedor=R$2000 + Gerente=R$500, fator=0.25 | Vendedor=-R$500, Gerente=-R$125 |
| 08.B5 | `test_tipo_comissao_devolucao` | Resultado do estorno | `Tipo_Comissao == "DEVOLUCAO"` |
| 08.B6 | `test_devolucao_total_100pct` | devolvido == realizado, fator=1.0 | Estorno = 100% da comissão histórica |

## Fixtures Necessários (subpasta `fixtures/`)

- `devolucoes.csv` — Espelho de Devoluções.xlsx (5-6 registros: com/sem NF, valores zero, NFs duplicadas)
- `analise_comercial.csv` — Processos referenciados pelas devoluções (2-3 processos)
- `historico_comissoes.csv` — Mock do Master DB com comissões históricas

## Cálculos Manuais

- **08.B1:** `25000 / 100000 = 0.25`
- **08.B2:** `150000 / 100000 = 1.5 → cap → 1.0`
- **08.B3:** `-(2000 × 0.25) = -500.00`
- **08.B4:** `Vendedor: -(2000 × 0.25) = -500.00` | `Gerente: -(500 × 0.25) = -125.00`

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
