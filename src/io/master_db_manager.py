"""
Gerenciador do Banco de Dados Master de Comissões.
Implementa append-only audit log com mecanismos de segurança.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging
import getpass

from src.utils.file_security import FileSecurityManager

logger = logging.getLogger(__name__)


# Schema padrão do banco de dados de comissões
MASTER_DB_COLUMNS = [
    # Metadados da execução
    "Data_Execucao",
    "Usuario_Execucao",
    "Mes_Referencia",
    "Ano_Referencia",
    "Tipo_Comissao",  # FATURAMENTO, ADIANTAMENTO, REGULAR, RECONCILIACAO
    
    # Identificação do processo e colaborador
    "Processo",
    "Nome_Colaborador",
    "Cargo",
    "Linha",
    
    # Valores da comissão
    "Valor_Base",  # Valor base usado para cálculo (faturamento ou pagamento)
    "TCMP",  # Taxa de comissão
    "FC",  # Fator de correção (se aplicável)
    "Comissao_Calculada",
    
    # Detalhes adicionais
    "Cod_Produto",
    "Descricao_Produto",
    "Grupo",
    "Subgrupo",
    "Tipo_Mercadoria",
    
    # Campos específicos de recebimento
    "Documento",
    "Data_Pagamento",
    "Tipo_Pagamento",  # ANTECIPACAO, REGULAR
    
    # Observações
    "Observacao",
]


class MasterDBManager:
    """
    Gerencia o banco de dados Excel de histórico de comissões.
    Implementa o protocolo de escrita segura com backup e integridade.
    """

    DEFAULT_FILENAME = "HISTORICO_COMISSOES_MASTER.xlsx"
    DEFAULT_SHEET = "HISTORICO"

    def __init__(self, base_path: str = "."):
        """
        Inicializa o gerenciador do banco de dados.

        Args:
            base_path: Caminho base do projeto.
        """
        self.base_path = base_path
        self.db_dir = os.path.join(base_path, "data", "banco_dados")
        self.backup_dir = os.path.join(self.db_dir, "backups")
        self.db_filepath = os.path.join(self.db_dir, self.DEFAULT_FILENAME)
        
        # Inicializar gerenciador de segurança
        self.security = FileSecurityManager(backup_dir=self.backup_dir)
        
        # Garantir que diretórios existam
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def _get_current_user(self) -> str:
        """Retorna o usuário atual do sistema."""
        try:
            return getpass.getuser()
        except Exception:
            return "UNKNOWN"

    def _create_empty_master(self) -> pd.DataFrame:
        """Cria um DataFrame vazio com o schema padrão."""
        return pd.DataFrame(columns=MASTER_DB_COLUMNS)

    def _load_master(self) -> Tuple[bool, pd.DataFrame, str]:
        """
        Carrega o banco de dados master.

        Returns:
            Tuple (sucesso, DataFrame, mensagem)
        """
        if not os.path.exists(self.db_filepath):
            logger.info("[MASTER_DB] Arquivo não existe, será criado na primeira escrita.")
            return True, self._create_empty_master(), "Novo banco de dados."

        try:
            # Verificar integridade antes de carregar
            valid, msg = self.security.verify_hash(self.db_filepath)
            if not valid:
                logger.warning(f"[MASTER_DB] Alerta de integridade: {msg}")
                # Continua mesmo assim, mas loga o alerta

            df = pd.read_excel(self.db_filepath, sheet_name=self.DEFAULT_SHEET)
            
            # Garantir que todas as colunas esperadas existam
            for col in MASTER_DB_COLUMNS:
                if col not in df.columns:
                    df[col] = None

            logger.info(f"[MASTER_DB] Banco carregado: {len(df)} registros existentes.")
            return True, df, "Banco carregado com sucesso."

        except Exception as e:
            error_msg = f"Falha ao carregar banco de dados: {str(e)}"
            logger.error(f"[MASTER_DB] {error_msg}")
            return False, self._create_empty_master(), error_msg

    def _save_master(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Salva o banco de dados master com todas as proteções.

        Args:
            df: DataFrame a salvar.

        Returns:
            Tuple (sucesso, mensagem)
        """
        try:
            # Reordenar colunas conforme schema
            cols_to_use = [c for c in MASTER_DB_COLUMNS if c in df.columns]
            extra_cols = [c for c in df.columns if c not in MASTER_DB_COLUMNS]
            df = df[cols_to_use + extra_cols]

            # Salvar
            df.to_excel(self.db_filepath, sheet_name=self.DEFAULT_SHEET, index=False)

            # Calcular e salvar hash
            success, hash_value = self.security.calculate_hash(self.db_filepath)
            if success:
                self.security.save_hash(self.db_filepath, hash_value)

            # Definir como somente leitura
            self.security.set_read_only(self.db_filepath, read_only=True)

            logger.info(f"[MASTER_DB] Banco salvo: {len(df)} registros totais.")
            return True, "Banco de dados salvo com sucesso."

        except Exception as e:
            error_msg = f"Falha ao salvar banco de dados: {str(e)}"
            logger.error(f"[MASTER_DB] {error_msg}")
            return False, error_msg

    def append_comissoes(
        self,
        df_comissoes: pd.DataFrame,
        mes: int,
        ano: int,
        tipo_comissao: str,
        column_mapping: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str]:
        """
        Adiciona comissões ao banco de dados master.

        Args:
            df_comissoes: DataFrame com as comissões a adicionar.
            mes: Mês de referência.
            ano: Ano de referência.
            tipo_comissao: Tipo de comissão (FATURAMENTO, ADIANTAMENTO, REGULAR, RECONCILIACAO).
            column_mapping: Mapeamento opcional de colunas do df_comissoes para o schema.

        Returns:
            Tuple (sucesso, mensagem)
        """
        if df_comissoes.empty:
            logger.info("[MASTER_DB] DataFrame vazio, nada a adicionar.")
            return True, "Nenhuma comissão para adicionar."

        print(f"[MASTER_DB] Iniciando append de {len(df_comissoes)} comissões ({tipo_comissao})...")

        # === FASE 1: Verificação de Lock ===
        if self.security.is_file_locked(self.db_filepath):
            error_msg = (
                f"ERRO: O arquivo {self.db_filepath} está aberto por outro programa. "
                "Feche o arquivo e tente novamente."
            )
            logger.error(f"[MASTER_DB] {error_msg}")
            return False, error_msg

        # === FASE 2: Backup ===
        if os.path.exists(self.db_filepath):
            success, backup_msg = self.security.create_backup(self.db_filepath)
            if not success:
                logger.warning(f"[MASTER_DB] Falha no backup: {backup_msg}")
                # Continua mesmo assim (backup é best-effort)

        # === FASE 3: Unlock (remover read-only) ===
        if os.path.exists(self.db_filepath):
            self.security.set_read_only(self.db_filepath, read_only=False)

        # === FASE 4: Carregar e Append ===
        try:
            success, df_master, msg = self._load_master()
            if not success:
                logger.warning(f"[MASTER_DB] {msg}")
                df_master = self._create_empty_master()

            # Preparar novos registros
            df_new = self._prepare_records(
                df_comissoes=df_comissoes,
                mes=mes,
                ano=ano,
                tipo_comissao=tipo_comissao,
                column_mapping=column_mapping,
            )

            # Concatenar
            df_combined = pd.concat([df_master, df_new], ignore_index=True)

            # === FASE 5: Salvar com integridade ===
            success, save_msg = self._save_master(df_combined)

            if success:
                # Limpar backups antigos (manter últimos 30)
                self.security.cleanup_old_backups(self.backup_dir, keep_count=30)
                
                result_msg = (
                    f"Comissões adicionadas com sucesso. "
                    f"Novos: {len(df_new)}, Total: {len(df_combined)}."
                )
                print(f"[MASTER_DB] {result_msg}")
                return True, result_msg
            else:
                return False, save_msg

        except Exception as e:
            error_msg = f"Erro durante append: {str(e)}"
            logger.error(f"[MASTER_DB] {error_msg}")
            
            # Tentar restaurar backup se falhou
            try:
                # Encontrar backup mais recente
                backups = sorted(
                    [f for f in os.listdir(self.backup_dir) if ".bak." in f],
                    reverse=True
                )
                if backups:
                    latest_backup = os.path.join(self.backup_dir, backups[0])
                    self.security.restore_backup(latest_backup, self.db_filepath)
                    logger.info("[MASTER_DB] Backup restaurado após falha.")
            except Exception:
                pass
            
            return False, error_msg

    def _prepare_records(
        self,
        df_comissoes: pd.DataFrame,
        mes: int,
        ano: int,
        tipo_comissao: str,
        column_mapping: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Prepara os registros para inserção no banco de dados.

        Args:
            df_comissoes: DataFrame original.
            mes: Mês de referência.
            ano: Ano de referência.
            tipo_comissao: Tipo de comissão.
            column_mapping: Mapeamento de colunas.

        Returns:
            DataFrame preparado com schema padronizado.
        """
        # Mapeamento padrão de colunas (origem -> destino)
        default_mapping = {
            # Colunas de faturamento
            "processo": "Processo",
            "PROCESSO": "Processo",
            "Processo": "Processo",
            "nome_colaborador": "Nome_Colaborador",
            "NOME_COLABORADOR": "Nome_Colaborador",
            "Nome Colaborador": "Nome_Colaborador",
            "cargo": "Cargo",
            "CARGO": "Cargo",
            "Cargo": "Cargo",
            "linha": "Linha",
            "LINHA": "Linha",
            "Linha": "Linha",
            "faturamento_item": "Valor_Base",
            "FATURAMENTO_ITEM": "Valor_Base",
            "valor_pago": "Valor_Base",
            "VALOR_PAGO": "Valor_Base",
            "tcmp": "TCMP",
            "TCMP": "TCMP",
            "taxa_rateio_aplicada": "TCMP",
            "fc": "FC",
            "FC": "FC",
            "fator_correcao_fc": "FC",
            "FATOR_CORRECAO_FC": "FC",
            "comissao_calculada": "Comissao_Calculada",
            "COMISSAO_CALCULADA": "Comissao_Calculada",
            "cod_produto": "Cod_Produto",
            "COD_PRODUTO": "Cod_Produto",
            "descricao_produto": "Descricao_Produto",
            "DESCRICAO_PRODUTO": "Descricao_Produto",
            "grupo": "Grupo",
            "GRUPO": "Grupo",
            "subgrupo": "Subgrupo",
            "SUBGRUPO": "Subgrupo",
            "tipo_mercadoria": "Tipo_Mercadoria",
            "TIPO_MERCADORIA": "Tipo_Mercadoria",
            # Colunas de recebimento
            "documento": "Documento",
            "DOCUMENTO": "Documento",
            "data_pagamento": "Data_Pagamento",
            "DATA_PAGAMENTO": "Data_Pagamento",
            "tipo_pagamento": "Tipo_Pagamento",
            "TIPO_PAGAMENTO": "Tipo_Pagamento",
            "observacao": "Observacao",
            "OBSERVACAO": "Observacao",
        }

        # Combinar com mapeamento customizado
        if column_mapping:
            default_mapping.update(column_mapping)

        # Criar DataFrame de saída
        df_out = pd.DataFrame()

        # Mapear colunas
        for orig_col in df_comissoes.columns:
            if orig_col in default_mapping:
                dest_col = default_mapping[orig_col]
                df_out[dest_col] = df_comissoes[orig_col]
            else:
                # Manter colunas extras com nome original
                df_out[orig_col] = df_comissoes[orig_col]

        # Adicionar metadados
        now = datetime.now()
        df_out["Data_Execucao"] = now.strftime("%Y-%m-%d %H:%M:%S")
        df_out["Usuario_Execucao"] = self._get_current_user()
        df_out["Mes_Referencia"] = mes
        df_out["Ano_Referencia"] = ano
        df_out["Tipo_Comissao"] = tipo_comissao

        # Garantir todas as colunas do schema
        for col in MASTER_DB_COLUMNS:
            if col not in df_out.columns:
                df_out[col] = None

        return df_out

    def get_historico(
        self,
        mes: Optional[int] = None,
        ano: Optional[int] = None,
        tipo_comissao: Optional[str] = None,
        processo: Optional[str] = None,
        colaborador: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Consulta o histórico de comissões com filtros opcionais.

        Args:
            mes: Filtrar por mês de referência.
            ano: Filtrar por ano de referência.
            tipo_comissao: Filtrar por tipo de comissão.
            processo: Filtrar por código do processo.
            colaborador: Filtrar por nome do colaborador (parcial).

        Returns:
            DataFrame com os registros filtrados.
        """
        success, df, msg = self._load_master()
        if not success or df.empty:
            return pd.DataFrame()

        # Aplicar filtros
        if mes is not None:
            df = df[df["Mes_Referencia"] == mes]
        if ano is not None:
            df = df[df["Ano_Referencia"] == ano]
        if tipo_comissao is not None:
            df = df[df["Tipo_Comissao"] == tipo_comissao]
        if processo is not None:
            df = df[df["Processo"].astype(str).str.contains(str(processo), case=False, na=False)]
        if colaborador is not None:
            df = df[df["Nome_Colaborador"].astype(str).str.contains(colaborador, case=False, na=False)]

        return df

    def get_resumo_por_colaborador(
        self,
        mes: int,
        ano: int,
        tipo_comissao: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retorna resumo agregado por colaborador para um mês/ano.

        Args:
            mes: Mês de referência.
            ano: Ano de referência.
            tipo_comissao: Filtrar por tipo (opcional).

        Returns:
            DataFrame com resumo por colaborador.
        """
        df = self.get_historico(mes=mes, ano=ano, tipo_comissao=tipo_comissao)
        
        if df.empty:
            return pd.DataFrame()

        resumo = df.groupby(["Nome_Colaborador", "Cargo", "Linha"]).agg({
            "Comissao_Calculada": "sum",
            "Processo": "nunique",
            "Data_Execucao": "max",
        }).reset_index()

        resumo.columns = [
            "Nome_Colaborador",
            "Cargo",
            "Linha",
            "Total_Comissao",
            "Qtd_Processos",
            "Ultima_Execucao",
        ]

        return resumo.sort_values("Total_Comissao", ascending=False)

    def get_resumo_por_processo(
        self,
        mes: int,
        ano: int,
    ) -> pd.DataFrame:
        """
        Retorna resumo agregado por processo para um mês/ano.

        Args:
            mes: Mês de referência.
            ano: Ano de referência.

        Returns:
            DataFrame com resumo por processo.
        """
        df = self.get_historico(mes=mes, ano=ano)
        
        if df.empty:
            return pd.DataFrame()

        resumo = df.groupby(["Processo"]).agg({
            "Comissao_Calculada": "sum",
            "Nome_Colaborador": "nunique",
            "Valor_Base": "sum",
            "Data_Execucao": "max",
        }).reset_index()

        resumo.columns = [
            "Processo",
            "Total_Comissao",
            "Qtd_Colaboradores",
            "Valor_Total_Base",
            "Ultima_Execucao",
        ]

        return resumo.sort_values("Total_Comissao", ascending=False)

    def get_estatisticas(self) -> Dict:
        """
        Retorna estatísticas gerais do banco de dados.

        Returns:
            Dict com estatísticas.
        """
        success, df, msg = self._load_master()
        if not success or df.empty:
            return {
                "total_registros": 0,
                "total_comissoes": 0.0,
                "periodos_distintos": 0,
                "colaboradores_distintos": 0,
                "processos_distintos": 0,
                "arquivo_existe": os.path.exists(self.db_filepath),
            }

        return {
            "total_registros": len(df),
            "total_comissoes": df["Comissao_Calculada"].sum() if "Comissao_Calculada" in df.columns else 0.0,
            "periodos_distintos": df.groupby(["Mes_Referencia", "Ano_Referencia"]).ngroups if all(c in df.columns for c in ["Mes_Referencia", "Ano_Referencia"]) else 0,
            "colaboradores_distintos": df["Nome_Colaborador"].nunique() if "Nome_Colaborador" in df.columns else 0,
            "processos_distintos": df["Processo"].nunique() if "Processo" in df.columns else 0,
            "arquivo_existe": True,
            "primeiro_registro": df["Data_Execucao"].min() if "Data_Execucao" in df.columns else None,
            "ultimo_registro": df["Data_Execucao"].max() if "Data_Execucao" in df.columns else None,
        }
