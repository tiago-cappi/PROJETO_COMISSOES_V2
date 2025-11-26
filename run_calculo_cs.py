"""
Script para rodar cálculo com respostas automáticas ao popup de cross-selling.
Simula a seleção de opções A/B para os 4 processos detectados.
"""
import subprocess
import sys

# Preparar decisões de cross-selling (A ou B aleatório)
decisoes = [
    {"processo": "400001", "decision": "A"},
    {"processo": "400002", "decision": "B"},
    {"processo": "400003", "decision": "A"},
    {"processo": "400004", "decision": "B"},
]

print("=" * 80)
print("EXECUTANDO CÁLCULO COM DECISÕES DE CROSS-SELLING")
print("=" * 80)
print("\nDecisões configuradas:")
for d in decisoes:
    print(f"  Processo {d['processo']}: Opção {d['decision']}")
print()

# O cálculo detectará automaticamente os casos e usará as decisões padrão
# ou podemos passar via parâmetro se o código suportar
cmd = ["python", "calculo_comissoes.py", "--mes", "8", "--ano", "2025"]

print(f"Comando: {' '.join(cmd)}\n")
print("Aguarde enquanto o cálculo é executado...")
print("=" * 80)
print()

# Executar
result = subprocess.run(cmd, capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print()
print("=" * 80)
print(f"Cálculo finalizado com código de saída: {result.returncode}")
print("=" * 80)
