# 📋 CENÁRIOS DE TESTE COMPLETOS - ROBÔ DE COMISSÕES

## 🎯 Objetivo

Este documento detalha TODOS os 57 processos de teste criados para validar o robô de comissões por recebimento antes de colocar em produção.

---

## 📊 RESUMO EXECUTIVO

| Categoria | Processos | Pagamentos | Reconciliações Esperadas | Prioridade |
|-----------|-----------|------------|--------------------------|------------|
| **Originais** | 10 (100001-100010) | 23 | 5 | ✅ Alta |
| **Linhas de Negócio** | 6 (200001-200006) | 12 | 6 | ✅ Alta |
| **Variações de FC** | 6 (200007-200012) | 12 | 5 | ✅ Alta |
| **Múltiplos Colaboradores** | 8 (200013-200020) | 16 | 8 | ✅ Alta |
| **Pagamentos Complexos** | 10 (200021-200030) | 25 | 7 | 🟡 Média |
| **Regras de Comissão** | 6 (200031-200036) | 12 | 6 | 🔵 Baixa |
| **Edge Cases** | 5 (200037-200044) | 8 | 0 | 🟡 Média |
| **Rentabilidade/FC** | 6 (200045-200050) | 12 | 6 | 🔵 Baixa |
| **TOTAL** | **57** | **120** | **~43** | - |

---

## 📦 BLOCO ORIGINAL: PROCESSOS 100001-100010

### 100001 - Adiantamento Simples (Não Faturado)
- **Objetivo**: Testar adiantamento de processo que ainda não foi faturado
- **Configuração**:
  - Valor Total: R$ 10.000
  - Adiantamento: R$ 5.000 (COT100001 em Agosto)
  - Status: PENDENTE
  - Colaborador: Alessandro Cappi
- **Resultado Esperado**:
  - Agosto: Comissão de adiantamento (FC=1.0)
  - **SEM reconciliação** (processo não faturado)

### 100002 - Adiantamento + Faturamento Mesmo Mês
- **Objetivo**: Testar reconciliação no mesmo mês do adiantamento
- **Configuração**:
  - Valor Total: R$ 15.000
  - Adiantamento: R$ 7.500 (COT100002 em 05/08)
  - Faturamento: 25/08 (NF 048001)
  - Pagamento Regular: R$ 7.500 (048001 em 28/08)
- **Resultado Esperado**:
  - Agosto: Adiantamento + Pagamento Regular + **RECONCILIAÇÃO**
  - FCMP < 1.0 → Reconciliação negativa

### 100003 - Adiantamento em Agosto, Faturamento em Setembro
- **Objetivo**: Testar reconciliação em mês diferente do adiantamento
- **Configuração**:
  - Valor Total: R$ 20.000
  - Adiantamento: R$ 10.000 (COT100003 em Agosto)
  - Faturamento: Setembro (NF 048002)
  - Pagamento Regular: R$ 10.000 (Setembro)
- **Resultado Esperado**:
  - Agosto: Apenas adiantamento (FC=1.0)
  - Setembro: Pagamento Regular + **RECONCILIAÇÃO**

### 100004 - Múltiplos Adiantamentos
- **Objetivo**: Testar reconciliação com soma de múltiplos adiantamentos
- **Configuração**:
  - Valor Total: R$ 25.000
  - Adiantamento 1: R$ 8.000 (COT100004 em 08/08)
  - Adiantamento 2: R$ 7.000 (COT100004 em 15/08)
  - Faturamento: Setembro (NF 048003)
  - Pagamento Regular: R$ 10.000 (Setembro)
- **Resultado Esperado**:
  - Agosto: 2 comissões de adiantamento
  - Setembro: Pagamento Regular + **RECONCILIAÇÃO sobre R$ 15.000 total**

### 100005 - Pagamento Regular Direto
- **Objetivo**: Testar processo sem adiantamento (sem reconciliação)
- **Configuração**:
  - Valor Total: R$ 12.000
  - Faturamento: Agosto (NF 048004)
  - Pagamentos Regulares: 2× R$ 6.000 (Agosto)
  - Colaborador: André Caramello
- **Resultado Esperado**:
  - Agosto: 2 comissões regulares (com FCMP)
  - **SEM reconciliação** (sem adiantamento)

### 100006 - Múltiplos Colaboradores
- **Objetivo**: Testar reconciliação individual por colaborador
- **Configuração**:
  - Valor Total: R$ 30.000 (2 itens)
  - Item 1: R$ 18.000 (Alessandro Cappi)
  - Item 2: R$ 12.000 (André Caramello)
  - Adiantamento: R$ 15.000 (Agosto)
  - Faturamento: Setembro (NF 048006)
