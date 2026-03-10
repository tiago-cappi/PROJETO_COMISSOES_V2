# test_02_normalization — Normalização de Texto e Atingimento

## Objetivo

Validar as funções utilitárias de normalização de texto (`normalize_text`) e cálculo seguro de atingimento (`calcular_atingimento`), que são usadas em todo o sistema.

## Módulos Testados

- `src/utils/normalization.py` → `normalize_text()`, `calcular_atingimento()`

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 5.3.1** — Fórmula do Atingimento por Meta

## ⚠️ Correção de Lógica (09/Mar/2026)

A função `calcular_atingimento()` foi corrigida para adotar comportamento **fail-fast** com `ValueError`. O comportamento anterior (retornar `0.0` em exceções) foi substituído por validação estrita que **aborta o cálculo de comissões** em qualquer entrada inválida.

### Regras atualizadas:

| Condição | Comportamento |
|----------|---------------|
| `realizado == 0` | `ValueError` — realizado zero é inválido |
| `realizado < 0` | `ValueError` — valor negativo é inválido |
| `meta < 0` | `ValueError` — meta negativa é inválida |
| `meta == 0` e `realizado > 0` | Retorna `1.0` — meta atingida por definição |
| `meta > 0` | Retorna `realizado / meta` |
| Não-numérico não-conversível (ex: `"abc"`, `None`) | `ValueError` — entrada inválida |
| String numérica (ex: `"90000"`) | **Válido** — convertida para float antes do cálculo |

## Testes Planejados

### normalize_text()

| ID | Teste | Entrada | Resultado Esperado |
|----|-------|---------|-------------------|
| 02.1 | `test_normaliza_acentos` | `"José da Silva"` | `"JOSE DA SILVA"` |
| 02.2 | `test_remove_bom` | `"\ufeffNome"` | `"NOME"` |
| 02.3 | `test_string_vazia` | `""` | `""` |
| 02.4 | `test_valor_none` | `None` | `""` |
| 02.5 | `test_valor_nan_pandas` | `pd.NA`, `float('nan')` | `""` |
| 02.6 | `test_ja_normalizado` | `"JOAO"` | `"JOAO"` |
| 02.7 | `test_espacos_extras` | `"  Ana   Maria  "` | `"ANA MARIA"` |
| 02.8 | `test_valor_numerico_inteiro` | `123` | `"123"` |
| 02.9 | `test_valor_numerico_float` | `99.5` | `"99.5"` |
| 02.10 | `test_idempotente` | `"Ação & Reação"` (2x) | resultado idêntico |

### calcular_atingimento() — casos válidos

| ID | Teste | Entrada | Resultado Esperado |
|----|-------|---------|-------------------|
| 02.11 | `test_atingimento_normal` | `realizado=90000, meta=100000` | `0.9` |
| 02.12 | `test_atingimento_superacao` | `realizado=120000, meta=100000` | `1.2` |
| 02.13 | `test_meta_zero_realizado_positivo` | `realizado=50000, meta=0` | `1.0` |
| 02.14 | `test_string_numerica_valida` | `realizado="90000", meta="100000"` | `0.9` |
| 02.15 | `test_string_numerica_meta_zero` | `realizado="50000", meta="0"` | `1.0` |

### calcular_atingimento() — casos de erro (ValueError esperado)

| ID | Teste | Entrada | Resultado Esperado |
|----|-------|---------|-------------------|
| 02.ERR1 | `test_realizado_zero_raise` | `realizado=0, meta=100000` | `ValueError` |
| 02.ERR2 | `test_realizado_negativo_raise` | `realizado=-1000, meta=100000` | `ValueError` |
| 02.ERR3 | `test_meta_negativa_raise` | `realizado=90000, meta=-100` | `ValueError` |
| 02.ERR4 | `test_realizado_string_invalida_raise` | `realizado="abc", meta=100000` | `ValueError` |
| 02.ERR5 | `test_meta_string_invalida_raise` | `realizado=90000, meta="abc"` | `ValueError` |
| 02.ERR6 | `test_realizado_none_raise` | `realizado=None, meta=100000` | `ValueError` |
| 02.ERR7 | `test_meta_none_raise` | `realizado=90000, meta=None` | `ValueError` |

## Fixtures Necessários

Nenhum — todos os dados são inline (funções puras sem dependência de arquivos).

## Cálculos Manuais

- **02.11:** `90000 / 100000 = 0.9`
- **02.12:** `120000 / 100000 = 1.2` (sem cap nesta função — o cap é aplicado no FC)
- **02.13:** Meta = 0, realizado > 0 → retorna `1.0` por convenção (meta atingida por definição)
- **02.14:** `float("90000") / float("100000") = 90000.0 / 100000.0 = 0.9`
- **02.15:** `float("0") == 0` → retorna `1.0`
- **02.ERR1:** `realizado=0` → `ValueError: Valor 'realizado' não pode ser zero`
- **02.ERR2:** `realizado=-1000 < 0` → `ValueError: Valor 'realizado' não pode ser negativo`
- **02.ERR3:** `meta=-100 < 0` → `ValueError: Valor 'meta' não pode ser negativo`
- **02.ERR4:** `float("abc")` levanta `ValueError` → relançado com contexto de 'realizado'
- **02.ERR5:** `float("abc")` levanta `ValueError` → relançado com contexto de 'meta'
- **02.ERR6:** `float(None)` levanta `TypeError` → relançado como `ValueError` com contexto de 'realizado'
- **02.ERR7:** `float(None)` levanta `TypeError` → relançado como `ValueError` com contexto de 'meta'

---

> **Status:** ✅ Implementado — Lógica corrigida e testes criados em 09/Mar/2026
