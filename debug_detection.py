import pandas as pd
import sys
import os

# Adicionar diretório atual ao path
sys.path.append(os.getcwd())

from calculo_comissoes import CalculoComissao

print("Iniciando teste isolado de detecção de cross-selling...")

# Instanciar calculadora
calc = CalculoComissao()

# Carregar dados (simulado ou real)
print("Carregando dados...")
calc._carregar_dados()

import sys

# Verificar se FATURADOS tem processos 400xxx
df_fat = calc.data["FATURADOS"]
sys.stderr.write(f"Keys in calc.data: {list(calc.data.keys())}\n")
sys.stderr.write(f"Colunas FATURADOS: {df_fat.columns.tolist()}\n")

sys.stderr.write("\nVerificando dados de CROSS_SELLING carregados:\n")
if "CROSS_SELLING" in calc.data:
    df_cs = calc.data["CROSS_SELLING"]
    sys.stderr.write(f"Colunas (repr): {[repr(c) for c in df_cs.columns]}\n")
    for idx, row in df_cs.iterrows():
        sys.stderr.write(f"Row {idx}: {row.to_dict()}\n")
else:
    sys.stderr.write("Chave CROSS_SELLING não encontrada em calc.data!\n")

if "Processo" in df_fat.columns:
    procs = df_fat["Processo"].unique()
    procs_400 = [p for p in procs if str(p).startswith("400")]
    print(f"Processos 400xxx em FATURADOS: {procs_400}")
else:
    print("Coluna Processo não encontrada em FATURADOS!")

# Chamar detecção
print("\nChamando _detectar_cross_selling()...")
calc._detectar_cross_selling()

print("\nResultados:")
print(calc.casos_cross_selling_detectados)
