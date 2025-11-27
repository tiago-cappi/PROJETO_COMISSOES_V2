"""
Script para atualizar categorias no gerador de dados de teste.
Substitui categorias fictícias/antigas por categorias reais fornecidas pelo usuário.
"""
import re

# Mapeamento de categorias antigas -> reais
SUBSTITUICOES = {
    # Analisador Fixo > Falco -> Detector Portátil > MicroClip  
    ('"Analisador Fixo"', '"Falco"'): ('"Detector Portátil"', '"MicroClip"'),
    ("'Analisador Fixo'", "'Falco'"): ("'Detector Portátil'", "'MicroClip'"),
    
    # Analisador Portátil > Acessório -> Detector Portátil > Sensor
    ('"Analisador Portátil"', '"Acessório"'): ('"Detector Portátil"', '"Sensor"'),
    ("'Analisador Portátil'", "'Acessório'"): ("'Detector Portátil'", "'Sensor'"),
    
    # Equipamento Amostragem > ISCO -> Medidor de Vazão Fixo > ADP
    ('"Equipamento Amostragem"', '"ISCO"'): ('"Medidor de Vazão Fixo"', '"ADP"'),
    ("'Equipamento Amostragem'", "'ISCO'"): ("'Medidor de Vazão Fixo'", "'ADP'"),
    
    # Sonda Multiparâmetros > EXO/YSI -> Amostrador Diversos > Acessório
    ('"Sonda Multiparâmetros"', '"EXO"'): ('"Amostrador Diversos"', '"Acessório"'),
    ("'Sonda Multiparâmetros'", "'EXO'"): ("'Amostrador Diversos'", "'Acessório'"),
    ('"Sonda Multiparâmetros"', '"YSI"'): ('"Amostrador Diversos"', '"Acessório"'),
    ("'Sonda Multiparâmetros'", "'YSI'"): ("'Amostrador Diversos'", "'Acessório'"),
    
    # Sistema Remediação > QED -> Analisador Portátil > GEM
    ('"Sistema Remediação"', '"QED"'): ('"Analisador Portátil"', '"GEM"'),
    ("'Sistema Remediação'", "'QED'"): ("'Analisador Portátil'", "'GEM'"),
    
    # Sistema Remediação > Thermo -> Analisador Diversos > Acessório
    ('"Sistema Remediação"', '"Thermo"'): ('"Analisador Diversos"', '"Acessório"'),
    ("'Sistema Remediação'", "'Thermo'"): ("'Analisador Diversos'", "'Acessório'"),
    
    # Detector Portátil > MicroClip (já existe, manter)
    
    # Detector Fixo > E3 Point -> Detector Portátil > MicroClip
    ('"Detector Fixo"', '"E3 Point"'): ('"Detector Portátil"', '"MicroClip"'),
    ("'Detector Fixo'", "'E3 Point'"): ("'Detector Portátil'", "'MicroClip'"),
}

# Ler arquivo
with open('tests/geradores_dados/gerar_todos_dados_teste.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Aplicar substituições
modificados = 0
for (grupo_antigo, subgrupo_antigo), (grupo_novo, subgrupo_novo) in SUBSTITUICOES.items():
    # Padrão: grupo=...  subgrupo=...
    padrao = f'grupo={grupo_antigo},?\\s+subgrupo={subgrupo_antigo}'
    substituto = f'grupo={grupo_novo},\n            subgrupo={subgrupo_novo}'
    
    count_antes = conteudo.count(grupo_antigo)
    conteudo = re.sub(padrao, substituto, conteudo)
    count_depois = conteudo.count(grupo_antigo)
    
    if count_antes != count_depois:
        modificados += (count_antes - count_depois)
        print(f"✓ Substituiu {count_antes - count_depois}x: {grupo_antigo}/{subgrupo_antigo} -> {grupo_novo}/{subgrupo_novo}")

# Salvar
with open('tests/geradores_dados/gerar_todos_dados_teste.py', 'w', encoding='utf-8') as f:
    f.write(conteudo)

print(f"\n✅ Total: {modificados} substituições aplicadas")
