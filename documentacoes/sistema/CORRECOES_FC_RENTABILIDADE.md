# Correções no Cálculo do FC de Rentabilidade

## Problema Identificado

O cálculo do Fator de Correção (FC) de rentabilidade não estava funcionando corretamente devido a problemas de correspondência de chaves entre:
- Os dados de rentabilidade realizada (carregados em `_calcular_realizado`)
- As metas de rentabilidade (buscadas em `_get_meta`)
- A busca do realizado durante o cálculo do FC (em `_calcular_fc_para_item`)

## Correções Implementadas

### 1. Normalização de Valores no Carregamento de Rentabilidade Realizada

**Arquivo:** `calculo_comissoes.py` (linhas 645-653)

**Mudança:**
- Adicionada normalização dos valores das colunas de índice antes de criar a Series
- Garante que todos os valores sejam strings normalizadas (sem espaços extras, tipos consistentes)

```python
# NOVO: Garantir que valores de índice sejam strings normalizadas para correspondência exata
if not rent_realizada.empty:
    # Normalizar valores das colunas de índice para garantir correspondência
    for col in ["linha", "Grupo", "Subgrupo", "Tipo de Mercadoria"]:
        if col in rent_realizada.columns:
            rent_realizada[col] = rent_realizada[col].astype(str).str.strip()
```

### 2. Normalização da Chave na Busca do Realizado

**Arquivo:** `calculo_comissoes.py` (linhas 828-961)

**Mudanças:**
- Normalização da chave de busca antes de consultar a Series de rentabilidade
- Fallback para chave original se a normalizada não encontrar
- Logs detalhados de debug para rastrear problemas

```python
# NOVO: Normalizar chave de rentabilidade para garantir correspondência exata
chave_normalizada = tuple(
    str(v).strip() if v is not None and not pd.isna(v) else ""
    for v in chave_busca
)

# Tentar busca com chave normalizada
realizado = self.realizado[realizado_key].get(chave_normalizada, None)

# Se não encontrou, tentar com chave original (fallback)
if realizado is None or ...:
    realizado = self.realizado[realizado_key].get(chave_busca, 0)
```

### 3. Normalização na Busca de Meta de Rentabilidade

**Arquivo:** `calculo_comissoes.py` (linhas 677-728)

**Mudanças:**
- Normalização dos valores da chave antes de buscar no DataFrame de metas
- Busca com normalização primeiro, fallback para busca original
- Logs detalhados de debug

```python
# NOVO: Normalizar valores da chave para garantir correspondência exata
linha_norm = str(linha).strip() if linha is not None and not pd.isna(linha) else ""
grupo_norm = str(grupo).strip() if grupo is not None and not pd.isna(grupo) else ""
# ... (similar para subgrupo e tipo_mercadoria)

# Buscar com valores normalizados
filtro = (
    (df["linha"].astype(str).str.strip() == linha_norm)
    & (df["grupo"].astype(str).str.strip() == grupo_norm)
    # ... (similar para outras colunas)
)
```

### 4. Logs de Debug Detalhados

**Arquivo:** `calculo_comissoes.py` (múltiplas localizações)

**Mudanças:**
- Adicionada flag `DEBUG_RENTABILIDADE` (variável de ambiente)
- Logs detalhados em todas as etapas do cálculo de FC de rentabilidade:
  - Busca do realizado
  - Busca da meta
  - Cálculo do atingimento
  - Cálculo do componente FC

**Como ativar:**
```bash
# Ativar logs de debug de rentabilidade
set DEBUG_RENTABILIDADE=1
python calculo_comissoes.py

# Ou ativar logs verbosos gerais
set COMISSOES_VERBOSE=1
python calculo_comissoes.py
```

### 5. Tratamento de Erros Melhorado

**Arquivo:** `calculo_comissoes.py` (linhas 729-750)

**Mudanças:**
- Logs mais detalhados quando meta não é encontrada
- Captura de exceções genéricas além de IndexError/KeyError
- Contexto adicional nos logs de validação

## Impacto das Correções

### Antes:
- Chaves não correspondiam devido a diferenças de tipo, espaços extras, ou normalização inconsistente
- Rentabilidade realizada retornava 0 mesmo quando dados existiam
- Metas não eram encontradas mesmo quando existiam no arquivo

### Depois:
- Normalização consistente garante correspondência exata
- Fallback para busca original mantém compatibilidade
- Logs detalhados permitem identificar problemas rapidamente

## Como Testar

1. **Executar o cálculo normalmente:**
   ```bash
   python calculo_comissoes.py
   ```

2. **Com logs de debug de rentabilidade:**
   ```bash
   set DEBUG_RENTABILIDADE=1
   python calculo_comissoes.py
   ```

3. **Verificar o arquivo de saída:**
   - Abrir `Comissoes_Calculadas_*.xlsx`
   - Verificar aba `COMISSOES_CALCULADAS`
   - Verificar se há valores de FC de rentabilidade > 0 para colaboradores com peso na meta

4. **Verificar logs de validação:**
   - Procurar por avisos relacionados a rentabilidade
   - Verificar se há mensagens de "Rentabilidade não encontrada" ou "Meta de rentabilidade é None"

## Notas Importantes

- **Não altera a lógica de cálculo existente:** Apenas corrige a correspondência de chaves
- **Mantém compatibilidade:** Fallback para busca original garante que não quebra código existente
- **Logs opcionais:** Logs de debug só aparecem se `DEBUG_RENTABILIDADE=1` ou `COMISSOES_VERBOSE=1`
- **Performance:** Normalização adiciona overhead mínimo, mas garante correção

## Próximos Passos

Após executar o cálculo:
1. Verificar se o FC de rentabilidade está sendo calculado corretamente
2. Se ainda houver problemas, verificar os logs de debug para identificar a causa
3. Comparar com o diagnóstico executado anteriormente (`diagnostics/diagnostico_rentabilidade.py`)

