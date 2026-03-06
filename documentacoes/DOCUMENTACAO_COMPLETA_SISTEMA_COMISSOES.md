# 📚 DOCUMENTAÇÃO COMPLETA DO SISTEMA DE COMISSÕES

> **Versão:** 1.1  
> **Data:** Março/2026  
> **Status:** Documento Mestre auditado contra o fluxo principal atual do projeto

---

## 📋 ÍNDICE

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura e Fluxo de Dados](#2-arquitetura-e-fluxo-de-dados)
3. [Documentos de Entrada](#3-documentos-de-entrada)
4. [Motor de Regras de Negócio](#4-motor-de-regras-de-negócio)
5. [Cálculo de Comissões por Faturamento](#5-cálculo-de-comissões-por-faturamento)
6. [Cálculo de Comissões por Recebimento](#6-cálculo-de-comissões-por-recebimento)
7. [Lógica de Cross-Selling](#7-lógica-de-cross-selling)
8. [Adiantamentos e Reconciliação](#8-adiantamentos-e-reconciliação)
9. [Devoluções e Saldos Negativos](#9-devoluções-e-saldos-negativos)
10. [Módulo de Rentabilidade](#10-módulo-de-rentabilidade)
11. [Taxas de Câmbio](#11-taxas-de-câmbio)
12. [Interface de Gestão (Frontend)](#12-interface-de-gestão-frontend)
13. [Implementações Futuras](#13-implementações-futuras)
14. [Glossário de Termos](#14-glossário-de-termos)

---

## 1. VISÃO GERAL DO SISTEMA

### 1.1 Propósito

O **Sistema de Comissões** é uma solução automatizada que transforma dados brutos de vendas e pagamentos em valores precisos de remuneração variável para colaboradores. O sistema elimina erros de cálculo manual e garante total conformidade com regras de negócio configuráveis.

### 1.2 Principais Benefícios

- **Automação completa** do cálculo de comissões
- **Transparência total** em cada etapa do cálculo
- **Flexibilidade** através de regras configuráveis
- **Auditabilidade** com rastreamento completo de cada valor
- **Consistência** na aplicação de regras de negócio

### 1.3 Dois Fluxos de Pagamento

O sistema processa dois fluxos distintos de comissionamento:

| Fluxo | Momento do Pagamento | Descrição |
|-------|---------------------|-----------|
| **Por Faturamento** | Na emissão da Nota Fiscal | Comissão paga quando o processo é faturado |
| **Por Recebimento** | Quando o cliente paga | Comissão paga proporcionalmente aos pagamentos recebidos |

No fluxo por faturamento, o sistema calcula um **FC em rampa** por item e, quando houver configuração por cargo, converte esse resultado em um **multiplicador final de escada**.

No fluxo por recebimento, o sistema calcula **TCMP** e **FCMP** por processo e por colaborador, reaproveitando a lógica do faturamento para os itens do processo quando ele já está faturado.

---

## 2. ARQUITETURA E FLUXO DE DADOS

### 2.1 Diagrama do Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           JORNADA DOS DADOS                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

   📥 ENTRADA                    ⚙️ PROCESSAMENTO                    📤 SAÍDA
   ─────────────                 ─────────────────                   ──────────
                                          
   ┌──────────────────┐     ┌─────────────────────────┐      ┌──────────────────┐
   │ Análise Comercial│────▶│  Motor de Preparação    │      │  Relatório de    │
   │ (Processos)      │     │  (Validação e Limpeza)  │      │  Comissões por   │
   └──────────────────┘     └───────────┬─────────────┘      │  Faturamento     │
                                        │                     └──────────────────┘
   ┌──────────────────┐                 ▼                            ▲
   │ Análise          │     ┌─────────────────────────┐              │
   │ Financeira       │────▶│  Motor de Mapeamento    │              │
   │ (Pagamentos)     │     │  (Vincula Pagamentos    │              │
   └──────────────────┘     │   aos Processos)        │              │
                            └───────────┬─────────────┘              │
   ┌──────────────────┐                 ▼                            │
   │ REGRAS_          │     ┌─────────────────────────┐      ┌───────┴──────────┐
   │ COMISSOES.xlsx   │────▶│  Motor de Cálculo       │─────▶│  Relatório de    │
   │ (Configurações)  │     │  de Comissões           │      │  Comissões por   │
   └──────────────────┘     └───────────┬─────────────┘      │  Recebimento     │
                                        │                     └──────────────────┘
   ┌──────────────────┐                 ▼                            ▲
   │ Arquivos de      │     ┌─────────────────────────┐              │
   │ Rentabilidade    │────▶│  Motor de Reconciliação │──────────────┘
   │ (Mensais)        │     │  (Ajustes)              │      ┌──────────────────┐
   └──────────────────┘     └─────────────────────────┘      │  Painel de       │
                                                      ──────▶│  Estado dos      │
   ┌──────────────────┐                                      │  Processos       │
   │ Taxas de Câmbio  │                                      └──────────────────┘
   │ (Mensais)        │                                      
   └──────────────────┘                                      ┌──────────────────┐
                                                             │  Saldos          │
   ┌──────────────────┐                                      │  Negativos       │
   │ Devoluções.xlsx  │─────────────────────────────────────▶│  (Reconciliação  │
   │                  │                                      │   + Devoluções)  │
   └──────────────────┘                                      └──────────────────┘
```

### 2.2 Etapas do Processamento

1. **Carga e validação:** Leitura do `REGRAS_COMISSOES.xlsx`, arquivos auxiliares e dados operacionais.
2. **Pré-processamento mensal:** Geração e normalização de bases como faturados, conversões e YTD.
3. **Cálculo de realizados:** Consolidação dos realizados de faturamento, conversão, rentabilidade e fornecedores.
4. **Detecção de cross-selling:** Identificação antecipada de processos que dependem de decisão do usuário.
5. **Cálculo por faturamento:** Comissão item a item com taxa, fatia, split e FC aplicado.
6. **Cálculo por recebimento:** Processamento de adiantamentos e pagamentos regulares com estado persistente por processo.
7. **Reconciliação:** Ajuste de adiantamentos após o faturamento do processo.
8. **Pós-processamento:** Persistência no banco histórico, devoluções e geração de saídas.

---

## 3. DOCUMENTOS DE ENTRADA

### 3.1 Análise Comercial Completa

Planilha contendo todos os processos de venda do período.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| Número do Processo | Identificador único da venda |
| Cliente | Nome/razão social do comprador |
| Dt Emissão / Data de Emissão | Data de emissão da Nota Fiscal |
| Status Processo | Estado atual (Em Andamento, Pendente, FATURADO) |
| Numero NF | Número da Nota Fiscal |
| Negócio / Linha de Negócio | Categoria principal do produto |
| Grupo | Subcategoria do produto |
| Subgrupo | Divisão mais específica |
| Tipo de Mercadoria | Classificação final do item |
| Valor Realizado | Valor efetivamente faturado do item |
| Valor Orçado | Valor usado como referência para processos ainda não faturados no fluxo de recebimento |
| Código Produto / Descrição Produto | Identificação do item faturado |
| Gerente Comercial-Pedido | Campo usado pelo motor de cross-selling para detectar participação externa |

### 3.2 Análise Financeira

Planilha contendo todos os pagamentos recebidos no período.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| Documento | Código do documento de pagamento |
| Valor Líquido | Valor efetivamente recebido |
| Data de Baixa | Data considerada para a apuração do recebimento |
| Tipo de Baixa | Indicador usado para filtrar apenas baixas válidas |

**Identificação de Adiantamentos:**
- Documentos que começam com **"COT"** são adiantamentos (pagamentos antes do faturamento)
- Demais documentos são tratados como pagamentos regulares e são vinculados à venda via número da NF

**Filtros aplicados no fluxo atual:**
- Apenas registros com **`Tipo de Baixa = B`** entram no cálculo
- A data usada para filtro mensal é **`Data de Baixa`**
- O vínculo documento → processo não vem pronto na planilha; ele é reconstruído pelo motor de recebimento

### 3.3 Arquivo de Regras de Negócio (REGRAS_COMISSOES.xlsx)

Arquivo mestre contendo todas as configurações do sistema. Detalhado na seção 4.

### 3.4 Arquivos de Rentabilidade

Arquivos mensais localizados na pasta `dados_entrada/rentabilidades/`.

**Formato esperado no fluxo principal:** `*MM*AAAA*agrupada*.xlsx`

**Conteúdo:** Rentabilidade realizada agregada por hierarquia de produto (`Negócio`, `Grupo`, `Subgrupo`, `Tipo de Mercadoria`).

**Propósito:** Alimentar diretamente o componente de rentabilidade do FC. O cálculo principal **não** consolida CSV bruto em tempo de execução; ele espera um arquivo mensal já agregado.

### 3.5 Taxas de Câmbio

O projeto mantém taxas médias mensais em `data/currency_rates/monthly_avg_rates.json`.

**Uso:** Converter metas de fornecedores em moedas estrangeiras (USD, EUR) para Reais no cálculo do componente de fornecedores do FC.

**Observação operacional:** antes do cálculo, o fluxo principal pode identificar moedas faltantes a partir de `config/METAS_FORNECEDORES.csv` e completar o JSON via integração com serviço de câmbio.

---

## 4. MOTOR DE REGRAS DE NEGÓCIO

### 4.1 Estrutura do Arquivo REGRAS_COMISSOES.xlsx

O arquivo de regras contém múltiplas abas. No fluxo principal auditado, as mais relevantes são:

- **ATRIBUICOES:** definição de responsáveis por hierarquia de produto
- **PESOS_METAS:** pesos do FC por cargo
- **COLABORADORES / CARGOS:** identificação de cargos e elegibilidade por recebimento
- **METAS_FORNECEDORES:** metas anuais por linha, fornecedor e moeda
- **PARAMS:** parâmetros operacionais como caps do FC
- **FC_ESCADA_CARGOS:** regra opcional de escada/rampa por cargo
- **CROSS_SELLING:** elegibilidade e taxa do consultor externo

### 4.2 Taxas de Rateio (Taxa de Comissão)

**Definição:** Percentual **máximo** de comissão que pode ser pago para determinada categoria de produto.

**Hierarquia de Categorias:**
```
Linha de Negócio
    └── Grupo
        └── Subgrupo
            └── Tipo de Mercadoria
```

**Exemplo:**
| Linha | Grupo | Subgrupo | Tipo Mercadoria | Taxa de Rateio |
|-------|-------|----------|-----------------|----------------|
| Ambiental | Equipamentos | Bombas | Submersível | 5% |
| Analítica | Instrumentos | Medidores | pH | 4% |

**Importante:** A Taxa de Rateio representa o valor **total** a ser dividido entre todos os colaboradores responsáveis pela venda. Não é o que cada um recebe individualmente.

### 4.3 Fatias por Cargo (Percentual de Elegibilidade - PE)

**Definição:** Como a Taxa de Rateio é dividida entre os diferentes cargos envolvidos na venda.

**Exemplo:**
| Cargo | Fatia (PE) |
|-------|------------|
| Gerente Comercial | 40% |
| Vendedor | 35% |
| Consultor Técnico | 25% |
| **TOTAL** | **100%** |

**Cálculo Individual:**
```
Comissão do Colaborador = Valor Item × Taxa de Rateio × Fatia do Cargo × FC
```

**Observação importante do estado atual:** além da fatia do cargo, o fluxo principal também pode aplicar **`fator_split`** quando a atribuição do cargo é compartilhada entre duas pessoas (por exemplo, gerente/coordenador 1 e 2).

### 4.4 Metas de Faturamento

**Definição:** Valor alvo de processos que tiveram **emissão de Nota Fiscal** no mês de apuração.

**Unidade de Medida:** Reais (R$)

**Níveis:**
| Nível | Descrição |
|-------|-----------|
| Meta de Linha | Objetivo coletivo para toda a linha de negócio |
| Meta Individual | Objetivo pessoal de cada colaborador |

**Exemplo:**
| Linha | Meta Mensal |
|-------|-------------|
| Ambiental | R$ 500.000 |
| Analítica | R$ 350.000 |

| Colaborador | Meta Individual |
|-------------|-----------------|
| João Silva | R$ 80.000 |
| Maria Santos | R$ 100.000 |

### 4.5 Metas de Conversão

**Definição:** Valor alvo de processos **convertidos em vendas confirmadas** no mês de apuração.

**Diferença Crucial:** Um processo pode ser convertido (venda confirmada) em um mês, mas só ser faturado (NF emitida) em meses futuros.

**Unidade de Medida:** Reais (R$)

**Níveis:** Linha e Individual (mesma estrutura das metas de faturamento)

### 4.6 Metas de Rentabilidade

**Definição:** Margem de lucro esperada para cada categoria de produto.

**Unidade de Medida:** Percentual (%)

**Características no fluxo atual:**
- O atingimento bruto pode ficar acima de 100%
- A contribuição final desse componente para o FC segue o mesmo cap configurado em `PARAMS` para os demais componentes

**Exemplo:**
| Linha | Grupo | Meta Rentabilidade |
|-------|-------|-------------------|
| Ambiental | Equipamentos | 25% |
| Analítica | Reagentes | 40% |

### 4.7 Metas de Fornecedores

**Definição:** Valor anual de compras de fornecedores estratégicos.

**Moeda:** Pode ser em moeda estrangeira (USD, EUR, etc.)

**Conversão:** O sistema converte o realizado YTD por fornecedor usando a taxa média mensal armazenada no JSON de câmbio.

**Regra operacional atual:** a meta anual é convertida em **meta YTD proporcional ao mês de apuração** antes da comparação com o realizado.

**Exemplo:**
| Fornecedor | Meta Anual | Moeda |
|------------|------------|-------|
| Fornecedor A | $500.000 | USD |
| Fornecedor B | €200.000 | EUR |

### 4.8 Pesos das Metas

**Definição:** Importância relativa de cada componente no cálculo do Fator de Correção.

Os pesos são lidos **por cargo**. O fluxo principal atualmente suporta os seguintes componentes, conforme disponibilidade de peso e dados:

- Faturamento da Linha
- Faturamento Individual
- Conversão da Linha
- Conversão Individual
- Rentabilidade
- Retenção de Clientes (aplicada na prática a `Gerente Linha`)
- Meta Fornecedor 1
- Meta Fornecedor 2

**Exemplo de Distribuição:**
| Componente | Peso |
|------------|------|
| Faturamento da Linha | 25% |
| Faturamento Individual | 15% |
| Conversão da Linha | 15% |
| Conversão Individual | 10% |
| Rentabilidade | 20% |
| Retenção de Clientes | 10% |
| Metas de Fornecedores | 5% |
| **TOTAL** | **100%** |

### 4.9 Atribuições

**Definição:** Mapeamento de qual colaborador é responsável por quais categorias de produto.

**Aba:** `ATRIBUICOES` no arquivo de regras

**Estrutura lógica observada no projeto:**
- Hierarquia por linha, grupo, subgrupo e tipo de mercadoria
- Possibilidade de formato “wide”, com múltiplos ocupantes por cargo
- Suporte a `fator_split` para divisão de comissão em cargos compartilhados

**Uso Principal:**
- Determinar quem recebe comissão por cada item
- Identificar itens de cross-selling
- Identificar divisões internas do mesmo cargo

---

## 5. CÁLCULO DE COMISSÕES POR FATURAMENTO

### 5.1 Visão Geral

Colaboradores que recebem por faturamento têm suas comissões calculadas no momento em que a Nota Fiscal do processo é emitida.

### 5.2 Fluxo de Cálculo por Item

Para **cada item** vendido dentro de um processo:

```
1. IDENTIFICAR CONTEXTO
   └── Determinar: Linha + Grupo + Subgrupo + Tipo de Mercadoria

2. LOCALIZAR TAXA DE RATEIO
   └── Buscar no arquivo de regras a taxa aplicável à categoria

3. IDENTIFICAR COLABORADORES
   └── Verificar na aba ATRIBUICOES quem é responsável, incluindo splits de cargo quando aplicável

4. CALCULAR FATOR DE CORREÇÃO (FC)
   └── Para cada colaborador, calcular o FC em rampa pelos componentes habilitados

5. APLICAR REGRA FINAL POR CARGO
   └── Se houver configuração em FC_ESCADA_CARGOS, transformar o FC em rampa no multiplicador final

6. APLICAR FÓRMULA
   └── Comissão = Valor Realizado × Taxa Rateio Ajustada × Fatia Cargo × Fator Split × FC Aplicado
```

### 5.3 Cálculo do Fator de Correção (FC)

O FC representa o desempenho do colaborador em relação às metas estabelecidas.

#### 5.3.1 Fórmula do Atingimento por Meta

```
Atingimento = Valor Realizado / Valor da Meta
```

#### 5.3.2 Fórmula do FC (Média Ponderada)

```
FC_rampa = Σ ( min(Atingimento de cada Meta, Cap do Componente) × Peso da Meta )
```

Depois disso, o sistema calcula o **multiplicador final aplicado na comissão**:

- Se o cargo estiver sem configuração específica, o multiplicador final é o próprio `FC_rampa`
- Se o cargo estiver em modo `RAMPA` na aba `FC_ESCADA_CARGOS`, o multiplicador final continua sendo o `FC_rampa`
- Se o cargo estiver em modo `ESCADA`, o sistema converte o `FC_rampa` para um degrau discreto conforme piso e número de degraus configurados

**Exemplo de Cálculo:**

| Meta | Peso | Realizado | Meta | Atingimento | Contribuição |
|------|------|-----------|------|-------------|--------------|
| Faturamento Linha | 25% | R$ 450.000 | R$ 500.000 | 90% | 22,5% |
| Faturamento Individual | 15% | R$ 85.000 | R$ 80.000 | 106% → **100%** | 15% |
| Conversão Linha | 15% | R$ 380.000 | R$ 400.000 | 95% | 14,25% |
| Rentabilidade | 20% | 28% | 25% | 112% → **100%** | 20% |
| ... | ... | ... | ... | ... | ... |

**FC em rampa calculado:** Soma das contribuições = 22,5% + 15% + 14,25% + 20% + ... = **97%**

**Componentes hoje suportados no fluxo principal:**
- Faturamento da linha
- Faturamento individual
- Conversão da linha
- Conversão individual
- Rentabilidade
- Retenção de clientes
- Meta fornecedor 1
- Meta fornecedor 2

### 5.4 Regras Críticas do Fator de Correção

#### 5.4.1 TETO MÁXIMO CONFIGURÁVEL DO FC EM RAMPA

- **Regra atual:** O FC em rampa é limitado pelo parâmetro `cap_fc_max`
- **Padrão observado no projeto:** `cap_fc_max = 1.0`
- **Implicação:** Com a configuração padrão, não há bônus por superação no fluxo principal

#### 5.4.2 SEM PISO MÍNIMO

- **Regra de negócio:** O desempenho ruim reduz o multiplicador final
- **Observação técnica:** no modo `ESCADA`, a regra respeita o piso configurado para o cargo; no modo `RAMPA`, o valor segue diretamente a performance calculada

#### 5.4.3 REGRA DE ESCADA POR CARGO

- **Regra atual do código:** a aba `FC_ESCADA_CARGOS` pode definir, por cargo:
   - `modo = RAMPA` ou `ESCADA`
   - `num_degraus`
   - `piso_pct`
- **Sem tolerância:** no modo `ESCADA`, o avanço de degrau usa corte exato; não existe regra operacional de `95% = 100%` no fluxo principal auditado
- **Topo da escada:** o multiplicador máximo (`1.0`) só ocorre quando a performance em rampa atinge pelo menos `1.0`

**Exemplo conceitual de escada:**
| FC em Rampa | Configuração do Cargo | Multiplicador Aplicado |
|-------------|-----------------------|------------------------|
| 0,82 | RAMPA | 0,82 |
| 0,82 | ESCADA com 4 degraus | Depende do degrau atingido |
| 1,00 | ESCADA | 1,00 |

### 5.5 Fórmula Final da Comissão por Faturamento

```
Comissão Potencial = Valor Realizado do Item × Taxa de Rateio Ajustada × Fatia do Cargo × Fator Split
Comissão Final = Comissão Potencial × FC Aplicado
```

**Onde:**
- **Valor Realizado do Item:** Valor monetário efetivamente faturado
- **Taxa de Rateio Ajustada:** Percentual máximo da categoria, eventualmente reduzido por cross-selling na opção A
- **Fatia do Cargo:** Percentual que o cargo do colaborador recebe
- **Fator Split:** Fração aplicada quando o mesmo cargo é compartilhado
- **FC Aplicado:** Multiplicador final após rampa e eventual escada por cargo

**Exemplo Numérico:**

| Componente | Valor |
|------------|-------|
| Valor do Item | R$ 10.000 |
| Taxa de Rateio | 5% |
| Fatia (Gerente) | 40% |
| Fator Split | 100% |
| FC Aplicado | 97% |
| **Comissão** | R$ 10.000 × 5% × 40% × 100% × 97% = **R$ 194,00** |

---

## 6. CÁLCULO DE COMISSÕES POR RECEBIMENTO

### 6.1 Visão Geral

Colaboradores que recebem por recebimento têm suas comissões calculadas quando o cliente efetua o pagamento, não no momento do faturamento.

O fluxo atual é orquestrado por um módulo dedicado de recebimento, com:

- carga filtrada da Análise Financeira
- mapeamento documento → processo
- estado persistente em `Estado_Processos_Recebimento.xlsx`
- cálculo separado para adiantamentos, pagamentos regulares e reconciliações

### 6.2 Desafio: Múltiplos Itens com Taxas Diferentes

Um único processo pode conter vários itens, cada um com:
- Taxa de Rateio diferente
- FC diferente (colaboradores diferentes)

**Solução:** Usar médias ponderadas pelo valor de cada item.

Além disso, o cálculo é feito **por colaborador elegível para recebimento**, não apenas por processo agregado.

### 6.3 TCMP - Taxa de Comissão Média Ponderada

**Definição:** Média das taxas de comissão do processo, ponderada pelo valor de cada item.

**Fórmula:**
```
TCMP = Σ (Taxa do Item × Valor do Item) / Σ (Valor Total dos Itens)
```

**Exemplo:**

| Item | Valor | Taxa |
|------|-------|------|
| Item A | R$ 10.000 | 5% |
| Item B | R$ 5.000 | 3% |
| **Total** | **R$ 15.000** | - |

```
TCMP = (5% × 10.000 + 3% × 5.000) / 15.000
TCMP = (500 + 150) / 15.000
TCMP = 650 / 15.000
TCMP = 4,33%
```

### 6.4 FCMP - Fator de Correção Médio Ponderado

**Definição:** Média dos Fatores de Correção do processo, ponderada pelo valor de cada item.

**Fórmula:**
```
FCMP = Σ (FC do Item × Valor do Item) / Σ (Valor Total dos Itens)
```

**Exemplo:**

| Item | Valor | FC |
|------|-------|-----|
| Item A | R$ 10.000 | 100% |
| Item B | R$ 5.000 | 85% |
| **Total** | **R$ 15.000** | - |

```
FCMP_rampa = (100% × 10.000 + 85% × 5.000) / 15.000
FCMP_rampa = (10.000 + 4.250) / 15.000
FCMP_rampa = 14.250 / 15.000
FCMP_rampa = 95%
```

Se o cargo do colaborador tiver configuração de escada, o sistema também calcula um **FCMP aplicado** a partir do `FCMP_rampa`.

### 6.5 Regras do FCMP

- **Processo não faturado:** FCMP é forçado para `1.0`
- **Processo faturado:** FCMP é recalculado item a item usando a mesma lógica de FC do faturamento
- **Escada por cargo:** o recebimento pode usar `FCMP_APLICADO` quando houver configuração de `FC_ESCADA_CARGOS`
- **Teto operacional padrão:** com `cap_fc_max = 1.0`, o `FCMP_rampa` tende a ficar no máximo em `1.0`

### 6.6 Cálculo por Pagamento

**Fórmula:**
```
Adiantamento = Valor Recebido × TCMP × 1,0
Pagamento Regular = Valor Recebido × TCMP × FCMP aplicado
```

**Exemplo:**

| Componente | Valor |
|------------|-------|
| Pagamento Recebido | R$ 8.000 |
| TCMP do Processo | 4,33% |
| FCMP Aplicado do Processo | 95% |
| **Comissão** | R$ 8.000 × 4,33% × 95% = **R$ 329,08** |

### 6.7 Condições para Cálculo do FCMP

| Status do Processo | FCMP Utilizado | Motivo |
|-------------------|----------------|--------|
| Em Andamento / Pendente / Orçamento | 1.0 (provisório) | O processo ainda não consolidou o FC real |
| FATURADO | FCMP real calculado | Os itens já podem reaproveitar a lógica de FC do faturamento |

### 6.8 Regras Operacionais Importantes do Fluxo de Recebimento

1. **Filtro financeiro:** somente registros com `Tipo de Baixa = B` e `Data de Baixa` no mês/ano de apuração entram no cálculo.
2. **Mapeamento de adiantamento:** documentos `COT...` são tratados como adiantamento; o sufixo numérico identifica o processo.
3. **Mapeamento de pagamento regular:** para documentos não `COT`, o sistema extrai os 5/6 primeiros dígitos numéricos e compara com `Numero NF` da Análise Comercial, com normalização de zeros à esquerda.
4. **Base de valor do processo no estado:**
   - se o processo ainda não está faturado, usa-se a soma do **Valor Orçado**
   - se o processo está faturado, usa-se a soma do **Valor Realizado**
5. **Persistência de estado:** o sistema mantém totais pagos, comissão acumulada, saldo a receber e métricas por processo em arquivo próprio de estado.

---

## 7. LÓGICA DE CROSS-SELLING

### 7.1 Definição

Cross-selling ocorre quando um único processo de venda envolve produtos de **múltiplas linhas de negócio**, exigindo colaboração entre especialistas de diferentes áreas.

### 7.2 Detecção Automática

**Regra de Identificação:**

No fluxo atual, um caso de cross-selling só é aberto quando **todas** as condições abaixo são verdadeiras:

1. A coluna `Gerente Comercial-Pedido` está preenchida em algum item do processo
2. O nome informado corresponde a um colaborador do tipo **Consultor Externo**
3. Esse consultor **não possui atribuição** para a linha do item
4. O consultor está cadastrado na aba/configuração de **CROSS_SELLING**

Ou seja: o preenchimento da coluna, sozinho, **não basta** para gerar caso elegível no motor.

### 7.3 Identificação dos Itens de Cross-Selling

**Processo:**
1. Verificar o nome na coluna `Gerente Comercial-Pedido`
2. Para cada item do processo, consultar a aba `ATRIBUICOES`
3. Identificar quais itens **NÃO** estão atribuídos a esse colaborador
4. Se não possuir atribuição para a linha do item, o processo é tratado como caso elegível de cross-selling

**Exemplo:**

| Processo 001 | Gerente Comercial-Pedido: João Silva |
|--------------|-------------------------------------|

| Item | Linha | Atribuído a João? | É Cross-Selling? |
|------|-------|-------------------|------------------|
| Item A | Ambiental | ✅ Sim | ❌ Não |
| Item B | Analítica | ❌ Não | ✅ Sim |
| Item C | Ambiental | ✅ Sim | ❌ Não |

**Resultado:** Apenas o Item B é item de cross-selling.

### 7.4 Opções de Distribuição

Para itens identificados como cross-selling, o usuário escolhe via Frontend uma das duas opções:

#### Opção A: Taxa Subtraída

A taxa do consultor externo (Gerente Comercial-Pedido) é **subtraída** da taxa dos demais colaboradores.

**Exemplo:**
- Taxa de Rateio do Item: 5%
- Taxa do Consultor Externo: 1%
- Taxa restante para outros: 5% - 1% = 4%

#### Opção B: Taxa Adicional

A comissão do consultor externo é **adicional** - todos os colaboradores recebem suas taxas integrais.

**Exemplo:**
- Taxa de Rateio do Item: 5% (para colaboradores normais)
- Taxa do Consultor Externo: 1% (adicional)
- **Total pago:** 6%

### 7.5 Aplicação das Opções

- No fluxo principal auditado, a decisão é tratada **por processo** quando o caso é detectado
- A decisão é registrada e reaplicada na execução final do cálculo
- Na **Opção A**, a taxa de cross-selling é abatida da taxa base dos demais participantes
- Na **Opção B**, a taxa base dos demais participantes é mantida e a comissão do consultor externo é adicional

---

## 8. ADIANTAMENTOS E RECONCILIAÇÃO

### 8.1 O Que São Adiantamentos

Adiantamentos ocorrem quando o cliente paga **antes** da emissão da Nota Fiscal do processo.

**Identificação:** Documentos cujo código começa com **"COT"**

**Exemplo:**
- COT-2024-001 → É adiantamento
- NF-2024-456 → É pagamento regular

### 8.2 O Problema dos Adiantamentos

No momento do adiantamento:
- O processo ainda **não está faturado**
- As metas do período de faturamento ainda **não foram medidas**
- Portanto, o **FC real não pode ser calculado**

### 8.3 Solução: FC Provisório

**Regra:** Para adiantamentos, o sistema usa FC = 1.0 (100%) **provisoriamente**.

**Implicação:** O colaborador recebe comissão integral no momento do adiantamento.

### 8.4 Reconciliação

A reconciliação é o **ajuste** que ocorre quando finalmente conhecemos o FC real.

#### 8.4.1 Condições para Reconciliação

A reconciliação **só ocorre** quando:

1. O processo teve **ao menos um adiantamento** (documento COT)
2. O processo atingiu `Status Processo` = **FATURADO**

**Enquanto o status for diferente de FATURADO:**
- Reconciliação NÃO ocorre
- Adiantamentos permanecem com FC = 1.0

#### 8.4.2 Fórmula da Reconciliação

```
Valor da Reconciliação = Total de Comissão Adiantada × (FCMP Real - 1)
```

**Onde:**
- **Total de Comissão Adiantada:** Soma de todas as comissões pagas via COT
- **FCMP Real:** Fator de Correção Médio Ponderado calculado após faturamento, priorizando o multiplicador efetivamente aplicado ao colaborador

#### 8.4.3 Resultados Possíveis da Reconciliação

| Cenário | FCMP Real | Resultado | Significado |
|---------|-----------|-----------|-------------|
| FCMP = 1.0 | Sem diferença | Reconciliação = **R$ 0** | Sem ajuste |
| FCMP < 1.0 | Performance abaixo do adiantado | Reconciliação = **Negativo** | Colaborador deve devolver |
| FCMP > 1.0 | Só ocorre se parâmetros/métricas permitirem > 1.0 | Reconciliação = **Positivo** | Colaborador recebe complemento |

**IMPORTANTE:** No fluxo principal com configuração padrão (`cap_fc_max = 1.0`), a reconciliação tende a ser **zero ou negativa**. Porém, a fórmula do módulo de reconciliação aceita tecnicamente ajuste positivo caso o FCMP salvo ultrapasse `1.0`.

#### 8.4.4 Exemplo de Reconciliação

**Situação:**
- Adiantamento recebido: R$ 10.000
- TCMP do Processo: 5%
- FC provisório usado: 100%
- Comissão paga no adiantamento: R$ 10.000 × 5% × 100% = **R$ 500**

**Após Faturamento:**
- FCMP Real calculado: 85%

**Cálculo da Reconciliação:**
```
Reconciliação = R$ 500 × (85% - 100%)
Reconciliação = R$ 500 × (-15%)
Reconciliação = -R$ 75
```

**Resultado:** O colaborador tem um **débito de R$ 75** a ser descontado de outras comissões.

### 8.5 Estado Persistente dos Processos

O recebimento mantém um arquivo de estado com informações por processo, incluindo:

- valor total do processo
- total de adiantamentos
- total de pagamentos regulares
- comissão acumulada
- saldo a receber
- status de pagamento
- status de reconciliação
- mês/ano de faturamento
- métricas `TCMP`, `FCMP` e `FCMP_APLICADO`

Esse estado é parte central da lógica de recebimento e reconciliação no projeto atual.

---

## 9. DEVOLUÇÕES E SALDOS NEGATIVOS

### 9.1 Fontes de Saldos Negativos

O sistema gera saldos negativos de **duas fontes**:

| Fonte | Aplica-se a | Quando Ocorre |
|-------|-------------|---------------|
| **Reconciliação** | Colaboradores que recebem por recebimento | Quando processo é faturado e FCMP < 1.0 |
| **Devoluções** | Colaboradores com comissão histórica registrada no processo | Quando cliente devolve valor vinculado à NF original |

### 9.2 Devoluções de Itens (✅ Implementado)

#### 9.2.1 Arquivo de Devoluções

**Localização:** `dados_entrada/Devoluções.xlsx`

**Estrutura do Arquivo:**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `Código Operação` | Texto | Identificador interno da operação de devolução |
| `Data de Entrada` | Data | Data em que a devolução foi registrada no sistema |
| `Valor Produtos` | Numérico | Valor total dos produtos devolvidos (em R$) |
| `Num docorigem` | Texto | **CHAVE DE VINCULAÇÃO** - Número da NF original que gerou a venda |

**Observações Importantes:**
- Aproximadamente 50% dos registros podem não ter `Num docorigem` preenchido
- Registros sem `Num docorigem` são **ignorados automaticamente** (não há como vincular à venda original)
- O sistema loga quantos registros foram ignorados por falta desta informação

#### 9.2.2 Módulo de Processamento

**Localização:** `src/devolucao/`

**Arquivos do Módulo:**

| Arquivo | Responsabilidade |
|---------|------------------|
| `devolucao_loader.py` | Carrega e filtra `Devoluções.xlsx` por mês/ano de apuração |
| `devolucao_calculator.py` | Calcula fator de devolução e estornos proporcionais |
| `devolucao_processor.py` | Orquestra todo o fluxo de processamento |
| `__init__.py` | Exports públicos do módulo |

#### 9.2.3 Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO DE DEVOLUÇÕES                                  │
└─────────────────────────────────────────────────────────────────────────────┘

1. CARREGAMENTO (DevolucaoLoader)
   │
   ├── Lê arquivo: dados_entrada/Devoluções.xlsx
   ├── Filtra por Data de Entrada = mês/ano de apuração
   ├── Remove registros sem Num docorigem (com log)
   ├── Remove registros com valor ≤ 0
   └── Agrupa múltiplas devoluções da mesma NF (soma valores)
   │
   ▼
2. VINCULAÇÃO COM ANÁLISE COMERCIAL
   │
   ├── Busca Num docorigem → Numero NF na Análise Comercial
   ├── Extrai número do Processo vinculado
   └── Obtém Valor Realizado total do processo original
   │
   ▼
3. CONSULTA BANCO HISTÓRICO (HISTORICO_COMISSOES_MASTER.xlsx)
   │
   ├── Busca comissões pagas do Processo
   ├── Filtra por Tipo_Comissao = "FATURAMENTO", "REGULAR" e "ADIANTAMENTO"
   └── Recupera todos os colaboradores que receberam comissão
   │
   ▼
4. CÁLCULO DO ESTORNO PROPORCIONAL (DevolucaoCalculator)
   │
   ├── Fator_Devolução = Valor_Devolvido / Valor_Realizado_Processo
   ├── Para cada colaborador do processo:
   │   └── Estorno = Comissão_Histórica × Fator_Devolução × (-1)
   └── O estorno é NEGATIVO (débito)
   │
   ▼
5. PERSISTÊNCIA NO BANCO DE DADOS
   │
   ├── Salva no HISTORICO_COMISSOES_MASTER.xlsx
   ├── Tipo_Comissao = "DEVOLUCAO"
   ├── Origem_Correcao = "DEVOLUCAO"
   ├── Processo_Referencia = Processo original
   └── Fator_Devolucao = Fator calculado
```

#### 9.2.4 Fórmulas de Cálculo

**Fator de Devolução:**
```
Fator_Devolução = Valor_Devolvido / Valor_Realizado_Processo
```

**Estorno por Colaborador:**
```
Estorno = Comissão_Histórica_Paga × Fator_Devolução × (-1)
```

**Exemplo Prático:**

| Dado | Valor |
|------|-------|
| Valor Realizado do Processo | R$ 100.000,00 |
| Valor Devolvido | R$ 25.000,00 |
| Fator de Devolução | 0,25 (25%) |
| Comissão paga ao Vendedor | R$ 2.000,00 |
| Comissão paga ao Gerente | R$ 500,00 |
| **Estorno Vendedor** | R$ -500,00 |
| **Estorno Gerente** | R$ -125,00 |

#### 9.2.5 Regra de Proporcionalidade

**Regra Crítica:** O estorno é **PROPORCIONAL** ao valor devolvido, **NÃO** item-específico.

**Justificativa:**
- O arquivo de devoluções contém apenas o valor total devolvido por NF
- Não há granularidade de item (SKU) disponível na fonte de dados
- O cálculo usa o **valor realizado total do processo**, não apenas o item devolvido isoladamente
- A proporcionalidade garante equidade: se 25% do valor do processo foi devolvido, 25% da comissão histórica elegível é estornada

#### 9.2.6 Características do Estorno

| Característica | Descrição |
|----------------|-----------|
| **Valor** | Proporcional ao percentual devolvido sobre o valor realizado |
| **Período** | Registrado no mês de apuração da devolução (não retroativo) |
| **Distribuição** | Cada colaborador que recebeu comissão pelo processo recebe débito proporcional |
| **Tipo** | `DEVOLUCAO` (novo tipo de comissão no banco de dados) |
| **Sinal** | Sempre NEGATIVO (débito) |

#### 9.2.7 Integração no Fluxo Principal

**Momento de Execução:** O processamento de devoluções ocorre **APÓS**:
1. ✅ Cálculo de comissões de faturamento
2. ✅ Cálculo de comissões de recebimento (se aplicável)
3. ✅ Salvamento das comissões no banco de dados master

**Método:** `_processar_devolucoes()` em `calculo_comissoes.py`

**Chamada Automática:** O processamento é executado automaticamente ao final do cálculo principal, sem necessidade de ação manual.

#### 9.2.8 Colunas Adicionadas ao Banco de Dados Histórico

Para suportar o rastreamento de devoluções, as seguintes colunas foram adicionadas ao schema do `HISTORICO_COMISSOES_MASTER.xlsx`:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `Numero_NF` | Texto | Número da NF para vinculação com devoluções |
| `Origem_Correcao` | Texto | Origem do registro: `NORMAL`, `RECONCILIACAO`, `DEVOLUCAO` |
| `Processo_Referencia` | Texto | Processo original (para estornos) |
| `Fator_Devolucao` | Numérico | Fator proporcional aplicado (0.0 a 1.0) |

#### 9.2.9 Logs e Rastreabilidade

O módulo gera logs detalhados durante o processamento:

```
[DEVOLUÇÕES] Iniciando processamento de devoluções...
[DEVOLUÇÕES] Período de apuração: 12/2025
[DEVOLUÇÕES] Análise Comercial carregada: 5000 registros
[DEVOLUCAO] Devoluções carregadas: 150 linhas originais, 75 sem doc origem ignoradas, 45 devoluções válidas para 12/2025
[DEVOLUCAO] Processando devolução: NF 123456, Valor R$ 25.000,00
[DEVOLUCAO] Processo vinculado: PROC-2024-001, Valor Realizado: R$ 100.000,00
[DEVOLUCAO] Fator de devolução: 0.2500
[DEVOLUCAO] Estorno gerado para colaborador JOAO SILVA: R$ -500.00
[DEVOLUÇÕES] ✓ Processamento concluído com sucesso!
[DEVOLUÇÕES]   - Estornos gerados: 120
[DEVOLUÇÕES]   - Processos afetados: 45
[DEVOLUÇÕES]   - Valor total estornado: R$ 15.230,50
```

### 9.3 Consolidação de Saldos Negativos

#### 9.3.1 Aplicação

Os saldos negativos são registrados no banco histórico no **mês da apuração da devolução ou reconciliação** e passam a compor a visão consolidada do período.

#### 9.3.2 Página de Saldos Negativos (Frontend)

O backend já gera os lançamentos necessários para uma visão consolidada de saldos negativos, separando ao menos:

- origem da correção
- processo de referência
- colaborador afetado
- fator de devolução, quando aplicável
- valor negativo calculado

---

## 10. MÓDULO DE RENTABILIDADE

### 10.1 Propósito

Calcular o componente de rentabilidade do Fator de Correção, comparando margens de lucro esperadas versus realizadas.

### 10.2 Fluxo de Processamento no Estado Atual

```
1. PREPARAÇÃO EXTERNA / MENSAL
   └── O arquivo de rentabilidade é consolidado fora do cálculo principal

2. CARGA NO CÁLCULO PRINCIPAL
   ├── O motor procura arquivo agrupado em `dados_entrada/rentabilidades/`
   ├── Prioriza arquivo `.xlsx` com mês/ano da apuração
   └── Se não encontrar, segue com DataFrame vazio

3. USO NO FC
   └── A rentabilidade realizada da hierarquia do item é comparada à meta configurada

4. IMPACTO
   └── O componente entra na soma do `FC_rampa` conforme peso do cargo
```

### 10.3 Fórmula da Rentabilidade Média por Categoria

```
Rentabilidade Categoria = Σ (Rentabilidade Item × Valor Item) / Σ (Valor Total Itens da Categoria)
```

### 10.4 Comparação com Meta

```
Atingimento Rentabilidade = Rentabilidade Realizada / Meta de Rentabilidade
```

**Nota:** Metas de rentabilidade não possuem piso nem teto, então o atingimento pode ser qualquer valor.

**Observação do código atual:** embora o atingimento bruto possa ultrapassar 100%, a contribuição final para o FC segue o mesmo cap configurado para os componentes do FC.

---

## 11. TAXAS DE CÂMBIO

### 11.1 Propósito

Converter metas de fornecedores definidas em moedas estrangeiras para Reais, permitindo comparação com valores realizados.

### 11.2 Funcionamento

1. **Metas de fornecedores:** Definidas com moeda original e meta anual
2. **Taxas armazenadas:** Mantidas em JSON com média mensal por moeda
3. **Verificação prévia:** Antes do cálculo, o sistema identifica meses faltantes e tenta buscar as taxas necessárias
4. **Conversão do realizado:** O faturamento YTD por fornecedor é convertido mês a mês
5. **Comparação:** O realizado convertido é comparado com a meta YTD proporcional do fornecedor

### 11.3 Exemplo

| Fornecedor | Meta Anual | Moeda | Taxa Média (Jan) | Meta em R$ (Jan) |
|------------|------------|-------|------------------|------------------|
| ABC Corp | $50.000 | USD | R$ 5,00 | R$ 250.000 |

---

## 12. INTERFACE DE GESTÃO (FRONTEND)

### 12.1 Áreas Funcionais

| Seção | Funcionalidade |
|-------|----------------|
| **Regras** | Editar taxas, pesos, atribuições, metas |
| **Uploads** | Carregar planilhas de entrada |
| **Dados de Entrada** | Visualizar dados antes do processamento |
| **Executar Cálculo** | Iniciar processamento para mês/ano |
| **Resultados (Faturamento)** | Visualizar comissões por faturamento |
| **Recebimentos** | Visualizar comissões por recebimento |
| **Estado dos Processos** | Monitorar situação de cada processo |
| **Taxas de Câmbio** | Configurar conversões |
| **Saldos Negativos** | Visualizar reconciliações e devoluções |

### 12.2 Fluxo Típico do Usuário

```
1. Carregar planilha Comercial
2. Carregar planilha Financeira
3. Garantir que o arquivo mensal de Rentabilidade agrupada esteja disponível
4. Revisar dados carregados
5. Resolver casos pendentes de cross-selling, se existirem
6. Executar cálculo
6. Revisar resultados
7. Exportar relatórios
```

---

## 13. IMPLEMENTAÇÕES FUTURAS

### 13.1 Política de Comissionamento Anual (PDF)

**Descrição:** Geração de documento PDF individualizado por colaborador contendo:
- Suas atribuições (categorias de produto)
- Suas metas (faturamento, conversão, rentabilidade)
- Pesos de cada meta
- Taxas de rateio aplicáveis
- Fatia por cargo

**Propósito:** Formalizar acordo de comissionamento para assinatura do colaborador.

### 13.2 Regra de Tolerância de 95%

**Descrição:** Regra histórica de negócio segundo a qual `FC ≥ 95%` seria arredondado para `100%`.

**Status no código atual:** **não está ativa no fluxo principal auditado**. Hoje o comportamento vigente é cap do FC e, opcionalmente, aplicação de escada por cargo sem tolerância.

### 13.3 Processamento Automático de Rentabilidade

**Descrição:** Transformar a preparação da rentabilidade em etapa integrada do sistema, eliminando a necessidade de entregar previamente um arquivo agrupado pronto.

**Fluxo desejado:** Upload/entrada bruta → agregação automática → arquivo padronizado → uso no cálculo.

### 13.4 Banco de Dados Histórico de Comissões

**Status atual:** **já implementado** no projeto.

**Descrição:** Arquivo Excel acumulativo (cresce a cada mês) armazenando comissões de faturamento, adiantamentos, pagamentos regulares, reconciliações e devoluções.

**Estrutura:**
| Nível | Informações |
|-------|-------------|
| Por Processo | Número, Data, Valor Total, Status |
| Por Item | Código, Categoria, Valor, Taxa, FC, Comissão |
| Por Colaborador | Nome, Cargo, Fatia, Comissão, Mês/Ano |

**Usos:**
- Consultas históricas
- Cálculo de estornos em devoluções
- Auditoria de longo prazo
- Evitar duplicidade de pagamentos

### 13.5 PDF Detalhado por Colaborador (Auditoria)

**Descrição:** Exportação de documento PDF individual contendo:
- Todos os itens em que o colaborador participou
- Para cada item: valor, taxa, fatia, FC (detalhado por meta), cálculo final
- Totais consolidados

**Propósito:** Transparência e esclarecimento de dúvidas sobre comissões.

### 13.6 Excel com Tabela Dinâmica (Auditoria)

**Descrição:** Exportação de planilha hierárquica expansível.

**Para Faturamento:**
```
📁 Processo
   └── 📄 Item
       └── [Colaborador] Detalhes do cálculo
```

**Para Recebimento:**
```
📁 Pagamento (COT ou NF)
   └── Métricas: TCMP, FCMP, Cálculo
```

**Funcionalidade:** Linhas expansíveis (agrupamento) para drill-down.

### 13.7 Processamento de Devoluções (✅ Implementado)

**Descrição:** Documentação completa na seção 9.2.

**Arquivo de Entrada:** `dados_entrada/Devoluções.xlsx`

**Módulo:** `src/devolucao/` (loader, calculator, processor)

**Execução:** Automática ao final do cálculo de comissões.

**Resultado:** Registros com `Tipo_Comissao = DEVOLUCAO` e valores negativos no banco histórico.

### 13.8 Dashboard de Saldos Negativos

**Descrição:** Evoluir a visualização operacional dos saldos negativos a partir dos registros já gravados no banco histórico.

**Consolidação:** Reconciliações + Devoluções em uma única visão.

---

## 14. GLOSSÁRIO DE TERMOS

| Termo | Definição |
|-------|-----------|
| **Processo** | Uma venda ou negócio comercial identificado por número único |
| **Item** | Produto individual dentro de um processo |
| **Linha de Negócio** | Categoria principal de produtos (ex: Ambiental, Analítica) |
| **Grupo** | Subcategoria dentro da linha |
| **Subgrupo** | Divisão mais específica dentro do grupo |
| **Tipo de Mercadoria** | Classificação final do item |
| **Taxa de Rateio** | Comissão máxima para uma categoria, a ser dividida entre colaboradores |
| **Fatia do Cargo (PE)** | Percentual da Taxa de Rateio que cada cargo recebe |
| **Fator Split** | Fração da comissão usada quando o mesmo cargo é dividido entre dois colaboradores |
| **FC** | Resultado do cálculo de performance por metas; no projeto atual existe `FC_rampa` e, opcionalmente, um multiplicador final por escada |
| **TCMP** | Taxa de Comissão Média Ponderada de um processo |
| **FCMP** | Fator de Correção Médio Ponderado de um processo |
| **FCMP Aplicado** | Multiplicador final do recebimento após eventual regra de escada por cargo |
| **Adiantamento (COT)** | Pagamento recebido antes do faturamento |
| **Reconciliação** | Ajuste do que foi pago em adiantamento contra o FCMP real do processo após faturamento |
| **Cross-Selling** | Venda envolvendo múltiplas linhas de negócio |
| **Metas de Faturamento** | Valor em R$ de processos com NF emitida no mês |
| **Metas de Conversão** | Valor em R$ de processos convertidos em venda no mês |
| **Metas de Rentabilidade** | Margem de lucro % esperada por categoria |
| **Status FATURADO** | Indica que processo teve NF emitida e permite cálculo real do FC |
| **Estado de Recebimento** | Arquivo persistente que acompanha totais pagos, métricas e status por processo |

---

## 📎 APÊNDICES

### A. Fórmulas Resumidas

**Comissão por Faturamento:**
```
Comissão Potencial = Valor Realizado × Taxa Rateio Ajustada × Fatia Cargo × Fator Split
Comissão Final = Comissão Potencial × FC Aplicado
```

**TCMP:**
```
TCMP = Σ(Taxa × Valor) / Σ(Valor Total)
```

**FCMP:**
```
FCMP_rampa = Σ(FC do item × Valor) / Σ(Valor Total)
```

**Comissão por Recebimento:**
```
Adiantamento = Valor Pagamento × TCMP × 1,0
Pagamento Regular = Valor Pagamento × TCMP × FCMP aplicado
```

**Reconciliação:**
```
Ajuste = Comissão Adiantada × (FCMP Real - 1)
```

### B. Regras de Negócio Resumidas

1. **FC por faturamento:** é calculado em rampa por item e pode ser convertido em escada por cargo
2. **Cap do FC:** o teto operacional vem de `cap_fc_max`, hoje normalmente configurado em `1.0`
3. **Recebimento não faturado:** usa `FCMP = 1.0` provisório
4. **Reconciliação:** só ocorre para processo com adiantamento já faturado no mês correto e ainda não reconciliado
5. **Reconciliação:** no padrão atual tende a ser zero ou negativa, mas a fórmula suporta positivo se o FCMP salvo exceder `1.0`
6. **Devoluções:** o estorno é proporcional ao valor devolvido sobre o valor realizado total do processo
7. **Cross-Selling:** depende de consultor externo elegível, sem atribuição para a linha e cadastrado em CROSS_SELLING

---

> **Documento mantido por:** Equipe de Desenvolvimento  
> **Última atualização:** Março/2026  
> **Próxima revisão:** Conforme implementações futuras
