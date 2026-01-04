# 📖 GUIA COMPLETO DO SISTEMA DE COMISSÕES
## Explicação Detalhada com Exemplos Reais, Fórmulas e Diagramas

---

# PARTE 1: VISÃO GERAL

## O Que é o Sistema de Comissões?

O Sistema de Comissões é uma ferramenta automatizada que calcula quanto cada colaborador deve receber de comissão pelas vendas realizadas. Ele elimina cálculos manuais, evita erros e garante que as regras da empresa sejam aplicadas de forma consistente.

## Como Funciona em Termos Simples?

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   📄 PLANILHAS         ⚙️ SISTEMA                📊 RESULTADOS              │
│   DE ENTRADA           PROCESSA                  GERADOS                    │
│                                                                              │
│   ┌──────────┐                                   ┌──────────────┐           │
│   │ Vendas   │ ──┐                           ┌──▶│ Comissões    │           │
│   └──────────┘   │     ┌──────────────┐      │   │ por Vendedor │           │
│                  │     │              │      │   └──────────────┘           │
│   ┌──────────┐   ├────▶│   CÁLCULO    │──────┤                              │
│   │Pagamentos│ ──┤     │  AUTOMÁTICO  │      │   ┌──────────────┐           │
│   └──────────┘   │     │              │      └──▶│ Relatórios   │           │
│                  │     └──────────────┘          │ Detalhados   │           │
│   ┌──────────┐   │                               └──────────────┘           │
│   │ Regras   │ ──┘                                                          │
│   └──────────┘                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Dois Modos de Pagamento de Comissão

O sistema trabalha com **dois modos** de pagamento de comissão:

| Modo | Quando a Comissão é Paga | Exemplo |
|------|--------------------------|---------|
| **Por Faturamento** | Quando a Nota Fiscal é emitida | Colaborador recebe quando a NF é emitida |
| **Por Recebimento** | Quando o cliente paga um adiantamento ou parcela regular | Colaborador (Gerente de Linha) recebe quando o dinheiro entra |

---

# PARTE 2: DADOS DE ENTRADA

## Usando os Dados Reais como Exemplo

Com base nos arquivos reais do sistema, temos:

### 📋 Análise Comercial (Vendas)

| Processo | Status | NF | Data Emissão | Valor | Consultor | Representante | Ger. Comercial-Pedido | Linha | Grupo | Subgrupo | Tipo de Mercadoria
|----------|--------|-----|--------------|-------|-----------|---------------|----------------------|-------|-------|----------|
| TESTE | FATURADO | 999001 | 01/10/2025 | R$ 30 | SAMANTA | MATEUS | ANDRÉ LUIS | Hidrologia | Sonda Serie EXO | EXO |
| TESTE | FATURADO | 999001 | 01/10/2025 | R$ 20 | SAMANTA | MATEUS | ANDRÉ LUIS | Hidrologia | Medidor de Vazão Fixo | IQ Standard |
| TESTE2 | FATURADO | 999002 | 11/10/2025 | R$ 30 | SAMANTA | MATEUS | *(vazio)* | Hidrologia | Sonda Serie EXO | EXO |

**Observação Importante:** O processo **TESTE** possui a coluna "Gerente Comercial-Pedido" preenchida com "ANDRÉ LUIS GONCALVES CAMARGO", o que indica que houve **CROSS-SELLING** neste processo.

### 💰 Análise Financeira (Pagamentos)

| Documento | Valor Líquido | Data de Baixa |
|-----------|---------------|---------------|
| 999001 | R$ 40 | 15/10/2025 |
| 999002 | R$ 30 | 20/10/2025 |

**Interpretação:**
- O Documento 999001 refere-se à NF 999001 (Processo TESTE) — pagamento de R$ 40
- O Documento 999002 refere-se à NF 999002 (Processo TESTE2) — pagamento de R$ 30

### 📊 Rentabilidade Realizada (Outubro/2025)

| Linha | Grupo | Subgrupo | Tipo | Rentabilidade Realizada |
|-------|-------|----------|------|------------------------|
| Hidrologia | Sonda Serie EXO | EXO | Produto | 40% |
| Hidrologia | Medidor de Vazão Fixo | IQ Standard | Produto | 30% |

---

# PARTE 3: CÁLCULO DE COMISSÕES POR FATURAMENTO

