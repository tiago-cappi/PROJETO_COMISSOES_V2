# test_05_cross_selling — Detecção e Opções A/B

## Objetivo

Validar a detecção automática de casos de cross-selling e a aplicação correta das duas opções de distribuição de comissão (A: taxa subtraída, B: taxa adicional).

## Módulos Testados

- `calculo_comissoes.py` → `_detectar_cross_selling()`, `_calcular_comissoes()` (tratamento de cross-selling)

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 7** — Lógica de Cross-Selling

## Condições para Detecção de Cross-Selling

Um caso só é aberto quando **todas** as condições são verdadeiras:
1. A coluna `Gerente Comercial-Pedido` está preenchida no item
2. O nome corresponde a um colaborador do tipo **Consultor Externo**
3. Esse consultor **não possui atribuição** na aba ATRIBUICOES para a linha do item
4. O consultor está cadastrado na aba **CROSS_SELLING** com `taxa_cross_selling_pct > 0`

## Testes Planejados

### Grupo A — Detecção

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 05.A1 | `test_detectar_cs_consultor_externo_sem_atribuicao` | Item com GC-Pedido = consultor externo sem atribuição na linha + presente em CROSS_SELLING | Caso detectado com taxa correta |
| 05.A2 | `test_nao_detectar_cs_com_atribuicao` | GC-Pedido é consultor externo mas tem atribuição na linha | Sem caso de CS |
| 05.A3 | `test_nao_detectar_cs_sem_config_cross_selling` | Consultor externo sem atribuição, mas **sem** entrada na aba CROSS_SELLING | Sem caso de CS |
| 05.A4 | `test_nao_detectar_cs_campo_vazio` | `Gerente Comercial-Pedido` vazio | Sem caso de CS |
| 05.A5 | `test_cs_somente_itens_sem_atribuicao` | Processo com 3 itens, apenas 1 em linha não atribuída ao consultor | Somente 1 item marcado como CS |

### Grupo B — Aplicação das Opções

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 05.B1 | `test_opcao_a_taxa_subtraida` | Processo com CS, decisão="A", taxa=5%, taxa_cs=1% | Taxa efetiva para demais = 4%, consultor recebe sobre 1% |
| 05.B2 | `test_opcao_b_taxa_adicional` | Processo com CS, decisão="B", taxa=5%, taxa_cs=1% | Taxa para demais = 5% (inalterada), consultor recebe 1% adicional |

## Fixtures Necessários (subpasta `fixtures/`)

- `faturados.csv` — Itens faturados (2 processos: 1 com CS, 1 sem)
- `config_colaboradores.csv` — Colaboradores (inclui consultor externo)
- `config_cargos.csv` — Cargos (inclui "Consultor Externo")
- `config_atribuicoes.csv` — Atribuições por hierarquia
- `config_cross_selling.csv` — Elegibilidade e taxa do consultor

## Cálculos Manuais

Serão detalhados no protocolo de validação antes da implementação.

- **Opção A:** `comissão_demais = V × (taxa - taxa_cs) × fatia × split × FC`
- **Opção B:** `comissão_demais = V × taxa × fatia × split × FC` + `comissão_consultor = V × taxa_cs × fatia_cs × FC`

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
