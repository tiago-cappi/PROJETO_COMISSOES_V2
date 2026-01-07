#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE DIAGNÓSTICO - FLUXO DE SALVAMENTO DE DEVOLUÇÕES

Este script investiga por que o DevolucaoProcessor gera saldos negativos
mas eles não aparecem no Master DB após execução do robô.

Execute com:
    python diagnostico_devolucoes_salvamento.py

Autor: Copilot (diagnóstico temporário)
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_PATH = Path(__file__).parent.resolve()
MES_TESTE = 10
ANO_TESTE = 2025

print("=" * 80)
print("DIAGNÓSTICO DE SALVAMENTO DE DEVOLUÇÕES")
print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()


# ============================================================================
# ETAPA 1: VERIFICAR COMO O PROCESSOR SALVA NO BANCO
# ============================================================================
print("-" * 80)
print("ETAPA 1: ANALISAR CÓDIGO DO DEVOLUCAO_PROCESSOR")
print("-" * 80)

processor_path = BASE_PATH / "src" / "devolucao" / "devolucao_processor.py"

if processor_path.exists():
    print(f"[OK] Arquivo encontrado: {processor_path}")
    
    with open(processor_path, "r", encoding="utf-8") as f:
        conteudo = f.read()
    
    # Verificar se há chamada para salvar no master_db
    print("\n[INFO] Buscando padrões de salvamento no código:")
    
    patterns = [
        ("master_db.append_comissoes", "Chamada para append_comissoes"),
        ("salvar_no_banco", "Parâmetro salvar_no_banco"),
        ("_save_master", "Método interno de salvamento"),
        ("to_excel", "Escrita direta em Excel"),
    ]
    
    for pattern, desc in patterns:
        if pattern in conteudo:
            print(f"  [ENCONTRADO] {desc}: '{pattern}'")
            
            # Mostrar contexto
            linhas = conteudo.split("\n")
            for i, linha in enumerate(linhas):
                if pattern in linha:
                    print(f"    Linha {i+1}: {linha.strip()[:100]}")
        else:
            print(f"  [NÃO ENCONTRADO] {desc}: '{pattern}'")
else:
    print(f"[ERRO] Arquivo não encontrado: {processor_path}")


# ============================================================================
# ETAPA 2: VERIFICAR MÉTODO processar() DO PROCESSOR
# ============================================================================
print()
print("-" * 80)
print("ETAPA 2: ANALISAR MÉTODO processar() COMPLETO")
print("-" * 80)

try:
    sys.path.insert(0, str(BASE_PATH))
    
    # Ler o código fonte do método processar
    import inspect
    from src.devolucao import DevolucaoProcessor
    
    source = inspect.getsource(DevolucaoProcessor.processar)
    
    print("[INFO] Código do método processar():")
    print("-" * 40)
    
    linhas = source.split("\n")
    for i, linha in enumerate(linhas):
        print(f"{i+1:3d} | {linha}")
    
    print("-" * 40)
    
    # Verificar se o método salvar_saldos_negativos existe
    if hasattr(DevolucaoProcessor, "_salvar_saldos_negativos"):
        print("\n[INFO] Método _salvar_saldos_negativos encontrado")
        source_salvar = inspect.getsource(DevolucaoProcessor._salvar_saldos_negativos)
        print("-" * 40)
        linhas = source_salvar.split("\n")
        for i, linha in enumerate(linhas):
            print(f"{i+1:3d} | {linha}")
        print("-" * 40)
    else:
        print("\n[AVISO] Método _salvar_saldos_negativos NÃO encontrado na classe")
        print("        Verificando todos os métodos disponíveis:")
        for name in dir(DevolucaoProcessor):
            if not name.startswith("__"):
                print(f"          - {name}")
                
except Exception as e:
    print(f"[ERRO] Falha ao analisar: {e}")
    import traceback
    traceback.print_exc()


# ============================================================================
# ETAPA 3: VERIFICAR CHAMADA NO CALCULO_COMISSOES.PY
# ============================================================================
print()
print("-" * 80)
print("ETAPA 3: ANALISAR CHAMADA EM CALCULO_COMISSOES.PY")
print("-" * 80)

calculo_path = BASE_PATH / "calculo_comissoes.py"

