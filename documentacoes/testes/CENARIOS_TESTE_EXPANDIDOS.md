# 📋 CENÁRIOS DE TESTE EXPANDIDOS - SISTEMA COMPLETO DE COMISSÕES

## 📌 VISÃO GERAL

Este documento detalha **TODOS os cenários de teste** implementados para validar o sistema completo de comissões, incluindo:
- ✅ **Comissões por Recebimento** (57 processos: 100001-200050)
- ✅ **Comissões por Faturamento** (50 processos: 300001-300050)
- ✅ **Cross-Selling** (10 processos: 400001-400010)
- ✅ **FC de Fornecedores** (15 processos: 500001-500015)

**Total: 132 processos de teste completos**

---

## 🎯 ESTRUTURA DOS TESTES

### Bloco 1: Comissões por Recebimento (100001-200050)
**Objetivo**: Testar cálculo de comissões baseado em pagamentos efetivos, com TCMP, FCMP, adiantamentos e reconciliações.

**Detalhamento completo**: Ver `CENARIOS_TESTE_COMPLETOS.md`

**Resumo**:
- 57 processos testando todos os aspectos de comissões por recebimento
- Cenários de adiantamentos, pagamentos regulares, reconciliações
- Múltiplas linhas de negócio, colaboradores e variações de FC
- Processos com múltiplos itens e múltiplos colaboradores

---

### Bloco 2: Comissões por Faturamento (300001-300050)
**Objetivo**: Testar cálculo de comissões no momento do faturamento, item a item.

#### Grupo A: Diferentes Colaboradores e Cargos (10 processos)

| Processo | Consultor Interno | Representante | Gestores | Linha | Valor (R$) | Observações |
|----------|-------------------|---------------|----------|-------|-----------|-------------|
| 300001 | ANDREY.ANDRADE | - | Diretor | SSO | 50.000 | Testar Consultor Interno + Diretor |
| 300002 | MATEUS.MACHADO | André Camargo | Gerente Geral | Hidrologia | 30.000 | Consultor Interno + Externo + Gerente Geral |
| 300003 | - | Leonardo Camargo | Coordenador | Remediação | 20.000 | Apenas Consultor Externo |
| 300004 | ANDREY.ANDRADE | - | Supervisor | SSO | 15.000 | Consultor Interno + Supervisor |
| 300005 | MATEUS.MACHADO | André Camargo | - | Hidrologia | 25.000 | Sem gestor específico atribuído |
| 300006 | ANDREY + MATEUS | - | Diretor + Coord | SSO | 40.000 | Múltiplos consultores internos, 2 itens |
| 300007 | - | André + Leonardo | Gerente Geral | Remediação | 35.000 | Múltiplos consultores externos |
| 300008 | ANDREY.ANDRADE | Leonardo Camargo | Diretor | Hidrologia | 45.000 | Interno + Externo + Diretor |
| 300009 | MATEUS.MACHADO | - | Coordenador | SSO | 28.000 | Consultor Interno + Coordenador |
| 300010 | ANDREY.ANDRADE | André Camargo | Supervisor | Remediação | 32.000 | Interno + Externo + Supervisor |

**Validações Esperadas**:
- ✅ Comissões calculadas corretamente para cada cargo
- ✅ Taxa de rateio e PE corretos conforme `CONFIG_COMISSAO.csv`
- ✅ FC calculado com componentes apropriados para cada cargo
- ✅ Múltiplos colaboradores recebem comissões proporcionais

---

#### Grupo B: Variações de Negócio/Grupo/Subgrupo/Tipo (15 processos)

