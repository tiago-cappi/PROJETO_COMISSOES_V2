# 📋 PLANO MESTRE DE TESTES — ROBÔ DE COMISSÕES V1

> **Versão:** 1.0  
> **Data de Criação:** Março/2026  
> **Status:** Estrutura criada — Testes pendentes de implementação  
> **Escopo:** Backend apenas (fluxo principal V1 com FC/escada/recebimento/devolução)

---

## 📌 OBJETIVO

Criar uma suíte completa de testes unitários e de integração que valide **todas** as regras e lógicas de negócio do Robô de Comissões (fluxo V1). Os testes devem:

1. Cobrir cada regra de negócio documentada em `documentacoes/DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`
2. Usar dados de fixtures CSV que espelham a estrutura real dos arquivos de entrada e configuração
3. Produzir resultados previsíveis e calculados manualmente para validação
4. Servir como base de regressão para futuras alterações no backend

---

## 🚨 PROTOCOLO OBRIGATÓRIO DE CRIAÇÃO DE TESTES (CRÍTICO)

### Regra de Ouro: VALIDAR ANTES DE IMPLEMENTAR

**Antes de escrever qualquer arquivo de teste**, o agente de IA **deve obrigatoriamente** executar o seguinte protocolo:

### Passo 1 — Apresentação ao Usuário

Para **cada pasta de testes** que será implementada, o agente deve apresentar ao usuário:

1. **Compreensão da Lógica de Negócio:**
   - Explicar em linguagem clara qual regra de negócio será testada
   - Citar a fórmula ou algoritmo exato envolvido
   - Referenciar a seção correspondente da documentação (`DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`)
   - Indicar quais arquivos do código-fonte implementam essa lógica

2. **Dados Exatos de Teste:**
   - Listar os valores numéricos exatos que serão usados nos CSVs de fixture
   - Mostrar a estrutura dos DataFrames de entrada (colunas e valores por linha)
   - Detalhar os parâmetros de configuração necessários (pesos, metas, taxas, etc.)

3. **Resultados Esperados:**
   - Calcular manualmente, passo a passo, o resultado esperado de cada teste
   - Mostrar as contas intermediárias (não apenas o valor final)
   - Ex: `FC = (25% × min(90%, 1.0)) + (15% × min(106%, 1.0)) + ... = 0.935`

### Passo 2 — Aguardar Validação do Usuário

- O agente **DEVE PARAR** e esperar a confirmação do usuário
- O agente **NÃO PODE** criar arquivos `.py` de teste antes da aprovação
- Se o usuário aprovar → proceder à implementação
- Se o usuário corrigir algo → seguir para o Passo 3

### Passo 3 — Correção de Lógica (se necessário)

Se o usuário corrigir a compreensão de alguma regra de negócio:

1. **Investigar o código atual:**
   - Localizar no código-fonte a implementação da lógica corrigida
   - Verificar se o código atual está de acordo com a correção do usuário
   
2. **Se o código estiver errado:**
   - Apresentar o problema encontrado ao usuário
   - Propor a correção do backend
   - Implementar a correção após aprovação
   - Somente então criar os testes de acordo com a lógica corrigida

3. **Se o código estiver correto:**
   - Ajustar apenas os dados/resultados esperados dos testes
   - Criar os testes de acordo com a lógica confirmada

### Passo 4 — Implementação

Somente após validação completa do Passo 2 (ou correção no Passo 3):

1. Criar os CSVs de fixture na subpasta `fixtures/` da pasta de testes
2. Criar o arquivo `.py` de testes com `pytest`
3. Executar os testes e confirmar que passam
4. Reportar resultados ao usuário

### Passo 5 — Atualização Obrigatória da Documentação (CRÍTICO)

Sempre que o usuário corrigir a compreensão de uma lógica de negócio ou solicitar modificações em como um teste deve ser realizado, o agente **DEVE imediatamente**:

1. **Atualizar o `README.md`** da pasta de testes correspondente:
   - Corrigir a descrição da lógica de negócio, fórmulas ou regras
   - Atualizar os dados de entrada e resultados esperados na tabela de testes
   - Refazer os cálculos manuais de exemplo para refletir a correção