if calculo_path.exists():
    with open(calculo_path, "r", encoding="utf-8") as f:
        conteudo = f.read()
    
    # Encontrar o método _processar_devolucoes
    print("[INFO] Buscando método _processar_devolucoes:")
    
    if "_processar_devolucoes" in conteudo:
        print("  [ENCONTRADO] Método _processar_devolucoes")
        
        # Extrair o método
        linhas = conteudo.split("\n")
        inicio = None
        fim = None
        indent_base = None
        
        for i, linha in enumerate(linhas):
            if "def _processar_devolucoes" in linha:
                inicio = i
                # Detectar indentação base
                indent_base = len(linha) - len(linha.lstrip())
            elif inicio is not None and fim is None:
                # Verificar se saímos do método (nova definição de método ou classe)
                stripped = linha.lstrip()
                current_indent = len(linha) - len(linha.lstrip())
                if stripped.startswith("def ") and current_indent <= indent_base:
                    fim = i
                    break
        
        if inicio is not None:
            if fim is None:
                fim = min(inicio + 100, len(linhas))
            
            print(f"\n[INFO] Código do método (linhas {inicio+1} a {fim}):")
            print("-" * 40)
            for i in range(inicio, fim):
                print(f"{i+1:4d} | {linhas[i]}")
            print("-" * 40)
            
            # Verificar se o resultado do processor é usado para salvar
            trecho = "\n".join(linhas[inicio:fim])
            
            if "salvar_no_banco=True" in trecho:
                print("\n[OK] Parâmetro salvar_no_banco=True encontrado")
            elif "salvar_no_banco=False" in trecho:
                print("\n[ERRO] Parâmetro salvar_no_banco=False encontrado - DEVOLUÇÕES NÃO SERÃO SALVAS!")
            elif "salvar_no_banco" in trecho:
                print("\n[INFO] Parâmetro salvar_no_banco encontrado, verificar valor")
            else:
                print("\n[AVISO] Parâmetro salvar_no_banco não especificado na chamada")
                print("        Verificar valor padrão no método processar()")
    else:
        print("  [NÃO ENCONTRADO] Método _processar_devolucoes")
else:
    print(f"[ERRO] Arquivo não encontrado: {calculo_path}")


# ============================================================================
# ETAPA 4: TESTAR SALVAMENTO REAL
# ============================================================================
print()
print("-" * 80)
print("ETAPA 4: TESTAR SALVAMENTO REAL (COM BACKUP)")
print("-" * 80)

