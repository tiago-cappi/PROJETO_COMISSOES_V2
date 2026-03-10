# test_10_atribuicao — Motor de Atribuição Unificado (REGRAS_ATRIBUICAO)

## Objetivo

Validar o motor de atribuição unificado (`atribuicao_engine.py`): pré-processamento, busca por especificidade **com seleção per-collaborator**, cálculo automático de `fator_split`, resolução de empates e funções auxiliares.

## Módulos Testados

- `src/regras/atribuicao_engine.py` → `preprocessar_regras()`, `buscar_regras_item()`, `buscar_taxa_para_cargo()`, `colaborador_tem_atribuicao()`, `obter_linhas_colaborador()`, `validar_cobertura_hierarquias()`

## Referência de Negócio

- `documentacoes/DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 4.9** — Atribuições

## Campos Hierárquicos (6)

```
linha, grupo, subgrupo, tipo_mercadoria, fabricante, aplicacao
```

## Regra Central de Negócio (Per-Collaborator Selection)

```
TODOS os colaboradores que possuem QUALQUER regra compatível com o item
devem ser comissionados. Para cada colaborador, seleciona-se a regra mais
específica (maior score INDIVIDUAL). Colaboradores com regras genéricas
NÃO são descartados em favor de colaboradores com regras mais específicas.

Regras rate-only (sem colaborador nomeado): apenas a(s) de maior score global.
```

### Exemplo Ilustrativo

```
Regra A: linha=INDUSTRIAL (score=1) → João GL
Regra B: linha=INDUSTRIAL + grupo=EQUIPAMENTOS + subgrupo=BOMBAS (score=3) → João GL + Pedro GL
Regra C: todos campos vazios (score=0) → Roberto Dir

Item faturado: INDUSTRIAL + EQUIPAMENTOS + BOMBAS + ...

Resultado CORRETO:
  - João  → score=3 (usa Regra B, a mais específica dele)
  - Pedro → score=3 (usa Regra B, sua única compatível)
  - Roberto → score=0 (usa Regra C, sua única compatível)

Resultado INCORRETO (bug antigo):
  - Apenas João + Pedro (score=3 global descartava Roberto com score=0)
```

## Regras de Split (auto-calculado)

```
Cada regra (mesmos 6 campos hierárquicos) pode ter múltiplos colaboradores.
fator_split = 1 / count(colaboradores_mesmo_cargo_mesma_regra)

