"""
Script para gerar arquivos de rentabilidade simulada para testes.

Este script cria arquivos de rentabilidade com valores variados para testar
diferentes cenários de FC (Fator de Correção).

Arquivos gerados:
- dados_entrada/rentabilidades/rentabilidade_08_2025_agrupada.xlsx
- dados_entrada/rentabilidades/rentabilidade_09_2025_agrupada.xlsx
- dados_entrada/rentabilidades/rentabilidade_10_2025_agrupada.xlsx
"""

import pandas as pd
import os


def gerar_rentabilidade_teste():
    """
    Gera arquivos de rentabilidade simulada para os meses de teste.
    """

    print("=" * 80)
    print("GERADOR DE RENTABILIDADE SIMULADA PARA TESTES")
    print("=" * 80)
    print()

    # Criar diretório
    os.makedirs("dados_entrada/rentabilidades", exist_ok=True)

    # Definir rentabilidades por contexto (linha, grupo, subgrupo, tipo)
    # Valores variados para testar diferentes níveis de FC
    
    rentabilidades = [
        # SSO - Valores variados
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Falco", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 15.0},  # FC baixo
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Titan", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 25.0},  # FC alto
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Reposição", "rentabilidade_realizada_pct": 8.0},  # FC muito baixo
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Sensor", 
         "Tipo de Mercadoria": "Reposição", "rentabilidade_realizada_pct": 10.0},
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Filtro", 
         "Tipo de Mercadoria": "Insumo", "rentabilidade_realizada_pct": 12.0},
        
        {"linha": "SSO", "Grupo": "Analisador Portátil", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 22.0},  # FC bom
        {"linha": "SSO", "Grupo": "Analisador Portátil", "Subgrupo": "MicroClip", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 20.0},
        
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Calibração", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 30.0},  # FC = 1.0 ou próximo
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Hora Técnica", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 28.0},
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 18.0},
        
        # Hidrologia - Valores variados
        {"linha": "Hidrologia", "Grupo": "Amostrador Diversos", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 17.0},
        {"linha": "Hidrologia", "Grupo": "Amostrador Não Refrigerado Portátil", "Subgrupo": "Amostrador", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 19.0},
        {"linha": "Hidrologia", "Grupo": "Analisador Microbiologico", "Subgrupo": "GeneCount", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 16.0},
        {"linha": "Hidrologia", "Grupo": "Sonda Diversos", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 14.0},
        {"linha": "Hidrologia", "Grupo": "Calibração Diversos", "Subgrupo": "Solução", 
         "Tipo de Mercadoria": "Insumo", "rentabilidade_realizada_pct": 13.0},
        
        # Remediação
        {"linha": "Remediação", "Grupo": "Bomba Diversos", "Subgrupo": "Bomba", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 18.0},
        {"linha": "Remediação", "Grupo": "Bomba Fixa", "Subgrupo": "Sistema", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 20.0},
        
        # Diversos
        {"linha": "Diversos", "Grupo": "Detector Diversos", "Subgrupo": "Certificado", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 27.0},
        {"linha": "Diversos", "Grupo": "Diversos Diversos", "Subgrupo": "Calibração", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 29.0},
        
        # Locação
        {"linha": "Locação", "Grupo": "Locação Diversos", "Subgrupo": "Locação", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 26.0},
        
        # Saneamento
        {"linha": "Saneamento", "Grupo": "Estação Diversos", "Subgrupo": "Sistema", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 21.0},
    ]

    # Criar DataFrame
    df_rentabilidade = pd.DataFrame(rentabilidades)

    # Gerar para os 3 meses
    meses = [
        ("08", "2025"),
        ("09", "2025"),
        ("10", "2025"),
    ]

    for mes, ano in meses:
        arquivo = f"dados_entrada/rentabilidades/rentabilidade_{mes}_{ano}_agrupada.xlsx"
        
        try:
            df_rentabilidade.to_excel(arquivo, index=False, sheet_name="Rentabilidade")
            print(f"✅ Criado: {arquivo}")
        except Exception as e:
            print(f"❌ Erro ao criar {arquivo}: {e}")

    print()
    print("=" * 80)
    print("✅ ARQUIVOS DE RENTABILIDADE GERADOS COM SUCESSO!")
    print("=" * 80)
    print()
    print(f"📊 Total de combinações de rentabilidade: {len(rentabilidades)}")
    print()
    print("💡 VALORES DE RENTABILIDADE:")
    print("   - Reposição: 8-10% (FC muito baixo)")
    print("   - Produto (baixa): 12-17% (FC baixo)")
    print("   - Produto (média): 18-22% (FC médio)")
    print("   - Produto (alta): 23-25% (FC alto)")
    print("   - Serviço: 26-30% (FC próximo de 1.0)")
    print()
    print("🎯 Os valores são calculados considerando:")
    print("   - Meta padrão de rentabilidade: ~17%")
    print("   - Peso da rentabilidade: 20% (Gerente Linha)")
    print("   - Cap de FC: 1.0")
    print()


if __name__ == "__main__":
    gerar_rentabilidade_teste()

