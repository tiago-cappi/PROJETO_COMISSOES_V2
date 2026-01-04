"""
Orquestrador de Processamento de Devoluções.

Coordena o fluxo completo de processamento de devoluções:
1. Carregar arquivo de devoluções
2. Vincular com Análise Comercial (via Numero NF)
3. Buscar comissões históricas no banco de dados
4. Calcular saldos negativos proporcionais
5. Salvar no banco de dados histórico
"""

import pandas as pd
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .devolucao_loader import DevolucaoLoader
from .devolucao_calculator import DevolucaoCalculator
from src.io.master_db_manager import MasterDBManager

logger = logging.getLogger(__name__)


class DevolucaoProcessor:
    """
    Orquestra o processamento completo de devoluções.
    
    Fluxo:
    1. Carregar devoluções do período
    2. Para cada devolução:
       a. Vincular Num docorigem -> Numero NF -> Processo
       b. Obter Valor Realizado total do processo
       c. Buscar comissões pagas no histórico
       d. Calcular saldos negativos proporcionais
    3. Consolidar e salvar no banco histórico
    """
    
    def __init__(
        self,
        base_path: str = ".",
        df_analise_comercial: Optional[pd.DataFrame] = None,
    ):
        """
        Inicializa o processador.
        
        Args:
            base_path: Caminho base do projeto
            df_analise_comercial: DataFrame da Análise Comercial Completa
                                  (se não fornecido, será carregado automaticamente)
        """
        self.base_path = base_path
        self.loader = DevolucaoLoader(base_path)
        self.calculator = DevolucaoCalculator()
        self.master_db = MasterDBManager(base_path)
        
        self._df_analise_comercial = df_analise_comercial
        self._resultados: Dict = {}
        self._saldos_negativos: List[Dict] = []
        
    def _carregar_analise_comercial(self) -> pd.DataFrame:
        """
        Carrega a Análise Comercial Completa se não foi fornecida.
        
        Returns:
            DataFrame da Análise Comercial
        """
        if self._df_analise_comercial is not None:
            return self._df_analise_comercial
        
        # Tentar carregar do arquivo
        caminhos = [
            os.path.join(self.base_path, "dados_entrada", "Analise_Comercial_Completa.xlsx"),
            os.path.join(self.base_path, "dados_entrada", "Analise_Comercial_Completa.csv"),
            os.path.join(self.base_path, "Analise_Comercial_Completa.xlsx"),
            os.path.join(self.base_path, "Analise_Comercial_Completa.csv"),
        ]
        
        for caminho in caminhos:
            if os.path.exists(caminho):
                logger.info(f"[DEVOLUCAO] Carregando Análise Comercial: {caminho}")
                if caminho.endswith(".csv"):
                    df = pd.read_csv(caminho, sep=",", encoding="utf-8")
                else:
                    df = pd.read_excel(caminho)
                self._df_analise_comercial = df
                return df
        
        logger.error("[DEVOLUCAO] Análise Comercial não encontrada")
        return pd.DataFrame()
    
    def _encontrar_coluna(
        self, 
        df: pd.DataFrame, 
        nomes_possiveis: List[str]
    ) -> Optional[str]:
        """Encontra uma coluna no DataFrame usando lista de nomes possíveis."""
        for nome in nomes_possiveis:
            if nome in df.columns:
                return nome
        return None
    
    def _vincular_nf_com_processo(
        self, 
        numero_nf: str, 
        df_comercial: pd.DataFrame
    ) -> Tuple[Optional[str], float]:
        """
        Vincula um Numero NF com o Processo e calcula o Valor Realizado total.
        
        Args:
            numero_nf: Número da NF a buscar
            df_comercial: DataFrame da Análise Comercial
            
        Returns:
            Tuple (processo, valor_realizado_total) ou (None, 0) se não encontrado
        """
        col_nf = self._encontrar_coluna(df_comercial, ["Numero NF", "numero nf", "NUMERO NF", "Num NF"])
        col_processo = self._encontrar_coluna(df_comercial, ["Processo", "processo", "PROCESSO"])
        col_valor = self._encontrar_coluna(df_comercial, ["Valor Realizado", "valor realizado", "VALOR REALIZADO"])
        
        if not col_nf or not col_processo or not col_valor:
            logger.error("[DEVOLUCAO] Colunas necessárias não encontradas na Análise Comercial")
            return None, 0
        
        # Normalizar NF para comparação
        nf_normalizado = str(numero_nf).strip()
        
        # Buscar linhas com esse Numero NF
        df_comercial_str = df_comercial[col_nf].astype(str).str.strip()
        mask = df_comercial_str == nf_normalizado
        
        # Tentar também sem zeros à esquerda
        if not mask.any():
            try:
                nf_int = str(int(float(nf_normalizado)))
                mask = df_comercial_str.str.lstrip("0") == nf_int.lstrip("0")
            except (ValueError, TypeError):
                pass
        
        linhas_nf = df_comercial[mask]
        
        if linhas_nf.empty:
            logger.warning(f"[DEVOLUCAO] NF {numero_nf} não encontrada na Análise Comercial")
            return None, 0
        
        # Obter processo (deve ser o mesmo para todas as linhas da mesma NF)
        processo = str(linhas_nf.iloc[0][col_processo]).strip()
        
        # Calcular valor realizado total do processo (soma de todos os itens)
        # Buscar TODAS as linhas do processo, não apenas as da NF
        mask_processo = df_comercial[col_processo].astype(str).str.strip() == processo
        linhas_processo = df_comercial[mask_processo]
        
        valor_realizado_total = linhas_processo[col_valor].sum()
        
        logger.info(
            f"[DEVOLUCAO] NF {numero_nf} -> Processo {processo} | "
            f"Valor Realizado Total: R$ {valor_realizado_total:.2f}"
        )
        
        return processo, valor_realizado_total
    
    def _buscar_comissoes_historicas(
        self, 
        processo: str
    ) -> pd.DataFrame:
        """
        Busca comissões históricas para um processo no banco de dados.
        
        Args:
            processo: Identificador do processo
            
        Returns:
            DataFrame com comissões históricas
        """
        # Carregar histórico e filtrar pelo processo
        df_historico = self.master_db.get_historico(processo=processo)
        
        if df_historico.empty:
            logger.warning(f"[DEVOLUCAO] Nenhuma comissão histórica encontrada para processo {processo}")
            return pd.DataFrame()
        
        # Filtrar apenas comissões de FATURAMENTO e REGULAR (não devoluções anteriores)
        col_tipo = self._encontrar_coluna(
            df_historico, 
            ["Tipo_Comissao", "tipo_comissao", "TIPO_COMISSAO"]
        )
        
        if col_tipo:
            tipos_validos = ["FATURAMENTO", "REGULAR", "ADIANTAMENTO"]
            df_historico = df_historico[df_historico[col_tipo].isin(tipos_validos)]
        
        logger.info(
            f"[DEVOLUCAO] Processo {processo}: "
            f"{len(df_historico)} registros de comissão encontrados no histórico"
        )
        
        return df_historico
    
    def processar(
        self,
        mes: int,
        ano: int,
        salvar_no_banco: bool = True,
    ) -> Dict:
        """
        Processa todas as devoluções do período.
        
        Args:
            mes: Mês de apuração (1-12)
            ano: Ano de apuração
            salvar_no_banco: Se True, salva os saldos negativos no banco histórico
            
        Returns:
            Dicionário com resultados do processamento
        """
        logger.info(f"[DEVOLUCAO] Iniciando processamento de devoluções para {mes:02d}/{ano}")
        
        self._saldos_negativos = []
        self._resultados = {
            "mes": mes,
            "ano": ano,
            "devolucoes_carregadas": 0,
            "devolucoes_processadas": 0,
            "devolucoes_ignoradas": 0,
            "saldos_negativos_gerados": 0,
            "total_estorno": 0.0,
            "detalhes_por_processo": [],
            "erros": [],
            "avisos": [],
        }
        
        # 1. Carregar devoluções do período
        sucesso, df_devolucoes, msg = self.loader.carregar(mes, ano)
        
        if not sucesso:
            self._resultados["erros"].append(msg)
            logger.warning(f"[DEVOLUCAO] {msg}")
            return self._resultados
        
        if df_devolucoes.empty:
            self._resultados["avisos"].append(f"Nenhuma devolução encontrada para {mes:02d}/{ano}")
            logger.info(f"[DEVOLUCAO] Nenhuma devolução para processar em {mes:02d}/{ano}")
            return self._resultados
        
        self._resultados["devolucoes_carregadas"] = len(df_devolucoes)
        logger.info(f"[DEVOLUCAO] {len(df_devolucoes)} devoluções carregadas para processamento")
        
        # 2. Carregar Análise Comercial
        df_comercial = self._carregar_analise_comercial()
        if df_comercial.empty:
            self._resultados["erros"].append("Análise Comercial não disponível")
            return self._resultados
        
        # 3. Processar cada devolução
        self.calculator.limpar_logs()
        
        for _, devolucao in df_devolucoes.iterrows():
            numero_nf = str(devolucao["numero_nf_original"]).strip()
            valor_devolvido = float(devolucao["valor_devolvido"])
            data_devolucao = devolucao["data_entrada"]
            
            logger.info(f"[DEVOLUCAO] Processando NF {numero_nf}: R$ {valor_devolvido:.2f}")
            
            # 3a. Vincular NF -> Processo
            processo, valor_realizado = self._vincular_nf_com_processo(numero_nf, df_comercial)
            
            if not processo:
                self._resultados["devolucoes_ignoradas"] += 1
                self._resultados["avisos"].append(
                    f"NF {numero_nf} não encontrada na Análise Comercial"
                )
                continue
            
            # 3b. Buscar comissões históricas
            df_comissoes = self._buscar_comissoes_historicas(processo)
            
            if df_comissoes.empty:
                self._resultados["devolucoes_ignoradas"] += 1
                self._resultados["avisos"].append(
                    f"Processo {processo} sem comissões históricas para estornar"
                )
                continue
            
            # 3c. Calcular saldos negativos
            saldos = self.calculator.calcular_estorno_processo(
                processo=processo,
                numero_nf=numero_nf,
                valor_devolvido=valor_devolvido,
                valor_realizado=valor_realizado,
                comissoes_historicas=df_comissoes,
                data_devolucao=data_devolucao,
                mes_apuracao=mes,
                ano_apuracao=ano,
            )
            
            if saldos:
                self._saldos_negativos.extend(saldos)
                self._resultados["devolucoes_processadas"] += 1
                
                total_processo = sum(s["comissao_calculada"] for s in saldos)
                self._resultados["detalhes_por_processo"].append({
                    "processo": processo,
                    "numero_nf": numero_nf,
                    "valor_devolvido": valor_devolvido,
                    "valor_realizado": valor_realizado,
                    "fator_devolucao": saldos[0]["fator_devolucao"] if saldos else 0,
                    "colaboradores_afetados": len(saldos),
                    "total_estorno": total_processo,
                })
            else:
                self._resultados["devolucoes_ignoradas"] += 1
        
        # Consolidar resultados
        self._resultados["saldos_negativos_gerados"] = len(self._saldos_negativos)
        self._resultados["total_estorno"] = sum(
            s["comissao_calculada"] for s in self._saldos_negativos
        )
        self._resultados["erros"].extend(self.calculator.get_erros())
        self._resultados["avisos"].extend(self.calculator.get_avisos())
        
        logger.info(
            f"[DEVOLUCAO] Processamento concluído: "
            f"{self._resultados['devolucoes_processadas']} devoluções processadas, "
            f"{self._resultados['saldos_negativos_gerados']} saldos negativos, "
            f"Total estorno: R$ {self._resultados['total_estorno']:.2f}"
        )
        
        # 4. Salvar no banco histórico
        if salvar_no_banco and self._saldos_negativos:
            sucesso_salvamento = self._salvar_no_banco_historico(mes, ano)
            if not sucesso_salvamento:
                self._resultados["erros"].append("Falha ao salvar saldos negativos no banco")
        
        return self._resultados
    
    def _salvar_no_banco_historico(self, mes: int, ano: int) -> bool:
        """
        Salva os saldos negativos calculados no banco de dados histórico.
        
        Args:
            mes: Mês de referência
            ano: Ano de referência
            
        Returns:
            True se salvou com sucesso
        """
        if not self._saldos_negativos:
            logger.info("[DEVOLUCAO] Nenhum saldo negativo para salvar")
            return True
        
        try:
            # Converter lista de dicts para DataFrame
            df_saldos = pd.DataFrame(self._saldos_negativos)
            
            # Renomear colunas para o padrão do banco
            column_mapping = {
                "processo": "Processo",
                "numero_nf": "Numero_NF",
                "nome_colaborador": "Nome_Colaborador",
                "cargo": "Cargo",
                "id_colaborador": "id_colaborador",
                "linha": "Linha",
                "valor_base": "Valor_Base",
                "comissao_calculada": "Comissao_Calculada",
                "tipo_comissao": "Tipo_Comissao",
                "origem_correcao": "Origem_Correcao",
                "processo_referencia": "Processo_Referencia",
                "fator_devolucao": "Fator_Devolucao",
                "observacao": "Observacao",
            }
            
            # Aplicar mapeamento
            df_para_salvar = df_saldos.rename(columns=column_mapping)
            
            logger.info(f"[DEVOLUCAO] Salvando {len(df_para_salvar)} saldos negativos no banco histórico")
            
            # Salvar usando o MasterDBManager
            sucesso, msg = self.master_db.append_comissoes(
                df_comissoes=df_para_salvar,
                mes=mes,
                ano=ano,
                tipo_comissao="DEVOLUCAO",
            )
            
            if sucesso:
                logger.info(f"[DEVOLUCAO] Saldos negativos salvos com sucesso: {msg}")
                return True
            else:
                logger.error(f"[DEVOLUCAO] Erro ao salvar saldos negativos: {msg}")
                return False
                
        except Exception as e:
            logger.error(f"[DEVOLUCAO] Exceção ao salvar saldos negativos: {str(e)}")
            return False
    
    def get_saldos_negativos(self) -> List[Dict]:
        """
        Retorna os saldos negativos calculados.
        
        Returns:
            Lista de dicionários com saldos negativos
        """
        return self._saldos_negativos.copy()
    
    def get_saldos_negativos_df(self) -> pd.DataFrame:
        """
        Retorna os saldos negativos como DataFrame.
        
        Returns:
            DataFrame com saldos negativos
        """
        if not self._saldos_negativos:
            return pd.DataFrame()
        return pd.DataFrame(self._saldos_negativos)
    
    def get_resultados(self) -> Dict:
        """
        Retorna os resultados do último processamento.
        
        Returns:
            Dicionário com resultados
        """
        return self._resultados.copy()