| Processo | Linha | Grupo | Subgrupo | Tipo | Valor (R$) | Mês Faturamento |
|----------|-------|-------|----------|------|-----------|-----------------|
| 300011 | SSO | Analisador Fixo | Falco | Produto | 15.000 | Agosto |
| 300012 | SSO | Detector Portátil | MicroClip | Reposição | 8.000 | Agosto |
| 300013 | Hidrologia | Equipamento Amostragem | ISCO | Serviço | 5.000 | Agosto |
| 300014 | Hidrologia | Sonda Multiparâmetros | EXO | Aluguel | 3.000 | Agosto |
| 300015 | Remediação | Sistema Remediação | QED | Produto | 25.000 | Agosto |
| 300016 | SSO | Analisador Fixo | Falco | Serviço | 7.000 | Agosto |
| 300017 | SSO | Detector Portátil | MicroClip | Produto | 12.000 | Agosto |
| 300018 | Hidrologia | Equipamento Amostragem | ISCO | Produto | 18.000 | Agosto |
| 300019 | Remediação | Sistema Remediação | QED | Reposição | 9.000 | Setembro |
| 300020 | SSO | Analisador Portátil | Innova | Produto | 20.000 | Setembro |
| 300021 | Hidrologia | Sonda Multiparâmetros | EXO | Produto | 22.000 | Setembro |
| 300022 | Remediação | Sistema Remediação | Thermo | Produto | 30.000 | Setembro |
| 300023 | SSO | Detector Portátil | QRAE | Produto | 11.000 | Setembro |
| 300024 | Hidrologia | Equipamento Amostragem | YSI | Produto | 16.000 | Setembro |
| 300025 | Remediação | Sistema Remediação | QED | Serviço | 6.000 | Setembro |

**Validações Esperadas**:
- ✅ Regras de comissão encontradas corretamente na hierarquia de `CONFIG_COMISSAO.csv`
- ✅ Taxas diferentes para Produto, Reposição, Serviço e Aluguel
- ✅ Todas as combinações de Linha/Grupo/Subgrupo funcionando
- ✅ Fallback para regras `legacy_token` quando não há match exato

---

#### Grupo C: Variação de FC - Componentes Específicos (15 processos)

| Processo | Cargo Testado | Componente FC Foco | Valor (R$) | Mês | Observações |
|----------|---------------|-------------------|-----------|-----|-------------|
| 300026-300029 | Diretor | faturamento_linha (40%) + rentabilidade (30%) | 15.000 | Setembro | Testar pesos e realizados |
| 300030-300031 | Gerente Geral | conversao_linha (40%) | 20.000 | Setembro | Testar conversões por linha |
| 300032-300033 | Consultor Interno | faturamento_individual (40%) | 10.000 | Setembro | Testar faturamento individual |
| 300034-300035 | Consultor Interno | conversao_individual (60%) | 12.000 | Setembro | Testar conversões individuais |
| 300036-300037 | Consultor Externo | faturamento_individual (60%) | 18.000 | Agosto | Representante comercial |
| 300038-300039 | Consultor Externo | conversao_individual (40%) | 14.000 | Agosto | Representante comercial |
| 300040 | Coordenador | Todos componentes | 25.000 | Agosto | FC mix com múltiplos componentes |

**Validações Esperadas**:
- ✅ Pesos corretos de `PESOS_METAS.csv` aplicados
- ✅ Cálculo de atingimento = realizado / meta
- ✅ Aplicação de caps (cap_atingimento_max, cap_fc_max)
- ✅ FC final = min(soma_componentes, cap_fc_max)
- ✅ Colunas de auditoria (peso_, realizado_, meta_, ating_, comp_fc_) preenchidas

---

#### Grupo D: Valores Extremos e Limites (10 processos)

| Processo | Cenário | Valor (R$) | Observações |
|----------|---------|-----------|-------------|
| 300041 | Valor mínimo | 100 | Testar comissões muito pequenas |
| 300042 | Valor médio | 10.000 | Caso típico de venda |
| 300043 | Valor alto | 100.000 | Grande venda |
| 300044 | Valor altíssimo | 500.000 | Mega venda (edge case) |
| 300045 | FC = 0.0 | 15.000 | Não atingiu nenhuma meta |
| 300046 | FC = 1.0 | 15.000 | Atingiu 100% das metas |
| 300047 | FC = 0.5 | 15.000 | Atingiu 50% das metas |
| 300048 | FC = 0.75 | 15.000 | Atingiu 75% das metas |
| 300049 | FC = 0.95 | 15.000 | Atingiu 95% das metas |
| 300050 | FC variável | 20.000 | Cada colaborador FC diferente |