try:
    from src.devolucao import DevolucaoProcessor
    from src.io.master_db_manager import MasterDBManager
    
    # Carregar Análise Comercial
    comercial_path = BASE_PATH / "dados_entrada" / "Analise_Comercial_Completa.xlsx"
    if comercial_path.exists():
        df_comercial = pd.read_excel(comercial_path)
        print(f"[OK] Análise Comercial carregada: {len(df_comercial)} linhas")
    else:
        comercial_path = BASE_PATH / "dados_entrada" / "Analise_Comercial_Completa.csv"
        df_comercial = pd.read_csv(comercial_path)
        print(f"[OK] Análise Comercial carregada: {len(df_comercial)} linhas")
    
    # Contar registros antes
    master_db = MasterDBManager(str(BASE_PATH))
    df_antes = master_db.get_historico()
    count_antes = len(df_antes) if not df_antes.empty else 0
    count_devolucao_antes = 0
    if not df_antes.empty and "Tipo_Comissao" in df_antes.columns:
        count_devolucao_antes = (df_antes["Tipo_Comissao"] == "DEVOLUCAO").sum()
    
    print(f"\n[INFO] Estado do Master DB ANTES:")
    print(f"  - Total de registros: {count_antes}")
    print(f"  - Registros DEVOLUCAO: {count_devolucao_antes}")
    
    # Executar processor COM salvamento
    print(f"\n[INFO] Executando DevolucaoProcessor com salvar_no_banco=True...")
    
    processor = DevolucaoProcessor(
        base_path=str(BASE_PATH),
        df_analise_comercial=df_comercial,
    )
    
    resultado = processor.processar(mes=MES_TESTE, ano=ANO_TESTE, salvar_no_banco=True)
    
    print(f"\n[RESULTADO] Retorno do processar():")
    for key, value in resultado.items():
        if isinstance(value, list) and len(value) > 3:
            print(f"  {key}: {len(value)} itens")
        else:
            print(f"  {key}: {value}")
    
    # Contar registros depois
    df_depois = master_db.get_historico()
    count_depois = len(df_depois) if not df_depois.empty else 0
    count_devolucao_depois = 0
    if not df_depois.empty and "Tipo_Comissao" in df_depois.columns:
        count_devolucao_depois = (df_depois["Tipo_Comissao"] == "DEVOLUCAO").sum()
    
    print(f"\n[INFO] Estado do Master DB DEPOIS:")
    print(f"  - Total de registros: {count_depois}")
    print(f"  - Registros DEVOLUCAO: {count_devolucao_depois}")
    
    novos = count_depois - count_antes
    novos_devolucao = count_devolucao_depois - count_devolucao_antes
    
    print(f"\n[RESULTADO] Diferença:")
    print(f"  - Novos registros totais: {novos}")
    print(f"  - Novos registros DEVOLUCAO: {novos_devolucao}")
    
    if novos_devolucao > 0:
        print(f"\n[OK] SALVAMENTO FUNCIONOU! {novos_devolucao} devoluções salvas.")
        
        # Mostrar algumas devoluções salvas
        df_devolucoes = df_depois[df_depois["Tipo_Comissao"] == "DEVOLUCAO"]
        print(f"\n[INFO] Algumas devoluções salvas:")
        cols_mostrar = ["Nome_Colaborador", "Processo", "Numero_NF", "Comissao_Calculada", "Fator_Devolucao"]
        cols_existentes = [c for c in cols_mostrar if c in df_devolucoes.columns]
        print(df_devolucoes[cols_existentes].head(10).to_string())
    else:
        print(f"\n[ERRO] SALVAMENTO NÃO FUNCIONOU!")
        print("       O processor gerou saldos mas não salvou no banco.")
        
        # Verificar se há erros no resultado
        if resultado.get("erros"):
            print(f"\n[ERROS] Erros retornados:")
            for erro in resultado["erros"]:
                print(f"  - {erro}")
        
        # Verificar se _salvar_saldos_negativos foi chamado
        if hasattr(processor, "_saldos_negativos"):
            print(f"\n[INFO] Saldos negativos internos: {len(processor._saldos_negativos)}")
        
except Exception as e:
    print(f"[ERRO] Falha no teste: {e}")
    import traceback
    traceback.print_exc()


# ============================================================================
# ETAPA 5: VERIFICAR SE GET_HISTORICO FUNCIONA
# ============================================================================
print()
print("-" * 80)
print("ETAPA 5: VERIFICAR MÉTODO get_historico() DO MASTER_DB")
print("-" * 80)

try:
    from src.io.master_db_manager import MasterDBManager
    import inspect
    
    # Verificar se o método existe
    if hasattr(MasterDBManager, "get_historico"):
        print("[OK] Método get_historico() existe")
        
        source = inspect.getsource(MasterDBManager.get_historico)
        print("\n[INFO] Código do método:")
        print("-" * 40)
        linhas = source.split("\n")
        for i, linha in enumerate(linhas):
            print(f"{i+1:3d} | {linha}")
        print("-" * 40)
    else:
        print("[ERRO] Método get_historico() NÃO existe!")
        print("       O DevolucaoProcessor precisa deste método para buscar comissões históricas.")
        
        print("\n[INFO] Métodos disponíveis em MasterDBManager:")
        for name in dir(MasterDBManager):
            if not name.startswith("_"):
                print(f"  - {name}")
                
except Exception as e:
    print(f"[ERRO] {e}")


# ============================================================================
# RESUMO
# ============================================================================
print()
print("=" * 80)
print("RESUMO")
print("=" * 80)

print("""
POSSÍVEIS CAUSAS DO BUG:

1. O método processar() pode estar com salvar_no_banco=False por padrão
2. O método _salvar_saldos_negativos pode não existir ou ter bug
3. O método get_historico() pode não existir no MasterDBManager
4. A chamada em calculo_comissoes.py pode não estar passando salvar_no_banco=True
5. Pode haver um try/except silenciando erros de salvamento

Verifique os logs acima para identificar a causa específica.
""")

print("=" * 80)
print("FIM DO DIAGNÓSTICO")
print("=" * 80)
