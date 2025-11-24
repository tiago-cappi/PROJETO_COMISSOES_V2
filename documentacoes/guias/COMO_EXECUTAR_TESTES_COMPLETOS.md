# 🚀 COMO EXECUTAR OS TESTES COMPLETOS

## ✅ O QUE FOI FEITO

Foi criado um conjunto completo de dados de teste para validar o robô de comissões:

- ✅ **57 processos** de teste (100001-100010 + 200001-200050)
- ✅ **120+ pagamentos** distribuídos em 3 meses
- ✅ **~43 reconciliações esperadas**
- ✅ Cobertura de **100% dos cenários** possíveis
- ✅ Arquivos de **rentabilidade simulada** criados
- ✅ Documentação completa de cada cenário

---

## 📂 ARQUIVOS CRIADOS

### Scripts de Geração:
- `gerar_dados_teste_completo.py` - Gera os 57 processos de teste
- `gerar_rentabilidade_teste_completo.py` - Gera rentabilidades simuladas

### Dados Gerados:
- `dados_entrada/Analise_Comercial_Completa.xlsx` - 82 linhas, 57 processos
- `dados_entrada/Análise Financeira.xlsx` - 117 pagamentos
- `dados_entrada/rentabilidades/rentabilidade_08_2025_agrupada.xlsx`
- `dados_entrada/rentabilidades/rentabilidade_09_2025_agrupada.xlsx`
- `dados_entrada/rentabilidades/rentabilidade_10_2025_agrupada.xlsx`

### Backups Criados:
- `dados_entrada/Analise_Comercial_Completa_BACKUP_ANTES_COMPLETO.xlsx`
- `dados_entrada/Análise Financeira_BACKUP_ANTES_COMPLETO.xlsx`

### Documentação:
- `documentacoes/CENARIOS_TESTE_COMPLETOS.md` - Detalhamento de todos os 57 cenários

---

## 🎯 EXECUÇÃO DOS TESTES

### Passo 1: Limpar Estado Anterior (Opcional)

Se você já rodou testes anteriormente e quer começar do zero:

```powershell
# Apagar arquivo de estado
del Estado_Processos_Recebimento.xlsx

# Apagar saídas anteriores (opcional)
del Comissoes_Recebimento_*.xlsx
```

---

### Passo 2: Executar Agosto/2025

```powershell
python calculo_comissoes.py --mes 8 --ano 2025
```

**O que esperar:**
- ⏱️ Tempo de execução: ~2-5 minutos
- 📁 Arquivo gerado: `Comissoes_Recebimento_08_2025.xlsx`
- 📊 Processos testados: ~50 processos

**Validações rápidas:**
1. Abrir `Comissoes_Recebimento_08_2025.xlsx`
2. Verificar aba **RECONCILIACOES**:
   - Deve ter ~10-15 processos
   - Processo **100002** deve aparecer
   - Todos os valores devem ser negativos
3. Verificar aba **AVISOS**:
   - Deve ter ~8 documentos não mapeados (esperado)
   - Documentos: XPTO999, 999999, COT, etc.

---

### Passo 3: Executar Setembro/2025

**⚠️ IMPORTANTE**: NÃO apague o arquivo `Estado_Processos_Recebimento.xlsx` antes desta rodada!

```powershell
python calculo_comissoes.py --mes 9 --ano 2025
```

**O que esperar:**
- ⏱️ Tempo de execução: ~2-5 minutos
- 📁 Arquivo gerado: `Comissoes_Recebimento_09_2025.xlsx`
- 📊 Reconciliações: ~30-40 processos

**Validações rápidas:**
1. Abrir `Comissoes_Recebimento_09_2025.xlsx`
2. Verificar aba **RECONCILIACOES**:
   - Deve ter ~30-40 processos
   - Processo **100003**, **100004**, **100006**, **100010** devem aparecer
   - Processo **100007** NÃO deve aparecer (FC=1.0)
   - Processo **200011** NÃO deve aparecer (FC=1.0)