**Validações Esperadas**:
- ✅ Sistema lida com valores extremos (muito pequenos e muito grandes)
- ✅ Comissões zeradas quando FC = 0.0
- ✅ Comissões máximas quando FC = 1.0
- ✅ Diferentes FCs para diferentes colaboradores no mesmo processo

---

### Bloco 3: Cross-Selling (400001-400010)
**Objetivo**: Testar comissões quando um processo tem itens de **múltiplas linhas de negócio** e o Gerente Comercial é um Consultor Externo sem atribuições para aquela linha.

#### Estrutura dos Testes de Cross-Selling

| Processo | Item 1 | Item 2 | Item 3 | Gerente Comercial | Taxa CS | Valor Total (R$) | Mês |
|----------|--------|--------|--------|-------------------|---------|-----------------|-----|
| 400001 | SSO (10k) | Hidrologia (8k) | - | André Camargo | 1% | 18.000 | Agosto |
| 400002 | SSO (12k) | Remediação (10k) | - | Leonardo Camargo | 1% | 22.000 | Agosto |
| 400003 | Hidrologia (15k) | SSO (5k) | Remediação (8k) | Mateus Machado | 1% | 28.000 | Agosto |
| 400004 | SSO (20k) | Hidrologia (15k) | - | André Camargo | 1% | 35.000 | Setembro |
| 400005 | Remediação (18k) | SSO (7k) | - | Leonardo Camargo | 1% | 25.000 | Setembro |
| 400006 | SSO (10k) | SSO (10k) | Hidrologia (10k) | Mateus Machado | 1% | 30.000 | Setembro |
| 400007 | Hidrologia (12k) | Remediação (12k) | - | André Camargo | 1% | 24.000 | Setembro |
| 400008 | SSO (25k) | - | - | Leonardo Camargo | N/A | 25.000 | Setembro |
| 400009 | Hidrologia (8k) | SSO (8k) | Remediação (8k) | Mateus Machado | 1% | 24.000 | Setembro |
| 400010 | Remediação (20k) | Hidrologia (15k) | - | André Camargo | 1% | 35.000 | Setembro |

**Configuração de Cross-Selling** (`CROSS_SELLING.csv`):
- Mateus Machado: 1%
- André Camargo (André Luis Gonçalves Camargo): 1%
- Leonardo Camargo: 1%

**Validações Esperadas**:

1. **Detecção de Cross-Selling**:
   - ✅ Sistema identifica quando "Gerente Comercial-Pedido" é Consultor Externo
   - ✅ Sistema identifica quando há múltiplas linhas no mesmo processo
   - ✅ Sistema verifica se o consultor externo NÃO tem atribuições para aquela linha

2. **Opção A (SUBTRAIR)**:
   - ✅ Taxa de rateio dos outros colaboradores é reduzida pela taxa CS
   - ✅ Fórmula: `taxa_aplicada = taxa_original - (taxa_original × taxa_cs)`
   - ✅ Consultor externo recebe comissão com a taxa reduzida

3. **Opção B (PAGAR SEPARADAMENTE)**:
   - ✅ Consultor externo é removido do cálculo normal
   - ✅ Linha separada de comissão é criada com a taxa CS
   - ✅ Outros colaboradores não são afetados

4. **Processo 400008** (Teste Negativo):
   - ✅ Apenas uma linha (SSO), NÃO deve aplicar cross-selling
   - ✅ Gerente Comercial recebe comissão normal

---

### Bloco 4: FC de Fornecedores (500001-500015)
**Objetivo**: Testar componentes `meta_fornecedor_1` e `meta_fornecedor_2` do FC para **Gerente Linha**, com vendas em moedas nativas (USD/GBP).