## Fluxo Visual do Cálculo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE CÁLCULO POR FATURAMENTO                        │
└─────────────────────────────────────────────────────────────────────────────┘

        ┌───────────────┐
        │    ITEM       │
        │   VENDIDO     │
        └───────┬───────┘
                │
                ▼
    ┌───────────────────────┐
    │ 1. Identificar        │
    │    Categoria do Item  │
    │    (Linha + Grupo +   │
    │     Subgrupo + Tipo)  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ 2. Buscar Taxa de     │
    │    Rateio nas Regras  │
    │    (Ex: 5%)           │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ 3. Identificar        │
    │    Colaboradores      │
    │    Responsáveis       │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ 4. Calcular Fator de  │
    │    Correção (FC) de   │
    │    cada colaborador   │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │ 5. Aplicar Fórmula    │
    │    para cada um       │
    └───────────┬───────────┘
                │
                ▼
        ┌───────────────┐
        │   COMISSÃO    │
        │   CALCULADA   │
        └───────────────┘
```

## Fórmula Principal

A comissão de cada colaborador para cada item é calculada assim:

$$\text{Comissão} = \text{Valor do Item} \times \text{Taxa de Rateio} \times \text{Fatia do Cargo} \times \text{FC}$$

**Onde:**
- **Valor do Item** = Quanto custou o produto vendido
- **Taxa de Rateio** = Percentual máximo de comissão daquela categoria de produto
- **Fatia do Cargo** = Quanto desse percentual vai para cada cargo
- **FC** = Fator de Correção (baseado no desempenho em metas)

---

## Exemplo Prático com Dados Reais

### Situação:
Vamos calcular a comissão do **Processo TESTE** para o item "Sonda Serie EXO"

**Dados do Item:**
- Valor: R$ 30,00
- Linha: Hidrologia
- Grupo: Sonda Serie EXO
- Subgrupo: EXO
- Tipo: Produto

**Suponha as seguintes regras:**
- Taxa de Rateio para esta categoria: 5%
- Fatia do Representante (MATEUS): 35%
- Fatia do Consultor (SAMANTA): 25%

**Suponha que o FC de MATEUS seja 92%**

### Cálculo Passo a Passo:

**Passo 1:** Identificar o Valor do Item
$$\text{Valor} = R\$ \space 30,00$$

**Passo 2:** Aplicar a Taxa de Rateio (5%)
$$R\$ \space 30,00 \times 0,05 = R\$ \space 1,50$$

Este é o "bolo" total de comissão a ser dividido.

**Passo 3:** Calcular a Fatia do MATEUS (35%)
$$R\$ \space 1,50 \times 0,35 = R\$ \space 0,525$$

**Passo 4:** Aplicar o Fator de Correção (92%)
$$R\$ \space 0,525 \times 0,92 = R\$ \space 0,483$$

**Resultado:** MATEUS receberia **R$ 0,48** de comissão por este item.

---

## O Fator de Correção (FC): Como é Calculado

O FC representa "quão bem" o colaborador está cumprindo suas metas. É uma média ponderada de vários componentes:

### Diagrama do FC

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    COMPOSIÇÃO DO FATOR DE CORREÇÃO (FC)                      │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐      ┌─────────────────────┐
    │ Faturamento Linha   │      │  Peso: 25%          │
    │ Meta: R$ 500.000    │─────▶│  Realizado/Meta     │───┐
    │ Realizado: R$450.000│      │  = 90%              │   │
    └─────────────────────┘      └─────────────────────┘   │
                                                           │
    ┌─────────────────────┐      ┌─────────────────────┐   │
    │ Faturamento Indiv.  │      │  Peso: 15%          │   │
    │ Meta: R$ 80.000     │─────▶│  Realizado/Meta     │───┤
    │ Realizado: R$ 85.000│      │  = 106% → 100%      │   │
    └─────────────────────┘      └─────────────────────┘   │
                                                           │    ┌─────────────┐
    ┌─────────────────────┐      ┌─────────────────────┐   ├───▶│     FC      │
    │ Conversão Linha     │      │  Peso: 15%          │   │    │   FINAL     │
    │ Meta: R$ 400.000    │─────▶│  Realizado/Meta     │───┤    │             │
    │ Realizado: R$380.000│      │  = 95%              │   │    │  = 97%      │
    └─────────────────────┘      └─────────────────────┘   │    │             │
                                                           │    │ (≥95% = 100%)
    ┌─────────────────────┐      ┌─────────────────────┐   │    └─────────────┘
    │ Rentabilidade       │      │  Peso: 20%          │   │
    │ Meta: 35%           │─────▶│  Realizado/Meta     │───┤
    │ Realizado: 40%      │      │  = 114% → 100%      │   │
    └─────────────────────┘      └─────────────────────┘   │
                                                           │
    ┌─────────────────────┐      ┌─────────────────────┐   │
    │   Outras Metas...   │─────▶│  Pesos restantes    │───┘
    └─────────────────────┘      └─────────────────────┘
```

