# 📋 GUIA COMPLETO DE TESTES - RECONCILIAÇÕES

## 🎯 Objetivo

Este guia detalha como executar testes completos da funcionalidade de reconciliações de comissões por recebimento.

---

## 📁 Arquivos Gerados

Os seguintes arquivos foram criados com dados de teste:

- ✅ `dados_entrada/Analise_Comercial_Completa.xlsx` - **10 processos** de teste
- ✅ `dados_entrada/Análise Financeira.xlsx` - **23 pagamentos** de teste
- 💾 **Backups** dos arquivos originais criados automaticamente

---

## 🧪 CENÁRIOS DE TESTE

### 📊 Resumo Geral

| ID | Processo | Descrição | Iterações | Meses |
|----|----------|-----------|-----------|-------|
| 1 | 100001 | Adiantamento simples (não faturado) | 1 | Agosto |
| 2 | 100002 | Adiantamento + Faturamento (mesmo mês) | 1 | Agosto |
| 3 | 100003 | Adiantamento (Ago) + Faturamento (Set) | 2 | Ago → Set |
| 4 | 100004 | Múltiplos adiantamentos | 2 | Ago → Set |
| 5 | 100005 | Pagamento regular direto (sem adiantamento) | 1 | Agosto |
| 6 | 100006 | Múltiplos colaboradores | 2 | Ago → Set |
| 7 | 100007 | FC = 1.0 (sem reconciliação) | 2 | Ago → Set |
| 8 | 100008 | Múltiplos pagamentos regulares | 1 | Agosto |
| 9 | 100009 | NF com 5 dígitos | 1 | Agosto |
| 10 | 100010 | Média ponderada (múltiplos itens) | 2 | Ago → Set |

---

## 🚀 COMO EXECUTAR OS TESTES

### 🔴 PREPARAÇÃO INICIAL

1. **Limpar estado anterior** (se necessário):
   ```bash
   # Apagar arquivo de estado para começar do zero
   del Estado_Processos_Recebimento.xlsx
   ```

2. **Verificar arquivos de entrada**:
   - ✅ `dados_entrada/Analise_Comercial_Completa.xlsx` existe
   - ✅ `dados_entrada/Análise Financeira.xlsx` existe

---

### 📅 TESTE 1: RODADA ÚNICA - AGOSTO/2025

**Comando:**
```bash
python calculo_comissoes.py --mes 8 --ano 2025
```

**Arquivo gerado:**
- `Comissoes_Recebimento_08_2025.xlsx`

**Cenários testados:**
- ✅ **Cenário 1** (100001): Adiantamento de R$ 5.000,00 com FC=1.0
- ✅ **Cenário 2** (100002): Adiantamento + Faturamento + **RECONCILIAÇÃO**
- ✅ **Cenário 5** (100005): 2 pagamentos regulares diretos
- ✅ **Cenário 8** (100008): 3 parcelas regulares
- ✅ **Cenário 9** (100009): NF com 5 dígitos (12345)

**Abas a verificar:**

#### 1️⃣ **COMISSOES_ADIANTAMENTOS**
Deve conter:
- Processo 100001: R$ 5.000,00 × TCMP × 1.0
- Processo 100002: R$ 7.500,00 × TCMP × 1.0
- Processo 100006: R$ 15.000,00 × TCMP × 1.0
- Processo 100007: R$ 15.000,00 × TCMP × 1.0
- Processo 100010: R$ 45.000,00 × TCMP × 1.0
- Processo 100003: R$ 10.000,00 × TCMP × 1.0
- Processo 100004: 2 linhas (R$ 8.000,00 + R$ 7.000,00)

**Total esperado:** ~7 a 9 linhas de adiantamentos

#### 2️⃣ **COMISSOES_REGULARES**
Deve conter:
- Processo 100002: R$ 7.500,00 × TCMP × FCMP
- Processo 100005: 2 linhas (R$ 6.000,00 cada) × TCMP × FCMP
- Processo 100008: 3 linhas (R$ 15k, R$ 20k, R$ 15k) × TCMP × FCMP
- Processo 100009: 2 linhas (R$ 4.000,00 cada) × TCMP × FCMP

