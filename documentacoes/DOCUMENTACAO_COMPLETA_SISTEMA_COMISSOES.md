# 📚 DOCUMENTAÇÃO COMPLETA DO SISTEMA DE COMISSÕES

> **Versão:** 1.0  
> **Data:** Dezembro/2024  
> **Status:** Documento Mestre - Fonte Única de Verdade

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

Ambos os fluxos aplicam **Fatores de Correção (FC)** baseados no desempenho do colaborador em relação às metas estabelecidas.

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
   │ Devoluções       │─────────────────────────────────────▶│  (Reconciliação  │
   │ [FUTURO]         │                                      │   + Devoluções)  │
   └──────────────────┘                                      └──────────────────┘
```

### 2.2 Etapas do Processamento

1. **Preparação:** Validação e limpeza dos dados de entrada
2. **Mapeamento:** Vinculação de pagamentos aos processos comerciais
3. **Cálculo:** Aplicação das regras de negócio para determinar comissões
4. **Reconciliação:** Ajuste de adiantamentos quando processos são faturados
5. **Consolidação:** Geração de relatórios e painéis

---

## 3. DOCUMENTOS DE ENTRADA

### 3.1 Análise Comercial Completa

Planilha contendo todos os processos de venda do período.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| Número do Processo | Identificador único da venda |
| Cliente | Nome/razão social do comprador |
| Data de Emissão | Data de emissão da Nota Fiscal |
| Status Processo | Estado atual (Em Andamento, Pendente, FATURADO) |
| Numero NF | Número da Nota Fiscal |
| Linha de Negócio | Categoria principal do produto |
| Grupo | Subcategoria do produto |
| Subgrupo | Divisão mais específica |
| Tipo de Mercadoria | Classificação final do item |
| Valor do Item | Valor monetário do item vendido |
| Gerente Comercial-Pedido | Campo que indica cross-selling quando preenchido |
| Colaboradores | Nomes dos responsáveis pela venda |

### 3.2 Análise Financeira

Planilha contendo todos os pagamentos recebidos no período.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| Documento | Código do documento de pagamento |
| Valor Líquido | Valor efetivamente recebido |
| Data de Pagamento | Data do recebimento |
| Processo Relacionado | Vínculo com o processo comercial |

**Identificação de Adiantamentos:**
- Documentos que começam com **"COT"** são adiantamentos (pagamentos antes do faturamento)
- Demais documentos são pagamentos regulares

### 3.3 Arquivo de Regras de Negócio (REGRAS_COMISSOES.xlsx)

Arquivo mestre contendo todas as configurações do sistema. Detalhado na seção 4.

### 3.4 Arquivos de Rentabilidade

Arquivos mensais localizados na pasta `dados_entrada/rentabilidades/`.

**Formato do Nome:** `rentabilidade_MM_AAAA_agrupada`

**Conteúdo:** Rentabilidade realizada (margem de lucro) de cada categoria de produto que foi faturada naquele mês.

**Propósito:** Comparar meta de rentabilidade versus realizado para cálculo do FC.

### 3.5 Taxas de Câmbio

Arquivo contendo taxas médias mensais para conversão de moedas estrangeiras.

**Uso:** Converter metas de fornecedores em moedas estrangeiras (USD, EUR) para Reais.

---

## 4. MOTOR DE REGRAS DE NEGÓCIO

### 4.1 Estrutura do Arquivo REGRAS_COMISSOES.xlsx

O arquivo de regras contém múltiplas abas, cada uma definindo um aspecto do sistema:

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

**Características Especiais:**
- **NÃO possui piso** (limite mínimo)
- **NÃO possui teto** (limite máximo)

**Exemplo:**
| Linha | Grupo | Meta Rentabilidade |
|-------|-------|-------------------|
| Ambiental | Equipamentos | 25% |
| Analítica | Reagentes | 40% |

### 4.7 Metas de Fornecedores

**Definição:** Valor anual de compras de fornecedores estratégicos.

**Moeda:** Pode ser em moeda estrangeira (USD, EUR, etc.)

**Conversão:** Sistema usa taxas de câmbio mensais para comparar realizado com meta.

**Exemplo:**
| Fornecedor | Meta Anual | Moeda |
|------------|------------|-------|
| Fornecedor A | $500.000 | USD |
| Fornecedor B | €200.000 | EUR |

### 4.8 Pesos das Metas

**Definição:** Importância relativa de cada componente no cálculo do Fator de Correção.

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

**Estrutura:**
| Colaborador | Linha | Grupo | Subgrupo | Tipo Mercadoria |
|-------------|-------|-------|----------|-----------------|
| João Silva | Ambiental | Equipamentos | Bombas | * |
| Maria Santos | Analítica | Instrumentos | * | * |

**Uso Principal:**
- Determinar quem recebe comissão por cada item
- Identificar itens de cross-selling

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
   └── Verificar na aba ATRIBUICOES quem é responsável

4. CALCULAR FATOR DE CORREÇÃO (FC)
   └── Para cada colaborador, baseado no atingimento de metas

5. APLICAR FÓRMULA
   └── Comissão = Valor Item × Taxa Rateio × Fatia Cargo × FC
```

