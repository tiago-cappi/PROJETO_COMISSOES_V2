# test_13_devolucao_e2e — Integração: Devoluções Ponta a Ponta

## Objetivo

Validar o fluxo completo de processamento de devoluções, desde o carregamento do arquivo de devoluções até a gravação dos estornos negativos no banco de dados histórico.

## Módulos Integrados

- `src/devolucao/devolucao_loader.py` (carga e filtros)
- `src/devolucao/devolucao_calculator.py` (fator e estorno)
- `src/devolucao/devolucao_processor.py` (orquestrador)
- `src/io/master_db_manager.py` (persistência — mockado)

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 9.2** — Devoluções de Itens

## Fluxo Integrado

```
Devoluções.xlsx (filtradas por mês/ano)
  → Remove sem Num docorigem e valor ≤ 0
  → Agrupa múltiplas devoluções da mesma NF
  → Para cada NF devolvida:
      → Vincula NF → Processo via Análise Comercial
      → Busca comissões históricas no Master DB (FATURAMENTO, REGULAR, ADIANTAMENTO)
      → Fator = devolvido / valor_realizado_processo (cap 1.0)
      → Para cada colaborador: estorno = -(comissão_histórica × fator)
  → Persiste no Master DB como Tipo_Comissao = "DEVOLUCAO"
```

## Testes Planejados

| ID | Teste | Cenário | O que valida |
|----|-------|---------|-------------|
| 13.1 | `test_fluxo_devolucao_simples` | 1 devolução, 1 NF, 2 colaboradores com comissão | Estornos negativos proporcionais corretos para ambos |
| 13.2 | `test_devolucao_multiplas_mesma_nf` | 2 devoluções para a mesma NF (agrupadas) | Fator calculado sobre soma total devolvida |
| 13.3 | `test_devolucao_sem_historico` | NF existe na AC mas sem comissões no Master DB | Nenhum estorno gerado (com aviso/log) |
| 13.4 | `test_devolucao_nf_inexistente` | NF da devolução não encontrada na AC | Sem vinculação, registro ignorado |
| 13.5 | `test_registros_invalidos_isolados` | Mix: registros válidos + sem NF + valor zero | Somente válidos processados |

## Fixtures Necessários (subpasta `fixtures/`)

- `devolucoes.csv` — Devoluções (6-8 registros variados)
- `analise_comercial.csv` — Processos com NFs referenciadas (2-3 processos, vários itens)
- `historico_comissoes.csv` — Mock de comissões históricas pagas (FATURAMENTO/REGULAR)

## Cálculos Manuais — Exemplo Cenário 13.1

```
Devolução: NF=123456, Valor_Devolvido = R$ 25.000
Processo vinculado: PROC-001, Valor_Realizado = R$ 100.000
Fator = 25000 / 100000 = 0.25

Comissões históricas do Processo PROC-001:
  - Vendedor "Ana": R$ 2.000 (FATURAMENTO)
  - Gerente "João": R$ 500 (FATURAMENTO)

Estornos:
  - Ana: -(2000 × 0.25) = -R$ 500,00
  - João: -(500 × 0.25) = -R$ 125,00

Total estornado: -R$ 625,00
```

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
