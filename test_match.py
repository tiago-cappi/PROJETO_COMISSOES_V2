import pandas as pd

# Simular o que acontece no código
cross_df = pd.DataFrame({
    'colaborador': ['Mateus Machado', 'André Camargo', 'Leonardo Camargo'],
    'taxa_cross_selling_pct': [1, 1, 1]
})

# Testar o match como no código
gerente_padrao = "André Camargo"  # Vindo do alias_map

print(f"Procurando: '{gerente_padrao}'")
print(f"Colaboradores em CROSS_SELLING: {cross_df['colaborador'].tolist()}")

mask_cs = (
    cross_df["colaborador"]
    .astype(str)
    .str.strip()
    .str.lower()
    == str(gerente_padrao).strip().lower()
)

print(f"\nMask: {mask_cs.tolist()}")

row_cs = cross_df[mask_cs]
print(f"Match encontrado? {not row_cs.empty}")

if not row_cs.empty:
    taxa = float(row_cs.iloc[0].get("taxa_cross_selling_pct", 0.0))
    print(f"Taxa: {taxa}")
else:
    print("Nenhum match encontrado!")
    # Mostrar os valores lowercase para debug
    print(f"\nValores lowercase no DataFrame:")
    for val in cross_df['colaborador'].str.lower():
        print(f"  '{val}'")
    print(f"Valor buscado lowercase: '{gerente_padrao.lower()}'")
