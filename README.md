# 🤖 Sistema de Cálculo de Comissões

Sistema automatizado para cálculo de comissões por **faturamento** e por **recebimento**, com reconciliações e geração de relatórios em Excel e PDF.

## 📚 Documentação

Toda a documentação do projeto está organizada na pasta **[`documentacoes/`](./documentacoes/)**

### 📖 Acesso Rápido

- **[📚 Índice Completo de Documentação](./documentacoes/README.md)** - Comece aqui!
- **[🎯 Visão Geral do Sistema](./documentacoes/DOCUMENTACAO_ROBO_COMISSOES.md)** - Funcionamento geral
- **[💰 Comissões por Recebimento (Detalhado)](./documentacoes/COMISSOES_POR_RECEBIMENTO_DETALHADO.md)** - Guia completo com exemplos
- **[🏗️ Estrutura do Projeto](./documentacoes/README_ESTRUTURA.md)** - Organização do código

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.x
- Bibliotecas: `pandas`, `openpyxl`, `requests`, `reportlab`

### Instalação
```bash
pip install -r requirements.txt
```

### Execução
```bash
python calculo_comissoes.py
```

O sistema solicitará:
1. **Ano de apuração** (ex: 2025)
2. **Mês de apuração** (1-12)

### Arquivos de Entrada Necessários

| Arquivo | Localização | Descrição |
|---------|-------------|-----------|
| `Regras_Comissoes.xlsx` | raiz | Regras, metas, pesos e colaboradores |
| `Analise_Comercial_Completa.xlsx` | `dados_entrada/` | Processos comerciais (gerado pelo preparador) |
| `Análise Financeira.xlsx` | `dados_entrada/` | Pagamentos recebidos dos clientes |
| `Rentabilidade_*.xlsx` | `dados_entrada/rentabilidades/` | Rentabilidade realizada por contexto |

### Arquivos de Saída

| Arquivo | Descrição |
|---------|-----------|
| `Comissoes_Calculadas_*.xlsx` | Comissões por **faturamento** (item a item) |
| `Comissoes_Recebimento_*.xlsx` | Comissões por **recebimento** (a nível de processo) |
| `Detalhamento_Comissoes_*.pdf` | Relatório detalhado em PDF (opcional) |

## 📊 Tipos de Comissão

### 💼 Comissões por Faturamento
- Calculadas **item a item** no momento do faturamento
- Para todos os colaboradores
- Baseadas em taxa por item e FC por item

### 💰 Comissões por Recebimento (Nova Lógica)
- Calculadas **a nível de processo** quando o cliente paga
- Apenas para **Gerentes de Linha**
- Baseadas em TCMP e FCMP (médias ponderadas)
- Inclui adiantamentos (COT) e pagamentos regulares

## 🔍 Recursos Principais

- ✅ Cálculo automático de Fator de Correção (FC) baseado em múltiplas metas
- ✅ Identificação de colaboradores via ATRIBUICOES (gestão)
- ✅ Suporte a cross-selling
- ✅ Reconciliações no mês do faturamento
- ✅ Estado persistente de processos
- ✅ Logs detalhados para debugging
- ✅ Validações e avisos automáticos

## 📁 Estrutura do Projeto

```
PROJETO_COMISSOES_V2/
├── calculo_comissoes.py          # Script principal
├── preparador_dados.py           # Preparação de arquivos de entrada
├── data_loader.py               # Carregamento de dados
├── documentacoes/               # 📚 Toda a documentação
│   ├── README.md               # Índice de documentação
│   ├── DOCUMENTACAO_ROBO_COMISSOES.md
│   ├── COMISSOES_POR_RECEBIMENTO_DETALHADO.md
│   └── ...
├── src/
│   └── recebimento/            # Módulos de comissão por recebimento
│       ├── recebimento_orchestrator.py
│       ├── core/              # Lógica de cálculo
│       ├── estado/            # Gerenciamento de estado
│       ├── io/                # Entrada/Saída
│       └── utils/             # Utilitários
├── config/                     # Arquivos de configuração (do Excel)
├── dados_entrada/             # Dados de entrada
│   └── rentabilidades/       # Histórico de rentabilidade
└── tests/                     # Testes automatizados
```

## 🛠️ Desenvolvimento

### Executar Testes
```bash
cd tests
python test_calculo_comissoes.py
```

### Debugging
- Ative logs detalhados em `PARAMS.csv`:
  - `debug_terminal_fornecedores`: Debug de fornecedores
  - `debug_show_missing_fornecedores`: Avisos de fornecedores faltantes
- Consulte a aba `VALIDACAO` no Excel de saída para avisos e erros

## 📞 Suporte

Para dúvidas sobre:
- **Conceitos e lógica**: Consulte [`documentacoes/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`](./documentacoes/COMISSOES_POR_RECEBIMENTO_DETALHADO.md)
- **Estrutura do código**: Consulte [`documentacoes/README_ESTRUTURA.md`](./documentacoes/README_ESTRUTURA.md)
- **FAQ e problemas comuns**: Veja seção FAQ em cada documento

## 📝 Notas de Versão

### Versão Atual: 2.0
- ✅ Implementado cálculo de comissões por recebimento
- ✅ Aba ESTADO para gerenciamento persistente de processos
- ✅ Separação completa entre faturamento e recebimento
- ✅ Logs detalhados com prefixo `[RECEBIMENTO]`
- ✅ Documentação completa e organizada
- 🔄 Reconciliações (em desenvolvimento)

---

**📚 Para informações completas, acesse a [documentação](./documentacoes/README.md)**