### Fórmula do FC

$$FC = \sum_{i=1}^{n} \left( \text{Atingimento da Meta}_i \times \text{Peso}_i \right)$$

**Onde o Atingimento de cada meta é:**

$$\text{Atingimento} = \frac{\text{Valor Realizado}}{\text{Valor da Meta}}$$

### Exemplo de Cálculo do FC

| Meta | Peso | Realizado | Meta | Atingimento | Contribuição |
|------|------|-----------|------|-------------|--------------|
| Faturamento Linha | 25% | R$ 450.000 | R$ 500.000 | 90% | 0,25 × 0,90 = 0,225 |
| Faturamento Individual | 15% | R$ 85.000 | R$ 80.000 | 106% → **100%** | 0,15 × 1,00 = 0,150 |
| Conversão Linha | 15% | R$ 380.000 | R$ 400.000 | 95% | 0,15 × 0,95 = 0,1425 |
| Rentabilidade | 20% | 40% | 35% | 114% → **100%** | 0,20 × 1,00 = 0,200 |
| Conversão Individual | 10% | R$ 75.000 | R$ 70.000 | 107% → **100%** | 0,10 × 1,00 = 0,100 |
| Retenção de Clientes nos últimos 2 anos | 10% | 92% | 90% | 102% → **100%** | 0,10 × 1,00 = 0,100 |
| Fornecedores | 5% | $45.000 | $50.000 | 90% | 0,05 × 0,90 = 0,045 |

**Soma Total:**
$$FC = 0,225 + 0,150 + 0,1425 + 0,200 + 0,100 + 0,100 + 0,045 = 0,9625 = 96,25\%$$

---

## Regras Críticas do FC

### 🔴 REGRA 1: Teto Máximo = 100%

O FC **nunca** pode ultrapassar 100%, mesmo que o colaborador supere todas as metas.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Se FC calculado > 100%  ────▶  FC aplicado = 100%            │
│                                                                 │
│   Exemplo: Atingiu 150% de todas as metas                      │
│            FC = 100% (não há bônus extra)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🔴 REGRA 2: Não Existe Piso Mínimo

O FC pode ser qualquer valor abaixo de 100%, tendendo até zero se as metas forem severamente não atingidas.

### 🔴 REGRA 3: Tolerância de 95%

Se o FC calculado for **95% ou mais**, considera-se **100%**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGRA DE TOLERÂNCIA                          │
│                                                                 │
│   FC ≥ 95%  ─────▶  FC APLICADO = 100% (sem penalização)       │
│                                                                 │
│   FC < 95%  ─────▶  FC APLICADO = valor calculado              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Exemplos:
   • FC = 98%  →  Aplica 100% ✅
   • FC = 96%  →  Aplica 100% ✅
   • FC = 95%  →  Aplica 100% ✅
   • FC = 94%  →  Aplica 94%  ⚠️ Penalização de 6%
   • FC = 80%  →  Aplica 80%  ⚠️ Penalização de 20%