### 5.3 Cálculo do Fator de Correção (FC)

O FC representa o desempenho do colaborador em relação às metas estabelecidas.

#### 5.3.1 Fórmula do Atingimento por Meta

```
Atingimento = Valor Realizado / Valor da Meta
```

#### 5.3.2 Fórmula do FC (Média Ponderada)

```
FC = Σ (Atingimento de cada Meta × Peso da Meta)
```

**Exemplo de Cálculo:**

| Meta | Peso | Realizado | Meta | Atingimento | Contribuição |
|------|------|-----------|------|-------------|--------------|
| Faturamento Linha | 25% | R$ 450.000 | R$ 500.000 | 90% | 22,5% |
| Faturamento Individual | 15% | R$ 85.000 | R$ 80.000 | 106% → **100%** | 15% |
| Conversão Linha | 15% | R$ 380.000 | R$ 400.000 | 95% | 14,25% |
| Rentabilidade | 20% | 28% | 25% | 112% → **100%** | 20% |
| ... | ... | ... | ... | ... | ... |

**FC Calculado:** Soma das contribuições = 22,5% + 15% + 14,25% + 20% + ... = **97%**

### 5.4 Regras Críticas do Fator de Correção

#### 5.4.1 TETO MÁXIMO: FC = 1.0 (100%)

- **Regra:** O FC **nunca** pode ultrapassar 1.0
- **Implicação:** Mesmo que o colaborador supere 100% de todas as metas, o FC máximo será 1.0
- **Motivo:** Não há bônus por superação; comissão máxima é a integral (100%)

#### 5.4.2 SEM PISO MÍNIMO

- **Regra:** O FC **não possui** limite inferior
- **Implicação:** Se metas forem severamente não atingidas, FC pode tender a zero

#### 5.4.3 REGRA DE TOLERÂNCIA: 95% = 100%

- **Regra:** Se o FC calculado for **≥ 95%**, considera-se **100%**
- **Implicação:** Colaboradores que atingem pelo menos 95% das metas recebem comissão integral
- **Penalização:** Só ocorre quando FC < 95%

**Exemplo da Regra de Tolerância:**
| FC Calculado | FC Aplicado | Resultado |
|--------------|-------------|-----------|
| 98% | 100% | Comissão integral |
| 96% | 100% | Comissão integral |
| 95% | 100% | Comissão integral |
| 94% | 94% | Penalização de 6% |
| 80% | 80% | Penalização de 20% |

### 5.5 Fórmula Final da Comissão por Faturamento

```
Comissão do Item = Valor do Item × Taxa de Rateio × Fatia do Cargo × FC
```

**Onde:**
- **Valor do Item:** Valor monetário do item vendido
- **Taxa de Rateio:** Percentual máximo de comissão da categoria
- **Fatia do Cargo:** Percentual que o cargo do colaborador recebe
- **FC:** Fator de Correção (máximo 1.0, mínimo sem limite)

**Exemplo Numérico:**

| Componente | Valor |
|------------|-------|
| Valor do Item | R$ 10.000 |
| Taxa de Rateio | 5% |
| Fatia (Gerente) | 40% |
| FC | 97% → 100% (tolerância) |
| **Comissão** | R$ 10.000 × 5% × 40% × 100% = **R$ 200,00** |

---

## 6. CÁLCULO DE COMISSÕES POR RECEBIMENTO

### 6.1 Visão Geral

Colaboradores que recebem por recebimento têm suas comissões calculadas quando o cliente efetua o pagamento, não no momento do faturamento.

### 6.2 Desafio: Múltiplos Itens com Taxas Diferentes

Um único processo pode conter vários itens, cada um com:
- Taxa de Rateio diferente
- FC diferente (colaboradores diferentes)

