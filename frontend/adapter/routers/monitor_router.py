"""
Router para endpoints de monitoramento de processos.

Gerencia a visualização do estado de ciclo de vida dos processos
de recebimento, incluindo antecipações, pagamentos regulares e reconciliações.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitor", tags=["Monitoramento"])


# ==================== MODELS ====================


class ColaboradorTCMP(BaseModel):
    """Taxa de Comissão Média Ponderada por colaborador."""
    colaborador: str
    tcmp: float


class ColaboradorFCMP(BaseModel):
    """Fator de Correção Médio Ponderado por colaborador."""
    colaborador: str
    fcmp: float


class ProcessoEstado(BaseModel):
    """Modelo de dados do estado de um processo."""
    processo: str
    valor_total_processo: float
    total_antecipacoes: float
    total_pagamentos_regulares: float
    total_pago_acumulado: float
    saldo_a_receber: float
    total_comissao_antecipacoes: float
    total_comissao_regulares: float
    total_comissao_acumulada: float
    status_processo: str
    status_pagamento: str
    status_calculo_medias: str
    mes_ano_faturamento: Optional[str]
    colaboradores_envolvidos: List[str]
    data_primeiro_pagamento: Optional[str]
    data_ultimo_pagamento: Optional[str]
    quantidade_pagamentos: int
    ultima_atualizacao: Optional[str]
    status_reconciliacao: str
    observacoes: Optional[str]
    # Dados expandidos (TCMP/FCMP por colaborador)
    tcmp_por_colaborador: List[ColaboradorTCMP]
    fcmp_por_colaborador: List[ColaboradorFCMP]
    # Percentual de progresso calculado
    percentual_pago: float


class EstadoProcessosResponse(BaseModel):
    """Resposta do endpoint de estado de processos."""
    total_processos: int
    processos: List[ProcessoEstado]
    resumo: Dict[str, Any]


# ==================== HELPER FUNCTIONS ====================


def get_robo_root_path() -> Path:
    """Retorna o caminho raiz do robô."""
    # Importar do módulo principal para manter consistência
    import sys
    adapter_dir = Path(__file__).parent.parent
    default_path = adapter_dir.parent.parent.resolve()
    
    import os
    from dotenv import load_dotenv
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


def safe_int(value: Any, default: int = 0) -> int:
    """Converte valor para int de forma segura."""
    if pd.isna(value) or value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Converte valor para string de forma segura."""
    if pd.isna(value) or value is None:
        return default
    return str(value)


# ==================== ENDPOINTS ====================


