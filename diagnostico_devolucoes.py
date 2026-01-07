#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE DIAGNÓSTICO - DEVOLUÇÕES

Este script temporário investiga por que as devoluções não estão gerando
saldos negativos no Master DB.

Execute com:
    python diagnostico_devolucoes.py

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

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================
BASE_PATH = Path(__file__).parent.resolve()
MES_TESTE = 10
ANO_TESTE = 2025

print("=" * 80)
print("DIAGNÓSTICO DE DEVOLUÇÕES")
print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Base Path: {BASE_PATH}")
print(f"Período de teste: {MES_TESTE:02d}/{ANO_TESTE}")
print("=" * 80)
print()


# ============================================================================
# ETAPA 1: LOCALIZAR E CARREGAR ARQUIVO DE DEVOLUÇÕES
# ============================================================================
print("-" * 80)
print("ETAPA 1: LOCALIZAR ARQUIVO DE DEVOLUÇÕES")
print("-" * 80)

nomes_possiveis = [
    "Devoluções.xlsx",
    "Devolucoes.xlsx",
    "Devoluções.xls",
    "Devolucoes.xls",
    "Devoluções.csv",
    "Devolucoes.csv",
]

pastas_possiveis = [
    BASE_PATH / "dados_entrada",
    BASE_PATH,
]

arquivo_devolucoes = None
for pasta in pastas_possiveis:
    print(f"\n[BUSCA] Verificando pasta: {pasta}")
    if not pasta.exists():
        print(f"  └─ Pasta NÃO existe")
        continue
    
    # Listar todos os arquivos na pasta
    arquivos_na_pasta = list(pasta.iterdir()) if pasta.is_dir() else []
    print(f"  └─ Arquivos encontrados: {len(arquivos_na_pasta)}")
    for arq in arquivos_na_pasta:
        if arq.is_file() and ("devolu" in arq.name.lower() or "devoluc" in arq.name.lower()):
            print(f"      • {arq.name} ({arq.stat().st_size} bytes)")
    
    for nome in nomes_possiveis:
        caminho = pasta / nome
        if caminho.exists():
            arquivo_devolucoes = caminho
            print(f"\n[OK] Arquivo encontrado: {caminho}")
            break
    if arquivo_devolucoes:
        break

if not arquivo_devolucoes:
    print("\n[ERRO] Nenhum arquivo de devoluções encontrado!")
    print("       Verifique se o arquivo existe em 'dados_entrada/' com um dos nomes:")
    for nome in nomes_possiveis:
        print(f"         - {nome}")
    sys.exit(1)


# ============================================================================
# ETAPA 2: CARREGAR E EXIBIR CONTEÚDO DO ARQUIVO
# ============================================================================
print()
print("-" * 80)
print("ETAPA 2: CARREGAR CONTEÚDO DO ARQUIVO DE DEVOLUÇÕES")
print("-" * 80)

try:
    if str(arquivo_devolucoes).endswith(".csv"):
        # Tentar diferentes separadores
        for sep in [";", ",", "\t"]:
            try:
                df_dev = pd.read_csv(arquivo_devolucoes, sep=sep, encoding="utf-8")
                if len(df_dev.columns) > 1:
                    print(f"[OK] CSV carregado com separador '{sep}'")
                    break
            except:
                pass
        else:
            df_dev = pd.read_csv(arquivo_devolucoes, encoding="utf-8")
    else:
        df_dev = pd.read_excel(arquivo_devolucoes)
    
    print(f"\n[OK] Arquivo carregado: {len(df_dev)} linhas, {len(df_dev.columns)} colunas")
    
except Exception as e:
    print(f"\n[ERRO] Falha ao carregar arquivo: {e}")
    sys.exit(1)

print(f"\n[INFO] Colunas encontradas:")
for i, col in enumerate(df_dev.columns):
    print(f"  {i+1}. '{col}'")

