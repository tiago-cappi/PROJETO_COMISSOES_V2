import pandas as pd
import sys

# Ler o Excel mais recente
xlsx = "Comissoes_Calculadas_20251126_174124.xlsx"
df = pd.read_excel(xlsx)

print(f"Total de linhas: {len(df)}")
print(f"\nColaboradores com comissão > 0:")
print(df[df['comissao_calculada'] > 0][['nome_colaborador', 'cargo', 'comissao_calculada']].groupby(['nome_colaborador', 'cargo']).sum())

print(f"\nConsultores Externos:")
externos = df[df['cargo'].str.contains('Externo', na=False)]
print(f"Total de linhas: {len(externos)}")
if len(externos) > 0:
    print(externos[['nome_colaborador', 'processo', 'comissao_calculada', 'observacao']].head(20))

print(f"\nLinhas com observacao preenchida:")
obs_preenchidas = df[df['observacao'].notna() & (df['observacao'] != '')]
print(f"Total: {len(obs_preenchidas)}")
if len(obs_preenchidas) > 0:
    print(obs_preenchidas[['nome_colaborador', 'processo', 'observacao']].head())

print(f"\nProcessos 400xxx:")
procs_400 = df[df['processo'].astype(str).str.startswith('400', na=False)]
print(f"Total: {len(procs_400)}")
if len(procs_400) > 0:
    print(procs_400[['nome_colaborador', 'processo', 'comissao_calculada', 'observacao']].head(20))
