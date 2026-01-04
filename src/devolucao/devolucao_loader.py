"""
Loader para arquivo de Devoluções.

Responsável por carregar, validar e filtrar o arquivo Devoluções.xlsx
pelo mês/ano de apuração selecionado.
"""

import pandas as pd
import os
import logging
from typing import Optional, Tuple, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DevolucaoLoader:
    """
    Carrega e valida o arquivo de Devoluções.
    
    Regras de negócio:
    - Ignora registros onde 'Num docorigem' está vazio
    - Filtra apenas devoluções do mês/ano de apuração
    - Ignora registros com valor zero
    """
    
    # Nomes de arquivo aceitos
    NOMES_ARQUIVO = [
        "Devoluções.xlsx",
        "Devolucoes.xlsx",
        "Devoluções.xls",
        "Devolucoes.xls",
    ]
    
    # Colunas esperadas no arquivo
    COLUNAS_ESPERADAS = {
        "num_docorigem": ["Num docorigem", "num docorigem", "NUM DOCORIGEM", "Numero Doc Origem"],
        "data_entrada": ["Data de Entrada", "data de entrada", "DATA DE ENTRADA", "Data Entrada"],
        "valor_produtos": ["Valor Produtos", "valor produtos", "VALOR PRODUTOS", "Valor"],
        "codigo_operacao": ["Código Operação", "codigo operacao", "CODIGO OPERACAO", "Cod Operacao"],
    }
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa o loader.
        
        Args:
            base_path: Caminho base do projeto (onde fica 'dados_entrada/')
        """
        self.base_path = base_path
        self.dados_entrada_path = os.path.join(base_path, "dados_entrada")
        self._df_raw: Optional[pd.DataFrame] = None
        self._arquivo_usado: Optional[str] = None
        
    def _encontrar_arquivo(self) -> Optional[str]:
        """
        Procura o arquivo de devoluções nos locais esperados.
        
        Returns:
            Caminho completo do arquivo ou None se não encontrado.
        """
        # Primeiro tentar em dados_entrada/
        for nome in self.NOMES_ARQUIVO:
            caminho = os.path.join(self.dados_entrada_path, nome)
            if os.path.exists(caminho):
                return caminho
        
        # Depois tentar na raiz do projeto
        for nome in self.NOMES_ARQUIVO:
            caminho = os.path.join(self.base_path, nome)
            if os.path.exists(caminho):
                return caminho
        
        return None
    
    def _encontrar_coluna(self, df: pd.DataFrame, nomes_possiveis: List[str]) -> Optional[str]:
        """
        Encontra uma coluna no DataFrame usando lista de nomes possíveis.
        
        Args:
            df: DataFrame para buscar
            nomes_possiveis: Lista de nomes possíveis para a coluna
            
        Returns:
            Nome da coluna encontrada ou None
        """
        for nome in nomes_possiveis:
            if nome in df.columns:
                return nome
        return None
    
    def _validar_colunas(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, str], List[str]]:
        """
        Valida se as colunas necessárias existem no DataFrame.
        
        Returns:
            Tuple (válido, mapeamento_colunas, erros)
        """
        mapeamento = {}
        erros = []
        
        for campo_interno, nomes_possiveis in self.COLUNAS_ESPERADAS.items():
            col_encontrada = self._encontrar_coluna(df, nomes_possiveis)
            if col_encontrada:
                mapeamento[campo_interno] = col_encontrada
            else:
                # Apenas num_docorigem, data_entrada e valor_produtos são obrigatórios
                if campo_interno != "codigo_operacao":
                    erros.append(f"Coluna '{campo_interno}' não encontrada. Esperado: {nomes_possiveis}")
        
        return len(erros) == 0, mapeamento, erros
    
    def carregar(
        self,
        mes: int,
        ano: int,
        caminho_arquivo: Optional[str] = None
    ) -> Tuple[bool, pd.DataFrame, str]:
        """
        Carrega e filtra as devoluções pelo mês/ano de apuração.
        
        Args:
            mes: Mês de apuração (1-12)
            ano: Ano de apuração (ex: 2025)
            caminho_arquivo: Caminho específico do arquivo (opcional)
            
        Returns:
            Tuple (sucesso, DataFrame filtrado, mensagem)
        """
        # Encontrar arquivo
        if caminho_arquivo:
            if not os.path.exists(caminho_arquivo):
                return False, pd.DataFrame(), f"Arquivo não encontrado: {caminho_arquivo}"
            arquivo = caminho_arquivo
        else:
            arquivo = self._encontrar_arquivo()
            if not arquivo:
                msg = f"Arquivo de devoluções não encontrado. Procurado em: {self.dados_entrada_path}"
                logger.warning(f"[DEVOLUCAO] {msg}")
                return False, pd.DataFrame(), msg
        
        self._arquivo_usado = arquivo
        logger.info(f"[DEVOLUCAO] Carregando arquivo: {arquivo}")
        
        try:
            # Carregar arquivo
            if arquivo.endswith(".csv"):
                df = pd.read_csv(arquivo, sep=";", encoding="utf-8")
            else:
                df = pd.read_excel(arquivo)
            
            self._df_raw = df.copy()
            logger.info(f"[DEVOLUCAO] Arquivo carregado: {len(df)} linhas")
            
        except Exception as e:
            msg = f"Erro ao carregar arquivo de devoluções: {str(e)}"
            logger.error(f"[DEVOLUCAO] {msg}")
            return False, pd.DataFrame(), msg
        
        # Validar colunas
        valido, mapeamento, erros = self._validar_colunas(df)
        if not valido:
            msg = f"Colunas inválidas no arquivo: {'; '.join(erros)}"
            logger.error(f"[DEVOLUCAO] {msg}")
            return False, pd.DataFrame(), msg
        
        # Extrair colunas mapeadas
        col_num_doc = mapeamento["num_docorigem"]
        col_data = mapeamento["data_entrada"]
        col_valor = mapeamento["valor_produtos"]
        
        # Criar DataFrame normalizado
        df_norm = pd.DataFrame()
        df_norm["numero_nf_original"] = df[col_num_doc]
        df_norm["data_entrada"] = pd.to_datetime(df[col_data], format="%d/%m/%Y", errors="coerce")
        df_norm["valor_devolvido"] = pd.to_numeric(df[col_valor], errors="coerce").fillna(0)
        
        # Registrar estatísticas antes do filtro
        total_antes = len(df_norm)
        
        # Filtro 1: Remover registros sem Num docorigem
        df_norm = df_norm[df_norm["numero_nf_original"].notna()]
        df_norm = df_norm[df_norm["numero_nf_original"].astype(str).str.strip() != ""]
        sem_docorigem = total_antes - len(df_norm)
        
        # Filtro 2: Remover registros com valor zero ou negativo
        df_norm = df_norm[df_norm["valor_devolvido"] > 0]
        
        # Filtro 3: Filtrar pelo mês/ano de apuração
        # Garantir que a coluna é do tipo datetime antes de acessar .dt
        df_norm["data_entrada"] = pd.to_datetime(df_norm["data_entrada"], errors="coerce")
        df_norm = df_norm[
            (df_norm["data_entrada"].dt.month == mes) &  # type: ignore[union-attr]
            (df_norm["data_entrada"].dt.year == ano)  # type: ignore[union-attr]
        ]
        
        # Normalizar numero_nf_original para string
        df_norm["numero_nf_original"] = df_norm["numero_nf_original"].astype(str).str.strip()
        
        # Remover duplicados potenciais (mesmo NF no mesmo período) - agrupa e soma valores
        df_agrupado = df_norm.groupby("numero_nf_original").agg({
            "data_entrada": "first",  # Manter primeira data
            "valor_devolvido": "sum",  # Somar valores de múltiplas devoluções da mesma NF
        }).reset_index()
        
        msg = (
            f"Devoluções carregadas: {total_antes} linhas originais, "
            f"{sem_docorigem} sem doc origem ignoradas, "
            f"{len(df_agrupado)} devoluções válidas para {mes:02d}/{ano}"
        )
        logger.info(f"[DEVOLUCAO] {msg}")
        
        return True, df_agrupado, msg
    
    def get_estatisticas(self) -> Dict:
        """
        Retorna estatísticas do último carregamento.
        
        Returns:
            Dicionário com estatísticas
        """
        if self._df_raw is None:
            return {"carregado": False}
        
        return {
            "carregado": True,
            "arquivo": self._arquivo_usado,
            "total_linhas_brutas": len(self._df_raw),
        }
