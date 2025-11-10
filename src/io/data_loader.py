"""
Módulo para carregar todos os arquivos de dados de entrada.
Responsável por ler arquivos mensais (Faturados, Conversões, etc.) e arquivos opcionais.
"""

import pandas as pd
import os
import glob
from typing import Dict, List, Optional
from src.utils.logging import ValidationLogger


class DataLoader:
    """
    Classe para carregar todos os arquivos de dados de entrada.
    """
    
    def __init__(self, validation_logger: Optional[ValidationLogger] = None):
        """
        Inicializa o DataLoader.
        
        Args:
            validation_logger: Instância opcional de ValidationLogger para registrar avisos/erros
        """
        self.validation_logger = validation_logger
    
    def load_input_data(
        self,
        mes: int,
        ano: int,
        base_path: str = ".",
        arquivo_faturados: Optional[str] = None,
        arquivo_conversoes: Optional[str] = None,
        arquivo_faturados_ytd: Optional[str] = None,
        arquivo_rentabilidade: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Carrega todos os arquivos de dados de entrada.
        
        Args:
            mes: Mês de apuração
            ano: Ano de apuração
            base_path: Caminho base para localizar arquivos
            arquivo_faturados: Caminho opcional para arquivo de faturados
            arquivo_conversoes: Caminho opcional para arquivo de conversões
            arquivo_faturados_ytd: Caminho opcional para arquivo de faturados YTD
            arquivo_rentabilidade: Caminho opcional para arquivo de rentabilidade
        
        Returns:
            Dicionário com todos os DataFrames de dados de entrada
        """
        data = {}
        
        # Carregar FATURADOS (com fallback)
        data["FATURADOS"] = self._try_read_file(
            arquivo_faturados,
            [
                "Faturados.xlsx",
                "Faturados.xls",
                "Faturados.csv",
            ],
            pattern_start="faturados",
        )
        
        # Carregar CONVERSOES (com fallback)
        data["CONVERSOES"] = self._try_read_file(
            arquivo_conversoes,
            [
                "Conversões.xlsx",
                "Conversoes.xlsx",
                "Conversões.csv",
                "Conversoes.csv",
            ],
            pattern_start="convers",
        )
        
        # Carregar RENTABILIDADE_REALIZADA
        data["RENTABILIDADE_REALIZADA"] = self.load_rentabilidade(
            mes, ano, base_path, arquivo_rentabilidade
        )
        
        # Carregar RETENCAO_CLIENTES
        data["RETENCAO_CLIENTES"] = self._load_retencao_clientes(base_path)
        
        # Carregar FATURADOS_YTD
        data["FATURADOS_YTD"] = self._load_faturados_ytd(
            base_path, arquivo_faturados_ytd
        )
        
        # Carregar RECEBIMENTOS (opcional)
        data["RECEBIMENTOS"] = self._load_recebimentos(base_path)
        
        # Carregar PAGAMENTOS_REGULARES (opcional)
        data["PAGAMENTOS_REGULARES"] = self._load_pagamentos_regulares(base_path)
        
        # Carregar ANALISE_COMERCIAL_COMPLETA (opcional, suporta .csv)
        data["ANALISE_COMERCIAL_COMPLETA"] = self._load_analise_comercial(base_path)
        
        # Carregar STATUS_PAGAMENTOS (opcional)
        data["STATUS_PAGAMENTOS"] = self._load_status_pagamentos(base_path)
        
        # Normalizar colunas e strings
        data = self.normalize_input_dataframes(data)
        
        return data
    
    def _try_read_file(
        self,
        primary_path: Optional[str],
        fallback_candidates: List[str],
        pattern_start: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Tenta ler um arquivo com múltiplos fallbacks.
        
        Args:
            primary_path: Caminho principal do arquivo (pode ser None)
            fallback_candidates: Lista de nomes de arquivo para tentar como fallback
            pattern_start: Prefixo para busca por padrão no diretório atual (opcional)
        
        Returns:
            DataFrame carregado ou DataFrame vazio se não encontrar
        """
        # Tentar caminho principal primeiro
        if primary_path and os.path.exists(primary_path):
            try:
                return pd.read_excel(primary_path)
            except Exception:
                pass
        
        # Tentar candidatos de fallback
        for candidate in fallback_candidates:
            try:
                if os.path.exists(candidate):
                    return pd.read_excel(candidate)
            except Exception:
                continue
        
        # Tentar busca por padrão no diretório atual
        if pattern_start:
            try:
                for fname in os.listdir("."):
                    if (
                        fname.lower().startswith(pattern_start)
                        and fname.lower().endswith((".xls", ".xlsx", ".csv"))
                    ):
                        try:
                            return pd.read_excel(fname)
                        except Exception:
                            continue
            except Exception:
                pass
        
        return pd.DataFrame()
    
    def load_rentabilidade(
        self,
        mes: int,
        ano: int,
        base_path: str = ".",
        arquivo_rentabilidade: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Carrega arquivo de rentabilidade agrupada.
        
        Procura em: rentabilidades/rentabilidade_{MM}_{AAAA}_agrupada.xlsx
        
        Args:
            mes: Mês de apuração
            ano: Ano de apuração
            base_path: Caminho base para localizar a pasta rentabilidades
            arquivo_rentabilidade: Caminho opcional direto para o arquivo
        
        Returns:
            DataFrame com rentabilidade ou DataFrame vazio com estrutura esperada
        """
        # Se foi fornecido caminho direto, usar
        if arquivo_rentabilidade and os.path.exists(arquivo_rentabilidade):
            try:
                return pd.read_excel(arquivo_rentabilidade)
            except Exception:
                pass
        
        # Tentar encontrar arquivo na pasta rentabilidades
        mm = str(mes).zfill(2)
        rentabilidades_dir = os.path.join(base_path, "dados_entrada", "rentabilidades")
        if not os.path.exists(rentabilidades_dir):
            rentabilidades_dir = os.path.join(base_path, "rentabilidades")
        
        if os.path.exists(rentabilidades_dir):
            # Buscar arquivo com padrão
            pattern = os.path.join(rentabilidades_dir, f"*{mm}*{ano}*agrupada*.xlsx")
            encontrados = glob.glob(pattern)
            if encontrados:
                try:
                    return pd.read_excel(encontrados[0])
                except Exception:
                    pass
        
        # Se não encontrou, retornar DataFrame vazio com estrutura esperada
        return pd.DataFrame(
            columns=[
                "Negócio",
                "Grupo",
                "Subgrupo",
                "Tipo de Mercadoria",
                "rentabilidade_realizada_pct",
            ]
        )
    
    def _load_retencao_clientes(self, base_path: str) -> pd.DataFrame:
        """Carrega arquivo de retenção de clientes."""
        arquivo_retencao = os.path.join(base_path, "Retencao_Clientes.xlsx")
        try:
            if os.path.exists(arquivo_retencao):
                return pd.read_excel(arquivo_retencao)
        except FileNotFoundError:
            pass
        except Exception:
            if self.validation_logger:
                self.validation_logger.aviso(
                    f"Erro ao carregar Retencao_Clientes.xlsx",
                    {"path": arquivo_retencao}
                )
        
        return pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )
    
    def _load_faturados_ytd(
        self, base_path: str, arquivo_faturados_ytd: Optional[str] = None
    ) -> pd.DataFrame:
        """Carrega arquivo de faturados YTD."""
        if arquivo_faturados_ytd and os.path.exists(arquivo_faturados_ytd):
            try:
                return pd.read_excel(arquivo_faturados_ytd, parse_dates=["Dt Emissão"])
            except Exception:
                pass
        
        # Tentar nome padrão
        arquivo_padrao = os.path.join(base_path, "Faturados_YTD.xlsx")
        try:
            if os.path.exists(arquivo_padrao):
                return pd.read_excel(arquivo_padrao, parse_dates=["Dt Emissão"])
        except Exception:
            pass
        
        return pd.DataFrame(
            columns=["Dt Emissão", "Fabricante", "Valor Realizado"]
        )
    
    def _load_recebimentos(self, base_path: str) -> pd.DataFrame:
        """Carrega arquivo de recebimentos do mês (opcional)."""
        arquivo_recebimentos = os.path.join(
            base_path, "Recebimentos_do_Mes.xlsx"
        )
        try:
            if os.path.exists(arquivo_recebimentos):
                return pd.read_excel(arquivo_recebimentos)
        except Exception:
            pass
        
        return pd.DataFrame(
            columns=[
                "PROCESSO",
                "DATA_RECEBIMENTO",
                "VALOR_RECEBIDO",
                "ID_CLIENTE",
                "TIPO_PAGAMENTO",
                "FONTE_ORIGINAL",
            ]
        )
    
    def _load_pagamentos_regulares(self, base_path: str) -> pd.DataFrame:
        """Carrega arquivo de pagamentos regulares do mês (opcional)."""
        arquivo_pagamentos = os.path.join(
            base_path, "Pagamentos_Regulares_do_Mes.xlsx"
        )
        try:
            if os.path.exists(arquivo_pagamentos):
                return pd.read_excel(arquivo_pagamentos)
        except Exception:
            pass
        
        return pd.DataFrame(
            columns=[
                "DOCUMENTO_NORMALIZADO",
                "DOCUMENTO_ORIGINAL",
                "DATA_PAGAMENTO",
                "VALOR_PAGO",
                "ID_CLIENTE",
                "TIPO_PAGAMENTO",
                "FONTE_ORIGINAL",
            ]
        )
    
    def _load_analise_comercial(self, base_path: str) -> pd.DataFrame:
        """
        Carrega arquivo de análise comercial completa (opcional, suporta .csv).
        
        Procura por: Analise_Comercial_Completa.xlsx, .xls ou .csv
        """
        analise_candidates = [
            os.path.join(base_path, "Analise_Comercial_Completa.xlsx"),
            os.path.join(base_path, "Analise_Comercial_Completa.xls"),
            os.path.join(base_path, "Analise_Comercial_Completa.csv"),
            os.path.join(base_path, "dados_entrada", "Analise_Comercial_Completa.xlsx"),
            os.path.join(base_path, "dados_entrada", "Analise_Comercial_Completa.xls"),
            os.path.join(base_path, "dados_entrada", "Analise_Comercial_Completa.csv"),
        ]
        
        analise_path = None
        for p in analise_candidates:
            if os.path.exists(p):
                analise_path = p
                break
        
        if analise_path is None:
            if self.validation_logger:
                self.validation_logger.aviso(
                    "ANALISE_COMERCIAL_COMPLETA ausente (procurados .xlsx/.xls/.csv).",
                    {"candidates": analise_candidates},
                )
            return pd.DataFrame()
        
        # Ler CSV ou Excel conforme a extensão
        try:
            if analise_path.lower().endswith(".csv"):
                # Tentar detectar delimitador automaticamente
                df_anal = pd.read_csv(
                    analise_path, sep=None, engine="python", dtype=str
                )
            else:
                # Excel: inferir se existe coluna 'Dt Emissão' para parse_dates
                try:
                    hdrs = pd.read_excel(analise_path, nrows=0).columns.tolist()
                except Exception:
                    hdrs = []
                parse_dates = (
                    ["Dt Emissão"] if "Dt Emissão" in hdrs else False
                )
                df_anal = pd.read_excel(
                    analise_path, parse_dates=parse_dates, dtype=str
                )
            
            # Normalizar colunas e strings (trim)
            if not df_anal.empty:
                df_anal.columns = df_anal.columns.str.strip()
                for c in df_anal.select_dtypes(include=["object"]):
                    df_anal[c] = df_anal[c].astype(str).str.strip()
            
            return df_anal
        except Exception as e_read:
            if self.validation_logger:
                self.validation_logger.aviso(
                    f"Falha ao ler {analise_path}: {e_read}",
                    {"path": analise_path},
                )
            return pd.DataFrame()
    
    def _load_status_pagamentos(self, base_path: str) -> pd.DataFrame:
        """Carrega arquivo de status de pagamentos (opcional)."""
        arquivo_status = os.path.join(
            base_path, "Status_Pagamentos_Processos.xlsx"
        )
        try:
            if os.path.exists(arquivo_status):
                return pd.read_excel(arquivo_status)
        except Exception:
            pass
        
        return pd.DataFrame(
            columns=["PROCESSO", "VALOR_ORIGINAL", "STATUS_PAGAMENTO"]
        )
    
    def normalize_input_dataframes(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Normaliza colunas e strings de todos os DataFrames de dados de entrada.
        
        Args:
            data: Dicionário com DataFrames a normalizar
        
        Returns:
            Dicionário com DataFrames normalizados
        """
        for df_name, df_any in list(data.items()):
            try:
                if not isinstance(df_any, pd.DataFrame):
                    continue
                try:
                    df_any.columns = df_any.columns.astype(str).str.strip()
                except Exception:
                    pass
                for col in df_any.columns:
                    s = df_any[col]
                    if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
                        try:
                            df_any[col] = s.apply(
                                lambda v: v.strip() if isinstance(v, str) else v
                            )
                        except Exception:
                            pass
                data[df_name] = df_any
            except Exception as e:
                if self.validation_logger:
                    self.validation_logger.aviso(
                        f"Falha ao normalizar strings para {df_name}: {e}",
                        {},
                    )
        
        return data

