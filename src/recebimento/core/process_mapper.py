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
        
        print(f"[RECEBIMENTO] [MAPPER] __init__: DataFrame recebido com {len(df_analise_comercial)} linhas")
        print(f"[RECEBIMENTO] [MAPPER] __init__: Colunas disponíveis: {list(df_analise_comercial.columns)}")
        
        # Encontrar colunas relevantes
        self.col_nf = self._encontrar_coluna(["numero nf", "número nf", "num nf", "Numero NF"])
        self.col_processo = self._encontrar_coluna(["processo", "id processo", "Processo"])
        
        print(f"[RECEBIMENTO] [MAPPER] __init__: Coluna NF encontrada: '{self.col_nf}'")
        print(f"[RECEBIMENTO] [MAPPER] __init__: Coluna Processo encontrada: '{self.col_processo}'")
    
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
        
        print(f"[RECEBIMENTO] [MAPPER] mapear_documento chamado com: '{documento}' (len={len(documento)})")
        
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
        
        # REGRA 2: Pagamento Regular via NF
        # Extrair apenas dígitos do documento (pode ter 5 ou 6 dígitos)
        doc_digits = ''.join(filter(str.isdigit, documento))
        
        if len(doc_digits) < 5:
            resultado = {
                'mapeado': False,
                'motivo': f'Documento muito curto (menos de 5 dígitos): {documento}'
            }
            self.documentos_nao_mapeados.append({
                'documento': documento,
                'motivo': resultado['motivo']
            })
            return resultado
        
        # Usar os primeiros 6 dígitos (ou todos se tiver menos)
        doc_6dig = doc_digits[:6] if len(doc_digits) >= 6 else doc_digits
        
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
        print(f"[RECEBIMENTO] [MAPPER] Chamando _buscar_por_nf com doc_6dig='{doc_6dig}'")
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
        print(f"[RECEBIMENTO] [MAPPER] _buscar_por_nf: verificando condições iniciais...")
        print(f"[RECEBIMENTO] [MAPPER]   - df_comercial vazio? {self.df_comercial.empty}")
        print(f"[RECEBIMENTO] [MAPPER]   - col_nf encontrada? {self.col_nf}")
        print(f"[RECEBIMENTO] [MAPPER]   - col_processo encontrada? {self.col_processo}")
        
        if self.df_comercial.empty or not self.col_nf or not self.col_processo:
            print(f"[RECEBIMENTO] [MAPPER] ATENÇÃO: Retornando None - condições iniciais não atendidas!")
            return None
        
        try:
            print(f"[RECEBIMENTO] [MAPPER] Buscando NF: doc_6dig='{doc_6dig}'")
            
            # Normalizar doc_6dig: remover zeros à esquerda para comparação
            # Se após remover zeros ficar vazio, manter pelo menos um zero
            doc_6dig_limpo = doc_6dig.lstrip('0') if doc_6dig else ""
            if not doc_6dig_limpo and doc_6dig:
                doc_6dig_limpo = "0"  # Caso especial: todos zeros
            print(f"[RECEBIMENTO] [MAPPER] Documento normalizado (sem zeros à esquerda): '{doc_6dig_limpo}'")
            
            # Normalizar coluna NF:
            # 1) Converter para string e trim
            # 2) Extrair somente a primeira sequência de dígitos (antes de qualquer decimal, ex: "48341.0" -> "48341")
            # 3) Remover zeros à esquerda para comparação consistente
            nfs_raw = self.df_comercial[self.col_nf].astype(str).str.strip()
            nfs_digits = nfs_raw.str.extract(r"(\d+)")[0].fillna("")
            nfs = nfs_digits.str.lstrip('0').replace("", "0")
            
            print(f"[RECEBIMENTO] [MAPPER] Total de linhas na Análise Comercial: {len(nfs)}")
            print(f"[RECEBIMENTO] [MAPPER] Primeiros valores normalizados de NF: {nfs.head(10).tolist()}")
            
            # Buscar matches: comparar valores normalizados (sem zeros à esquerda)
            mask = nfs == doc_6dig_limpo
            candidatos = self.df_comercial[mask]
            
            print(f"[RECEBIMENTO] [MAPPER] Matches encontrados: {len(candidatos)}")
            
            if not candidatos.empty:
                # Retornar o primeiro processo encontrado
                processo = str(candidatos.iloc[0][self.col_processo]).strip()
                print(f"[RECEBIMENTO] [MAPPER] Processo encontrado: '{processo}'")
                return processo if processo and processo != "nan" else None
            else:
                print(f"[RECEBIMENTO] [MAPPER] Nenhum processo encontrado para NF '{doc_6dig}' (normalizado: '{doc_6dig_limpo}')")
        except Exception as e:
            print(f"[RECEBIMENTO] [MAPPER] ERRO ao buscar NF: {e}")
            import traceback
            traceback.print_exc()
        
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
        # Remover BOM (\ufeff) que pode aparecer no início dos nomes das colunas
        colunas_df = {col.lower().strip().replace('\ufeff', ''): col for col in self.df_comercial.columns}
        
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