**Total esperado:** ~8 linhas de pagamentos regulares

#### 3️⃣ **RECONCILIACOES**
Deve conter:
- **Processo 100002**: Reconciliação negativa
  - `Total_Adiantado` = R$ 7.500,00
  - `FCMP` < 1.0 (devido ao negócio RENTAL)
  - `Reconciliação` = R$ 7.500 × (FCMP - 1.0) < 0

**Validações:**
- ✅ Coluna `processo` = "100002"
- ✅ Coluna `total_adiantado_colaborador` > 0
- ✅ Coluna `fcmp` < 1.0
- ✅ Coluna `reconciliacao_valor` < 0 (negativo)
- ✅ Coluna `mes_reconciliacao` = "08/2025"

#### 4️⃣ **ESTADO**
Deve conter 10 processos (100001 a 100010)

Verificar especificamente:
- **Processo 100002**:
  - `STATUS_CALCULO_MEDIAS` = "CALCULADO"
  - `STATUS_RECONCILIACAO` = "RECONCILIADO"
  - `COMISSOES_ADIANTADAS_JSON` contém valor por colaborador
  - `TCMP_JSON` contém taxa por colaborador
  - `FCMP_JSON` contém fator por colaborador

- **Processo 100001** (não faturado):
  - `STATUS_CALCULO_MEDIAS` = "PENDENTE"
  - `STATUS_RECONCILIACAO` = "PENDENTE"

#### 5️⃣ **AVISOS**
Deve conter documentos não mapeados:
- `XYZ999`
- `COT` (sem número)

---

### 📅 TESTE 2: RODADA DUPLA - AGOSTO + SETEMBRO

#### 🟢 **PRIMEIRA RODADA - Agosto/2025**

**Comando:**
```bash
python calculo_comissoes.py --mes 8 --ano 2025
```

**Resultado esperado:**
- Adiantamentos calculados e salvos no `ESTADO`
- Processos 100003, 100004, 100006, 100007, 100010 com adiantamentos mas **SEM** reconciliação (ainda não faturados)

**Arquivo gerado:**
- `Comissoes_Recebimento_08_2025.xlsx`

**Validar:**
- ✅ `COMISSOES_ADIANTAMENTOS`: todos os COTs de Agosto
- ✅ `ESTADO`: processos com `STATUS_PROCESSO` = "PENDENTE" ou "ORCAMENTO"
- ✅ `Estado_Processos_Recebimento.xlsx` criado na raiz do projeto

---

#### 🔵 **SEGUNDA RODADA - Setembro/2025**

**IMPORTANTE:** 
- ⚠️ **NÃO APAGUE** o arquivo `Estado_Processos_Recebimento.xlsx`
- Ele contém os adiantamentos de Agosto que serão reconciliados agora

**Comando:**
```bash
python calculo_comissoes.py --mes 9 --ano 2025
```

**Arquivo gerado:**
- `Comissoes_Recebimento_09_2025.xlsx`

**Cenários testados:**
- ✅ **Cenário 3** (100003): Reconciliação após 1 mês
- ✅ **Cenário 4** (100004): Reconciliação com múltiplos adiantamentos
- ✅ **Cenário 6** (100006): Reconciliação para múltiplos colaboradores
- ✅ **Cenário 7** (100007): SEM reconciliação (FC=1.0)
- ✅ **Cenário 10** (100010): Reconciliação com média ponderada

**Abas a verificar:**

#### 1️⃣ **COMISSOES_ADIANTAMENTOS**
Deve estar **VAZIA** (nenhum COT em Setembro)

#### 2️⃣ **COMISSOES_REGULARES**
Deve conter:
- Processo 100003: R$ 10.000,00 × TCMP × FCMP
- Processo 100004: R$ 10.000,00 × TCMP × FCMP
- Processo 100006: R$ 15.000,00 × TCMP × FCMP (dividido por colaborador)
- Processo 100007: R$ 15.000,00 × TCMP × FCMP
- Processo 100010: R$ 45.000,00 × TCMP × FCMP

