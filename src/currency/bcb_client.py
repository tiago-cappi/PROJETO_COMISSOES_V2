"""
Cliente para a API de Dados Abertos do Banco Central do Brasil (BCB).
Focado na obtenção de taxas de câmbio (PTAX) para cálculo de médias mensais.
"""

from __future__ import annotations

import requests
from datetime import date, datetime
from typing import List, Optional, Dict, Any

class BCBClient:
    """
    Cliente para interagir com a API OData do Banco Central do Brasil.
    Endpoint: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/
    """

    BASE_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
    
    # Mapeamento de códigos ISO para símbolos do BCB, se necessário.
    # Geralmente o BCB usa os mesmos códigos (USD, EUR, GBP).
    # Caso haja divergência, adicionar aqui.
    CURRENCY_MAP = {
        "USD": "USD",
        "EUR": "EUR",
        "GBP": "GBP",
        # Adicionar outras se necessário
    }

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def get_daily_rates(self, currency: str, start_date: date, end_date: date) -> List[float]:
        """
        Busca as taxas de venda diárias (PTAX fechamento) para o período.
        
        IMPORTANTE: 
        A API do BCB retorna a cotação em BRL (ex: 1 USD = 5.00 BRL).
        O sistema espera a taxa inversa (ex: 1 BRL = 0.20 USD).
        Este método já retorna as taxas INVERTIDAS (1 / cotacaoVenda).

        Args:
            currency: Código da moeda (ex: 'USD', 'EUR').
            start_date: Data inicial.
            end_date: Data final.

        Returns:
            Lista de taxas diárias (invertidas). Retorna lista vazia em caso de erro ou sem dados.
        """
        symbol = self.CURRENCY_MAP.get(currency.upper(), currency.upper())
        
        # Formato de data exigido pelo OData do BCB: 'MM-DD-YYYY'
        fmt_start = start_date.strftime("%m-%d-%Y")
        fmt_end = end_date.strftime("%m-%d-%Y")
        
        # URL OData
        # CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)
        endpoint = f"{self.BASE_URL}/CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
        
        params = {
            "@moeda": f"'{symbol}'",
            "@dataInicial": f"'{fmt_start}'",
            "@dataFinalCotacao": f"'{fmt_end}'",
            "$format": "json",
            "$select": "cotacaoVenda,dataHoraCotacao"
        }

        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            values = data.get("value", [])
            
            # Agrupar por data para pegar apenas o fechamento (última cotação do dia)
            daily_rates = {}
            
            for item in values:
                cotacao_venda = item.get("cotacaoVenda")
                data_hora = item.get("dataHoraCotacao")
                
                if cotacao_venda and cotacao_venda > 0 and data_hora:
                    # Extrair apenas a data (YYYY-MM-DD) da string dataHoraCotacao
                    # Formato esperado: 'YYYY-MM-DD HH:MM:SS.mmm'
                    date_str = data_hora.split(" ")[0]
                    
                    # Como a lista costuma vir ordenada, o último valor processado para o dia
                    # será o fechamento (ou o mais recente).
                    # Armazenamos o valor invertido.
                    daily_rates[date_str] = 1.0 / float(cotacao_venda)
            
            # Retornar apenas os valores dos fechamentos diários
            return list(daily_rates.values())

        except requests.RequestException as e:
            print(f"[BCB_API] Erro ao buscar taxas para {currency}: {e}")
            return []
        except Exception as e:
            print(f"[BCB_API] Erro inesperado: {e}")
            return []
