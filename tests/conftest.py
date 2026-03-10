"""
Fixtures globais da suíte de testes do Robô de Comissões.

Este módulo fornece fixtures compartilhadas por todos os testes,
incluindo caminhos de referência e helpers utilitários.
"""
import os
import sys
from pathlib import Path

import pytest

# ──────────────────────────────────────────────────────────────────────
# Garantir que a raiz do projeto esteja no sys.path
# ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ──────────────────────────────────────────────────────────────────────
# Fixtures de caminhos
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Caminho absoluto da raiz do projeto."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def config_path(project_root) -> Path:
    """Caminho do arquivo de regras de negócio real."""
    return project_root / "config" / "REGRAS_COMISSOES.xlsx"


@pytest.fixture(scope="session")
def dados_entrada_path(project_root) -> Path:
    """Caminho da pasta de dados de entrada."""
    return project_root / "dados_entrada"


# ──────────────────────────────────────────────────────────────────────
# Helper: carregar CSV de fixture local
# ──────────────────────────────────────────────────────────────────────

def load_fixture_csv(test_file: str, filename: str):
    """
    Carrega um CSV de fixture relativo ao arquivo de teste que o chamou.

    Uso dentro de um teste:
        from tests.conftest import load_fixture_csv
        df = load_fixture_csv(__file__, "config_colaboradores.csv")

    Parâmetros:
        test_file: __file__ do módulo de teste chamador
        filename: nome do arquivo CSV dentro da subpasta fixtures/

    Retorna:
        pd.DataFrame carregado
    """
    import pandas as pd

    fixtures_dir = Path(test_file).resolve().parent / "fixtures"
    filepath = fixtures_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Fixture não encontrado: {filepath}\n"
            f"Verifique se o arquivo '{filename}' existe em {fixtures_dir}"
        )
    return pd.read_csv(filepath)
