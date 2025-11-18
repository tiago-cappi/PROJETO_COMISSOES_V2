# 🚀 INÍCIO RÁPIDO - SISTEMA DE COMISSÕES

## ⚡ EXECUTAR TESTES EM 3 MINUTOS

### 1️⃣ Gerar Dados de Teste
```bash
python tests/geradores_dados/gerar_todos_dados_teste.py
python tests/geradores_dados/gerar_rentabilidade_teste.py
```
⏱️ Tempo: ~30 segundos

---

### 2️⃣ Executar Robô de Comissões
```bash
python calculo_comissoes.py --mes 8 --ano 2025
python calculo_comissoes.py --mes 9 --ano 2025
```
⏱️ Tempo: ~2-3 minutos por mês

---

### 3️⃣ Validar Resultados
Abra os arquivos gerados:
- `Comissoes_08_2025.xlsx` (faturamento)
- `Comissoes_09_2025.xlsx` (faturamento)
- `Comissoes_Recebimento_08_2025.xlsx` (recebimento)
- `Comissoes_Recebimento_09_2025.xlsx` (recebimento + reconciliações)

**Validação completa**: `documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`

---

## 📚 DOCUMENTAÇÃO PRINCIPAL

| Documento | Quando Usar |
|-----------|-------------|
| **[README_PROJETO.md](README_PROJETO.md)** | Visão geral do projeto |
| **[documentacoes/INDEX.md](documentacoes/INDEX.md)** | Índice completo de documentações |
| **[RESUMO_REORGANIZACAO.md](RESUMO_REORGANIZACAO.md)** | O que mudou na reorganização |

---

## 🎯 O QUE O SISTEMA FAZ

### Entrada
- `Analise_Comercial_Completa.xlsx` - Dados comerciais
- `Análise Financeira.xlsx` - Pagamentos (para recebimento)

### Processamento Automático
O robô executa automaticamente `preparar_dados_mensais.py` para gerar:
- `Faturados.xlsx`
- `Conversões.xlsx`
- `Faturados_YTD.xlsx`
- `Retencao_Clientes.xlsx`

### Saída
- `Comissoes_MM_AAAA.xlsx` - Comissões por faturamento
- `Comissoes_Recebimento_MM_AAAA.xlsx` - Comissões por recebimento

---

## 📊 TESTES INCLUÍDOS

**135 processos de teste**:
- 60 processos para Comissões por Recebimento
- 50 processos para Comissões por Faturamento
- 10 processos para Cross-Selling
- 15 processos para FC de Fornecedores

---

## ⚠️ IMPORTANTE

### ✅ O Fluxo Correto É:
1. Gerar APENAS `Analise_Comercial_Completa.xlsx` e `Análise Financeira.xlsx`
2. Executar o robô (ele gera os arquivos intermediários automaticamente)
3. Validar os resultados

### ❌ NÃO Gere Manualmente:
- `Faturados.xlsx`
- `Conversões.xlsx`
- `Faturados_YTD.xlsx`
- `vendas_fornecedores_moeda_nativa.xlsx` (não existe mais!)

---

## 🆘 PROBLEMAS?

1. **Erro ao gerar dados**: Ver `tests/geradores_dados/README.md`
2. **Erro ao executar robô**: Ver logs na tela
3. **Dúvidas sobre testes**: Ver `documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`
4. **Dúvidas sobre o sistema**: Ver `documentacoes/sistema/DOCUMENTACAO_ROBO_COMISSOES.md`

---

## 📁 ESTRUTURA RÁPIDA

```
PROJETO_COMISSOES_V2/
├── tests/geradores_dados/     ← Scripts de teste
├── documentacoes/              ← Documentação organizada
│   ├── guias/                  ← Guias de uso
│   ├── sistema/                ← Docs técnicas
│   └── testes/                 ← Docs de testes
├── config/                     ← Configurações (NÃO ALTERAR)
├── dados_entrada/              ← Arquivos de entrada
└── calculo_comissoes.py        ← Script principal
```

---

**Próximo Passo**: Siga este documento para começar ou leia `README_PROJETO.md` para mais detalhes!

---

**Versão**: 1.0  
**Data**: 18/11/2025