```

---

# PARTE 4: CÁLCULO DE COMISSÕES POR RECEBIMENTO

## Quando se Usa Este Cálculo?

Alguns colaboradores recebem comissão **quando o cliente paga**, não quando a NF é emitida. Isso é chamado de "comissão por recebimento".

## O Desafio: Múltiplos Itens

Um processo de venda pode ter vários itens, cada um com:
- Taxa de comissão diferente
- Fator de Correção diferente

**Como dividir proporcionalmente quando um pagamento chega?**

**Solução:** Usar **médias ponderadas**.

---

## TCMP: Taxa de Comissão Média Ponderada

### Conceito

O TCMP calcula uma taxa de comissão "média" para o processo inteiro, considerando o peso (valor faturado) de cada item.

### Fórmula

$$TCMP = \frac{\sum (\text{Taxa do Item} \times \text{Valor do Item})}{\sum \text{Valor Total dos Itens}}$$

### Exemplo com Dados Reais (Processo TESTE)

| Item | Valor | Taxa de Rateio |
|------|-------|----------------|
| Sonda Serie EXO | R$ 30 | 5% |
| Medidor de Vazão IQ Standard | R$ 20 | 4% |
| **TOTAL** | **R$ 50** | - |

**Cálculo Passo a Passo:**

**Passo 1:** Multiplicar cada taxa pelo valor do item

$$\text{Contribuição Item 1} = 0,05 \times 30 = 1,50$$
$$\text{Contribuição Item 2} = 0,04 \times 20 = 0,80$$

**Passo 2:** Somar as contribuições

$$\text{Soma} = 1,50 + 0,80 = 2,30$$

**Passo 3:** Dividir pelo valor total

$$TCMP = \frac{2,30}{50} = 0,046 = 4,6\%$$

**Interpretação:** A taxa média de comissão do Processo TESTE é **4,6%**.

---

## FCMP: Fator de Correção Médio Ponderado

### Conceito

Similar ao TCMP, mas para o Fator de Correção. Calcula um FC "médio" ponderado pelo valor de cada item.

### Fórmula

$$FCMP = \frac{\sum (\text{FC do Item} \times \text{Valor do Item})}{\sum \text{Valor Total dos Itens}}$$

### Exemplo

| Item | Valor | FC |
|------|-------|-----|
| Sonda Serie EXO | R$ 30 | 100% |
| Medidor de Vazão IQ Standard | R$ 20 | 88% |
| **TOTAL** | **R$ 50** | - |

**Cálculo:**

**Passo 1:** Multiplicar cada FC pelo valor

$$\text{Contribuição Item 1} = 1,00 \times 30 = 30$$
$$\text{Contribuição Item 2} = 0,88 \times 20 = 17,60$$

**Passo 2:** Somar

$$\text{Soma} = 30 + 17,60 = 47,60$$

**Passo 3:** Dividir pelo valor total

$$FCMP = \frac{47,60}{50} = 0,952 = 95,2\%$$

**Aplicando a Regra de Tolerância:** 95,2% ≥ 95% → **FCMP = 100%**

---

## Cálculo da Comissão por Pagamento

### Fórmula

$$\text{Comissão} = \text{Valor do Pagamento} \times TCMP \times FCMP$$

### Exemplo com Dados Reais

**Pagamento recebido:** Documento 999001 = **R$ 40**

**Dados calculados:**
- TCMP = 4,6%
- FCMP = 100%

**Cálculo:**

$$\text{Comissão} = 40 \times 0,046 \times 1,00 = R\$ \space 1,84$$

---

## Condição Importante: Status do Processo

```
┌─────────────────────────────────────────────────────────────────┐
│                 FCMP DEPENDE DO STATUS                          │
└─────────────────────────────────────────────────────────────────┘

   ┌─────────────────────┐
   │ Status = FATURADO   │────▶  FCMP = valor real calculado
   └─────────────────────┘

   ┌─────────────────────┐
   │ Status ≠ FATURADO   │────▶  FCMP = 1.0 (provisório)
   │ (Em Andamento,      │       
   │  Pendente, etc.)    │       Motivo: metas ainda não 
   └─────────────────────┘       foram medidas. Isso acontecerá somente em Adiantamentos de pagamentos
```

---

# PARTE 5: CROSS-SELLING (VENDA CRUZADA)

## O Que é Cross-Selling?

Cross-selling ocorre quando um processo de venda envolve produtos **que o consultor externo não é um responsável direto**, exigindo colaboração entre especialistas de áreas distintas.

## Detecção Automática

```
┌─────────────────────────────────────────────────────────────────┐
│                 COMO DETECTAR CROSS-SELLING                     │
└─────────────────────────────────────────────────────────────────┘

   Se a coluna "Gerente Comercial-Pedido" estiver PREENCHIDA
   
                    │
                    ▼
                    
   ┌─────────────────────────────────────┐
   │    HOUVE CROSS-SELLING             │
   │    com certeza!                     │
   └─────────────────────────────────────┘
   
   Esta coluna SÓ é preenchida quando alguém
   de fora da atribuição normal de um produto participou da venda.