print(f"\n[INFO] Primeiras 10 linhas do arquivo:")
print(df_dev.head(10).to_string())

print(f"\n[INFO] Tipos de dados:")
print(df_dev.dtypes.to_string())


# ============================================================================
# ETAPA 3: VERIFICAR COLUNAS ESPERADAS
# ============================================================================
print()
print("-" * 80)
print("ETAPA 3: VERIFICAR COLUNAS ESPERADAS")
print("-" * 80)

COLUNAS_ESPERADAS = {
    "num_docorigem": ["Num docorigem", "num docorigem", "NUM DOCORIGEM", "Numero Doc Origem"],
    "data_entrada": ["Data de Entrada", "data de entrada", "DATA DE ENTRADA", "Data Entrada"],
    "valor_produtos": ["Valor Produtos", "valor produtos", "VALOR PRODUTOS", "Valor"],
}

mapeamento_colunas = {}
colunas_faltando = []

for campo, nomes_possiveis_col in COLUNAS_ESPERADAS.items():
    encontrada = None
    for nome in nomes_possiveis_col:
        if nome in df_dev.columns:
            encontrada = nome
            break
    
    if encontrada:
        mapeamento_colunas[campo] = encontrada
        print(f"[OK] Campo '{campo}' -> Coluna '{encontrada}'")
    else:
        colunas_faltando.append(campo)
        print(f"[ERRO] Campo '{campo}' NÃO encontrado. Esperado: {nomes_possiveis_col}")

if colunas_faltando:
    print(f"\n[ERRO CRÍTICO] Colunas obrigatórias faltando: {colunas_faltando}")
    print("O processador de devoluções não vai funcionar sem essas colunas!")


# ============================================================================
# ETAPA 4: ANALISAR DADOS DE DEVOLUÇÃO
# ============================================================================
print()
print("-" * 80)
print("ETAPA 4: ANALISAR DADOS DE DEVOLUÇÃO")
print("-" * 80)

if "num_docorigem" in mapeamento_colunas:
    col_nf = mapeamento_colunas["num_docorigem"]
    print(f"\n[INFO] Valores na coluna '{col_nf}':")
    for i, val in enumerate(df_dev[col_nf].tolist()):
        print(f"  Linha {i+1}: '{val}' (tipo: {type(val).__name__})")
    
    # Verificar vazios
    vazios = df_dev[col_nf].isna().sum() + (df_dev[col_nf].astype(str).str.strip() == "").sum()
    print(f"\n[INFO] Valores vazios/nulos em '{col_nf}': {vazios}")

if "data_entrada" in mapeamento_colunas:
    col_data = mapeamento_colunas["data_entrada"]
    print(f"\n[INFO] Valores na coluna '{col_data}':")
    for i, val in enumerate(df_dev[col_data].tolist()):
        print(f"  Linha {i+1}: '{val}' (tipo: {type(val).__name__})")
    
    # Tentar converter para datetime
    print(f"\n[INFO] Tentando converter datas...")
    try:
        # Tentar formato DD/MM/YYYY primeiro
        datas_convertidas = pd.to_datetime(df_dev[col_data], format="%d/%m/%Y", errors="coerce")
        nao_convertidas = datas_convertidas.isna().sum()
        print(f"  Formato DD/MM/YYYY: {len(df_dev) - nao_convertidas} OK, {nao_convertidas} falhas")
        
        if nao_convertidas > 0:
            # Tentar inferir automaticamente
            datas_convertidas = pd.to_datetime(df_dev[col_data], errors="coerce")
            nao_convertidas = datas_convertidas.isna().sum()
            print(f"  Formato automático: {len(df_dev) - nao_convertidas} OK, {nao_convertidas} falhas")
        
        print(f"\n[INFO] Datas convertidas:")
        for i, (original, convertida) in enumerate(zip(df_dev[col_data].tolist(), datas_convertidas.tolist())):
            mes_ok = ""
            if pd.notna(convertida):
                mes = convertida.month
                ano = convertida.year
                mes_ok = f" -> mês={mes}, ano={ano}"
                if mes == MES_TESTE and ano == ANO_TESTE:
                    mes_ok += " [MATCH PERÍODO!]"
                else:
                    mes_ok += f" [NÃO MATCH: esperado {MES_TESTE}/{ANO_TESTE}]"
            print(f"  Linha {i+1}: '{original}' -> {convertida}{mes_ok}")
            
    except Exception as e:
        print(f"  [ERRO] Falha na conversão: {e}")

