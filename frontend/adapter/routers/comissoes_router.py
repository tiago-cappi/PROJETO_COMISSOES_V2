"""
Router para dados de comissões agrupados por colaborador.

Fornece visão "Colaborador-First" unificada para Faturamento e Recebimento,
permitindo que o frontend exiba dashboards centrados no colaborador.
"""

import logging
import math
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resultado/comissoes", tags=["comissoes"])

# ---------------------------------------------------------------------------
# Helpers reutilizados do app.py (importados em runtime para evitar circular)
# ---------------------------------------------------------------------------


def _get_app_helpers():
    """Importa helpers do app.py em runtime para evitar import circular."""
    import app as main_app

    return {
        "get_resultado_path": main_app.get_resultado_path,
        "get_recebimento_path": main_app.get_recebimento_path,
        "read_excel_sheet": main_app.read_excel_sheet,
        "ROBO_ROOT_PATH": main_app.ROBO_ROOT_PATH,
    }


def _safe_float(val) -> float:
    """Converte valor para float de forma segura (NaN/Inf -> 0.0)."""
    if val is None:
        return 0.0
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        try:
            s = str(val).strip().replace(",", "")
            if not s or s.lower() == "nan":
                return 0.0
            f = float(s)
            return 0.0 if (math.isnan(f) or math.isinf(f)) else f
        except (ValueError, TypeError):
            return 0.0


def _safe_str(val) -> str:
    """Converte valor para string de forma segura."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _df_to_records_safe(df: pd.DataFrame) -> list:
    """Converte DataFrame para list[dict] com tratamento de NaN/Inf."""
    if df.empty:
        return []
    records = df.where(df.notna(), None).to_dict(orient="records")
    # Sanitizar valores que json.dumps não suporta (nan, inf, -inf)
    sanitized = []
    for rec in records:
        clean = {}
        for k, v in rec.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean[k] = None
            elif isinstance(v, (np.floating, np.integer)):
                fv = float(v)
                clean[k] = None if (math.isnan(fv) or math.isinf(fv)) else fv
            else:
                clean[k] = v
        sanitized.append(clean)
    return sanitized


# ---------------------------------------------------------------------------
# FATURAMENTO — Agrupado por colaborador
# ---------------------------------------------------------------------------


@router.get("/colaboradores/faturamento")
async def get_colaboradores_faturamento():
    """
    Retorna dados de comissão por faturamento agrupados por colaborador.

    Lê a aba COMISSOES_CALCULADAS do último arquivo de resultado e agrupa
    todas as linhas por nome_colaborador, com totais e lista de itens.
    """
    helpers = _get_app_helpers()
    resultado_path = helpers["get_resultado_path"]()

    if not resultado_path:
        return {"colaboradores": []}

    try:
        df = helpers["read_excel_sheet"](resultado_path, "COMISSOES_CALCULADAS")
    except Exception as e:
        logger.error("Erro ao ler COMISSOES_CALCULADAS: %s", e)
        return {"colaboradores": []}

    if df.empty:
        return {"colaboradores": []}

    # Normalizar tipos numéricos nas colunas relevantes
    numeric_cols = [
        "faturamento_item", "taxa_rateio_aplicada", "percentual_elegibilidade_pe",
        "comissao_potencial_maxima", "fator_correcao_fc", "comissao_calculada",
        "cap_fc_max", "fator_correcao_fc_rampa",
        "fc_escada_num_degraus", "fc_escada_piso", "fc_escada_degrau_indice",
    ]
    # Adicionar colunas de meta (peso_*, realizado_*, meta_*, ating_*, ating_cap_*, comp_fc_*)
    meta_keys = ["fat_linha", "conv_linha", "rentab", "fat_ind", "conv_ind", "retencao", "forn1", "forn2"]
    for key in meta_keys:
        for prefix in ["peso_", "realizado_", "meta_", "ating_", "ating_cap_", "comp_fc_"]:
            numeric_cols.append(f"{prefix}{key}")

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Garantir que colunas-chave existem
    if "nome_colaborador" not in df.columns:
        logger.warning("Coluna 'nome_colaborador' ausente em COMISSOES_CALCULADAS")
        return {"colaboradores": []}

    # Agrupar por colaborador
    colaboradores = []
    grouped = df.groupby("nome_colaborador", dropna=False)

    for nome, group_df in grouped:
        nome_str = _safe_str(nome)
        if not nome_str:
            continue

        # Obter cargo (pegar o primeiro não-vazio)
        cargo = ""
        if "cargo" in group_df.columns:
            cargos = group_df["cargo"].dropna().astype(str).str.strip()
            cargos = cargos[cargos != ""]
            if len(cargos) > 0:
                cargo = cargos.iloc[0]

        # Contar processos e itens únicos
        processos_unicos = set()
        if "processo" in group_df.columns:
            processos_unicos = set(group_df["processo"].dropna().astype(str).str.strip()) - {""}

        total_comissao = _safe_float(group_df["comissao_calculada"].sum()) if "comissao_calculada" in group_df.columns else 0.0

        # Converter cada linha em dict para o frontend
        itens = _df_to_records_safe(group_df)

        colaboradores.append({
            "nome_colaborador": nome_str,
            "cargo": cargo,
            "total_comissao": round(total_comissao, 2),
            "total_processos": len(processos_unicos),
            "total_itens": len(itens),
            "itens": itens,
        })

    # Ordenar por comissão total descendente
    colaboradores.sort(key=lambda c: c["total_comissao"], reverse=True)

    return {"colaboradores": colaboradores}


# ---------------------------------------------------------------------------
# RECEBIMENTO — Agrupado por colaborador
# ---------------------------------------------------------------------------


@router.get("/colaboradores/recebimento")
async def get_colaboradores_recebimento(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
):
    """
    Retorna dados de comissão por recebimento agrupados por colaborador.

    Combina COMISSOES_ADIANTAMENTOS + COMISSOES_REGULARES em uma visão
    centrada no colaborador, com totais e lista de pagamentos.
    """
    helpers = _get_app_helpers()
    recebimento_path = helpers["get_recebimento_path"](mes, ano)

    if not recebimento_path:
        return {"colaboradores": [], "mes": mes, "ano": ano}

    # Carregar mapa de cargos como fallback
    cargo_map = _load_cargo_map(helpers)

    pagamentos_por_colab: dict[str, list] = {}
    meta_por_colab: dict[str, dict] = {}

    # Processar adiantamentos
    _process_recebimento_aba(
        helpers, recebimento_path, "COMISSOES_ADIANTAMENTOS", "ADIANTAMENTO",
        mes, ano, cargo_map, pagamentos_por_colab, meta_por_colab,
    )

    # Processar regulares
    _process_recebimento_aba(
        helpers, recebimento_path, "COMISSOES_REGULARES", "REGULAR",
        mes, ano, cargo_map, pagamentos_por_colab, meta_por_colab,
    )

    # Montar resposta
    colaboradores = []
    for nome, pagamentos in pagamentos_por_colab.items():
        meta = meta_por_colab.get(nome, {})
        total_comissao = sum(p.get("comissao_calculada", 0) for p in pagamentos)
        total_adiantamentos = sum(1 for p in pagamentos if p.get("tipo") == "ADIANTAMENTO")
        total_regulares = sum(1 for p in pagamentos if p.get("tipo") == "REGULAR")
        processos_unicos = set(p.get("processo", "") for p in pagamentos) - {""}

        colaboradores.append({
            "nome_colaborador": nome,
            "cargo": meta.get("cargo", ""),
            "total_comissao": round(total_comissao, 2),
            "total_adiantamentos": total_adiantamentos,
            "total_regulares": total_regulares,
            "total_processos": len(processos_unicos),
            "total_pagamentos": len(pagamentos),
            "pagamentos": pagamentos,
        })

    colaboradores.sort(key=lambda c: c["total_comissao"], reverse=True)

    return {"colaboradores": colaboradores, "mes": mes, "ano": ano}


def _load_cargo_map(helpers: dict) -> dict:
    """Carrega mapa nome_colaborador(lower) -> cargo a partir de REGRAS_COMISSOES."""
    cargo_map: dict[str, str] = {}
    try:
        from app import get_regras_path

        regras_path = get_regras_path()
        if regras_path.exists():
            df_colab = helpers["read_excel_sheet"](regras_path, "COLABORADORES")
            for _, row in df_colab.iterrows():
                nome = None
                cargo = None
                for col in row.index:
                    if col.lower() == "nome_colaborador":
                        nome = str(row[col]).strip().lower()
                    elif col.lower() == "cargo":
                        cargo = str(row[col]).strip()
                if nome and cargo:
                    cargo_map[nome] = cargo
    except Exception as e:
        logger.warning("Erro ao carregar mapa de cargos: %s", e)
    return cargo_map


def _safe_date(val) -> str:
    """Converte data para string ISO de forma segura."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s_val = str(val).strip()
    if not s_val or s_val.lower() == "nan":
        return ""
    if "/" in s_val:
        try:
            parts = s_val.split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        except Exception:
            pass
    return s_val