```

## Exemplo com Dados Reais

No **Processo TESTE**, vemos:
- **Gerente Comercial-Pedido:** ANDRÉ LUIS GONCALVES CAMARGO

Isso indica que ANDRÉ LUIS participou da venda, mas alguns itens **não são de sua atribuição normal**.

### Identificação dos Itens de Cross-Selling

| Item | Linha | Atribuído a ANDRÉ? | É Cross-Selling? |
|------|-------|-------------------|------------------|
| Sonda Serie EXO | Hidrologia | ❌ Não | ✅ Sim |
| Medidor de Vazão IQ Standard | Hidrologia | ❌ Não | ✅ Sim |

*(Supondo que ANDRÉ está atribuído a outra linha, como SSO)*

## Opções de Divisão da Comissão

Quando há cross-selling, o usuário escolhe como dividir a comissão:

### Opção A: Taxa Subtraída (EXEMPLO)

```
┌─────────────────────────────────────────────────────────────────┐
│                      OPÇÃO A                                     │
│                 Taxa do Consultor Externo é                      │
│                 SUBTRAÍDA da taxa dos outros                     │
└─────────────────────────────────────────────────────────────────┘

   Taxa de Rateio do Item: 5%
   
   Taxa do Consultor Externo (ANDRÉ): 1%
   
   Taxa restante dos itens para os outros colaboradores envolvidos em um Processo Comercial: 5% - 1% = 4%
   
   
      TOTAL PAGO: 4% (taxa de rateio máxima de cada item do Processo diminuiu)
   
```

### Opção B: Taxa Adicional (EXEMPLO)

```
┌─────────────────────────────────────────────────────────────────┐
│                      OPÇÃO B                                     │
│                 Taxa do Consultor Externo é                      │
│                 ADICIONAL (não subtrai)                          │
└─────────────────────────────────────────────────────────────────┘

   Taxa de Rateio do Item: 5% (para MATEUS e SAMANTA)
   
   Taxa do Consultor Externo (ANDRÉ): 1% (adicional)
   
   ┌─────────────────────────────────────┐
   │  TOTAL PAGO: 6% (empresa paga mais) │
   └─────────────────────────────────────┘
```

---

# PARTE 6: ADIANTAMENTOS E RECONCILIAÇÃO

## O Que São Adiantamentos?

Adiantamentos são pagamentos que o cliente faz **antes** da emissão da Nota Fiscal.

### Como Identificar

```
┌─────────────────────────────────────────────────────────────────┐
│              IDENTIFICAÇÃO DE ADIANTAMENTOS                     │
└─────────────────────────────────────────────────────────────────┘

   Documento começa com "COT"  ────▶  É ADIANTAMENTO
   
   Exemplos:
   • COT-2025-001  → Adiantamento ✓
   • COT123        → Adiantamento ✓
   • 999001        → Pagamento normal
   • 999002        → Pagamento normal
```

## O Problema dos Adiantamentos

```
┌─────────────────────────────────────────────────────────────────┐
│                      O PROBLEMA                                  │
└─────────────────────────────────────────────────────────────────┘

   Quando o cliente paga ANTES do faturamento:
   
   • O processo ainda NÃO está faturado
   • As metas do período ainda NÃO foram medidas
   • O FC REAL não pode ser calculado
   
   ┌─────────────────────────────────────────────┐
   │  SOLUÇÃO: Usar FC = 100% (provisório)       │
   │                                             │
   │  O colaborador recebe comissão integral     │
   │  agora, e o ajuste vem depois.              │
   └─────────────────────────────────────────────┘
```

## Reconciliação: O Ajuste Final

A reconciliação é o ajuste que ocorre quando finalmente conhecemos o FC real.

### Condições para Reconciliação

```
┌─────────────────────────────────────────────────────────────────┐
│           QUANDO A RECONCILIAÇÃO ACONTECE?                      │
└─────────────────────────────────────────────────────────────────┘

   Condição 1: O processo teve ao menos um adiantamento (COT)
                              +
   Condição 2: O status do processo mudou para "FATURADO"
   
   ════════════════════════════════════════════════════════════════
   
   Enquanto Status ≠ FATURADO:
   → Reconciliação NÃO ocorre
   → Adiantamentos permanecem com FC = 100%
