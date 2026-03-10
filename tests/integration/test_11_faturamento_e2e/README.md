# test_11_faturamento_e2e — Integração: Faturamento Ponta a Ponta

## Objetivo

Validar o fluxo completo de cálculo de comissões por faturamento, desde a carga de dados até a geração das comissões finais, integrando todos os módulos unitários: config, atribuições, realizado, FC, regras, escada e cross-selling.

## Módulos Integrados

- `src/io/config_loader.py` (carga de regras)
- `src/io/data_loader.py` (carga de dados operacionais)
- `calculo_comissoes.py`:
  - `_calcular_realizado()` (agregação de valores)
  - `_get_meta()` (busca de metas)
  - `_calcular_fc_para_item()` (FC em rampa)
  - `_get_regra_comissao()` (busca de regras)
  - `_calcular_comissoes()` (loop de itens)
  - `_detectar_cross_selling()` (detecção de CS)
- `src/core/fc_escada.py` (escada por cargo)

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seções 5 e 7** — Cálculo por Faturamento + Cross-Selling

## Fluxo Integrado

```
Carga de Regras + Dados
  → Calcular Realizados (por linha, individual)
  → Para cada item faturado:
      → Buscar Atribuição (wide-format)
      → Buscar Regra de Comissão (hierarquia + fallback)
      → Calcular FC (rampa: metas × pesos)
      → Aplicar Escada por Cargo (se configurado)
      → Aplicar Fórmula: V × taxa × fatia × split × FC_aplicado
      → Tratar Cross-Selling se aplicável
  → Gerar lista de comissões
```

## Testes Planejados

| ID | Teste | Cenário | O que valida |
|----|-------|---------|-------------|
| 11.1 | `test_fluxo_1_item_1_colaborador` | Processo simples com 1 item e 1 colaborador responsável | Caminho básico completo, sem escada nem CS |
| 11.2 | `test_fluxo_multiplos_itens_taxas_diferentes` | 2 itens com taxas/fatias diferentes | Comissões calculadas individualmente por item |
| 11.3 | `test_fluxo_fc_parcial` | Metas parcialmente atingidas | FC < 1.0, comissão proporcional |
| 11.4 | `test_fluxo_com_escada` | Cargo com modo=ESCADA | FC transformado em degrau |
| 11.5 | `test_fluxo_com_cross_selling_opcao_a` | Processo com CS detectado, decisão=A | Taxa reduzida para Time, taxa CS para consultor |
| 11.6 | `test_fluxo_com_cross_selling_opcao_b` | Processo com CS detectado, decisão=B | Taxa integral + taxa CS adicional |
| 11.7 | `test_fluxo_com_split_gerente` | 2 gerentes compartilhando cargo | Comissão dividida pelo fator_split |

## Fixtures Necessários (subpasta `fixtures/`)

Conjunto completo simulando o ambiente mínimo do robô:

- `config_params.csv` — Parâmetros de execução
- `config_colaboradores.csv` — Colaboradores (5-6 incluindo consultor externo)
- `config_cargos.csv` — Cargos (3-4 tipos)
- `config_atribuicoes.csv` — Atribuições wide-format (3-4 linhas)
- `config_pesos_metas.csv` — Pesos por cargo
- `config_metas_aplicacao.csv` — Metas de faturamento/conversão por linha
- `config_metas_individuais.csv` — Metas individuais
- `config_meta_rentabilidade.csv` — Metas de rentabilidade
- `config_comissao.csv` — Regras de comissão (taxa/fatia)
- `config_fc_escada_cargos.csv` — Configuração de escada
- `config_cross_selling.csv` — Elegibilidade CS
- `faturados.csv` — Itens faturados para o cálculo
- `conversoes.csv` — Conversões
- `rentabilidade_agrupada.csv` — Rentabilidade realizada

## Cálculos Manuais

Serão realizados teste a teste no momento da implementação, passo a passo, como parte do protocolo obrigatório de validação com o usuário.

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
