# Refatoração: Gerenciamento de Taxas de Câmbio

## Problema Identificado

A busca de taxas de câmbio estava travando o cálculo de comissões durante a Etapa 5. O problema ocorria porque:

1. **Busca durante o loop**: As taxas eram buscadas DURANTE o processamento de cada item, causando travamentos quando as APIs estavam lentas
2. **Múltiplas requisições repetidas**: Para cada item com fornecedor, eram feitas requisições HTTP que poderiam demorar vários segundos
3. **Timeout longo**: Timeout de 12 segundos com 3 tentativas causava esperas muito longas
4. **Sem cache persistente**: Taxas eram buscadas novamente a cada execução, mesmo que já tivessem sido obtidas anteriormente

## Nova Abordagem Implementada

### 1. Módulo Separado: `src/core/currency_rates.py`

A lógica de busca de taxas foi **completamente removida** de `calculo_comissoes.py` e movida para um módulo dedicado:

- **Classe `CurrencyRateManager`**: Gerencia todas as operações de busca e cache
- **Cache persistente**: Salva taxas em arquivo JSON (`cache_taxas_cambio.json`) para evitar buscas repetidas
- **Cache em memória**: Mantém taxas em memória durante a execução para acesso rápido

### 2. Pré-carregamento Otimizado

**ANTES (problema):**
```python
# Durante o loop de itens (lento e pode travar)
for item in itens:
    taxas = self._get_taxas_de_cambio(ano, mes, moedas)  # Busca HTTP aqui!
    # ... cálculo com taxas
```

**AGORA (otimizado):**
```python
# ANTES do loop (uma vez só, rápido)
todas_moedas = identificar_moedas_necessarias()  # Analisa METAS_FORNECEDORES
taxas_precarregadas = currency_manager.preload_all_rates(ano, mes, todas_moedas)

# Durante o loop (apenas leitura do cache)
for item in itens:
    taxas = extrair_do_cache_precarregado(moedas_necessarias)  # Instantâneo!
    # ... cálculo com taxas
```

### 3. Otimizações de Performance

#### Timeout Reduzido
- **Antes**: 12 segundos por requisição
- **Agora**: 5 segundos por requisição
- **Benefício**: Falhas são detectadas mais rapidamente

#### Menos Tentativas
- **Antes**: 3 tentativas com backoff exponencial (pode demorar 12s + 24s + 48s = 84s)
- **Agora**: 2 tentativas com backoff curto (máximo ~10s)
- **Benefício**: Fallback mais rápido entre APIs

#### Cache Persistente
- **Arquivo**: `cache_taxas_cambio.json`
- **Formato**: `{ano_mes_moedas: {moeda: {mes: taxa}}}`
- **Benefício**: Taxas já buscadas não precisam ser buscadas novamente

#### Cache em Memória
- Durante a execução, taxas ficam em `self.taxas_precarregadas`
- Acesso instantâneo durante o loop de itens
- **Benefício**: Zero latência durante o cálculo

### 4. Estratégia de Busca (Mantida, mas Otimizada)

A ordem de tentativas foi mantida, mas com timeouts menores:

1. **exchangerate.host/timeseries** (média mensal - mais preciso)
   - Timeout: 5s
   - Tentativas: 2
   - Backoff: 0.5s, 1.0s

2. **frankfurter.app** (dia 15 do mês - fallback rápido)
   - Timeout: 5s
   - Tentativas: 2
   - Backoff: 0.3s, 0.6s

3. **exchangerate.host/convert** (dia 15 do mês - último recurso)
   - Timeout: 5s
   - Tentativas: 2
   - Backoff: 0.3s, 0.6s

### 5. Fluxo de Execução

```
┌─────────────────────────────────────────────────────────┐
│ 1. Início da Etapa 5                                    │
│    - Carrega dados (FATURADOS, ATRIBUICOES, etc.)       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Identificar Moedas Necessárias                       │
│    - Analisa METAS_FORNECEDORES                         │
│    - Extrai todas as moedas únicas                      │
│    - Exemplo: {USD, EUR, GBP}                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Pré-carregar Taxas (UMA VEZ)                         │
│    - Verifica cache persistente (arquivo JSON)          │
│    - Se não encontrado, busca todas as taxas            │
│    - Salva no cache persistente                         │
│    - Armazena em self.taxas_precarregadas               │
│    - Tempo: ~10-30s (dependendo de moedas/meses)        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Loop de Itens (RÁPIDO)                               │
│    for item in itens:                                   │
│      - Identifica moedas do item                        │
│      - Extrai taxas do cache pré-carregado (instantâneo) │
│      - Calcula FC com taxas                             │
│      - Nenhuma requisição HTTP aqui!                    │
└─────────────────────────────────────────────────────────┘
```

