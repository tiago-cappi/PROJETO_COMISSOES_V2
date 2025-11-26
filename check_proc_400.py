import pandas as pd

# Verificar processos 400xxx existentes
df = pd.read_csv('Analise_Comercial_Completa.csv')

proc_400 = df[df['Processo'].astype(str).str.startswith('400', na=False)]
processes = sorted(proc_400['Processo'].unique())

print(f"Processos 400xxx no CSV de entrada: {processes}")
print(f"Total de itens: {len(proc_400)}")

if len(proc_400) > 0:
    print("\nAmostra de dados 400xxx:")
    print(proc_400[['Processo', 'Gerente Comercial-Pedido', 'Negócio']].head().to_string())
else:
    print("\n❌ NENHUM processo 400xxx no CSV! Os dados de teste não foram gerados para Cross-Selling.")
    
# Verificar se há faturamento para esses processos
print(f"\n\nVerificando FATURADOS.xlsx...")
try:
    df_fat = pd.read_excel('Faturados.xlsx')
    proc_400_fat = df_fat[df_fat['Processo'].astype(str).str.startswith('400', na=False)]
    print(f"Processos 400xxx em FATURADOS: {sorted(proc_400_fat['Processo'].unique())}")
except FileNotFoundError:
    print("FATURADOS.xlsx não encontrado - provavelmente ainda não foi gerado para este mês")
