# test_03_fc_calculation — Fator de Correção (Rampa + Escada)

## Objetivo

Validar o cálculo do Fator de Correção (FC), que é a média ponderada dos atingimentos de cada meta, e a sua transformação opcional em multiplicador por escada/rampa por cargo.

## Módulos Testados

- `calculo_comissoes.py` → `_calcular_fc_para_item()`
- `src/core/fc_escada.py` → `aplicar_fc_escada()`, `load_fc_escada_cargos()`, `FcEscadaCargoConfig`

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seções 5.3 e 5.4** — Cálculo do FC, Cap Máximo, Escada por Cargo

## Fórmulas

```
FC_rampa = Σ (min(Realizado_i / Meta_i, cap) × Peso_i / 100)

Escada (modo ESCADA):
  Se performance < piso → mult = piso
  Se performance >= 1.0 → mult = 1.0
  Senão → degrau = floor(performance × num_degraus)
         mult = piso + degrau × (1 - piso) / (num_degraus - 1)

Escada (modo RAMPA):
  mult = performance (sem alteração)
```

## Testes Planejados

### Grupo A — FC em Rampa

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 03.A1 | `test_fc_rampa_all_100pct` | Todas as metas atingidas 100%, cap=1.0 | FC = 1.0 |
| 03.A2 | `test_fc_rampa_partial_performance` | Performance mista entre componentes | FC = soma ponderada < 1.0 |
| 03.A3 | `test_fc_rampa_zero_meta` | Meta de um componente = 0, realizado > 0 | Atingimento=1.0 para esse componente |
| 03.A4 | `test_fc_rampa_cap_applied` | Atingimento > 1.0 em todos os componentes | FC = 1.0 (cap aplicado) |
| 03.A5 | `test_fc_rampa_single_component_zero` | Um componente com realizado=0 | Contribuição desse componente = 0 |

### Grupo B — FC Escada por Cargo

| ID | Teste | Cenário | Resultado Esperado |
|----|-------|---------|-------------------|
| 03.B1 | `test_fc_escada_modo_rampa` | Cargo com modo=RAMPA, FC=0.82 | Multiplicador = 0.82 (sem alteração) |
| 03.B2 | `test_fc_escada_modo_escada_medio` | Cargo com ESCADA, 4 degraus, piso=0.70, FC=0.82 | Multiplicador determinado pelo degrau |
| 03.B3 | `test_fc_escada_topo` | FC=1.0, ESCADA com 4 degraus | Multiplicador = 1.0 |
| 03.B4 | `test_fc_escada_abaixo_piso` | FC=0.50, piso=0.70 | Multiplicador = 0.70 (piso) |
| 03.B5 | `test_fc_sem_config_escada` | Cargo sem entrada em FC_ESCADA_CARGOS | Multiplicador = FC_rampa (passthrough) |
| 03.B6 | `test_load_fc_escada_cargos` | Parsing da aba FC_ESCADA_CARGOS | Dict com configs corretas por cargo |

## Fixtures Necessários (subpasta `fixtures/`)

- `config_pesos_metas.csv` — Pesos por cargo (2-3 cargos)
- `config_metas_aplicacao.csv` — Metas de faturamento/conversão por linha
- `config_metas_individuais.csv` — Metas individuais por colaborador
- `config_meta_rentabilidade.csv` — Metas de rentabilidade por hierarquia
- `config_fc_escada_cargos.csv` — Configurações de escada RAMPA e ESCADA
- `faturados.csv` — Itens faturados para calcular realizados
- `conversoes.csv` — Conversões para calcular realizados
- `rentabilidade_agrupada.csv` — Rentabilidade realizada

## Cálculos Manuais

Serão detalhados no protocolo de validação (apresentação ao usuário) antes da implementação, com valores exatos por componente e cálculos passo a passo.

---

> **Status:** ⏳ Pendente — Aguardando protocolo de validação antes da criação dos testes