if "valor_produtos" in mapeamento_colunas:
    col_valor = mapeamento_colunas["valor_produtos"]
    print(f"\n[INFO] Valores na coluna '{col_valor}':")
    for i, val in enumerate(df_dev[col_valor].tolist()):
        try:
            val_num = float(str(val).replace(",", ".").replace(" ", ""))
            print(f"  Linha {i+1}: '{val}' -> {val_num:.2f}")
        except:
            print(f"  Linha {i+1}: '{val}' -> [NÃO NUMÉRICO]")


# ============================================================================
# ETAPA 5: SIMULAR FILTRO DO LOADER
# ============================================================================
print()
print("-" * 80)
print("ETAPA 5: SIMULAR FILTRO DO LOADER (mês/ano)")
print("-" * 80)

if all(k in mapeamento_colunas for k in ["num_docorigem", "data_entrada", "valor_produtos"]):
    col_nf = mapeamento_colunas["num_docorigem"]
    col_data = mapeamento_colunas["data_entrada"]
    col_valor = mapeamento_colunas["valor_produtos"]
    
    # Criar DataFrame normalizado
    df_norm = pd.DataFrame()
    df_norm["numero_nf_original"] = df_dev[col_nf]
    
    # Tentar converter data
    df_norm["data_entrada"] = pd.to_datetime(df_dev[col_data], format="%d/%m/%Y", errors="coerce")
    # Se falhou, tentar automático
    if df_norm["data_entrada"].isna().all():
        df_norm["data_entrada"] = pd.to_datetime(df_dev[col_data], errors="coerce")
    
    df_norm["valor_devolvido"] = pd.to_numeric(
        df_dev[col_valor].astype(str).str.replace(",", ".").str.replace(" ", ""), 
        errors="coerce"
    ).fillna(0)
    
    print(f"\n[INFO] DataFrame normalizado:")
    print(df_norm.to_string())
    
    total_antes = len(df_norm)
    print(f"\n[FILTRO] Total inicial: {total_antes} linhas")
    
    # Filtro 1: Remover sem Num docorigem
    df_norm = df_norm[df_norm["numero_nf_original"].notna()]
    df_norm = df_norm[df_norm["numero_nf_original"].astype(str).str.strip() != ""]
    print(f"[FILTRO] Após remover vazios: {len(df_norm)} linhas")
    
    # Filtro 2: Remover valor zero
    df_norm = df_norm[df_norm["valor_devolvido"] > 0]
    print(f"[FILTRO] Após remover valor <= 0: {len(df_norm)} linhas")
    
    # Filtro 3: Filtrar por mês/ano
    df_norm["data_entrada"] = pd.to_datetime(df_norm["data_entrada"], errors="coerce")
    
    print(f"\n[INFO] Verificando mês/ano de cada linha:")
    for i, row in df_norm.iterrows():
        data = row["data_entrada"]
        if pd.notna(data):
            mes = data.month
            ano = data.year
            match = (mes == MES_TESTE and ano == ANO_TESTE)
            print(f"  Linha {i}: data={data}, mês={mes}, ano={ano} -> {'MATCH' if match else 'NÃO MATCH'}")
        else:
            print(f"  Linha {i}: data=NaT -> NÃO MATCH (data inválida)")
    
    df_filtrado = df_norm[
        (df_norm["data_entrada"].dt.month == MES_TESTE) &
        (df_norm["data_entrada"].dt.year == ANO_TESTE)
    ]
    print(f"\n[FILTRO] Após filtrar mês={MES_TESTE}, ano={ANO_TESTE}: {len(df_filtrado)} linhas")
    
    if len(df_filtrado) > 0:
        print(f"\n[OK] Devoluções válidas para processamento:")
        print(df_filtrado.to_string())
    else:
        print(f"\n[ERRO] Nenhuma devolução passou nos filtros!")
        print("       Verifique se as datas estão no formato correto (DD/MM/YYYY)")
        print(f"       e se correspondem ao período {MES_TESTE:02d}/{ANO_TESTE}")


