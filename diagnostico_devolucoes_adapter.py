"""
Diagnóstico de Devoluções - Simulação do Adapter.

Este script simula exatamente o que acontece quando o adapter 
chama CalculoComissao().executar() para verificar onde o
processamento de devoluções falha.
"""

import os
import sys
from pathlib import Path

# Simular o mesmo path handling do adapter
ROBO_ROOT_PATH = str(Path(__file__).parent.resolve())
if ROBO_ROOT_PATH not in sys.path:
    sys.path.insert(0, ROBO_ROOT_PATH)

os.chdir(ROBO_ROOT_PATH)

print("=" * 80)
print("DIAGNÓSTICO: Simulação do Adapter para Devoluções")
print("=" * 80)
print(f"[1] ROBO_ROOT_PATH: {ROBO_ROOT_PATH}")
print(f"[2] CWD: {os.getcwd()}")
print()

# Verificar arquivos de entrada
from pathlib import Path as P

devol_xlsx = P("dados_entrada/Devoluções.xlsx")
devol_csv = P("dados_entrada/Devoluções.csv")
master_db = P("data/banco_dados/HISTORICO_COMISSOES_MASTER.xlsx")

print("[3] Verificação de arquivos de entrada:")
print(f"    Devoluções.xlsx existe: {devol_xlsx.exists()}")
print(f"    Devoluções.csv existe: {devol_csv.exists()}")
print(f"    Master DB existe: {master_db.exists()}")
print()

# Verificar estado inicial do Master DB
import pandas as pd

def contar_devolucoes_master():
    if not master_db.exists():
        return 0, 0
    try:
        df = pd.read_excel(master_db)
        total = len(df)
        devol = len(df[df["Tipo_Comissao"].str.upper() == "DEVOLUCAO"]) if "Tipo_Comissao" in df.columns else 0
        return total, devol
    except Exception as e:
        print(f"    ERRO ao ler Master DB: {e}")
        return -1, -1

total_antes, devol_antes = contar_devolucoes_master()
print(f"[4] Estado do Master DB ANTES da execução:")
print(f"    Total de registros: {total_antes}")
print(f"    Registros DEVOLUCAO: {devol_antes}")
print()

# Parâmetros de teste
MES_TESTE = 10
ANO_TESTE = 2025

print(f"[5] Parâmetros de teste: mes={MES_TESTE}, ano={ANO_TESTE}")
print()

# Simular o fluxo do adapter
print("[6] Simulando fluxo do adapter...")
print()

# 1. Importar módulos como o adapter faz
print("    [6.1] Importando módulos...")
try:
    from calculo_comissoes import CalculoComissao
    print("         ✓ CalculoComissao importado")
except Exception as e:
    print(f"         ✗ ERRO ao importar CalculoComissao: {e}")
    sys.exit(1)

try:
    import calculo_comissoes as cc
    print("         ✓ Módulo calculo_comissoes importado")
except Exception as e:
    print(f"         ✗ ERRO ao importar módulo: {e}")
    sys.exit(1)

# 2. Configurar arquivos como o adapter faz
print("    [6.2] Configurando arquivos de entrada...")
try:
    cc.ARQUIVO_FATURADOS = "Faturados.xlsx"
    cc.ARQUIVO_CONVERSOES = "Conversões.xlsx"
    cc.ARQUIVO_FATURADOS_YTD = "Faturados_YTD.xlsx"
    
    import glob
    mm = str(MES_TESTE).zfill(2)
    encontrados = glob.glob(str(Path("dados_entrada/rentabilidades") / f"*{mm}*{ANO_TESTE}*agrupada*.xlsx"))
    if encontrados:
        cc.ARQUIVO_RENTABILIDADE = encontrados[0]
    else:
        padrao = Path("dados_entrada/rentabilidades") / f"rentabilidade_{mm}_{ANO_TESTE}_agrupada.xlsx"
        if padrao.exists():
            cc.ARQUIVO_RENTABILIDADE = str(padrao)
        else:
            cc.ARQUIVO_RENTABILIDADE = None
    
    print(f"         ARQUIVO_FATURADOS: {cc.ARQUIVO_FATURADOS}")
    print(f"         ARQUIVO_RENTABILIDADE: {cc.ARQUIVO_RENTABILIDADE}")
except Exception as e:
    print(f"         ✗ ERRO ao configurar arquivos: {e}")

# 3. Criar instância e configurar parâmetros
print("    [6.3] Criando instância de CalculoComissao...")
try:
    calc = CalculoComissao()
    calc.params['mes_apuracao'] = MES_TESTE
    calc.params['ano_apuracao'] = ANO_TESTE
    print(f"         ✓ Instância criada")
    print(f"         params['mes_apuracao']: {calc.params.get('mes_apuracao')}")
    print(f"         params['ano_apuracao']: {calc.params.get('ano_apuracao')}")
except Exception as e:
    print(f"         ✗ ERRO ao criar instância: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Verificar se _processar_devolucoes existe
print("    [6.4] Verificando método _processar_devolucoes...")
if hasattr(calc, '_processar_devolucoes'):
    print("         ✓ Método existe")
else:
    print("         ✗ Método NÃO existe!")
    sys.exit(1)

# 5. Verificar import de DevolucaoProcessor
print("    [6.5] Verificando import de DevolucaoProcessor...")
try:
    from src.devolucao import DevolucaoProcessor
    print("         ✓ DevolucaoProcessor importado")
except Exception as e:
    print(f"         ✗ ERRO ao importar: {e}")
    sys.exit(1)

# 6. Executar o cálculo (SEM verificar cross-selling para agilizar)
print()
print("=" * 80)
print("[7] EXECUTANDO calc.executar() - IGUAL AO ADAPTER")
print("    AGUARDE... Isso pode demorar alguns minutos.")
print("=" * 80)
print()

# Forçar batch mode para pular cross-selling
calc.params['force_batch_cross_selling'] = False  # Não interromper por cross-selling

try:
    calc.executar(decisoes_cross_selling=[])
    print()
    print("=" * 80)
    print("    ✓ EXECUÇÃO CONCLUÍDA COM SUCESSO")
    print("=" * 80)
except SystemExit as e:
    print(f"    ⚠ SystemExit (provavelmente cross-selling): {e}")
except Exception as e:
    print(f"    ✗ ERRO durante execução: {e}")
    import traceback
    traceback.print_exc()

print()

# 7. Verificar estado final do Master DB
total_depois, devol_depois = contar_devolucoes_master()
print(f"[8] Estado do Master DB DEPOIS da execução:")
print(f"    Total de registros: {total_depois}")
print(f"    Registros DEVOLUCAO: {devol_depois}")
print()

# 8. Comparar
print("[9] RESULTADO:")
if devol_depois > devol_antes:
    print(f"    ✓ SUCESSO! {devol_depois - devol_antes} novo(s) registro(s) DEVOLUCAO criado(s)")
else:
    print(f"    ✗ FALHA! Nenhum novo registro DEVOLUCAO foi criado")
    print()
    print("    Possíveis causas:")
    print("    1. O arquivo Devoluções.xlsx está vazio ou sem dados do período")
    print("    2. Não há comissões históricas para os processos das devoluções")
    print("    3. O método _processar_devolucoes não está sendo chamado")
    print("    4. Erro silencioso no processador de devoluções")
    
print()
print("=" * 80)
print("FIM DO DIAGNÓSTICO")
print("=" * 80)
