"""Router para exposição do Banco de Dados Histórico (Master DB).

Este router provê endpoints para:
- Leitura paginada/filtrável do HISTORICO_COMISSOES_MASTER
- Visões agregadas para Saldos Negativos (DEVOLUCAO/RECONCILIACAO)
- Resumo final por colaborador (somatório do mês, incluindo adiantamentos)

Observação: o adapter apenas lê e formata dados; a lógica de negócio permanece no core.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/api/historico", tags=["Histórico"])


def _get_robo_root_path() -> Path:
    """Obtém o caminho raiz do robô a partir do módulo app.py do adapter."""
    try:
        # app.py injeta ROBO_ROOT_PATH no módulo global; import local para evitar ciclo no import do adapter.
        from app import ROBO_ROOT_PATH  # type: ignore

        return Path(ROBO_ROOT_PATH).resolve()
    except Exception:
        # fallback: duas pastas acima (adapter/routers -> adapter -> frontend -> raiz)
        return Path(__file__).parent.parent.parent.parent.resolve()


def _get_master_db_path() -> Path:
    robo_root = _get_robo_root_path()
    return (robo_root / "data" / "banco_dados" / "HISTORICO_COMISSOES_MASTER.xlsx").resolve()


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if pd.isna(value):
        return None
    s = str(value)
    return s


def _load_master_df() -> pd.DataFrame:
    master_path = _get_master_db_path()
    if not master_path.exists():
        # Não é erro; significa que ainda não houve escrita.
        return pd.DataFrame()

    try:
        df = pd.read_excel(master_path, sheet_name="HISTORICO")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler Master DB: {e}")

    return df


def _normalize_master_types(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    numeric_cols = [
        "Mes_Referencia",
        "Ano_Referencia",
        "Valor_Base",
        "TCMP",
        "FC",
        "Comissao_Calculada",
        "Fator_Devolucao",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Datas como string ISO para UI
    for col in ["Data_Execucao", "Data_Pagamento"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df


def _df_to_records_json_safe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converte DataFrame para list[dict] garantindo JSON-safe.

    Starlette/FastAPI não permite NaN/Inf em JSON ("Out of range float values are not JSON compliant").
    Como o Master DB vem do Excel/pandas, valores ausentes frequentemente aparecem como NaN.
    Este helper normaliza NaN/NaT/Inf para None, evitando crash do servidor.
    """
    if df is None or df.empty:
        return []

    df_safe = df.copy()

    # Normalizar +/-inf para NA
    df_safe = df_safe.replace([float("inf"), float("-inf")], pd.NA)

    # IMPORTANT: converter para object antes de inserir None,
    # caso contrário colunas float convertem None -> NaN.
    df_safe = df_safe.astype(object)

    # Normalizar NaN/NaT/NA para None
    df_safe = df_safe.where(pd.notna(df_safe), None)

    return df_safe.to_dict(orient="records")


def _apply_contains_filter(df: pd.DataFrame, column: str, value: Optional[str]) -> pd.DataFrame:
    if not value:
        return df
    if column not in df.columns:
        return df
    return df[df[column].astype(str).str.contains(str(value), case=False, na=False)]


def _apply_equals_filter(df: pd.DataFrame, column: str, value: Optional[str]) -> pd.DataFrame:
    if value is None or value == "":
        return df
    if column not in df.columns:
        return df
    return df[df[column].astype(str).str.strip() == str(value).strip()]


@router.get("/master")
async def get_master_historico(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000, le=2100),
    tipo_comissao: Optional[str] = Query(None),
    nome_colaborador: Optional[str] = Query(None),
    processo: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """Leitura paginada e filtrável do banco histórico (Master DB)."""
    df = _normalize_master_types(_load_master_df())

    if df.empty:
        return {"data": [], "total": 0, "page": page, "size": size, "columns": []}

    # Filtros
    if mes is not None and "Mes_Referencia" in df.columns:
        df = df[df["Mes_Referencia"].fillna(-1).astype(int) == int(mes)]
    if ano is not None and "Ano_Referencia" in df.columns:
        df = df[df["Ano_Referencia"].fillna(-1).astype(int) == int(ano)]

    df = _apply_equals_filter(df, "Tipo_Comissao", tipo_comissao)
    df = _apply_contains_filter(df, "Nome_Colaborador", nome_colaborador)
    df = _apply_contains_filter(df, "Processo", processo)

    # Ordenação
    if sort_by and sort_by in df.columns:
        ascending = sort_order == "asc"
        try:
            df = df.sort_values(by=sort_by, ascending=ascending)
        except Exception:
            pass

    total = len(df)
    start = (page - 1) * size
    end = start + size

    df_page = df.iloc[start:end]

    return {
        "data": _df_to_records_json_safe(df_page),
        "total": total,
        "page": page,
        "size": size,
        "columns": list(df.columns),
    }