# ============================================================================
# ETAPA 6: VERIFICAR ANÁLISE COMERCIAL
# ============================================================================
print()
print("-" * 80)
print("ETAPA 6: VERIFICAR ANÁLISE COMERCIAL")
print("-" * 80)

caminhos_comercial = [
    BASE_PATH / "dados_entrada" / "Analise_Comercial_Completa.xlsx",
    BASE_PATH / "dados_entrada" / "Analise_Comercial_Completa.csv",
    BASE_PATH / "Analise_Comercial_Completa.xlsx",
    BASE_PATH / "Analise_Comercial_Completa.csv",
]

df_comercial = None
for caminho in caminhos_comercial:
    if caminho.exists():
        print(f"[OK] Análise Comercial encontrada: {caminho}")
        try:
            if str(caminho).endswith(".csv"):
                df_comercial = pd.read_csv(caminho, encoding="utf-8")
            else:
                df_comercial = pd.read_excel(caminho)
            print(f"[OK] Carregada: {len(df_comercial)} linhas, {len(df_comercial.columns)} colunas")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar: {e}")
        break

if df_comercial is None:
    print("[ERRO] Análise Comercial não encontrada!")
else:
    # Verificar colunas necessárias
    print(f"\n[INFO] Colunas da Análise Comercial:")
    for col in df_comercial.columns:
        if any(x in col.lower() for x in ["numero", "nf", "processo", "valor", "realizado"]):
            print(f"  • '{col}'")
    
    # Buscar coluna de NF
    col_nf_comercial = None
    for nome in ["Numero NF", "numero nf", "NUMERO NF", "Num NF"]:
        if nome in df_comercial.columns:
            col_nf_comercial = nome
            break
    
    col_processo_comercial = None
    for nome in ["Processo", "processo", "PROCESSO"]:
        if nome in df_comercial.columns:
            col_processo_comercial = nome
            break
    
    col_valor_comercial = None
    for nome in ["Valor Realizado", "valor realizado", "VALOR REALIZADO"]:
        if nome in df_comercial.columns:
            col_valor_comercial = nome
            break
    
    print(f"\n[INFO] Mapeamento de colunas:")
    print(f"  Numero NF: {col_nf_comercial}")
    print(f"  Processo: {col_processo_comercial}")
    print(f"  Valor Realizado: {col_valor_comercial}")
    
    if all([col_nf_comercial, col_processo_comercial, col_valor_comercial]):
        # Verificar se as NFs do arquivo de devolução existem
        if "num_docorigem" in mapeamento_colunas:
            print(f"\n[INFO] Verificando vínculo NF -> Processo:")
            nfs_devolucao = df_dev[mapeamento_colunas["num_docorigem"]].astype(str).str.strip().unique()
            
            for nf in nfs_devolucao:
                if not nf or nf == "nan":
                    continue
                    
                # Buscar na Análise Comercial
                nf_normalizado = str(nf).strip()
                mask = df_comercial[col_nf_comercial].astype(str).str.strip() == nf_normalizado
                
                # Tentar sem zeros à esquerda
                if not mask.any():
                    try:
                        nf_int = str(int(float(nf_normalizado)))
                        mask = df_comercial[col_nf_comercial].astype(str).str.strip().str.lstrip("0") == nf_int.lstrip("0")
                    except:
                        pass
                
                linhas = df_comercial[mask]
                
                if linhas.empty:
                    print(f"\n  NF '{nf}': [NÃO ENCONTRADA na Análise Comercial]")
                    
                    # Mostrar algumas NFs existentes para comparação
                    print(f"    Exemplos de NFs na Análise Comercial:")
                    sample_nfs = df_comercial[col_nf_comercial].astype(str).str.strip().head(10).tolist()
                    for s in sample_nfs:
                        print(f"      '{s}'")
                else:
                    processo = str(linhas.iloc[0][col_processo_comercial]).strip()
                    
                    # Calcular valor realizado total do processo
                    mask_processo = df_comercial[col_processo_comercial].astype(str).str.strip() == processo
                    linhas_processo = df_comercial[mask_processo]
                    valor_total = linhas_processo[col_valor_comercial].sum()
                    
                    print(f"\n  NF '{nf}':")
                    print(f"    -> Processo: '{processo}'")
                    print(f"    -> Linhas da NF: {len(linhas)}")
                    print(f"    -> Linhas do Processo: {len(linhas_processo)}")
                    print(f"    -> Valor Realizado Total: R$ {valor_total:,.2f}")


