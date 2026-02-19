"""
conftest.py — Fixtures globais e hook de geração do relatório de auditoria.

Após todos os testes executarem, gera automaticamente:
    tests_comissoes/relatorios/auditoria_testes_YYYY-MM-DD_HHMMSS.xlsx

Cada teste pode usar a fixture `audit` para registrar verificações
com cálculos detalhados visíveis no relatório Excel final.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Garantir que a raiz do projeto está no sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests_comissoes.audit import AuditCollector, AuditReportGenerator


# =========================================================================
# Variável global do gerador de relatório (compartilhada entre sessões)
# =========================================================================
_report_generator = AuditReportGenerator()


# =========================================================================
# FIXTURE: audit
# =========================================================================
@pytest.fixture
def audit(request) -> AuditCollector:
    """Fixture que fornece um coletor de auditoria por teste.

    Uso:
        def test_algo(audit):
            audit.set_contexto(modulo="FC Escada", cenario="Piso 50%")
            audit.verificar(
                descricao="Multiplicador no degrau 0",
                formula="piso + (0 × (1-piso)/(n-1))",
                entradas={"performance": 0.1, "piso": 0.5, "n": 4},
                esperado=0.5,
                real=resultado_real,
            )
    """
    test_name = request.node.name
    collector = AuditCollector(test_name)
    yield collector
    # Após o teste, coletar verificações no gerador global
    if collector.verificacoes:
        _report_generator.adicionar(collector.verificacoes)


# =========================================================================
# HOOK: gerar relatório após todos os testes
# =========================================================================
def pytest_sessionfinish(session, exitstatus):
    """Hook executado após todos os testes finalizarem."""
    if not _report_generator.todas_verificacoes:
        return

    output_dir = os.path.join(
        str(Path(__file__).resolve().parent),
        "relatorios",
    )
    filepath = _report_generator.gerar_relatorio(output_dir)

    total = len(_report_generator.todas_verificacoes)
    passou = sum(1 for v in _report_generator.todas_verificacoes if v.passou)
    falhou = total - passou

    print(f"\n{'=' * 70}")
    print(f"  [AUDIT] RELATORIO DE AUDITORIA GERADO")
    print(f"  [PATH]  {filepath}")
    print(f"  [OK] Passou: {passou}  |  [FAIL] Falhou: {falhou}  |  Total: {total}")
    print(f"{'=' * 70}\n")
