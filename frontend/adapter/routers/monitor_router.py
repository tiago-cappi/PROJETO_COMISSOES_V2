"""
Router para endpoints de estado de processos de recebimento.

Fornece acesso raw ao arquivo Estado_Processos_Recebimento.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitor", tags=["Estado Processos"])


# ==================== MODELS ====================


class EstadoRawResponse(BaseModel):
    """Resposta do endpoint de estado raw (todas as colunas)."""
    total_processos: int
    colunas: List[str]
    dados: List[Dict[str, Any]]


# ==================== HELPER FUNCTIONS ====================


def get_robo_root_path() -> Path:
    """Retorna o caminho raiz do robô."""
    import sys
    import os
    from dotenv import load_dotenv
    
    adapter_dir = Path(__file__).parent.parent
    default_path = adapter_dir.parent.parent.resolve()
    
    env_path = adapter_dir / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    
    robo_path = os.getenv("ROBO_ROOT_PATH")
    if not robo_path:
        return default_path
    return Path(robo_path).resolve()


def get_estado_file_path() -> Path:
    """Retorna o caminho do arquivo de estado de processos."""
    robo_root = get_robo_root_path()
    # Tentar primeiro .xlsx (formato padrão de produção), depois .csv
    xlsx_path = robo_root / "Estado_Processos_Recebimento.xlsx"
    csv_path = robo_root / "Estado_Processos_Recebimento.csv"
    
    if xlsx_path.exists():
        return xlsx_path
    elif csv_path.exists():
        return csv_path
    else:
        # Retorna o path xlsx como padrão (para mensagem de erro)
        return xlsx_path


def parse_json_column(value: Any) -> Any:
    """
    Parse de colunas JSON armazenadas como string.
    Retorna o valor original se não for JSON válido.
    """
    if pd.isna(value) or value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def parse_colaboradores(value: Any) -> List[str]:
    """Parse da coluna de colaboradores envolvidos."""
    if pd.isna(value) or value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Pode ser uma string separada por vírgula ou ponto-e-vírgula
        separators = [";", ","]
        for sep in separators:
            if sep in value:
                return [c.strip() for c in value.split(sep) if c.strip()]
        return [value.strip()] if value.strip() else []
    return []


def format_date(value: Any) -> Optional[str]:
    """Formata datas para string ISO."""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Converte valor para float de forma segura."""
    if pd.isna(value) or value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Converte valor para string de forma segura."""
    if pd.isna(value) or value is None:
        return default
    return str(value)


# ==================== ENDPOINTS ====================


@router.get("/estado-raw", response_model=EstadoRawResponse)
async def get_estado_raw(
    busca: Optional[str] = Query(None, description="Busca por texto em processo ou colaborador"),
    status_processo: Optional[str] = Query(None, description="Filtrar por status do processo"),
    status_pagamento: Optional[str] = Query(None, description="Filtrar por status de pagamento"),
    status_calculo: Optional[str] = Query(None, description="Filtrar por status de cálculo de médias"),
):
    """
    Retorna o estado completo de todos os processos em formato raw.
    
    Este endpoint retorna TODAS as colunas do arquivo Estado_Processos_Recebimento
    exatamente como estão armazenadas, ideal para visualização completa dos dados.
    
    Colunas JSON são retornadas como objetos (não strings) para facilitar a renderização.
    """
    estado_path = get_estado_file_path()
    
    if not estado_path.exists():
        logger.warning(f"Arquivo de estado não encontrado: {estado_path}")
        return EstadoRawResponse(
            total_processos=0,
            colunas=[],
            dados=[]
        )
    
    try:
        # Ler arquivo (xlsx ou csv)
        if estado_path.suffix.lower() == ".xlsx":
            df = pd.read_excel(estado_path, dtype=str)
        else:
            df = pd.read_csv(estado_path, sep=";", dtype=str)
        
        logger.info(f"[ESTADO-RAW] Lido arquivo de estado com {len(df)} processos: {estado_path}")
        
    except Exception as e:
        logger.error(f"[ESTADO-RAW] Erro ao ler arquivo de estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler arquivo de estado: {str(e)}"
        )
    
    # Lista de colunas que contêm JSON
    json_columns = [
        "TCMP_JSON", "FCMP_JSON", 
        "TCMP_DETALHES_JSON", "FCMP_DETALHES_JSON",
        "COMISSOES_ADIANTADAS_JSON"
    ]
    
    # Lista de colunas numéricas
    numeric_columns = [
        "VALOR_TOTAL_PROCESSO", "TOTAL_ANTECIPACOES", "TOTAL_PAGAMENTOS_REGULARES",
        "TOTAL_PAGO_ACUMULADO", "SALDO_A_RECEBER", "TOTAL_COMISSAO_ANTECIPACOES",
        "TOTAL_COMISSAO_REGULARES", "TOTAL_COMISSAO_ACUMULADA", "QUANTIDADE_PAGAMENTOS"
    ]
    
    # Processar cada linha
    dados = []
    for _, row in df.iterrows():
        registro = {}
        
        for col in df.columns:
            value = row.get(col)
            
            if col in json_columns:
                # Parse de colunas JSON
                registro[col] = parse_json_column(value)
            elif col in numeric_columns:
                # Converter para número
                registro[col] = safe_float(value) if pd.notna(value) else None
            elif col == "COLABORADORES_ENVOLVIDOS":
                # Parse de colaboradores
                registro[col] = parse_colaboradores(value)
            elif "DATA" in col or "ATUALIZACAO" in col:
                # Formatar datas
                registro[col] = format_date(value)
            else:
                # Manter como string
                registro[col] = safe_str(value) if pd.notna(value) else None
        
        dados.append(registro)
    
    # Aplicar filtros
    if busca:
        busca_lower = busca.lower()
        dados = [
            d for d in dados
            if (d.get("PROCESSO") and busca_lower in str(d["PROCESSO"]).lower()) or
               (d.get("COLABORADORES_ENVOLVIDOS") and any(busca_lower in c.lower() for c in d["COLABORADORES_ENVOLVIDOS"]))
        ]
    
    if status_processo:
        dados = [d for d in dados if d.get("STATUS_PROCESSO") == status_processo]
    
    if status_pagamento:
        dados = [d for d in dados if d.get("STATUS_PAGAMENTO") == status_pagamento]
    
    if status_calculo:
        dados = [d for d in dados if d.get("STATUS_CALCULO_MEDIAS") == status_calculo]
    
    logger.info(f"[ESTADO-RAW] Retornando {len(dados)} processos após filtros")
    
    return EstadoRawResponse(
        total_processos=len(dados),
        colunas=list(df.columns),
        dados=dados
    )