# ============================================================================
# ETAPA 7: VERIFICAR MASTER DB
# ============================================================================
print()
print("-" * 80)
print("ETAPA 7: VERIFICAR MASTER DB (Histórico de Comissões)")
print("-" * 80)

master_db_path = BASE_PATH / "data" / "banco_dados" / "HISTORICO_COMISSOES_MASTER.xlsx"

if not master_db_path.exists():
    print(f"[ERRO] Master DB não encontrado: {master_db_path}")
    print("       Rode o cálculo de comissões primeiro para criar o banco de dados.")
else:
    try:
        df_master = pd.read_excel(master_db_path, sheet_name="HISTORICO")
        print(f"[OK] Master DB carregado: {len(df_master)} registros")
        
        print(f"\n[INFO] Colunas do Master DB:")
        for col in df_master.columns:
            print(f"  • '{col}'")
        
        # Verificar tipos de comissão
        if "Tipo_Comissao" in df_master.columns:
            print(f"\n[INFO] Tipos de comissão no banco:")
            tipos = df_master["Tipo_Comissao"].value_counts()
            for tipo, qtd in tipos.items():
                print(f"  • {tipo}: {qtd} registros")
        
        # Verificar período
        if "Mes_Referencia" in df_master.columns and "Ano_Referencia" in df_master.columns:
            print(f"\n[INFO] Registros do período {MES_TESTE:02d}/{ANO_TESTE}:")
            mask_periodo = (
                (df_master["Mes_Referencia"].fillna(-1).astype(int) == MES_TESTE) &
                (df_master["Ano_Referencia"].fillna(-1).astype(int) == ANO_TESTE)
            )
            df_periodo = df_master[mask_periodo]
            print(f"  Total: {len(df_periodo)} registros")
            
            if "Tipo_Comissao" in df_periodo.columns:
                tipos_periodo = df_periodo["Tipo_Comissao"].value_counts()
                for tipo, qtd in tipos_periodo.items():
                    print(f"    • {tipo}: {qtd}")
            
            # Verificar se há DEVOLUCAO
            if "DEVOLUCAO" in df_periodo["Tipo_Comissao"].values:
                print(f"\n[OK] Devoluções encontradas no período!")
            else:
                print(f"\n[AVISO] Nenhuma DEVOLUCAO encontrada no período {MES_TESTE:02d}/{ANO_TESTE}")
        
        # Para cada NF de devolução, verificar se há comissões históricas
        if "num_docorigem" in mapeamento_colunas and df_comercial is not None:
            print(f"\n[INFO] Verificando comissões históricas para processos das devoluções:")
            
            col_processo_master = None
            for nome in ["Processo", "processo", "PROCESSO"]:
                if nome in df_master.columns:
                    col_processo_master = nome
                    break
            
            if col_processo_master and col_nf_comercial and col_processo_comercial:
                nfs_devolucao = df_dev[mapeamento_colunas["num_docorigem"]].astype(str).str.strip().unique()
                
                for nf in nfs_devolucao:
                    if not nf or nf == "nan":
                        continue
                    
                    # Buscar processo na Análise Comercial
                    mask = df_comercial[col_nf_comercial].astype(str).str.strip() == str(nf).strip()
                    if not mask.any():
                        try:
                            nf_int = str(int(float(nf)))
                            mask = df_comercial[col_nf_comercial].astype(str).str.strip().str.lstrip("0") == nf_int.lstrip("0")
                        except:
                            pass
                    
                    linhas = df_comercial[mask]
                    if linhas.empty:
                        print(f"\n  NF '{nf}': Processo não identificado")
                        continue
                    
                    processo = str(linhas.iloc[0][col_processo_comercial]).strip()
                    
                    # Buscar comissões históricas para este processo
                    mask_processo = df_master[col_processo_master].astype(str).str.strip() == processo
                    comissoes = df_master[mask_processo]
                    
                    # Filtrar apenas FATURAMENTO/REGULAR/ADIANTAMENTO
                    if "Tipo_Comissao" in comissoes.columns:
                        tipos_validos = ["FATURAMENTO", "REGULAR", "ADIANTAMENTO"]
                        comissoes = comissoes[comissoes["Tipo_Comissao"].isin(tipos_validos)]
                    
                    print(f"\n  NF '{nf}' -> Processo '{processo}':")
                    print(f"    -> Comissões históricas (FAT/REG/ADI): {len(comissoes)}")
                    
                    if len(comissoes) > 0 and "Comissao_Calculada" in comissoes.columns:
                        total_comissao = comissoes["Comissao_Calculada"].sum()
                        print(f"    -> Total de comissões pagas: R$ {total_comissao:,.2f}")
                        
                        if "Nome_Colaborador" in comissoes.columns:
                            colaboradores = comissoes["Nome_Colaborador"].unique()
                            print(f"    -> Colaboradores: {', '.join(map(str, colaboradores[:5]))}")
                    else:
                        print(f"    [AVISO] Sem comissões históricas para estornar!")
                        
    except Exception as e:
        print(f"[ERRO] Falha ao carregar Master DB: {e}")


