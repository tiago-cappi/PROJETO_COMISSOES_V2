"""
Módulo para carregar todas as planilhas de configuração.
Responsável por ler REGRAS_COMISSOES.xlsx (ou CSVs individuais) e processar os dados.
"""

import pandas as pd
import os
import logging
from typing import Dict, Set, Any, Optional


class ConfigLoader:
    """
    Classe para carregar e processar todas as planilhas de configuração.
    """
    
    def __init__(self, validation_logger=None):
        """
        Inicializa o ConfigLoader.
        
        Args:
            validation_logger: Instância opcional de ValidationLogger para registrar avisos/erros
        """
        self.validation_logger = validation_logger
        self._logger = None
    
    def load_configs(self, config_path: str = "config/REGRAS_COMISSOES.xlsx") -> Dict[str, pd.DataFrame]:
        """
        Carrega todas as planilhas de configuração.
        
        Tenta carregar de REGRAS_COMISSOES.xlsx primeiro. Se não existir,
        tenta carregar arquivos CSV individuais da pasta config/.
        
        Args:
            config_path: Caminho para o arquivo REGRAS_COMISSOES.xlsx
        
        Returns:
            Dicionário com todas as abas/DataFrames de configuração
        """
        data = {}
        
        # Tentar carregar do arquivo Excel unificado
        if os.path.exists(config_path):
            try:
                regras_data = pd.read_excel(config_path, sheet_name=None)
                data.update(regras_data)
            except Exception as e:
                if self.validation_logger:
                    self.validation_logger.aviso(
                        f"Falha ao carregar {config_path}: {e}. Tentando CSVs individuais.",
                        {"path": config_path}
                    )
                # Fallback: tentar carregar CSVs individuais
                data = self._load_from_csvs()
        else:
            # Se não existe Excel, tentar CSVs
            if self.validation_logger:
                self.validation_logger.aviso(
                    f"Arquivo {config_path} não encontrado. Tentando CSVs individuais.",
                    {"path": config_path}
                )
            data = self._load_from_csvs()
        
        # Carregar CROSS_SELLING separadamente (pode estar no Excel ou ser CSV)
        if "CROSS_SELLING" not in data:
            try:
                if os.path.exists(config_path):
                    data["CROSS_SELLING"] = pd.read_excel(config_path, sheet_name="CROSS_SELLING")
                else:
                    csv_path = os.path.join("config", "CROSS_SELLING.csv")
                    if os.path.exists(csv_path):
                        data["CROSS_SELLING"] = pd.read_csv(csv_path)
                    else:
                        data["CROSS_SELLING"] = pd.DataFrame(
                            columns=["colaborador", "taxa_cross_selling_pct"]
                        )
            except Exception:
                data["CROSS_SELLING"] = pd.DataFrame(
                    columns=["colaborador", "taxa_cross_selling_pct"]
                )
        
        # Normalizar colunas e strings
        data = self.normalize_config_dataframes(data)
        
        # Normalizar colunas especiais
        data = self._normalize_special_columns(data)
        
        return data
    
    def _load_from_csvs(self) -> Dict[str, pd.DataFrame]:
        """
        Carrega configurações de arquivos CSV individuais na pasta config/.
        
        Returns:
            Dicionário com DataFrames carregados dos CSVs
        """
        data = {}
        config_dir = "config"
        
        # Lista de arquivos CSV esperados
        csv_files = [
            "PARAMS.csv",
            "CONFIG_COMISSAO.csv",
            "PESOS_METAS.csv",
            "METAS_APLICACAO.csv",
            "METAS_INDIVIDUAIS.csv",
            "META_RENTABILIDADE.csv",
            "METAS_FORNECEDORES.csv",
            "ATRIBUICOES.csv",
            "COLABORADORES.csv",
            "CARGOS.csv",
            "ALIASES.csv",
            "HIERARQUIA.csv",
            "ENUM_TIPO_META.csv",
        ]
        
        for csv_file in csv_files:
            csv_path = os.path.join(config_dir, csv_file)
            sheet_name = csv_file.replace(".csv", "")
            try:
                if os.path.exists(csv_path):
                    data[sheet_name] = pd.read_csv(csv_path)
            except Exception as e:
                if self.validation_logger:
                    self.validation_logger.aviso(
                        f"Falha ao carregar {csv_path}: {e}",
                        {"path": csv_path}
                    )
                # Criar DataFrame vazio com estrutura esperada
                data[sheet_name] = pd.DataFrame()
        
        return data
    
    def normalize_config_dataframes(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Normaliza colunas e strings de todos os DataFrames de configuração.
        
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
                        {}
                    )
        
        return data
    
    def _normalize_special_columns(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Normaliza colunas especiais (ex: 'fabricante' -> 'fornecedor').
        
        Args:
            data: Dicionário com DataFrames
        
        Returns:
            Dicionário com DataFrames normalizados
        """
        # Normalizar colunas da aba METAS_FORNECEDORES
        if "METAS_FORNECEDORES" in data:
            df_met = data["METAS_FORNECEDORES"]
            if (
                "fabricante" in df_met.columns
                and "fornecedor" not in df_met.columns
            ):
                df_met = df_met.rename(columns={"fabricante": "fornecedor"})
                data["METAS_FORNECEDORES"] = df_met
        
        return data
    
    def process_params(self, params_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Processa o DataFrame PARAMS e converte para dicionário.
        
        Args:
            params_df: DataFrame com colunas 'chave' e 'valor'
        
        Returns:
            Dicionário com parâmetros processados
        """
        params = pd.Series(
            params_df.valor.values, index=params_df.chave
        ).to_dict()
        
        # Parâmetro para escolha default em execuções não interativas
        params["cross_selling_default_option"] = str(
            params.get("cross_selling_default_option", "A")
        ).upper()
        
        return params
    
    def detect_recebimento_colaboradores(
        self, data: Dict[str, pd.DataFrame], logger: Optional[logging.Logger] = None
    ) -> Set[str]:
        """
        Detecta colaboradores que recebem por recebimento.
        
        Verifica:
        1. Coluna TIPO_COMISSAO em CARGOS
        2. Coluna TIPO_COMISSAO em COLABORADORES
        3. Heurística: cargos com nome contendo 'receb' ou 'recebimento'
        
        Args:
            data: Dicionário com DataFrames de configuração
            logger: Logger opcional para mensagens de debug
        
        Returns:
            Set com nomes dos colaboradores que recebem por recebimento
        """
        recebe_set = set()
        
        try:
            # Prefer explicit coluna TIPO_COMISSAO na aba CARGOS
            if "CARGOS" in data and "TIPO_COMISSAO" in data["CARGOS"].columns:
                cargos_rc = data["CARGOS"][
                    data["CARGOS"]["TIPO_COMISSAO"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == "recebimento"
                ]["nome_cargo"].tolist()
                
                if logger:
                    logger.info(f"CARGOS marcados como recebimento: {cargos_rc}")
                
                if cargos_rc and "COLABORADORES" in data:
                    dfcol = data["COLABORADORES"]
                    colabs_receb = (
                        dfcol[dfcol["cargo"].isin(cargos_rc)]["nome_colaborador"]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .tolist()
                    )
                    if logger:
                        logger.info(
                            f"Colaboradores detectados para recebimento (via cargo): {colabs_receb}"
                        )
                    recebe_set.update(colabs_receb)
            
            # Se existir coluna 'TIPO_COMISSAO' em COLABORADORES, use-a direto
            if (
                "COLABORADORES" in data
                and "TIPO_COMISSAO" in data["COLABORADORES"].columns
            ):
                colabs_receb2 = (
                    data["COLABORADORES"][
                        data["COLABORADORES"]["TIPO_COMISSAO"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        == "recebimento"
                    ]["nome_colaborador"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .tolist()
                )
                if logger:
                    logger.info(
                        f"Colaboradores detectados para recebimento (via TIPO_COMISSAO): {colabs_receb2}"
                    )
                recebe_set.update(colabs_receb2)
            
            # Fallback heurístico: cargos com nome contendo 'Receb' ou 'Recebimento'
            if (
                not recebe_set
                and "CARGOS" in data
                and "nome_cargo" in data["CARGOS"].columns
            ):
                heur = data["CARGOS"][
                    data["CARGOS"]["nome_cargo"]
                    .astype(str)
                    .str.contains("receb", case=False, na=False)
                ]["nome_cargo"].tolist()
                
                if logger:
                    logger.info(
                        f"CARGOS detectados por heurística (nome contém 'receb'): {heur}"
                    )
                
                if heur and "COLABORADORES" in data:
                    colabs_heur = (
                        data["COLABORADORES"][
                            data["COLABORADORES"]["cargo"].isin(heur)
                        ]["nome_colaborador"]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .tolist()
                    )
                    if logger:
                        logger.info(
                            f"Colaboradores detectados por heurística: {colabs_heur}"
                        )
                    recebe_set.update(colabs_heur)
            
            if logger:
                logger.info(
                    f"Set final de colaboradores que recebem por recebimento: {recebe_set}"
                )
        except Exception as e:
            if self.validation_logger:
                self.validation_logger.aviso(
                    f"Erro ao detectar colaboradores que recebem por recebimento: {e}",
                    {}
                )
        
        return recebe_set

