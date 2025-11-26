import pandas as pd
import traceback

try:
    print("Lendo REGRAS_COMISSOES.xlsx...")
    df = pd.read_excel('config/REGRAS_COMISSOES.xlsx', sheet_name='CROSS_SELLING')
    print("Conteúdo da aba CROSS_SELLING:")
    print(df.to_string())
    
    print("\nTipos de dados:")
    print(df.dtypes)
except Exception:
    traceback.print_exc()