```

### Fórmula da Reconciliação

$$\text{Valor da Reconciliação} = \text{Comissão Adiantada Total} \times (FCMP_{real} - 1)$$

### Resultados Possíveis

```
┌─────────────────────────────────────────────────────────────────┐
│              RESULTADOS DA RECONCILIAÇÃO                        │
└─────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────┐
   │  FCMP = 100%            │────▶  Reconciliação = R$ 0
   │  (metas atingidas)      │       (sem ajuste)
   └─────────────────────────┘
   
   ┌─────────────────────────┐
   │  FCMP < 100%            │────▶  Reconciliação = NEGATIVO
   │  (metas não atingidas)  │       (saldo negativo que será subtraído das outras comissões do mês)
   └─────────────────────────┘
   
   ⚠️ NUNCA há crédito adicional, pois FCMP máximo é 100%
```

### Exemplo Numérico de Reconciliação

**Situação:**
- Adiantamento recebido: R$ 10.000
- TCMP do Processo: 5%
- FC provisório usado: 100%
- Comissão paga no adiantamento:

$$\text{Comissão Paga} = 10.000 \times 0,05 \times 1,00 = R\$ \space 500$$

**Após Faturamento:**
- FCMP Real calculado: 85%

**Cálculo da Reconciliação:**

**Passo 1:** Calcular a diferença entre FC real e provisório
$$85\% - 100\% = -15\%$$

**Passo 2:** Aplicar à comissão paga
$$\text{Reconciliação} = 500 \times (-0,15) = -R\$ \space 75$$

**Resultado:** O colaborador tem um **débito de R$ 75** a ser descontado das outras comissões do mês

---

# PARTE 7: DEVOLUÇÕES E SALDOS NEGATIVOS

## Fontes de Saldos Negativos

O sistema pode gerar saldos negativos (débitos) de **duas formas**:

```
┌─────────────────────────────────────────────────────────────────┐
│              FONTES DE SALDOS NEGATIVOS                         │
└─────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────┐
   │  FONTE 1: RECONCILIAÇÃO                                      │
   │                                                               │
   │  • Aplica-se a: colaboradores que recebem por recebimento    │
   │  • Quando: processo é faturado e FCMP < 100%                 │
   │  • Motivo: adiantou-se mais comissão do que devia            │
   └─────────────────────────────────────────────────────────────┘
   
   ┌─────────────────────────────────────────────────────────────┐
   │  FONTE 2: DEVOLUÇÕES                                         │
   │                                                               │
   │  • Aplica-se a: TODOS os colaboradores do processo           │
   │  • Quando: cliente devolve produtos                          │
   │  • Motivo: se devolveu, a comissão precisa ser estornada     │
   └─────────────────────────────────────────────────────────────┘
```

## Lógica de Devoluções

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO DE DEVOLUÇÕES                                  │
└─────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────┐
   │ 1. Carrega arquivo  │
   │    de Devoluções    │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ 2. Filtra pelo mês  │
   │    de apuração      │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ 3. Vincula NF da    │
   │    devolução com    │
   │    NF original      │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ 4. Consulta banco   │
   │    histórico para   │
   │    ver comissões    │
   │    já pagas         │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ 5. Calcula Fator    │
   │    de Devolução     │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ 6. Gera estorno     │
   │    proporcional     │
   │    para cada        │
   │    colaborador      │
   └─────────────────────┘
```

### Fórmula do Fator de Devolução

$$\text{Fator de Devolução} = \frac{\text{Valor Devolvido}}{\text{Valor Total do Processo}}$$

### Fórmula do Estorno

$$\text{Estorno} = \text{Comissão Histórica Paga} \times \text{Fator de Devolução} \times (-1)$$

### Exemplo Numérico

**Situação:**
- Valor Total do Processo: R$ 100.000
- Valor Devolvido: R$ 25.000
- Comissão paga ao Consultor (histórico): R$ 500
- Comissão paga ao Gerente (histórico): R$ 2.000

**Cálculo:**

**Passo 1:** Calcular o Fator de Devolução
$$\text{Fator} = \frac{25.000}{100.000} = 0,25 = 25\%$$

**Passo 2:** Calcular o Estorno do Vendedor
$$\text{Estorno Gerente} = 2.000 \times 0,25 \times (-1) = -R\$ \space 500$$

**Passo 3:** Calcular o Estorno do Gerente
$$\text{Estorno Consultor} = 500 \times 0,25 \times (-1) = -R\$ \space 125$$

**Resultado:**
- Gerente: débito de **R$ 500**
- Consultor: débito de **R$ 125**

