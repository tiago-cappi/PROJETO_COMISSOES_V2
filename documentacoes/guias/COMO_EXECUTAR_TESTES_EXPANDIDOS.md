# 🚀 COMO EXECUTAR OS TESTES EXPANDIDOS - GUIA RÁPIDO

## 📋 VISÃO GERAL

Este guia fornece instruções passo a passo para executar **TODOS os testes** do sistema de comissões, incluindo:
- ✅ Comissões por Recebimento (57 processos)
- ✅ Comissões por Faturamento (50 processos)
- ✅ Cross-Selling (10 processos)
- ✅ FC de Fornecedores (15 processos)

**Total: 132 processos de teste**

---

## ⚙️ PRÉ-REQUISITOS

1. ✅ Python 3.8+ instalado
2. ✅ Bibliotecas instaladas: `pandas`, `openpyxl`, `numpy`
3. ✅ Arquivos de configuração em `config/` (não alterar)
4. ✅ Scripts de geração de dados executados

---

## 📝 PASSO 1: GERAR DADOS DE TESTE

### 1.1 Gerar Dados de Recebimento (57 processos)

```bash
python gerar_dados_teste_completo.py
```

**O que este script faz**:
- Cria processos 100001-100010 (testes originais de reconciliação)
- Cria processos 200001-200050 (testes expandidos de recebimento)
- Gera arquivo `Analise_Comercial_Completa.xlsx` com **Data Aceite**
- Gera arquivo `Análise Financeira.xlsx` com pagamentos
- Total: 57 processos, 82 linhas, 117 pagamentos

**Arquivos gerados**:
- ✅ `dados_entrada/Analise_Comercial_Completa.xlsx`
- ✅ `dados_entrada/Análise Financeira.xlsx`

---

### 1.2 Gerar Dados de Faturamento (75 processos)

```bash
python gerar_dados_faturamento_completo.py
```

**O que este script faz**:
- Cria processos 300001-300050 (comissões por faturamento)
- Cria processos 400001-400010 (cross-selling)
- Cria processos 500001-500015 (FC de fornecedores)
- Gera arquivos de Faturados e Conversões (agosto e setembro)
- Gera arquivo de vendas de fornecedores em moedas nativas
- Total: 75 processos, 91 linhas faturadas, 75 conversões

**Arquivos gerados**:
- ✅ `dados_entrada/Faturados_08_2025.xlsx`
- ✅ `dados_entrada/Faturados_09_2025.xlsx`
- ✅ `dados_entrada/Conversões_08_2025.xlsx`
- ✅ `dados_entrada/Conversões_09_2025.xlsx`
- ✅ `dados_entrada/vendas_fornecedores_moeda_nativa.xlsx`

---

### 1.3 Gerar Dados de Rentabilidade

```bash
python gerar_rentabilidade_teste_completo.py
```

**O que este script faz**:
- Gera rentabilidade simulada para agosto, setembro e outubro 2025
- Rentabilidade por Linha/Grupo/Subgrupo/Tipo de Mercadoria
- Valores de rentabilidade variados (12% a 20%)

**Arquivos gerados**:
- ✅ `dados_entrada/rentabilidades/rentabilidade_08_2025_agrupada.xlsx`
- ✅ `dados_entrada/rentabilidades/rentabilidade_09_2025_agrupada.xlsx`
- ✅ `dados_entrada/rentabilidades/rentabilidade_10_2025_agrupada.xlsx`

---

## 🧪 PASSO 2: EXECUTAR TESTES

### 2.1 Executar Comissões de Agosto 2025

```bash
python calculo_comissoes.py --mes 8 --ano 2025
```

**O que será testado**:
- ✅ Comissões por Faturamento: processos 300001-300050 (agosto)
- ✅ Comissões por Recebimento: processos com pagamentos em agosto
- ✅ Cross-Selling: processos 400001-400003 (agosto)
- ✅ FC de Fornecedores: processos 500001-500006 (agosto)
- ✅ Adiantamentos e pagamentos regulares

**Arquivos de saída**:
- `Comissoes_08_2025.xlsx` (faturamento)
- `Comissoes_Recebimento_08_2025.xlsx` (recebimento)

**Tempo estimado**: 2-5 minutos

---

