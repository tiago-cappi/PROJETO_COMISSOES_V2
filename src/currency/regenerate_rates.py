"""
Script utilitário para REGENERAR completamente o histórico de taxas de câmbio.

Objetivo:
1. Limpar/Ignorar o cache atual.
2. Buscar taxas oficiais do BCB para todas as moedas e meses relevantes.
3. Gerar um novo arquivo JSON limpo e confiável.

Uso:
    python src/currency/regenerate_rates.py
"""

import sys
import os
import json
from datetime import date, datetime
import time

# Adicionar raiz ao path para imports funcionarem
sys.path.append(os.getcwd())

from src.currency.rate_fetcher import RateFetcher
from src.currency.rate_storage import RateStorage

# Configuração do range de regeneração
# Apenas o ano corrente, conforme solicitado
ano_atual = date.today().year
ANOS_PARA_PROCESSAR = [ano_atual]
MOEDAS_PARA_PROCESSAR = ["USD", "EUR", "GBP"]

def regenerate_all():
    print("=== INICIANDO REGENERAÇÃO DE TAXAS DE CÂMBIO (FONTE: BCB) ===")
    
    # 1. Inicializar Storage (apontando para o arquivo padrão)
    storage = RateStorage()
    
    # Opcional: Fazer backup do arquivo antigo antes de sobrescrever?
    # Por enquanto, vamos apenas carregar e atualizar, ou podemos limpar "taxas".
    # Vamos limpar a seção "taxas" para garantir que não sobre lixo antigo.
    print("Limpar dados antigos em memória...")
    storage._load() # Garante que carregou
    storage._data["taxas"] = {} # Limpa tudo
    
    # 2. Inicializar Fetcher
    fetcher = RateFetcher(timeout=30.0, max_retries=3)
    
    total_sucesso = 0
    total_falha = 0
    
    # 3. Loop de processamento
    for ano in ANOS_PARA_PROCESSAR:
        # Garantir estrutura do ano
        if str(ano) not in storage._data["taxas"]:
            storage._data["taxas"][str(ano)] = {}
            
        for moeda in MOEDAS_PARA_PROCESSAR:
            # Garantir estrutura da moeda
            if moeda not in storage._data["taxas"][str(ano)]:
                storage._data["taxas"][str(ano)][moeda] = {}
            
            # Definir até que mês processar
            # Se for ano atual, vai até o mês atual. Se for passado, vai até 12.
            hoje = date.today()
            mes_limite = 12
            if ano == hoje.year:
                mes_limite = hoje.month
            elif ano > hoje.year:
                continue # Futuro não processa
                
            print(f"\nProcessando {moeda} - {ano} (Meses 1 a {mes_limite})...")
            
            for mes in range(1, mes_limite + 1):
                print(f"  > Buscando {moeda} {mes:02d}/{ano}...", end=" ", flush=True)
                
                # Tentar buscar no BCB
                resultado = fetcher.buscar_taxa_media_mensal(moeda, ano, mes)
                
                if resultado:
                    taxa, fonte, dias = resultado
                    print(f"OK! Taxa: {taxa:.6f} ({dias} dias)")
                    
                    # Salvar no storage
                    storage.salvar_taxa(
                        moeda=moeda,
                        ano=ano,
                        mes=mes,
                        taxa_media=taxa,
                        fonte=fonte,
                        dias_utilizados=dias,
                        fallback=False
                    )
                    total_sucesso += 1
                else:
                    print("FALHA/SEM DADOS.")
                    total_falha += 1
                
                # Pequeno delay para não bombardear a API (embora BCB aguente bem)
                time.sleep(0.2)

    # 4. Persistir no disco
    # O método salvar_taxa já persiste a cada chamada.
    print("\nSalvar alterações no disco... (Já realizado incrementalmente)")
    # storage.salvar_arquivo()
    
    print(f"\n=== CONCLUÍDO ===")
    print(f"Taxas atualizadas: {total_sucesso}")
    print(f"Falhas/Ausentes: {total_falha}")
    print(f"Arquivo: {storage.json_path}")

if __name__ == "__main__":
    regenerate_all()
