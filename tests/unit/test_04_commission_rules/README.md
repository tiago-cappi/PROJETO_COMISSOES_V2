# test_04_commission_rules — Regras de Comissão (Taxa, Fatia, Split)

## Objetivo

Validar a busca por especificidade de regras de comissão via `REGRAS_ATRIBUICAO`, o cálculo final da comissão por faturamento, e o cache de regras.

## Módulos Testados

- `src/regras/atribuicao_engine.py` → `buscar_taxa_para_cargo()`, `buscar_regras_item()`
- `calculo_comissoes.py` → `_get_regra_comissao()`, `_calcular_comissoes()` (parcial)

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seções 4.2, 4.3 e 5.5** — Taxas de Rateio, Fatias por Cargo, Fórmula Final

## Fórmula

```
Comissão = Valor_Realizado × (taxa_rateio_maximo_pct / 100) × (fatia_cargo_pct / 100) × fator_split × FC_aplicado
```

## Busca por Especificidade (Score)

```
Para cada campo hierárquico (linha, grupo, subgrupo, tipo_mercadoria, fabricante, aplicacao):
  - campo VAZIO na regra     → genérico, score += 0
  - campo PREENCHIDO e BATE  → score += 1
  - campo PREENCHIDO e NÃO bate → regra EXCLUÍDA

Regra com maior score vence. Empate → resolver_empate (terminal ou programático).
```

## Testes Planejados

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 04.1 | `test_regra_exact_match` | Busca com 6 campos hierárquicos preenchidos (score=6) | Retorna regra exata com taxa e fatia corretas |
| 04.2 | `test_regra_fallback_generico` | Sem match exato, existe regra genérica (campos vazios) | Retorna regra genérica (score=1) |
| 04.3 | `test_regra_especificidade_media` | Regra com 3 campos match + regra com 1 campo match | Vence a de score 3 |
| 04.4 | `test_regra_exclusao_mismatch` | Regra com campo preenchido que NÃO bate | Regra excluída |
| 04.5 | `test_regra_nao_encontrada` | Hierarquia e cargo sem nenhuma regra aplicável | Retorna `None` |
| 04.6 | `test_formula_comissao_basica` | V=10000, taxa=5%, fatia=40%, split=1.0, FC=0.97 | R$ 194,00 |
| 04.7 | `test_formula_com_split` | V=10000, taxa=5%, fatia=40%, split=0.5, FC=1.0 | R$ 100,00 |
| 04.8 | `test_cache_regras_funciona` | Busca mesma regra 2× consecutivas | Segundo resultado vem do cache |

## Fixtures Necessários (subpasta `fixtures/`)

- `regras_atribuicao.csv` — Espelho de REGRAS_ATRIBUICAO com 8-10 linhas (específicas + genéricas, vários cargos)

## Cálculos Manuais

- **04.6:** `10000 × 0.05 × 0.40 × 1.0 × 0.97 = 194.00`
- **04.7:** `10000 × 0.05 × 0.40 × 0.5 × 1.0 = 100.00`

---

> **Status:** ⏳ Pendente — README atualizado para arquitetura REGRAS_ATRIBUICAO
