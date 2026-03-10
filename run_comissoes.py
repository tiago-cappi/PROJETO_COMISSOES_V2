#!/usr/bin/env python3
"""
Script de execução interativa do robô de comissões.

Modo terminal: resolve empates de atribuição via prompt interativo.
Uso:
    python run_comissoes.py
    python run_comissoes.py --mes 10 --ano 2025
    python run_comissoes.py --mes 10 --ano 2025 --verbose
"""

import os
import sys
import argparse
from datetime import datetime

# Garantir que o diretório raiz do projeto esteja no PATH
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execução interativa do robô de comissões (modo terminal)."
    )
    parser.add_argument("--mes", type=int, help="Mês de apuração (1-12)")
    parser.add_argument("--ano", type=int, help="Ano de apuração (ex: 2025)")
    parser.add_argument(
        "--verbose", action="store_true", help="Ativar logs detalhados"
    )
    return parser.parse_args()


def _solicitar_mes_ano(mes_cli: int | None, ano_cli: int | None) -> tuple[int, int]:
    """Retorna (mes, ano) vindos de CLI ou solicitando interativamente."""
    if (
        isinstance(mes_cli, int)
        and 1 <= mes_cli <= 12
        and isinstance(ano_cli, int)
        and 2000 < ano_cli < 2100
    ):
        return mes_cli, ano_cli

    now = datetime.now()
    default_mes = now.month - 1 if now.month > 1 else 12
    default_ano = now.year if now.month > 1 else now.year - 1

    while True:
        try:
            ano_input = input(f"Ano de apuração [{default_ano}]: ").strip()
            ano = int(ano_input) if ano_input else default_ano
            if 2000 < ano < 2100:
                break
            print("Ano inválido. Tente novamente.")
        except ValueError:
            print("Valor inválido. Digite um número.")

    while True:
        try:
            mes_input = input(f"Mês de apuração (1-12) [{default_mes}]: ").strip()
            mes = int(mes_input) if mes_input else default_mes
            if 1 <= mes <= 12:
                break
            print("Mês inválido. Tente 1 a 12.")
        except ValueError:
            print("Valor inválido. Digite um número.")

    return mes, ano


def main() -> None:
    args = _parse_args()

    if args.verbose:
        os.environ["COMISSOES_VERBOSE"] = "1"

    mes, ano = _solicitar_mes_ano(args.mes, args.ano)
    print(f"\n{'='*60}")
    print(f"  Robô de Comissões — Modo Terminal")
    print(f"  Período: {mes:02d}/{ano}")
    print(f"{'='*60}\n")

    # Executar preparador de dados
    try:
        import preparar_dados_mensais

        print("[1/3] Preparando dados mensais...")
        if not preparar_dados_mensais.run_preparador(mes, ano):
            print("ERRO: preparar_dados_mensais falhou. Abortando.")
            sys.exit(1)
        print("      Dados preparados com sucesso.\n")
    except Exception as exc:
        print(f"ERRO ao preparar dados: {exc}")
        sys.exit(1)

    # Instanciar e executar com modo_terminal=True
    from calculo_comissoes import CalculoComissao

    print("[2/3] Inicializando robô (modo terminal)...")
    calculadora = CalculoComissao(modo_terminal=True)
    calculadora.params["mes_apuracao"] = mes
    calculadora.params["ano_apuracao"] = ano

    print("[3/3] Executando cálculo de comissões...\n")
    calculadora.executar()

    print(f"\n{'='*60}")
    print("  Execução concluída.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
