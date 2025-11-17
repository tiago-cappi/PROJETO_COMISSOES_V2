import os

# Verificar arquivos
files = os.listdir('dados_entrada')
print("=== Arquivos em dados_entrada ===")
for f in files:
    if f.endswith('.xlsx'):
        print(f"  {repr(f)}")

# Verificar o que o código procura
path_hardcoded = os.path.join("dados_entrada", "Análise Financeira.xlsx")
print(f"\n=== Caminho hardcoded no código ===")
print(f"Path: {repr(path_hardcoded)}")
print(f"Existe? {os.path.exists(path_hardcoded)}")

# Verificar o arquivo real
analise_files = [f for f in files if 'lise Financeira' in f]
if analise_files:
    real_name = analise_files[0]
    path_real = os.path.join("dados_entrada", real_name)
    print(f"\n=== Arquivo real no sistema ===")
    print(f"Nome: {repr(real_name)}")
    print(f"Path: {repr(path_real)}")
    print(f"Existe? {os.path.exists(path_real)}")
    
    # Comparar bytes
    print(f"\n=== Comparação de encoding ===")
    print(f"Hardcoded bytes: {path_hardcoded.encode('utf-8')}")
    print(f"Real bytes:      {path_real.encode('utf-8')}")
    print(f"\nSão iguais? {path_hardcoded == path_real}")

