"""
Gerenciador de estado dos processos de recebimento.
"""

import pandas as pd
import os
import json
from typing import Dict, Optional, Any
from datetime import datetime
from .state_schema import COLUNAS_ESTADO, VALORES_PADRAO_ESTADO


class StateManager:
    """
    Gerencia o estado persistente dos processos de recebimento.
    
    Mantém um DataFrame interno com o estado de cada processo e fornece
    métodos para atualizar valores, métricas e status.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de estado."""
        self.estado_df = pd.DataFrame(columns=COLUNAS_ESTADO)
    
    def carregar_estado_anterior(self, filepath: str) -> bool:
        """
        Carrega estado de execução anterior.
        
        Args:
            filepath: Caminho para o arquivo Excel com a aba ESTADO
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        try:
            if os.path.exists(filepath):
                # Tentar ler a aba ESTADO
                self.estado_df = pd.read_excel(filepath, sheet_name="ESTADO")
                
                # Normalizar colunas (case-insensitive, trim)
                self.estado_df.columns = self.estado_df.columns.str.strip()
                
                # Garantir que todas as colunas esperadas existam
                for col in COLUNAS_ESTADO:
                    if col not in self.estado_df.columns:
                        self.estado_df[col] = VALORES_PADRAO_ESTADO.get(col, None)
                
                # Selecionar apenas colunas esperadas
                self.estado_df = self.estado_df[COLUNAS_ESTADO]
                
                # Converter PROCESSO para string
                if "PROCESSO" in self.estado_df.columns:
                    self.estado_df["PROCESSO"] = self.estado_df["PROCESSO"].astype(str).str.strip()
                
                return True
        except Exception:
            # Em caso de erro, criar DataFrame vazio
            self.estado_df = pd.DataFrame(columns=COLUNAS_ESTADO)
        
        return False
    
    def obter_processo(self, processo_id: str) -> Optional[Dict]:
        """
        Retorna dados do processo ou None se não existir.
        
        Args:
            processo_id: ID do processo
        
        Returns:
            Dict com dados do processo ou None
        """
        if self.estado_df.empty:
            return None
        
        processo_id = str(processo_id).strip()
        mask = self.estado_df["PROCESSO"] == processo_id
        
        if mask.any():
            row = self.estado_df[mask].iloc[0]
            return row.to_dict()
        
        return None
    
    def criar_processo(
        self,
        processo_id: str,
        valor_total: float = 0.0,
        status_processo: str = "ORCAMENTO"
    ) -> Dict:
        """
        Cria novo processo no estado.
        
        Args:
            processo_id: ID do processo
            valor_total: Valor total do processo (da Análise Comercial)
            status_processo: Status inicial do processo
        
        Returns:
            Dict com dados do processo criado
        """
        processo_id = str(processo_id).strip()
        
        # Verificar se já existe
        processo_existente = self.obter_processo(processo_id)
        if processo_existente:
            return processo_existente
        
        # Criar novo registro
        novo_registro = VALORES_PADRAO_ESTADO.copy()
        novo_registro["PROCESSO"] = processo_id
        novo_registro["VALOR_TOTAL_PROCESSO"] = valor_total
        novo_registro["SALDO_A_RECEBER"] = valor_total
        novo_registro["STATUS_PROCESSO"] = status_processo
        novo_registro["ULTIMA_ATUALIZACAO"] = datetime.now()
        
        # Adicionar ao DataFrame
        novo_df = pd.DataFrame([novo_registro])
        self.estado_df = pd.concat([self.estado_df, novo_df], ignore_index=True)
        
        return novo_registro
    
    def atualizar_pagamento_adiantamento(
        self,
        processo_id: str,
        valor: float,
        comissao_total: float,
        data_pagamento: Optional[datetime] = None
    ):
        """
        Atualiza estado com novo adiantamento.
        
        Args:
            processo_id: ID do processo
            valor: Valor do adiantamento
            comissao_total: Total de comissões pagas no adiantamento
            data_pagamento: Data do pagamento
        """
        processo_id = str(processo_id).strip()
        mask = self.estado_df["PROCESSO"] == processo_id
        
        if not mask.any():
            # Criar processo se não existir
            self.criar_processo(processo_id)
            mask = self.estado_df["PROCESSO"] == processo_id
        
        # Atualizar valores
        idx = self.estado_df[mask].index[0]
        
        self.estado_df.at[idx, "TOTAL_ANTECIPACOES"] += valor
        self.estado_df.at[idx, "TOTAL_COMISSAO_ANTECIPACOES"] += comissao_total
        self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"] = (
            self.estado_df.at[idx, "TOTAL_ANTECIPACOES"] +
            self.estado_df.at[idx, "TOTAL_PAGAMENTOS_REGULARES"]
        )
        self.estado_df.at[idx, "TOTAL_COMISSAO_ACUMULADA"] = (
            self.estado_df.at[idx, "TOTAL_COMISSAO_ANTECIPACOES"] +
            self.estado_df.at[idx, "TOTAL_COMISSAO_REGULARES"]
        )
        self.estado_df.at[idx, "SALDO_A_RECEBER"] = (
            self.estado_df.at[idx, "VALOR_TOTAL_PROCESSO"] -
            self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"]
        )
        self.estado_df.at[idx, "QUANTIDADE_PAGAMENTOS"] += 1
        
        # Atualizar datas
        if data_pagamento:
            if pd.isna(self.estado_df.at[idx, "DATA_PRIMEIRO_PAGAMENTO"]):
                self.estado_df.at[idx, "DATA_PRIMEIRO_PAGAMENTO"] = data_pagamento
            self.estado_df.at[idx, "DATA_ULTIMO_PAGAMENTO"] = data_pagamento
        
        # Atualizar status de pagamento
        if self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"] >= self.estado_df.at[idx, "VALOR_TOTAL_PROCESSO"]:
            self.estado_df.at[idx, "STATUS_PAGAMENTO"] = "COMPLETO"
        elif self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"] > 0:
            self.estado_df.at[idx, "STATUS_PAGAMENTO"] = "PARCIAL"
        
        self.estado_df.at[idx, "ULTIMA_ATUALIZACAO"] = datetime.now()
    
    def atualizar_pagamento_regular(
        self,
        processo_id: str,
        valor: float,
        comissao_total: float,
        data_pagamento: Optional[datetime] = None
    ):
        """
        Atualiza estado com novo pagamento regular.
        
        Args:
            processo_id: ID do processo
            valor: Valor do pagamento regular
            comissao_total: Total de comissões pagas no pagamento
            data_pagamento: Data do pagamento
        """
        processo_id = str(processo_id).strip()
        mask = self.estado_df["PROCESSO"] == processo_id
        
        if not mask.any():
            # Criar processo se não existir
            self.criar_processo(processo_id)
            mask = self.estado_df["PROCESSO"] == processo_id
        
        # Atualizar valores
        idx = self.estado_df[mask].index[0]
        
        self.estado_df.at[idx, "TOTAL_PAGAMENTOS_REGULARES"] += valor
        self.estado_df.at[idx, "TOTAL_COMISSAO_REGULARES"] += comissao_total
        self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"] = (
            self.estado_df.at[idx, "TOTAL_ANTECIPACOES"] +
            self.estado_df.at[idx, "TOTAL_PAGAMENTOS_REGULARES"]
        )
        self.estado_df.at[idx, "TOTAL_COMISSAO_ACUMULADA"] = (
            self.estado_df.at[idx, "TOTAL_COMISSAO_ANTECIPACOES"] +
            self.estado_df.at[idx, "TOTAL_COMISSAO_REGULARES"]
        )
        self.estado_df.at[idx, "SALDO_A_RECEBER"] = (
            self.estado_df.at[idx, "VALOR_TOTAL_PROCESSO"] -
            self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"]
        )
        self.estado_df.at[idx, "QUANTIDADE_PAGAMENTOS"] += 1
        
        # Atualizar datas
        if data_pagamento:
            if pd.isna(self.estado_df.at[idx, "DATA_PRIMEIRO_PAGAMENTO"]):
                self.estado_df.at[idx, "DATA_PRIMEIRO_PAGAMENTO"] = data_pagamento
            self.estado_df.at[idx, "DATA_ULTIMO_PAGAMENTO"] = data_pagamento
        
        # Atualizar status de pagamento
        if self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"] >= self.estado_df.at[idx, "VALOR_TOTAL_PROCESSO"]:
            self.estado_df.at[idx, "STATUS_PAGAMENTO"] = "COMPLETO"
        elif self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"] > 0:
            self.estado_df.at[idx, "STATUS_PAGAMENTO"] = "PARCIAL"
        
        self.estado_df.at[idx, "ULTIMA_ATUALIZACAO"] = datetime.now()
    
    def definir_metricas(
        self,
        processo_id: str,
        tcmp_dict: Dict[str, float],
        fcmp_dict: Dict[str, float],
        mes_faturamento: str
    ):
        """
        Define TCMP e FCMP para um processo (quando faturado).
        
        Args:
            processo_id: ID do processo
            tcmp_dict: Dict {nome_colaborador: tcmp}
            fcmp_dict: Dict {nome_colaborador: fcmp}
            mes_faturamento: Mês/ano do faturamento (ex: "09/2025")
        """
        processo_id = str(processo_id).strip()
        mask = self.estado_df["PROCESSO"] == processo_id
        
        if not mask.any():
            # Criar processo se não existir
            self.criar_processo(processo_id)
            mask = self.estado_df["PROCESSO"] == processo_id
        
        idx = self.estado_df[mask].index[0]
        
        # Converter dicts para JSON
        self.estado_df.at[idx, "TCMP_JSON"] = json.dumps(tcmp_dict, ensure_ascii=False)
        self.estado_df.at[idx, "FCMP_JSON"] = json.dumps(fcmp_dict, ensure_ascii=False)
        
        # Lista de colaboradores envolvidos
        colaboradores = list(tcmp_dict.keys())
        self.estado_df.at[idx, "COLABORADORES_ENVOLVIDOS"] = ", ".join(colaboradores)
        
        # Atualizar status e mês de faturamento
        self.estado_df.at[idx, "STATUS_CALCULO_MEDIAS"] = "CALCULADO"
        self.estado_df.at[idx, "MES_ANO_FATURAMENTO"] = mes_faturamento
        self.estado_df.at[idx, "STATUS_PROCESSO"] = "FATURADO"
        
        self.estado_df.at[idx, "ULTIMA_ATUALIZACAO"] = datetime.now()
    
    def obter_metricas(self, processo_id: str) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Retorna TCMP e FCMP salvos para um processo.
        
        Args:
            processo_id: ID do processo
        
        Returns:
            Dict com 'TCMP' e 'FCMP' (cada um é um dict {nome: valor})
            ou None se não encontrado ou não calculado
        """
        processo = self.obter_processo(processo_id)
        if not processo:
            return None
        
        if processo.get("STATUS_CALCULO_MEDIAS") != "CALCULADO":
            return None
        
        try:
            tcmp_json = processo.get("TCMP_JSON", "{}")
            fcmp_json = processo.get("FCMP_JSON", "{}")
            
            tcmp_dict = json.loads(tcmp_json) if tcmp_json else {}
            fcmp_dict = json.loads(fcmp_json) if fcmp_json else {}
            
            return {
                "TCMP": tcmp_dict,
                "FCMP": fcmp_dict
            }
        except Exception:
            return None
    
    def atualizar_valor_total_processo(self, processo_id: str, valor_total: float):
        """
        Atualiza o valor total do processo.
        
        Args:
            processo_id: ID do processo
            valor_total: Valor total do processo
        """
        processo_id = str(processo_id).strip()
        mask = self.estado_df["PROCESSO"] == processo_id
        
        if not mask.any():
            self.criar_processo(processo_id, valor_total)
            mask = self.estado_df["PROCESSO"] == processo_id
        
        idx = self.estado_df[mask].index[0]
        self.estado_df.at[idx, "VALOR_TOTAL_PROCESSO"] = valor_total
        self.estado_df.at[idx, "SALDO_A_RECEBER"] = (
            valor_total - self.estado_df.at[idx, "TOTAL_PAGO_ACUMULADO"]
        )
        self.estado_df.at[idx, "ULTIMA_ATUALIZACAO"] = datetime.now()
    
    def obter_processos_cadastrados(self) -> list:
        """
        Retorna lista de IDs de processos cadastrados no estado.
        
        Returns:
            Lista de IDs de processos (strings)
        """
        if self.estado_df.empty or "PROCESSO" not in self.estado_df.columns:
            return []
        
        processos = self.estado_df["PROCESSO"].dropna().astype(str).str.strip().unique().tolist()
        return processos
    
    def obter_dataframe_estado(self) -> pd.DataFrame:
        """
        Retorna DataFrame do estado completo para salvar em Excel.
        
        Returns:
            DataFrame com todas as colunas do estado
        """
        # Garantir que todas as colunas existam
        for col in COLUNAS_ESTADO:
            if col not in self.estado_df.columns:
                self.estado_df[col] = VALORES_PADRAO_ESTADO.get(col, None)
        
        # Selecionar apenas colunas esperadas e ordenar por PROCESSO
        df_retorno = self.estado_df[COLUNAS_ESTADO].copy()
        
        if not df_retorno.empty and "PROCESSO" in df_retorno.columns:
            df_retorno = df_retorno.sort_values("PROCESSO")
        
        return df_retorno

