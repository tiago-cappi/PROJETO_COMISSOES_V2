"""src.core.fc_escada

Regra de "escada" (degraus) para aplicar um multiplicador de comissão a partir

- de um score de performance (FC ou FCMP) em modo rampa, e
- de uma configuração por cargo carregada do REGRAS_COMISSOES.xlsx.

A aba esperada é `FC_ESCADA_CARGOS` (Opção A), com as colunas:
- cargo: str
- modo: "RAMPA" | "ESCADA"
- num_degraus: int >= 2
- piso_pct: 0..100 (percentual do teto; ex: 50 = 50% do teto)

Regras:
- Sem tolerância: para subir de degrau, precisa atingir o gatilho exatamente.
- O topo (multiplicador=1.0) só ocorre se performance >= 1.0.
- Se o cargo não estiver configurado, faz fallback para RAMPA (multiplicador=performance).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

import pandas as pd


_VALID_MODES = {"RAMPA", "ESCADA"}


@dataclass(frozen=True)
class FcEscadaCargoConfig:
    """Configuração de escada por cargo."""

    cargo: str
    modo: str
    num_degraus: int
    piso: float  # 0..1 (fração do teto)


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    try:
        return str(v).strip()
    except Exception:
        return ""


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        if isinstance(v, str):
            v = v.strip().replace("%", "")
        if v == "":
            return None
        return float(v)
    except Exception:
        return None


def _to_int(v: Any) -> Optional[int]:
    f = _to_float(v)
    if f is None:
        return None
    try:
        return int(round(f))
    except Exception:
        return None


def load_fc_escada_cargos(df: Optional[pd.DataFrame]) -> Dict[str, FcEscadaCargoConfig]:
    """Carrega configurações de escada por cargo a partir da aba FC_ESCADA_CARGOS.

    Args:
        df: DataFrame da aba FC_ESCADA_CARGOS.

    Returns:
        Dict {cargo_normalizado: FcEscadaCargoConfig}

    Notes:
        - Chave é o cargo em lowercase/strip, para facilitar matches.
        - Linhas inválidas são ignoradas (fail-safe).
    """

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return {}

    expected_cols = {"cargo", "modo", "num_degraus", "piso_pct"}
    cols = {c.strip() for c in df.columns.astype(str)}
    if not expected_cols.issubset(cols):
        # Aba existe, mas não tem contrato mínimo — ignorar.
        return {}

    out: Dict[str, FcEscadaCargoConfig] = {}

    for _, row in df.iterrows():
        cargo_raw = _to_str(row.get("cargo"))
        if not cargo_raw:
            continue

        modo = _to_str(row.get("modo")).upper() or "RAMPA"
        if modo not in _VALID_MODES:
            modo = "RAMPA"

        num_degraus = _to_int(row.get("num_degraus"))
        if num_degraus is None:
            num_degraus = 2
        num_degraus = max(2, int(num_degraus))

        piso_pct = _to_float(row.get("piso_pct"))
        if piso_pct is None:
            piso_pct = 0.0

        # piso_pct pode vir como 0..1 por erro do usuário; normalizar.
        if 0.0 <= piso_pct <= 1.0:
            piso = float(piso_pct)
        else:
            piso = float(piso_pct) / 100.0

        # Clamp seguro
        if piso < 0.0:
            piso = 0.0
        if piso > 1.0:
            piso = 1.0

        key = cargo_raw.strip().lower()
        out[key] = FcEscadaCargoConfig(
            cargo=cargo_raw.strip(),
            modo=modo,
            num_degraus=num_degraus,
            piso=piso,
        )

    return out


def aplicar_fc_escada(
    performance: float,
    cargo: str,
    configs_por_cargo: Mapping[str, FcEscadaCargoConfig],
) -> Tuple[float, Dict[str, Any]]:
    """Aplica regra de escada (ou rampa) e devolve multiplicador + detalhes.

    Args:
        performance: FC (item) ou FCMP (processo), calculado em modo rampa.
        cargo: Cargo do colaborador.
        configs_por_cargo: Dict de configs carregado por `load_fc_escada_cargos`.

    Returns:
        (multiplicador_aplicado, detalhes)

    Detalhes contém:
        - modo: "RAMPA"|"ESCADA"
        - cargo
        - performance_rampa
        - multiplicador
        - piso
        - num_degraus
        - degrau_indice (0..N-1)
    """

    cargo_norm = (cargo or "").strip().lower()
    cfg = configs_por_cargo.get(cargo_norm)

    perf = 0.0
    try:
        perf = float(performance)
    except Exception:
        perf = 0.0

    if perf < 0.0:
        perf = 0.0

    if cfg is None or cfg.modo == "RAMPA":
        return perf, {
            "modo": "RAMPA",
            "cargo": cargo,
            "performance_rampa": perf,
            "multiplicador": perf,
            "num_degraus": None,
            "piso": None,
            "degrau_indice": None,
        }

    # ESCADA
    n = max(2, int(cfg.num_degraus))
    piso = float(cfg.piso)

    # Topo só quando perf >= 1.0
    if perf >= 1.0:
        i = n - 1
    else:
        # Sem tolerância: floor exato.
        # Ex: n=3 -> intervalos=2 -> perf*2 em [0,2)
        i = int(perf * (n - 1))
        if i < 0:
            i = 0
        if i > n - 2:
            i = n - 2

    multiplicador = piso + (i * (1.0 - piso) / (n - 1))

    # Clamp final (defensivo)
    if multiplicador < 0.0:
        multiplicador = 0.0
    if multiplicador > 1.0:
        multiplicador = 1.0

    return multiplicador, {
        "modo": "ESCADA",
        "cargo": cargo,
        "performance_rampa": perf,
        "multiplicador": multiplicador,
        "num_degraus": n,
        "piso": piso,
        "degrau_indice": i,
    }
