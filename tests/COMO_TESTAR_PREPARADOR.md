# Como Testar o Preparador de Dados

Este documento explica como verificar se o robô está lendo corretamente o arquivo `Analise_Comercial_Completa.xlsx` e gerando os arquivos de saída.

## Script de Validação

Foi criado o script `test_preparador_dados.py` que valida automaticamente todo o processo.

### Como Executar

```bash
# Testar com mês/ano atual (padrão)
python test_preparador_dados.py

# Testar com mês/ano específico
python test_preparador_dados.py 11 2025
```

### O que o Script Valida

O script executa 3 etapas de validação:

#### 1. Verificação do Arquivo de Entrada
- ✅ Verifica se `Analise_Comercial_Completa.xlsx` existe (na raiz ou em `dados_entrada/`)
- ✅ Tenta ler o arquivo e verifica se está acessível
- ✅ Valida se as colunas essenciais estão presentes:
  - `Processo`
  - `Dt Emissão`
  - `Valor Realizado`

#### 2. Execução do Preparador
- ✅ Copia o arquivo para a raiz (se necessário)
- ✅ Executa `preparar_dados_mensais.py`
- ✅ Verifica se o preparador executou sem erros críticos

#### 3. Validação dos Arquivos de Saída
Valida cada arquivo gerado:

**Faturados.xlsx**
- ✅ Arquivo existe e pode ser lido
- ✅ Contém colunas esperadas: `Processo`, `Dt Emissão`, `Valor Realizado`, `Código Produto`, `Consultor Interno`
- ⚠️ Pode estar vazio se não houver dados do mês/ano especificado

**Conversões.xlsx**
- ✅ Arquivo existe e pode ser lido
- ✅ Contém colunas esperadas: `Processo`, `Data Aceite`, `Valor Orçado`, `Valor Realizado`
- ⚠️ Pode estar vazio se não houver conversões no período

**Faturados_YTD.xlsx**
- ✅ Arquivo existe e pode ser lido
- ✅ Contém colunas esperadas: `Processo`, `Dt Emissão`, `Valor Realizado`, `Fabricante`
- ✅ Deve conter dados (YTD = Year To Date, acumulado do ano)

**Retencao_Clientes.xlsx**
- ✅ Arquivo existe e pode ser lido
- ✅ Contém colunas esperadas: `linha`, `clientes_mes_anterior`, `clientes_mes_atual`
- ✅ Deve conter dados (retenção por linha de negócio)

### Interpretação dos Resultados

#### ✅ Sucesso Total
```
[SUCESSO] TODAS AS VALIDAÇÕES PASSARAM!
```
Todos os arquivos foram gerados corretamente e têm a estrutura esperada.

#### ⚠️ Arquivos Vazios (Normal em alguns casos)
Se `Faturados.xlsx` ou `Conversões.xlsx` estiverem vazios, isso é **normal** se:
- Não houver dados faturados no mês/ano especificado
- Não houver conversões no período

O importante é que os arquivos foram **gerados** e têm a **estrutura correta**.

#### ❌ Erros
Se aparecer `[ERRO]` ou `[ATENÇÃO]`, verifique:
1. Se o arquivo `Analise_Comercial_Completa.xlsx` existe e está acessível
2. Se o arquivo contém dados válidos
3. Se as colunas esperadas estão presentes no arquivo de entrada

### Exemplo de Saída Esperada

```
============================================================
VALIDAÇÃO DO PREPARADOR DE DADOS
============================================================

Mês/Ano de apuração: 11/2025

============================================================
1. VERIFICANDO ARQUIVO DE ENTRADA
============================================================
[OK] Arquivo encontrado: dados_entrada/Analise_Comercial_Completa.xlsx
[OK] Arquivo lido com sucesso: 3 linhas (amostra)
[OK] Colunas encontradas: 19
[OK] Todas as colunas essenciais foram encontradas

============================================================
2. EXECUTANDO PREPARADOR DE DADOS (11/2025)
============================================================
[OK] Preparador executado com sucesso!

============================================================
3. VALIDANDO ARQUIVOS DE SAÍDA GERADOS
============================================================
[OK] Todos os arquivos foram validados com sucesso

============================================================
[SUCESSO] TODAS AS VALIDAÇÕES PASSARAM!
============================================================
```

### Validação Manual (Alternativa)

Se preferir validar manualmente:

1. **Verificar arquivo de entrada:**
   ```bash
   # Verificar se o arquivo existe
   dir Analise_Comercial_Completa.xlsx
   # ou
   dir dados_entrada\Analise_Comercial_Completa.xlsx
   ```

2. **Executar o preparador:**
   ```bash
   python preparar_dados_mensais.py
   ```

3. **Verificar arquivos gerados:**
   ```bash
   # Verificar se os arquivos foram criados
   dir Faturados.xlsx
   dir Conversões.xlsx
   dir Faturados_YTD.xlsx
   dir Retencao_Clientes.xlsx
   ```

4. **Abrir e inspecionar os arquivos:**
   - Abra cada arquivo no Excel
   - Verifique se as colunas esperadas estão presentes
   - Verifique se há dados (ou se está vazio por falta de dados do período)

### Troubleshooting

**Problema: "Arquivo não encontrado"**
- Verifique se `Analise_Comercial_Completa.xlsx` existe em `dados_entrada/` ou na raiz
- O script tentará copiar automaticamente de `dados_entrada/` para a raiz

**Problema: "Preparador retornou False"**
- Verifique os logs do preparador para identificar o erro específico
- Verifique se o arquivo de entrada está corrompido ou em formato incorreto

**Problema: "Arquivos de saída não gerados"**
- Verifique se há permissões de escrita no diretório
- Verifique se o preparador executou sem erros

### Próximos Passos

Após validar que o preparador está funcionando:
1. Execute o cálculo de comissões completo
2. Verifique os arquivos de saída do cálculo de comissões
3. Valide os resultados finais