## Benefícios da Nova Abordagem

### Performance
- ✅ **Elimina travamentos**: Taxas são buscadas ANTES do loop, não durante
- ✅ **Cache persistente**: Taxas não precisam ser buscadas novamente em execuções futuras
- ✅ **Acesso instantâneo**: Durante o loop, taxas vêm do cache em memória (0ms)

### Manutenibilidade
- ✅ **Código separado**: Lógica de câmbio isolada em `src/core/currency_rates.py`
- ✅ **Fácil de testar**: Módulo pode ser testado independentemente
- ✅ **Fácil de modificar**: Mudanças na lógica de busca não afetam o cálculo principal

### Robustez
- ✅ **Fallback rápido**: Se uma API falhar, tenta a próxima imediatamente
- ✅ **Timeout reduzido**: Falhas são detectadas rapidamente
- ✅ **Logs detalhados**: Identifica exatamente onde está travando

## Estrutura de Arquivos

```
PROJETO_COMISSOES_V2/
├── src/
│   └── core/
│       └── currency_rates.py    ← NOVO: Lógica de taxas de câmbio
├── calculo_comissoes.py         ← MODIFICADO: Usa CurrencyRateManager
└── cache_taxas_cambio.json      ← NOVO: Cache persistente (gerado automaticamente)
```

## Como Funciona o Cache Persistente

O arquivo `cache_taxas_cambio.json` armazena taxas no formato:

```json
{
  "2025_9_USD_EUR_GBP": {
    "USD": {
      "1": 0.201234,
      "2": 0.201456,
      ...
      "9": 0.202345
    },
    "EUR": {
      "1": 0.185123,
      ...
    }
  }
}
```

**Chave do cache**: `{ano}_{mes_final}_{moedas_ordenadas}`

**Benefício**: Se você executar o cálculo novamente para o mesmo mês/ano, as taxas serão carregadas do arquivo instantaneamente (sem requisições HTTP).

## Logs de Depuração

A nova implementação gera logs detalhados:

```
[Etapa 5.4.1] Pré-carregando taxas de câmbio para 2 moeda(s): ['GBP', 'USD'] (2025, mês 1-9)
[TAXAS_CAMBIO] Buscando taxas para 2 moeda(s): ['GBP', 'USD'] (2025, mês 1-9)
[TAXAS_CAMBIO] Progresso busca taxas: 9/18 (50%) em 5.2s
[TAXAS_CAMBIO] Busca concluída: 18/18 taxas obtidas (0 faltando) em 12.45s
[Etapa 5.4.1] Pré-carregamento concluído em 12.45s
```

Se alguma taxa não for encontrada:
```
[TAXAS_CAMBIO] AVISO: Falha após 5.1s para USD mês 5: Connection timeout
[TAXAS_CAMBIO] Busca concluída: 17/18 taxas obtidas (1 faltando) em 15.23s
```

## Compatibilidade

- ✅ **Mantém funcionalidade**: O cálculo continua funcionando exatamente como antes
- ✅ **Mesma precisão**: Taxas são calculadas da mesma forma (média mensal)
- ✅ **Mesma lógica de fallback**: Se uma API falhar, tenta as outras

## Próximos Passos (Opcional)

Para melhorias futuras, você pode considerar:

1. **Cache com TTL**: Invalidar cache após X dias (ex: 30 dias)
2. **Busca paralela**: Usar threading para buscar múltiplas moedas simultaneamente
3. **API alternativa**: Adicionar mais fontes de taxas como fallback
4. **Validação de taxas**: Verificar se taxas estão dentro de limites razoáveis

## Teste

Para testar a nova implementação:

```bash
python calculo_comissoes.py
```

Você verá logs como:
```
[Etapa 5.4.1] Pré-carregando taxas de câmbio para 2 moeda(s): ['GBP', 'USD']
[TAXAS_CAMBIO] Buscando taxas para 2 moeda(s): ['GBP', 'USD'] (2025, mês 1-9)
[TAXAS_CAMBIO] Busca concluída: 18/18 taxas obtidas em 12.45s
[Etapa 5.4.1] Pré-carregamento concluído em 12.45s
[Etapa 5.4] Iniciando processamento de 3 itens...
```

Na segunda execução (com cache):
```
[Etapa 5.4.1] Pré-carregando taxas de câmbio para 2 moeda(s): ['GBP', 'USD']
[TAXAS_CAMBIO] Cache persistente hit: ['GBP', 'USD'] (2025, mês 9)
[Etapa 5.4.1] Pré-carregamento concluído em 0.01s  ← MUITO MAIS RÁPIDO!
```

