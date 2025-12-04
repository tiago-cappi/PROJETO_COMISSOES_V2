import os
import pandas as pd
import sys
from calculo_comissoes import CalculoComissao
from src.recebimento.recebimento_orchestrator import RecebimentoOrchestrator

# Configuração
BASE_PATH = os.path.abspath("test_env")
MES = 8
ANO = 2025

# Criar estrutura de pastas se não existir
os.makedirs(os.path.join(BASE_PATH, "dados_entrada"), exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "config"), exist_ok=True)

# Copiar regras (se não existir no test_env)
config_dest = os.path.join(BASE_PATH, "config", "REGRAS_COMISSOES.xlsx")
if not os.path.exists(config_dest) and os.path.exists("config/REGRAS_COMISSOES.xlsx"):
    import shutil
    shutil.copy("config/REGRAS_COMISSOES.xlsx", config_dest)
    print(f"Copiado: config/REGRAS_COMISSOES.xlsx -> {config_dest}")

# Copiar data (taxas) - se não existir
data_dest = os.path.join(BASE_PATH, "data")
if not os.path.exists(data_dest) and os.path.exists("data"):
    import shutil
    shutil.copytree("data", data_dest)
    print(f"Copiado: data -> {data_dest}")

# Limpar apenas arquivos de saída (NÃO os dados de entrada!)
for f in ["Estado_Processos_Recebimento.xlsx"]:
    path = os.path.join(BASE_PATH, f)
    if os.path.exists(path):
        os.remove(path)
        print(f"Removido arquivo de saída anterior: {f}")

# Remover arquivos Comissoes_Recebimento_*.xlsx e Auditoria_*.pdf
import glob
for pattern in ["Comissoes_Recebimento_*.xlsx", "Auditoria_*.pdf"]:
    for f in glob.glob(os.path.join(BASE_PATH, pattern)):
        os.remove(f)
        print(f"Removido: {os.path.basename(f)}")

print(f"\n=== VERIFICANDO DADOS DE ENTRADA EM {BASE_PATH}/dados_entrada ===")

# Verificar se os arquivos de entrada existem
fin_path = os.path.join(BASE_PATH, "dados_entrada", "Análise Financeira.xlsx")
com_path = os.path.join(BASE_PATH, "dados_entrada", "Analise_Comercial_Completa.csv")

# Se não existir Análise Financeira, criar com dados padrão de teste
if not os.path.exists(fin_path):
    print(f"AVISO: {fin_path} não encontrado. Criando arquivo de teste...")
    df_fin = pd.DataFrame({
        "Documento": ["COT100002"],
        "Valor Líquido": [1000.0],
        "Data de Baixa": [pd.Timestamp("2025-08-01")],
        "Tipo de Baixa": ["B"]
    })
    df_fin.to_excel(fin_path, index=False)
    print(f"Criado: {fin_path}")
else:
    print(f"Usando Análise Financeira existente: {fin_path}")
    df_fin = pd.read_excel(fin_path)

print("Conteúdo Análise Financeira:")
print(df_fin)
print("-" * 50)

# Se não existir Análise Comercial, criar com dados padrão de teste
if not os.path.exists(com_path):
    print(f"AVISO: {com_path} não encontrado. Criando arquivo de teste...")
    df_com = pd.DataFrame({
        "Processo": ["100002"],
        "Status Processo": ["PENDENTE"],  # PENDENTE, não FATURADO!
        "Numero NF": ["048001"],
        "Dt Emissão": [""],  # Vazio para não faturado
        "Data Aceite": ["2025-07-16"],
        "Valor Realizado": [""],  # Vazio para não faturado
        "Valor Orçado": [5000.0],
        "Consultor Interno": ["ANDREY.ANDRADE"],
        "Representante-pedido": ["ANDRÉ LUIS GONCALVES CAMARGO"],
        "Gerente Comercial-Pedido": [""],
        "Negócio": ["SSO"],
        "Grupo": ["Detector Portátil"],
        "Subgrupo": ["MicroClip"],
        "Tipo de Mercadoria": ["Produto"],
        "Aplicação Mat./Serv.": ["Industrial"],
        "Cliente": ["9999"],
        "Nome Cliente": ["CLIENTE TESTE LTDA"],
        "Cidade": ["São Paulo"],
        "UF": ["SP"],
        "Código Produto": ["PROD100002"],
        "Descrição Produto": ["Produto de Teste"],
        "Qtde Atendida": ["1"],
        "Operação": ["PVEN - Produto Venda"],
        "Fabricante": [""]
    })
    df_com.to_csv(com_path, index=False, sep=";")
    print(f"Criado: {com_path}")
else:
    print(f"Usando Análise Comercial existente: {com_path}")
    df_com = pd.read_csv(com_path, sep=";")

print("Conteúdo Análise Comercial:")
print(df_com[["Processo", "Status Processo", "Numero NF"]])
print("-" * 50)

print("=== EXECUTANDO CÁLCULO ===")

# Mudar CWD para test_env para enganar o AnaliseFinanceiraLoader
original_cwd = os.getcwd()
os.chdir(BASE_PATH)
print(f"CWD alterado para: {os.getcwd()}")

# Instanciar CalculoComissao
calc = CalculoComissao()
calc.base_path = "." # Agora é relativo ao CWD (test_env)

# Forçar carregamento dos dados
try:
    calc._carregar_dados()
    # Verificar se carregou
    if "ANALISE_COMERCIAL_COMPLETA" not in calc.data or calc.data["ANALISE_COMERCIAL_COMPLETA"].empty:
        print("AVISO: ANALISE_COMERCIAL_COMPLETA não carregada automaticamente. Forçando carga manual.")
        calc.data["ANALISE_COMERCIAL_COMPLETA"] = df_com
    else:
        print(f"Dados carregados com sucesso. Linhas Comercial: {len(calc.data['ANALISE_COMERCIAL_COMPLETA'])}")
except Exception as e:
    print(f"Erro ao carregar dados: {e}")
    # Fallback
    calc.data["ANALISE_COMERCIAL_COMPLETA"] = df_com

# Instanciar Orchestrator
orch = RecebimentoOrchestrator(calc, mes=MES, ano=ANO, base_path=".")

# Executar
try:
    output_file = orch.executar()
    print(f"Execução concluída. Arquivo gerado: {output_file}")
    
    # Salvar estado (importante!)
    orch.salvar_estado_processos()
    print("Estado salvo.")
    
except Exception as e:
    print(f"ERRO NA EXECUÇÃO: {e}")
    import traceback
    traceback.print_exc()

# Restaurar CWD
os.chdir(original_cwd)

print("=== RESULTADOS (ESTADO) ===")
estado_path = os.path.join(BASE_PATH, "Estado_Processos_Recebimento.xlsx")
if os.path.exists(estado_path):
    df_estado = pd.read_excel(estado_path)
    print(f"Arquivo de Estado: {estado_path}")
    print(df_estado.T) # Transpor para facilitar leitura vertical
else:
    print("Arquivo de Estado NÃO encontrado!")

print("=== FIM DO TESTE ===")