- **Resultado Esperado**:
  - Agosto: Adiantamento dividido entre colaboradores
  - Setembro: **2 linhas de reconciliação** (uma por colaborador)

### 100007 - FC = 1.0 (Sem Reconciliação)
- **Objetivo**: Testar que FC=1.0 NÃO gera reconciliação
- **Configuração**:
  - Valor Total: R$ 30.000
  - Tipo: Serviço / Calibração (FC próximo de 1.0)
  - Adiantamento: R$ 15.000 (Agosto)
  - Faturamento: Setembro (NF 048007)
- **Resultado Esperado**:
  - Agosto: Adiantamento
  - Setembro: Pagamento Regular + **SEM reconciliação** (FC ≈ 1.0)

### 100008 - Múltiplos Pagamentos Regulares
- **Objetivo**: Testar múltiplas parcelas de pagamento regular
- **Configuração**:
  - Valor Total: R$ 50.000
  - Faturamento: Agosto (NF 048005)
  - Pagamentos: 3 parcelas (R$ 15k, R$ 20k, R$ 15k)
- **Resultado Esperado**:
  - Agosto: 3 comissões regulares
  - **SEM reconciliação** (sem adiantamento)

### 100009 - NF com 5 Dígitos
- **Objetivo**: Testar mapeamento de NF com 5 dígitos
- **Configuração**:
  - Valor Total: R$ 8.000
  - NF: 12345 (5 dígitos)
  - Pagamentos: 2× R$ 4.000 (Agosto)
  - Colaborador: André Caramello
- **Resultado Esperado**:
  - Agosto: 2 comissões regulares
  - Mapeamento correto da NF

### 100010 - Múltiplos Itens (Média Ponderada)
- **Objetivo**: Testar cálculo de TCMP e FCMP ponderados
- **Configuração**:
  - Valor Total: R$ 90.000 (3 itens)
  - Item 1: R$ 40.000 (Produto, FC baixo)
  - Item 2: R$ 30.000 (Serviço, FC alto)
  - Item 3: R$ 20.000 (Reposição, FC muito baixo)
  - Adiantamento: R$ 45.000 (Agosto)
  - Faturamento: Setembro
- **Resultado Esperado**:
  - TCMP e FCMP calculados como média ponderada
  - Setembro: **RECONCILIAÇÃO com média ponderada**

---

## 📦 BLOCO 1: LINHAS DE NEGÓCIO (200001-200006)

### 200001 - Linha: Hidrologia
- **Linha**: Hidrologia / Amostrador Diversos / Acessório / Produto
- **Valor**: R$ 20.000
- **Adiantamento**: Agosto, **Faturamento**: Setembro
- **Reconciliação**: ✅ Sim

### 200002 - Linha: Remediação
- **Linha**: Remediação / Bomba Diversos / Bomba / Produto
- **Colaborador**: André Caramello
- **Valor**: R$ 15.000
- **Reconciliação**: ✅ Sim

### 200003 - Linha: Diversos
- **Linha**: Diversos / Detector Diversos / Certificado / Serviço
- **Colaborador**: Neimar (Gerente Linha)
- **Valor**: R$ 10.000
- **Reconciliação**: ✅ Sim (FC alto, mas não 1.0)

### 200004 - Linha: Locação
- **Linha**: Locação / Locação Diversos / Locação / Serviço
- **Valor**: R$ 25.000
- **Reconciliação**: ✅ Sim

### 200005 - Linha: Saneamento
- **Linha**: Saneamento / Estação Diversos / Sistema / Produto
- **Colaborador**: André Caramello
- **Valor**: R$ 30.000
- **Reconciliação**: ✅ Sim

### 200006 - Linha: Hidrologia (2ª variação)
- **Linha**: Hidrologia / Analisador Microbiologico / GeneCount / Produto
- **Colaborador**: Neimar
- **Valor**: R$ 50.000
- **Reconciliação**: ✅ Sim

**Objetivo Geral**: Garantir que todas as linhas de negócio da empresa são testadas.

---

## 📦 BLOCO 2: VARIAÇÕES DE FC (200007-200012)

### 200007 - FC Muito Baixo (< 0,5)
- **Tipo**: Reposição (rentabilidade muito baixa: ~8%)
- **Valor**: R$ 15.000
- **FC Esperado**: < 0,5
- **Reconciliação**: ✅ Grande negativa

### 200008 - FC Médio (0,6-0,7)
- **Tipo**: Produto (rentabilidade média: ~15%)
- **Valor**: R$ 20.000
- **FC Esperado**: 0,6-0,7
- **Reconciliação**: ✅ Média negativa