@router.get("/processos", response_model=EstadoProcessosResponse)
async def get_estado_processos(
    status_pagamento: Optional[str] = Query(
        None, description="Filtrar por status de pagamento (PENDENTE, PARCIAL, COMPLETO)"
    ),
    status_reconciliacao: Optional[str] = Query(
        None, description="Filtrar por status de reconciliação (PENDENTE, CONCLUIDA)"
    ),
    apenas_saldo_aberto: bool = Query(
        False, description="Mostrar apenas processos com saldo a receber > 0"
    ),
):
    """
    Retorna o estado atual de todos os processos de recebimento.
    
    Este endpoint lê o arquivo Estado_Processos_Recebimento e retorna
    informações detalhadas sobre o ciclo de vida de cada processo,
    incluindo valores pagos, saldos, comissões e métricas TCMP/FCMP.
    """
    estado_path = get_estado_file_path()
    
    if not estado_path.exists():
        logger.warning(f"Arquivo de estado não encontrado: {estado_path}")
        return EstadoProcessosResponse(
            total_processos=0,
            processos=[],
            resumo={
                "total_valor_processos": 0,
                "total_pago": 0,
                "total_saldo_aberto": 0,
                "total_comissoes": 0,
                "por_status_pagamento": {},
                "por_status_reconciliacao": {},
            }
        )
    
    try:
        # Ler arquivo (xlsx ou csv)
        if estado_path.suffix.lower() == ".xlsx":
            df = pd.read_excel(estado_path, dtype=str)
        else:
            df = pd.read_csv(estado_path, sep=";", dtype=str)
        
        logger.info(f"Lido arquivo de estado com {len(df)} processos")
        
    except Exception as e:
        logger.error(f"Erro ao ler arquivo de estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler arquivo de estado: {str(e)}"
        )
    
    # Processar cada linha
    processos: List[ProcessoEstado] = []
    
    # Contadores para resumo
    total_valor_processos = 0.0
    total_pago = 0.0
    total_saldo_aberto = 0.0
    total_comissoes = 0.0
    por_status_pagamento: Dict[str, int] = {}
    por_status_reconciliacao: Dict[str, int] = {}
    
    for _, row in df.iterrows():
        # Parse dos valores numéricos
        valor_total = safe_float(row.get("VALOR_TOTAL_PROCESSO"))
        total_pago_acum = safe_float(row.get("TOTAL_PAGO_ACUMULADO"))
        saldo = safe_float(row.get("SALDO_A_RECEBER"))
        comissao_acum = safe_float(row.get("TOTAL_COMISSAO_ACUMULADA"))
        
        # Calcular percentual pago
        percentual_pago = (total_pago_acum / valor_total * 100) if valor_total > 0 else 0.0
        
        # Parse dos JSONs de TCMP e FCMP
        tcmp_json = parse_json_column(row.get("TCMP_JSON"))
        fcmp_json = parse_json_column(row.get("FCMP_JSON"))
        
        # Converter para lista de colaboradores
        tcmp_lista = [
            ColaboradorTCMP(colaborador=k, tcmp=safe_float(v))
            for k, v in tcmp_json.items()
        ]
        fcmp_lista = [
            ColaboradorFCMP(colaborador=k, fcmp=safe_float(v))
            for k, v in fcmp_json.items()
        ]
        
        # Status
        status_pag = safe_str(row.get("STATUS_PAGAMENTO"), "PENDENTE")
        status_recon = safe_str(row.get("STATUS_RECONCILIACAO"), "PENDENTE")
        
        # Aplicar filtros
        if status_pagamento and status_pag != status_pagamento:
            continue
        if status_reconciliacao and status_recon != status_reconciliacao:
            continue
        if apenas_saldo_aberto and saldo <= 0:
            continue
        
        # Criar objeto do processo
        processo = ProcessoEstado(
            processo=safe_str(row.get("PROCESSO")),
            valor_total_processo=valor_total,
            total_antecipacoes=safe_float(row.get("TOTAL_ANTECIPACOES")),
            total_pagamentos_regulares=safe_float(row.get("TOTAL_PAGAMENTOS_REGULARES")),
            total_pago_acumulado=total_pago_acum,
            saldo_a_receber=saldo,
            total_comissao_antecipacoes=safe_float(row.get("TOTAL_COMISSAO_ANTECIPACOES")),
            total_comissao_regulares=safe_float(row.get("TOTAL_COMISSAO_REGULARES")),
            total_comissao_acumulada=comissao_acum,
            status_processo=safe_str(row.get("STATUS_PROCESSO"), "DESCONHECIDO"),
            status_pagamento=status_pag,
            status_calculo_medias=safe_str(row.get("STATUS_CALCULO_MEDIAS"), "PENDENTE"),
            mes_ano_faturamento=safe_str(row.get("MES_ANO_FATURAMENTO")) or None,
            colaboradores_envolvidos=parse_colaboradores(row.get("COLABORADORES_ENVOLVIDOS")),
            data_primeiro_pagamento=format_date(row.get("DATA_PRIMEIRO_PAGAMENTO")),
            data_ultimo_pagamento=format_date(row.get("DATA_ULTIMO_PAGAMENTO")),
            quantidade_pagamentos=safe_int(row.get("QUANTIDADE_PAGAMENTOS")),
            ultima_atualizacao=format_date(row.get("ULTIMA_ATUALIZACAO")),
            status_reconciliacao=status_recon,
            observacoes=safe_str(row.get("OBSERVACOES")) or None,
            tcmp_por_colaborador=tcmp_lista,
            fcmp_por_colaborador=fcmp_lista,
            percentual_pago=round(percentual_pago, 2),
        )
        
        processos.append(processo)
        
        # Atualizar contadores
        total_valor_processos += valor_total
        total_pago += total_pago_acum
        total_saldo_aberto += saldo
        total_comissoes += comissao_acum
        por_status_pagamento[status_pag] = por_status_pagamento.get(status_pag, 0) + 1
        por_status_reconciliacao[status_recon] = por_status_reconciliacao.get(status_recon, 0) + 1
    
    logger.info(f"Retornando {len(processos)} processos após filtros")
    
    return EstadoProcessosResponse(
        total_processos=len(processos),
        processos=processos,
        resumo={
            "total_valor_processos": round(total_valor_processos, 2),
            "total_pago": round(total_pago, 2),
            "total_saldo_aberto": round(total_saldo_aberto, 2),
            "total_comissoes": round(total_comissoes, 4),
            "por_status_pagamento": por_status_pagamento,
            "por_status_reconciliacao": por_status_reconciliacao,
        }
    )


