"""
Calcula TCMP (Taxa de Comissão Média Ponderada) e FCMP (Fator de Correção Médio Ponderado)
para processos faturados, reutilizando funções existentes de CalculoComissao.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

from .identificador_colaboradores import IdentificadorColaboradores


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
    
    def calcular_metricas_processo(
        self,
        processo: str,
        mes_apuracao: int,
        ano_apuracao: int
    ) -> Dict:
        """
        Calcula TCMP e FCMP por colaborador para um processo.
        
        Args:
            processo: ID do processo
            mes_apuracao: Mês de apuração (1-12)
            ano_apuracao: Ano de apuração (ex: 2025)
        
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
                "valores": [],
                "taxas": [],
                "fcs": []
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
                
                # Calcular FC usando função existente
                try:
                    fc, _ = self.calc_comissao._calcular_fc_para_item(
                        nome_colab=nome,
                        cargo_colab=cargo,
                        item_faturado=item.to_dict(),
                        mes_apuracao_override=mes_apuracao,
                        ano_apuracao_override=ano_apuracao
                    )
                except Exception:
                    fc = 0.0
                
                # Obter regra de comissão
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
        
        # 5. Calcular médias ponderadas
        tcmp_dict = {}
        fcmp_dict = {}
        
        for nome, dados in dados_por_colaborador.items():
            valores = np.array(dados["valores"])
            taxas = np.array(dados["taxas"])
            fcs = np.array(dados["fcs"])
            
            if len(valores) == 0 or valores.sum() == 0:
                tcmp_dict[nome] = 0.0
                fcmp_dict[nome] = 0.0
                continue
            
            # TCMP = média ponderada das taxas
            tcmp_dict[nome] = float((taxas * valores).sum() / valores.sum())
            
            # FCMP = média ponderada dos FCs
            fcmp_dict[nome] = float((fcs * valores).sum() / valores.sum())
        
        print(f"[RECEBIMENTO] [MÉTRICAS] Resultado: TCMP({len(tcmp_dict)}), FCMP({len(fcmp_dict)})")
        
        return {
            "TCMP": tcmp_dict,
            "FCMP": fcmp_dict,
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
    
    def _obter_valor_item(self, item: pd.Series) -> float:
        """
        Obtém o valor realizado de um item.
        
        Args:
            item: Series do item
        
        Returns:
            Valor realizado ou 0.0
        """
        valor_col = self._encontrar_coluna_item(
            item,
            ["Valor Realizado", "valor realizado", "VALOR_REALIZADO"]
        )
        
        if valor_col:
            try:
                return float(pd.to_numeric(item.get(valor_col, 0.0), errors='coerce') or 0.0)
            except Exception:
                pass
        
        return 0.0
    
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

