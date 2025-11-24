# 📊 Resultados Esperados dos Testes - Robô de Comissões

Este documento detalha os resultados esperados nos arquivos de saída do robô para os cenários de teste gerados pelo script `gerar_todos_dados_teste.py`. Use este guia para validar se o processamento ocorreu corretamente.

---

## 📂 1. Arquivo: `Comissoes_MM_AAAA.xlsx` (Faturamento)

Este arquivo contém as comissões calculadas item a item no momento do faturamento.
**Cenários Cobertos**: Blocos 3 (Faturamento) e 4 (Cross-Selling).

### 📑 Aba: `COMISSOES_CALCULADAS`

#### ✅ Cenários de Faturamento Normal (Bloco 3)
Exemplos de linhas esperadas para processos 300001-300050.

| Processo | Colaborador | Cargo | Valor Base | Taxa Rateio | PE | FC (Est.) | Comissão (Est.) | Observação |
|---|---|---|---|---|---|---|---|---|
| **300001** | Andrey Andrade | Consultor Interno | R$ 50.000 | 100% | 1,5% | ~0,8-1,0 | ~R$ 600-750 | Consultor Interno padrão |
| **300001** | Diretor | Diretor | R$ 50.000 | 100% | 0,5% | ~0,8-1,0 | ~R$ 200-250 | Comissão de gestão |
| **300002** | Mateus Machado | Consultor Interno | R$ 30.000 | 100% | 1,5% | ~0,8-1,0 | ~R$ 360-450 | Consultor Interno |
| **300002** | André Camargo | Consultor Externo | R$ 30.000 | 100% | 3,5% | ~0,8-1,0 | ~R$ 840-1.050 | Representante com atribuição |
| **300002** | Gerente Geral | Gerente Geral | R$ 30.000 | 100% | 0,3% | ~0,8-1,0 | ~R$ 72-90 | Comissão de gestão |
| **300003** | Leonardo Carmo | Consultor Externo | R$ 20.000 | 100% | 3,5% | ~0,8-1,0 | ~R$ 560-700 | Apenas Representante |

#### ✅ Cenários de Cross-Selling (Bloco 4)
Exemplos de linhas esperadas para processos 400001-400010.
*Nota: Assumindo configuração "SUBTRAIR" (Opção A) e Taxa CS = 1%.*

| Processo | Item | Colaborador | Cargo | Taxa Rateio | Observação |
|---|---|---|---|---|---|
| **400001** | SSO (10k) | André Camargo | Consultor Externo | 100% | Linha normal (tem atribuição) |
| **400001** | Hidrologia (8k) | André Camargo | Consultor Externo | **1%** (Fixa) | **CROSS-SELLING** (não tem atribuição) |
| **400002** | Hidrologia (12k) | Mateus Machado | Consultor Externo | 100% | Linha normal (tem atribuição) |
| **400002** | SSO (10k) | Mateus Machado | Consultor Externo | **1%** (Fixa) | **CROSS-SELLING** (não tem atribuição) |
| **400008** | SSO (25k) | Leonardo Carmo | Consultor Externo | 100% | **NÃO É CROSS-SELLING** (apenas 1 linha e tem atribuição) |

---

## 📂 2. Arquivo: `Comissoes_Recebimento_MM_AAAA.xlsx` (Recebimento)

Este arquivo contém as comissões pagas no recebimento (Gestores de Linha) e as reconciliações.
**Cenários Cobertos**: Blocos 1 (Original), 2 (Expandido) e 4 (FC Fornecedores).

### 📑 Aba: `COMISSOES_ADIANTAMENTOS` (Execução Agosto)
Comissões pagas sobre adiantamentos (COT), sempre com **FC = 1.0**.

