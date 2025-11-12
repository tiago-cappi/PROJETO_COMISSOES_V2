"""
Loader para carregar e filtrar dados da Análise Financeira.
"""

import pandas as pd
import os
from typing import Optional
from datetime import datetime


class AnaliseFinanceiraLoader:
    """
    Carrega e filtra dados do arquivo Análise Financeira.xlsx.
    
    Filtros aplicados:
    - Tipo de Baixa == 'B'
    - Data de Baixa no mês/ano especificado
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
        """
        Carrega o arquivo Análise Financeira.xlsx e aplica filtros.
        
        Args:
            mes: Mês de apuração (1-12)
            ano: Ano de apuração (ex: 2025)
            base_path: Caminho base para busca do arquivo
            filepath: Caminho específico do arquivo (opcional)
        
        Returns:
            DataFrame com colunas: Documento, Valor Líquido, Data de Baixa
        """
        print(f"[RECEBIMENTO] [LOADER] Iniciando carregamento da Análise Financeira...")
        print(f"[RECEBIMENTO] [LOADER] Parâmetros: mes={mes}, ano={ano}, base_path={base_path}")
        
        # Determinar caminho do arquivo
        if filepath:
            path = filepath
            print(f"[RECEBIMENTO] [LOADER] Usando caminho específico: {path}")
        else:
            # Procurar primeiro em dados_entrada/, depois na raiz
            path_entrada = os.path.join("dados_entrada", "Análise Financeira.xlsx")
            path_raiz = os.path.join(base_path, "Análise Financeira.xlsx")
            
            print(f"[RECEBIMENTO] [LOADER] Procurando arquivo em: {path_entrada}")
            print(f"[RECEBIMENTO] [LOADER] Existe? {os.path.exists(path_entrada)}")
            print(f"[RECEBIMENTO] [LOADER] Procurando arquivo em: {path_raiz}")
            print(f"[RECEBIMENTO] [LOADER] Existe? {os.path.exists(path_raiz)}")
            
            if os.path.exists(path_entrada):
                path = path_entrada
                print(f"[RECEBIMENTO] [LOADER] Arquivo encontrado em dados_entrada/")
            elif os.path.exists(path_raiz):
                path = path_raiz
                print(f"[RECEBIMENTO] [LOADER] Arquivo encontrado na raiz")
            else:
                print(f"[RECEBIMENTO] [LOADER] ERRO: Arquivo não encontrado em nenhum local!")
                # Retornar DataFrame vazio se arquivo não encontrado
                return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        # Carregar arquivo Excel
        print(f"[RECEBIMENTO] [LOADER] Carregando arquivo Excel: {path}")
        try:
            # Primeiro, ler apenas o cabeçalho para identificar a coluna Documento
            df_temp = pd.read_excel(path, nrows=0)
            col_doc_temp = self._encontrar_coluna(df_temp, ["Documento", "documento", "DOCUMENTO"])
            
            # Usar converters para forçar leitura como string e preservar zeros à esquerda
            converters = {}
            if col_doc_temp:
                converters[col_doc_temp] = str
            
            df = pd.read_excel(path, converters=converters)
            print(f"[RECEBIMENTO] [LOADER] Arquivo carregado: {len(df)} linha(s), {len(df.columns)} coluna(s)")
            print(f"[RECEBIMENTO] [LOADER] Colunas encontradas: {list(df.columns)[:10]}...")  # Primeiras 10 colunas
        except Exception as e:
            print(f"[RECEBIMENTO] [LOADER] ERRO ao carregar arquivo: {e}")
            # Se houver erro, retornar DataFrame vazio
            return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        if df.empty:
            return df
        
        # Normalizar nomes de colunas (case-insensitive, remover espaços)
        df.columns = df.columns.str.strip()
        
        # Procurar colunas relevantes (tolerante a variações)
        col_documento = self._encontrar_coluna(df, ["Documento", "documento", "DOCUMENTO"])
        col_valor = self._encontrar_coluna(df, ["Valor Líquido", "Valor Liquido", "valor líquido", "VALOR LIQUIDO"])
        col_data = self._encontrar_coluna(df, ["Data de Baixa", "Data Baixa", "data de baixa", "DATA BAIXA"])
        col_tipo = self._encontrar_coluna(df, ["Tipo de Baixa", "Tipo Baixa", "tipo de baixa", "TIPO BAIXA"])
        
        # Verificar se todas as colunas foram encontradas
        if not all([col_documento, col_valor, col_data, col_tipo]):
            # Retornar DataFrame vazio se colunas essenciais não foram encontradas
            return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        # Selecionar apenas colunas relevantes
        df_filtrado = df[[col_documento, col_valor, col_data, col_tipo]].copy()
        
        # Renomear colunas para nomes padrão
        df_filtrado.columns = ["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"]
        
        # Filtrar por Tipo de Baixa == 'B'
        print(f"[RECEBIMENTO] [LOADER] Filtrando por Tipo de Baixa == 'B'...")
        antes_filtro_tipo = len(df_filtrado)
        df_filtrado = df_filtrado[df_filtrado["Tipo de Baixa"].astype(str).str.strip().str.upper() == "B"]
        depois_filtro_tipo = len(df_filtrado)
        print(f"[RECEBIMENTO] [LOADER] Após filtro Tipo de Baixa: {antes_filtro_tipo} -> {depois_filtro_tipo} linha(s)")
        
        if df_filtrado.empty:
            print(f"[RECEBIMENTO] [LOADER] AVISO: Nenhuma linha com Tipo de Baixa == 'B'")
            return pd.DataFrame(columns=["Documento", "Valor Líquido", "Data de Baixa", "Tipo de Baixa"])
        
        # Converter Data de Baixa para datetime
        print(f"[RECEBIMENTO] [LOADER] Convertendo Data de Baixa para datetime...")
        try:
            df_filtrado["Data de Baixa"] = pd.to_datetime(
                df_filtrado["Data de Baixa"],
                dayfirst=True,
                errors='coerce'
            )
            print(f"[RECEBIMENTO] [LOADER] Conversão bem-sucedida")
        except Exception as e:
            print(f"[RECEBIMENTO] [LOADER] Erro na conversão (tentativa 1): {e}")
            # Se houver erro na conversão, tentar formato alternativo
            try:
                df_filtrado["Data de Baixa"] = pd.to_datetime(
                    df_filtrado["Data de Baixa"],
                    format='%d/%m/%Y',
                    errors='coerce'
                )
                print(f"[RECEBIMENTO] [LOADER] Conversão bem-sucedida (tentativa 2)")
            except Exception as e2:
                print(f"[RECEBIMENTO] [LOADER] Erro na conversão (tentativa 2): {e2}")
        
        # Filtrar por mês e ano
        print(f"[RECEBIMENTO] [LOADER] Filtrando por mês={mes} e ano={ano}...")
        antes_filtro_data = len(df_filtrado)
        mask_mes = df_filtrado["Data de Baixa"].dt.month == mes
        mask_ano = df_filtrado["Data de Baixa"].dt.year == ano
        df_filtrado = df_filtrado[mask_mes & mask_ano]
        depois_filtro_data = len(df_filtrado)
        print(f"[RECEBIMENTO] [LOADER] Após filtro de data: {antes_filtro_data} -> {depois_filtro_data} linha(s)")
        
        # Normalizar coluna Documento (trim, uppercase, preservar valor exato)
        # A coluna já foi lida como string via converters
        # Apenas fazer trim e uppercase, mantendo zeros à esquerda
        df_filtrado["Documento"] = df_filtrado["Documento"].astype(str).str.strip().str.upper()
        
        # Log para debug: mostrar o documento carregado
        if len(df_filtrado) > 0:
            print(f"[RECEBIMENTO] [LOADER] Documento(s) carregado(s): {df_filtrado['Documento'].tolist()}")
        
        # Remover linhas com Documento vazio ou inválido
        df_filtrado = df_filtrado[df_filtrado["Documento"].notna()]
        df_filtrado = df_filtrado[df_filtrado["Documento"] != ""]
        df_filtrado = df_filtrado[df_filtrado["Documento"] != "NAN"]
        
        # Converter Valor Líquido para numérico
        df_filtrado["Valor Líquido"] = pd.to_numeric(
            df_filtrado["Valor Líquido"],
            errors='coerce'
        )
        
        # Remover linhas com valor inválido
        df_filtrado = df_filtrado[df_filtrado["Valor Líquido"].notna()]
        df_filtrado = df_filtrado[df_filtrado["Valor Líquido"] > 0]
        
        # Resetar índice
        df_filtrado = df_filtrado.reset_index(drop=True)
        
        print(f"[RECEBIMENTO] [LOADER] Carregamento concluído: {len(df_filtrado)} linha(s) finais")
        print(f"[RECEBIMENTO] [LOADER] Colunas finais: {list(df_filtrado.columns)}")
        
        return df_filtrado
    
    def _encontrar_coluna(self, df: pd.DataFrame, nomes_possiveis: list) -> Optional[str]:
        """
        Encontra uma coluna no DataFrame por nomes possíveis.
        
        Args:
            df: DataFrame
            nomes_possiveis: Lista de nomes possíveis para a coluna
        
        Returns:
            Nome da coluna encontrada ou None
        """
        for nome in nomes_possiveis:
            if nome in df.columns:
                return nome
        return None