#### Configuração de Metas de Fornecedores (`METAS_FORNECEDORES.csv`)

| Linha | Fabricante | Moeda | Meta Anual |
|-------|------------|-------|------------|
| Hidrologia | YSI | USD | 100.000 |
| Hidrologia | ISCO | USD | 100.000 |
| Remediação | QED | USD | 100.000 |
| Remediação | Thermo | USD | 100.000 |
| SSO | HON | USD | 100.000 |
| SSO | ION | GBP | 100.000 |

#### Pesos de FC para Gerente Linha (`PESOS_METAS.csv`)
- `faturamento_linha`: 15%
- `rentabilidade`: 20%
- `conversao_linha`: 30%
- `retencao_clientes`: 15%
- `meta_fornecedor_1`: **10%**
- `meta_fornecedor_2`: **10%**

#### Estrutura dos Testes de FC Fornecedores

| Processo | Fabricante(s) | Moeda | Valor BRL | Valor Moeda Nativa | Mês Fat | Observações |
|----------|---------------|-------|-----------|-------------------|---------|-------------|
| 500001 | YSI | USD | 30.000 | 6.000 USD | Agosto | Teste fornecedor único |
| 500002 | ISCO | USD | 25.000 | 5.000 USD | Agosto | Teste fornecedor único |
| 500003 | QED | USD | 35.000 | 7.000 USD | Agosto | Teste fornecedor único |
| 500004 | Thermo | USD | 40.000 | 8.000 USD | Agosto | Teste fornecedor único |
| 500005 | HON | USD | 28.000 | 5.600 USD | Agosto | Teste fornecedor único |
| 500006 | ION | GBP | 32.000 | ~4.923 GBP | Agosto | Teste moeda GBP |
| 500007 | YSI | USD | 50.000 | 10.000 USD | Setembro | Acumular YTD |
| 500008 | ISCO | USD | 45.000 | 9.000 USD | Setembro | Acumular YTD |
| 500009 | QED | USD | 60.000 | 12.000 USD | Setembro | Acumular YTD |
| 500010 | Thermo | USD | 55.000 | 11.000 USD | Setembro | Acumular YTD |
| 500011 | HON | USD | 38.000 | 7.600 USD | Setembro | Acumular YTD |
| 500012 | ION | GBP | 42.000 | ~6.462 GBP | Setembro | Acumular YTD |
| 500013 | YSI + ISCO | USD | 70.000 | 14.000 USD | Setembro | **2 fornecedores, 2 itens** |
| 500014 | QED + Thermo | USD | 80.000 | 16.000 USD | Setembro | **2 fornecedores, 2 itens** |
| 500015 | HON + ION | Mix | 75.000 | 7.500 USD + 5.769 GBP | Setembro | **2 fornecedores, 2 moedas** |

**Taxas de Câmbio Simuladas**:
- 1 USD = 5,00 BRL
- 1 GBP = 6,50 BRL

**Validações Esperadas**:

1. **Conversão de Moeda**:
   - ✅ Valores em BRL convertidos para moeda nativa do fornecedor
   - ✅ Taxas de câmbio aplicadas corretamente (USD e GBP)
   - ✅ Faturamento YTD calculado na moeda nativa

2. **Cálculo do FC de Fornecedores**:
   - ✅ Componente `meta_fornecedor_1` calculado: `realizado_USD / meta_USD`
   - ✅ Componente `meta_fornecedor_2` calculado (quando aplicável)
   - ✅ Peso de 10% aplicado para cada componente
   - ✅ Cap de atingimento máximo aplicado

3. **Processos com Múltiplos Fornecedores**:
   - ✅ Processo 500013: YSI e ISCO, ambos contam para FC
   - ✅ Processo 500014: QED e Thermo, ambos contam para FC
   - ✅ Processo 500015: HON (USD) e ION (GBP), moedas diferentes

4. **Reconciliações**:
   - ✅ FC de fornecedores só é testado em **reconciliações** (quando processo teve adiantamento)
   - ✅ FCMP calculado com os componentes de fornecedores incluídos
   - ✅ Ajuste de reconciliação considera o FC real com fornecedores

