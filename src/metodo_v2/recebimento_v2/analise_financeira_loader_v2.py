"""
src.metodo_v2.recebimento_v2.analise_financeira_loader_v2 - Loader de Análise Financeira

Carrega e filtra dados do arquivo Análise Financeira.xlsx para a Metodologia V2.

Filtros aplicados:
- Tipo de Baixa == 'B' (pagamento efetivo)
- Data de Baixa no mês/ano de apuração
"""

from __future__ import annotations

import logging
import os
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd


logger = logging.getLogger(__name__)


class AnaliseFinanceiraLoaderV2:
    """Carrega e filtra dados da Análise Financeira para V2.
    
    Independente do loader do método padrão (src/recebimento/io/).
    """
    
    def __init__(self):
        """Inicializa o loader."""
        pass
    
    def carregar(
        self,
        mes: int,
        ano: int,
        base_path: str = ".",
        filepath: Optional[str] = None
    ) -> pd.DataFrame:
        """Carrega o arquivo Análise Financeira.xlsx e aplica filtros.
        
        Args:
            mes: Mês de apuração (1-12).
            ano: Ano de apuração (ex: 2026).
            base_path: Caminho base para busca do arquivo.
            filepath: Caminho específico do arquivo (opcional).
        
        Returns:
            DataFrame com colunas: Documento, Valor Líquido, Data de Baixa
            
        Raises:
            FileNotFoundError: Se o arquivo não for encontrado.
        """
        logger.info(f"[V2-REC] Carregando Análise Financeira (mes={mes}, ano={ano})...")
        
        # Determinar caminho do arquivo
        path = self._encontrar_arquivo(base_path, filepath)
        
        if path is None:
            logger.error("[V2-REC] Arquivo Análise Financeira não encontrado!")
            return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        logger.info(f"[V2-REC] Arquivo encontrado: {path}")
        
        # Carregar Excel com Documento como string (preservar zeros à esquerda)
        try:
            df_temp = pd.read_excel(path, nrows=0)
            col_doc = self._encontrar_coluna(df_temp, ["Documento", "documento", "DOCUMENTO"])
            
            converters = {}
            if col_doc:
                converters[col_doc] = str
            
            df = pd.read_excel(path, converters=converters)
            logger.info(f"[V2-REC] Arquivo carregado: {len(df)} linhas, {len(df.columns)} colunas")
        except Exception as e:
            logger.error(f"[V2-REC] Erro ao carregar arquivo: {e}")
            return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        if df.empty:
            return df
        
        # Normalizar nomes de colunas
        df.columns = df.columns.str.strip()
        
        # Encontrar colunas relevantes
        col_documento = self._encontrar_coluna(df, ["Documento", "documento", "DOCUMENTO"])
        col_valor = self._encontrar_coluna(df, ["Valor Líquido", "Valor Liquido", "valor líquido", "VALOR LIQUIDO"])
        col_data = self._encontrar_coluna(df, ["Data de Baixa", "Data Baixa", "data de baixa", "DATA BAIXA"])
        col_tipo = self._encontrar_coluna(df, ["Tipo de Baixa", "Tipo Baixa", "tipo de baixa", "TIPO BAIXA"])
        
        if not all([col_documento, col_valor, col_data, col_tipo]):
            logger.error(f"[V2-REC] Colunas essenciais não encontradas!")
            logger.error(f"[V2-REC] Encontradas: doc={col_documento}, valor={col_valor}, data={col_data}, tipo={col_tipo}")
            return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        # Selecionar apenas colunas relevantes
        df_filtrado = df[[col_documento, col_valor, col_data, col_tipo]].copy()
        df_filtrado.columns = ["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"]
        
        # Filtrar por Tipo de Baixa == 'B'
        antes = len(df_filtrado)
        df_filtrado = df_filtrado[
            df_filtrado["Tipo de Baixa"].astype(str).str.strip().str.upper() == "B"
        ]
        logger.info(f"[V2-REC] Após filtro Tipo Baixa='B': {antes} → {len(df_filtrado)}")
        
        if df_filtrado.empty:
            logger.warning("[V2-REC] Nenhum registro com Tipo de Baixa = 'B'")
            return df_filtrado
        
        # Converter Data de Baixa para datetime
        df_filtrado["Data de Baixa"] = pd.to_datetime(
            df_filtrado["Data de Baixa"],
            errors='coerce'
        )
        
        # Filtrar por mês e ano
        antes = len(df_filtrado)
        mask = (
            (df_filtrado["Data de Baixa"].dt.month == mes) &
            (df_filtrado["Data de Baixa"].dt.year == ano)
        )
        df_filtrado = df_filtrado[mask]
        logger.info(f"[V2-REC] Após filtro mês={mes:02d}/ano={ano}: {antes} → {len(df_filtrado)}")
        
        # Normalizar Documento
        df_filtrado["Documento"] = (
            df_filtrado["Documento"]
            .astype(str)
            .str.strip()
            .str.upper()
        )
        
        # Remover documentos inválidos
        df_filtrado = df_filtrado[
            df_filtrado["Documento"].notna() &
            (df_filtrado["Documento"] != "") &
            (df_filtrado["Documento"] != "NAN")
        ]
        
        # Converter Valor Líquido para numérico
        df_filtrado["Valor Líquido"] = pd.to_numeric(
            df_filtrado["Valor Líquido"],
            errors='coerce'
        )
        
        # Remover valores inválidos
        df_filtrado = df_filtrado[
            df_filtrado["Valor Líquido"].notna() &
            (df_filtrado["Valor Líquido"] > 0)
        ]
        
        df_filtrado = df_filtrado.reset_index(drop=True)
        
        logger.info(f"[V2-REC] Total final: {len(df_filtrado)} pagamentos para processar")
        
        return df_filtrado
    
    def _encontrar_arquivo(
        self, 
        base_path: str, 
        filepath: Optional[str]
    ) -> Optional[str]:
        """Encontra o arquivo Análise Financeira.
        
        Args:
            base_path: Caminho base.
            filepath: Caminho específico (opcional).
            
        Returns:
            Caminho do arquivo ou None.
        """
        if filepath and os.path.exists(filepath):
            return filepath
        
        def normalizar_nome(nome: str) -> str:
            """Remove acentos e converte para minúsculas."""
            nfkd = unicodedata.normalize('NFKD', nome)
            sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
            return sem_acento.lower()
        
        # Buscar em dados_entrada/
        path_entrada = Path(base_path) / "dados_entrada"
        if path_entrada.exists():
            for arquivo in path_entrada.glob("*.xlsx"):
                nome_norm = normalizar_nome(arquivo.name)
                if "analise" in nome_norm and "financeira" in nome_norm:
                    return str(arquivo)
        
        # Buscar na raiz
        path_raiz = Path(base_path)
        for arquivo in path_raiz.glob("*.xlsx"):
            nome_norm = normalizar_nome(arquivo.name)
            if "analise" in nome_norm and "financeira" in nome_norm:
                return str(arquivo)
        
        return None
    
    def _encontrar_coluna(
        self, 
        df: pd.DataFrame, 
        nomes_possiveis: list
    ) -> Optional[str]:
        """Encontra uma coluna no DataFrame.
        
        Args:
            df: DataFrame.
            nomes_possiveis: Lista de nomes possíveis.
            
        Returns:
            Nome da coluna encontrada ou None.
        """
        if df.empty:
            return None
        
        colunas_norm = {col.lower().strip(): col for col in df.columns}
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_norm:
                return colunas_norm[nome_norm]
        
        return None
