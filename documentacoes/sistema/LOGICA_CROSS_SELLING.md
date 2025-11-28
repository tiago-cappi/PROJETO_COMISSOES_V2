# 📋 LÓGICA DE CROSS-SELLING

**Data de Atualização**: 28 de Novembro de 2025

---

## 🎯 O QUE É CROSS-SELLING?

Cross-selling ocorre quando um **Consultor Externo** realiza uma venda em uma **linha de negócio (Negócio)** para a qual ele **não possui atribuição**. Ou seja, ele está vendendo fora de sua área normal de atuação.

---

## 🔍 COMO O CROSS-SELLING É DETECTADO?

O sistema detecta cross-selling verificando as seguintes condições:

### 1. Coluna "Gerente Comercial-Pedido" Preenchida
- A coluna `Gerente Comercial-Pedido` no arquivo de faturados deve conter o nome de um colaborador
- Esta coluna indica quem foi o responsável pela venda cross-selling

### 2. Colaborador é Consultor Externo
- O colaborador indicado em `Gerente Comercial-Pedido` deve ter o cargo "Consultor Externo"
- Verificado na aba `COLABORADORES` do arquivo de configuração

### 3. Colaborador NÃO Possui Atribuição para a Linha
- O Consultor Externo não deve ter atribuição para o `Negócio` (linha) do item vendido
- Verificado na aba `ATRIBUICOES` do arquivo de configuração

### 4. ⚠️ Colaborador DEVE Estar na Aba CROSS_SELLING
- **IMPORTANTE**: O colaborador DEVE estar explicitamente listado na aba `CROSS_SELLING`
- Se não estiver cadastrado, o cross-selling **NÃO será processado**
- Um aviso será gerado informando que o colaborador não está elegível

---

## 📊 ESTRUTURA DA ABA CROSS_SELLING

A aba `CROSS_SELLING` no arquivo `REGRAS_COMISSOES.xlsx` contém:

| Coluna | Descrição |
|--------|-----------|
| `colaborador` | Nome do Consultor Externo elegível para cross-selling |
| `taxa_cross_selling_pct` | Taxa de comissão (%) que será aplicada ao valor do item |

### Exemplo:
| colaborador | taxa_cross_selling_pct |
|-------------|------------------------|
| Mateus Machado | 1.5 |
| André Camargo | 1.0 |
| Leonardo Camargo | 2.0 |

---

## 💰 CÁLCULO DA COMISSÃO DE CROSS-SELLING

A comissão de cross-selling é calculada de forma **fixa**, sem aplicação de fatores de correção:

```
Comissão CS = Valor Realizado × (taxa_cross_selling_pct / 100)
```

### Características:
- ✅ **Taxa fixa**: Não é afetada pelo cumprimento de metas
- ✅ **Sem fator de correção (FC)**: A taxa é aplicada diretamente
- ✅ **Por colaborador**: Cada consultor pode ter sua própria taxa
- ✅ **Marcada como "CROSS_SELLING"**: Na coluna `observacao` da planilha de saída

---

## 🔄 OPÇÕES A E B

Quando há cross-selling, o usuário deve escolher como tratar os demais colaboradores do processo:

### Opção A - Subtrair do Rateio
- A taxa de cross-selling é **subtraída** da `taxa_rateio_maximo_pct`
- Os demais colaboradores (Consultor Interno, Representante-Pedido) dividem o restante
- Exemplo: Se taxa_rateio = 5% e taxa_cs = 1%, os demais dividem 4%

### Opção B - Adicional
- A taxa de rateio permanece **intacta** para os demais colaboradores
- A comissão de cross-selling é paga **adicionalmente**
- Exemplo: Se taxa_rateio = 5% e taxa_cs = 1%, os demais dividem 5% + 1% é pago ao consultor CS

---

## ⚠️ VALIDAÇÕES E AVISOS

### Colaborador Não Cadastrado na Aba CROSS_SELLING
Se um Consultor Externo estiver na coluna `Gerente Comercial-Pedido` mas **não** estiver cadastrado na aba `CROSS_SELLING`:
- ❌ O cross-selling **NÃO será processado** para esse processo
- ⚠️ Um aviso será gerado no log de validação
- 📝 O arquivo `cs_not_eligible_log.txt` registrará o caso

### Aba CROSS_SELLING Vazia
Se a aba `CROSS_SELLING` estiver vazia:
- ❌ Nenhum cross-selling será processado
- ⚠️ Um aviso será gerado

### Taxa de CS Maior que Taxa de Rateio
Se `taxa_cross_selling_pct` > `taxa_rateio_maximo_pct`:
- ⚠️ Um aviso será gerado
- O cálculo continua, mas pode resultar em taxa zero para os demais colaboradores

---

## 📁 ARQUIVOS DE LOG

O sistema gera os seguintes arquivos de log para debug:

| Arquivo | Descrição |
|---------|-----------|
| `cs_detection_log.txt` | Casos de cross-selling detectados |
| `cs_not_eligible_log.txt` | Colaboradores não elegíveis (não cadastrados) |
| `cs_commission_log.txt` | Detalhes do cálculo da comissão |

---

## 🔧 COMO CONFIGURAR

### 1. Adicionar Consultor à Aba CROSS_SELLING
No arquivo `config/REGRAS_COMISSOES.xlsx`, aba `CROSS_SELLING`:
1. Adicione o nome exato do colaborador na coluna `colaborador`
2. Defina a taxa em `taxa_cross_selling_pct` (em %)

### 2. Garantir Cargo Correto
Na aba `COLABORADORES`:
1. O colaborador deve ter `cargo` = "Consultor Externo"
2. Ou `tipo_cargo` = "externo"

### 3. Configurar Atribuições
Na aba `ATRIBUICOES`:
1. Defina as linhas/Negócios que o consultor atende normalmente
2. Cross-selling só ocorre quando ele vende FORA dessas linhas

---

## 📝 RESUMO

| Condição | Cross-Selling? |
|----------|----------------|
| Gerente Comercial-Pedido preenchido + é Consultor Externo + sem atribuição + cadastrado em CROSS_SELLING | ✅ SIM |
| Gerente Comercial-Pedido preenchido + é Consultor Externo + sem atribuição + NÃO cadastrado em CROSS_SELLING | ❌ NÃO (aviso) |
| Gerente Comercial-Pedido vazio | ❌ NÃO |
| Gerente Comercial-Pedido preenchido + NÃO é Consultor Externo | ❌ NÃO |
| Gerente Comercial-Pedido preenchido + é Consultor Externo + TEM atribuição | ❌ NÃO |
