# Refatoração: Gerenciamento de Taxas de Câmbio

## Problema Identificado

A busca de taxas de câmbio estava travando o cálculo de comissões durante a Etapa 5. O problema ocorria porque:

1. **Busca durante o loop**: As taxas eram buscadas DURANTE o processamento de cada item, causando travamentos quando as APIs estavam lentas
2. **Múltiplas requisições repetidas**: Para cada item com fornecedor, eram feitas requisições HTTP que poderiam demorar vários segundos
3. **Timeout longo**: Timeout de 12 segundos com 3 tentativas causava esperas muito longas
4. **Sem cache persistente**: Taxas eram buscadas novamente a cada execução, mesmo que já tivessem sido obtidas anteriormente

## Nova Abordagem Implementada

### 1. Camada de Câmbio Centralizada: `src/currency/` + JSON persistente

A lógica de busca e armazenamento de taxas foi **completamente removida** de `calculo_comissoes.py` e do módulo antigo `src/core/currency_rates.py` e substituída por uma camada dedicada:

- **`src/currency/rate_fetcher.py` (`RateFetcher`)**: responsável por buscar taxas médias mensais nas APIs.
- **`src/currency/rate_storage.py` (`RateStorage`)**: gerencia o JSON persistente de câmbio em `data/currency_rates/monthly_avg_rates.json`.
- **`src/currency/rate_validator.py` (`RateValidator`)**: identifica (moeda, ano, mês) faltantes no JSON.
- **`src/currency/rate_calculator.py` (`RateCalculator`)**: usa o JSON para converter faturamento YTD em BRL para a moeda do fornecedor, sem fazer chamadas HTTP.

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

### 3. Estratégia de Busca e Timeouts

Hoje a busca de taxas é feita **somente na etapa de preparação do JSON**, antes de qualquer cálculo de comissão. Isso permite usar um timeout maior por requisição, já que esse passo acontece poucas vezes.

- **APIs utilizadas (em ordem de prioridade)**:
  1. `exchangerate.host/timeseries` — média mensal verdadeira (muitos dias).
  2. `frankfurter.app` — taxa do dia central do mês.
  3. `exchangerate.host/convert` — taxa do dia central do mês.

- **Timeout e tentativas (`RateFetcher`)**:
  - Timeout padrão: **60 segundos** por requisição.
  - Tentativas: **2** por API.

Como essa etapa é feita **antes do cálculo das comissões** e apenas para meses/moedas faltantes, é aceitável que a preparação leve alguns minutos se necessário, em troca de maior chance de obter as taxas de câmbio corretas.

### 4. JSON Persistente de Câmbio

- **Arquivo**: `data/currency_rates/monthly_avg_rates.json`
- **Formato** (simplificado):

```json
{
  "metadata": {
    "ultima_atualizacao": "2025-11-14T10:30:00",
    "ano_atual": 2025,
    "mes_atual": 11,
    "moedas_disponiveis": ["USD", "GBP"],
    "schema_version": 1
  },
  "taxas": {
    "2025": {
      "USD": {
        "1": {
          "taxa_media": 0.201234,
          "fonte": "exchangerate.host/timeseries",
          "dias_utilizados": 31,
          "data_atualizacao": "...",
          "fallback": false,
          "observacao": null
        }
      }
    }
  }
}
```

Quando não é possível buscar a taxa de um mês em nenhuma API, o sistema:

1. Calcula a **média simples das taxas do mesmo ano até o mês anterior**.
2. Grava essa média como `taxa_media` com:
   - `fallback = true`
   - `fonte = "fallback_media_anual"`
   - `observacao` explicando claramente que foi usada a média do ano até o mês anterior.

### 5. Fluxo de Execução (atualizado)

```
┌─────────────────────────────────────────────────────────┐
│ 0. Verificação Inicial de Câmbio                        │
│    - Lê `config/METAS_FORNECEDORES.csv`                 │
│    - Descobre moedas dos fornecedores (exceto BRL)      │
│    - Para o ano atual, meses 1..(mês_atual-1):          │
│      ├─ Verifica quais (moeda, mês) ainda não existem   │
│      │   no JSON                                        │
│      ├─ Busca taxas nas APIs para os faltantes          │
│      └─ Se falhar, usa média do ano até mês anterior    │
│         como fallback, anotando isso no JSON            │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Início da Etapa 5                                    │
│    - Carrega dados (FATURADOS, ATRIBUICOES, etc.)       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Cálculo de FC dos Fornecedores                       │
│    - Usa FATURADOS_YTD para calcular faturamento YTD    │
│      em BRL por fornecedor                              │
│    - Usa `RateCalculator` para converter para moeda     │
│      alvo usando SOMENTE o JSON persistente             │
│    - Nenhuma requisição HTTP durante o loop de itens    │
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

