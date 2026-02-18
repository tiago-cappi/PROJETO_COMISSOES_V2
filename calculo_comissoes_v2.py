#!/usr/bin/env python3
"""
calculo_comissoes_v2.py - Entry Point para Metodologia V2 de Comissões

Este script é o ponto de entrada CLI para executar o cálculo de comissões
usando a Metodologia V2 (simplificada, baseada em degraus por colaborador).

É completamente independente do calculo_comissoes.py original.

Uso:
    python calculo_comissoes_v2.py --mes 1 --ano 2026
    python calculo_comissoes_v2.py --mes 1 --ano 2026 --output resultado_customizado.xlsx
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Garantir que o diretório raiz está no path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.metodo_v2 import OrchestratorV2


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def print_banner():
    """Imprime banner do sistema."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        CÁLCULO DE COMISSÕES - METODOLOGIA V2 (SIMPLIFICADA)         ║
║                                                                      ║
║   Sistema de comissões baseado em degraus por colaborador           ║
║   com fator de correção (FC) proporcional à meta de faturamento     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_resumo(df_resumo):
    """Imprime resumo dos resultados no console."""
    if df_resumo.empty:
        print("\n⚠️  Nenhum resultado calculado.")
        return
    
    print("\n" + "=" * 80)
    print("                         RESUMO DAS COMISSÕES V2")
    print("=" * 80)
    
    total_comissao = df_resumo["comissao_total"].sum()
    
    for _, row in df_resumo.iterrows():
        nome = row["nome_colaborador"]
        meta = row["meta_faturamento"]
        realizado = row["faturamento_realizado"]
        fc = row["fc_calculado_pct"]
        taxa = row["taxa_comissao_aplicada_pct"]
        comissao = row["comissao_total"]
        tipo = row["tipo_degrau"]
        
        print(f"\n👤 {nome}")
        print(f"   Meta: R$ {meta:,.2f} | Realizado: R$ {realizado:,.2f}")
        print(f"   FC: {fc:.1f}% | Taxa: {taxa:.2f}% | Tipo: {tipo}")
        print(f"   💰 Comissão: R$ {comissao:,.2f}")
    
    print("\n" + "-" * 80)
    print(f"   TOTAL DE COMISSÕES: R$ {total_comissao:,.2f}")
    print("=" * 80 + "\n")


def main():
    """Função principal."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Calcula comissões usando a Metodologia V2 (simplificada)."
    )
    parser.add_argument(
        "--mes", "-m",
        type=int,
        required=True,
        help="Mês de referência (1-12)"
    )
    parser.add_argument(
        "--ano", "-a",
        type=int,
        required=True,
        help="Ano de referência"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/REGRAS_COMISSOES_V2.xlsx",
        help="Caminho para arquivo de configuração V2"
    )
    parser.add_argument(
        "--dados", "-d",
        type=str,
        default="dados_entrada/Analise_Comercial_Completa.xlsx",
        help="Caminho para arquivo de dados comerciais"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Caminho para arquivo de saída (default: dados_saida/Resultado_Comissoes_V2_YYYY-MM.xlsx)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verboso (debug)"
    )
    
    args = parser.parse_args()
    
    # Ajustar nível de log se verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validar argumentos
    if not 1 <= args.mes <= 12:
        logger.error(f"Mês inválido: {args.mes}. Deve ser entre 1 e 12.")
        sys.exit(1)
    
    if args.ano < 2000 or args.ano > 2100:
        logger.error(f"Ano inválido: {args.ano}.")
        sys.exit(1)
    
    # Definir output padrão se não especificado
    if args.output is None:
        args.output = f"dados_saida/Resultado_Comissoes_V2_{args.ano}-{args.mes:02d}.xlsx"
    
    print(f"📅 Período: {args.mes:02d}/{args.ano}")
    print(f"📁 Config: {args.config}")
    print(f"📁 Dados: {args.dados}")
    print(f"📁 Saída: {args.output}")
    print()
    
    try:
        # Criar orquestrador
        orchestrator = OrchestratorV2(
            config_path=args.config,
            comercial_path=args.dados,
        )
        
        # Executar cálculo
        start = datetime.now()
        df_resumo, df_detalhes = orchestrator.executar(mes=args.mes, ano=args.ano)
        elapsed = (datetime.now() - start).total_seconds()
        
        # Salvar resultados
        output_path = orchestrator.salvar_resultados(args.output)
        
        # Exibir resumo
        print_resumo(df_resumo)
        
        print(f"✅ Cálculo concluído em {elapsed:.2f} segundos")
        print(f"📄 Resultados salvos em: {output_path}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        print(f"\n❌ ERRO: {e}")
        print("\nVerifique se os arquivos de configuração existem:")
        print(f"  - {args.config}")
        print(f"  - {args.dados}")
        return 1
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        print(f"\n❌ ERRO DE VALIDAÇÃO: {e}")
        return 1
        
    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
        print(f"\n❌ ERRO INESPERADO: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