#### 3️⃣ **RECONCILIACOES** ⭐ **PRINCIPAL VALIDAÇÃO**

Deve conter **4 processos** com reconciliações:

##### **Processo 100003:**
- `total_adiantado_colaborador`: R$ 10.000,00
- `fcmp`: < 1.0
- `reconciliacao_valor`: negativo
- `mes_reconciliacao`: "09/2025"

##### **Processo 100004:**
- `total_adiantado_colaborador`: R$ 15.000,00 (soma de R$ 8k + R$ 7k)
- `fcmp`: < 1.0
- `reconciliacao_valor`: negativo
- `mes_reconciliacao`: "09/2025"

##### **Processo 100006:** (2 linhas - um para cada colaborador)
- Linha 1 (Alessandro Cappi):
  - `nome_colaborador`: "Alessandro Cappi"
  - `total_adiantado_colaborador`: proporcional ao valor do item dele
  - `reconciliacao_valor`: negativo
  
- Linha 2 (Leandro Daher):
  - `nome_colaborador`: "Leandro Daher"
  - `total_adiantado_colaborador`: proporcional ao valor do item dele
  - `reconciliacao_valor`: negativo

##### **Processo 100010:**
- `total_adiantado_colaborador`: R$ 45.000,00
- `fcmp`: calculado como média ponderada dos 3 itens
- `reconciliacao_valor`: negativo

##### **Processo 100007: NÃO deve aparecer**
- ❌ Este processo **NÃO** deve ter reconciliação (FC=1.0)

#### 4️⃣ **ESTADO**
Verificar processos reconciliados:

**Processos 100003, 100004, 100006, 100010:**
- ✅ `STATUS_CALCULO_MEDIAS` = "CALCULADO"
- ✅ `STATUS_RECONCILIACAO` = "RECONCILIADO"
- ✅ `TCMP_JSON` preenchido
- ✅ `FCMP_JSON` preenchido
- ✅ `COMISSOES_ADIANTADAS_JSON` preenchido
- ✅ `MES_ANO_FATURAMENTO` = "09/2025"

**Processo 100007:**
- ✅ `STATUS_CALCULO_MEDIAS` = "CALCULADO"
- ✅ `STATUS_RECONCILIACAO` = "NAO_NECESSARIA" ou "PENDENTE"
- ✅ `FCMP_JSON` contém valor ~1.0

---

## ✅ CHECKLIST DE VALIDAÇÕES

### 📌 Validações Gerais

- [ ] Arquivo `Estado_Processos_Recebimento.xlsx` criado na raiz
- [ ] Aba `ESTADO` contém todos os processos
- [ ] Aba `AVISOS` contém documentos não mapeados
- [ ] Nenhum erro no console durante execução
- [ ] Arquivos de saída criados com sucesso

### 📌 Validações Específicas de Reconciliações

#### Agosto/2025:
- [ ] Processo 100002 tem reconciliação (faturado no mesmo mês)
- [ ] Reconciliação do 100002 é negativa (FCMP < 1.0)
- [ ] Processos 100003-100007-100010 **NÃO** têm reconciliação (ainda não faturados)

#### Setembro/2025:
- [ ] Processos 100003, 100004, 100006, 100010 têm reconciliações
- [ ] Processo 100007 **NÃO** tem reconciliação (FC=1.0)
- [ ] Processo 100006 tem 2 linhas (uma por colaborador)
- [ ] Processo 100004 considera soma de 2 adiantamentos (R$ 15k total)
- [ ] Todas as reconciliações são negativas (FCMP < 1.0)

### 📌 Validações de Fórmulas

Para cada reconciliação, validar manualmente:

```
Reconciliação = Total_Adiantado_Colaborador × (FCMP - 1.0)
```

**Exemplo (Processo 100003):**
- Total_Adiantado = R$ 10.000,00
- FCMP = 0,80 (exemplo)
- Reconciliação = R$ 10.000 × (0,80 - 1,0) = R$ 10.000 × (-0,20) = -R$ 2.000,00