**Solução:** Usar médias ponderadas pelo valor de cada item.

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
FCMP = (100% × 10.000 + 85% × 5.000) / 15.000
FCMP = (10.000 + 4.250) / 15.000
FCMP = 14.250 / 15.000
FCMP = 95% → 100% (aplica regra de tolerância)
```

### 6.5 Regras do FCMP

- **Teto Máximo:** FCMP = 1.0 (mesma regra do FC)
- **Sem Piso:** Pode tender a zero
- **Tolerância:** Se FCMP ≥ 95%, considera-se 100%

### 6.6 Cálculo por Pagamento

**Fórmula:**
```
Comissão do Pagamento = Valor Recebido × TCMP × FCMP
```

**Exemplo:**

| Componente | Valor |
|------------|-------|
| Pagamento Recebido | R$ 8.000 |
| TCMP do Processo | 4,33% |
| FCMP do Processo | 100% |
| **Comissão** | R$ 8.000 × 4,33% × 100% = **R$ 346,40** |

### 6.7 Condições para Cálculo do FCMP

| Status do Processo | FCMP Utilizado | Motivo |
|-------------------|----------------|--------|
| Em Andamento / Pendente | 1.0 (provisório) | Metas ainda não realizadas |
| FATURADO | FCMP real calculado | Metas já conhecidas |

---

## 7. LÓGICA DE CROSS-SELLING

### 7.1 Definição

Cross-selling ocorre quando um único processo de venda envolve produtos de **múltiplas linhas de negócio**, exigindo colaboração entre especialistas de diferentes áreas.

### 7.2 Detecção Automática

**Regra de Identificação:**

Se a coluna `Gerente Comercial-Pedido` estiver **preenchida** no processo, então **obrigatoriamente** houve cross-selling.

**Motivo:** Esta coluna só é preenchida quando um colaborador participa da venda de itens fora de sua atribuição normal.

### 7.3 Identificação dos Itens de Cross-Selling

**Processo:**
1. Verificar o nome na coluna `Gerente Comercial-Pedido`
2. Para cada item do processo, consultar a aba `ATRIBUICOES`
3. Identificar quais itens **NÃO** estão atribuídos a esse colaborador
4. Esses itens são os **itens de cross-selling**

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

- A escolha é feita **por item** ou em **lote** para todos os itens de cross-selling do processo
- A decisão é registrada e aplicada no cálculo final

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
- **FCMP Real:** Fator de Correção Médio Ponderado calculado após faturamento

#### 8.4.3 Resultados Possíveis da Reconciliação

| Cenário | FCMP Real | Resultado | Significado |
|---------|-----------|-----------|-------------|
| Meta atingida 100%+ | FCMP = 1.0 | Reconciliação = **R$ 0** | Sem ajuste |
| Meta abaixo de 100% | FCMP < 1.0 | Reconciliação = **Negativo** | Colaborador deve devolver |

**IMPORTANTE:** A reconciliação **NUNCA** gera crédito adicional, pois o FCMP máximo é 1.0.

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

---

## 9. DEVOLUÇÕES E SALDOS NEGATIVOS

### 9.1 Fontes de Saldos Negativos

O sistema gera saldos negativos de **duas fontes**:

| Fonte | Aplica-se a | Quando Ocorre |
|-------|-------------|---------------|
| **Reconciliação** | Colaboradores que recebem por recebimento | Quando processo é faturado e FCMP < 1.0 |
| **Devoluções** | TODOS os colaboradores do item devolvido | Quando cliente devolve um item |

### 9.2 Devoluções de Itens (Implementação Futura)

#### 9.2.1 Arquivo de Devoluções

Novo arquivo de entrada contendo:
- Número da NF original
- Código do item devolvido
- Data da devolução
- Valor devolvido

#### 9.2.2 Lógica de Estorno

**Regra Crítica:** Apenas o **item específico** devolvido gera estorno, **NÃO** o processo inteiro.

**Processo:**
1. Identificar o item devolvido através do Número NF
2. Consultar o **Banco de Dados Histórico de Comissões**
3. Recuperar a comissão **exata** que foi paga originalmente para cada colaborador
4. Esta comissão (com o FC aplicado na época) se torna saldo negativo

#### 9.2.3 Características do Estorno

- **Valor:** Comissão original paga (com FC do mês de faturamento)
- **Período:** Registrado no mês de apuração em que a devolução ocorreu (não retroativo)
- **Distribuição:** Cada colaborador que recebeu comissão pelo item recebe débito proporcional

### 9.3 Consolidação de Saldos Negativos

#### 9.3.1 Aplicação

Os saldos negativos são **descontados** das demais comissões que o colaborador recebe no **mesmo mês de apuração**.

#### 9.3.2 Página de Saldos Negativos (Frontend)

O sistema exibirá uma página dedicada mostrando:
- Lista de todos os saldos negativos do mês
- Para cada saldo:
  - Origem (Reconciliação ou Devolução)
  - Processo/Item envolvido
  - Colaborador afetado
  - Cálculo detalhado justificando o valor
- Total consolidado por colaborador

---

## 10. MÓDULO DE RENTABILIDADE

### 10.1 Propósito

Calcular o componente de rentabilidade do Fator de Correção, comparando margens de lucro esperadas versus realizadas.

### 10.2 Fluxo de Processamento (Implementação Futura)

```
1. UPLOAD
   └── Usuário carrega CSV bruto com rentabilidade por item vendido