2. **Atualizar este `PLANO_TESTES.md`** (documento mestre):
   - Se a correção afeta fórmulas de referência → atualizar a seção "Fórmulas de Referência"
   - Se a correção afeta o escopo/descrição de uma pasta → atualizar a tabela "Mapa de Testes por Módulo"
   - Se a correção revela novas regras não documentadas → adicionar na seção apropriada

3. **Manter consistência entre documentos:**
   - O `PLANO_TESTES.md` e o `README.md` de cada pasta **nunca** podem conter informações contraditórias
   - A documentação deve **sempre** refletir o estado atual e correto das regras de negócio
   - Se uma correção do usuário invalidar testes já implementados em outras pastas, o agente deve **sinalizar** quais testes precisam ser revisados

> **Regra:** A documentação é tão importante quanto o código de teste. Testes com documentação desatualizada são considerados incompletos.

### Diagrama do Protocolo

```
┌─────────────────────────────┐
│  1. Agente estuda a lógica  │
│     de negócio e o código   │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  2. Apresenta ao usuário:   │
│     - Compreensão da lógica │
│     - Dados exatos          │
│     - Resultados esperados  │
│     (com cálculos manuais)  │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  3. PARAR e AGUARDAR        │
│     validação do usuário    │
└──────────────┬──────────────┘
               ▼
        ┌──────┴──────┐
        │  Aprovado?  │
        └──┬───────┬──┘
       Sim │       │ Não
           ▼       ▼
    ┌──────────┐  ┌──────────────────────┐
    │ Criar    │  │ Investigar o código  │
    │ testes   │  │ atual e corrigir o   │
    └──────────┘  │ backend se necessário│
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │ Apresentar correção  │
                  │ ao usuário e só      │
                  │ então criar testes   │
                  └──────────────────────┘
```

---

## 🏗️ ESTRUTURA DE PASTAS

```
tests/
├── conftest.py                              # Fixtures globais (paths, helpers)
├── pytest.ini                               # Configuração pytest
├── PLANO_TESTES.md                          # ESTE DOCUMENTO
│
├── unit/                                    # Testes unitários por módulo
│   ├── test_01_config_loader/               # Carga e validação de regras
│   │   ├── README.md                        # Documentação dos testes desta pasta
│   │   ├── fixtures/                        # CSVs espelhando abas do REGRAS_COMISSOES
│   │   └── test_config_loader.py            # Arquivo de testes (a criar)
│   │
│   ├── test_02_normalization/               # Normalização de texto e atingimento
│   │   ├── README.md
│   │   └── test_normalization.py
│   │
│   ├── test_03_fc_calculation/              # FC em rampa + escada por cargo
│   │   ├── README.md
│   │   ├── fixtures/
│   │   └── test_fc_calculation.py
│   │
│   ├── test_04_commission_rules/            # Taxa de rateio, fatia, split, hierarquia
│   │   ├── README.md
│   │   ├── fixtures/
│   │   └── test_commission_rules.py
│   │
│   ├── test_05_cross_selling/               # Detecção + Opções A e B
│   │   ├── README.md
│   │   ├── fixtures/
│   │   └── test_cross_selling.py
│   │
│   ├── test_06_recebimento/                 # TCMP, FCMP, adiantamentos, regulares
│   │   ├── README.md
│   │   ├── fixtures/
│   │   └── test_recebimento.py
│   │
│   ├── test_07_reconciliacao/               # Detecção + cálculo de ajuste
│   │   ├── README.md
│   │   ├── fixtures/
│   │   └── test_reconciliacao.py
│   │
│   ├── test_08_devolucao/                   # Fator de devolução + estorno proporcional
│   │   ├── README.md
│   │   ├── fixtures/
│   │   └── test_devolucao.py
│   │
│   ├── test_09_currency/                    # Validação, conversão, cálculo YTD
│   │   ├── README.md
│   │   └── test_currency.py
│   │
│   └── test_10_atribuicao/                  # Motor unificado REGRAS_ATRIBUICAO: per-collaborator search
│       ├── README.md
│       ├── fixtures/
│       └── test_atribuicao.py
│
└── integration/                             # Testes de integração ponta a ponta
    ├── test_11_faturamento_e2e/             # Fluxo completo por faturamento
    │   ├── README.md
    │   ├── fixtures/
    │   └── test_faturamento_e2e.py
    │
    ├── test_12_recebimento_e2e/             # Fluxo completo por recebimento
    │   ├── README.md
    │   ├── fixtures/
    │   └── test_recebimento_e2e.py
    │
    └── test_13_devolucao_e2e/               # Fluxo completo de devoluções
        ├── README.md
        ├── fixtures/
        └── test_devolucao_e2e.py
```

