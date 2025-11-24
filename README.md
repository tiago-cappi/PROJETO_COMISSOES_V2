# 🎯 SISTEMA DE COMISSÕES - PROJETO COMPLETO

## 📌 ESTRUTURA DO PROJETO

```
PROJETO_COMISSOES_V2/
├── src/                          # Código fonte do sistema
├── config/                       # Arquivos de configuração (regras, metas, etc.)
├── dados_entrada/                # Arquivos de entrada do robô
├── tests/                        # Testes e geradores de dados
│   └── geradores_dados/          # Scripts para gerar dados de teste
├── documentacoes/                # Documentação organizada
│   ├── testes/                   # Docs de testes
│   ├── sistema/                  # Docs técnicas do sistema
│   ├── guias/                    # Guias de uso e execução
│   └── historico/                # Histórico de atualizações e correções
├── frontend/                     # Interface web (opcional)
└── data/                         # Dados auxiliares (taxas de câmbio, etc.)
```

---

## 🚀 INÍCIO RÁPIDO

### Para Executar o Sistema em Produção:

1. Coloque os arquivos de entrada em `dados_entrada/`:
   - `Analise_Comercial_Completa.xlsx`
   - `Análise Financeira.xlsx`

2. Execute o robô:
```bash
python calculo_comissoes.py --mes MM --ano AAAA
```

3. Resultados estarão em:
   - `Comissoes_MM_AAAA.xlsx` (faturamento)
   - `Comissoes_Recebimento_MM_AAAA.xlsx` (recebimento)

---

### Para Executar Testes Completos:

1. **Gerar dados de teste**:
```bash
python tests/geradores_dados/gerar_todos_dados_teste.py
python tests/geradores_dados/gerar_rentabilidade_teste.py
```

2. **Executar testes**:
```bash
python calculo_comissoes.py --mes 8 --ano 2025
python calculo_comissoes.py --mes 9 --ano 2025
```

3. **Validar resultados**:
   - Ver `documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`

---

## 📚 DOCUMENTAÇÃO

### 🎯 Comece por Aqui
- **Visão Geral**: [`documentacoes/sistema/DOCUMENTACAO_ROBO_COMISSOES.md`](documentacoes/sistema/DOCUMENTACAO_ROBO_COMISSOES.md)
- **Índice Completo**: [`documentacoes/INDEX.md`](documentacoes/INDEX.md)

### 🧪 Para Testes
- **Guia de Testes**: [`documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`](documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md)
- **Cenários de Teste**: [`documentacoes/testes/CENARIOS_TESTE_EXPANDIDOS.md`](documentacoes/testes/CENARIOS_TESTE_EXPANDIDOS.md)

### 🔧 Para Desenvolvimento
- **Comissões por Recebimento**: [`documentacoes/sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`](documentacoes/sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md)
- **Estrutura do Código**: [`documentacoes/sistema/README_ESTRUTURA.md`](documentacoes/sistema/README_ESTRUTURA.md)

---

## 🔄 FLUXO DE EXECUÇÃO

### 1. Entrada
- `Analise_Comercial_Completa.xlsx` - Dados comerciais completos
- `Análise Financeira.xlsx` - Dados de pagamentos (para recebimento)

### 2. Preparação Automática
O robô executa `preparar_dados_mensais.py` que gera:
- `Faturados.xlsx` - Processos faturados do mês
- `Conversões.xlsx` - Conversões do mês (baseado em Data Aceite)
- `Faturados_YTD.xlsx` - Faturamento acumulado do ano
- `Retencao_Clientes.xlsx` - Dados de retenção de clientes

### 3. Processamento
- Comissões por Faturamento (item a item)
- Comissões por Recebimento (por processo, com TCMP/FCMP)
- Cálculo de FC (Factor de Correção baseado em metas)
- Cross-Selling (quando aplicável)
- Reconciliações (ajustes de adiantamentos)

### 4. Saída
- `Comissoes_MM_AAAA.xlsx` - Comissões por faturamento
- `Comissoes_Recebimento_MM_AAAA.xlsx` - Comissões por recebimento

---

## 🎓 CONCEITOS-CHAVE

| Conceito | Descrição |
|----------|-----------|
| **Comissões por Faturamento** | Calculadas item a item no momento do faturamento |
| **Comissões por Recebimento** | Calculadas por processo quando o cliente paga (apenas para Gerente Linha) |
| **TCMP** | Taxa de Comissão Média Ponderada (para recebimento) |
| **FCMP** | Fator de Correção Médio Ponderado (para recebimento) |
| **FC** | Fator de Correção (multiplicador baseado em metas, 0.0 a 1.0) |
| **Cross-Selling** | Comissão especial para vendas com múltiplas linhas de negócio |
| **Reconciliação** | Ajuste no mês de faturamento para corrigir adiantamentos |
| **Adiantamento (COT)** | Pagamento antes do faturamento (FC = 1.0) |

---

## 🧪 TESTES IMPLEMENTADOS

**Total: 132 processos de teste**

- 57 processos para Comissões por Recebimento
- 50 processos para Comissões por Faturamento
- 10 processos para Cross-Selling
- 15 processos para FC de Fornecedores

Ver detalhes em: `documentacoes/testes/CENARIOS_TESTE_EXPANDIDOS.md`

---

## ⚙️ REQUISITOS

- Python 3.8+
- pandas
- openpyxl
- numpy

```bash
pip install pandas openpyxl numpy
```

---

## 📞 SUPORTE

Para problemas ou dúvidas:
1. Consulte `documentacoes/INDEX.md` para encontrar a documentação relevante
2. Verifique `documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md` (seção Troubleshooting)

---

**Versão**: 2.0  
**Data**: 18/11/2025  
**Status**: ✅ Pronto para Produção (após validação dos testes)