### 2.2 Executar Comissões de Setembro 2025

```bash
python calculo_comissoes.py --mes 9 --ano 2025
```

**O que será testado**:
- ✅ Comissões por Faturamento: processos 300001-300050 (setembro)
- ✅ Comissões por Recebimento: processos com pagamentos em setembro
- ✅ **Reconciliações**: ajustes de processos faturados em setembro que tiveram adiantamentos
- ✅ Cross-Selling: processos 400004-400010 (setembro)
- ✅ FC de Fornecedores: processos 500007-500015 (setembro)
- ✅ **FC de Fornecedores nas Reconciliações** (teste principal)

**Arquivos de saída**:
- `Comissoes_09_2025.xlsx` (faturamento)
- `Comissoes_Recebimento_09_2025.xlsx` (recebimento + **reconciliações**)

**Tempo estimado**: 2-5 minutos

---

## ✅ PASSO 3: VALIDAR RESULTADOS

### 3.1 Validar Comissões por Faturamento

**Arquivo**: `Comissoes_08_2025.xlsx` e `Comissoes_09_2025.xlsx`

**Aba**: `COMISSOES_CALCULADAS`

**Checklist de Validação**:

| Item | Verificar | Esperado |
|------|-----------|----------|
| 1 | Total de linhas | ~150-200 linhas (processos × colaboradores × itens) |
| 2 | Processos 300001-300050 | Todos aparecem |
| 3 | Processos 400001-400010 | Todos aparecem |
| 4 | Processos 500001-500015 | Todos aparecem |
| 5 | Coluna `taxa_rateio_aplicada` | Valores entre 1% e 15% |
| 6 | Coluna `percentual_elegibilidade_pe` | Valores entre 10% e 100% |
| 7 | Coluna `fator_correcao_fc` | Valores entre 0.0 e 1.0 |
| 8 | Coluna `comissao_calculada` | Valores > 0 (se FC > 0) |
| 9 | Colunas de auditoria FC | `peso_*`, `realizado_*`, `meta_*`, `ating_*`, `comp_fc_*` |
| 10 | Colaboradores corretos | Consultores, Gerentes, Diretores |

**Filtros úteis no Excel**:
```
- Filtrar por Processo: 300001-300050 (faturamento)
- Filtrar por Processo: 400001-400010 (cross-selling)
- Filtrar por Processo: 500001-500015 (fornecedores)
- Filtrar por Cargo: Consultor Interno, Consultor Externo, Diretor, Gerente Geral, etc.
- Ordenar por `comissao_calculada` (decrescente) para ver maiores comissões
```

---

### 3.2 Validar Cross-Selling

**Arquivo**: `Comissoes_08_2025.xlsx` e `Comissoes_09_2025.xlsx`

**Aba**: `COMISSOES_CALCULADAS` (ou `CROSS_SELLING` se houver)

**Checklist de Validação**:

| Processo | Linhas Envolvidas | Gerente Comercial | Taxa CS | Validar |
|----------|-------------------|-------------------|---------|---------|
| 400001 | SSO + Hidrologia | André Camargo | 1% | ✅ Cross-selling detectado |
| 400002 | SSO + Remediação | Leonardo Camargo | 1% | ✅ Cross-selling detectado |
| 400003 | Hidrologia + SSO + Remediação | Mateus Machado | 1% | ✅ 3 linhas |
| 400008 | SSO apenas | Leonardo Camargo | N/A | ❌ NÃO aplicar CS |

**Como verificar**:
1. Filtrar por "Gerente Comercial-Pedido" contendo "ANDRÉ", "LEONARDO" ou "MATEUS"
2. Verificar se `taxa_rateio_aplicada` foi reduzida em ~1% (Opção A)
3. OU verificar se há linha separada com taxa CS (Opção B)
4. Processo 400008 deve ter comissão NORMAL (sem redução)

---

### 3.3 Validar Comissões por Recebimento

**Arquivo**: `Comissoes_Recebimento_08_2025.xlsx` e `Comissoes_Recebimento_09_2025.xlsx`

**Abas**: 
- `COMISSOES_ADIANTAMENTOS`
- `COMISSOES_REGULARES`
- `RECONCILIACOES`
- `ESTADO`

**Checklist de Validação**:

| Item | Aba | Verificar | Esperado |
|------|-----|-----------|----------|
| 1 | `ESTADO` | Total de processos | 57 processos (100001-200050) |
| 2 | `ESTADO` | Coluna `TCMP_JSON` | JSON com colaboradores e taxas |
| 3 | `ESTADO` | Coluna `FCMP_JSON` | JSON com colaboradores e FCs |
| 4 | `ESTADO` | Coluna `STATUS_CALCULO_MEDIAS` | "CALCULADO" ou "PENDENTE" |
| 5 | `COMISSOES_ADIANTAMENTOS` | Coluna `fc` | Todos = 1.0 |
| 6 | `COMISSOES_ADIANTAMENTOS` | Coluna `tipo_lancamento` | "Adiantamento" |
| 7 | `COMISSOES_REGULARES` | Coluna `fcmp` | Valores entre 0.0 e 1.0 |
| 8 | `COMISSOES_REGULARES` | Coluna `tipo_lancamento` | "Pagamento Regular" |
| 9 | `RECONCILIACOES` (set) | Total de linhas | Processos faturados em setembro com adiantamentos |
| 10 | `RECONCILIACOES` (set) | Coluna `ajuste_reconciliacao` | Geralmente negativo (FCMP < 1.0) |

**Fórmulas para validar manualmente**:
```
TCMP = Σ(Valor_Item × Taxa_Item) / Σ(Valor_Item)
FCMP = Σ(Valor_Item × FC_Item) / Σ(Valor_Item)

Comissão Adiantamento = Valor_Pago × TCMP × 1.0
Comissão Regular = Valor_Pago × TCMP × FCMP
Reconciliação = Comissao_Adiantada × (FCMP - 1.0)
```

---

### 3.4 Validar FC de Fornecedores (nas Reconciliações)

**Arquivo**: `Comissoes_Recebimento_09_2025.xlsx` (setembro - mês de faturamento)

**Aba**: `RECONCILIACOES`

**Checklist de Validação**:

| Item | Verificar | Esperado |
|------|-----------|----------|
| 1 | Processos 500001-500015 | Aparecem se tiveram adiantamentos |
| 2 | Colaborador | "Alessandro Cappi" (Gerente Linha) |
| 3 | Coluna `fcmp` | Inclui componentes de fornecedores |
| 4 | Colunas de auditoria | `moeda_forn1`, `moeda_forn2` preenchidas |
| 5 | Colunas de auditoria | `peso_forn1 = 0.10`, `peso_forn2 = 0.10` |
| 6 | Colunas de auditoria | `realizado_forn1`, `meta_forn1` |
| 7 | Valores em moeda nativa | Conversão de BRL para USD/GBP |
| 8 | Atingimento fornecedor | `ating_forn1 = realizado / meta` |
| 9 | Componente FC fornecedor | `comp_fc_forn1 = ating_cap × peso` |

**Como verificar manualmente**:

```
Exemplo: Processo 500001 (YSI, USD 6.000)

1. Meta YSI (USD): 100.000 (de METAS_FORNECEDORES.csv)
2. Realizado YSI (USD): 6.000 (agosto) + acumulados
3. Atingimento: realizado / meta
4. Ating_cap: min(atingimento, 1.0)
5. Componente FC: ating_cap × 0.10 (peso de 10%)
6. FC Final: inclui este componente na soma
```

**Fornecedores e Moedas**:
- YSI (USD), ISCO (USD) → Hidrologia
- QED (USD), Thermo (USD) → Remediação
- HON (USD), ION (GBP) → SSO

**Taxas de Câmbio** (simuladas):
- 1 USD = 5,00 BRL
- 1 GBP = 6,50 BRL

---

## 📊 PASSO 4: RELATÓRIO DE VALIDAÇÃO

Após executar todos os testes, preencher o checklist abaixo:

### Checklist Final

- [ ] **Geração de Dados**
  - [ ] Script `gerar_dados_teste_completo.py` executado com sucesso
  - [ ] Script `gerar_dados_faturamento_completo.py` executado com sucesso
  - [ ] Script `gerar_rentabilidade_teste_completo.py` executado com sucesso
  - [ ] Todos os arquivos de entrada gerados