---

## 📊 ESTRUTURA DOS ARQUIVOS DE ENTRADA (COLUNAS REAIS)

### Análise Comercial Completa

Fonte: `dados_entrada/Analise_Comercial_Completa.xlsx` (ou `.csv`)

```
Processo, Status Processo, Numero NF, Dt Emissão, Data Aceite,
Valor Realizado, Valor Orçado, Consultor Interno, Representante-pedido,
Gerente Comercial-Pedido, Negócio, Grupo, Subgrupo, Tipo de Mercadoria,
Aplicação Mat./Serv., Cliente, Nome Cliente, Cidade, UF,
Código Produto, Descrição Produto, Qtde Atendida, Operação,
Fabricante, Centro Custo-pedido
```

### Análise Financeira

Fonte: `dados_entrada/Análise Financeira.xlsx`

```
Documento, Valor Líquido, Data de Baixa, Tipo de Baixa
```

### Devoluções

Fonte: `dados_entrada/Devoluções.xlsx`

```
Código Operação, Data de Entrada, Valor Produtos, Num docorigem
```

### Rentabilidade Agrupada

Fonte: `dados_entrada/rentabilidades/rentabilidade_MM_YYYY_agrupada.xlsx`

```
Negócio, Grupo, Subgrupo, Tipo de Mercadoria, rentabilidade_realizada_pct
```

### REGRAS_COMISSOES.xlsx — Abas e Colunas

| Aba | Colunas |
|-----|---------|
| **PARAMS** | `chave`, `valor` |
| **COLABORADORES** | `nome_colaborador`, `cargo`, `TIPO_COMISSAO` (opcional) |
| **CARGOS** | `nome_cargo`, `TIPO_COMISSAO` (opcional: "recebimento"/"faturamento") |
| **REGRAS_ATRIBUICAO** | `linha`, `grupo`, `subgrupo`, `tipo_mercadoria`, `fabricante`, `aplicacao`, `colaborador`, `cargo`, `taxa_rateio_maximo_pct`, `fatia_cargo_pct`, `fator_split` (opc.) |
| **PESOS_METAS** | `cargo`, `faturamento_linha`, `rentabilidade`, `conversao_linha`, `faturamento_individual`, `conversao_individual`, `retencao_clientes` (opc.), `meta_fornecedor_1` (opc.), `meta_fornecedor_2` (opc.) |
| **METAS_APLICACAO** | `linha`, `grupo`, `subgrupo`, `tipo_mercadoria`, `tipo_meta` ("faturamento"/"conversao"), `valor_meta` |
| **METAS_INDIVIDUAIS** | `colaborador`, `tipo_meta` ("faturamento"/"conversao"), `valor_meta` |
| **META_RENTABILIDADE** | `linha`, `grupo`, `subgrupo`, `tipo_mercadoria`, `meta_rentabilidade_alvo_pct` |
| ~~CONFIG_COMISSAO~~ | *(eliminada — unificada em REGRAS_ATRIBUICAO)* |
| **METAS_FORNECEDORES** | `linha`, `fornecedor`/`fabricante`, `meta_anual`, `moeda` |
| **ALIASES** | `entidade`, `alias`, `padrao` |
| **FC_ESCADA_CARGOS** | `cargo`, `modo` (RAMPA/ESCADA), `num_degraus`, `piso_pct` |
| **CROSS_SELLING** | `colaborador`, `taxa_cross_selling_pct` |

---

## 🔢 FÓRMULAS DE REFERÊNCIA

