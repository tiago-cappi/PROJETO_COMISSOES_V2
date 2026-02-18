"""
src.metodo_v2.recebimento_v2.comissao_recebimento_calculator_v2 - Calculadora de Comissões

Calcula comissões para colaboradores do tipo "recebimento" na V2.

Dois modos de cálculo:
1. ADIANTAMENTO: Usa taxa_adiantamento_pct fixa do colaborador
2. REGULAR/FATURADO: Usa regras/faixas definidas em REGRAS_COMISSAO_V2 ou REGRAS_COMISSAO_CC_V2

Não usa Fator de Correção (FC) - V2 não implementa essa lógica.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..models_v2 import ColaboradorV2, RegraComissao


logger = logging.getLogger(__name__)


@dataclass
class ResultadoComissaoRecebimentoV2:
    """Resultado do cálculo de comissão por recebimento.
    
    Attributes:
        colaborador_id: ID do colaborador.
        colaborador_nome: Nome do colaborador.
        documento: Documento original.
        documento_normalizado: Documento normalizado.
        valor_base: Valor base para cálculo.
        percentual_aplicado: Percentual aplicado.
        comissao_calculada: Valor da comissão.
        tipo_calculo: "ADIANTAMENTO" ou "REGULAR".
        regra_utilizada: Nome da regra (se aplicável).
        faixa_utilizada: Faixa (se aplicável).
    """
    colaborador_id: str
    colaborador_nome: str
    documento: str
    documento_normalizado: str
    valor_base: float
    percentual_aplicado: float
    comissao_calculada: float
    tipo_calculo: str
    regra_utilizada: Optional[str] = None
    faixa_utilizada: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "Colaborador ID": self.colaborador_id,
            "Colaborador Nome": self.colaborador_nome,
            "Documento": self.documento,
            "Documento Normalizado": self.documento_normalizado,
            "Valor Base": self.valor_base,
            "Percentual Aplicado": self.percentual_aplicado,
            "Comissão Calculada": self.comissao_calculada,
            "Tipo Cálculo": self.tipo_calculo,
            "Regra Utilizada": self.regra_utilizada or "",
            "Faixa Utilizada": self.faixa_utilizada or ""
        }


class ComissaoRecebimentoCalculatorV2:
    """Calculadora de comissões por recebimento para V2.
    
    Modos:
    - Hierarquia: Usa regras de REGRAS_COMISSAO_V2
    - Centro de Custo: Usa regras de REGRAS_COMISSAO_CC_V2
    """
    
    def __init__(
        self,
        colaboradores: Dict[str, ColaboradorV2],
        regras: Dict[str, RegraComissao],
        modo_cc: bool = False
    ):
        """Inicializa a calculadora.
        
        Args:
            colaboradores: Dicionário de colaboradores por ID.
            regras: Dicionário de regras por nome.
            modo_cc: Se True, usa modo Centro de Custo.
        """
        self.colaboradores = colaboradores
        self.regras = regras
        self.modo_cc = modo_cc
        
        # Indexar colaboradores por nome para busca
        self._colab_por_nome: Dict[str, ColaboradorV2] = {
            c.nome.upper(): c for c in colaboradores.values()
        }
        
        logger.info(f"[V2-REC-CALC] Inicializado com {len(colaboradores)} colaboradores, {len(regras)} regras (modo_cc={modo_cc})")
    
    def obter_colaborador_por_nome(self, nome: str) -> Optional[ColaboradorV2]:
        """Obtém colaborador por nome.
        
        Args:
            nome: Nome do colaborador.
            
        Returns:
            ColaboradorV2 ou None.
        """
        return self._colab_por_nome.get(nome.upper().strip())
    
    def calcular_adiantamento(
        self,
        colaborador: ColaboradorV2,
        documento: str,
        documento_normalizado: str,
        valor_pagamento: float
    ) -> ResultadoComissaoRecebimentoV2:
        """Calcula comissão de adiantamento usando taxa fixa.
        
        Args:
            colaborador: Colaborador.
            documento: Documento original.
            documento_normalizado: Documento normalizado.
            valor_pagamento: Valor do pagamento.
            
        Returns:
            ResultadoComissaoRecebimentoV2.
        """
        if not colaborador.recebe_por_recebimento:
            logger.warning(f"[V2-REC-CALC] Colaborador não recebe por recebimento: {colaborador.nome}")
            return ResultadoComissaoRecebimentoV2(
                colaborador_id=colaborador.nome,  # V2 usa nome como ID
                colaborador_nome=colaborador.nome,
                documento=documento,
                documento_normalizado=documento_normalizado,
                valor_base=valor_pagamento,
                percentual_aplicado=0.0,
                comissao_calculada=0.0,
                tipo_calculo="ADIANTAMENTO"
            )
        
        taxa = colaborador.taxa_adiantamento_pct or 0.0
        comissao = valor_pagamento * (taxa / 100.0)
        
        logger.debug(
            f"[V2-REC-CALC] Adiantamento: {colaborador.nome} | "
            f"Doc={documento_normalizado} | Valor={valor_pagamento:.2f} | "
            f"Taxa={taxa:.2f}% | Comissão={comissao:.2f}"
        )
        
        return ResultadoComissaoRecebimentoV2(
            colaborador_id=colaborador.nome,  # V2 usa nome como ID
            colaborador_nome=colaborador.nome,
            documento=documento,
            documento_normalizado=documento_normalizado,
            valor_base=valor_pagamento,
            percentual_aplicado=taxa,
            comissao_calculada=comissao,
            tipo_calculo="ADIANTAMENTO"
        )
    
    def calcular_regular(
        self,
        colaborador: ColaboradorV2,
        documento: str,
        documento_normalizado: str,
        valor_faturado: float,
        margem_pct: Optional[float] = None
    ) -> ResultadoComissaoRecebimentoV2:
        """Calcula comissão regular usando regras/faixas.
        
        Args:
            colaborador: Colaborador.
            documento: Documento original.
            documento_normalizado: Documento normalizado.
            valor_faturado: Valor faturado.
            margem_pct: Margem percentual (não utilizado na V2).
            
        Returns:
            ResultadoComissaoRecebimentoV2.
        """
        # Na V2, colaborador pode ter múltiplas regras por hierarquia
        # Para recebimento, usamos a primeira regra disponível ou taxa fixa
        regra = colaborador.regras[0] if colaborador.regras else None
        
        if not regra:
            # Sem regra hierárquica, usar taxa_adiantamento como fallback
            taxa = colaborador.taxa_adiantamento_pct or 0.0
            logger.warning(f"[V2-REC-CALC] Sem regra hierárquica para {colaborador.nome}, usando taxa_adiantamento={taxa}%")
            return ResultadoComissaoRecebimentoV2(
                colaborador_id=colaborador.nome,  # V2 usa nome como ID
                colaborador_nome=colaborador.nome,
                documento=documento,
                documento_normalizado=documento_normalizado,
                valor_base=valor_faturado,
                percentual_aplicado=taxa,
                comissao_calculada=valor_faturado * (taxa / 100.0),
                tipo_calculo="REGULAR",
                regra_utilizada=None
            )
        
        # Usar método get_taxa_para_faturamento da regra
        percentual = regra.get_taxa_para_faturamento(valor_faturado)
        faixa_nome = self._identificar_faixa(regra, valor_faturado)
        
        comissao = valor_faturado * (percentual / 100.0)
        
        logger.debug(
            f"[V2-REC-CALC] Regular: {colaborador.nome} | "
            f"Doc={documento_normalizado} | Valor={valor_faturado:.2f} | "
            f"RegraID={regra.regra_id} | Faixa={faixa_nome} | "
            f"Pct={percentual:.2f}% | Comissão={comissao:.2f}"
        )
        
        return ResultadoComissaoRecebimentoV2(
            colaborador_id=colaborador.nome,  # V2 usa nome como ID
            colaborador_nome=colaborador.nome,
            documento=documento,
            documento_normalizado=documento_normalizado,
            valor_base=valor_faturado,
            percentual_aplicado=percentual,
            comissao_calculada=comissao,
            tipo_calculo="REGULAR",
            regra_utilizada=f"Regra_{regra.regra_id}",
            faixa_utilizada=faixa_nome
        )
    
    def _identificar_faixa(
        self, 
        regra: RegraComissao, 
        valor: float
    ) -> str:
        """Identifica qual faixa se aplica ao valor.
        
        Args:
            regra: Regra de comissão.
            valor: Valor para verificar.
            
        Returns:
            Descrição da faixa.
        """
        for i, faixa in enumerate(regra.faixas):
            if faixa.aplica_ao_faturamento(valor):
                return f"Faixa_{i+1}_{faixa.limite_inferior}"
        return "SEM_FAIXA"
    
    def calcular_lote_adiantamentos(
        self,
        adiantamentos: List[dict]
    ) -> List[ResultadoComissaoRecebimentoV2]:
        """Calcula comissões para um lote de adiantamentos.
        
        Args:
            adiantamentos: Lista de dicts com:
                - colaborador_nome: Nome do colaborador
                - documento: Documento original
                - documento_normalizado: Documento normalizado
                - valor: Valor do pagamento
                
        Returns:
            Lista de resultados.
        """
        resultados = []
        
        for item in adiantamentos:
            colab_nome = item.get("colaborador_nome", "")
            colaborador = self.obter_colaborador_por_nome(colab_nome)
            
            if not colaborador:
                logger.warning(f"[V2-REC-CALC] Colaborador não encontrado: {colab_nome}")
                continue
            
            if not colaborador.recebe_por_recebimento:
                logger.debug(f"[V2-REC-CALC] Colaborador não é recebimento: {colab_nome}")
                continue
            
            resultado = self.calcular_adiantamento(
                colaborador=colaborador,
                documento=item.get("documento", ""),
                documento_normalizado=item.get("documento_normalizado", ""),
                valor_pagamento=float(item.get("valor", 0))
            )
            
            resultados.append(resultado)
        
        return resultados
    
    def to_dataframe(
        self, 
        resultados: List[ResultadoComissaoRecebimentoV2]
    ) -> pd.DataFrame:
        """Converte resultados para DataFrame.
        
        Args:
            resultados: Lista de resultados.
            
        Returns:
            DataFrame com resultados.
        """
        if not resultados:
            return pd.DataFrame(columns=[
                "Colaborador ID", "Colaborador Nome", "Documento",
                "Documento Normalizado", "Valor Base", "Percentual Aplicado",
                "Comissão Calculada", "Tipo Cálculo", "Regra Utilizada", "Faixa Utilizada"
            ])
        
        return pd.DataFrame([r.to_dict() for r in resultados])