Se fator_split explícito na planilha → usar valor fornecido.
```

---

## Fixture: `fixtures/regras_atribuicao.csv` (12 linhas)

| Row | linha | grupo | subgrupo | tipo_mercadoria | fabricante | aplicacao | colaborador | cargo | taxa | fatia | split |
|-----|-------|-------|----------|-----------------|------------|-----------|-------------|-------|------|-------|-------|
| 1 | INDUSTRIAL | EQUIPAMENTOS | BOMBAS | CENTRIFUGAS | KSB | SANEAMENTO | João Silva | Gerente Linha | 5.0 | 100 | (auto=1.0) |
| 2 | INDUSTRIAL | EQUIPAMENTOS | BOMBAS | CENTRIFUGAS | KSB | SANEAMENTO | Maria Souza | Coordenador | 3.0 | 100 | (auto=1.0) |
| 3 | INDUSTRIAL | EQUIPAMENTOS | BOMBAS | | | | João Silva | Gerente Linha | 4.0 | 100 | (auto=0.5) |
| 4 | INDUSTRIAL | EQUIPAMENTOS | BOMBAS | | | | Pedro Lima | Gerente Linha | 4.0 | 100 | (auto=0.5) |
| 5 | INDUSTRIAL | | | | | | Ana Costa | Gerente Linha | 3.0 | 100 | 0.7 (explícito) |
| 6 | INDUSTRIAL | | | | | | Lucia Reis | Gerente Linha | 3.0 | 100 | 0.3 (explícito) |
| 7 | *(vazio)* | | | | | | Roberto Neto | Diretor | 2.0 | 100 | (auto=1.0) |
| 8 | AMBIENTAL | TRATAMENTO | ETE | ESTACOES | OPERSAN | | Felipe Gomes | Gerente Linha | 5.0 | 100 | (auto=1.0) |
| 9 | INDUSTRIAL | | | | | | *(vazio)* | Consultor Interno | 2.5 | 50 | (auto=1.0) |
| 10 | *(vazio)* | | | | | | *(vazio)* | Consultor Interno | 2.0 | 50 | (auto=1.0) |
| 11 | AMBIENTAL | TRATAMENTO | | | | | Bruno Matos | Coordenador | 3.0 | 100 | (auto=1.0) |
| 12 | INDUSTRIAL | EQUIPAMENTOS | VALVULAS | | | | João Silva | Gerente Linha | 4.5 | 100 | (auto=1.0) |

### Lógica do Fixture

- **Rows 1-2:** Regra score-6 (todos 6 campos). João=GL + Maria=Coord. Cargos diferentes → split=1.0 cada.
- **Rows 3-4:** Regra score-3 (3 campos). João=GL + Pedro=GL. Mesmo cargo → split auto=0.5.
- **Rows 5-6:** Regra score-1 (só linha). Ana=GL + Lucia=GL. Split **explícito** 0.7/0.3.
- **Row 7:** Regra score-0 (global). Roberto=Diretor. Sempre compatível com qualquer item.
- **Row 8:** AMBIENTAL score-5. Felipe=GL. Para testar exclusão por linha diferente.
- **Rows 9-10:** Rate-only (sem colaborador). Duas especificidades: score-1 e score-0.
- **Row 11:** AMBIENTAL score-2. Bruno=Coord. Para `obter_linhas_colaborador`.
- **Row 12:** João em regra DIFERENTE (VALVULAS). Score-3 para contexto VALVULAS.

**João Silva aparece em 3 regras** (rows 1, 3, 12) — permite testar seleção da mais específica.

---

## Testes Implementados — 22 testes em 3 Grupos

### Grupo A — Pré-processamento (`TestPreprocessamento`, 6 testes)

#### A1: `test_preprocessar_normaliza_upper`

- **Entrada:** CSV com campos hierárquicos (já uppercase no fixture; engine aplica `.str.upper()` para garantir).
- **Dados verificados:** Row 1 (6 campos), Row 5 (1 campo), Row 8 (AMBIENTAL).
- **Resultado esperado:** `row[0]["linha"] == "INDUSTRIAL"`, `row[0]["fabricante"] == "KSB"`, `row[7]["linha"] == "AMBIENTAL"`.

#### A2: `test_preprocessar_nan_para_vazio`

- **Entrada:** Row 3 (idx=2) com tipo_mercadoria/fabricante/aplicacao vazios no CSV. Row 7 (idx=6) com TODOS vazios.
- **Resultado esperado:** Todos esses campos são `""` (string vazia), não NaN.
- **Verificação:** Loop sobre HIERARCHY_FIELDS para row 6 garante nenhum campo escapou.

#### A3: `test_preprocessar_auto_split_single`

- **Entrada:** Row 1 (João GL) e Row 2 (Maria Coord) na regra score-6.
- **Lógica:** Auto-split conta colaboradores do **mesmo cargo** na **mesma regra**. João é único GL na regra score-6. Maria é única Coord.
- **Resultado esperado:** Ambos `fator_split == 1.0`.

#### A4: `test_preprocessar_auto_split_double`

- **Entrada:** Rows 3-4: João GL + Pedro GL na regra IND|EQUIP|BOMBAS|||.
- **Lógica:** 2 colaboradores com cargo "Gerente Linha" na mesma `_regra_key` → `1/2 = 0.5`.
- **Resultado esperado:** `row[2]["fator_split"] == 0.5`, `row[3]["fator_split"] == 0.5`.

#### A5: `test_preprocessar_split_explicito`

- **Entrada:** Rows 5-6: Ana split=0.7, Lucia split=0.3 (coluna preenchida no CSV).
- **Lógica:** Quando `fator_split` já tem valor numérico, engine NÃO recalcula.
- **Resultado esperado:** `row[4]["fator_split"] == 0.7`, `row[5]["fator_split"] == 0.3`.

#### A6: `test_preprocessar_colunas_faltantes`

- **Entrada:** DataFrame com apenas 2 colunas ("linha", "colaborador").
- **Resultado esperado:** `ValueError` com mensagem "colunas obrigatórias ausentes".

---

### Grupo B — Busca por Especificidade Per-Collaborator (`TestBuscaEspecificidade`, 8 testes)

#### B1: `test_busca_retorna_todos_colaboradores_diferentes_scores` — **O TESTE CENTRAL**

- **Entrada:** Contexto `{linha: INDUSTRIAL, grupo: EQUIPAMENTOS, subgrupo: BOMBAS, tipo_mercadoria: CENTRIFUGAS, fabricante: KSB, aplicacao: SANEAMENTO}`.
- **Cálculo de scores por row:**

```
Row 1  João   GL    → 6/6 campos BATEM           → score=6  ✓ válida
Row 2  Maria  Coord → 6/6 campos BATEM           → score=6  ✓ válida
Row 3  João   GL    → 3/3 BATEM + 3 vazios       → score=3  ✓ válida
Row 4  Pedro  GL    → 3/3 BATEM + 3 vazios       → score=3  ✓ válida
Row 5  Ana    GL    → 1/1 BATE + 5 vazios        → score=1  ✓ válida
Row 6  Lucia  GL    → 1/1 BATE + 5 vazios        → score=1  ✓ válida
Row 7  Roberto Dir  → 0 campos preenchidos        → score=0  ✓ válida
Row 8  Felipe GL    → AMBIENTAL ≠ INDUSTRIAL     → EXCLUÍDA
Row 9  (rate) CI    → 1/1 BATE (INDUSTRIAL)      → score=1  ✓ válida
Row 10 (rate) CI    → 0 campos preenchidos        → score=0  ✓ válida
Row 11 Bruno  Coord → AMBIENTAL ≠ INDUSTRIAL     → EXCLUÍDA
Row 12 João   GL    → VALVULAS ≠ BOMBAS          → EXCLUÍDA
```

- **Seleção per-collaborator (melhor score individual de cada um):**

```
João Silva   → rows 1(s6) vs 3(s3) → row 1: score=6, taxa=5.0, split=1.0
Maria Souza  → row 2(s6)           → row 2: score=6, taxa=3.0, split=1.0
Pedro Lima   → row 4(s3)           → row 4: score=3, taxa=4.0, split=0.5
Ana Costa    → row 5(s1)           → row 5: score=1, taxa=3.0, split=0.7
Lucia Reis   → row 6(s1)           → row 6: score=1, taxa=3.0, split=0.3
Roberto Neto → row 7(s0)           → row 7: score=0, taxa=2.0, split=1.0
```

- **Seleção rate-only (maior score global entre rate-only):**

```
Row 9(s1) vs Row 10(s0) → row 9: score=1, taxa=2.5
```

- **Resultado esperado:** 7 resultados totais (6 nomeados + 1 rate-only), ordenados por score DESC.
- **Verificações:** Score, taxa, split de cada colaborador individualmente; lista ordenada DESC.

#### B2: `test_busca_regra_mais_especifica_individual`

- **Entrada:** Contexto `{linha: INDUSTRIAL, grupo: EQUIPAMENTOS, subgrupo: VALVULAS, ...vazio}`.
- **Cálculo:**

```
Rows 1,2   → BOMBAS≠VALVULAS     → EXCLUÍDAS
Rows 3,4   → BOMBAS≠VALVULAS     → EXCLUÍDAS
Row 5 Ana  → IND match + rest vazio → score=1
Row 6 Lucia → IND match             → score=1
Row 7 Roberto → all empty           → score=0
Row 8 Felipe → AMBIENTAL≠IND        → EXCLUÍDA
Row 9 (rate) → IND match            → score=1
Row 10 (rate) → all empty           → score=0
Row 11 Bruno → AMBIENTAL≠IND        → EXCLUÍDA
Row 12 João  → IND+EQUIP+VALVULAS match → score=3
```

- **Per-collaborator:** João(s3, taxa=4.5), Ana(s1), Lucia(s1), Roberto(s0)
- **Rate-only:** row 9(s1)
- **Resultado esperado:** 5 resultados. João usa row 12 (taxa=4.5, score=3).

#### B3: `test_busca_exclusao_mismatch_com_fallback`

- **Entrada:** Contexto `{...fabricante: SULZER...}` (KSB→SULZER mismatch).
- **Cálculo:**

```
Rows 1,2 → KSB≠SULZER → EXCLUÍDAS (Maria perde TODAS as regras válidas)
Row 3 João → 3/3 match + 3 empty → score=3
Row 4 Pedro → score=3
(Ana, Lucia score=1; Roberto score=0; row 9 rate score=1)
Row 12 João → VALVULAS≠BOMBAS → EXCLUÍDA
```

- **Resultado esperado:** 6 resultados. **Maria NÃO aparece.** João cai para score=3 (taxa=4.0, split=0.5).

#### B4: `test_busca_generica_fallback_score_0`

- **Entrada:** Contexto `{linha: QUIMICA, grupo: ESPECIAL, ...vazio}`.
- **Cálculo:** Todas as regras com campos preenchidos são excluídas (INDUSTRIAL≠QUIMICA, AMBIENTAL≠QUIMICA). Restam apenas rows com campos vazios:

```
Row 7  Roberto Dir → score=0
Row 10 (rate) CI   → score=0
```

- **Resultado esperado:** 2 resultados, ambos score=0.

#### B5: `test_busca_dataframe_vazio_retorna_lista_vazia`

- **Entrada:** DataFrame vazio (0 rows).
- **Resultado esperado:** `[]` (retorno imediato).

#### B6: `test_busca_filtro_cargo_gerente_linha`

- **Entrada:** Contexto full (score-6), `cargo_filtro="Gerente Linha"`.
- **Cálculo:** Todos os scores são iguais a B1, mas filtro cargo remove Maria(Coord), Roberto(Dir), rate-only(CI).
- **Resultado esperado:** 4 resultados: João(s6), Pedro(s3), Ana(s1), Lucia(s1). Todos cargo="Gerente Linha".

#### B7: `test_busca_rate_only_maior_score`

- **Entrada:** Contexto full, `cargo_filtro="Consultor Interno"`.
- **Cálculo:** Row 9 (rate-only, score=1, taxa=2.5) vence Row 10 (score=0, taxa=2.0). Nenhum colaborador nomeado tem cargo CI.
- **Resultado esperado:** 1 resultado, taxa=2.5, score=1, fatia=50.0.

#### B8: `test_busca_resolver_empate_por_colaborador`

- **Entrada:** DataFrame inline com 2 regras distintas para "Carlos Nunes" GL:
  - Regra X: linha=INDUSTRIAL, grupo="" → score=1
  - Regra Y: linha="", grupo=EQUIPAMENTOS → score=1
- **Contexto:** `{linha: INDUSTRIAL, grupo: EQUIPAMENTOS, ...vazio}` → ambas score=1 para Carlos.
- **Mock resolver_empate:** Retorna sempre a primeira `_regra_key`.
- **Resultado esperado:** `resolver_empate` chamado 1× com score=1 e 2 regras distintas. Carlos aparece 1 vez com taxa=3.0 (regra X).

---

### Grupo C — Funções Auxiliares (`TestFuncoesAuxiliares`, 8 testes)

#### C1: `test_colaborador_tem_atribuicao_true`

- **Entrada:** nome="João Silva", que existe em rows 1, 3, 12.
- **Resultado esperado:** `True`.

#### C2: `test_colaborador_tem_atribuicao_false`

- **Entrada:** nome="Zé Ninguém", inexistente.
- **Resultado esperado:** `False`.

#### C3: `test_colaborador_tem_atribuicao_por_linha`

- **Entrada:** nome="Felipe Gomes", presente apenas na linha AMBIENTAL (row 8).
- **Resultado esperado:** `True` para linha="AMBIENTAL", `False` para linha="INDUSTRIAL".

#### C4: `test_obter_linhas_colaborador`

- **Entrada:** nome="João Silva" — rows 1, 3, 12 todas com linha=INDUSTRIAL.
- **Resultado esperado:** `["INDUSTRIAL"]` (sem duplicatas).

#### C4b: `test_obter_linhas_colaborador_multiplas`

- **Entrada:** DataFrame inline com "Carlos" em 2 linhas (INDUSTRIAL + AMBIENTAL).
- **Resultado esperado:** `sorted() == ["AMBIENTAL", "INDUSTRIAL"]`.

#### C5: `test_buscar_taxa_para_cargo`

- **Entrada:** Contexto full, cargo="Consultor Interno".
- **Cálculo:** `buscar_regras_item` com cargo_filtro retorna row 9 (score=1, taxa=2.5). `buscar_taxa_para_cargo` pega `[0]`.
- **Resultado esperado:** `{taxa: 2.5, fatia: 50.0, split: 1.0}`.

#### C6: `test_buscar_taxa_para_cargo_sem_match`

- **Entrada:** cargo="Estagiario" (inexistente).
- **Resultado esperado:** `None`.

#### C7: `test_validar_cobertura_ok`

- **Entrada:** Hierarquia `(INDUSTRIAL, EQUIPAMENTOS, BOMBAS, CENTRIFUGAS, KSB, SANEAMENTO)`. Cargos gestão: `["Gerente Linha", "Coordenador", "Diretor"]`.
- **Cálculo:** Busca retorna João(GL), Maria(Coord), Pedro(GL), Ana(GL), Lucia(GL), Roberto(Dir) — todos gestores nomeados.
- **Resultado esperado:** Lista vazia (nenhum problema).

#### C8: `test_validar_cobertura_gap`

- **Entrada:** Hierarquia `(QUIMICA, ESPECIAL, "", "", "", "")`. Cargos gestão: `["Gerente Linha", "Coordenador"]` (**Diretor propositalmente excluído**).
- **Cálculo:** Busca retorna Roberto(Diretor, score=0) + rate-only(CI). Nenhum é GL/Coord.
- **Resultado esperado:** Lista com 1 problema, hierarquia == `(QUIMICA, ESPECIAL, "", "", "", "")`.

---

## Estrutura de Arquivos

```
tests/unit/test_10_atribuicao/
├── README.md                          ← Este arquivo
├── fixtures/
│   └── regras_atribuicao.csv          ← 12 linhas de test data
└── test_atribuicao.py                 ← 3 classes, 22 testes
```

## Comando de Execução

```bash
python -m pytest tests/unit/test_10_atribuicao/ -v --tb=short
```

---

> **Status:** ✅ Implementado — 22 testes (6 prep + 8 busca + 8 auxiliares)