# ============================================================================
# ETAPA 8: TENTAR EXECUTAR O LOADER REAL
# ============================================================================
print()
print("-" * 80)
print("ETAPA 8: EXECUTAR LOADER REAL (src.devolucao.DevolucaoLoader)")
print("-" * 80)

try:
    sys.path.insert(0, str(BASE_PATH))
    from src.devolucao import DevolucaoLoader
    
    loader = DevolucaoLoader(str(BASE_PATH))
    sucesso, df_resultado, msg = loader.carregar(MES_TESTE, ANO_TESTE)
    
    print(f"\n[RESULTADO] Sucesso: {sucesso}")
    print(f"[RESULTADO] Mensagem: {msg}")
    print(f"[RESULTADO] Devoluções carregadas: {len(df_resultado)}")
    
    if not df_resultado.empty:
        print(f"\n[INFO] Devoluções retornadas pelo Loader:")
        print(df_resultado.to_string())
    else:
        print(f"\n[AVISO] Loader retornou DataFrame vazio!")
        
except ImportError as e:
    print(f"[ERRO] Falha ao importar DevolucaoLoader: {e}")
except Exception as e:
    print(f"[ERRO] Falha ao executar Loader: {e}")
    import traceback
    traceback.print_exc()


# ============================================================================
# ETAPA 9: TENTAR EXECUTAR O PROCESSOR REAL
# ============================================================================
print()
print("-" * 80)
print("ETAPA 9: EXECUTAR PROCESSOR REAL (src.devolucao.DevolucaoProcessor)")
print("-" * 80)

