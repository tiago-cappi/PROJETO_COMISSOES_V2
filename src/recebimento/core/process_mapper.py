"""
Mapeia documentos da Análise Financeira para processos comerciais.
"""

import pandas as pd
from typing import Dict, Optional, List
import re


class ProcessMapper:
    """
    Mapeia documentos financeiros para processos comerciais.
    
    Regras de mapeamento:
    - Se Documento começa com "COT": é Adiantamento, processo = sufixo numérico
    - Caso contrário: Pagamento Regular, busca por 6 primeiros dígitos na coluna "Numero NF"
    """
    
    def __init__(self, df_analise_comercial: pd.DataFrame):
        """
        Inicializa o mapeador.
        
        Args:
            df_analise_comercial: DataFrame da Análise Comercial Completa
        """
        self.df_comercial = df_analise_comercial
        self.documentos_nao_mapeados = []
        self.cache_mapeamento = {}
        
        # Encontrar colunas relevantes
        self.col_nf = self._encontrar_coluna(["numero nf", "número nf", "num nf", "Numero NF"])
        self.col_processo = self._encontrar_coluna(["processo", "id processo", "Processo"])
    
    def mapear_documento(self, documento: str) -> Dict:
        """
        Mapeia um documento para um processo.
        
        Args:
            documento: Documento da Análise Financeira (já normalizado: trim, uppercase)
        
        Returns:
            Dict com:
            - 'mapeado': bool
            - 'processo': str (se mapeado)
            - 'tipo': 'ADIANTAMENTO' | 'PAGAMENTO_REGULAR' (se mapeado)
            - 'numero_nf': str (se pagamento regular)
            - 'motivo': str (se não mapeado)
        """
        if not documento or pd.isna(documento):
            return {
                'mapeado': False,
                'motivo': 'Documento vazio ou inválido'
            }
        
        documento = str(documento).strip().upper()
        
        # Verificar cache
        if documento in self.cache_mapeamento:
            return self.cache_mapeamento[documento]
        
        # REGRA 1: COT → Adiantamento
        if documento.startswith("COT"):
            processo = documento.replace("COT", "").strip()
            # Validar que o sufixo é numérico
            if processo.isdigit():
                resultado = {
                    'processo': processo,
                    'tipo': 'ADIANTAMENTO',
                    'mapeado': True
                }
                self.cache_mapeamento[documento] = resultado
                return resultado
            else:
                resultado = {
                    'mapeado': False,
                    'motivo': f'COT sem sufixo numérico válido: {documento}'
                }
                self.documentos_nao_mapeados.append({
                    'documento': documento,
                    'motivo': resultado['motivo']
                })
                return resultado
        
        # REGRA 2: Pagamento Regular via NF (6 primeiros dígitos)
        if len(documento) < 6:
            resultado = {
                'mapeado': False,
                'motivo': f'Documento muito curto para extrair 6 dígitos: {documento}'
            }
            self.documentos_nao_mapeados.append({
                'documento': documento,
                'motivo': resultado['motivo']
            })
            return resultado
        
        doc_6dig = documento[:6]
        
        # Validar que os 6 dígitos são numéricos
        if not doc_6dig.isdigit():
            resultado = {
                'mapeado': False,
                'motivo': f'6 primeiros caracteres não são numéricos: {documento}'
            }
            self.documentos_nao_mapeados.append({
                'documento': documento,
                'documento_6dig': doc_6dig,
                'motivo': resultado['motivo']
            })
            return resultado
        
        # Buscar na coluna "Numero NF" do Analise_Comercial_Completa
        processo = self._buscar_por_nf(doc_6dig)
        
        if processo:
            resultado = {
                'processo': processo,
                'tipo': 'PAGAMENTO_REGULAR',
                'numero_nf': doc_6dig,
                'mapeado': True
            }
            self.cache_mapeamento[documento] = resultado
            return resultado
        else:
            resultado = {
                'mapeado': False,
                'motivo': f'NF não encontrada na Análise Comercial: {doc_6dig}'
            }
            self.documentos_nao_mapeados.append({
                'documento': documento,
                'documento_6dig': doc_6dig,
                'motivo': resultado['motivo']
            })
            return resultado
    
    def _buscar_por_nf(self, doc_6dig: str) -> Optional[str]:
        """
        Busca processo pela NF (6 primeiros dígitos).
        
        Args:
            doc_6dig: 6 primeiros dígitos do documento
        
        Returns:
            ID do processo ou None se não encontrado
        """
        if self.df_comercial.empty or not self.col_nf or not self.col_processo:
            return None
        
        try:
            # Normalizar coluna NF: remover caracteres não numéricos
            nfs = (
                self.df_comercial[self.col_nf]
                .astype(str)
                .str.replace(r"\D", "", regex=True)
            )
            
            # Buscar matches
            mask = nfs.str.contains(doc_6dig, na=False)
            candidatos = self.df_comercial[mask]
            
            if not candidatos.empty:
                # Retornar o primeiro processo encontrado
                processo = str(candidatos.iloc[0][self.col_processo]).strip()
                return processo if processo and processo != "nan" else None
        except Exception:
            pass
        
        return None
    
    def _encontrar_coluna(self, nomes_possiveis: List[str]) -> Optional[str]:
        """
        Encontra uma coluna no DataFrame por nomes possíveis.
        
        Args:
            nomes_possiveis: Lista de nomes possíveis para a coluna
        
        Returns:
            Nome da coluna encontrada ou None
        """
        if self.df_comercial.empty:
            return None
        
        # Normalizar nomes de colunas do DataFrame
        colunas_df = {col.lower().strip(): col for col in self.df_comercial.columns}
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_df:
                return colunas_df[nome_norm]
        
        return None
    
    def obter_documentos_nao_mapeados(self) -> pd.DataFrame:
        """
        Retorna DataFrame com documentos não mapeados.
        
        Returns:
            DataFrame com colunas: documento, documento_6dig (se aplicável), motivo
        """
        if not self.documentos_nao_mapeados:
            return pd.DataFrame(columns=["documento", "documento_6dig", "motivo"])
        
        return pd.DataFrame(self.documentos_nao_mapeados)

