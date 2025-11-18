# 🧪 GERADORES DE DADOS DE TESTE

## 📋 VISÃO GERAL

Esta pasta contém os scripts para gerar dados fictícios de teste para o sistema de comissões.

---

## 📄 SCRIPTS DISPONÍVEIS

### 1. `gerar_todos_dados_teste.py` ⭐
**O que faz**: Gera TODOS os dados de teste em um único script

**Gera**:
- `dados_entrada/Analise_Comercial_Completa.xlsx` (132 processos)
- `dados_entrada/Análise Financeira.xlsx` (pagamentos)

**Processos incluídos**:
- 57 processos para Comissões por Recebimento (100001-200050)
- 50 processos para Comissões por Faturamento (300001-300050)
- 10 processos para Cross-Selling (400001-400010)
- 15 processos para FC de Fornecedores (500001-500015)

**Como executar**:
```bash
python tests/geradores_dados/gerar_todos_dados_teste.py
```

---

### 2. `gerar_rentabilidade_teste.py`
**O que faz**: Gera dados de rentabilidade simulada

**Gera**:
- `dados_entrada/rentabilidades/rentabilidade_08_2025_agrupada.xlsx`
- `dados_entrada/rentabilidades/rentabilidade_09_2025_agrupada.xlsx`
- `dados_entrada/rentabilidades/rentabilidade_10_2025_agrupada.xlsx`

**Como executar**:
```bash
python tests/geradores_dados/gerar_rentabilidade_teste.py
```

---

## 🔄 FLUXO CORRETO DE EXECUÇÃO

### 1️⃣ Gerar Dados de Entrada
```bash
python tests/geradores_dados/gerar_todos_dados_teste.py
python tests/geradores_dados/gerar_rentabilidade_teste.py
```

### 2️⃣ Executar o Robô de Comissões
O robô irá automaticamente:
- Ler `Analise_Comercial_Completa.xlsx`
- Executar `preparar_dados_mensais.py` para gerar:
  - `Faturados.xlsx`
  - `Conversões.xlsx`
  - `Faturados_YTD.xlsx`
  - `Retencao_Clientes.xlsx`
- Calcular comissões

```bash
python calculo_comissoes.py --mes 8 --ano 2025
python calculo_comissoes.py --mes 9 --ano 2025
```

---

## ⚠️ IMPORTANTE

### O QUE OS SCRIPTS DEVEM GERAR
✅ `Analise_Comercial_Completa.xlsx` - Arquivo de entrada único  
✅ `Análise Financeira.xlsx` - Arquivo de entrada único  
✅ `rentabilidade_*.xlsx` - Dados de rentabilidade  

### O QUE OS SCRIPTS **NÃO** DEVEM GERAR
❌ `Faturados.xlsx` - Gerado pelo `preparar_dados_mensais.py`  
❌ `Conversões.xlsx` - Gerado pelo `preparar_dados_mensais.py`  
❌ `Faturados_YTD.xlsx` - Gerado pelo `preparar_dados_mensais.py`  
❌ `Retencao_Clientes.xlsx` - Gerado pelo `preparar_dados_mensais.py`  
❌ `vendas_fornecedores_moeda_nativa.xlsx` - Não faz parte do fluxo (FC de fornecedores é calculado do Faturados_YTD)

---

## 📊 ESTRUTURA DOS DADOS GERADOS

### Analise_Comercial_Completa.xlsx
- Todos os processos (100001-500015)
- Incluindo faturados e pendentes
- Com coluna "Data Aceite" preenchida

### Análise Financeira.xlsx
- Pagamentos (COT* e NFs)
- Para processos de recebimento

---

## 🎯 CENÁRIOS TESTADOS

Ver documentação completa em:
- `documentacoes/testes/CENARIOS_TESTE_EXPANDIDOS.md`
- `documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`

---

**Versão**: 1.0  
**Data**: 18/11/2025