### 200009 - FC Bom (0,8-0,9)
- **Tipo**: Produto / Analisador Portátil (rentabilidade boa: ~22%)
- **Valor**: R$ 25.000
- **FC Esperado**: 0,8-0,9
- **Reconciliação**: ✅ Pequena negativa

### 200010 - FC Alto (0,95-0,99)
- **Tipo**: Serviço / Hora Técnica (rentabilidade alta: ~28%)
- **Valor**: R$ 18.000
- **FC Esperado**: 0,95-0,99
- **Reconciliação**: ✅ Muito pequena negativa

### 200011 - FC = 1.0
- **Tipo**: Serviço / Calibração (rentabilidade alta: ~30%)
- **Valor**: R$ 12.000
- **FC Esperado**: ~1,0 (capado)
- **Reconciliação**: ❌ Não (FC = 1.0)

### 200012 - Tentativa FC > 1.0
- **Tipo**: Produto / Titan (rentabilidade premium: ~25%)
- **Valor**: R$ 30.000
- **FC Esperado**: 1,0 (capado pelo cap_fc_max)
- **Reconciliação**: ✅ Possível pequena (se não for exatamente 1.0)

**Objetivo Geral**: Validar que o FC é calculado corretamente em todos os níveis e que reconciliações variam proporcionalmente.

---

## 📦 BLOCO 3: MÚLTIPLOS COLABORADORES (200013-200020)

### 200013 - Alessandro (SSO) + Neimar (Hidrologia)
- **Itens**: 2 (linhas diferentes)
- **Colaboradores**: Alessandro Cappi, Neimar
- **Valor Total**: R$ 30.000
- **Reconciliação**: ✅ 2 linhas (uma por colaborador)

### 200014 - Alessandro + André + Neimar (3 iguais)
- **Itens**: 3 (valores iguais: R$ 10k cada)
- **Colaboradores**: Alessandro, André, Neimar
- **Valor Total**: R$ 30.000
- **Reconciliação**: ✅ 3 linhas (valores iguais)

### 200015 - Apenas Neimar
- **Colaborador**: Neimar (isolado)
- **Linha**: Hidrologia
- **Valor**: R$ 20.000
- **Reconciliação**: ✅ 1 linha

### 200016 - Alessandro + Neimar + André (valores diferentes)
- **Itens**: 3 (R$ 30k + R$ 20k + R$ 10k)
- **Colaboradores**: Todos os 3 Gerentes
- **TCMPs e FCMPs**: Distintos por colaborador
- **Reconciliação**: ✅ 3 linhas (valores proporcionais)

### 200017 - Alessandro + André (5 itens variados)
- **Itens**: 5 (3 de Alessandro, 2 de André)
- **Valores**: R$ 8k × 3 + R$ 7k × 2
- **Reconciliação**: ✅ 2 linhas (proporcionais)

### 200018 - Apenas Alessandro (10 itens uniformes)
- **Itens**: 10 (todos iguais: R$ 5k cada)
- **TCMP e FCMP**: Uniformes
- **Reconciliação**: ✅ 1 linha

### 200019 - Apenas André (alto valor)
- **Colaborador**: André Caramello
- **Valor**: R$ 100.000 (teste de valor alto)
- **Reconciliação**: ✅ 1 linha

### 200020 - Todos os 3 Gerentes (valores iguais)
- **Itens**: 3 (R$ 10k cada)
- **Colaboradores**: Alessandro, André, Neimar
- **Reconciliação**: ✅ 3 linhas (iguais)

**Objetivo Geral**: Validar que reconciliações são calculadas individualmente por colaborador e que médias ponderadas funcionam com múltiplos colaboradores.

---

## 📦 BLOCO 4: CENÁRIOS DE PAGAMENTO COMPLEXOS (200021-200030)

### 200021 - Adiantamento Parcial + 2 Parcelas Regulares
- **Adiantamento**: R$ 10.000 (50% do total)
- **Regulares**: 2× R$ 5.000
- **Reconciliação**: ✅ Sobre os R$ 10k adiantados

### 200022 - Adiantamento Total (100%)
- **Adiantamento**: R$ 20.000 (100% do valor)
- **Regular**: Nenhum
- **Reconciliação**: ✅ Sobre todo o valor

### 200023 - 3 Adiantamentos Diferentes
- **Adiantamentos**: R$ 5k + R$ 7k + R$ 8k = R$ 20k
- **Reconciliação**: ✅ Sobre a soma (R$ 20k)

### 200024 - Adiantamento (Ago) + Faturamento (Out)
- **Pula**: Setembro
- **Reconciliação**: ✅ Em Outubro

