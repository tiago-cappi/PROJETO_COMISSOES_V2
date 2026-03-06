"""
Router FastAPI para a Metodologia V2 de Cálculo de Comissões.

Nova Arquitetura (Hierarquia + Faixas):
- GET /v2/config - Retorna colaboradores com suas regras de comissão
- POST /v2/config - Salva configuração de colaboradores e regras
- GET /v2/lookups - Dados de referência (cargos, hierarquias)
- POST /v2/executar - Executa cálculo
- GET /v2/resultados - Retorna últimos resultados
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import pandas as pd

# Adicionar diretório raiz ao path
ADAPTER_DIR = Path(__file__).parent.parent
ROOT_DIR = ADAPTER_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.metodo_v2 import (
    OrchestratorV2,
    ConfigLoaderV2,
    ColaboradorV2,
    RegraComissao,
    FaixaComissao,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["Metodologia V2"])


# ==================== MODELOS PYDANTIC ====================

class FaixaComissaoModel(BaseModel):
    """Modelo de faixa de comissão para API."""
    limite_inferior: float = Field(..., ge=0, description="Limite inferior (R$)")
    limite_superior: Optional[float] = Field(None, ge=0, description="Limite superior (R$) - null = infinito")
    taxa_comissao_pct: float = Field(..., ge=0, le=100, description="Taxa de comissão em %")


class RegraComissaoModel(BaseModel):
    """Modelo de regra de comissão para API."""
    regra_id: Any = Field(..., description="ID único da regra (string ou int)")
    # Filtros hierárquicos (None = wildcard "*")
    linha: Optional[str] = Field(None, description="Linha (null = qualquer)")
    grupo: Optional[str] = Field(None, description="Grupo (null = qualquer)")
    subgrupo: Optional[str] = Field(None, description="Subgrupo (null = qualquer)")
    tipo_mercadoria: Optional[str] = Field(None, description="Tipo Mercadoria (null = qualquer)")
    fabricante: Optional[str] = Field(None, description="Fabricante (null = qualquer)")
    # Faixas de comissão
    faixas: List[FaixaComissaoModel] = Field(default_factory=list, description="Até 5 faixas")


class ColaboradorConfigModel(BaseModel):
    """Modelo de configuração de colaborador para API."""
    nome_colaborador: str = Field(..., min_length=1, alias="nome", description="Nome completo")
    cargo: Optional[str] = Field(None, description="Cargo (dropdown de CARGOS_V2)")
    regras: List[RegraComissaoModel] = Field(default_factory=list, description="Regras de comissão")

    class Config:
        populate_by_name = True


class ConfigV2Request(BaseModel):
    """Request para salvar configuração completa."""
    colaboradores: List[ColaboradorConfigModel]


class ExecutarV2Request(BaseModel):
    """Request para executar cálculo V2."""
    mes: int = Field(..., ge=1, le=12, description="Mês (1-12)")
    ano: int = Field(..., ge=2000, le=2100, description="Ano")
    modo_calculo: str = Field(
        default="hierarquia", 
        description="Modo de cálculo: 'hierarquia' ou 'centro_custo'"
    )


class ExecutarRecebimentoV2Request(BaseModel):
    """Request para executar recebimento V2."""
    mes: int = Field(..., ge=1, le=12, description="Mês (1-12)")
    ano: int = Field(..., ge=2000, le=2100, description="Ano")
    modo_calculo: str = Field(
        default="hierarquia",
        description="Modo de cálculo: 'hierarquia' ou 'centro_custo'"
    )


class EstadoV2RawResponse(BaseModel):
    """Resposta do endpoint de estado raw V2 (todas as colunas)."""
    total_processos: int
    colunas: List[str]
    dados: List[Dict[str, Any]]


# ==================== ENDPOINTS PRINCIPAIS ====================

@router.get("/config", summary="Obter configuração atual")
async def get_config() -> Dict[str, Any]:
    """Retorna a configuração atual de colaboradores e regras."""
    config_path = ROOT_DIR / "config" / "REGRAS_COMISSOES_V2.xlsx"
    
    if not config_path.exists():
        return {"colaboradores": [], "existe": False}
    
    try:
        loader = ConfigLoaderV2(str(config_path))
        colaboradores = loader.load()
        
        # Converter para formato JSON serializável
        result = []
        
        for nome, colab in colaboradores.items():
            regras_json = []
            for regra in colab.regras:
                faixas_json = [
                    {
                        "limite_inferior": f.limite_inferior,
                        "limite_superior": getattr(f, 'limite_superior', None),
                        "taxa_comissao_pct": f.taxa_comissao_pct,
                    }
                    for f in regra.faixas
                ]
                regras_json.append({
                    "regra_id": regra.regra_id,
                    "linha": regra.linha,
                    "grupo": regra.grupo,
                    "subgrupo": regra.subgrupo,
                    "tipo_mercadoria": regra.tipo_mercadoria,
                    "fabricante": regra.fabricante,
                    "especificidade": regra.especificidade,
                    "faixas": faixas_json,
                })
            
            result.append({
                "nome": colab.nome,
                "cargo": colab.cargo,
                "regras": regras_json,
            })
        
        return {"colaboradores": result, "existe": True}
        
    except ValueError as e:
        logger.error(f"Erro de validação na configuração V2: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Erro ao carregar config V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", summary="Salvar configuração")
async def save_config(request: ConfigV2Request) -> Dict[str, str]:
    """Salva colaboradores e regras no REGRAS_COMISSOES_V2.xlsx."""
    config_path = ROOT_DIR / "config" / "REGRAS_COMISSOES_V2.xlsx"
    
    try:
        # Carregar arquivo existente para preservar outras abas
        existing_sheets = {}
        if config_path.exists():
            xl = pd.ExcelFile(str(config_path))
            for sheet in xl.sheet_names:
                # Preservar TODAS as abas exceto REGRAS_COMISSAO_V2 (que será reconstruída)
                # COLABORADORES_V2 é gerenciada pela aba "Colaboradores/Cargos", NÃO sobrescrever aqui
                if sheet != "REGRAS_COMISSAO_V2":
                    existing_sheets[sheet] = pd.read_excel(xl, sheet_name=sheet)
        
        # Criar DataFrame de regras (uma linha por regra, colunas para faixas)
        regras_data = []
        for colab in request.colaboradores:
            for regra in colab.regras:
                row = {
                    "colaborador": colab.nome_colaborador,
                    "regra_id": regra.regra_id,
                    "linha": regra.linha or "",
                    "grupo": regra.grupo or "",
                    "subgrupo": regra.subgrupo or "",
                    "tipo_mercadoria": regra.tipo_mercadoria or "",
                    "fabricante": regra.fabricante or "",
                }
                # Adicionar até 5 faixas (com limite_inferior, limite_superior, taxa)
                for i, faixa in enumerate(regra.faixas[:5], start=1):
                    row[f"faixa_{i}_de"] = faixa.limite_inferior
                    row[f"faixa_{i}_ate"] = faixa.limite_superior  # Pode ser None = infinito
                    row[f"faixa_{i}_taxa"] = faixa.taxa_comissao_pct
                # Preencher faixas vazias com None
                for i in range(len(regra.faixas) + 1, 6):
                    row[f"faixa_{i}_de"] = None
                    row[f"faixa_{i}_ate"] = None
                    row[f"faixa_{i}_taxa"] = None
                regras_data.append(row)
        
        df_regras = pd.DataFrame(regras_data) if regras_data else pd.DataFrame()
        
        # Garantir colunas de regras na ordem correta
        if not df_regras.empty:
            col_order = [
                "colaborador", "regra_id", 
                "linha", "grupo", "subgrupo", "tipo_mercadoria", "fabricante",
                "faixa_1_de", "faixa_1_ate", "faixa_1_taxa",
                "faixa_2_de", "faixa_2_ate", "faixa_2_taxa",
                "faixa_3_de", "faixa_3_ate", "faixa_3_taxa",
                "faixa_4_de", "faixa_4_ate", "faixa_4_taxa",
                "faixa_5_de", "faixa_5_ate", "faixa_5_taxa",
            ]
            for col in col_order:
                if col not in df_regras.columns:
                    df_regras[col] = None
            df_regras = df_regras[col_order]
        
        # Salvar arquivo
        with pd.ExcelWriter(str(config_path), engine="openpyxl") as writer:
            # Abas existentes (README, HIERARQUIA_V2, CARGOS_V2, COLABORADORES_V2, etc.)
            for sheet_name, sheet_df in existing_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Apenas REGRAS_COMISSAO_V2 é atualizada
            if not df_regras.empty:
                df_regras.to_excel(writer, sheet_name="REGRAS_COMISSAO_V2", index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name="REGRAS_COMISSAO_V2", index=False)
        
        logger.info(f"Config V2 salva: {len(regras_data)} regras")
        return {
            "status": "ok", 
            "message": f"Configuração salva: {len(regras_data)} regras de {len(request.colaboradores)} colaboradores"
        }
        
    except Exception as e:
        logger.exception(f"Erro ao salvar config V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executar", summary="Executar cálculo V2")
async def executar_calculo(request: ExecutarV2Request) -> Dict[str, Any]:
    """Executa o cálculo de comissões usando a Metodologia V2.
    
    Suporta dois modos de cálculo:
    - hierarquia: Regras por linha/grupo/subgrupo/tipo/fabricante (padrão)
    - centro_custo: Regras por Centro de Custo (usa coluna 'Centro Custo-pedido' da AC)
    
    Após o cálculo de faturamento, também processa recebimento para colaboradores
    configurados com tipo_comissao='recebimento'.
    """
    try:
        orchestrator = OrchestratorV2(
            config_path=str(ROOT_DIR / "config" / "REGRAS_COMISSOES_V2.xlsx"),
        )
        
        # Tentar encontrar arquivo de dados
        dados_paths = [
            ROOT_DIR / "dados_entrada" / "Analise_Comercial_Completa.xlsx",
            ROOT_DIR / "dados_entrada" / "Analise_Comercial_Completa.csv",
            ROOT_DIR / "Analise_Comercial_Completa.csv",
        ]
        
        for path in dados_paths:
            if path.exists():
                orchestrator.comercial_path = str(path)
                break
        
        # Executar com o modo selecionado
        modo = request.modo_calculo.lower().strip()
        if modo not in ("hierarquia", "centro_custo"):
            modo = "hierarquia"
        
        df_resumo, df_detalhes = orchestrator.executar(
            mes=request.mes, 
            ano=request.ano,
            modo_calculo=modo
        )
        
        # Salvar resultados (sufixo diferente para modo CC)
        sufixo_modo = "_CC" if modo == "centro_custo" else ""
        output_path = ROOT_DIR / "dados_saida" / f"Resultado_Comissoes_V2_{request.ano}-{request.mes:02d}{sufixo_modo}.xlsx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        orchestrator.salvar_resultados(str(output_path))
        
        # ========================================
        # PROCESSAR RECEBIMENTO (colaboradores com tipo_comissao='recebimento')
        # ========================================
        recebimento_info = {"processado": False, "total_adiantamentos": 0, "total_comissao_recebimento": 0.0}
        try:
            df_adiantamentos, df_reconciliacoes, receb_path = orchestrator.processar_recebimento(
                mes=request.mes,
                ano=request.ano
            )
            recebimento_info = {
                "processado": True,
                "total_adiantamentos": len(df_adiantamentos) if not df_adiantamentos.empty else 0,
                "total_reconciliacoes": len(df_reconciliacoes) if not df_reconciliacoes.empty else 0,
                "total_comissao_recebimento": round(df_adiantamentos["Comissão Calculada"].sum(), 2) if not df_adiantamentos.empty and "Comissão Calculada" in df_adiantamentos.columns else 0.0,
                "arquivo_recebimento": str(receb_path) if receb_path else None,
            }
            logger.info(f"Recebimento processado: {recebimento_info}")
        except Exception as e:
            logger.warning(f"Erro ao processar recebimento (não crítico): {e}")
            recebimento_info["erro"] = str(e)
        
        # Converter para resposta (estrutura pode variar por modo)
        resultados = df_resumo.to_dict("records") if not df_resumo.empty else []
        
        # Coluna de comissão pode ter nome diferente por modo
        col_comissao = "comissao_total" if "comissao_total" in df_resumo.columns else "comissao"
        total_comissao = df_resumo[col_comissao].sum() if col_comissao in df_resumo.columns else 0
        
        return {
            "status": "ok",
            "mes_ano": f"{request.ano}-{request.mes:02d}",
            "modo_calculo": modo,
            "total_colaboradores": len(resultados),
            "total_comissao": round(total_comissao, 2),
            "resultados": resultados,
            "detalhes": df_detalhes.to_dict("records") if not df_detalhes.empty else [],
            "arquivo_saida": str(output_path),
            "recebimento": recebimento_info,
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        # Erros de validação de configuração (ex: nomes duplicados em COLABORADORES_V2)
        logger.error(f"Erro de validação na configuração V2: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Erro ao executar cálculo V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resultados", summary="Obter últimos resultados")
async def get_resultados(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    modo_calculo: str = Query(default="hierarquia", description="Modo: 'hierarquia' ou 'centro_custo'"),
) -> Dict[str, Any]:
    """Retorna os resultados salvos para um período específico."""
    modo = modo_calculo.lower().strip()
    sufixo_modo = "_CC" if modo == "centro_custo" else ""
    output_path = ROOT_DIR / "dados_saida" / f"Resultado_Comissoes_V2_{ano}-{mes:02d}{sufixo_modo}.xlsx"
    
    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Resultados não encontrados para {mes:02d}/{ano} (modo: {modo})"
        )
    
    try:
        # Nomes das abas variam por modo
        if modo == "centro_custo":
            resumo_sheet = "Resumo_CC"
            detalhes_sheets = ["Detalhes_Item_CC"]
        else:
            resumo_sheet = "Resumo"
            detalhes_sheets = ["Detalhes_Item", "Detalhes_Hierarquia"]
        
        df_resumo = pd.read_excel(str(output_path), sheet_name=resumo_sheet)
        
        # Tentar carregar detalhes
        df_detalhes = pd.DataFrame()
        for sheet_name in detalhes_sheets:
            try:
                df_detalhes = pd.read_excel(str(output_path), sheet_name=sheet_name)
                if not df_detalhes.empty:
                    break
            except Exception:
                continue
        
        # Coluna de comissão pode ter nome diferente
        col_comissao = "comissao_total" if "comissao_total" in df_resumo.columns else "comissao"
        total_comissao = df_resumo[col_comissao].sum() if col_comissao in df_resumo.columns else 0
        
        return {
            "mes_ano": f"{ano}-{mes:02d}",
            "modo_calculo": modo,
            "resumo": df_resumo.to_dict("records"),
            "detalhes": df_detalhes.to_dict("records") if not df_detalhes.empty else [],
            "total_comissao": round(total_comissao, 2),
            "total_colaboradores": len(df_resumo),
        }
        
    except Exception as e:
        logger.exception(f"Erro ao carregar resultados V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recebimento/executar", summary="Executar recebimento V2")
async def executar_recebimento_v2(request: ExecutarRecebimentoV2Request) -> Dict[str, Any]:
    """Executa o cálculo de comissões por recebimento na V2."""
    try:
        orchestrator = OrchestratorV2(
            config_path=str(ROOT_DIR / "config" / "REGRAS_COMISSOES_V2.xlsx"),
        )

        # Tentar encontrar arquivo de dados (para reconciliação)
        dados_paths = [
            ROOT_DIR / "dados_entrada" / "Analise_Comercial_Completa.xlsx",
            ROOT_DIR / "dados_entrada" / "Analise_Comercial_Completa.csv",
            ROOT_DIR / "Analise_Comercial_Completa.csv",
        ]

        for path in dados_paths:
            if path.exists():
                orchestrator.comercial_path = str(path)
                break

        modo = request.modo_calculo.lower().strip()
        if modo not in ("hierarquia", "centro_custo"):
            modo = "hierarquia"

        # Pré-carregar dados necessários para reconciliação
        orchestrator._modo_calculo = modo
        orchestrator._carregar_configuracoes()
        orchestrator._carregar_dados_atribuicao()
        orchestrator._carregar_dados_comerciais(request.mes, request.ano)

        df_adiantamentos, df_reconciliacoes, output_path = orchestrator.processar_recebimento(
            mes=request.mes,
            ano=request.ano,
            df_margens=None
        )

        adiantamentos = df_adiantamentos.to_dict("records") if not df_adiantamentos.empty else []
        reconciliacoes = df_reconciliacoes.to_dict("records") if not df_reconciliacoes.empty else []

        total_adiantamentos = 0.0
        if not df_adiantamentos.empty:
            if "Comissão" in df_adiantamentos.columns:
                total_adiantamentos = df_adiantamentos["Comissão"].sum()
            elif "Comissão Calculada" in df_adiantamentos.columns:
                total_adiantamentos = df_adiantamentos["Comissão Calculada"].sum()

        total_ajustes = 0.0
        if not df_reconciliacoes.empty and "Ajuste" in df_reconciliacoes.columns:
            total_ajustes = df_reconciliacoes["Ajuste"].sum()

        return {
            "status": "ok",
            "mes_ano": f"{request.ano}-{request.mes:02d}",
            "modo_calculo": modo,
            "total_adiantamentos": len(adiantamentos),
            "total_reconciliacoes": len(reconciliacoes),
            "total_comissao_adiantamentos": round(float(total_adiantamentos), 2),
            "total_ajustes": round(float(total_ajustes), 2),
            "adiantamentos": adiantamentos,
            "reconciliacoes": reconciliacoes,
            "arquivo_saida": output_path,
        }

    except Exception as e:
        logger.exception(f"Erro ao executar recebimento V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recebimento/resultados", summary="Obter resultados de recebimento V2")
async def get_resultados_recebimento_v2(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    modo_calculo: str = Query(default="hierarquia", description="Modo: 'hierarquia' ou 'centro_custo'"),
) -> Dict[str, Any]:
    """Retorna os resultados de recebimento V2 salvos para um período."""
    output_path = _get_recebimento_output_path(mes, ano)

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Resultados de recebimento não encontrados para {mes:02d}/{ano}"
        )

    try:
        df_resumo = pd.read_excel(str(output_path), sheet_name="Resumo")
        df_adiantamentos = pd.read_excel(str(output_path), sheet_name="Adiantamentos")
        df_reconciliacoes = pd.read_excel(str(output_path), sheet_name="Reconciliações")
        df_pendentes = pd.read_excel(str(output_path), sheet_name="Histórico Pendente")

        metadata = {}
        try:
            df_meta = pd.read_excel(str(output_path), sheet_name="Metadata")
            if not df_meta.empty:
                metadata = df_meta.iloc[0].to_dict()
        except Exception:
            metadata = {}

        return {
            "mes_ano": f"{ano}-{mes:02d}",
            "modo_calculo": modo_calculo,
            "resumo": df_resumo.to_dict("records") if not df_resumo.empty else [],
            "adiantamentos": df_adiantamentos.to_dict("records") if not df_adiantamentos.empty else [],
            "reconciliacoes": df_reconciliacoes.to_dict("records") if not df_reconciliacoes.empty else [],
            "pendentes": df_pendentes.to_dict("records") if not df_pendentes.empty else [],
            "metadata": metadata,
        }

    except Exception as e:
        logger.exception(f"Erro ao carregar resultados recebimento V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recebimento/periodos", summary="Listar períodos com resultados de recebimento V2")
async def listar_periodos_recebimento_v2(
    modo_calculo: str = Query(default="hierarquia", description="Modo: 'hierarquia' ou 'centro_custo'"),
) -> Dict[str, Any]:
    """Lista os períodos (mês/ano) com resultados de recebimento V2 salvos."""
    resultados_dir = ROOT_DIR / "dados_saida"
    periodos: List[Dict[str, Any]] = []

    if not resultados_dir.exists():
        return {"periodos": []}

    for arquivo in resultados_dir.glob("Comissoes_Recebimento_V2_*.xlsx"):
        nome = arquivo.name
        try:
            base = nome.replace("Comissoes_Recebimento_V2_", "").replace(".xlsx", "")
            mes_str, ano_str = base.split("_")
            mes = int(mes_str)
            ano = int(ano_str)
            periodos.append({
                "ano": ano,
                "mes": mes,
                "modo_calculo": modo_calculo,
                "arquivo": nome,
            })
        except Exception:
            continue

    periodos.sort(key=lambda p: (p["ano"], p["mes"]), reverse=True)
    return {"periodos": periodos}


@router.get("/recebimento/baixar", summary="Baixar arquivo de recebimento V2")
async def baixar_recebimento_v2(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    modo_calculo: str = Query(default="hierarquia", description="Modo: 'hierarquia' ou 'centro_custo'"),
) -> FileResponse:
    """Baixa o arquivo de recebimento V2 do período."""
    output_path = _get_recebimento_output_path(mes, ano)

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo de recebimento não encontrado para {mes:02d}/{ano}"
        )

    return FileResponse(
        path=str(output_path),
        filename=output_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/resultados/periodos", summary="Listar períodos com resultados salvos")
async def listar_periodos_resultados() -> Dict[str, Any]:
    """Lista os períodos (mês/ano) que possuem resultados V2 salvos."""
    resultados_dir = ROOT_DIR / "dados_saida"
    periodos: List[Dict[str, Any]] = []

    if not resultados_dir.exists():
        return {"periodos": []}

    for arquivo in resultados_dir.glob("Resultado_Comissoes_V2_*.xlsx"):
        nome = arquivo.name
        # Formatos esperados:
        # Resultado_Comissoes_V2_YYYY-MM.xlsx
        # Resultado_Comissoes_V2_YYYY-MM_CC.xlsx
        try:
            base = nome.replace("Resultado_Comissoes_V2_", "").replace(".xlsx", "")
            modo = "centro_custo" if base.endswith("_CC") else "hierarquia"
            if modo == "centro_custo":
                base = base.replace("_CC", "")
            ano_str, mes_str = base.split("-")
            ano = int(ano_str)
            mes = int(mes_str)
            periodos.append({
                "ano": ano,
                "mes": mes,
                "modo_calculo": modo,
                "arquivo": nome,
            })
        except Exception:
            # Ignorar arquivos fora do padrão
            continue

    # Ordenar por ano/mes desc
    periodos.sort(key=lambda p: (p["ano"], p["mes"], p["modo_calculo"]), reverse=True)
    return {"periodos": periodos}


@router.delete("/resultados", summary="Excluir resultados salvos")
async def excluir_resultados(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000, le=2100),
    modo_calculo: str = Query(default="hierarquia", description="Modo: 'hierarquia' ou 'centro_custo'"),
) -> Dict[str, Any]:
    """Remove o arquivo de resultados salvo para um período específico."""
    modo = modo_calculo.lower().strip()
    sufixo_modo = "_CC" if modo == "centro_custo" else ""
    output_path = ROOT_DIR / "dados_saida" / f"Resultado_Comissoes_V2_{ano}-{mes:02d}{sufixo_modo}.xlsx"

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo de resultados não encontrado para {mes:02d}/{ano} (modo: {modo})"
        )

    try:
        output_path.unlink()
        return {
            "status": "ok",
            "message": f"Resultados removidos para {mes:02d}/{ano} (modo: {modo})",
        }
    except Exception as e:
        logger.exception(f"Erro ao remover resultados V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check")
async def health_check() -> Dict[str, str]:
    """Verifica se o módulo V2 está funcionando."""
    return {"status": "ok", "modulo": "metodo_v2"}


@router.get("/estado-processos/estado-raw", response_model=EstadoV2RawResponse)
async def get_estado_processos_v2_raw(
    modo_calculo: str = Query(default="hierarquia", description="Modo: 'hierarquia' ou 'centro_custo'"),
    busca: Optional[str] = Query(None, description="Busca por texto em processo ou colaborador"),
    status_processo: Optional[str] = Query(None, description="Filtrar por status do processo"),
    status_pagamento: Optional[str] = Query(None, description="Filtrar por status de pagamento"),
    status_calculo: Optional[str] = Query(None, description="Filtrar por status de cálculo de médias"),
) -> EstadoV2RawResponse:
    """Retorna o estado completo dos processos de recebimento V2 em formato raw."""
    estado_path = _get_recebimento_estado_v2_path()

    if not estado_path.exists():
        return EstadoV2RawResponse(
            total_processos=0,
            colunas=[],
            dados=[]
        )

    try:
        df = pd.read_excel(estado_path, dtype=str)
    except Exception as e:
        logger.error(f"Erro ao ler estado V2: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler estado V2: {str(e)}")

    dados: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        estado = row.get("Estado")
        doc = row.get("Documento Normalizado")
        colaborador_id = row.get("Colaborador ID")
        valor_adiantado = row.get("Valor Adiantado")
        valor_faturado = row.get("Valor Faturado")

        valor_total = _safe_float(valor_faturado)
        if valor_total is None:
            valor_total = _safe_float(valor_adiantado) or 0.0

        registro = {
            "PROCESSO": _safe_str(doc),
            "STATUS_PROCESSO": _map_status_processo_v2(_safe_str(estado)),
            "STATUS_PAGAMENTO": None,
            "STATUS_CALCULO_MEDIAS": None,
            "COLABORADORES_ENVOLVIDOS": _parse_colaboradores(colaborador_id),
            "VALOR_TOTAL_PROCESSO": valor_total,
            "TOTAL_PAGO_ACUMULADO": _safe_float(valor_faturado) or 0.0,
            "SALDO_A_RECEBER": None,
            "TOTAL_COMISSAO_ACUMULADA": _safe_float(row.get("Comissão Real")) or 0.0,
            "DATA_ADIANTAMENTO": _format_date(row.get("Data Adiantamento")),
            "DATA_FATURAMENTO": _format_date(row.get("Data Faturamento")),
            "DATA_RECONCILIACAO": _format_date(row.get("Data Reconciliação")),
            "DOCUMENTO_NORMALIZADO": _safe_str(doc),
            "ESTADO_V2": _safe_str(estado),
            "VALOR_ADIANTADO": _safe_float(valor_adiantado),
            "COMISSAO_ADIANTADA": _safe_float(row.get("Comissão Adiantada")),
            "VALOR_FATURADO": _safe_float(valor_faturado),
            "COMISSAO_REAL": _safe_float(row.get("Comissão Real")),
            "AJUSTE_APLICADO": _safe_float(row.get("Ajuste Aplicado")),
            "MES_APURACAO": _safe_str(row.get("Mês Apuração")),
            "ANO_APURACAO": _safe_str(row.get("Ano Apuração")),
        }

        # Preservar colunas originais também
        for col in df.columns:
            if col not in registro:
                registro[col] = _safe_str(row.get(col))

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

    return EstadoV2RawResponse(
        total_processos=len(dados),
        colunas=list(df.columns),
        dados=dados
    )


# ==================== ENDPOINTS PARA ABAS GENÉRICAS V2 ====================

# Abas permitidas no arquivo V2
ABAS_PERMITIDAS_V2 = [
    "HIERARQUIA_V2", 
    "COLABORADORES_V2", 
    "CARGOS_V2",
    "REGRAS_COMISSAO_V2",
    "REGRAS_COMISSAO_CC_V2",
]


def _get_config_path() -> Path:
    """Retorna o caminho do arquivo de configuração V2."""
    return ROOT_DIR / "config" / "REGRAS_COMISSOES_V2.xlsx"


def _get_recebimento_output_path(mes: int, ano: int) -> Path:
    """Retorna caminho do arquivo de recebimento V2 para o período."""
    filename = f"Comissoes_Recebimento_V2_{mes:02d}_{ano}.xlsx"
    return ROOT_DIR / "dados_saida" / filename


def _get_recebimento_estado_v2_path() -> Path:
    """Retorna caminho do arquivo de estado de processos V2."""
    return ROOT_DIR / "dados_saida" / "Estado_Processos_Recebimento_V2.xlsx"


def _map_status_processo_v2(estado: str) -> str:
    """Mapeia o estado V2 para o status esperado pelo frontend."""
    estado_norm = (estado or "").strip().upper()
    if estado_norm == "ADIANTAMENTO":
        return "PENDENTE"
    if estado_norm == "FATURADO":
        return "FATURADO"
    if estado_norm == "RECONCILIADO":
        return "RECONCILIADO"
    return estado_norm or "DESCONHECIDO"


def _safe_float(value: Any) -> Optional[float]:
    """Converte valor para float de forma segura."""
    if pd.isna(value) or value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_str(value: Any) -> Optional[str]:
    """Converte valor para string de forma segura."""
    if pd.isna(value) or value is None:
        return None
    return str(value)


def _format_date(value: Any) -> Optional[str]:
    """Formata datas para string ISO."""
    if pd.isna(value) or value is None:
        return None
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def _parse_colaboradores(value: Any) -> List[str]:
    """Parse da coluna de colaboradores envolvidos."""
    if pd.isna(value) or value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [v.strip() for v in value.replace(";", ",").split(",") if v.strip()]
    return [str(value)]


def _ensure_sheet_exists(config_path: Path, sheet_name: str) -> None:
    """Garante que a aba existe no arquivo Excel. Cria vazia se não existir."""
    if not config_path.exists():
        # Criar arquivo com abas vazias
        with pd.ExcelWriter(str(config_path), engine="openpyxl") as writer:
            pd.DataFrame().to_excel(writer, sheet_name="README", index=False)
            for aba in ABAS_PERMITIDAS_V2:
                pd.DataFrame().to_excel(writer, sheet_name=aba, index=False)
        return
    
    # Verificar se a aba existe
    xl = pd.ExcelFile(str(config_path))
    if sheet_name not in xl.sheet_names:
        # Adicionar aba vazia
        with pd.ExcelWriter(str(config_path), engine="openpyxl", mode="a", if_sheet_exists="error") as writer:
            pd.DataFrame().to_excel(writer, sheet_name=sheet_name, index=False)


@router.get("/aba/{nome_aba}", summary="Ler aba do arquivo V2")
async def ler_aba_v2(
    nome_aba: str,
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    all_pages: bool = Query(False),
) -> Dict[str, Any]:
    """
    Lê dados de uma aba do REGRAS_COMISSOES_V2.xlsx.
    
    Abas disponíveis: HIERARQUIA_V2, COLABORADORES_V2, CARGOS_V2, REGRAS_COMISSAO_V2
    """
    if nome_aba not in ABAS_PERMITIDAS_V2:
        raise HTTPException(
            status_code=400, 
            detail=f"Aba '{nome_aba}' não permitida. Permitidas: {ABAS_PERMITIDAS_V2}"
        )
    
    config_path = _get_config_path()
    
    if not config_path.exists():
        return {"data": [], "columns": [], "total": 0, "page": page, "size": size}
    
    try:
        xl = pd.ExcelFile(str(config_path))
        
        if nome_aba not in xl.sheet_names:
            return {"data": [], "columns": [], "total": 0, "page": page, "size": size}
        
        df = pd.read_excel(xl, sheet_name=nome_aba)
        
        # Converter NaN para None
        df = df.where(pd.notna(df), None)
        
        total = len(df)
        columns = df.columns.tolist()
        
        # Paginação
        if all_pages:
            data = df.to_dict("records")
        else:
            start = (page - 1) * size
            end = start + size
            data = df.iloc[start:end].to_dict("records")
        
        return {
            "data": data,
            "columns": columns,
            "total": total,
            "page": page,
            "size": size,
        }
        
    except Exception as e:
        logger.exception(f"Erro ao ler aba {nome_aba}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aba/{nome_aba}/save", summary="Salvar aba do arquivo V2")
async def salvar_aba_v2(
    nome_aba: str,
    request: Dict[str, Any],
) -> Dict[str, str]:
    """
    Salva dados em uma aba do REGRAS_COMISSOES_V2.xlsx.
    
    Body: { "data": [...], "preserve_columns": true }
    """
    if nome_aba not in ABAS_PERMITIDAS_V2:
        raise HTTPException(
            status_code=400, 
            detail=f"Aba '{nome_aba}' não permitida. Permitidas: {ABAS_PERMITIDAS_V2}"
        )
    
    config_path = _get_config_path()
    data = request.get("data", [])
    preserve_columns = request.get("preserve_columns", True)
    
    try:
        # Carregar arquivo existente ou criar novo
        if config_path.exists():
            xl = pd.ExcelFile(str(config_path))
            existing_sheets = {sheet: pd.read_excel(xl, sheet_name=sheet) for sheet in xl.sheet_names}
        else:
            existing_sheets = {"README": pd.DataFrame({"Info": ["REGRAS_COMISSOES_V2"]})}
        
        # Criar DataFrame dos novos dados
        if data:
            df_new = pd.DataFrame(data)
        else:
            df_new = pd.DataFrame()
        
        # Preservar colunas existentes se solicitado
        if preserve_columns and nome_aba in existing_sheets and not existing_sheets[nome_aba].empty:
            existing_cols = existing_sheets[nome_aba].columns.tolist()
            for col in existing_cols:
                if col not in df_new.columns:
                    df_new[col] = None
            # Reordenar para manter ordem original
            df_new = df_new[[c for c in existing_cols if c in df_new.columns] + 
                           [c for c in df_new.columns if c not in existing_cols]]
        
        # Atualizar aba
        existing_sheets[nome_aba] = df_new
        
        # Salvar todas as abas
        with pd.ExcelWriter(str(config_path), engine="openpyxl") as writer:
            for sheet_name, sheet_df in existing_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Aba {nome_aba} salva com {len(data)} registros")
        return {"status": "ok", "message": f"Aba {nome_aba} salva com {len(data)} registros"}
        
    except Exception as e:
        logger.exception(f"Erro ao salvar aba {nome_aba}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aba/{nome_aba}/valores-unicos/{coluna}", summary="Valores únicos de uma coluna")
async def valores_unicos_v2(nome_aba: str, coluna: str) -> Dict[str, List[str]]:
    """Retorna valores únicos de uma coluna de uma aba V2."""
    if nome_aba not in ABAS_PERMITIDAS_V2:
        raise HTTPException(status_code=400, detail=f"Aba '{nome_aba}' não permitida")
    
    config_path = _get_config_path()
    
    if not config_path.exists():
        return {"valores": []}
    
    try:
        xl = pd.ExcelFile(str(config_path))
        
        if nome_aba not in xl.sheet_names:
            return {"valores": []}
        
        df = pd.read_excel(xl, sheet_name=nome_aba)
        
        if coluna not in df.columns:
            return {"valores": []}
        
        valores = df[coluna].dropna().astype(str).unique().tolist()
        return {"valores": sorted(valores)}
        
    except Exception as e:
        logger.exception(f"Erro ao obter valores únicos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS CC + FABRICANTE ====================

@router.get("/cc-fabricantes", summary="Listar CCs e Fabricantes da Análise Comercial")
async def get_cc_fabricantes() -> Dict[str, Any]:
    """
    Retorna os Centros de Custo e Fabricantes únicos da Análise Comercial.
    
    Usado pelo editor de regras CC para:
    - Popular dropdown de CCs
    - Popular dropdown de Fabricantes  
    - Filtrar dinamicamente (CC ↔ Fab)
    
    Returns:
        {
            "centros_custo": ["CC1", "CC2", ...],
            "fabricantes": ["FAB1", "FAB2", ...],
            "mapeamento": {"CC1": ["FAB_A", "FAB_B"], "CC2": ["FAB_C"], ...}
        }
    """
    # Tentar encontrar arquivo de dados
    dados_paths = [
        ROOT_DIR / "dados_entrada" / "Analise_Comercial_Completa.xlsx",
        ROOT_DIR / "dados_entrada" / "Analise_Comercial_Completa.csv",
        ROOT_DIR / "Analise_Comercial_Completa.csv",
    ]
    
    df = None
    for path in dados_paths:
        if path.exists():
            try:
                if path.suffix == ".csv":
                    df = pd.read_csv(str(path), encoding="utf-8", low_memory=False)
                else:
                    df = pd.read_excel(str(path))
                break
            except Exception as e:
                logger.warning(f"Erro ao ler {path}: {e}")
                continue
    
    if df is None:
        return {
            "centros_custo": [],
            "fabricantes": [],
            "mapeamento": {},
        }
    
    try:
        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip()
        
        # Colunas esperadas
        col_cc = "Centro Custo-pedido"
        col_fab = "Fabricante"
        
        # Extrair CCs únicos
        centros_custo = []
        if col_cc in df.columns:
            centros_custo = sorted([
                str(v).strip() for v in df[col_cc].dropna().unique() 
                if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
            ])
        
        # Extrair Fabricantes únicos
        fabricantes = []
        if col_fab in df.columns:
            fabricantes = sorted([
                str(v).strip() for v in df[col_fab].dropna().unique()
                if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
            ])
        
        # Construir mapeamento CC -> [Fabricantes]
        mapeamento = {}
        if col_cc in df.columns and col_fab in df.columns:
            for cc in centros_custo:
                mask = df[col_cc].astype(str).str.strip() == cc
                fabs_cc = df.loc[mask, col_fab].dropna().astype(str).str.strip().unique()
                fabs_cc = [f for f in fabs_cc if f and f.lower() not in ("nan", "none")]
                mapeamento[cc] = sorted(fabs_cc)
        
        logger.info(f"CC-Fabricantes: {len(centros_custo)} CCs, {len(fabricantes)} Fabs")
        
        return {
            "centros_custo": centros_custo,
            "fabricantes": fabricantes,
            "mapeamento": mapeamento,
        }
        
    except Exception as e:
        logger.exception(f"Erro ao extrair CC/Fabricantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lookups", summary="Dados de referência para V2")
async def get_lookups_v2() -> Dict[str, Any]:
    """
    Retorna dados de referência para os editores V2:
    - colaboradores (de COLABORADORES_V2: nome + cargo)
    - cargos (de CARGOS_V2)
    - hierarquias (de HIERARQUIA_V2: linhas, grupos, subgrupos, tipos, fabricantes)
    """
    config_path = _get_config_path()
    
    result = {
        "colaboradores": [],
        "cargos": [],
        "hierarquias": {
            "linhas": [],
            "grupos": [],
            "subgrupos": [],
            "tipos_mercadoria": [],
            "fabricantes": [],
        },
    }
    
    if not config_path.exists():
        return result
    
    try:
        xl = pd.ExcelFile(str(config_path))
        
        # Colaboradores
        if "COLABORADORES_V2" in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name="COLABORADORES_V2")
            if "nome_colaborador" in df.columns:
                for _, row in df.iterrows():
                    nome = row.get("nome_colaborador")
                    if nome:
                        result["colaboradores"].append({
                            "nome": nome,
                            "cargo": row.get("cargo") or None,
                        })
        
        # Cargos
        if "CARGOS_V2" in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name="CARGOS_V2")
            if "nome_cargo" in df.columns:
                result["cargos"] = sorted(df["nome_cargo"].dropna().astype(str).unique().tolist())
        
        # Hierarquia
        if "HIERARQUIA_V2" in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name="HIERARQUIA_V2")
            hier_map = {
                "linha": "linhas",
                "grupo": "grupos",
                "subgrupo": "subgrupos",
                "tipo_mercadoria": "tipos_mercadoria",
                "fabricante": "fabricantes",
            }
            for col_src, col_dest in hier_map.items():
                if col_src in df.columns:
                    result["hierarquias"][col_dest] = sorted(
                        [v for v in df[col_src].dropna().astype(str).unique().tolist() if v]
                    )
        
        return result
        
    except Exception as e:
        logger.exception(f"Erro ao obter lookups V2: {e}")
        raise HTTPException(status_code=500, detail=str(e))
