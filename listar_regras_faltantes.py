import pandas as pd
import re

arquivo_comissoes = 'Comissoes_Calculadas_20251127_125015.xlsx'

try:
    df_validacao = pd.read_excel(arquivo_comissoes, sheet_name='VALIDACAO')
    
    # Ajuste para nomes de colunas corretos (Nível, Mensagem, Contexto)
    col_msg = 'Mensagem' if 'Mensagem' in df_validacao.columns else 'mensagem'
    col_ctx = 'Contexto' if 'Contexto' in df_validacao.columns else 'contexto'
    
    # Filtrar logs de aviso sobre regras
    avisos = df_validacao[df_validacao[col_msg].astype(str).str.contains('Nenhuma regra', case=False, na=False)]
    
    combinações = set()
    
    for _, row in avisos.iterrows():
        ctx = str(row[col_ctx])
        # Extrair dicionário do contexto (string representation)
        # Ex: {'linha': 'Remediação', 'grupo': 'Sistema Remediação', ...}
        match = re.search(r"\{.*\}", ctx)
        if match:
            combinações.add(match.group(0))
            
    with open('regras_faltantes.txt', 'w', encoding='utf-8') as f:
        f.write(f"Encontradas {len(combinações)} combinações únicas sem regra:\n")
        for c in sorted(list(combinações)):
            f.write(c + "\n")
    print("Arquivo regras_faltantes.txt gerado com sucesso.")
        
except Exception as e:
    print(f"Erro: {e}")