2. PROCESSAMENTO
   ├── Vincular cada item ao seu Processo
   ├── Agrupar itens por categoria (Linha + Grupo + Subgrupo + Tipo)
   └── Calcular média ponderada de rentabilidade por categoria

3. ARMAZENAMENTO
   └── Salvar arquivo: rentabilidade_MM_AAAA_agrupada

4. USO
   └── Alimentar cálculo do FC com componente de rentabilidade
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

---

## 11. TAXAS DE CÂMBIO

### 11.1 Propósito

Converter metas de fornecedores definidas em moedas estrangeiras para Reais, permitindo comparação com valores realizados.

### 11.2 Funcionamento

1. **Metas Definidas:** Em moeda original (USD, EUR, etc.)
2. **Taxas Armazenadas:** Média mensal de câmbio por moeda
3. **Conversão:** No momento do cálculo, converte meta para R$ usando taxa do mês

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
3. Carregar arquivo de Rentabilidade
4. Revisar dados carregados
5. Executar cálculo
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

**Descrição:** Já documentada na seção 5.4.3.

**Status:** A ser implementada no motor de cálculo.

### 13.3 Processamento Automático de Rentabilidade

**Descrição:** Já documentada na seção 10.2.

**Fluxo:** Upload CSV → Processamento → Arquivo padronizado → Uso no cálculo.

### 13.4 Banco de Dados Histórico de Comissões

**Descrição:** Arquivo Excel acumulativo (cresce a cada mês) armazenando todas as comissões pagas.

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

### 13.7 Processamento de Devoluções

**Descrição:** Já documentado na seção 9.2.

**Novo Upload:** Arquivo de devoluções com NF, item, data.

### 13.8 Dashboard de Saldos Negativos

**Descrição:** Já documentado na seção 9.3.2.

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
| **FC** | Fator de Correção - multiplicador baseado em metas (teto = 1.0, sem piso) |
| **TCMP** | Taxa de Comissão Média Ponderada de um processo |
| **FCMP** | Fator de Correção Médio Ponderado de um processo (teto = 1.0, sem piso) |
| **Adiantamento (COT)** | Pagamento recebido antes do faturamento |
| **Reconciliação** | Ajuste quando processo é faturado e FCMP real < 1.0 |
| **Cross-Selling** | Venda envolvendo múltiplas linhas de negócio |
| **Metas de Faturamento** | Valor em R$ de processos com NF emitida no mês |
| **Metas de Conversão** | Valor em R$ de processos convertidos em venda no mês |
| **Metas de Rentabilidade** | Margem de lucro % esperada por categoria |
| **Tolerância (95%)** | Regra que considera FC ≥ 95% como 100% |
| **Status FATURADO** | Indica que processo teve NF emitida e permite cálculo real do FC |

---

## 📎 APÊNDICES

### A. Fórmulas Resumidas

**Comissão por Faturamento:**
```
Comissão = Valor Item × Taxa Rateio × Fatia Cargo × FC
```

**TCMP:**
```
TCMP = Σ(Taxa × Valor) / Σ(Valor Total)
```

**FCMP:**
```
FCMP = Σ(FC × Valor) / Σ(Valor Total)
```

**Comissão por Recebimento:**
```
Comissão = Valor Pagamento × TCMP × FCMP
```

**Reconciliação:**
```
Ajuste = Comissão Adiantada × (FCMP Real - 1)
```

### B. Regras de Negócio Resumidas

1. **FC Máximo:** Sempre 1.0 (nunca gera bônus)
2. **FC Mínimo:** Não existe (pode tender a zero)
3. **Tolerância:** FC ≥ 95% → considera 100%
4. **Reconciliação:** Só quando Status = FATURADO e houve COT
5. **Reconciliação nunca gera crédito:** Resultado é 0 ou negativo
6. **Devoluções:** Apenas o item devolvido é estornado
7. **Cross-Selling:** Detectado por coluna `Gerente Comercial-Pedido` preenchida

---

> **Documento mantido por:** Equipe de Desenvolvimento  
> **Última atualização:** Dezembro/2024  
> **Próxima revisão:** Conforme implementações futuras
