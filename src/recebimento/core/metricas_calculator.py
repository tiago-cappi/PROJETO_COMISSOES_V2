"""
Calcula TCMP (Taxa de Comissão Média Ponderada) e FCMP (Fator de Correção Médio Ponderado)
para processos faturados, reutilizando funções existentes de CalculoComissao.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

from .identificador_colaboradores import IdentificadorColaboradores
from src.core.fc_escada import load_fc_escada_cargos, aplicar_fc_escada


class MetricasCalculator:
    """
    Calcula TCMP e FCMP para processos faturados.
    
    Reutiliza as funções _calcular_fc_para_item e _get_regra_comissao
    da classe CalculoComissao para garantir consistência.
    """
    
    def __init__(self, calculo_comissao_instance):
        """
        Inicializa o calculador de métricas.
        
        Args:
            calculo_comissao_instance: Instância da classe CalculoComissao
                                       (para reutilizar funções existentes)
        """
        self.calc_comissao = calculo_comissao_instance
        
        # Inicializar identificador de colaboradores
        self.identificador = IdentificadorColaboradores(
            df_analise_comercial=calculo_comissao_instance.data.get("ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()),
            colaboradores_df=calculo_comissao_instance.data.get("COLABORADORES", pd.DataFrame()),
            atribuicoes_df=calculo_comissao_instance.data.get("ATRIBUICOES", pd.DataFrame()),
            recebe_por_recebimento_ids=calculo_comissao_instance.recebe_por_recebimento
        )

        # Cache local das configs de escada (por cargo)
        try:
            self._fc_escada_configs_by_cargo = load_fc_escada_cargos(
                calculo_comissao_instance.data.get("FC_ESCADA_CARGOS", pd.DataFrame())
            )
        except Exception:
            self._fc_escada_configs_by_cargo = {}
    
    def calcular_metricas_processo(
        self,
        processo: str,
        mes_apuracao: int,
        ano_apuracao: int,
        status_processo: str = None
    ) -> Dict:
        """
        Calcula TCMP e FCMP por colaborador para um processo.
        
        Args:
            processo: ID do processo
            mes_apuracao: Mês de apuração (1-12)
            ano_apuracao: Ano de apuração (ex: 2025)
            status_processo: Status do processo na Análise Comercial (opcional).
                            Se não for FATURADO, FCMP será forçado a 1.0.
        
        Returns:
            Dict com:
            - 'TCMP': Dict {nome_colaborador: tcmp}
            - 'FCMP': Dict {nome_colaborador: fcmp}
            - 'colaboradores': Lista de nomes
        """
        print(f"[RECEBIMENTO] [MÉTRICAS] Iniciando cálculo de métricas para processo={processo}, mes={mes_apuracao}, ano={ano_apuracao}")
        processo = str(processo).strip()
        
        # 1. Buscar TODOS os itens do processo no Analise_Comercial_Completa
        df_comercial = self.calc_comissao.data.get("ANALISE_COMERCIAL_COMPLETA", pd.DataFrame())
        
        if df_comercial.empty:
            print(f"[RECEBIMENTO] [MÉTRICAS] AVISO: Análise Comercial vazia")
            return {"TCMP": {}, "FCMP": {}, "colaboradores": []}
        
        # Encontrar coluna de processo
        proc_col = self._encontrar_coluna(df_comercial, ["processo", "Processo", "PROCESSO"])
        if not proc_col:
            print(f"[RECEBIMENTO] [MÉTRICAS] AVISO: Coluna 'Processo' não encontrada")
            return {"TCMP": {}, "FCMP": {}, "colaboradores": []}
        
        itens = df_comercial[
            df_comercial[proc_col].astype(str).str.strip() == processo
        ]
        
        if itens.empty:
            print(f"[RECEBIMENTO] [MÉTRICAS] AVISO: Nenhum item encontrado para o processo {processo}")
            return {"TCMP": {}, "FCMP": {}, "colaboradores": []}
        else:
            print(f"[RECEBIMENTO] [MÉTRICAS] Itens encontrados para processo {processo}: {len(itens)}")
        
        # Verificar se deve calcular FCMP real ou usar 1.0 (para processos não faturados)
        # Se status_processo não foi passado, tentar descobrir do DataFrame
        if status_processo is None:
            status_col = self._encontrar_coluna(df_comercial, ["Status Processo", "status processo", "STATUS_PROCESSO"])
            if status_col:
                status_raw = itens.iloc[0].get(status_col, "")
                status_processo = str(status_raw).strip().upper() if pd.notna(status_raw) else ""
        
        # REGRA: Se o processo NÃO está FATURADO, FCMP = 1.0 (sem ajuste de metas)
        forcar_fcmp_1 = (status_processo or "").upper() != "FATURADO"
        if forcar_fcmp_1:
            print(f"[RECEBIMENTO] [MÉTRICAS] Processo {processo} não faturado (status={status_processo}). FCMP será forçado a 1.0")
        
        # 2. Identificar colaboradores que recebem por recebimento
        colaboradores = self.identificador.identificar_colaboradores(processo)
        
        if not colaboradores:
            print(f"[RECEBIMENTO] [MÉTRICAS] AVISO: Nenhum colaborador elegível por recebimento encontrado para o processo {processo}")
            return {"TCMP": {}, "FCMP": {}, "colaboradores": []}
        else:
            nomes = [c['nome'] for c in colaboradores]
            print(f"[RECEBIMENTO] [MÉTRICAS] Colaboradores identificados ({len(nomes)}): {nomes}")
        
        # 3. Estruturas para acumular dados por colaborador
        dados_por_colaborador = {}
        
        for colab in colaboradores:
            nome = colab["nome"]
            cargo = colab["cargo"]
            
            dados_por_colaborador[nome] = {
                "cargo": cargo,
                "valores": [],
                "taxas": [],
                "fcs": [],
                "itens_detalhes": []  # Lista de dicts com detalhes de cada item
            }
        
        # 4. Para cada item do processo
        for _, item in itens.iterrows():
            valor_item = self._obter_valor_item(item)
            
            if valor_item <= 0:
                continue
            
            # Para cada colaborador
            for colab in colaboradores:
                nome = colab["nome"]
                cargo = colab["cargo"]
                
                # Calcular FC usando função existente (capturando detalhes para auditoria)
                fc_detalhes_item = {}
                
                # REGRA: Se processo não faturado, FCMP = 1.0 (sem ajuste de metas)
                if forcar_fcmp_1:
                    fc = 1.0
                    fc_detalhes_item = {"nota": "FCMP=1.0 (processo não faturado)"}
                else:
                    try:
                        fc, fc_detalhes_item = self.calc_comissao._calcular_fc_para_item(
                            nome_colab=nome,
                            cargo_colab=cargo,
                            item_faturado=item.to_dict(),
                            mes_apuracao_override=mes_apuracao,
                            ano_apuracao_override=ano_apuracao
                        )
                    except Exception as e:
                        print(f"[RECEBIMENTO] [MÉTRICAS] [FC] ERRO ao calcular FC: {e}")
                        fc = 1.0  # Fallback para 1.0 em caso de erro
                        fc_detalhes_item = {"erro": str(e)}
                
                # Obter regra de comissão
                taxa_rateio_detalhes = 0.0
                fatia_cargo_detalhes = 0.0
                try:
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA] Buscando regra para:")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - Colaborador: {nome}, Cargo: {cargo}")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - Linha: {str(item.get('Negócio', '')).strip()}")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - Grupo: {str(item.get('Grupo', '')).strip()}")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - Subgrupo: {str(item.get('Subgrupo', '')).strip()}")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - Tipo de Mercadoria: {str(item.get('Tipo de Mercadoria', '')).strip()}")
                    
                    regra = self.calc_comissao._get_regra_comissao(
                        linha=str(item.get("Negócio", "")).strip(),
                        grupo=str(item.get("Grupo", "")).strip(),
                        subgrupo=str(item.get("Subgrupo", "")).strip(),
                        tipo_mercadoria=str(item.get("Tipo de Mercadoria", "")).strip(),
                        cargo=cargo
                    )
                    
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA] Regra obtida: {regra}")
                    
                    taxa_rateio = float(regra.get("taxa_rateio_maximo_pct", 0.0) or 0.0) / 100.0
                    fatia_cargo = float(regra.get("fatia_cargo_pct", 0.0) or 0.0) / 100.0
                    taxa = taxa_rateio * fatia_cargo
                    
                    # Salvar para usar nos detalhes
                    taxa_rateio_detalhes = taxa_rateio
                    fatia_cargo_detalhes = fatia_cargo
                    
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - taxa_rateio: {taxa_rateio}")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - fatia_cargo: {fatia_cargo}")
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA]   - taxa final: {taxa}")
                except Exception as e:
                    print(f"[RECEBIMENTO] [MÉTRICAS] [TAXA] ERRO ao buscar regra: {e}")
                    import traceback
                    traceback.print_exc()
                    taxa = 0.0
                
                # Acumular dados
                dados_por_colaborador[nome]["valores"].append(valor_item)
                dados_por_colaborador[nome]["taxas"].append(taxa)
                dados_por_colaborador[nome]["fcs"].append(fc)
                
                # Processar detalhes do FC para formato legível
                fc_componentes = []
                if fc_detalhes_item:
                    # Mapear nomes legíveis para cada tipo de meta
                    nomes_metas = {
                        "rentabilidade": "Rentabilidade",
                        "faturamento_linha": "Faturamento da Linha",
                        "conversao_linha": "Conversão da Linha",
                        "faturamento_individual": "Faturamento Individual",
                        "conversao_individual": "Conversão Individual",
                        "retencao_clientes": "Retenção de Clientes",
                        "meta_fornecedor_1": "Meta Fornecedor 1",
                        "meta_fornecedor_2": "Meta Fornecedor 2"
                    }
                    
                    for tipo_meta, detalhes in fc_detalhes_item.items():
                        if isinstance(detalhes, dict):
                            fc_componentes.append({
                                "nome_meta": nomes_metas.get(tipo_meta, tipo_meta.replace("_", " ").title()),
                                "peso": float(detalhes.get("peso", 0.0)),
                                "realizado": float(detalhes.get("realizado", 0.0)),
                                "meta": float(detalhes.get("meta", 0.0)) if detalhes.get("meta") is not None else 0.0,
                                "atingimento": float(detalhes.get("atingimento", 0.0)),
                                "atingimento_cap": float(detalhes.get("atingimento_cap", 0.0)),
                                "componente_fc": float(detalhes.get("componente_fc", 0.0))
                            })
                
                # Acumular detalhes do item para auditoria
                dados_por_colaborador[nome]["itens_detalhes"].append({
                    "negocio": str(item.get("Negócio", "")).strip(),
                    "grupo": str(item.get("Grupo", "")).strip(),
                    "subgrupo": str(item.get("Subgrupo", "")).strip(),
                    "tipo_mercadoria": str(item.get("Tipo de Mercadoria", "")).strip(),
                    "valor": float(valor_item),
                    "taxa": float(taxa),
                    "fc": float(fc),
                    "taxa_rateio": float(taxa_rateio_detalhes),
                    "fatia_cargo": float(fatia_cargo_detalhes),
                    "fc_detalhes": {
                        "componentes": fc_componentes,
                        "fc_total": float(fc)
                    } if fc_componentes else None
                })
        
        # 5. Calcular médias ponderadas
        tcmp_dict = {}
        fcmp_dict = {}
        fcmp_aplicado_dict = {}
        tcmp_detalhes_dict = {}
        fcmp_detalhes_dict = {}
        fcmp_escada_detalhes_dict = {}
        
        for nome, dados in dados_por_colaborador.items():
            valores = np.array(dados["valores"])
            taxas = np.array(dados["taxas"])
            fcs = np.array(dados["fcs"])
            
            if len(valores) == 0 or valores.sum() == 0:
                tcmp_dict[nome] = 0.0
                fcmp_dict[nome] = 0.0
                tcmp_detalhes_dict[nome] = {"itens": [], "total_valor": 0.0}
                fcmp_detalhes_dict[nome] = {"itens": [], "total_valor": 0.0}
                continue
            
            # TCMP = média ponderada das taxas
            tcmp_dict[nome] = float((taxas * valores).sum() / valores.sum())
            
            # FCMP = média ponderada dos FCs
            fcmp_dict[nome] = float((fcs * valores).sum() / valores.sum())

            # Aplicar escada somente depois do FCMP estar calculado (FCMP é rampa; escada é o multiplicador final)
            cargo_nome = str(dados.get("cargo", "") or "").strip()
            fcmp_aplicado, detalhes_escada = aplicar_fc_escada(
                performance=fcmp_dict[nome],
                cargo=cargo_nome,
                configs_por_cargo=self._fc_escada_configs_by_cargo,
            )
            fcmp_aplicado_dict[nome] = float(fcmp_aplicado)
            fcmp_escada_detalhes_dict[nome] = detalhes_escada
            
            # Armazenar detalhes para auditoria
            tcmp_detalhes_dict[nome] = {
                "itens": dados["itens_detalhes"],
                "total_valor": float(valores.sum()),
                "soma_ponderada": float((taxas * valores).sum()),
                "tcmp_final": float((taxas * valores).sum() / valores.sum())
            }
            
            fcmp_detalhes_dict[nome] = {
                "itens": dados["itens_detalhes"],
                "total_valor": float(valores.sum()),
                "soma_ponderada": float((fcs * valores).sum()),
                "fcmp_final": float((fcs * valores).sum() / valores.sum())
            }
        
        print(f"[RECEBIMENTO] [MÉTRICAS] Resultado: TCMP({len(tcmp_dict)}), FCMP({len(fcmp_dict)})")
        
        return {
            "TCMP": tcmp_dict,
            "FCMP": fcmp_dict,
            "FCMP_APLICADO": fcmp_aplicado_dict,
            "TCMP_DETALHES": tcmp_detalhes_dict,
            "FCMP_DETALHES": fcmp_detalhes_dict,
            "FCMP_ESCADA_DETALHES": fcmp_escada_detalhes_dict,
            "colaboradores": list(tcmp_dict.keys())
        }
    
    def verificar_processo_faturado_no_mes(
        self,
        processo: str,
        mes: int,
        ano: int
    ) -> bool:
        """
        Verifica se processo foi faturado no mês/ano especificado.
        
        Args:
            processo: ID do processo
            mes: Mês (1-12)
            ano: Ano (ex: 2025)
        
        Returns:
            True se processo foi faturado no mês/ano, False caso contrário
        """
        processo = str(processo).strip()
        
        df_comercial = self.calc_comissao.data.get("ANALISE_COMERCIAL_COMPLETA", pd.DataFrame())
        
        if df_comercial.empty:
            return False
        
        # Encontrar colunas
        proc_col = self._encontrar_coluna(df_comercial, ["processo", "Processo", "PROCESSO"])
        status_col = self._encontrar_coluna(
            df_comercial,
            ["Status Processo", "status processo", "STATUS_PROCESSO"]
        )
        data_col = self._encontrar_coluna(
            df_comercial,
            ["Dt Emissão", "dt emissão", "DT_EMISSAO", "Data Emissão"]
        )
        nf_col = self._encontrar_coluna(
            df_comercial,
            ["Numero NF", "numero nf", "número nf", "num nf"]
        )
        
        if not proc_col or not status_col:
            return False
        
        # Filtrar por processo
        mask_processo = df_comercial[proc_col].astype(str).str.strip() == processo
        
        # Filtrar por status faturado
        mask_faturado = df_comercial[status_col].astype(str).str.strip().str.upper() == "FATURADO"
        # Alternativa: Numero NF não vazio
        if nf_col:
            nf_vals = df_comercial[nf_col].astype(str).str.strip().str.upper()
            mask_nf = (~nf_vals.isna()) & (nf_vals != "") & (nf_vals != "NAN")
        else:
            mask_nf = False
        
        # Filtrar por mês/ano (se coluna de data existir)
        if data_col:
            try:
                df_comercial[data_col] = pd.to_datetime(df_comercial[data_col], errors='coerce')
                mask_mes = df_comercial[data_col].dt.month == mes
                mask_ano = df_comercial[data_col].dt.year == ano
                mask = mask_processo & (mask_faturado | mask_nf) & mask_mes & mask_ano
            except Exception:
                mask = mask_processo & (mask_faturado | mask_nf)
        else:
            mask = mask_processo & (mask_faturado | mask_nf)
        
        return mask.any()
    
    def _obter_valor_item(self, item: pd.Series, status_processo: str = None) -> float:
        """
        Obtém o valor do item de forma inteligente.
        
        Regra:
        - Primeiro tenta Valor Realizado
        - Se não existir ou for zero/NaN, usa Valor Orçado
        
        Args:
            item: Series do item
            status_processo: Status do processo (opcional, para otimizar busca)
        
        Returns:
            Valor do item ou 0.0
        """
        # Primeiro tentar Valor Realizado
        valor_realizado_col = self._encontrar_coluna_item(
            item,
            ["Valor Realizado", "valor realizado", "VALOR_REALIZADO"]
        )
        
        valor = 0.0
        if valor_realizado_col:
            raw_val = item.get(valor_realizado_col)
            try:
                valor_convertido = pd.to_numeric(raw_val, errors='coerce')
                # Verificar se é válido (não NaN e não None)
                if pd.notna(valor_convertido) and valor_convertido != 0:
                    valor = float(valor_convertido)
            except Exception:
                pass
        
        # Se Valor Realizado não existir, for zero ou NaN, tentar Valor Orçado
        if valor == 0.0:
            valor_orcado_col = self._encontrar_coluna_item(
                item,
                ["Valor Orçado", "valor orçado", "Valor Orcado", "VALOR_ORCADO"]
            )
            if valor_orcado_col:
                raw_val = item.get(valor_orcado_col)
                try:
                    valor_convertido = pd.to_numeric(raw_val, errors='coerce')
                    # Verificar se é válido (não NaN e não None)
                    if pd.notna(valor_convertido):
                        valor = float(valor_convertido)
                except Exception:
                    pass
        
        return valor
    
    def _encontrar_coluna(self, df: pd.DataFrame, nomes_possiveis: list) -> Optional[str]:
        """Encontra uma coluna no DataFrame."""
        if df.empty:
            return None
        
        # Remover BOM (\ufeff) e normalizar
        colunas_df = {col.lower().strip().replace("\ufeff", ""): col for col in df.columns}
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_df:
                return colunas_df[nome_norm]
        
        return None
    
    def _encontrar_coluna_item(self, item: pd.Series, nomes_possiveis: list) -> Optional[str]:
        """Encontra uma coluna no Series (item)."""
        if item.empty:
            return None
        
        colunas_item = {str(col).lower().strip(): col for col in item.index}
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_item:
                return colunas_item[nome_norm]
        
        return None