5. **Exclusividade para Gerente Linha**:
   - ✅ Apenas colaboradores com cargo "Gerente Linha" têm FC de fornecedores
   - ✅ Outros cargos NÃO têm `meta_fornecedor_1/2` nos pesos

---

## 📊 MATRIZ DE COBERTURA DE TESTES

### Comissões por Recebimento (100001-200050)
| Aspecto Testado | Processos | Status |
|-----------------|-----------|--------|
| Adiantamento simples | 100001, 200001-200005 | ✅ |
| Pagamento regular simples | 100005, 100008 | ✅ |
| Adiantamento + Faturamento no mesmo mês | 100002, 200006-200010 | ✅ |
| Adiantamento (Ago) + Faturamento (Set) | 100003, 200011-200015 | ✅ |
| Múltiplos adiantamentos | 100004, 200016-200020 | ✅ |
| Reconciliação positiva (FCMP > 1.0) | - | ⚠️ Raro |
| Reconciliação negativa (FCMP < 1.0) | 100002-100007 | ✅ |
| Múltiplos colaboradores | 100006, 200026-200030 | ✅ |
| Múltiplos pagamentos regulares | 100008, 200031-200035 | ✅ |
| Diferentes linhas de negócio | 200001-200006 | ✅ |
| Variações de FC (alto/médio/baixo) | 200007-200012 | ✅ |
| Processos pendentes (não faturados) | 100001, 100009, 200041-200045 | ✅ |

### Comissões por Faturamento (300001-300050)
| Aspecto Testado | Processos | Status |
|-----------------|-----------|--------|
| Consultor Interno | 300001, 300004, 300005, 300032-300035 | ✅ |
| Consultor Externo | 300003, 300007, 300036-300039 | ✅ |
| Consultor Interno + Externo | 300002, 300008, 300010 | ✅ |
| Múltiplos consultores internos | 300006 | ✅ |
| Diretor | 300001, 300026-300029 | ✅ |
| Gerente Geral | 300002, 300030-300031 | ✅ |
| Coordenador | 300003, 300040 | ✅ |
| Supervisor | 300004, 300010 | ✅ |
| Todas as linhas de negócio | 300001-300025 | ✅ |
| Todos os tipos de mercadoria | 300011-300019 | ✅ |
| FC - faturamento_linha | 300026-300027 | ✅ |
| FC - conversao_linha | 300030-300031 | ✅ |
| FC - faturamento_individual | 300032-300033, 300036-300037 | ✅ |
| FC - conversao_individual | 300034-300035, 300038-300039 | ✅ |
| FC - rentabilidade | 300028-300029 | ✅ |
| Valores extremos | 300041-300044 | ✅ |
| Variação de FC (0.0 a 1.0) | 300045-300049 | ✅ |

### Cross-Selling (400001-400010)
| Aspecto Testado | Processos | Status |
|-----------------|-----------|--------|
| 2 linhas diferentes | 400001, 400002, 400004, 400005, 400007, 400010 | ✅ |
| 3 linhas diferentes | 400003, 400006, 400009 | ✅ |
| Apenas 1 linha (teste negativo) | 400008 | ✅ |
| André Camargo como Gerente Comercial | 400001, 400004, 400007, 400010 | ✅ |
| Leonardo Camargo como Gerente Comercial | 400002, 400005, 400008 | ✅ |
| Mateus Machado como Gerente Comercial | 400003, 400006, 400009 | ✅ |
| SSO + Hidrologia | 400001, 400004 | ✅ |
| SSO + Remediação | 400002, 400005 | ✅ |
| Hidrologia + SSO + Remediação | 400003, 400009 | ✅ |
| Hidrologia + Remediação | 400007 | ✅ |
| Remediação + Hidrologia | 400010 | ✅ |