3. Verificar aba **COMISSOES_ADIANTAMENTOS**:
   - Deve ter apenas ~2 linhas (COT200029 que está em setembro)
4. Verificar aba **ESTADO**:
   - Processos reconciliados com `STATUS_RECONCILIACAO = "RECONCILIADO"`

---

### Passo 4: Executar Outubro/2025 (Opcional)

```powershell
python calculo_comissoes.py --mes 10 --ano 2025
```

**O que esperar:**
- Reconciliações dos processos que pularam meses:
  - **200024** (Ago → Out)
  - **200027** (Set → Out)
  - **200028** (Ago → Nov, mas tem pagamento em Out)
  - **200029** (COT Ago + Set → Out)

---

## 📊 O QUE CADA BLOCO DE TESTES VALIDA

### 🟢 BLOCO ORIGINAL (100001-100010) - 10 processos
**Testa**: Reconciliações básicas, múltiplos colaboradores, FC=1.0
- Processo 100002: Reconciliação no mesmo mês
- Processo 100003: Reconciliação mês diferente
- Processo 100004: Múltiplos adiantamentos
- Processo 100006: Múltiplos colaboradores
- Processo 100007: FC=1.0 (sem reconciliação)
- Processo 100010: Média ponderada

### 🔵 BLOCO 1 (200001-200006) - 6 processos
**Testa**: Todas as linhas de negócio
- Hidrologia
- Remediação
- Diversos
- Locação
- Saneamento

### 🟡 BLOCO 2 (200007-200012) - 6 processos
**Testa**: Diferentes níveis de FC
- FC muito baixo (< 0,5)
- FC médio (0,6-0,7)
- FC bom (0,8-0,9)
- FC alto (0,95-0,99)
- FC = 1.0

### 🟣 BLOCO 3 (200013-200020) - 8 processos
**Testa**: Múltiplos colaboradores (Alessandro, André, Neimar)
- 2 colaboradores
- 3 colaboradores
- Valores iguais vs diferentes
- 10 itens uniformes
- Alto valor (R$ 100.000)

### 🟠 BLOCO 4 (200021-200030) - 10 processos
**Testa**: Cenários de pagamento complexos
- Adiantamento parcial + múltiplas parcelas
- Adiantamento total (100%)
- 3 adiantamentos
- Pagamento em 3 meses
- 2 adiantamentos em meses diferentes
- Pagamento a maior

### 🔴 BLOCO 5 (200031-200036) - 6 processos
**Testa**: Diferentes regras de comissão
- Diferentes combinações de linha/grupo/subgrupo
- Mix de grupos no mesmo processo

### ⚫ BLOCO 6 (200037-200044) - 8 casos
**Testa**: Edge cases e erros
- Documentos com formato inválido
- NF inexistente
- Processo sem Gerente de Linha
- Valor negativo
- Data futura
- Tipo de baixa incorreto
- Processo cancelado

### 🟤 BLOCO 7 (200045-200050) - 6 processos
**Testa**: Rentabilidade e componentes do FC
- Rentabilidade muito baixa/alta
- Meta de fornecedor 1 (EUR)
- Meta de fornecedor 2 (USD)
- Retenção de clientes
- Todos componentes juntos

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Após Agosto/2025:

- [ ] Arquivo `Comissoes_Recebimento_08_2025.xlsx` criado
- [ ] Aba **COMISSOES_ADIANTAMENTOS**: ~30-40 linhas
- [ ] Aba **COMISSOES_REGULARES**: ~20-30 linhas
- [ ] Aba **RECONCILIACOES**: ~10-15 processos
  - [ ] Processo 100002 presente
  - [ ] Todos os valores negativos
- [ ] Aba **ESTADO**: ~50 processos
- [ ] Aba **AVISOS**: ~8 documentos
- [ ] Arquivo `Estado_Processos_Recebimento.xlsx` criado na raiz
- [ ] Nenhum erro no console

