import pandas as pd
import os

def update_goals():
    print("=" * 80)
    print("ATUALIZADOR DE METAS - REGRAS_COMISSOES.xlsx")
    print("=" * 80)

    config_path = os.path.join("config", "Regras_Comissoes.xlsx")
    if not os.path.exists(config_path):
        print(f"❌ Arquivo não encontrado: {config_path}")
        return

    print(f"📂 Carregando: {config_path}")
    xls = pd.ExcelFile(config_path)
    
    # Dicionário para armazenar os DataFrames de todas as abas
    sheets = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}

    # =================================================================================
    # 1. ATUALIZAR METAS DE APLICAÇÃO (LINHA/TIPO)
    # =================================================================================
    # Estimativas baseadas no script gerar_todos_dados_teste.py para Ago/Set 2025
    # Cenários desejados:
    # - SSO: Atingimento ~100%
    # - Hidrologia: Atingimento > 100% (Superação)
    # - Remediação: Atingimento < 80% (Baixo)
    
    if "METAS_APLICACAO" in sheets:
        df_meta = sheets["METAS_APLICACAO"]
        
        # Definir metas mensais para Ago/Set/Out
        # Estrutura: (Linha, Tipo) -> Meta Mensal
        metas_base = {
            ("SSO", "Produto"): 150000,      # Realizado est: ~150k
            ("SSO", "Serviço"): 50000,       # Realizado est: ~50k
            ("SSO", "Reposição"): 30000,
            ("Hidrologia", "Produto"): 80000, # Realizado est: ~120k (Superação)
            ("Hidrologia", "Serviço"): 20000,
            ("Remediação", "Produto"): 200000, # Realizado est: ~100k (Baixo)
            ("Remediação", "Serviço"): 50000,
        }

        print("\n🔄 Atualizando METAS_APLICACAO...")
        # Iterar e atualizar
        for idx, row in df_meta.iterrows():
            chave = (row["linha"], row["tipo_mercadoria"])
            if chave in metas_base:
                nova_meta = metas_base[chave]
                df_meta.at[idx, "valor_meta"] = nova_meta
                print(f"   - {chave}: Meta ajustada para R$ {nova_meta:,.2f}")
        
        sheets["METAS_APLICACAO"] = df_meta

    # =================================================================================
    # 2. ATUALIZAR METAS INDIVIDUAIS (COLABORADORES)
    # =================================================================================
    if "METAS_INDIVIDUAIS" in sheets:
        df_indiv = sheets["METAS_INDIVIDUAIS"]
        
        # Metas individuais para atingir FCs específicos
        metas_indiv = {
            "Andrey Andrade": 100000,  # Consultor Interno SSO
            "Dener Martins": 50000,    # Consultor Interno Hidro
            "André Camargo": 200000,   # Externo SSO
            "Mateus Machado": 150000,  # Externo Hidro
            "Leonardo Carmo": 250000,  # Externo Remediação (Meta alta -> FC baixo)
        }

        print("\n🔄 Atualizando METAS_INDIVIDUAIS...")
        for idx, row in df_indiv.iterrows():
            colab = row["colaborador"]
            # Remover sufixos/prefixos se houver para match simples
            nome_match = None
            for k in metas_indiv:
                if k in colab:
                    nome_match = k
                    break
            
            if nome_match:
                nova_meta = metas_indiv[nome_match]
                df_indiv.at[idx, "valor_meta"] = nova_meta
                print(f"   - {colab}: Meta ajustada para R$ {nova_meta:,.2f}")

        sheets["METAS_INDIVIDUAIS"] = df_indiv

    # =================================================================================
    # 3. SALVAR ARQUIVO
    # =================================================================================
    print("\n💾 Salvando alterações...")
    with pd.ExcelWriter(config_path, engine='openpyxl') as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print("✅ REGRAS_COMISSOES.xlsx atualizado com sucesso!")

if __name__ == "__main__":
    update_goals()