| Processo | Colaborador | Valor Pago | FC Aplicado | Comissão | Observação |
|---|---|---|---|---|---|
| **100001** | Alessandro Cappi | R$ 5.000 | **1,0** | R$ 5.000 * Taxa * PE | Adiantamento simples |
| **100002** | Alessandro Cappi | R$ 7.500 | **1,0** | R$ 7.500 * Taxa * PE | Adiantamento (será reconciliado) |
| **100003** | Alessandro Cappi | R$ 10.000 | **1,0** | R$ 10.000 * Taxa * PE | Adiantamento (será reconciliado em Set) |
| **100006** | Alessandro Cappi | R$ 9.000 | **1,0** | (Proporcional) | Adiantamento compartilhado (60%) |
| **100006** | André Caramello | R$ 6.000 | **1,0** | (Proporcional) | Adiantamento compartilhado (40%) |

### 📑 Aba: `RECONCILIACOES` (Execução Setembro)
Ajustes feitos quando o processo é faturado e o FCMP real é apurado.
*Fórmula: (Valor Total Pago * FCMP Real) - (Valor Adiantado * 1.0)*

| Processo | Colaborador | Valor Base | FCMP Real | Valor Adiantado | Ajuste Esperado | Observação |
|---|---|---|---|---|---|---|
| **100002** | Alessandro Cappi | R$ 15.000 | < 1,0 | R$ 7.500 | **NEGATIVO** | FCMP real menor que 1.0 |
| **100003** | Alessandro Cappi | R$ 20.000 | < 1,0 | R$ 10.000 | **NEGATIVO** | Reconciliação de mês anterior |
| **100007** | Alessandro Cappi | R$ 30.000 | **~1,0** | R$ 15.000 | **ZERO / POUCO** | FC alto (Serviço), pouco ajuste |
| **500001** | Alessandro Cappi | R$ 30.000 | Variável | R$ 15.000 | Variável | FC inclui meta fornecedor YSI (USD) |
| **500006** | Alessandro Cappi | R$ 32.000 | Variável | R$ 16.000 | Variável | FC inclui meta fornecedor ION (GBP) |

### 📑 Aba: `ESTADO` (Persistência)
Verifique se os processos estão sendo rastreados corretamente.

| Processo | Status | TCMP | FCMP | Status Reconciliação |
|---|---|---|---|---|
| **100001** | PENDENTE | Calculado | 1.0 (Prov.) | PENDENTE |
| **100002** | FATURADO | Calculado | Calculado | **CONCLUIDA** |
| **100009** | PENDENTE | Calculado | 1.0 (Prov.) | PENDENTE |
| **200024** | FATURADO | Calculado | Calculado | PENDENTE (se faturado em mês futuro) |

---

## 🔍 Detalhes Específicos de Validação

### 1. FC de Fornecedores (Bloco 4 - Processos 5000xx)
Verificar na aba `RECONCILIACOES` (ou logs) se os componentes de fornecedor foram ativados para o **Gerente de Linha**:
*   **500001**: Deve ter componente `meta_fornecedor_1` (YSI) calculado.
*   **500015**: Deve ter `meta_fornecedor_1` (HON) e `meta_fornecedor_2` (ION) calculados.
*   **Moedas**: Verificar se os valores realizados foram convertidos corretamente (USD ~5.0, GBP ~6.5).

### 2. Cross-Selling (Bloco 4 - Processos 4000xx)
Verificar na aba `COMISSOES_CALCULADAS`:
*   **Identificação**: A coluna `tipo_comissao` ou observação deve indicar "Cross-Selling".
*   **Taxa**: A taxa aplicada deve ser exatamente a configurada (ex: 1%), ignorando a taxa padrão da linha.

### 3. Reconciliação Negativa
É o comportamento **esperado** e correto para a maioria dos casos.
*   Como o adiantamento paga com FC=1.0 (meta 100% atingida), e raramente se atinge 100% de todas as metas, o FCMP real costuma ser menor (ex: 0.85).
*   Isso gera uma devolução da diferença: `Valor * (0.85 - 1.0) = Valor * -0.15`.

---

**Dica de Debug**: Se algum valor estiver muito discrepante, verifique os arquivos de log gerados na pasta `logs/` ou a aba `VALIDACAO` nos arquivos Excel.