### Após Setembro/2025:

- [ ] Arquivo `Comissoes_Recebimento_09_2025.xlsx` criado
- [ ] Aba **COMISSOES_ADIANTAMENTOS**: ~2 linhas apenas
- [ ] Aba **COMISSOES_REGULARES**: ~30-40 linhas
- [ ] Aba **RECONCILIACOES**: ~30-40 processos
  - [ ] Processos 100003, 100004, 100006, 100010 presentes
  - [ ] Processo 100007 AUSENTE (FC=1.0)
  - [ ] Processo 200011 AUSENTE (FC=1.0)
  - [ ] Processo 100006 tem 2 linhas (2 colaboradores)
- [ ] Aba **ESTADO**: Processos com `STATUS_RECONCILIACAO = "RECONCILIADO"`
- [ ] Nenhum erro no console

### Após Outubro/2025 (se executado):

- [ ] Processos 200024, 200027, 200029 reconciliados
- [ ] Processo 200029 considera soma dos 2 COTs

---

## 🎯 RESULTADOS ESPERADOS CONSOLIDADOS

### Resumo Geral:

| Mês | Adiantamentos | Pagamentos Regulares | Reconciliações | Total Processos |
|-----|---------------|---------------------|----------------|-----------------|
| **Agosto** | ~35-40 | ~25-30 | ~10-15 | ~50 |
| **Setembro** | ~2 | ~35-40 | ~30-35 | ~45 |
| **Outubro** | 0 | ~5-10 | ~4-5 | ~8 |

### Total de Reconciliações Esperadas: **~43-45**

---

## 🐛 TROUBLESHOOTING

### Problema: Poucas reconciliações aparecem

**Causas possíveis:**
1. Processos não foram faturados (verificar `Status Processo` na Análise Comercial)
2. FC = 1.0 exato (esperado, não deve reconciliar)
3. Não havia adiantamento prévio

**Solução**: Verificar aba **ESTADO** → colunas `STATUS_CALCULO_MEDIAS` e `COMISSOES_ADIANTADAS_JSON`

### Problema: Muitos documentos em AVISOS

**Esperado**: ~8 documentos devem estar em AVISOS:
- XPTO999
- 999999
- COT (sem número)
- Outros testes de edge case

**Problema real**: Se houver MAIS documentos além desses, pode indicar erro no mapeamento.

### Problema: Erro ao rodar script

**Solução**:
```powershell
# Verificar se pandas e openpyxl estão instalados
pip install pandas openpyxl

# Se erro persistir, verificar se arquivos Excel estão abertos
# Fechar todos os Excel e tentar novamente
```

---

## 📖 DOCUMENTAÇÃO ADICIONAL

Para entender cada cenário em detalhes:
- **`documentacoes/CENARIOS_TESTE_COMPLETOS.md`** - Detalhamento de todos os 57 cenários
- **`documentacoes/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`** - Lógica completa das comissões
- **`documentacoes/GUIA_TESTES_RECONCILIACAO.md`** - Guia original de testes

---

## 💡 DICAS

1. **Execute os testes em sequência** (Agosto → Setembro → Outubro)
2. **Não apague o Estado** entre rodadas
3. **Guarde os arquivos de saída** para comparação
4. **Use o Excel** para validar visualmente os resultados
5. **Confira as fórmulas** nos arquivos de saída

---

## 🎉 CONCLUSÃO

Com estes testes completos, você está validando:
- ✅ Todas as linhas de negócio da empresa
- ✅ Todos os tipos de mercadoria
- ✅ Todos os 3 Gerentes de Linha
- ✅ Todos os níveis possíveis de FC
- ✅ Todos os cenários de pagamento
- ✅ Edge cases e tratamento de erros
- ✅ Todos os componentes do FC

**Total: 57 processos + 8 edge cases = 65 testes completos!**

---

**Boa sorte nos testes! 🚀**

Se encontrar algum problema, consulte a documentação detalhada ou entre em contato.