@router.get("/saldos-negativos")
async def get_saldos_negativos(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    origem: str = Query("ALL", pattern="^(DEVOLUCAO|RECONCILIACAO|ALL)$"),
    size_itens: int = Query(2000, ge=1, le=10000),
):
    """Retorna visão limpa de saldos negativos do mês (DEVOLUCAO agora, RECONCILIACAO no futuro)."""
    df = _normalize_master_types(_load_master_df())
    if df.empty:
        return {"resumo_colaboradores": [], "itens": []}

    required_cols = ["Mes_Referencia", "Ano_Referencia", "Tipo_Comissao", "Nome_Colaborador", "Comissao_Calculada"]
    for c in required_cols:
        if c not in df.columns:
            raise HTTPException(status_code=500, detail=f"Master DB sem coluna obrigatória: {c}")

    df = df[df["Mes_Referencia"].fillna(-1).astype(int) == int(mes)]
    df = df[df["Ano_Referencia"].fillna(-1).astype(int) == int(ano)]

    tipos = ["DEVOLUCAO", "RECONCILIACAO"]
    if origem in ("DEVOLUCAO", "RECONCILIACAO"):
        tipos = [origem]

    df = df[df["Tipo_Comissao"].astype(str).isin(tipos)]

    # Itens (detalhe)
    df_itens = df.copy()
    df_itens = df_itens.sort_values(by=["Tipo_Comissao", "Nome_Colaborador"], ascending=[True, True])
    if len(df_itens) > size_itens:
        df_itens = df_itens.iloc[:size_itens]

    itens = _df_to_records_json_safe(df_itens)

    # Resumo por colaborador
    grouped = df.groupby(["Nome_Colaborador", "Tipo_Comissao"], dropna=False)["Comissao_Calculada"].sum().reset_index()

    # Pivot para DEVOLUCAO/RECONCILIACAO
    pivot = grouped.pivot_table(
        index="Nome_Colaborador",
        columns="Tipo_Comissao",
        values="Comissao_Calculada",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    # Contagem de itens por colaborador
    counts = df.groupby("Nome_Colaborador")["Comissao_Calculada"].count().reset_index().rename(columns={"Comissao_Calculada": "Quantidade"})

    resumo = pivot.merge(counts, on="Nome_Colaborador", how="left")

    if "DEVOLUCAO" not in resumo.columns:
        resumo["DEVOLUCAO"] = 0.0
    if "RECONCILIACAO" not in resumo.columns:
        resumo["RECONCILIACAO"] = 0.0

    resumo["Total_Negativo"] = resumo["DEVOLUCAO"].astype(float) + resumo["RECONCILIACAO"].astype(float)

    # Para UI: também enviar totais absolutos (como "valor a descontar")
    resumo["Total_Absoluto"] = resumo["Total_Negativo"].abs()
    resumo["DEVOLUCAO_ABS"] = resumo["DEVOLUCAO"].abs()
    resumo["RECONCILIACAO_ABS"] = resumo["RECONCILIACAO"].abs()

    resumo = resumo.sort_values(by=["Total_Absoluto"], ascending=False)

    return {
        "resumo_colaboradores": _df_to_records_json_safe(resumo),
        "itens": itens,
    }


@router.get("/resumo-final-colaboradores")
async def get_resumo_final_colaboradores(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
):
    """Retorna o resultado final por colaborador no mês, incluindo ADIANTAMENTO."""
    df = _normalize_master_types(_load_master_df())
    if df.empty:
        return {"colaboradores": []}

    required_cols = ["Mes_Referencia", "Ano_Referencia", "Tipo_Comissao", "Nome_Colaborador", "Comissao_Calculada"]
    for c in required_cols:
        if c not in df.columns:
            raise HTTPException(status_code=500, detail=f"Master DB sem coluna obrigatória: {c}")

    df = df[df["Mes_Referencia"].fillna(-1).astype(int) == int(mes)]
    df = df[df["Ano_Referencia"].fillna(-1).astype(int) == int(ano)]

    # Agrupar por colaborador e tipo
    grouped = (
        df.groupby(["Nome_Colaborador", "Tipo_Comissao"], dropna=False)["Comissao_Calculada"].sum().reset_index()
    )

    pivot = grouped.pivot_table(
        index="Nome_Colaborador",
        columns="Tipo_Comissao",
        values="Comissao_Calculada",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    # Total do mês (inclui todos os tipos existentes)
    tipo_cols = [c for c in pivot.columns if c != "Nome_Colaborador"]
    pivot["Total_Mes"] = pivot[tipo_cols].sum(axis=1)

    # Normalizar colunas esperadas para UI (mesmo se não existirem no mês)
    for col in ["FATURAMENTO", "ADIANTAMENTO", "REGULAR", "RECONCILIACAO", "DEVOLUCAO"]:
        if col not in pivot.columns:
            pivot[col] = 0.0

    pivot = pivot.sort_values(by=["Total_Mes"], ascending=False)

    return {
        "colaboradores": _df_to_records_json_safe(pivot),
    }


@router.get("/resumo-final-colaborador/detalhes")
async def get_resumo_final_colaborador_detalhes(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    nome_colaborador: str = Query(..., min_length=1),
):
    """Retorna linhas do Master DB para um colaborador no mês (para modal detalhado)."""
    df = _normalize_master_types(_load_master_df())
    if df.empty:
        return {"linhas": []}

    required_cols = ["Mes_Referencia", "Ano_Referencia", "Nome_Colaborador"]
    for c in required_cols:
        if c not in df.columns:
            raise HTTPException(status_code=500, detail=f"Master DB sem coluna obrigatória: {c}")

    df = df[df["Mes_Referencia"].fillna(-1).astype(int) == int(mes)]
    df = df[df["Ano_Referencia"].fillna(-1).astype(int) == int(ano)]

    df = df[df["Nome_Colaborador"].astype(str).str.strip().str.lower() == nome_colaborador.strip().lower()]

    # Ordenar: primeiro tipos, depois processo
    for col in ["Tipo_Comissao", "Processo"]:
        if col not in df.columns:
            continue
    if "Tipo_Comissao" in df.columns:
        df = df.sort_values(by=["Tipo_Comissao"], ascending=True)

    return {"linhas": _df_to_records_json_safe(df)}