### Comissão por Faturamento (por item)

```
Comissão_Potencial = Valor_Realizado × (taxa_rateio_maximo_pct / 100) × (fatia_cargo_pct / 100) × fator_split
Comissão_Final = Comissão_Potencial × FC_Aplicado
```

### Fator de Correção (FC) — Rampa

```
FC_rampa = Σ (min(Atingimento_i, cap_fc_max) × Peso_i / 100)

Onde: Atingimento_i = calcular_atingimento(Realizado_i, Meta_i)
      (se meta=0 e realizado>0 → atingimento=1.0)
      (se realizado=0 ou realizado<0 ou meta<0 ou entrada não-numérica → ValueError: cálculo abortado)
```

> **Atenção:** `calcular_atingimento()` é fail-fast. Entradas inválidas levantam `ValueError`
> e abortam o cálculo de comissões. Strings numéricas (ex: `"90000"`) são válidas.

### FC Escada

```
Se modo = RAMPA → multiplicador = FC_rampa (sem alteração)
Se modo = ESCADA:
  - degrau = floor(performance × num_degraus) (limitado a [0, num_degraus-1])
  - Se performance < piso → multiplicador = piso
  - Se performance >= 1.0 → multiplicador = 1.0
  - Senão → multiplicador = piso + degrau × (1 - piso) / (num_degraus - 1)
```

### TCMP (Taxa de Comissão Média Ponderada)

```
TCMP = Σ(taxa_item × valor_item) / Σ(valor_total_itens)
```

### FCMP (Fator de Correção Médio Ponderado)

```
FCMP_rampa = Σ(FC_item × valor_item) / Σ(valor_total_itens)
```

### Comissão por Recebimento

```
Adiantamento (COT): comissão = valor_pago × TCMP × 1.0
Pagamento Regular:  comissão = valor_pago × TCMP × FCMP_aplicado

FCMP_aplicado é o FCMP após eventual regra de escada por cargo.
Se processo NÃO FATURADO → FCMP = 1.0 (provisório)
```

### Reconciliação

```
Ajuste = Comissão_Adiantada × (FCMP_real - 1.0)

Se FCMP_real < 1.0 → ajuste negativo (débito)
Se FCMP_real = 1.0 → ajuste zero
Se FCMP_real > 1.0 → ajuste positivo (raro, depende de parâmetros)
```

### Devoluções

```
Fator_Devolução = min(Valor_Devolvido / Valor_Realizado_Processo, 1.0)
Estorno = -(Comissão_Histórica × Fator_Devolução)  →  sempre NEGATIVO
```

### Cross-Selling

```
Opção A (taxa subtraída):
  - taxa_demais = taxa_rateio - taxa_cross_selling
  - comissão_consultor = valor × taxa_cross_selling × fatia × split × FC

Opção B (taxa adicional):
  - taxa_demais = taxa_rateio (inalterada)
  - comissão_consultor = valor × taxa_cross_selling × fatia × split × FC (adicional)
```

---

## 📂 MAPA DE TESTES POR MÓDULO

### Testes Unitários

| # | Pasta | Módulo Testado | Lógica de Negócio |
|---|-------|---------------|-------------------|
| 01 | `test_01_config_loader` | `src/io/config_loader.py` | Carga de todas as abas do REGRAS_COMISSOES, parsing de PARAMS, normalização, detecção de colaboradores por recebimento |
| 02 | `test_02_normalization` | `src/utils/normalization.py` | Remoção de acentos/BOM, cálculo de atingimento (divisão segura) |
| 03 | `test_03_fc_calculation` | `calculo_comissoes.py` (`_calcular_fc_para_item`) + `src/core/fc_escada.py` | FC em rampa (soma ponderada de componentes com cap), escada por cargo (RAMPA/ESCADA), piso e degraus |
| 04 | `test_04_commission_rules` | `src/regras/atribuicao_engine.py` + `calculo_comissoes.py` (`_get_regra_comissao`) | Busca por especificidade (score), cálculo da fórmula final da comissão |
| 05 | `test_05_cross_selling` | `calculo_comissoes.py` (`_detectar_cross_selling`) | Detecção de casos elegíveis, aplicação das Opções A e B |
| 06 | `test_06_recebimento` | `src/recebimento/core/` | Mapeamento documento→processo (COT vs NF), cálculo TCMP/FCMP, comissão de adiantamento e regular |
| 07 | `test_07_reconciliacao` | `src/recebimento/reconciliacao/` | Detecção de processos elegíveis, cálculo do ajuste |
| 08 | `test_08_devolucao` | `src/devolucao/` | Fator de devolução, estorno proporcional, agrupamento por NF |
| 09 | `test_09_currency` | `src/currency/` | Validação de taxas faltantes, conversão YTD, persistência JSON |
| 10 | `test_10_atribuicao` | `src/regras/atribuicao_engine.py` | Motor unificado REGRAS_ATRIBUICAO: preprocessamento, busca por especificidade, auto-split, funções auxiliares |

