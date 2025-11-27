import pandas as pd
import os

# Arquivos
arquivo_faturados = 'Faturados.xlsx'
arquivo_comissoes = 'Comissoes_Calculadas_20251127_141855.xlsx'

print(f"Analisando arquivos:\n1. {arquivo_faturados}\n2. {arquivo_comissoes}\n")

# Carregar Faturados
if os.path.exists(arquivo_faturados):
    df_fat = pd.read_excel(arquivo_faturados)
    processos_fat = set(df_fat['Processo'].unique())
    print(f"FATURADOS: {len(df_fat)} linhas, {len(processos_fat)} processos únicos")
else:
    print("ERRO: Faturados.xlsx não encontrado")
    exit(1)

# Carregar Comissões
if os.path.exists(arquivo_comissoes):
    df_com = pd.read_excel(arquivo_comissoes, sheet_name='COMISSOES_CALCULADAS')
    processos_com = set(df_com['processo'].unique())
    print(f"COMISSOES: {len(df_com)} linhas, {len(processos_com)} processos únicos")
else:
    print(f"ERRO: {arquivo_comissoes} não encontrado")
    exit(1)

# Comparar
faltantes = processos_fat - processos_com
extras = processos_com - processos_fat

print("\n" + "="*50)
print(f"PROCESSOS FALTANTES ({len(faltantes)}):")
print("="*50)
if faltantes:
    lista_faltantes = sorted(list(faltantes))
    print(lista_faltantes)
    
    # Detalhar os primeiros 10 faltantes
    print("\nDETALHES DOS PRIMEIROS 10 FALTANTES EM FATURADOS:")
    cols_show = ['Processo', 'Código Produto', 'Negócio', 'Grupo', 'Subgrupo', 'Tipo de Mercadoria', 'Consultor Interno', 'Representante-pedido']
    cols_existentes = [c for c in cols_show if c in df_fat.columns]
    
    # Filtrar apenas os faltantes
    df_faltantes = df_fat[df_fat['Processo'].isin(lista_faltantes)]
    print(df_faltantes[cols_existentes].head(20).to_string(index=False))

    # Verificar Logs de Validação para os faltantes
    print("\n" + "="*50)
    print("BUSCANDO NOS LOGS DE VALIDAÇÃO:")
    print("="*50)
    try:
        df_validacao = pd.read_excel(arquivo_comissoes, sheet_name='VALIDACAO')
        print(f"Logs de validação carregados: {len(df_validacao)} linhas")
        
        # Ajuste para nomes de colunas corretos (Nível, Mensagem, Contexto)
        col_msg = 'Mensagem' if 'Mensagem' in df_validacao.columns else 'mensagem'
        col_nivel = 'Nível' if 'Nível' in df_validacao.columns else 'nivel'
        col_ctx = 'Contexto' if 'Contexto' in df_validacao.columns else 'contexto'
        
        # Filtrar logs de aviso sobre regras
        avisos_regras = df_validacao[df_validacao[col_msg].astype(str).str.contains('Nenhuma regra', case=False, na=False)]
        
        if not avisos_regras.empty:
            print(f"\nEncontrados {len(avisos_regras)} avisos de 'Nenhuma regra encontrada'. Primeiros 20:")
            print(avisos_regras[[col_msg, col_ctx]].head(20).to_string(index=False))
        else:
            print("Nenhum aviso específico de 'Nenhuma regra' encontrado.")

    except Exception as e:
        print(f"Erro ao ler aba VALIDACAO: {e}")
