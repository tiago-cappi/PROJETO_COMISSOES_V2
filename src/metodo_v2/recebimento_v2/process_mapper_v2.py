"""
src.metodo_v2.recebimento_v2.process_mapper_v2 - Mapeador de Processos

Classifica documentos da Análise Financeira em:
- ADIANTAMENTO: Documento começa com "COT" (prefixo de cotação)
- REGULAR: Documento tem 6 dígitos numéricos (NF)

Lógica idêntica ao método padrão, implementada de forma independente.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import pandas as pd


logger = logging.getLogger(__name__)


class TipoProcesso(Enum):
    """Tipo de processo (adiantamento ou regular)."""
    ADIANTAMENTO = "ADIANTAMENTO"
    REGULAR = "REGULAR"
    DESCONHECIDO = "DESCONHECIDO"


@dataclass
class ProcessoMapeado:
    """Processo mapeado com classificação.
    
    Attributes:
        documento: Número do documento original.
        documento_normalizado: Documento normalizado (sem COT, só NF).
        valor_liquido: Valor líquido do pagamento.
        data_baixa: Data do pagamento (pode ser None/NaT).
        tipo: Tipo do processo (ADIANTAMENTO ou REGULAR).
    """
    documento: str
    documento_normalizado: str
    valor_liquido: float
    data_baixa: Optional[pd.Timestamp]  # Pode ser NaT ou None
    tipo: TipoProcesso
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "Documento": self.documento,
            "Documento Normalizado": self.documento_normalizado,
            "Valor Líquido": self.valor_liquido,
            "Data de Baixa": self.data_baixa,
            "Tipo Processo": self.tipo.value
        }


class ProcessMapperV2:
    """Mapeador de processos para V2.
    
    Classifica documentos em ADIANTAMENTO ou REGULAR usando padrões:
    - COT*: Adiantamento (documento começa com COT)
    - 6 dígitos: NF regular
    """
    
    # Padrões para classificação
    PADRAO_ADIANTAMENTO = re.compile(r'^COT', re.IGNORECASE)
    PADRAO_NF = re.compile(r'^\d{6}$')
    
    def __init__(self):
        """Inicializa o mapeador."""
        pass
    
    def classificar_documento(self, documento: str) -> TipoProcesso:
        """Classifica um documento individual.
        
        Args:
            documento: Número do documento.
            
        Returns:
            TipoProcesso (ADIANTAMENTO, REGULAR ou DESCONHECIDO).
        """
        doc_limpo = str(documento).strip().upper()
        
        if not doc_limpo or doc_limpo == "NAN":
            return TipoProcesso.DESCONHECIDO
        
        # COT* → Adiantamento
        if self.PADRAO_ADIANTAMENTO.match(doc_limpo):
            return TipoProcesso.ADIANTAMENTO
        
        # 6 dígitos → Regular (NF)
        if self.PADRAO_NF.match(doc_limpo):
            return TipoProcesso.REGULAR
        
        # Documentos desconhecidos são tratados como REGULAR
        # (comportamento compatível com método padrão)
        return TipoProcesso.REGULAR
    
    def normalizar_documento(self, documento: str, tipo: TipoProcesso) -> str:
        """Normaliza documento para vinculação.
        
        Args:
            documento: Número do documento.
            tipo: Tipo classificado.
            
        Returns:
            Documento normalizado (NF extraída).
        """
        doc_limpo = str(documento).strip().upper()
        
        if tipo == TipoProcesso.ADIANTAMENTO:
            # COT12345 → 12345 (extrair números após COT)
            match = re.search(r'COT\s*(\d+)', doc_limpo, re.IGNORECASE)
            if match:
                return match.group(1).zfill(6)  # Preencher com zeros à esquerda
            # Se não encontrar padrão, retornar original
            return doc_limpo
        
        # Regular: normalizar removendo zeros à esquerda para casar com AC NFs
        doc_stripped = doc_limpo.lstrip('0') or '0'
        return doc_stripped
    
    def mapear_pagamentos(self, df_pagamentos: pd.DataFrame) -> List[ProcessoMapeado]:
        """Mapeia todos os pagamentos de um DataFrame.
        
        Args:
            df_pagamentos: DataFrame com colunas:
                - Documento
                - Valor Líquido
                - Data de Baixa
                
        Returns:
            Lista de ProcessoMapeado.
        """
        if df_pagamentos.empty:
            logger.info("[V2-REC] Nenhum pagamento para mapear")
            return []
        
        resultados = []
        stats = {"ADIANTAMENTO": 0, "REGULAR": 0, "DESCONHECIDO": 0}
        
        for _, row in df_pagamentos.iterrows():
            documento = str(row.get("Documento", "")).strip()
            valor = row.get("Valor Líquido", 0)
            data = row.get("Data de Baixa")
            
            tipo = self.classificar_documento(documento)
            doc_normalizado = self.normalizar_documento(documento, tipo)
            
            processo = ProcessoMapeado(
                documento=documento,
                documento_normalizado=doc_normalizado,
                valor_liquido=float(valor) if pd.notna(valor) else 0.0,
                data_baixa=pd.Timestamp(data) if pd.notna(data) else pd.NaT,
                tipo=tipo
            )
            
            resultados.append(processo)
            stats[tipo.value] += 1
        
        logger.info(f"[V2-REC] Mapeamento concluído: {stats}")
        
        return resultados
    
    def filtrar_adiantamentos(
        self, 
        processos: List[ProcessoMapeado]
    ) -> List[ProcessoMapeado]:
        """Filtra apenas adiantamentos.
        
        Args:
            processos: Lista de processos mapeados.
            
        Returns:
            Lista contendo apenas adiantamentos.
        """
        return [p for p in processos if p.tipo == TipoProcesso.ADIANTAMENTO]
    
    def filtrar_regulares(
        self, 
        processos: List[ProcessoMapeado]
    ) -> List[ProcessoMapeado]:
        """Filtra apenas processos regulares.
        
        Args:
            processos: Lista de processos mapeados.
            
        Returns:
            Lista contendo apenas processos regulares.
        """
        return [p for p in processos if p.tipo == TipoProcesso.REGULAR]
    
    def to_dataframe(self, processos: List[ProcessoMapeado]) -> pd.DataFrame:
        """Converte lista de processos para DataFrame.
        
        Args:
            processos: Lista de ProcessoMapeado.
            
        Returns:
            DataFrame com dados dos processos.
        """
        if not processos:
            return pd.DataFrame(columns=[
                "Documento", "Documento Normalizado", 
                "Valor Líquido", "Data de Baixa", "Tipo Processo"
            ])
        
        return pd.DataFrame([p.to_dict() for p in processos])
