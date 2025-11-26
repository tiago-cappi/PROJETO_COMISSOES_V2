import pandas as pd
import os
import glob

# Encontrar arquivo de comissões calculadas
files = glob.glob("Comissoes_Calculadas_*.xlsx")
if files:
    path = sorted(files)[-1]  # Pegar o mais recente
    print(f"Arquivo encontrado: {path}")
    
    df = pd.read_excel(path)
    print(f"\nTotal de linhas: {len(df)}")
    print(f"Colunas: {df.columns.tolist()}")
    
    if 'observacao' in df.columns:
        cs = df[df['observacao'] == 'CROSS_SELLING']
        print(f"\nLinhas de Cross-Selling: {len(cs)}")
        if len(cs) > 0:
            print(f"Processos com CS: {cs['processo'].unique().tolist()}")
            print(f"Colaboradores CS: {cs['nome_colaborador'].unique().tolist()}")
            print(f"\nAmostra de dados CS:")
            print(cs[['processo', 'nome_colaborador', 'cargo', 'comissao_calculada', 'observacao']].head())
        else:
            print("PROBLEMA: Nenhuma linha de CROSS_SELLING encontrada!")
            print("\nVerificando coluna observacao:")
            print(df['observacao'].value_counts())
    else:
        print("ERRO: Coluna 'observacao' não existe no DataFrame!")
else:
    print("Nenhum arquivo Comissoes_Calculadas_*.xlsx encontrado!")
