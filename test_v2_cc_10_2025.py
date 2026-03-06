#!/usr/bin/env python3
"""
Teste V2 — Recebimento (modo Centro de Custo) — 10/2025.

Executa SOMENTE o fluxo de recebimento para os colaboradores que recebem
por recebimento (André Caramello, Alessandro Cappi, Neimar), no modo CC.

Requer que o OrchestratorV2 rode primeiro para obter o df_comercial (AC)
filtrado — necessário para vincular pagamentos a Centros de Custo.
"""

import io
import logging
import os
import sys

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

import pandas as pd
from src.metodo_v2.orchestrator_v2 import OrchestratorV2, MODO_CENTRO_CUSTO
from src.metodo_v2.recebimento_v2.recebimento_orchestrator_v2 import RecebimentoOrchestratorV2


def main():
    mes, ano = 10, 2025

    print("=" * 80)
    print(f"  TESTE V2 — RECEBIMENTO (modo CC) — {mes:02d}/{ano}")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Rodar Faturamento apenas para obter o _df_comercial (AC filtrado)
    # -------------------------------------------------------------------------
    print("\n>>> Carregando dados de faturamento (AC) para vincular CCs...\n")
    orchestrator = OrchestratorV2(
        config_path="config/REGRAS_COMISSOES_V2.xlsx",
        comercial_path="dados_entrada/Analise_Comercial_Completa.xlsx",
    )
    # Executar faturamento CC — resultado será usado como referência de CCs
    df_resumo_fat, _ = orchestrator.executar(mes=mes, ano=ano, modo_calculo=MODO_CENTRO_CUSTO)
    df_ac = orchestrator._df_comercial  # AC filtrado (FATURADO + mês/ano)

    print(f"\n>>> AC carregada: {len(df_ac)} registros FATURADOS em {mes:02d}/{ano}")

    # -------------------------------------------------------------------------
    # 2. Executar Recebimento V2 (modo CC)
    # -------------------------------------------------------------------------
    print("\n>>> Executando cálculo de RECEBIMENTO (modo CC)...\n")
    rec_orch = RecebimentoOrchestratorV2(base_path=".", modo_cc=True)

    if not rec_orch.carregar_configuracao():
        print("  [ERRO] Falha ao carregar configuração de recebimento")
        return

    # Listar colaboradores de recebimento
    colabs_rec = rec_orch.obter_colaboradores_recebimento()
    print(f"  Colaboradores de recebimento ({len(colabs_rec)}):")
    for c in colabs_rec:
        ccs = [r.centro_custo for r in c.regras_cc] if hasattr(c, 'regras_cc') and c.regras_cc else []
        print(f"    - {c.nome} | taxa_adiantamento={c.taxa_adiantamento_pct}% | CCs={ccs}")

    adiantamentos, reconciliacoes, output_path = rec_orch.processar_mes(
        mes=mes, ano=ano, df_faturamento=df_ac
    )

    # -------------------------------------------------------------------------
    # 3. Resultados
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  RESULTADOS — RECEBIMENTO (modo CC)")
    print("=" * 80)

    if adiantamentos:
        total_rec = sum(a.comissao_calculada for a in adiantamentos)
        print(f"\n  Total de comissões: {len(adiantamentos)} registros")
        print(f"  Valor total: R$ {total_rec:,.2f}\n")

        # Agrupar por colaborador
        from collections import defaultdict
        por_colab = defaultdict(list)
        for a in adiantamentos:
            por_colab[a.colaborador_nome].append(a)

        for nome, resultados in sorted(por_colab.items()):
            subtotal = sum(r.comissao_calculada for r in resultados)
            print(f"  {nome} — R$ {subtotal:,.2f} ({len(resultados)} docs)")
            for r in resultados:
                print(
                    f"    Doc={r.documento_normalizado:>10} | "
                    f"Valor={r.valor_base:>12,.2f} | "
                    f"Taxa={r.percentual_aplicado:>5.1f}% | "
                    f"Comissão={r.comissao_calculada:>10,.2f} | "
                    f"Tipo={r.tipo_calculo} | "
                    f"Regra={r.regra_utilizada}"
                )
            print()
    else:
        print("\n  [Nenhum resultado de recebimento]")
        print("  ATENÇÃO: Resultado zero — investigar matching de documentos.")

    if reconciliacoes:
        total_aj = sum(r.ajuste for r in reconciliacoes)
        print(f"\n  Reconciliações: {len(reconciliacoes)} — Total ajustes: R$ {total_aj:,.2f}")
        for r in reconciliacoes:
            print(
                f"    {r.colaborador_nome:<22} | Doc={r.documento_normalizado} | "
                f"Adiant={r.comissao_adiantada:>10,.2f} | Real={r.comissao_real:>10,.2f} | "
                f"Ajuste={r.ajuste:>10,.2f} ({r.tipo_ajuste})"
            )

    if output_path:
        print(f"\n  Arquivo: {output_path}")

    # -------------------------------------------------------------------------
    # 4. Resumo Consolidado
    # -------------------------------------------------------------------------
    rec_total = sum(a.comissao_calculada for a in adiantamentos) if adiantamentos else 0
    aj_total = sum(r.ajuste for r in reconciliacoes) if reconciliacoes else 0

    print("\n" + "=" * 80)
    print("  RESUMO CONSOLIDADO — RECEBIMENTO CC")
    print("=" * 80)
    print(f"  Comissões por Recebimento: R$ {rec_total:,.2f}")
    print(f"  Ajustes de Reconciliação:  R$ {aj_total:,.2f}")
    print(f"  TOTAL:                     R$ {rec_total + aj_total:,.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