### 200025 - 5 Parcelas Regulares (Sem Adiantamento)
- **Parcelas**: 5× R$ 10.000
- **Reconciliação**: ❌ Não (sem adiantamento)

### 200026 - Pagamento a Maior
- **Processo**: R$ 20.000
- **Pagamento**: R$ 25.000 (125%)
- **Teste**: Comportamento com pagamento > valor processo

### 200027 - Pagamento em 3 Meses
- **Adiantamento**: Agosto
- **Faturamento**: Setembro
- **Parcial Regular**: Setembro
- **Final Regular**: Outubro
- **Reconciliação**: ✅ Em Setembro

### 200028 - Adiantamento Ago + Faturamento Nov
- **Pula**: Setembro e Outubro
- **Reconciliação**: ✅ Em Novembro

### 200029 - 2 Adiantamentos em Meses Diferentes
- **COT 1**: Agosto (R$ 10k)
- **COT 2**: Setembro (R$ 15k)
- **Faturamento**: Outubro
- **Reconciliação**: ✅ Em Outubro (sobre R$ 25k total)

### 200030 - Pagamento Zero (Edge Case)
- **Valor**: R$ 0,01
- **Teste**: Comportamento com valor mínimo

**Objetivo Geral**: Validar cenários de pagamento não lineares e complexos.

---

## 📦 BLOCO 5: DIFERENTES REGRAS DE COMISSÃO (200031-200036)

### 200031 - SSO / Analisador Fixo / Falco / Produto
- **Taxa Rateio**: 5%
- **PE (Gerente Linha)**: 20%
- **TCMP Esperada**: 1,0% (0,05 × 0,20)

### 200032 - Hidrologia / Calibração Diversos / Solução / Insumo
- **Taxa Rateio**: 5%
- **PE**: 20%
- **TCMP Esperada**: 1,0%

### 200033 - Diversos / Diversos Diversos / Calibração / Serviço
- **Taxa Rateio**: 5%
- **PE**: 20%
- **TCMP Esperada**: 1,0%

### 200034 - Mix de Vários Grupos no Mesmo Processo
- **Itens**: 3 (grupos diferentes)
- **TCMP**: Média ponderada de taxas diferentes

### 200035 - Hidrologia / Sonda Diversos / Acessório
- **Taxa Rateio**: 5%
- **PE**: 20%

### 200036 - Remediação / Bomba Fixa / Sistema
- **Taxa Rateio**: 5%
- **PE**: 20%

**Objetivo Geral**: Validar que diferentes combinações de linhas/grupos/subgrupos/tipos resultam em cálculos corretos de TCMP.

---

## 📦 BLOCO 6: EDGE CASES E ERROS (200037-200044)

### 200037 - Documento Formato Estranho
- **Documento**: "XPTO999"
- **Resultado Esperado**: Aba **AVISOS** com documento não mapeado

### 200038 - NF Inexistente
- **Documento**: "999999"
- **Resultado Esperado**: Aba **AVISOS**

### 200039 - Processo Sem Gerente de Linha
- **Colaborador**: Andrey Andrade (Consultor Interno)
- **Resultado Esperado**: **Sem comissão de recebimento** (não é Gerente Linha)

### 200040 - Valor Negativo de Pagamento
- **Valor**: -R$ 1.000
- **Resultado Esperado**: Tratado como estorno ou ignorado

### 200041 - Data de Baixa Futura
- **Data**: 2026-01-15
- **Resultado Esperado**: Não processado (fora do mês de apuração)

### 200042 - Tipo de Baixa != 'B'
- **Tipo**: 'C'
- **Resultado Esperado**: Filtrado (não processado)

### 200043 - Processo CANCELADO
- **Status**: CANCELADO
- **Resultado Esperado**: Não calcula comissões

### 200044 - COT Sem Número
- **Documento**: "COT" (sem sufixo numérico)
- **Resultado Esperado**: Aba **AVISOS**

**Objetivo Geral**: Validar tratamento de erros e casos extremos.

---

## 📦 BLOCO 7: RENTABILIDADE E COMPONENTES DO FC (200045-200050)

### 200045 - Rentabilidade Muito Baixa
- **Tipo**: Reposição
- **Rentabilidade**: ~8% (meta: ~17%)
- **Componente FC Rentabilidade**: Muito baixo
- **FC Total**: Muito baixo

### 200046 - Rentabilidade Muito Alta
- **Tipo**: Produto / Analisador Portátil
- **Rentabilidade**: ~22% (meta: ~17%)
- **Componente FC Rentabilidade**: Alto
- **FC Total**: Próximo do cap (1.0)

