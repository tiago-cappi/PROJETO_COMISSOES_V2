# 📚 Documentação do Sistema de Comissões

Bem-vindo à documentação completa do Sistema de Cálculo de Comissões!

## 📑 Índice de Documentos

### 🎯 Documentação Principal

#### [DOCUMENTACAO_ROBO_COMISSOES.md](./DOCUMENTACAO_ROBO_COMISSOES.md)
**Visão Geral do Sistema Completo**
- Descrição de todos os arquivos de entrada e saída
- Fluxo geral de execução do robô
- Comissões por faturamento (item a item)
- Comissões por recebimento (visão geral)
- Reconciliações (conceito)
- Parâmetros e configurações
- Fórmulas-chave

#### [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md) 🆕
**Guia Completo de Comissões por Recebimento**
- Conceitos fundamentais (TCMP, FCMP)
- Detalhamento completo de todos os arquivos de entrada
- Relacionamento entre Análise Financeira e Análise Comercial
- Estrutura e funcionamento da aba ESTADO
- Cálculos matemáticos detalhados com exemplos
- Comissões por adiantamento (COT)
- Comissões por pagamento regular
- Reconciliações (lógica completa a implementar)
- Exemplos práticos passo a passo
- FAQ e resolução de problemas

### 🏗️ Documentação Técnica

#### [README_ESTRUTURA.md](./README_ESTRUTURA.md)
**Estrutura do Projeto**
- Organização de pastas e arquivos
- Descrição dos módulos principais
- Fluxo de dados entre componentes
- Dependências e bibliotecas utilizadas

### 🔧 Documentação de Correções e Refatorações

#### [CORRECOES_FC_RENTABILIDADE.md](./CORRECOES_FC_RENTABILIDADE.md)
**Correções no Cálculo de FC de Rentabilidade**
- Problemas identificados no cálculo original
- Soluções implementadas
- Exemplos de correção

#### [REFATORACAO_TAXAS_CAMBIO.md](./REFATORACAO_TAXAS_CAMBIO.md)
**Refatoração do Sistema de Taxas de Câmbio**
- Melhorias no cálculo de câmbio
- Otimizações de performance
- Cache e reuso de dados

---

## 🚀 Por Onde Começar?

### Se você é novo no sistema:
1. Leia primeiro: **[DOCUMENTACAO_ROBO_COMISSOES.md](./DOCUMENTACAO_ROBO_COMISSOES.md)** para entender a visão geral
2. Depois: **[README_ESTRUTURA.md](./README_ESTRUTURA.md)** para conhecer a estrutura do código

### Se você quer entender comissões por recebimento:
1. Vá direto para: **[COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md)**
   - Este documento contém TUDO sobre o assunto com exemplos práticos

### Se você está debugando um problema:
1. Consulte a seção **"Resolução de Problemas"** em cada documento
2. Verifique o **FAQ** em **[COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md)**

---

## 📊 Comparação: Faturamento vs. Recebimento

| Aspecto | Comissões por Faturamento | Comissões por Recebimento |
|---------|---------------------------|---------------------------|
| **Documentação** | [DOCUMENTACAO_ROBO_COMISSOES.md](./DOCUMENTACAO_ROBO_COMISSOES.md) | [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md) |
| **Momento** | Quando fatura | Quando recebe pagamento |
| **Granularidade** | Item a item | Processo inteiro |
| **Quem recebe** | Todos colaboradores | Apenas Gerentes de Linha |
| **Taxa** | Por item | TCMP (média ponderada) |
| **Fator de Correção** | FC por item | FCMP (média ponderada) |
| **Arquivo de Entrada** | Faturados.xlsx | Análise Financeira.xlsx |
| **Arquivo de Saída** | Comissoes_Calculadas_*.xlsx | Comissoes_Recebimento_*.xlsx |

---

## 🗂️ Organização dos Documentos

```
documentacoes/
├── README.md (este arquivo)
├── DOCUMENTACAO_ROBO_COMISSOES.md
├── COMISSOES_POR_RECEBIMENTO_DETALHADO.md
├── README_ESTRUTURA.md
├── CORRECOES_FC_RENTABILIDADE.md
└── REFATORACAO_TAXAS_CAMBIO.md
```

---

## 🔍 Encontre o que Procura

### Conceitos e Definições
- **TCMP**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#cálculo-de-tcmp)
- **FCMP**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#cálculo-de-fcmp)
- **FC (Fator de Correção)**: [DOCUMENTACAO_ROBO_COMISSOES.md](./DOCUMENTACAO_ROBO_COMISSOES.md#cálculo-do-fator-de-correção-fc)
- **Reconciliação**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#reconciliações-a-implementar)

### Arquivos de Entrada
- **Análise Financeira.xlsx**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#1-análise-financeiraxlsx)
- **Analise_Comercial_Completa.csv**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#2-analise_comercial_completacsv)
- **Regras_Comissoes.xlsx**: [DOCUMENTACAO_ROBO_COMISSOES.md](./DOCUMENTACAO_ROBO_COMISSOES.md#arquivos-de-entrada)

### Aba ESTADO
- **Estrutura**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#aba-estado-estrutura-e-funcionamento)
- **Ciclo de Vida**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#ciclo-de-vida-de-um-processo-no-estado)

### Cálculos e Fórmulas
- **Adiantamento**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#comissões-por-adiantamento)
- **Pagamento Regular**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#comissões-por-pagamento-regular)
- **Reconciliação**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#reconciliações-a-implementar)

### Exemplos Práticos
- **Exemplos Completos**: [COMISSOES_POR_RECEBIMENTO_DETALHADO.md](./COMISSOES_POR_RECEBIMENTO_DETALHADO.md#exemplos-práticos)

---

## 💡 Dicas de Leitura

- 📖 Use o **Índice** no início de cada documento para navegar rapidamente
- 🔍 Use **Ctrl+F** para buscar termos específicos
- 📊 Os exemplos numéricos contêm todos os passos do cálculo
- ❓ Consulte o **Glossário** se encontrar termos desconhecidos
- 🐛 A seção **FAQ** resolve os problemas mais comuns

---

## 📝 Contribuindo com a Documentação

Se você identificar:
- ❌ Informações incorretas ou desatualizadas
- ❓ Conceitos que precisam de mais explicação
- 📝 Exemplos que poderiam ser melhorados
- 🆕 Novos recursos que precisam ser documentados

Por favor, atualize a documentação correspondente mantendo:
- ✅ Clareza e objetividade
- ✅ Exemplos práticos e numéricos
- ✅ Estrutura organizada com índice
- ✅ Links entre documentos relacionados

---

**Última Atualização**: 12/11/2025  
**Versão**: 1.0

