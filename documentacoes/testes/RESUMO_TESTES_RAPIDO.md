# 🎯 RESUMO RÁPIDO - TESTES DE RECONCILIAÇÃO

## ✅ Arquivos Criados

- ✅ `dados_entrada/Analise_Comercial_Completa.xlsx` (10 processos)
- ✅ `dados_entrada/Análise Financeira.xlsx` (23 pagamentos)
- 💾 Backups dos arquivos originais salvos automaticamente

---

## 🚀 COMANDOS RÁPIDOS

### Opção 1: Teste Simples (Agosto apenas)
```bash
python calculo_comissoes.py --mes 8 --ano 2025
```
**Testa:** Cenários 1, 2, 5, 8, 9

### Opção 2: Teste Completo (Agosto + Setembro)
```bash
# 1ª Rodada
python calculo_comissoes.py --mes 8 --ano 2025

# 2ª Rodada (NÃO apague o Estado!)
python calculo_comissoes.py --mes 9 --ano 2025
```
**Testa:** TODOS os 10 cenários incluindo reconciliações

---

## 📊 O QUE VERIFICAR

### Arquivo: `Comissoes_Recebimento_08_2025.xlsx`

#### Aba `RECONCILIACOES`:
- ✅ Processo **100002** deve aparecer (faturado em Agosto)
- ✅ Valor de reconciliação deve ser **negativo**
- ✅ Coluna `mes_reconciliacao` = "08/2025"

#### Aba `ESTADO`:
- ✅ Processo 100002: `STATUS_RECONCILIACAO` = "RECONCILIADO"
- ✅ Processo 100002: `COMISSOES_ADIANTADAS_JSON` preenchido

### Arquivo: `Comissoes_Recebimento_09_2025.xlsx`

#### Aba `RECONCILIACOES`:
- ✅ **4 a 5 processos** com reconciliações:
  - 100003 (1 linha)
  - 100004 (1 linha - múltiplos adiantamentos)
  - 100006 (2 linhas - um por colaborador)
  - 100010 (1 linha - média ponderada)
  
- ❌ Processo **100007 NÃO** deve aparecer (FC=1.0)

#### Aba `COMISSOES_ADIANTAMENTOS`:
- ✅ Deve estar **VAZIA** (nenhum COT em Setembro)

---

## 📋 TABELA DE CENÁRIOS

| Processo | Descrição | Mês | Tem Reconciliação? |
|----------|-----------|-----|-------------------|
| 100001 | Adiantamento não faturado | Ago | ❌ Não |
| 100002 | Adiantamento + Faturamento | Ago | ✅ Sim (Ago) |
| 100003 | Adiantamento (Ago) + Faturamento (Set) | Set | ✅ Sim (Set) |
| 100004 | 2× Adiantamentos + Faturamento | Set | ✅ Sim (Set) |
| 100005 | Pagamento regular direto | Ago | ❌ Não |
| 100006 | 2 Colaboradores | Set | ✅ Sim (Set - 2 linhas) |
| 100007 | FC = 1.0 | Set | ❌ Não (FC=1.0) |
| 100008 | 3 Parcelas regulares | Ago | ❌ Não |
| 100009 | NF 5 dígitos | Ago | ❌ Não |
| 100010 | 3 Itens (média ponderada) | Set | ✅ Sim (Set) |

---

## ⚠️ PONTOS DE ATENÇÃO

### ✅ DEVE acontecer:
- Reconciliações aparecem no **mês do faturamento**
- Valores de reconciliação são **negativos** (FCMP < 1.0)
- Processo 100006 tem **2 linhas** (um por colaborador)
- Processo 100004 considera **soma** dos adiantamentos (R$ 15.000)

### ❌ NÃO DEVE acontecer:
- Reconciliação para processo sem adiantamento (ex: 100005)
- Reconciliação para processo não faturado (ex: 100001 em Agosto)
- Reconciliação para FC=1.0 (ex: 100007)

---

## 🐛 Se algo der errado:

### Resetar e recomeçar:
```bash
del Estado_Processos_Recebimento.xlsx
del Comissoes_Recebimento_*.xlsx
python calculo_comissoes.py --mes 8 --ano 2025
python calculo_comissoes.py --mes 9 --ano 2025
```

### Verificar logs:
- Console mostra mensagens `[RECEBIMENTO] [RECONCILIACAO]`
- Aba `AVISOS` mostra documentos não mapeados

---

## 📖 Documentação Completa

Ver arquivo: **`GUIA_TESTES_RECONCILIACAO.md`**

---

**Boa sorte! 🚀**