### Regra de Proporcionalidade

O estorno é **proporcional** ao valor devolvido:
- Se 25% do valor foi devolvido → 25% da comissão é estornada
- Se 100% do valor foi devolvido → 100% da comissão é estornada

---

# PARTE 8: MÓDULO DE RENTABILIDADE

## O Que é Rentabilidade?

Rentabilidade é a **margem de lucro** de cada categoria de produto. Indica quanto a empresa ganha (percentualmente) com cada venda.

## Dados Reais de Rentabilidade (Outubro/2025)

| Linha | Grupo | Subgrupo | Tipo | Rentab. Realizada |
|-------|-------|----------|------|-------------------|
| Hidrologia | Sonda Serie EXO | EXO | Produto | 40% |
| Hidrologia | Medidor de Vazão Fixo | IQ Standard | Produto | 30% |
| SSO | Analisador Fixo | Falco | Produto | 30% |
| Remediação | Sistema Remediação | QED | Produto | 42% |

## Como a Rentabilidade Afeta o FC

A rentabilidade é uma das **metas** que compõe o Fator de Correção.

**Exemplo:**
- Meta de Rentabilidade para "Sonda Serie EXO": 35%
- Rentabilidade Realizada: 30%
- Atingimento: 40% ÷ 35% = 86% 

---

# PARTE 9: RESUMO DAS FÓRMULAS

## Quadro de Referência Rápida

| Cálculo | Fórmula |
|---------|---------|
| **Comissão por Faturamento** | $\text{Valor} \times \text{Taxa Rateio} \times \text{Fatia Cargo} \times FC$ |
| **TCMP** | $\displaystyle\frac{\sum(\text{Taxa} \times \text{Valor Item})}{\sum\text{Valor Total}}$ |
| **FCMP** | $\displaystyle\frac{\sum(FC \times \text{Valor Item})}{\sum\text{Valor Total}}$ |
| **Comissão por Recebimento** | $\text{Pagamento} \times TCMP \times FCMP$ |
| **Reconciliação** | $\text{Comissão Adiantada} \times (FCMP_{real} - 1)$ |
| **Fator de Devolução** | $\displaystyle\frac{\text{Valor Devolvido}}{\text{Valor Total Processo}}$ |
| **Estorno por Devolução** | $\text{Comissão Histórica} \times \text{Fator Devolução} \times (-1)$ |
| **FC** | $\displaystyle\sum(\text{Atingimento Meta} \times \text{Peso})$ |

## Regras de Negócio Resumidas

```
┌─────────────────────────────────────────────────────────────────┐
│                   REGRAS PRINCIPAIS                             │
├─────────────────────────────────────────────────────────────────┤
│  1. FC máximo = 100% (nunca passa disso)                        │
│  2. FC mínimo = não existe (pode ser próximo de zero)          │
│  3. Se FC ≥ 95% → considera 100% (tolerância)                  │
│  4. Reconciliação só ocorre quando Status = FATURADO           │
│  5. Reconciliação NUNCA gera crédito (só débito ou zero)       │
│  6. Devolução gera estorno PROPORCIONAL ao valor devolvido     │
│  7. Cross-selling detectado por "Gerente Comercial-Pedido"     │
└─────────────────────────────────────────────────────────────────┘
```

---

# PARTE 10: IMPLEMENTAÇÕES FUTURAS

## Funcionalidades Planejadas

### 1. Política de Comissionamento Anual (PDF)
Documento personalizado para cada colaborador assinar, contendo suas metas, atribuições e taxas.

### 2. Processamento Automático de Rentabilidade
Upload de CSV bruto → Sistema organiza e calcula médias ponderadas automaticamente por categoria de produto.

### 3. Banco de Dados Histórico
Arquivo que armazena TODAS as comissões pagas, crescendo a cada mês.

### 4. PDF Detalhado de Auditoria
Relatório individual mostrando cada item, taxa, FC e cálculo para transparência total.

### 5. Excel com Tabela Dinâmica
Planilha expansível para auditoria detalhada, com hierarquia Processo → Item → Colaborador.

### 6. Dashboard de Saldos Negativos
Página consolidando todos os débitos (reconciliações + devoluções) com justificativas.

---

*Este guia cobre toda a lógica de negócio do Sistema de Comissões, com exemplos reais e fórmulas detalhadas.*