try:
    from src.devolucao import DevolucaoProcessor
    
    # Carregar Análise Comercial para passar ao processor
    if df_comercial is not None:
        processor = DevolucaoProcessor(
            base_path=str(BASE_PATH),
            df_analise_comercial=df_comercial,
        )
        
        # Executar processamento SEM salvar no banco (dry run)
        print(f"\n[INFO] Executando processamento (dry run, sem salvar)...")
        
        # Sobrescrever método para não salvar
        resultado = processor.processar(mes=MES_TESTE, ano=ANO_TESTE, salvar_no_banco=False)
        
        print(f"\n[RESULTADO] Resultado do processamento:")
        for key, value in resultado.items():
            if isinstance(value, list) and len(value) > 3:
                print(f"  {key}: {len(value)} itens")
            else:
                print(f"  {key}: {value}")
        
        # Mostrar saldos negativos gerados
        if hasattr(processor, "_saldos_negativos") and processor._saldos_negativos:
            print(f"\n[OK] Saldos negativos gerados: {len(processor._saldos_negativos)}")
            for i, saldo in enumerate(processor._saldos_negativos[:5]):
                print(f"\n  Saldo {i+1}:")
                for k, v in saldo.items():
                    print(f"    {k}: {v}")
        else:
            print(f"\n[AVISO] Nenhum saldo negativo foi gerado!")
            
    else:
        print("[ERRO] Análise Comercial não disponível para o teste")
        
except ImportError as e:
    print(f"[ERRO] Falha ao importar DevolucaoProcessor: {e}")
except Exception as e:
    print(f"[ERRO] Falha ao executar Processor: {e}")
    import traceback
    traceback.print_exc()


# ============================================================================
# RESUMO FINAL
# ============================================================================
print()
print("=" * 80)
print("RESUMO DO DIAGNÓSTICO")
print("=" * 80)

problemas = []

if colunas_faltando:
    problemas.append(f"Colunas faltando no arquivo de devoluções: {colunas_faltando}")

if "data_entrada" in mapeamento_colunas:
    col_data = mapeamento_colunas["data_entrada"]
    datas = pd.to_datetime(df_dev[col_data], format="%d/%m/%Y", errors="coerce")
    if datas.isna().all():
        datas = pd.to_datetime(df_dev[col_data], errors="coerce")
    
    match_count = ((datas.dt.month == MES_TESTE) & (datas.dt.year == ANO_TESTE)).sum()
    if match_count == 0:
        problemas.append(f"Nenhuma data corresponde ao período {MES_TESTE:02d}/{ANO_TESTE}")

if df_comercial is not None and "num_docorigem" in mapeamento_colunas:
    nfs_encontradas = 0
    nfs_devolucao = df_dev[mapeamento_colunas["num_docorigem"]].astype(str).str.strip().unique()
    for nf in nfs_devolucao:
        if not nf or nf == "nan":
            continue
        mask = df_comercial[col_nf_comercial].astype(str).str.strip() == str(nf).strip()
        if mask.any():
            nfs_encontradas += 1
    
    if nfs_encontradas == 0:
        problemas.append("Nenhuma NF do arquivo de devoluções foi encontrada na Análise Comercial")

if problemas:
    print("\n[PROBLEMAS ENCONTRADOS]")
    for i, prob in enumerate(problemas, 1):
        print(f"  {i}. {prob}")
else:
    print("\n[OK] Nenhum problema óbvio encontrado na configuração.")
    print("     Se ainda não gera saldos negativos, verifique os logs detalhados acima.")

print()
print("=" * 80)
print("FIM DO DIAGNÓSTICO")
print("=" * 80)