### Testes de Integração

| # | Pasta | Fluxo Testado | Escopo |
|---|-------|--------------|--------|
| 11 | `test_11_faturamento_e2e` | Faturamento ponta a ponta | Carga → Realizado → FC → Regra → Comissão final (com escada e cross-selling) |
| 12 | `test_12_recebimento_e2e` | Recebimento ponta a ponta | Financeiro → Mapeamento → TCMP/FCMP → Adiantamento → Regular → Reconciliação |
| 13 | `test_13_devolucao_e2e` | Devoluções ponta a ponta | Devolução → Vinculação NF → Histórico → Estorno proporcional |

---

## 🛠️ REGRAS TÉCNICAS PARA IMPLEMENTAÇÃO

### Framework e Configuração

- **Framework:** `pytest` com fixtures parametrizadas
- **Idioma:** Documentação e docstrings em Português (BR); nomes de funções em inglês (`test_*`)
- **Fixtures CSV:** Espelham a estrutura das abas e arquivos reais, com apenas dados mínimos necessários
- **Sem chamadas externas:** Mocks para BCB/API de câmbio; sem acesso a rede

### Padrão dos Arquivos de Fixture CSV

Cada pasta de testes que precisar de dados de entrada deve ter uma subpasta `fixtures/` com CSVs nomeados de forma descritiva:

```
fixtures/
├── config_colaboradores.csv       # Espelho da aba COLABORADORES
├── config_cargos.csv              # Espelho da aba CARGOS
├── config_pesos_metas.csv         # Espelho da aba PESOS_METAS
├── analise_comercial.csv          # Espelho da AC com amostra mínima
├── analise_financeira.csv         # Espelho da AF com amostra mínima
└── ...
```

**Regras dos CSVs:**
- Devem usar **exatamente os mesmos nomes de colunas** dos arquivos reais
- Devem conter **apenas a amostra mínima** de dados necessários para testar
- Não copiar dados reais de clientes/colaboradores — usar nomes fictícios
- Cada CSV deve ser legível e autoexplicativo

### Padrão dos Arquivos de Teste

```python
# tests/unit/test_XX_nome/test_nome.py
"""
Testes unitários: [Descrição do módulo testado]

Módulo testado: [caminho do módulo]
Lógica de negócio: [breve descrição]
Referência: DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md, Seção X
"""
import pytest
import pandas as pd
from pathlib import Path

# Fixture para carregar CSVs
FIXTURES_DIR = Path(__file__).parent / "fixtures"

class TestNomeDaLogica:
    """[Docstring explicando o grupo de testes]"""
    
    def test_caso_especifico(self):
        """[Docstring explicando este teste, dados e resultado esperado]"""
        ...
```

### README.md de Cada Pasta

Cada pasta de testes deve ter um `README.md` contendo:

1. **Objetivo:** O que exatamente está sendo testado
2. **Módulos envolvidos:** Caminhos dos arquivos do código-fonte
3. **Referência de negócio:** Seção da documentação que descreve a regra
4. **Tabela de testes:** Cada teste com dados de entrada e resultado esperado
5. **Cálculos manuais:** Demonstração passo a passo dos resultados esperados

---

## 📐 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

