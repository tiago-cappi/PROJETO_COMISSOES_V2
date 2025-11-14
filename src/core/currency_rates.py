"""
ANTIGO módulo de gerenciamento de taxas de câmbio.

Este arquivo foi mantido apenas como "stub" vazio para compatibilidade
retroativa durante a migração. Toda a lógica real de câmbio agora está
centralizada em:

    - src/currency/rate_fetcher.py
    - src/currency/rate_storage.py
    - src/currency/rate_validator.py
    - src/currency/rate_calculator.py

e o JSON persistente:

    - data/currency_rates/monthly_avg_rates.json

Nenhuma parte do código de produção deve mais importar ou utilizar
`CurrencyRateManager`. Novas implementações devem usar o pacote
`src.currency` diretamente.
"""