def _get_col(row, col_name):
    """Obtém valor de coluna case-insensitive."""
    if col_name in row.index:
        return row[col_name]
    col_map = {c.lower(): c for c in row.index}
    if col_name.lower() in col_map:
        return row[col_map[col_name.lower()]]
    return None


def _process_recebimento_aba(
    helpers: dict,
    recebimento_path: Path,
    sheet_name: str,
    tipo: str,
    mes: int,
    ano: int,
    cargo_map: dict,
    pagamentos_por_colab: dict,
    meta_por_colab: dict,
):
    """Processa uma aba do recebimento e agrupa por colaborador."""
    try:
        df = helpers["read_excel_sheet"](recebimento_path, sheet_name)
    except Exception as e:
        logger.warning("Aba %s não encontrada ou erro: %s", sheet_name, e)
        return

    for idx, row in df.iterrows():
        nome = _safe_str(_get_col(row, "nome_colaborador"))
        if not nome:
            continue

        cargo = _safe_str(_get_col(row, "cargo"))
        if not cargo and nome.lower() in cargo_map:
            cargo = cargo_map[nome.lower()]

        # Inicializar colaborador no mapa se necessário
        if nome not in pagamentos_por_colab:
            pagamentos_por_colab[nome] = []
            meta_por_colab[nome] = {"cargo": cargo}

        fcmp_value = _safe_float(_get_col(row, "fcmp")) if tipo == "REGULAR" else 1.0

        pagamentos_por_colab[nome].append({
            "id": f"{tipo[:5]}_{mes}_{ano}_{idx}",
            "tipo": tipo,
            "processo": _safe_str(_get_col(row, "processo")),
            "data_pagamento": _safe_date(_get_col(row, "data_pagamento")),
            "valor_pago": _safe_float(_get_col(row, "valor_pago")),
            "tcmp": _safe_float(_get_col(row, "tcmp")),
            "fcmp": fcmp_value if fcmp_value else 1.0,
            "comissao_calculada": _safe_float(_get_col(row, "comissao_calculada")),
        })