### 200047 - Meta de Fornecedor 1 (EUR)
- **Fabricante**: DRÄGER
- **Moeda**: EUR
- **Teste**: Conversão cambial + componente meta_fornecedor_1

### 200048 - Meta de Fornecedor 2 (USD)
- **Fabricante**: HONEYWELL
- **Moeda**: USD
- **Teste**: Conversão cambial + componente meta_fornecedor_2

### 200049 - Retenção de Clientes
- **Componente**: retencao_clientes (15% para Gerente Linha)
- **Teste**: Peso de retenção no FC

### 200050 - Combinação Completa
- **Fabricante**: DRÄGER
- **Teste**: Todos os componentes ativos simultaneamente
- **FC**: Máximo possível (capado em 1.0)

**Objetivo Geral**: Validar que todos os componentes do FC são calculados corretamente.

---

## 🎯 COMO USAR ESTE DOCUMENTO

### Para Executar os Testes:

1. **Gerar Dados** (já feito):
   ```bash
   python gerar_dados_teste_completo.py
   python gerar_rentabilidade_teste_completo.py
   ```

2. **Executar Agosto/2025**:
   ```bash
   python calculo_comissoes.py --mes 8 --ano 2025
   ```
   - Validar: 10-15 reconciliações esperadas

3. **Executar Setembro/2025**:
   ```bash
   python calculo_comissoes.py --mes 9 --ano 2025
   ```
   - Validar: 30-40 reconciliações esperadas

4. **Executar Outubro/2025** (opcional):
   ```bash
   python calculo_comissoes.py --mes 10 --ano 2025
   ```
   - Validar: Processos 200024, 200027, 200028, 200029

### Para Validar Resultados:

1. Abrir arquivo `Comissoes_Recebimento_MM_AAAA.xlsx`
2. Verificar aba **RECONCILIACOES**:
   - Quantidade de processos
   - Valores negativos (maioria)
   - Colaboradores corretos
3. Verificar aba **ESTADO**:
   - STATUS_RECONCILIACAO
   - TCMP_JSON e FCMP_JSON preenchidos
4. Verificar aba **AVISOS**:
   - Documentos não mapeados (esperados)

---

## 📊 MATRIZ DE COBERTURA

| Categoria | Cenários Testados | Cobertura |
|-----------|-------------------|-----------|
| **Linhas de Negócio** | Todas (SSO, Hidrologia, Remediação, Diversos, Locação, Saneamento) | ✅ 100% |
| **Tipos de Mercadoria** | Produto, Serviço, Reposição, Insumo | ✅ 100% |
| **Colaboradores** | Alessandro, André, Neimar (todos Gerentes Linha) | ✅ 100% |
| **Variações de FC** | Muito Baixo, Baixo, Médio, Alto, ~1.0 | ✅ 100% |
| **Tipos de Pagamento** | Adiantamento, Regular, Múltiplos, Parcelas | ✅ 100% |
| **Reconciliações** | Mesmo mês, Meses diferentes, Múltiplos COTs, Múltiplos colaboradores | ✅ 100% |
| **Edge Cases** | Documentos inválidos, Valores negativos, Datas futuras, Status cancelado | ✅ 100% |
| **Componentes FC** | Rentabilidade, Metas fornecedor, Retenção | ✅ 100% |

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Agosto/2025:
- [ ] Aba COMISSOES_ADIANTAMENTOS: ~30-40 linhas
- [ ] Aba COMISSOES_REGULARES: ~20-30 linhas
- [ ] Aba RECONCILIACOES: ~10-15 processos
- [ ] Aba ESTADO: 50+ processos
- [ ] Aba AVISOS: ~8 documentos não mapeados

### Setembro/2025:
- [ ] Aba COMISSOES_ADIANTAMENTOS: ~2 linhas (200029)
- [ ] Aba COMISSOES_REGULARES: ~30-40 linhas
- [ ] Aba RECONCILIACOES: ~30-40 processos
- [ ] Processo 100007 NÃO aparece (FC=1.0)
- [ ] Processo 200011 NÃO aparece (FC=1.0)

### Outubro/2025:
- [ ] Processos 200024, 200027, 200028, 200029 reconciliados

---

## 📞 SUPORTE

Em caso de dúvidas sobre algum cenário específico:
1. Consultar este documento
2. Verificar código do script: `gerar_dados_teste_completo.py`
3. Conferir valores esperados na planilha de validação

---

**Versão**: 1.0  
**Data**: 17/11/2025  
**Total de Cenários**: 57 processos + 8 edge cases = 65 testes