### FC de Fornecedores (500001-500015)
| Aspecto Testado | Processos | Status |
|-----------------|-----------|--------|
| Fornecedor YSI (USD) | 500001, 500007, 500013 | ✅ |
| Fornecedor ISCO (USD) | 500002, 500008, 500013 | ✅ |
| Fornecedor QED (USD) | 500003, 500009, 500014 | ✅ |
| Fornecedor Thermo (USD) | 500004, 500010, 500014 | ✅ |
| Fornecedor HON (USD) | 500005, 500011, 500015 | ✅ |
| Fornecedor ION (GBP) | 500006, 500012, 500015 | ✅ |
| Moeda USD | 500001-500005, 500007-500011, 500013-500014 | ✅ |
| Moeda GBP | 500006, 500012, 500015 | ✅ |
| Múltiplos fornecedores mesma moeda | 500013, 500014 | ✅ |
| Múltiplos fornecedores moedas diferentes | 500015 | ✅ |
| Acumulação YTD (Agosto + Setembro) | Todos | ✅ |

---

## 🔍 COMO VALIDAR OS TESTES

### Passo 1: Executar Cálculos de Comissões

```bash
# Agosto 2025 (comissões por faturamento + recebimento)
python calculo_comissoes.py --mes 8 --ano 2025

# Setembro 2025 (comissões por faturamento + recebimento + reconciliações)
python calculo_comissoes.py --mes 9 --ano 2025
```

### Passo 2: Validar Comissões por Faturamento

**Arquivo de Saída**: `Comissoes_08_2025.xlsx` e `Comissoes_09_2025.xlsx`

**Aba**: `COMISSOES_CALCULADAS`

**Verificar**:
1. ✅ Todos os processos 300001-300050 aparecem
2. ✅ Colaboradores corretos identificados
3. ✅ Taxas de rateio corretas (`taxa_rateio_aplicada`)
4. ✅ Percentual de elegibilidade correto (`percentual_elegibilidade_pe`)
5. ✅ Fator de correção calculado (`fator_correcao_fc`)
6. ✅ Comissão potencial máxima = `faturamento × taxa × pe`
7. ✅ Comissão calculada = `comissao_potencial × fc`
8. ✅ Colunas de auditoria FC preenchidas

### Passo 3: Validar Cross-Selling

**Arquivo de Saída**: `Comissoes_08_2025.xlsx` e `Comissoes_09_2025.xlsx`

**Aba**: `COMISSOES_CALCULADAS` ou `CROSS_SELLING` (se houver)

**Verificar**:
1. ✅ Processos 400001-400010 detectados como cross-selling
2. ✅ Taxa CS de 1% aplicada
3. ✅ Opção A ou B aplicada conforme configuração
4. ✅ Processo 400008 (uma linha só) NÃO aplica cross-selling

### Passo 4: Validar Comissões por Recebimento

**Arquivo de Saída**: `Comissoes_Recebimento_08_2025.xlsx` e `Comissoes_Recebimento_09_2025.xlsx`

**Abas**: `COMISSOES_ADIANTAMENTOS`, `COMISSOES_REGULARES`, `RECONCILIACOES`, `ESTADO`

**Verificar**:
1. ✅ Processos 100001-200050 aparecem no `ESTADO`
2. ✅ TCMP calculado corretamente
3. ✅ FCMP calculado corretamente
4. ✅ Adiantamentos com FC = 1.0
5. ✅ Pagamentos regulares com FCMP real
6. ✅ Reconciliações aplicadas no mês de faturamento

### Passo 5: Validar FC de Fornecedores (nas Reconciliações)

**Arquivo de Saída**: `Comissoes_Recebimento_09_2025.xlsx` (setembro - mês de faturamento)

**Aba**: `RECONCILIACOES`

**Verificar**:
1. ✅ Processos 500001-500015 têm reconciliações (se tiveram adiantamentos)
2. ✅ FCMP inclui componentes `meta_fornecedor_1` e `meta_fornecedor_2`
3. ✅ Colunas de auditoria `moeda_forn1` e `moeda_forn2` preenchidas
4. ✅ Valores em moeda nativa convertidos corretamente
5. ✅ Apenas "Gerente Linha" (Alessandro Cappi) tem FC de fornecedores

