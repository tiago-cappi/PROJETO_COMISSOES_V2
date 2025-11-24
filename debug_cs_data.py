import pandas as pd
import os

def check_cross_selling(mes, ano):
    base_path = os.getcwd()
    file_path = os.path.join(base_path, "Faturados.xlsx")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Checking file: {file_path}")
    # Faturados.xlsx usually has only one sheet or the first sheet is the data
    xls = pd.ExcelFile(file_path)
    sheet_name = xls.sheet_names[0]
    df_faturados = pd.read_excel(xls, sheet_name=sheet_name)
    
    if "Gerente Comercial-Pedido" not in df_faturados.columns:
        print("Column 'Gerente Comercial-Pedido' not found in FATURADOS")
        return
        
    # Filter potential cross-selling
    mask = df_faturados["Gerente Comercial-Pedido"].notna() & (df_faturados["Gerente Comercial-Pedido"] != "")
    df_cs = df_faturados[mask]
    
    print(f"Total rows with Gerente Comercial-Pedido: {len(df_cs)}")
    
    if len(df_cs) > 0:
        print("Sample rows:")
        print(df_cs[["Processo", "Gerente Comercial-Pedido", "Negócio", "Grupo", "Subgrupo"]].head())
        
    # Check ATRIBUICOES
    if "ATRIBUICOES" in xls.sheet_names:
        df_atribuicoes = pd.read_excel(xls, sheet_name="ATRIBUICOES")
        print(f"\nATRIBUICOES loaded: {len(df_atribuicoes)} rows")
        
        # Check if any of the potential CS are actually valid attributions
        # Logic: (Linha, Grupo, Subgrupo) -> Colaborador
        
        atribuicoes_map = {}
        for _, row in df_atribuicoes.iterrows():
            chave = (row["linha"], row["grupo"], row["subgrupo"])
            if chave not in atribuicoes_map:
                atribuicoes_map[chave] = []
            atribuicoes_map[chave].append(str(row["colaborador"]).strip())
            
        real_cs_count = 0
        for _, row in df_cs.iterrows():
            colaborador = str(row["Gerente Comercial-Pedido"]).strip()
            # We might need alias mapping here, but let's check exact match first
            chave = (row["Negócio"], row["Grupo"], row["Subgrupo"])
            
            is_attributed = False
            if chave in atribuicoes_map:
                # Check if collaborator is in the list (fuzzy match might be needed)
                # For now just check simple containment
                for attr_colab in atribuicoes_map[chave]:
                    if colaborador.lower() in attr_colab.lower() or attr_colab.lower() in colaborador.lower():
                        is_attributed = True
                        break
            
            if not is_attributed:
                real_cs_count += 1
                if real_cs_count <= 5:
                    print(f"Potential Cross-Selling: Processo={row['Processo']}, Colab={colaborador}, Linha={row['Negócio']}")

        print(f"\nEstimated Real Cross-Selling Cases: {real_cs_count}")

if __name__ == "__main__":
    check_cross_selling(8, 2025)