- [ ] **Execução de Testes**
  - [ ] Comissões de Agosto 2025 calculadas sem erros
  - [ ] Comissões de Setembro 2025 calculadas sem erros
  - [ ] Arquivos de saída gerados corretamente

- [ ] **Validação - Comissões por Faturamento**
  - [ ] Processos 300001-300050 aparecem
  - [ ] Colaboradores corretos identificados
  - [ ] Taxas e PEs corretos
  - [ ] FC calculado corretamente
  - [ ] Colunas de auditoria preenchidas
  - [ ] Comissões calculadas = potencial × FC

- [ ] **Validação - Cross-Selling**
  - [ ] Processos 400001-400010 aparecem
  - [ ] Cross-selling detectado nos processos corretos
  - [ ] Taxa CS de 1% aplicada
  - [ ] Processo 400008 (sem CS) validado

- [ ] **Validação - Comissões por Recebimento**
  - [ ] Processos 100001-200050 no `ESTADO`
  - [ ] TCMP e FCMP calculados
  - [ ] Adiantamentos com FC = 1.0
  - [ ] Pagamentos regulares com FCMP real
  - [ ] Reconciliações aplicadas corretamente

- [ ] **Validação - FC de Fornecedores**
  - [ ] Processos 500001-500015 aparecem
  - [ ] Conversão de moedas correta (USD/GBP)
  - [ ] Componentes `meta_fornecedor_1/2` calculados
  - [ ] Pesos de 10% aplicados
  - [ ] Colunas de auditoria `moeda_forn*` preenchidas
  - [ ] Apenas "Gerente Linha" tem FC de fornecedores

- [ ] **Validação - Sem Erros**
  - [ ] Nenhum erro crítico no log
  - [ ] Nenhum aviso de dados ausentes
  - [ ] Nenhum processo sem comissão (quando deveria ter)

---

## 🐛 TROUBLESHOOTING

### Problema: "Arquivo não encontrado"
**Solução**: Verificar se os scripts de geração foram executados antes

### Problema: "Processo não aparece nas comissões"
**Solução**: 
1. Verificar se o processo está no arquivo de entrada correto
2. Verificar se o colaborador tem comissão configurada para aquele contexto
3. Ver aba `AVISOS` nos arquivos de saída

### Problema: "FC = 0.0 para todos"
**Solução**: Verificar se arquivos de rentabilidade e metas foram gerados

### Problema: "Cross-selling não detectado"
**Solução**: 
1. Verificar se `Gerente Comercial-Pedido` está preenchido
2. Verificar se há múltiplas linhas no processo
3. Verificar se o gerente está em `CROSS_SELLING.csv`

### Problema: "FC de fornecedores não aparece"
**Solução**: 
1. FC de fornecedores só aparece em **reconciliações**
2. Verificar se o processo teve **adiantamento**
3. Verificar se o processo foi **faturado** no mês
4. Verificar se o colaborador é "Gerente Linha"

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- **Detalhes dos Cenários**: `documentacoes/CENARIOS_TESTE_EXPANDIDOS.md`
- **Testes de Reconciliação**: `documentacoes/CENARIOS_TESTE_COMPLETOS.md`
- **Lógica Completa de Recebimento**: `documentacoes/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`
- **Documentação do Robô**: `documentacoes/DOCUMENTACAO_ROBO_COMISSOES.md`

---

## ⏱️ TEMPO ESTIMADO TOTAL

- Geração de dados: **3-5 minutos**
- Execução de testes: **5-10 minutos**
- Validação manual: **20-30 minutos**

**TOTAL: ~30-45 minutos**

---

## ✅ CONCLUSÃO

Após executar todos os passos acima, você terá testado **132 processos** cobrindo:
- ✅ Comissões por Recebimento (TCMP, FCMP, Adiantamentos, Reconciliações)
- ✅ Comissões por Faturamento (Taxas, PE, FC, Colunas de Auditoria)
- ✅ Cross-Selling (Múltiplas Linhas, Taxa CS)
- ✅ FC de Fornecedores (Moedas Nativas, Componentes meta_fornecedor_1/2)

O sistema estará **100% testado** e pronto para produção! 🎉

---

**Versão**: 1.0  
**Data**: 17/11/2025  
**Autor**: Sistema Automático de Testes

