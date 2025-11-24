import pandas as pd
import os

config_path = r"c:\Users\m.rafael\Desktop\PROJETO_COMISSOES_V2\config\REGRAS_COMISSOES.xlsx"

if os.path.exists(config_path):
    try:
        xls = pd.ExcelFile(config_path)
        print("Sheets found in REGRAS_COMISSOES.xlsx:")
        for sheet in xls.sheet_names:
            print(f"- {sheet}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
else:
    print(f"File not found: {config_path}")
