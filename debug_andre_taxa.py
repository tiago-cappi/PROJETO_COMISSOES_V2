"""Script para debugar a taxa de André Caramello."""
import pandas as pd
from src.metodo_v2.config_loader_v2 import ConfigLoaderV2
from src.metodo_v2.cc_calculator_v2 import CCCalculatorV2

loader = ConfigLoaderV2('config/REGRAS_COMISSOES_V2.xlsx')
config = loader.load()

# config é um dict, precisamos acessar os colaboradores
colaboradores = config.get('colaboradores', config)
if isinstance(colaboradores, dict) and 'colaboradores' in colaboradores:
    colaboradores = colaboradores['colaboradores']

print("=" * 60)
print("VERIFICANDO MODELO")
print("=" * 60)

# Ver faixas do André Caramello para CC 2.5.031
for nome, colab in colaboradores.items():
    if 'andré caramello' in nome.lower():
        print(f'Colaborador: {nome}')
        print(f'  Cargo: {colab.cargo}')
        for regra in colab.regras_cc:
            if regra.centro_custo == '2.5.031':
                print(f'  Regra CC {regra.centro_custo}:')
                for i, f in enumerate(regra.faixas):
                    print(f'    Faixa {i+1}: limite={f.limite_inferior}, taxa={f.taxa_comissao_pct}%, op_inf={f.operador_inferior}, limite_sup={f.limite_superior}, op_sup={f.operador_superior}')
                
                print()
                print('  Teste aplica_ao_faturamento(80):')
                for i, f in enumerate(regra.faixas):
                    aplica = f.aplica_ao_faturamento(80)
                    print(f'    Faixa {i+1}: {aplica}')
                
                print()
                print(f'  Taxa para R$80: {regra.get_taxa_para_faturamento(80)}%')

print()
print("=" * 60)
print("SIMULANDO CÁLCULO")
print("=" * 60)

# Criar dados de teste
df_test = pd.DataFrame([
    {'Processo': 'TESTE-001', 'Centro Custo-pedido': '2.5.031', 'Valor Realizado': 30.0, 'Consultor Interno': '', 'Representante-pedido': ''},
    {'Processo': 'TESTE-002', 'Centro Custo-pedido': '2.5.031', 'Valor Realizado': 20.0, 'Consultor Interno': '', 'Representante-pedido': ''},
    {'Processo': 'TESTE-003', 'Centro Custo-pedido': '2.5.031', 'Valor Realizado': 30.0, 'Consultor Interno': '', 'Representante-pedido': ''},
])

# Carregar cargos
df_cargos = pd.read_excel('config/REGRAS_COMISSOES_V2.xlsx', 'CARGOS_V2')
df_colaboradores_xlsx = pd.read_excel('config/REGRAS_COMISSOES_V2.xlsx', 'COLABORADORES_V2')

print()
print("DF CARGOS:")
print(df_cargos.to_string())

# Rodar calculador
calc = CCCalculatorV2(colaboradores, df_cargos, df_colaboradores_xlsx)

print()
print("CARGOS_TIPO do calculador:")
print(calc._cargos_tipo)

df_resumo, df_detalhes = calc.calcular(df_test)

print()
print("DF RESUMO:")
print(df_resumo.to_string())

print()
print("DF DETALHES:")
print(df_detalhes.to_string() if not df_detalhes.empty else "VAZIO")