@router.get("/processos/{processo_id}/detalhes")
async def get_processo_detalhes(processo_id: str):
    """
    Retorna detalhes completos de um processo específico,
    incluindo breakdown de TCMP e FCMP por item.
    """
    estado_path = get_estado_file_path()
    
    if not estado_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Arquivo de estado não encontrado"
        )
    
    try:
        if estado_path.suffix.lower() == ".xlsx":
            df = pd.read_excel(estado_path, dtype=str)
        else:
            df = pd.read_csv(estado_path, sep=";", dtype=str)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler arquivo de estado: {str(e)}"
        )
    
    # Buscar processo
    processo_row = df[df["PROCESSO"].astype(str) == str(processo_id)]
    
    if processo_row.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Processo {processo_id} não encontrado"
        )
    
    row = processo_row.iloc[0]
    
    # Parse completo dos detalhes
    tcmp_detalhes = parse_json_column(row.get("TCMP_DETALHES_JSON"))
    fcmp_detalhes = parse_json_column(row.get("FCMP_DETALHES_JSON"))
    comissoes_adiantadas = parse_json_column(row.get("COMISSOES_ADIANTADAS_JSON"))
    
    return {
        "processo": safe_str(row.get("PROCESSO")),
        "valor_total_processo": safe_float(row.get("VALOR_TOTAL_PROCESSO")),
        "total_antecipacoes": safe_float(row.get("TOTAL_ANTECIPACOES")),
        "total_pagamentos_regulares": safe_float(row.get("TOTAL_PAGAMENTOS_REGULARES")),
        "total_pago_acumulado": safe_float(row.get("TOTAL_PAGO_ACUMULADO")),
        "saldo_a_receber": safe_float(row.get("SALDO_A_RECEBER")),
        "total_comissao_antecipacoes": safe_float(row.get("TOTAL_COMISSAO_ANTECIPACOES")),
        "total_comissao_regulares": safe_float(row.get("TOTAL_COMISSAO_REGULARES")),
        "total_comissao_acumulada": safe_float(row.get("TOTAL_COMISSAO_ACUMULADA")),
        "status_processo": safe_str(row.get("STATUS_PROCESSO")),
        "status_pagamento": safe_str(row.get("STATUS_PAGAMENTO")),
        "status_calculo_medias": safe_str(row.get("STATUS_CALCULO_MEDIAS")),
        "mes_ano_faturamento": safe_str(row.get("MES_ANO_FATURAMENTO")) or None,
        "colaboradores_envolvidos": parse_colaboradores(row.get("COLABORADORES_ENVOLVIDOS")),
        "data_primeiro_pagamento": format_date(row.get("DATA_PRIMEIRO_PAGAMENTO")),
        "data_ultimo_pagamento": format_date(row.get("DATA_ULTIMO_PAGAMENTO")),
        "quantidade_pagamentos": safe_int(row.get("QUANTIDADE_PAGAMENTOS")),
        "ultima_atualizacao": format_date(row.get("ULTIMA_ATUALIZACAO")),
        "status_reconciliacao": safe_str(row.get("STATUS_RECONCILIACAO")),
        "observacoes": safe_str(row.get("OBSERVACOES")) or None,
        # Detalhes expandidos
        "tcmp_json": parse_json_column(row.get("TCMP_JSON")),
        "fcmp_json": parse_json_column(row.get("FCMP_JSON")),
        "tcmp_detalhes": tcmp_detalhes,
        "fcmp_detalhes": fcmp_detalhes,
        "comissoes_adiantadas": comissoes_adiantadas,
    }