A ordem abaixo garante que módulos base sejam testados antes dos que dependem deles:

```
1.  test_02_normalization       (sem dependências, funções puras)
2.  test_01_config_loader       (carga de dados, usado por todos)
3.  test_10_atribuicao          (motor unificado: busca per-collaborator, auto-split, auxiliares)
4.  test_09_currency            (taxas de câmbio, módulo isolado)
5.  test_03_fc_calculation      (FC — módulo central, depende de normalization)
6.  test_04_commission_rules    (regras de comissão, depende de FC)
7.  test_05_cross_selling       (detecção CS, depende de atribuições)
8.  test_06_recebimento         (TCMP/FCMP, depende de FC + regras)
9.  test_07_reconciliacao       (ajustes, depende de recebimento)
10. test_08_devolucao           (estornos, módulo semi-isolado)
11. test_11_faturamento_e2e     (integração faturamento)
12. test_12_recebimento_e2e     (integração recebimento)
13. test_13_devolucao_e2e       (integração devoluções)
```

---

## 🔍 REFERÊNCIAS DO CÓDIGO-FONTE

| Componente | Arquivo Principal | Métodos/Classes Chave |
|------------|-------------------|----------------------|
| Entry Point | `calculo_comissoes.py` | `CalculoComissao.executar()` |
| Config Loader | `src/io/config_loader.py` | `ConfigLoader.load_configs()` |
| Data Loader | `src/io/data_loader.py` | `DataLoader.load_input_data()` |
| FC Escada | `src/core/fc_escada.py` | `aplicar_fc_escada()`, `FcEscadaCargoConfig` |
| Normalização | `src/utils/normalization.py` | `normalize_text()`, `calcular_atingimento()` |
| Process Mapper | `src/recebimento/core/process_mapper.py` | `ProcessMapper.mapear_documento()` |
| Comissão Receb. | `src/recebimento/core/comissao_calculator.py` | `ComissaoCalculator.calcular_adiantamento/regular()` |
| Métricas | `src/recebimento/core/metricas_calculator.py` | `MetricasCalculator.calcular_metricas_processo()` |
| Reconciliação | `src/recebimento/reconciliacao/reconciliacao_calculator.py` | `ReconciliacaoCalculator.calcular_reconciliacao_processo()` |
| Detecção Reconc. | `src/recebimento/reconciliacao/reconciliacao_detector.py` | `ReconciliacaoDetector.detectar_processos_para_reconciliar()` |
| Devoluções | `src/devolucao/devolucao_processor.py` | `DevolucaoProcessor.processar()` |
| Dev. Cálculo | `src/devolucao/devolucao_calculator.py` | `DevolucaoCalculator.calcular_fator_devolucao()` |
| Câmbio | `src/currency/rate_calculator.py` | `RateCalculator.calcular_faturamento_convertido_ytd()` |
| Master DB | `src/io/master_db_manager.py` | `MasterDBManager.append_comissoes()` |
| State Manager | `src/recebimento/estado/state_manager.py` | `StateManager` |
| Atribuição | `src/regras/atribuicao_engine.py` | `preprocessar_regras()`, `buscar_regras_item()`, `buscar_taxa_para_cargo()` |
| FC Cálculo | `calculo_comissoes.py` | `_calcular_fc_para_item()` |
| Regra Comissão | `calculo_comissoes.py` | `_get_regra_comissao()` |
| Cross-Selling | `calculo_comissoes.py` | `_detectar_cross_selling()` |

---

## 📖 DOCUMENTAÇÃO DE REFERÊNCIA

- **Regras de negócio:** `documentacoes/DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`
- **Diagramas de fluxo:** `documentacoes/DIAGRAMAS_LOGICA_NEGOCIOS.md`
- **Fluxo completo do robô:** `documentacoes/FLUXO_COMPLETO_ROBO_COMISSOES.md`

---

> **Nota para agentes de IA:** Este documento é o ponto de partida para qualquer trabalho de criação de testes.
> Siga rigorosamente o **Protocolo Obrigatório de Criação de Testes** descrito acima.
> Na dúvida, **pergunte ao usuário** antes de assumir qualquer comportamento.
