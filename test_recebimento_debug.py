"""
Script de debug para testar o carregamento dos arquivos de entrada do recebimento.
"""
import pandas as pd
import os
from pathlib import Path

print("=" * 80)
print("DEBUG: Testando carregamento de arquivos de recebimento para 08/2025")
print("=" * 80)

mes = 8
ano = 2025

# 1. Testar Análise Financeira
print("\n### 1. ANÁLISE FINANCEIRA ###")
path_entrada = os.path.join("dados_entrada", "Análise Financeira.xlsx")
print(f"Procurando: {repr(path_entrada)}")
print(f"Existe? {os.path.exists(path_entrada)}")

if os.path.exists(path_entrada):
    df = pd.read_excel(path_entrada)
    print(f"✓ Arquivo carregado: {len(df)} linhas")
    print(f"Colunas: {list(df.columns)}")
    
    # Filtrar por Tipo de Baixa == 'B'
    df_filtrado = df[df["Tipo de Baixa"].astype(str).str.strip().str.upper() == "B"]
    print(f"✓ Após filtro Tipo de Baixa=='B': {len(df_filtrado)} linhas")
    
    # Converter Data de Baixa para datetime
    df_filtrado["Data de Baixa"] = pd.to_datetime(df_filtrado["Data de Baixa"], errors='coerce')
    
    # Filtrar por mês/ano
    mask_mes = df_filtrado["Data de Baixa"].dt.month == mes
    mask_ano = df_filtrado["Data de Baixa"].dt.year == ano
    df_filtrado = df_filtrado[mask_mes & mask_ano]
    print(f"✓ Após filtro mês/ano {mes}/{ano}: {len(df_filtrado)} linhas")
    
    if len(df_filtrado) > 0:
        print(f"\nDocumentos encontrados para 08/2025:")
        for idx, row in df_filtrado.iterrows():
            print(f"  - {row['Documento']}: R$ {row['Valor Líquido']:.2f} em {row['Data de Baixa']}")
    else:
        print(f"❌ PROBLEMA: Nenhuma linha encontrada para {mes}/{ano}!")
        print(f"\n  Análise das datas no arquivo:")
        df["Data de Baixa"] = pd.to_datetime(df["Data de Baixa"], errors='coerce')
        datas_unicas = df["Data de Baixa"].dt.to_period('M').value_counts().sort_index()
        print(f"  Meses disponíveis:")
        for periodo, qtd in datas_unicas.items():
            print(f"    {periodo}: {qtd} linhas")
else:
    print(f"❌ ERRO: Arquivo não encontrado!")

# 2. Testar Análise Comercial Completa
print("\n### 2. ANÁLISE COMERCIAL COMPLETA ###")
path_comercial = os.path.join("dados_entrada", "Analise_Comercial_Completa.xlsx")
print(f"Procurando: {repr(path_comercial)}")
print(f"Existe? {os.path.exists(path_comercial)}")

if os.path.exists(path_comercial):
    df_comercial = pd.read_excel(path_comercial, dtype=str)
    print(f"✓ Arquivo carregado: {len(df_comercial)} linhas")
    print(f"Colunas: {list(df_comercial.columns)}")
    
    if 'Processo' in df_comercial.columns:
        processos_unicos = df_comercial['Processo'].unique()
        print(f"✓ Processos únicos: {len(processos_unicos)}")
        print(f"  Processos: {sorted(processos_unicos)}")
    else:
        print(f"❌ PROBLEMA: Coluna 'Processo' não encontrada!")
else:
    print(f"❌ ERRO: Arquivo não encontrado!")

print("\n" + "=" * 80)
print("FIM DO DEBUG")
print("=" * 80)

