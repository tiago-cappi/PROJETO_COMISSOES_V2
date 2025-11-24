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
    # Meta de rentabilidade agora é 50% - valores variados para testar diferentes níveis de FC
    # FC muito baixo (< 0.5): ~25% de rentabilidade
    # FC baixo (0.6-0.7): ~30-35% de rentabilidade
    # FC médio (0.8-0.9): ~40-45% de rentabilidade
    # FC alto (0.95-0.99): ~47-49% de rentabilidade
    # FC = 1.0: ~50% de rentabilidade
    
    rentabilidades = [
        # SSO - Valores variados de 25% a 50%
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Falco", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 30.0},  # FC baixo
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Titan", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 45.0},  # FC alto
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Reposição", "rentabilidade_realizada_pct": 25.0},  # FC muito baixo
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Sensor", 
         "Tipo de Mercadoria": "Reposição", "rentabilidade_realizada_pct": 27.0},  # FC muito baixo
        {"linha": "SSO", "Grupo": "Analisador Fixo", "Subgrupo": "Filtro", 
         "Tipo de Mercadoria": "Insumo", "rentabilidade_realizada_pct": 32.0},  # FC baixo
        
        {"linha": "SSO", "Grupo": "Analisador Portátil", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 42.0},  # FC bom
        {"linha": "SSO", "Grupo": "Analisador Portátil", "Subgrupo": "MicroClip", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 40.0},  # FC médio
        {"linha": "SSO", "Grupo": "Analisador Portátil", "Subgrupo": "Panther", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 43.0},  # FC bom
        {"linha": "SSO", "Grupo": "Analisador Portátil", "Subgrupo": "Innova", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 41.0},  # FC médio
        
        {"linha": "SSO", "Grupo": "Detector Portátil", "Subgrupo": "MicroClip", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 38.0},  # FC médio
        {"linha": "SSO", "Grupo": "Detector Fixo", "Subgrupo": "E3 Point", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 39.0},  # FC médio
        
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Calibração", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 50.0},  # FC = 1.0
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Hora Técnica", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 48.0},  # FC alto
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Instalação", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 47.0},  # FC alto
        {"linha": "SSO", "Grupo": "Diversos Diversos", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 36.0},  # FC baixo-médio
        
        # Hidrologia - Valores variados de 28% a 48%
        {"linha": "Hidrologia", "Grupo": "Amostrador Diversos", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 35.0},  # FC baixo
        {"linha": "Hidrologia", "Grupo": "Amostrador Não Refrigerado Portátil", "Subgrupo": "Amostrador", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 38.0},  # FC médio
        {"linha": "Hidrologia", "Grupo": "Analisador Microbiologico", "Subgrupo": "GeneCount", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 34.0},  # FC baixo
        {"linha": "Hidrologia", "Grupo": "Equipamento Amostragem", "Subgrupo": "ISCO", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 40.0},  # FC médio
        {"linha": "Hidrologia", "Grupo": "Equipamento Amostragem", "Subgrupo": "YSI", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 42.0},  # FC bom
        {"linha": "Hidrologia", "Grupo": "Sonda Multiparâmetros", "Subgrupo": "EXO", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 44.0},  # FC bom
        {"linha": "Hidrologia", "Grupo": "Sonda Multiparâmetros", "Subgrupo": "YSI", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 43.0},  # FC bom
        {"linha": "Hidrologia", "Grupo": "Sonda Diversos", "Subgrupo": "Acessório", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 33.0},  # FC baixo
        {"linha": "Hidrologia", "Grupo": "Calibração Diversos", "Subgrupo": "Solução", 
         "Tipo de Mercadoria": "Insumo", "rentabilidade_realizada_pct": 31.0},  # FC baixo
        {"linha": "Hidrologia", "Grupo": "Fotometro Portátil", "Subgrupo": "9500", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 37.0},  # FC médio
        {"linha": "Hidrologia", "Grupo": "Medidor de Vazão Fixo", "Subgrupo": "IQ Standard", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 39.0},  # FC médio
        {"linha": "Hidrologia", "Grupo": "Medidor de Vazão Fixo", "Subgrupo": "IQ PLUS", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 41.0},  # FC médio-bom
        
        # Remediação - Valores de 36% a 46%
        {"linha": "Remediação", "Grupo": "Bomba Diversos", "Subgrupo": "Bomba", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 38.0},  # FC médio
        {"linha": "Remediação", "Grupo": "Bomba Fixa", "Subgrupo": "Sistema", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 40.0},  # FC médio
        {"linha": "Remediação", "Grupo": "Sistema Remediação", "Subgrupo": "QED", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 42.0},  # FC bom
        {"linha": "Remediação", "Grupo": "Sistema Remediação", "Subgrupo": "Thermo", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 44.0},  # FC bom
        
        # Diversos - Valores de 45% a 49%
        {"linha": "Diversos", "Grupo": "Detector Diversos", "Subgrupo": "Certificado", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 47.0},  # FC alto
        {"linha": "Diversos", "Grupo": "Diversos Diversos", "Subgrupo": "Calibração", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 49.0},  # FC muito alto
        {"linha": "Diversos", "Grupo": "Diversos Diversos", "Subgrupo": "Instalação", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 48.0},  # FC alto
        {"linha": "Diversos", "Grupo": "Diversos Diversos", "Subgrupo": "Treinamento", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 46.0},  # FC alto
        
        # Locação - Valor médio
        {"linha": "Locação", "Grupo": "Locação Diversos", "Subgrupo": "Locação", 
         "Tipo de Mercadoria": "Serviço", "rentabilidade_realizada_pct": 45.0},  # FC alto
        
        # Saneamento - Valor bom
        {"linha": "Saneamento", "Grupo": "Estação Diversos", "Subgrupo": "Sistema", 
         "Tipo de Mercadoria": "Produto", "rentabilidade_realizada_pct": 41.0},  # FC médio-bom
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
    print("==" * 80)
    print("✅ ARQUIVOS DE RENTABILIDADE GERADOS COM SUCESSO!")
    print("=" * 80)
    print()
    print(f"📊 Total de combinações de rentabilidade: {len(rentabilidades)}")
    print()
    print("💡 VALORES DE RENTABILIDADE (Meta: 50%):")
    print("   - Reposição: 25-27% (FC muito baixo < 0.5)")
    print("   - Produto (baixa): 30-35% (FC baixo 0.6-0.7)")
    print("   - Produto (média): 36-42% (FC médio 0.8-0.9)")
    print("   - Produto (alta): 43-45% (FC alto 0.9-0.99)")
    print("   - Serviço: 46-50% (FC muito alto 0.95-1.0)")
    print()
    print("🎯 Os valores são calculados considerando:")
    print("   - Meta padrão de rentabilidade: 50%")
    print("   - Distribuição: 25% a 50% para testar todos os níveis de FC")
    print("   - Cap de FC: 1.0")
    print()


if __name__ == "__main__":
    gerar_rentabilidade_teste()

