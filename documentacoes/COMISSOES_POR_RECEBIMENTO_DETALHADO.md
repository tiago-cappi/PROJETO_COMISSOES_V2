# Documentação Detalhada: Comissões Por Recebimento e Reconciliações

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Conceitos Fundamentais](#conceitos-fundamentais)
3. [Arquivos de Entrada e Suas Colunas](#arquivos-de-entrada-e-suas-colunas)
4. [Relacionamento Entre Arquivos](#relacionamento-entre-arquivos)
5. [Aba ESTADO: Estrutura e Funcionamento](#aba-estado-estrutura-e-funcionamento)
6. [Cálculo de TCMP (Taxa de Comissão Média Ponderada)](#cálculo-de-tcmp)
7. [Cálculo de FCMP (Fator de Correção Médio Ponderado)](#cálculo-de-fcmp)
8. [Comissões por Adiantamento](#comissões-por-adiantamento)
9. [Comissões por Pagamento Regular](#comissões-por-pagamento-regular)
10. [Reconciliações (A Implementar)](#reconciliações-a-implementar)
11. [Fluxo Completo de Execução](#fluxo-completo-de-execução)
12. [Exemplos Práticos](#exemplos-práticos)

---

## Visão Geral

O sistema de **Comissões Por Recebimento** é uma lógica alternativa de cálculo de comissões que, ao invés de calcular item a item no momento do faturamento, calcula **a nível de processo** baseado nos **recebimentos efetivos** (pagamentos) do cliente.

### Diferença Principal: Faturamento vs. Recebimento

| Aspecto | Comissões por Faturamento | Comissões por Recebimento |
|---------|---------------------------|---------------------------|
| **Momento do Cálculo** | Quando o processo é faturado | Quando o cliente paga |
| **Granularidade** | Item a item | Processo inteiro |
| **Fator de Correção** | FC calculado no momento | FCMP (média ponderada) |
| **Taxa de Comissão** | Taxa por item | TCMP (média ponderada) |
| **Quem Recebe** | Todos os colaboradores | Apenas "Gerentes de Linha" |

### Colaboradores que Recebem por Recebimento

São identificados através de:
- **Cargo**: `CARGOS.TIPO_COMISSAO == 'Recebimento'`
- **Colaborador**: `COLABORADORES.TIPO_COMISSAO == 'Recebimento'`
- **Heurística**: Nome do cargo contendo "Gerente Linha"

**Exemplo**: André Caramello, Neimar, Alessandro Cappi (cargo: Gerente Linha)

---

## Conceitos Fundamentais

### 1. TCMP - Taxa de Comissão Média Ponderada

A **TCMP** é a taxa de comissão média de um colaborador para um processo inteiro, ponderada pelo valor de cada item.

**Fórmula Matemática:**

```
TCMP_colaborador = Σ(Valor_Item_i × Taxa_Item_i) / Σ(Valor_Item_i)

Onde:
- Taxa_Item_i = taxa_rateio_maximo_pct × fatia_cargo_pct (da regra de comissão)
- Valor_Item_i = Valor Realizado do item (da Análise Comercial)
- Σ = soma para todos os itens do processo
```

**Exemplo Numérico:**

Um processo tem 3 itens:
- Item 1: Valor = R$ 1.000, Taxa = 0,05 (5%)
- Item 2: Valor = R$ 2.000, Taxa = 0,03 (3%)
- Item 3: Valor = R$ 1.500, Taxa = 0,04 (4%)

```
TCMP = (1.000 × 0,05 + 2.000 × 0,03 + 1.500 × 0,04) / (1.000 + 2.000 + 1.500)
TCMP = (50 + 60 + 60) / 4.500
TCMP = 170 / 4.500
TCMP = 0,0378 (3,78%)
```

### 2. FCMP - Fator de Correção Médio Ponderado

O **FCMP** é o fator de correção médio de um colaborador para um processo inteiro, ponderado pelo valor de cada item.

**Fórmula Matemática:**

```
FCMP_colaborador = Σ(Valor_Item_i × FC_Item_i) / Σ(Valor_Item_i)

Onde:
- FC_Item_i = Fator de Correção calculado para o item (baseado em metas)
- Valor_Item_i = Valor Realizado do item
- Σ = soma para todos os itens do processo
```

**Exemplo Numérico:**

Mesmo processo com 3 itens:
- Item 1: Valor = R$ 1.000, FC = 0,85
- Item 2: Valor = R$ 2.000, FC = 0,92
- Item 3: Valor = R$ 1.500, FC = 0,88

```
FCMP = (1.000 × 0,85 + 2.000 × 0,92 + 1.500 × 0,88) / (1.000 + 2.000 + 1.500)
FCMP = (850 + 1.840 + 1.320) / 4.500
FCMP = 4.010 / 4.500
FCMP = 0,8911 (89,11%)
```

### 3. Adiantamento vs. Pagamento Regular

#### Adiantamento (COT)
- **Quando**: ANTES do processo ser faturado
- **Identificação**: Documento começa com "COT" (ex: COT123456)
- **Fórmula**: `Comissão = Valor_Pago × TCMP × 1,0` (FC sempre 1,0)
- **Por quê FC = 1,0?**: Porque ainda não sabemos o desempenho real das metas (o processo não foi faturado)

#### Pagamento Regular
- **Quando**: APÓS o processo ser faturado
- **Identificação**: Documento é um número de NF (ex: 048341)
- **Fórmula**: `Comissão = Valor_Pago × TCMP × FCMP`
- **Por quê usar FCMP?**: Porque já conhecemos o desempenho real das metas no mês do faturamento

---

## Arquivos de Entrada e Suas Colunas

### 1. Análise Financeira.xlsx

**Localização**: `dados_entrada/Análise Financeira.xlsx`

**Propósito**: Contém TODOS os pagamentos recebidos dos clientes

**Colunas Relevantes**:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `Documento` | String | Número do documento de pagamento | "048341" ou "COT123456" |
| `Valor Líquido` | Decimal | Valor efetivamente recebido | 50,00 |
| `Data de Baixa` | Data | Data em que o pagamento foi baixado | 2025-09-15 |
| `Tipo de Baixa` | String | Tipo de baixa (usar apenas 'B') | "B" |

**Filtros Aplicados**:
```python
# Filtro 1: Tipo de Baixa == 'B'
df = df[df["Tipo de Baixa"] == "B"]

# Filtro 2: Mês/Ano de apuração
df = df[(df["Data de Baixa"].dt.month == mes) & 
        (df["Data de Baixa"].dt.year == ano)]
```

### 2. Analise_Comercial_Completa.csv

**Localização**: `Analise_Comercial_Completa.csv` (gerado pelo preparador)

**Propósito**: Contém TODOS os itens de TODOS os processos comerciais

**Colunas Relevantes**:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `Processo` | String | ID único do processo | "999999" |
| `Numero NF` | String | Número da Nota Fiscal | "048341" ou "" |
| `Status Processo` | String | Status atual do processo | "FATURADO", "PENDENTE" |
| `Dt Emissão` | Data | Data de emissão da NF | 2025-09-15 |
| `Valor Realizado` | Decimal | Valor realizado do item | 100,00 |
| `Negócio` | String | Linha de negócio | "SSO" |
| `Grupo` | String | Grupo do produto | "Detector Portátil" |
| `Subgrupo` | String | Subgrupo do produto | "MicroClip" |
| `Tipo de Mercadoria` | String | Tipo do item | "Produto", "Reposição" |
| `Consultor Interno` | String | Nome do consultor interno | "ANDREY.ANDRADE" |
| `Representante-pedido` | String | Nome do consultor externo | "ANDRÉ LUIS GONCALVES CAMARGO" |

**Observação Importante**: 
- Um **processo único** pode ter **múltiplas linhas** (um item por linha)
- Cada linha representa um item diferente do pedido
- As médias ponderadas (TCMP/FCMP) consideram TODOS os itens do processo

### 3. CONFIG_COMISSAO.csv (em Regras_Comissoes.xlsx)

**Propósito**: Define as regras de comissão por contexto

**Colunas Relevantes**:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `linha` | String | Linha de negócio |
| `grupo` | String | Grupo do produto |
| `subgrupo` | String | Subgrupo do produto |
| `tipo_mercadoria` | String | Tipo de mercadoria |
| `cargo` | String | Cargo do colaborador |
| `taxa_rateio_maximo_pct` | Decimal | Taxa de rateio (%) |
| `fatia_cargo_pct` | Decimal | Percentual de Elegibilidade (%) |

**Exemplo de Busca**:
```
Contexto: SSO / Detector Portátil / MicroClip / Produto / Gerente Linha
Resultado: taxa_rateio=10%, fatia_cargo=50%
Taxa Final = 10% × 50% = 5%
```

### 4. ATRIBUICOES.csv (em Regras_Comissoes.xlsx)

**Propósito**: Define os colaboradores de gestão por contexto

**Colunas Relevantes**:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `linha` | String | Linha de negócio |
| `grupo` | String | Grupo do produto |
| `subgrupo` | String | Subgrupo do produto |
| `tipo_mercadoria` | String | Tipo de mercadoria |
| `id_colaborador` | String | ID do colaborador |
| `colaborador` | String | Nome do colaborador (alternativa) |

**Uso**: Identifica colaboradores de gestão (ex: Gerente Linha) que não aparecem diretamente na Análise Comercial

---

## Relacionamento Entre Arquivos

### Mapeamento: Análise Financeira → Análise Comercial

O relacionamento entre os arquivos é feito através do campo `Documento`:

```
┌─────────────────────────────┐
│  Análise Financeira.xlsx    │
│  Documento: "048341"        │
│  Valor Líquido: R$ 50,00    │
└──────────┬──────────────────┘
           │
           │ REGRA DE MAPEAMENTO:
           │
           ├─ Se Documento começa com "COT":
           │    → Tipo: ADIANTAMENTO
           │    → Processo = dígitos após "COT"
           │    → Exemplo: "COT123456" → Processo "123456"
           │
           └─ Caso contrário:
                → Tipo: PAGAMENTO_REGULAR
                → Extrai 6 primeiros dígitos
                → Normaliza (remove zeros à esquerda)
                → Exemplo: "048341" → "48341"
                ↓
┌─────────────────────────────────┐
│ Analise_Comercial_Completa.csv │
│ Numero NF: "48341"              │
│ Processo: "999999"              │
└─────────────────────────────────┘
```

### Normalização para Comparação

**Documento na Análise Financeira**: "048341" (mantém zeros à esquerda)
**Numero NF na Análise Comercial**: "48341.0" (pode ter formato numérico)

**Lógica de Normalização**:
```python
# Análise Financeira
doc_financeira = "048341"
doc_digits = ''.join(filter(str.isdigit, doc_financeira))  # "048341"
doc_normalizado = doc_digits.lstrip('0')  # "48341"

# Análise Comercial
nf_comercial = "48341.0"
nf_digits = nf_comercial.split('.')[0]  # "48341"
nf_normalizado = nf_digits.lstrip('0')  # "48341"

# Comparação
if doc_normalizado == nf_normalizado:  # "48341" == "48341" ✓
    processo_encontrado = True
```

### Fluxo Completo de Identificação

```
1. Ler Análise Financeira
   └─ Filtrar: Tipo de Baixa == 'B' E Mês/Ano corretos
      └─ Para cada linha:
         ├─ Documento = "048341"
         ├─ Valor = R$ 50,00
         └─ Mapear → Processo

2. Mapear Documento → Processo
   └─ "048341" não começa com "COT"
      └─ É PAGAMENTO_REGULAR
         └─ Normalizar: "48341"
            └─ Buscar em Analise_Comercial_Completa
               └─ WHERE Numero NF normalizado == "48341"
                  └─ RETORNA: Processo = "999999" ✓

3. Buscar Itens do Processo
   └─ Na Analise_Comercial_Completa
      └─ WHERE Processo == "999999"
         └─ RETORNA: Todos os itens (linhas) desse processo

4. Identificar Colaboradores
   └─ Colaboradores Operacionais:
      ├─ Consultor Interno: "ANDREY.ANDRADE"
      └─ Representante-pedido: "ANDRÉ LUIS GONCALVES CAMARGO"
   └─ Colaboradores de Gestão (ATRIBUICOES):
      └─ WHERE linha+grupo+subgrupo+tipo == contexto do item
         └─ RETORNA: "Alessandro Cappi" (Gerente Linha)

5. Filtrar por "Recebe por Recebimento"
   └─ De todos os colaboradores identificados:
      └─ Verificar: Cargo == "Gerente Linha" OU TIPO_COMISSAO == "Recebimento"
         └─ RETORNA: ["Alessandro Cappi"] ✓
```

---

## Aba ESTADO: Estrutura e Funcionamento

### Propósito

A aba **ESTADO** é um **registro persistente** de todos os processos que tiveram ao menos UM pagamento registrado na Análise Financeira. Ela funciona como um "banco de dados" que acumula informações ao longo do tempo.

### Estrutura Completa

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| **PROCESSO** | String | ID único do processo | "999999" |
| **VALOR_TOTAL_PROCESSO** | Decimal | Valor total do processo (soma de todos os itens) | 100,00 |
| **TOTAL_ANTECIPACOES** | Decimal | Soma de todos os adiantamentos recebidos | 0,00 |
| **TOTAL_PAGAMENTOS_REGULARES** | Decimal | Soma de todos os pagamentos regulares | 50,00 |
| **TOTAL_PAGO_ACUMULADO** | Decimal | Total recebido até o momento | 50,00 |
| **SALDO_A_RECEBER** | Decimal | Valor ainda não recebido | 50,00 |
| **TOTAL_COMISSAO_ANTECIPACOES** | Decimal | Comissões pagas em adiantamentos | 0,00 |
| **TOTAL_COMISSAO_REGULARES** | Decimal | Comissões pagas em pagamentos regulares | 0,00 |
| **TOTAL_COMISSAO_ACUMULADA** | Decimal | Total de comissões pagas | 0,00 |
| **STATUS_PROCESSO** | String | Status do processo | "FATURADO", "PENDENTE" |
| **STATUS_PAGAMENTO** | String | Status do pagamento | "PARCIAL", "COMPLETO" |
| **STATUS_CALCULO_MEDIAS** | String | Se TCMP/FCMP foram calculados | "CALCULADO", "PENDENTE" |
| **MES_ANO_FATURAMENTO** | String | Mês/ano em que foi faturado | "09/2025" |
| **TCMP_JSON** | JSON String | TCMP por colaborador | {"Alessandro Cappi": 0.05} |
| **FCMP_JSON** | JSON String | FCMP por colaborador | {"Alessandro Cappi": 0.89} |
| **COLABORADORES_ENVOLVIDOS** | String | Lista de colaboradores | "Alessandro Cappi" |
| **DATA_PRIMEIRO_PAGAMENTO** | Data | Data do primeiro pagamento | 2025-09-15 |
| **DATA_ULTIMO_PAGAMENTO** | Data | Data do último pagamento | 2025-09-15 |
| **QUANTIDADE_PAGAMENTOS** | Integer | Número de pagamentos recebidos | 1 |
| **ULTIMA_ATUALIZACAO** | DateTime | Última atualização do registro | 2025-11-12 12:44:36 |
| **OBSERVACOES** | String | Observações adicionais | "" |

### Ciclo de Vida de um Processo no ESTADO

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: PRIMEIRO PAGAMENTO (pode ser adiantamento ou regular)  │
└─────────────────────────────────────────────────────────────────┘
 
 Ação: Criar nova linha no ESTADO
 
 PROCESSO: "999999"
 VALOR_TOTAL_PROCESSO: R$ 100,00 (da Análise Comercial)
 TOTAL_ANTECIPACOES: R$ 0,00
 TOTAL_PAGAMENTOS_REGULARES: R$ 50,00  (pagamento recebido)
 TOTAL_PAGO_ACUMULADO: R$ 50,00
 SALDO_A_RECEBER: R$ 50,00
 STATUS_PROCESSO: "PENDENTE"  (ainda não faturado)
 STATUS_PAGAMENTO: "PARCIAL"  (não pagou tudo ainda)
 STATUS_CALCULO_MEDIAS: "PENDENTE"  (ainda não calculou TCMP/FCMP)
 TCMP_JSON: null
 FCMP_JSON: null

┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: PROCESSO É FATURADO (aparece com Status=FATURADO)      │
└─────────────────────────────────────────────────────────────────┘
 
 Ação: Calcular e salvar TCMP/FCMP
 
 STATUS_PROCESSO: "FATURADO" ✓
 STATUS_CALCULO_MEDIAS: "CALCULADO" ✓
 MES_ANO_FATURAMENTO: "09/2025"
 TCMP_JSON: {"Alessandro Cappi": 0.05}  (calculado)
 FCMP_JSON: {"Alessandro Cappi": 0.89}  (calculado)
 COLABORADORES_ENVOLVIDOS: "Alessandro Cappi"

┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: PAGAMENTOS SUBSEQUENTES (parcelas)                      │
└─────────────────────────────────────────────────────────────────┘
 
 Ação: Atualizar valores acumulados
 
 TOTAL_PAGAMENTOS_REGULARES: R$ 100,00  (+ nova parcela)
 TOTAL_PAGO_ACUMULADO: R$ 100,00
 SALDO_A_RECEBER: R$ 0,00
 STATUS_PAGAMENTO: "COMPLETO" ✓
 TOTAL_COMISSAO_REGULARES: R$ 4,45  (comissões calculadas)
 TOTAL_COMISSAO_ACUMULADA: R$ 4,45
 QUANTIDADE_PAGAMENTOS: 2
```

### Fórmulas de Atualização do ESTADO

#### Ao receber um pagamento:

```python
# Atualizar valores pagos
if tipo == "ADIANTAMENTO":
    TOTAL_ANTECIPACOES += valor
    TOTAL_COMISSAO_ANTECIPACOES += soma_comissoes
else:  # PAGAMENTO_REGULAR
    TOTAL_PAGAMENTOS_REGULARES += valor
    TOTAL_COMISSAO_REGULARES += soma_comissoes

# Recalcular totais
TOTAL_PAGO_ACUMULADO = TOTAL_ANTECIPACOES + TOTAL_PAGAMENTOS_REGULARES
TOTAL_COMISSAO_ACUMULADA = TOTAL_COMISSAO_ANTECIPACOES + TOTAL_COMISSAO_REGULARES
SALDO_A_RECEBER = VALOR_TOTAL_PROCESSO - TOTAL_PAGO_ACUMULADO

# Atualizar status de pagamento
if TOTAL_PAGO_ACUMULADO >= VALOR_TOTAL_PROCESSO:
    STATUS_PAGAMENTO = "COMPLETO"
elif TOTAL_PAGO_ACUMULADO > 0:
    STATUS_PAGAMENTO = "PARCIAL"
else:
    STATUS_PAGAMENTO = "PENDENTE"

# Atualizar contadores
QUANTIDADE_PAGAMENTOS += 1
if DATA_PRIMEIRO_PAGAMENTO is null:
    DATA_PRIMEIRO_PAGAMENTO = data_pagamento
DATA_ULTIMO_PAGAMENTO = data_pagamento
ULTIMA_ATUALIZACAO = agora()
```

---

## Cálculo de TCMP

### Passo a Passo Detalhado

**Entrada**: Processo "999999"

**1. Buscar todos os itens do processo na Análise Comercial**

```sql
SELECT * FROM Analise_Comercial_Completa 
WHERE Processo = '999999'
```

Resultado:
```
Linha 1: Valor=R$ 100, Linha=SSO, Grupo=Detector Portátil, Subgrupo=MicroClip, Tipo=Produto
```

**2. Para cada item, identificar colaboradores**

```
Colaboradores Operacionais (direto da Análise Comercial):
- Consultor Interno: "ANDREY.ANDRADE"
- Representante-pedido: "ANDRÉ LUIS GONCALVES CAMARGO"

Colaboradores de Gestão (via ATRIBUICOES):
Busca: WHERE linha='SSO' AND grupo='Detector Portátil' 
       AND subgrupo='MicroClip' AND tipo='Produto'
Resultado: Alessandro Cappi (id: C018, cargo: Gerente Linha)
```

**3. Filtrar apenas colaboradores que recebem por recebimento**

```
Colaboradores Totais: ["ANDREY.ANDRADE", "ANDRÉ LUIS GONCALVES CAMARGO", "Alessandro Cappi"]

Filtragem (cargo == "Gerente Linha"):
Colaboradores Filtrados: ["Alessandro Cappi"] ✓
```

**4. Para cada colaborador, buscar a regra de comissão de cada item**

```python
colaborador = "Alessandro Cappi"
cargo = "Gerente Linha"

# Item 1
contexto = ("SSO", "Detector Portátil", "MicroClip", "Produto")
regra = buscar_regra_comissao(linha="SSO", grupo="Detector Portátil", 
                                subgrupo="MicroClip", tipo_mercadoria="Produto",
                                cargo="Gerente Linha")

# Resultado da CONFIG_COMISSAO:
taxa_rateio_maximo_pct = 10%  (0,10)
fatia_cargo_pct = 50%  (0,50)

# Taxa final do item
taxa_item = 0,10 × 0,50 = 0,05 (5%)
```

**5. Calcular TCMP (média ponderada)**

```python
# Para o colaborador "Alessandro Cappi":
valores = [100]  # Valor dos itens
taxas = [0.05]   # Taxa de cada item

TCMP = sum(valores[i] × taxas[i]) / sum(valores)
TCMP = (100 × 0.05) / 100
TCMP = 5 / 100
TCMP = 0.05 (5%)
```

**Resultado Final**:
```json
{
  "Alessandro Cappi": 0.05
}
```

### Código Implementado

```python
# src/recebimento/core/metricas_calculator.py

def calcular_metricas_processo(self, processo, mes_apuracao, ano_apuracao):
    # 1. Buscar itens do processo
    itens = df_comercial[df_comercial["Processo"] == processo]
    
    # 2. Identificar colaboradores que recebem por recebimento
    colaboradores = identificador.identificar_colaboradores(processo)
    
    # 3. Para cada colaborador, acumular valores e taxas
    dados_por_colaborador = {}
    for colab in colaboradores:
        dados_por_colaborador[colab["nome"]] = {
            "valores": [],
            "taxas": []
        }
    
    # 4. Para cada item
    for item in itens:
        valor_item = item["Valor Realizado"]
        
        for colab in colaboradores:
            # Buscar regra de comissão
            regra = _get_regra_comissao(
                linha=item["Negócio"],
                grupo=item["Grupo"],
                subgrupo=item["Subgrupo"],
                tipo_mercadoria=item["Tipo de Mercadoria"],
                cargo=colab["cargo"]
            )
            
            taxa_rateio = regra["taxa_rateio_maximo_pct"] / 100.0
            fatia_cargo = regra["fatia_cargo_pct"] / 100.0
            taxa = taxa_rateio * fatia_cargo
            
            # Acumular
            dados_por_colaborador[colab["nome"]]["valores"].append(valor_item)
            dados_por_colaborador[colab["nome"]]["taxas"].append(taxa)
    
    # 5. Calcular TCMP para cada colaborador
    tcmp_dict = {}
    for nome, dados in dados_por_colaborador.items():
        valores = np.array(dados["valores"])
        taxas = np.array(dados["taxas"])
        
        if len(valores) > 0 and valores.sum() > 0:
            tcmp_dict[nome] = (taxas * valores).sum() / valores.sum()
        else:
            tcmp_dict[nome] = 0.0
    
    return {"TCMP": tcmp_dict, "FCMP": fcmp_dict}
```

---

## Cálculo de FCMP

### Passo a Passo Detalhado

O FCMP segue a mesma lógica do TCMP, mas ao invés de calcular a média das **taxas**, calcula a média dos **Fatores de Correção** (FC).

**1. Buscar todos os itens do processo** (igual ao TCMP)

**2. Identificar colaboradores** (igual ao TCMP)

**3. Para cada item de cada colaborador, calcular o FC**

O FC é calculado através da mesma lógica das comissões por faturamento:

```python
# Componentes do FC (exemplos):
# - Faturamento Linha
# - Conversão Linha
# - Faturamento Individual
# - Conversão Individual
# - Rentabilidade
# - Retenção de Clientes
# - Metas de Fornecedor

# Para cada componente:
componente_fc = min(realizado / meta, cap_atingimento) * peso

# FC final:
fc = min(soma_componentes, cap_fc_max)  # Geralmente cap_fc_max = 1.0
```

**Exemplo para Item 1, Colaborador "Alessandro Cappi":**

```
Componente Rentabilidade:
  - Realizado: 19,13%
  - Meta: 17,05%
  - Atingimento: 19,13% / 17,05% = 1,122
  - Atingimento (cap 1.0): min(1.122, 1.0) = 1.0
  - Peso: 0,2 (20%)
  - Componente FC: 1.0 × 0,2 = 0,20

[... outros componentes ...]

FC Total: 0,20 + 0,15 + ... = 0,89 (89%)
FC Final: min(0,89, 1,0) = 0,89
```

**4. Calcular FCMP (média ponderada dos FCs)**

```python
# Para o colaborador "Alessandro Cappi":
valores = [100]  # Valor dos itens
fcs = [0.89]     # FC de cada item

FCMP = sum(valores[i] × fcs[i]) / sum(valores)
FCMP = (100 × 0.89) / 100
FCMP = 89 / 100
FCMP = 0.89 (89%)
```

**Resultado Final**:
```json
{
  "Alessandro Cappi": 0.89
}
```

### Código Implementado

```python
# src/recebimento/core/metricas_calculator.py

def calcular_metricas_processo(self, processo, mes_apuracao, ano_apuracao):
    # ... (identificação de colaboradores e itens)
    
    # Para cada item
    for item in itens:
        valor_item = item["Valor Realizado"]
        
        for colab in colaboradores:
            # Calcular FC usando função existente
            fc, _ = self.calc_comissao._calcular_fc_para_item(
                nome_colab=colab["nome"],
                cargo_colab=colab["cargo"],
                item_faturado=item.to_dict(),
                mes_apuracao_override=mes_apuracao,
                ano_apuracao_override=ano_apuracao
            )
            
            # Acumular
            dados_por_colaborador[colab["nome"]]["valores"].append(valor_item)
            dados_por_colaborador[colab["nome"]]["fcs"].append(fc)
    
    # Calcular FCMP para cada colaborador
    fcmp_dict = {}
    for nome, dados in dados_por_colaborador.items():
        valores = np.array(dados["valores"])
        fcs = np.array(dados["fcs"])
        
        if len(valores) > 0 and valores.sum() > 0:
            fcmp_dict[nome] = (fcs * valores).sum() / valores.sum()
        else:
            fcmp_dict[nome] = 0.0
    
    return {"TCMP": tcmp_dict, "FCMP": fcmp_dict}
```

---

## Comissões por Adiantamento

### Quando Acontece

- Cliente paga **antes** do processo ser faturado
- Documento começa com "COT"
- Exemplo: "COT123456"

### Fórmula

```
Comissão_Adiantamento = Valor_Pago × TCMP × 1,0
```

**Por quê FC = 1,0?**
- O processo ainda não foi faturado
- Não sabemos o desempenho real das metas
- Assumimos que o colaborador atingirá 100% das metas

### Exemplo Prático

```
Processo: "123456"
Documento: "COT123456"
Valor Pago: R$ 1.000,00
Colaborador: "Alessandro Cappi"
TCMP: 0,05 (5%)

Cálculo:
Comissão = R$ 1.000,00 × 0,05 × 1,0
Comissão = R$ 50,00
```

### Atualização do ESTADO

```python
# Atualizar valores
TOTAL_ANTECIPACOES += 1000.00
TOTAL_PAGO_ACUMULADO = TOTAL_ANTECIPACOES + TOTAL_PAGAMENTOS_REGULARES
SALDO_A_RECEBER = VALOR_TOTAL_PROCESSO - TOTAL_PAGO_ACUMULADO

# Atualizar comissões
TOTAL_COMISSAO_ANTECIPACOES += 50.00
TOTAL_COMISSAO_ACUMULADA = TOTAL_COMISSAO_ANTECIPACOES + TOTAL_COMISSAO_REGULARES

# Atualizar contadores
QUANTIDADE_PAGAMENTOS += 1
if DATA_PRIMEIRO_PAGAMENTO is null:
    DATA_PRIMEIRO_PAGAMENTO = data_pagamento
DATA_ULTIMO_PAGAMENTO = data_pagamento
```

### Código Implementado

```python
# src/recebimento/core/comissao_calculator.py

def calcular_adiantamento(self, processo, valor, tcmp_dict, documento, data_pagamento):
    comissoes = []
    
    for colaborador, tcmp in tcmp_dict.items():
        if tcmp <= 0:
            continue
        
        # FC sempre 1.0 para adiantamentos
        fc = 1.0
        comissao = valor * tcmp * fc
        
        comissoes.append({
            'processo': processo,
            'documento': documento,
            'data_pagamento': data_pagamento,
            'valor_pago': valor,
            'nome_colaborador': colaborador,
            'tcmp': tcmp,
            'fc': fc,
            'comissao_calculada': comissao,
            'tipo_lancamento': 'Adiantamento'
        })
    
    return comissoes
```

---

## Comissões por Pagamento Regular

### Quando Acontece

- Cliente paga **depois** do processo ser faturado
- Documento é um número de NF
- Exemplo: "048341"
- **Pré-requisito**: TCMP e FCMP já devem estar calculados e salvos no ESTADO

### Fórmula

```
Comissão_Regular = Valor_Pago × TCMP × FCMP
```

**Por quê usar FCMP?**
- O processo já foi faturado
- Já conhecemos o desempenho real das metas
- O FCMP reflete esse desempenho

### Exemplo Prático

```
Processo: "999999"
Documento: "048341"
Valor Pago: R$ 50,00
Colaborador: "Alessandro Cappi"
TCMP: 0,05 (5%)
FCMP: 0,89 (89%)

Cálculo:
Comissão = R$ 50,00 × 0,05 × 0,89
Comissão = R$ 50,00 × 0,0445
Comissão = R$ 2,23
```

### Fluxo de Cálculo

```
1. Recebe pagamento de R$ 50,00 (documento "048341")
   └─ Mapeia para Processo "999999"

2. Verifica ESTADO para o processo "999999"
   ├─ STATUS_CALCULO_MEDIAS == "CALCULADO"? 
   │  └─ SIM ✓ → Carrega TCMP/FCMP do ESTADO
   │     TCMP: {"Alessandro Cappi": 0.05}
   │     FCMP: {"Alessandro Cappi": 0.89}
   │
   └─ STATUS_CALCULO_MEDIAS == "PENDENTE"?
      └─ Verifica se processo foi faturado agora
         ├─ Status Processo == "FATURADO" E Numero NF preenchido?
         │  └─ SIM ✓ → Calcula TCMP/FCMP agora
         │     └─ Salva no ESTADO
         │
         └─ NÃO → Não calcula comissão (AVISO)

3. Calcula comissão para cada colaborador
   └─ Alessandro Cappi:
      └─ R$ 50,00 × 0,05 × 0,89 = R$ 2,23

4. Atualiza ESTADO
   ├─ TOTAL_PAGAMENTOS_REGULARES: += R$ 50,00
   ├─ TOTAL_COMISSAO_REGULARES: += R$ 2,23
   └─ QUANTIDADE_PAGAMENTOS: += 1
```

### Atualização do ESTADO

```python
# Atualizar valores
TOTAL_PAGAMENTOS_REGULARES += 50.00
TOTAL_PAGO_ACUMULADO = TOTAL_ANTECIPACOES + TOTAL_PAGAMENTOS_REGULARES
SALDO_A_RECEBER = VALOR_TOTAL_PROCESSO - TOTAL_PAGO_ACUMULADO

# Atualizar comissões
TOTAL_COMISSAO_REGULARES += 2.23
TOTAL_COMISSAO_ACUMULADA = TOTAL_COMISSAO_ANTECIPACOES + TOTAL_COMISSAO_REGULARES

# Atualizar status de pagamento
if TOTAL_PAGO_ACUMULADO >= VALOR_TOTAL_PROCESSO:
    STATUS_PAGAMENTO = "COMPLETO"
else:
    STATUS_PAGAMENTO = "PARCIAL"

# Atualizar contadores
QUANTIDADE_PAGAMENTOS += 1
DATA_ULTIMO_PAGAMENTO = data_pagamento
```

### Código Implementado

```python
# src/recebimento/core/comissao_calculator.py

def calcular_regular(self, processo, valor, tcmp_dict, fcmp_dict, documento, 
                      data_pagamento, mes_faturamento):
    comissoes = []
    
    for colaborador, tcmp in tcmp_dict.items():
        if tcmp <= 0:
            continue
        
        # Obter FCMP do colaborador
        fcmp = fcmp_dict.get(colaborador, 1.0)
        
        if fcmp <= 0:
            fcmp = 1.0  # Fallback
        
        comissao = valor * tcmp * fcmp
        
        comissoes.append({
            'processo': processo,
            'documento': documento,
            'data_pagamento': data_pagamento,
            'valor_pago': valor,
            'nome_colaborador': colaborador,
            'tcmp': tcmp,
            'fcmp': fcmp,
            'comissao_calculada': comissao,
            'tipo_lancamento': 'Pagamento Regular',
            'mes_faturamento': mes_faturamento
        })
    
    return comissoes
```

---

## Reconciliações (A Implementar)

### Conceito

A **Reconciliação** é um ajuste que acontece no **mês do faturamento** quando um processo teve **adiantamentos** pagos com FC = 1,0, mas o FCMP real acabou sendo diferente de 1,0.

### Quando Acontece

1. Processo teve **adiantamentos** (COT)
2. Processo é **faturado** (Status = "FATURADO")
3. **FCMP ≠ 1,0** (geralmente FCMP < 1,0)

### Por Quê é Necessária?

```
Exemplo:
- Adiantamento de R$ 1.000,00 foi pago
- Comissão calculada: R$ 1.000 × 0,05 × 1,0 = R$ 50,00
- Mas FCMP real: 0,89

Se o pagamento fosse feito após o faturamento:
- Comissão correta: R$ 1.000 × 0,05 × 0,89 = R$ 44,50

Diferença (Reconciliação):
- R$ 50,00 - R$ 44,50 = R$ 5,50 (a menos para o colaborador)
- Ou seja: R$ 1.000 × 0,05 × (0,89 - 1,0) = -R$ 5,50
```

### Fórmula de Reconciliação

**Para o processo inteiro:**

```
Saldo_Reconciliacao_Processo = Σ_colaboradores (
    Total_Adiantado × w_colaborador × (FCMP_colaborador - 1,0)
)

Onde:
- Total_Adiantado = TOTAL_ANTECIPACOES do ESTADO
- w_colaborador = TCMP_colaborador / Σ(TCMP_todos)  (peso do colaborador)
- FCMP_colaborador = Fator de Correção Médio Ponderado
```

**Para cada colaborador:**

```
Reconciliacao_Colaborador = (
    Total_Adiantado × w_colaborador × (FCMP_colaborador - 1,0)
)
```

### Exemplo Numérico

```
Processo "999999":
- Total_Adiantado: R$ 1.000,00
- Colaboradores:
  - Alessandro Cappi: TCMP=0,05, FCMP=0,89
  - Neimar: TCMP=0,03, FCMP=0,92

Passo 1: Calcular pesos (w_colaborador)
w_Alessandro = 0,05 / (0,05 + 0,03) = 0,05 / 0,08 = 0,625 (62,5%)
w_Neimar = 0,03 / (0,05 + 0,03) = 0,03 / 0,08 = 0,375 (37,5%)

Passo 2: Calcular reconciliação por colaborador
Reconciliacao_Alessandro = R$ 1.000 × 0,625 × (0,89 - 1,0)
                         = R$ 1.000 × 0,625 × (-0,11)
                         = -R$ 68,75

Reconciliacao_Neimar = R$ 1.000 × 0,375 × (0,92 - 1,0)
                     = R$ 1.000 × 0,375 × (-0,08)
                     = -R$ 30,00

Passo 3: Total da reconciliação do processo
Saldo_Reconciliacao = -R$ 68,75 + (-R$ 30,00) = -R$ 98,75

Interpretação:
- Alessandro Cappi recebe R$ 68,75 a menos
- Neimar recebe R$ 30,00 a menos
- Total: R$ 98,75 foi pago a mais nos adiantamentos
```

### Momento de Aplicação

A reconciliação é **aplicada no mês do faturamento** e aparece como:
- Uma linha adicional na aba `RECONCILIACOES`
- Um ajuste no `RESUMO_COLABORADOR` (subtrai da comissão total)

### Estrutura da Aba RECONCILIACOES (A Implementar)

| Coluna | Descrição |
|--------|-----------|
| PROCESSO | ID do processo |
| MES_ANO_FATURAMENTO | Mês/ano em que foi faturado |
| TOTAL_ADIANTADO | Total de adiantamentos |
| COLABORADOR | Nome do colaborador |
| TCMP | Taxa de Comissão Média Ponderada |
| FCMP | Fator de Correção Médio Ponderado |
| PESO_COLABORADOR | Proporção do colaborador (w) |
| DIFERENCA_FC | FCMP - 1,0 |
| RECONCILIACAO | Valor da reconciliação |

---

## Fluxo Completo de Execução

### Fase 1: Inicialização

```
1. Usuário informa: Mês = 9, Ano = 2025
2. Carregar arquivos de entrada:
   ├─ Regras_Comissoes.xlsx (todas as abas)
   ├─ Analise_Comercial_Completa.csv
   ├─ Análise Financeira.xlsx
   └─ Estado anterior (se existir)
```

### Fase 2: Processamento de Pagamentos

```
Para cada linha em Análise Financeira (filtrado por mês/ano):
│
├─ 1. Extrair dados do pagamento
│   ├─ Documento: "048341"
│   ├─ Valor: R$ 50,00
│   └─ Data: 2025-09-15
│
├─ 2. Mapear Documento → Processo
│   ├─ Tipo: PAGAMENTO_REGULAR (não começa com COT)
│   ├─ Normalizar: "48341"
│   └─ Buscar em Analise_Comercial_Completa
│       └─ Processo encontrado: "999999" ✓
│
├─ 3. Verificar se processo existe no ESTADO
│   ├─ NÃO → Criar novo registro
│   │   ├─ PROCESSO: "999999"
│   │   ├─ VALOR_TOTAL_PROCESSO: R$ 100,00 (da Análise Comercial)
│   │   └─ ... (valores iniciais)
│   └─ SIM → Carregar registro existente
│
├─ 4. Processar conforme tipo
│   │
│   ├─ ADIANTAMENTO (COT):
│   │   ├─ Calcular TCMP (média ponderada das taxas)
│   │   ├─ Calcular Comissões: Valor × TCMP × 1,0
│   │   └─ Atualizar ESTADO:
│   │       ├─ TOTAL_ANTECIPACOES += valor
│   │       └─ TOTAL_COMISSAO_ANTECIPACOES += comissões
│   │
│   └─ PAGAMENTO_REGULAR:
│       ├─ Verificar TCMP/FCMP no ESTADO
│       │   ├─ Já calculados? → Usar do ESTADO
│       │   └─ Não calculados? → Calcular agora (se faturado)
│       ├─ Calcular Comissões: Valor × TCMP × FCMP
│       └─ Atualizar ESTADO:
│           ├─ TOTAL_PAGAMENTOS_REGULARES += valor
│           └─ TOTAL_COMISSAO_REGULARES += comissões
│
└─ 5. Salvar no ESTADO
```

### Fase 3: Cálculo de Métricas para Processos Faturados

```
Para cada processo no ESTADO:
│
├─ 1. Verificar se processo foi faturado no mês
│   ├─ Status Processo == "FATURADO"?
│   ├─ Numero NF preenchido?
│   └─ Dt Emissão == mês/ano de apuração?
│
├─ 2. SE faturado E métricas não calculadas:
│   ├─ Buscar todos os itens do processo
│   ├─ Identificar colaboradores que recebem por recebimento
│   ├─ Para cada colaborador:
│   │   ├─ Calcular TCMP (média ponderada das taxas)
│   │   └─ Calcular FCMP (média ponderada dos FCs)
│   └─ Salvar no ESTADO:
│       ├─ TCMP_JSON: {"Alessandro Cappi": 0.05}
│       ├─ FCMP_JSON: {"Alessandro Cappi": 0.89}
│       ├─ STATUS_CALCULO_MEDIAS: "CALCULADO"
│       └─ MES_ANO_FATURAMENTO: "09/2025"
│
└─ 3. SE faturado E houve adiantamentos:
    └─ Calcular Reconciliação (A Implementar)
```

### Fase 4: Geração de Saída

```
1. Preparar DataFrames:
   ├─ COMISSOES_ADIANTAMENTOS (lista de comissões de adiantamentos)
   ├─ COMISSOES_REGULARES (lista de comissões regulares)
   ├─ RECONCILIACOES (vazio - a implementar)
   ├─ ESTADO (snapshot do estado atual)
   └─ AVISOS (documentos não mapeados)

2. Gerar arquivo Excel:
   └─ Comissoes_Recebimento_09_2025.xlsx
      ├─ Aba: COMISSOES_ADIANTAMENTOS
      ├─ Aba: COMISSOES_REGULARES
      ├─ Aba: RECONCILIACOES
      ├─ Aba: ESTADO
      └─ Aba: AVISOS

3. Logs de sucesso
```

---

## Exemplos Práticos

### Exemplo 1: Pagamento Regular Simples

**Cenário:**
- Processo "999999" já foi faturado em 09/2025
- Cliente paga parcela de R$ 50,00
- TCMP e FCMP já estão salvos no ESTADO

**Entrada (Análise Financeira):**
```
Documento: 048341
Valor Líquido: 50,00
Data de Baixa: 2025-09-15
Tipo de Baixa: B
```

**Mapeamento:**
```
048341 → Normaliza → 48341
Busca em Analise_Comercial_Completa onde Numero NF = 48341
Encontra: Processo = 999999 ✓
```

**Busca no ESTADO:**
```
Processo: 999999
STATUS_CALCULO_MEDIAS: CALCULADO
TCMP_JSON: {"Alessandro Cappi": 0.05}
FCMP_JSON: {"Alessandro Cappi": 0.89}
```

**Cálculo de Comissão:**
```
Colaborador: Alessandro Cappi
Valor: R$ 50,00
TCMP: 0,05
FCMP: 0,89

Comissão = R$ 50,00 × 0,05 × 0,89
Comissão = R$ 2,23
```

**Atualização do ESTADO:**
```
TOTAL_PAGAMENTOS_REGULARES: R$ 0,00 → R$ 50,00
TOTAL_COMISSAO_REGULARES: R$ 0,00 → R$ 2,23
TOTAL_PAGO_ACUMULADO: R$ 0,00 → R$ 50,00
SALDO_A_RECEBER: R$ 100,00 → R$ 50,00
STATUS_PAGAMENTO: PENDENTE → PARCIAL
QUANTIDADE_PAGAMENTOS: 0 → 1
```

**Saída (COMISSOES_REGULARES):**
```
processo: 999999
documento: 048341
valor_pago: 50,00
nome_colaborador: Alessandro Cappi
tcmp: 0,05
fcmp: 0,89
comissao_calculada: 2,23
mes_faturamento: 09/2025
```

---

### Exemplo 2: Adiantamento Seguido de Pagamento Regular

**Fase 1: Adiantamento (Agosto/2025)**

**Entrada:**
```
Documento: COT999999
Valor Líquido: 1000,00
Data de Baixa: 2025-08-10
```

**Ações:**
```
1. Mapear: COT999999 → Processo 999999
2. Tipo: ADIANTAMENTO
3. Calcular TCMP (processo ainda não faturado):
   - TCMP = 0,05 (5%)
4. Calcular Comissão:
   - R$ 1.000,00 × 0,05 × 1,0 = R$ 50,00
5. Atualizar ESTADO:
   - TOTAL_ANTECIPACOES: R$ 1.000,00
   - TOTAL_COMISSAO_ANTECIPACOES: R$ 50,00
   - STATUS_CALCULO_MEDIAS: PENDENTE
```

**Fase 2: Faturamento (Setembro/2025)**

**Entrada (Analise_Comercial_Completa):**
```
Processo: 999999
Status Processo: FATURADO
Numero NF: 048341
Dt Emissão: 2025-09-15
```

**Ações:**
```
1. Processo aparece como FATURADO no mês 09/2025
2. Calcular TCMP e FCMP:
   - TCMP: 0,05 (5%)
   - FCMP: 0,89 (89%)
3. Salvar no ESTADO:
   - TCMP_JSON: {"Alessandro Cappi": 0.05}
   - FCMP_JSON: {"Alessandro Cappi": 0.89}
   - STATUS_CALCULO_MEDIAS: CALCULADO
   - MES_ANO_FATURAMENTO: 09/2025
4. (A Implementar) Calcular Reconciliação:
   - Total_Adiantado: R$ 1.000,00
   - w_Alessandro: 1,0 (100% - único colaborador)
   - Reconciliação: R$ 1.000 × 1,0 × (0,89 - 1,0) = -R$ 110,00
```

**Fase 3: Pagamento Regular (Outubro/2025)**

**Entrada:**
```
Documento: 048341
Valor Líquido: 500,00
Data de Baixa: 2025-10-20
```

**Ações:**
```
1. Mapear: 048341 → Processo 999999
2. Carregar TCMP/FCMP do ESTADO
3. Calcular Comissão:
   - R$ 500,00 × 0,05 × 0,89 = R$ 22,25
4. Atualizar ESTADO:
   - TOTAL_PAGAMENTOS_REGULARES: R$ 0,00 → R$ 500,00
   - TOTAL_COMISSAO_REGULARES: R$ 0,00 → R$ 22,25
   - TOTAL_PAGO_ACUMULADO: R$ 1.000,00 → R$ 1.500,00
```

**Resumo Final para Alessandro Cappi:**
```
Mês          | Tipo           | Valor    | Comissão | Obs
-------------|----------------|----------|----------|------------------
Agosto/2025  | Adiantamento   | 1.000,00 | 50,00    | FC = 1,0
Setembro/2025| Reconciliação  | -        | -110,00  | Ajuste (FCMP=0,89)
Outubro/2025 | Pag. Regular   | 500,00   | 22,25    | FCMP=0,89
-------------|----------------|----------|----------|------------------
TOTAL        |                | 1.500,00 | -37,75   |

Interpretação:
- Pagou R$ 50,00 no adiantamento (considerando FC=1,0)
- Descobriu que FCMP real = 0,89 (deveria ter pago R$ 44,50)
- Ajuste de -R$ 110,00 no mês do faturamento (reconciliação)
- Pagamento regular de R$ 22,25 (já com FCMP correto)
- Saldo final: R$ 50,00 - R$ 110,00 + R$ 22,25 = -R$ 37,75
```

---

## Glossário de Termos

| Termo | Significado |
|-------|-------------|
| **TCMP** | Taxa de Comissão Média Ponderada - média das taxas de comissão ponderada pelo valor dos itens |
| **FCMP** | Fator de Correção Médio Ponderado - média dos FCs ponderada pelo valor dos itens |
| **FC** | Fator de Correção - multiplicador baseado no atingimento de metas (0,0 a 1,0) |
| **PE** | Percentual de Elegibilidade - fatia do cargo na comissão (`fatia_cargo_pct`) |
| **Taxa de Rateio** | Percentual máximo de comissão sobre o valor do item (`taxa_rateio_maximo_pct`) |
| **Adiantamento (COT)** | Pagamento antecipado, antes do faturamento (FC = 1,0) |
| **Pagamento Regular** | Pagamento após o faturamento (usa FCMP) |
| **Reconciliação** | Ajuste aplicado no mês do faturamento para corrigir adiantamentos |
| **Estado** | Registro persistente de processos e seus pagamentos/comissões acumulados |
| **Processo** | Pedido comercial único, pode conter múltiplos itens |
| **Item** | Linha individual de um processo (produto/serviço específico) |

---

## Perguntas Frequentes (FAQ)

### 1. Por que alguns processos não têm comissões calculadas?

**Resposta**: Pode haver várias razões:
- Nenhum colaborador que recebe por recebimento está envolvido no processo
- O processo ainda não foi faturado (necessário para calcular TCMP/FCMP)
- O TCMP calculado é zero (não há regras de comissão para o contexto)

### 2. O que acontece se um processo for parcialmente pago?

**Resposta**: O ESTADO mantém registro de:
- `TOTAL_PAGO_ACUMULADO`: quanto já foi pago
- `SALDO_A_RECEBER`: quanto ainda falta pagar
- `STATUS_PAGAMENTO`: "PARCIAL" até ser pago completamente

### 3. Como funciona o cálculo quando há múltiplos colaboradores?

**Resposta**: Cada colaborador tem seu próprio TCMP e FCMP calculados independentemente. A comissão é calculada para cada um e somada.

### 4. O que acontece se o FCMP for maior que 1,0?

**Resposta**: O sistema aplica um cap (limite) de 1,0 no FC de cada item antes de calcular o FCMP. Portanto, o FCMP nunca será maior que 1,0.

### 5. Por que a reconciliação é negativa?

**Resposta**: Porque o FCMP real (geralmente < 1,0) é menor que o assumido nos adiantamentos (1,0). O ajuste retira a diferença que foi paga a mais.

### 6. Como identificar problemas de mapeamento?

**Resposta**: Consulte a aba **AVISOS** no arquivo de saída. Ela lista todos os documentos que não puderam ser mapeados para um processo e o motivo.

### 7. O que significa "Processo PENDENTE"?

**Resposta**: O processo ainda não foi faturado. TCMP/FCMP só podem ser calculados após o faturamento.

### 8. Posso ter adiantamentos e pagamentos regulares no mesmo mês?

**Resposta**: Não é comum, mas tecnicamente sim. Se um processo for faturado no mesmo mês em que há um pagamento, a reconciliação será aplicada imediatamente.

---

## Arquitetura do Código

### Módulos Principais

```
src/recebimento/
│
├── recebimento_orchestrator.py
│   └─ Coordena todo o fluxo de execução
│
├── io/
│   ├── analise_financeira_loader.py
│   │   └─ Carrega e filtra Análise Financeira.xlsx
│   └── output_generator.py
│       └─ Gera arquivo Excel de saída
│
├── core/
│   ├── process_mapper.py
│   │   └─ Mapeia Documento → Processo
│   ├── identificador_colaboradores.py
│   │   └─ Identifica colaboradores que recebem por recebimento
│   ├── metricas_calculator.py
│   │   └─ Calcula TCMP e FCMP
│   └── comissao_calculator.py
│       └─ Calcula comissões (adiantamento e regular)
│
├── estado/
│   ├── state_manager.py
│   │   └─ Gerencia leitura/escrita do ESTADO
│   └── state_schema.py
│       └─ Define estrutura da aba ESTADO
│
└── utils/
    └─ (reservado para utilitários futuros)
```

### Fluxo de Dados

```
[Análise Financeira.xlsx]
          ↓
   [AnaliseFinanceiraLoader]
          ↓
   [RecebimentoOrchestrator] ←→ [StateManager] ←→ [ESTADO]
          ↓
   [ProcessMapper] → [Analise_Comercial_Completa.csv]
          ↓
   [IdentificadorColaboradores] → [ATRIBUICOES.csv]
          ↓
   [MetricasCalculator] → [CONFIG_COMISSAO.csv]
          ↓
   [ComissaoCalculator]
          ↓
   [RecebimentoOutputGenerator]
          ↓
   [Comissoes_Recebimento_MM_AAAA.xlsx]
```

---

## Próximos Passos (Roadmap)

### Fase Atual: ✅ Comissões por Recebimento
- ✅ Cálculo de TCMP
- ✅ Cálculo de FCMP
- ✅ Comissões por adiantamento
- ✅ Comissões por pagamento regular
- ✅ Gestão do ESTADO
- ✅ Geração de arquivo de saída

### Fase Futura: 🔄 Reconciliações
- ⏳ Lógica de cálculo de reconciliação
- ⏳ Aba RECONCILIACOES detalhada
- ⏳ Aplicação de ajustes no RESUMO_COLABORADOR
- ⏳ Integração com arquivo principal de comissões

---

**Versão do Documento**: 1.0  
**Data de Criação**: 12/11/2025  
**Última Atualização**: 12/11/2025  
**Autor**: Sistema de Documentação Automatizada

