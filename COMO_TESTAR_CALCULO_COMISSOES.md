# Como Testar o Cálculo de Comissões por Faturamento

Este documento explica como testar se o cálculo de comissões por faturamento está funcionando corretamente item a item para cada processo.

## Status da Implementação

✅ **O código de cálculo de comissões por faturamento JÁ ESTÁ IMPLEMENTADO**

A função `_calcular_comissoes()` no arquivo `calculo_comissoes.py` já calcula as comissões item a item para cada processo. Esta função:

1. Itera sobre cada item em `FATURADOS`
2. Para cada item, identifica os colaboradores (gestão + operacional)
3. Calcula o Fator de Correção (FC) para cada colaborador
4. Calcula a comissão: `comissao_calculada = comissao_potencial_maxima * fator_correcao_fc`
5. Gera o DataFrame `comissoes_df` com todas as comissões calculadas

## Como Executar o Cálculo

### Passo 1: Preparar os Dados

Primeiro, certifique-se de que os arquivos de entrada estão prontos:

```bash
# Executar o preparador de dados
python test_preparador_dados.py 9 2025
```

Isso gerará:
- `Faturados.xlsx`
- `Conversões.xlsx`
- `Faturados_YTD.xlsx`
- `Retencao_Clientes.xlsx`

### Passo 2: Executar o Cálculo de Comissões

Execute o script principal:

```bash
python calculo_comissoes.py
```

O script irá:
1. Carregar todas as configurações e dados
2. Preparar os dados
3. **Calcular comissões por faturamento** (item a item)
4. Calcular comissões por recebimento
5. Gerar arquivo de saída: `Comissoes_09_2025.xlsx`

### Passo 3: Validar os Resultados

Após a execução, valide os resultados:

```bash
python test_validar_comissoes_faturamento.py 9 2025
```

Este script valida:
- ✅ Estrutura do arquivo de comissões gerado
- ✅ Presença de todas as colunas esperadas
- ✅ Fórmula de cálculo: `comissao_calculada = comissao_potencial_maxima * fator_correcao_fc`
- ✅ Cálculo item a item por processo
- ✅ Estatísticas gerais (processos, colaboradores, itens)

## O que o Teste Valida

### 1. Estrutura do Arquivo

O teste verifica se o arquivo `Comissoes_09_2025.xlsx` contém:
- Aba `COMISSOES_CALCULADAS` com as comissões calculadas
- Colunas essenciais:
  - `processo`: ID do processo
  - `cod_produto`: Código do produto/item
  - `nome_colaborador`: Nome do colaborador
  - `cargo`: Cargo do colaborador
  - `faturamento_item`: Valor faturado do item
  - `taxa_rateio_aplicada`: Taxa de rateio aplicada
  - `percentual_elegibilidade_pe`: Percentual de elegibilidade
  - `fator_correcao_fc`: Fator de correção calculado
  - `comissao_potencial_maxima`: Comissão potencial máxima
  - `comissao_calculada`: Comissão final calculada

### 2. Fórmula de Cálculo

O teste valida que para cada linha:
```
comissao_calculada = comissao_potencial_maxima × fator_correcao_fc
```

Com tolerância de R$ 0,01 para erros de arredondamento.

### 3. Cálculo Item a Item

O teste verifica que:
- Cada processo faturado tem comissões calculadas
- Cada item faturado tem pelo menos uma linha de comissão (se houver colaboradores atribuídos)
- Os valores estão consistentes entre `Faturados.xlsx` e `Comissoes_09_2025.xlsx`

## Exemplo de Saída Esperada

```
============================================================
VALIDAÇÃO DE CÁLCULO DE COMISSÕES POR FATURAMENTO
============================================================

Mês/Ano de apuração: 09/2025

============================================================
VALIDANDO ARQUIVO DE COMISSÕES GERADO
============================================================
[OK] Arquivo encontrado: Comissoes_09_2025.xlsx
[OK] Arquivo lido: 15 linhas, 25 colunas
[OK] Colunas encontradas: 10/10
[INFO] Processos únicos: 3
[INFO] Colaboradores únicos: 5
[INFO] Itens únicos: 3
[INFO] Total de comissões calculadas: R$ 1.234,56

============================================================
VALIDANDO CÁLCULO ITEM A ITEM POR PROCESSO
============================================================
[OK] Fórmula de cálculo validada: comissao_calculada = comissao_potencial_maxima * fator_correcao_fc

[OK] Processo PROC001:
    Itens faturados: 1
    Linhas de comissão: 3
    Colaboradores: 3

[OK] Processo PROC002:
    Itens faturados: 1
    Linhas de comissão: 2
    Colaboradores: 2

[INFO] Processos validados: 3
[INFO] Itens validados: 15

============================================================
[SUCESSO] TODAS AS VALIDAÇÕES PASSARAM!
============================================================
```

## Troubleshooting

### Problema: "Arquivo de comissões não encontrado"

**Solução:** Execute primeiro o cálculo de comissões:
```bash
python calculo_comissoes.py
```

### Problema: "Nenhuma comissão calculada"

**Possíveis causas:**
1. Não há colaboradores atribuídos aos processos/itens
2. Não há regras de comissão configuradas
3. Os itens não atendem aos critérios de cálculo

**Solução:** Verifique:
- Arquivo `config/REGRAS_COMISSOES.xlsx` (aba `ATRIBUICOES`)
- Arquivo `config/REGRAS_COMISSOES.xlsx` (aba `CONFIG_COMISSAO`)
- Se os colaboradores estão corretamente atribuídos

### Problema: "Erros na fórmula de cálculo"

**Solução:** Isso indica um bug no código. Verifique:
- Se o cálculo do FC está correto
- Se há problemas de arredondamento
- Se os valores estão sendo calculados corretamente

## Próximos Passos

Após validar que o cálculo está funcionando:
1. Execute o cálculo completo para o mês desejado
2. Revise os resultados no arquivo gerado
3. Compare com cálculos manuais (se necessário)
4. Valide os totais e somas por colaborador

## Nota Importante

O código de cálculo de comissões por faturamento **já está implementado** e faz parte do código monolítico atual. Durante a refatoração (conforme `PLANO_REFATORACAO.txt`), esta lógica será extraída para:
- `src/core/commission_calculator.py` (classe `CommissionCalculator`)
- `src/core/fc_calculator.py` (classe `FCCalculator`)

Mas a funcionalidade atual já está completa e funcionando.