---

## 🐛 PROBLEMAS COMUNS E SOLUÇÕES

### ❌ **Erro: "Arquivo não encontrado"**
**Solução:** Certifique-se de estar na raiz do projeto:
```bash
cd C:\Users\m.rafael\Desktop\PROJETO_COMISSOES_V2
```

### ❌ **Reconciliações não aparecem**
**Possíveis causas:**
1. Processo não foi faturado (verificar `Status Processo` = "FATURADO")
2. Processo não tinha adiantamento prévio
3. FCMP = 1.0 (não gera reconciliação)

**Solução:** Verificar aba `ESTADO` e colunas:
- `STATUS_CALCULO_MEDIAS`
- `COMISSOES_ADIANTADAS_JSON`
- `FCMP_JSON`

### ❌ **Estado não persiste entre rodadas**
**Causa:** Arquivo `Estado_Processos_Recebimento.xlsx` foi apagado

**Solução:** 
1. Apagar arquivos de saída
2. Apagar estado
3. Rodar novamente desde Agosto

### ❌ **Valores de reconciliação incorretos**
**Verificar:**
1. `total_adiantado_colaborador` está correto?
2. `FCMP` está sendo calculado como média ponderada?
3. Fórmula: `Reconciliação = Total_Adiantado × (FCMP - 1.0)`

---

## 📊 ANÁLISE DOS RESULTADOS

### 🔍 Como Interpretar as Abas

#### **COMISSOES_ADIANTAMENTOS**
- Contém comissões pagas **antes** do faturamento
- `fc` sempre = 1.0
- `observacao` = "Adiantamento (FC=1.0)"

#### **COMISSOES_REGULARES**
- Contém comissões pagas **após** o faturamento
- `fc` = FCMP do processo
- Usa métricas salvas no `ESTADO`

#### **RECONCILIACOES**
- Contém ajustes no mês do **faturamento**
- Valores negativos = desconto (FCMP < 1.0)
- Valores positivos = acréscimo (FCMP > 1.0) - raro
- Somente processos com adiantamento prévio

#### **ESTADO**
- Histórico completo de cada processo
- Colunas JSON contêm dados por colaborador
- Status indicam situação atual

---

## 🎯 TESTES AVANÇADOS (Opcional)

### Teste 1: Modificar FCMP Manualmente

1. Editar `Analise_Comercial_Completa.xlsx`
2. Alterar `Negócio` do processo 100003 para "VENDA"
3. Rodar Setembro novamente
4. **Resultado esperado:** FCMP = 1.0, SEM reconciliação

### Teste 2: Adicionar Terceiro Colaborador

1. Editar `Analise_Comercial_Completa.xlsx`
2. Adicionar novo item no processo 100006 com novo consultor
3. Rodar testes novamente
4. **Resultado esperado:** 3 linhas de reconciliação (uma por colaborador)

### Teste 3: Testar Processo com FC > 1.0

1. Seria necessário rentabilidade acima do esperado
2. Não implementado nestes dados de teste (cap_fc_max ≤ 1.0)

---

## 📞 SUPORTE

Em caso de dúvidas ou erros:

1. Verificar logs no console
2. Verificar aba `AVISOS` nos arquivos de saída
3. Verificar arquivo `Estado_Processos_Recebimento.xlsx`
4. Comparar resultados com fórmulas esperadas

---

## ✨ CONCLUSÃO

Este guia fornece todos os passos necessários para testar completamente a funcionalidade de reconciliações. Os 10 cenários cobrem todos os casos possíveis:

1. ✅ Adiantamentos simples
2. ✅ Reconciliações no mesmo mês
3. ✅ Reconciliações em mês diferente
4. ✅ Múltiplos adiantamentos
5. ✅ Múltiplos colaboradores
6. ✅ Múltiplos itens (média ponderada)
7. ✅ Casos sem reconciliação (FC=1.0)
8. ✅ Pagamentos regulares diretos
9. ✅ Mapeamento de NFs
10. ✅ Documentos não mapeados

**Boa sorte nos testes! 🚀**