---

## 📁 ARQUIVOS GERADOS

### Arquivos de Entrada
- ✅ `dados_entrada/Analise_Comercial_Completa.xlsx` (processos 100001-200050 - recebimento)
- ✅ `dados_entrada/Análise Financeira.xlsx` (pagamentos para recebimento)
- ✅ `dados_entrada/Faturados_08_2025.xlsx` (processos 300001-500015 - agosto)
- ✅ `dados_entrada/Faturados_09_2025.xlsx` (processos 300001-500015 - setembro)
- ✅ `dados_entrada/Conversões_08_2025.xlsx` (conversões - agosto)
- ✅ `dados_entrada/Conversões_09_2025.xlsx` (conversões - setembro)
- ✅ `dados_entrada/vendas_fornecedores_moeda_nativa.xlsx` (vendas em USD/GBP)
- ✅ `dados_entrada/rentabilidades/rentabilidade_08_2025_agrupada.xlsx`
- ✅ `dados_entrada/rentabilidades/rentabilidade_09_2025_agrupada.xlsx`
- ✅ `dados_entrada/rentabilidades/rentabilidade_10_2025_agrupada.xlsx`

### Arquivos de Saída (Após Execução)
- `Comissoes_08_2025.xlsx` (comissões por faturamento - agosto)
- `Comissoes_09_2025.xlsx` (comissões por faturamento - setembro)
- `Comissoes_Recebimento_08_2025.xlsx` (comissões por recebimento - agosto)
- `Comissoes_Recebimento_09_2025.xlsx` (comissões por recebimento - setembro)

---

## 🎓 GLOSSÁRIO DE TERMOS

| Termo | Significado |
|-------|-------------|
| **TCMP** | Taxa de Comissão Média Ponderada (para recebimento) |
| **FCMP** | Fator de Correção Médio Ponderado (para recebimento) |
| **FC** | Fator de Correção (multiplicador baseado em metas) |
| **PE** | Percentual de Elegibilidade (fatia do cargo na comissão) |
| **Taxa de Rateio** | Taxa de comissão base sobre o valor do item |
| **Cross-Selling** | Venda com múltiplas linhas de negócio no mesmo processo |
| **Adiantamento (COT)** | Pagamento antes do faturamento (FC = 1.0) |
| **Pagamento Regular** | Pagamento após o faturamento (usa FCMP) |
| **Reconciliação** | Ajuste no mês de faturamento para corrigir adiantamentos |
| **YTD** | Year-to-Date (acumulado do ano) |

---

## ✅ CHECKLIST DE VALIDAÇÃO FINAL

- [ ] Todos os 132 processos foram criados corretamente
- [ ] Arquivos de entrada gerados (Faturados, Conversões, Análise Comercial, Análise Financeira)
- [ ] Arquivos de rentabilidade simulada criados
- [ ] Arquivo de vendas de fornecedores em moedas nativas criado
- [ ] Executado cálculo de comissões para Agosto 2025
- [ ] Executado cálculo de comissões para Setembro 2025
- [ ] Validadas comissões por faturamento (300001-300050)
- [ ] Validadas comissões por recebimento (100001-200050)
- [ ] Validado cross-selling (400001-400010)
- [ ] Validado FC de fornecedores em reconciliações (500001-500015)
- [ ] Verificadas colunas de auditoria do FC
- [ ] Conferidas taxas e PEs conforme `CONFIG_COMISSAO.csv`
- [ ] Conferidos pesos de metas conforme `PESOS_METAS.csv`
- [ ] Verificada conversão de moedas (USD/GBP)
- [ ] Sistema sem erros ou warnings críticos

---

**Versão**: 1.0  
**Data**: 17/11/2025  
**Autor**: Sistema Automático de Testes  
**Status**: ✅ COMPLETO

