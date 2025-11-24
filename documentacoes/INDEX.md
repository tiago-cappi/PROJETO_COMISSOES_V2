# 📚 ÍNDICE DA DOCUMENTAÇÃO - SISTEMA DE COMISSÕES

## 🗂️ ORGANIZAÇÃO DAS DOCUMENTAÇÕES

As documentações estão organizadas em subpastas temáticas para facilitar a busca:

---

## 📂 `/testes` - Documentação de Testes

Documentações relacionadas aos testes do sistema:

- **`CENARIOS_TESTE_COMPLETOS.md`** - Detalhamento dos 57 processos de teste para comissões por recebimento e reconciliações
- **`CENARIOS_TESTE_EXPANDIDOS.md`** - Detalhamento completo de TODOS os 132 processos de teste (recebimento + faturamento + cross-selling + fornecedores)
- **`GUIA_TESTES_RECONCILIACAO.md`** - Guia original dos 10 cenários de teste para reconciliações
- **`RESUMO_TESTES_RAPIDO.md`** - Resumo rápido dos testes de reconciliação
- **`DADOS_TESTE_ATUALIZADOS.md`** - Detalhes sobre a atualização dos dados de teste com valores reais
- **`VERIFICACAO_CROSS_SELLING.md`** - Análise e verificação dos testes de cross-selling

---

## 📂 `/sistema` - Documentação Técnica do Sistema

Documentações técnicas sobre o funcionamento interno do sistema:

- **`DOCUMENTACAO_ROBO_COMISSOES.md`** - Documentação completa do robô de comissões (visão geral)
- **`COMISSOES_POR_RECEBIMENTO_DETALHADO.md`** - Documentação detalhada da lógica de comissões por recebimento (TCMP, FCMP, reconciliações)
- **`README_ESTRUTURA.md`** - Estrutura de arquivos e pastas do projeto
- **`PLANO_REFATORACAO.txt`** - Histórico de planejamento de refatorações
- **`REFATORACAO_TAXAS_CAMBIO.md`** - Documentação da refatoração do sistema de taxas de câmbio
- **`CORRECOES_FC_RENTABILIDADE.md`** - Correções aplicadas no cálculo de FC de rentabilidade
- **`PRÓXIMOS_PASSOS.md`** - Roadmap e próximos passos do sistema

---

## 📂 `/guias` - Guias de Uso e Execução

Guias práticos para executar e validar os testes:

- **`README_TESTES_COMPLETOS.md`** - **⭐ COMEÇE POR AQUI** - Overview geral de todos os testes
- **`COMO_EXECUTAR_TESTES_EXPANDIDOS.md`** - Guia passo a passo completo de execução dos testes
- **`RESUMO_IMPLEMENTACAO_EXPANDIDA.md`** - Resumo técnico da implementação dos testes expandidos
- **`RESUMO_IMPLEMENTACAO_COMPLETA.md`** - Resumo da implementação completa dos testes
- **`COMO_EXECUTAR_TESTES_COMPLETOS.md`** - Guia específico para execução dos testes completos
- **`INICIO_RAPIDO.md`** - Guia de início rápido para execução e validação

---

## 📂 `/historico` - Histórico de Atualizações
Documentos que registram o histórico de mudanças, correções e reorganizações do projeto:

- **`RESUMO_REORGANIZACAO.md`** - Resumo da reorganização do projeto (Nov 2025)
- **`SUMARIO_FINAL_CORRECOES.md`** - Sumário executivo das correções nos dados de teste
- **`RESUMO_CORRECOES_DADOS_TESTE.md`** - Detalhamento técnico das correções nos dados de teste

---

## 🚀 INÍCIO RÁPIDO

### Para Executar os Testes:

1. **Leia primeiro**: [`guias/README_TESTES_COMPLETOS.md`](guias/README_TESTES_COMPLETOS.md)
2. **Siga o guia**: [`guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`](guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md)

### Para Entender o Sistema:

1. **Visão Geral**: [`sistema/DOCUMENTACAO_ROBO_COMISSOES.md`](sistema/DOCUMENTACAO_ROBO_COMISSOES.md)
2. **Comissões por Recebimento**: [`sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`](sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md)
3. **Estrutura do Projeto**: [`sistema/README_ESTRUTURA.md`](sistema/README_ESTRUTURA.md)

### Para Validar Cenários de Teste:

1. **Todos os Cenários**: [`testes/CENARIOS_TESTE_EXPANDIDOS.md`](testes/CENARIOS_TESTE_EXPANDIDOS.md)
2. **Recebimento**: [`testes/CENARIOS_TESTE_COMPLETOS.md`](testes/CENARIOS_TESTE_COMPLETOS.md)
3. **Reconciliações**: [`testes/GUIA_TESTES_RECONCILIACAO.md`](testes/GUIA_TESTES_RECONCILIACAO.md)

---

## 📊 MAPA DE CONTEÚDO POR TEMA

### Comissões por Faturamento
- [`sistema/DOCUMENTACAO_ROBO_COMISSOES.md`](sistema/DOCUMENTACAO_ROBO_COMISSOES.md) (seção "Cálculo Por Faturamento")
- [`testes/CENARIOS_TESTE_EXPANDIDOS.md`](testes/CENARIOS_TESTE_EXPANDIDOS.md) (Bloco 2)

### Comissões por Recebimento
- [`sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`](sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md) - **Documentação completa**
- [`testes/CENARIOS_TESTE_COMPLETOS.md`](testes/CENARIOS_TESTE_COMPLETOS.md)
- [`testes/GUIA_TESTES_RECONCILIACAO.md`](testes/GUIA_TESTES_RECONCILIACAO.md)

### Cross-Selling
- [`sistema/DOCUMENTACAO_ROBO_COMISSOES.md`](sistema/DOCUMENTACAO_ROBO_COMISSOES.md) (seção "Cross-Selling")
- [`testes/CENARIOS_TESTE_EXPANDIDOS.md`](testes/CENARIOS_TESTE_EXPANDIDOS.md) (Bloco 3)

### FC de Fornecedores
- [`testes/CENARIOS_TESTE_EXPANDIDOS.md`](testes/CENARIOS_TESTE_EXPANDIDOS.md) (Bloco 4)

### Fator de Correção (FC)
- [`sistema/DOCUMENTACAO_ROBO_COMISSOES.md`](sistema/DOCUMENTACAO_ROBO_COMISSOES.md) (seção "Cálculo Do Fator De Correção")
- [`sistema/CORRECOES_FC_RENTABILIDADE.md`](sistema/CORRECOES_FC_RENTABILIDADE.md)

### Taxas de Câmbio
- [`sistema/REFATORACAO_TAXAS_CAMBIO.md`](sistema/REFATORACAO_TAXAS_CAMBIO.md)

---

## 🔍 BUSCAR POR PALAVRA-CHAVE

- **TCMP / FCMP**: `sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`
- **Reconciliação**: `sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`, `testes/GUIA_TESTES_RECONCILIACAO.md`
- **Adiantamento / COT**: `sistema/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`
- **Regras de Comissão**: `sistema/DOCUMENTACAO_ROBO_COMISSOES.md`
- **Metas**: `sistema/DOCUMENTACAO_ROBO_COMISSOES.md`, `sistema/CORRECOES_FC_RENTABILIDADE.md`
- **Validação**: `guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md`
- **Estrutura de Pastas**: `sistema/README_ESTRUTURA.md`

---

**Versão**: 1.0  
**Data**: 18/11/2025  
**Última Atualização**: 18/11/2025

