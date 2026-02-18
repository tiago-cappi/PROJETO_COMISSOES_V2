"""
src.metodo_v2.comissao_calculator_v2 - Calculador de Comissão V2

Nova arquitetura: calcula comissão baseada em faixas de faturamento por
combinação hierárquica.

Fluxo:
1. Recebe faturamentos agrupados por hierarquia
2. Para cada hierarquia, encontra a regra mais específica (via RegraMatcher)
3. Determina a faixa de comissão baseada no faturamento
4. Calcula comissão = faturamento × taxa da faixa
5. Soma todas as comissões por hierarquia

Fórmula por hierarquia:
    Comissão_h = Faturamento_h × Taxa_faixa(Faturamento_h)
    
Total:
    Comissão_Total = Σ Comissão_h
"""

from __future__ import annotations

import logging
from typing import List, Dict, Tuple, Any

from .models_v2 import (
    ColaboradorV2,
    RegraComissao,
    ResultadoHierarquia,
    ResultadoColaboradorV2,
)
from .regra_matcher_v2 import RegraMatcher


logger = logging.getLogger(__name__)


class ComissaoCalculatorV2:
    """Calculador de comissão para a Metodologia V2.
    
    Processa faturamentos por hierarquia e calcula comissão baseada em faixas.
    """

    def __init__(self):
        """Inicializa o calculador com o matcher de regras."""
        self.matcher = RegraMatcher()

    def calcular(
        self,
        colaborador: ColaboradorV2,
        mes_ano: str,
        faturamentos_por_hierarquia: Dict[Tuple[str, str, str, str, str], float],
    ) -> ResultadoColaboradorV2:
        """Calcula a comissão total para um colaborador.
        
        Args:
            colaborador: Colaborador com suas regras de comissão.
            mes_ano: Período de referência (ex: "2026-01").
            faturamentos_por_hierarquia: Dict mapeando hierarquia -> faturamento.
                Hierarquia é uma tupla (linha, grupo, subgrupo, tipo_mercadoria, fabricante).
                
        Returns:
            ResultadoColaboradorV2 com detalhamento por hierarquia.
        """
        resultados_hierarquia: List[ResultadoHierarquia] = []
        hierarquias_sem_regra: List[Dict[str, Any]] = []
        faturamento_total = 0.0
        comissao_total = 0.0

        for hierarquia, faturamento in faturamentos_por_hierarquia.items():
            linha, grupo, subgrupo, tipo_mercadoria, fabricante = hierarquia
            faturamento_total += faturamento

            # Encontrar regra mais específica
            regra = self.matcher.encontrar_regra(
                colaborador, linha, grupo, subgrupo, tipo_mercadoria, fabricante
            )

            if regra:
                # Determinar taxa da faixa
                taxa = regra.get_taxa_para_faturamento(faturamento)
                comissao = faturamento * (taxa / 100.0)
                comissao_total += comissao

                resultado_h = ResultadoHierarquia(
                    linha=linha,
                    grupo=grupo,
                    subgrupo=subgrupo,
                    tipo_mercadoria=tipo_mercadoria,
                    fabricante=fabricante,
                    faturamento=round(faturamento, 2),
                    regra_aplicada=regra,
                    taxa_aplicada=taxa,
                    comissao=round(comissao, 2),
                )
                resultados_hierarquia.append(resultado_h)

                logger.debug(
                    f"Hierarquia processada: {linha}>{fabricante} | "
                    f"Fat={faturamento:,.2f} | Taxa={taxa}% | Com={comissao:,.2f}"
                )
            else:
                # Registrar hierarquia sem regra (comissão zero)
                hierarquias_sem_regra.append({
                    "linha": linha,
                    "grupo": grupo,
                    "subgrupo": subgrupo,
                    "tipo_mercadoria": tipo_mercadoria,
                    "fabricante": fabricante,
                    "faturamento": round(faturamento, 2),
                })
                logger.warning(
                    f"Sem regra para '{colaborador.nome}': "
                    f"{linha}>{grupo}>{subgrupo}>{tipo_mercadoria}>{fabricante} "
                    f"(Faturamento: R$ {faturamento:,.2f})"
                )

        resultado = ResultadoColaboradorV2(
            nome_colaborador=colaborador.nome,
            cargo=colaborador.cargo,
            mes_ano=mes_ano,
            faturamento_total=round(faturamento_total, 2),
            comissao_total=round(comissao_total, 2),
            resultados_por_hierarquia=resultados_hierarquia,
            hierarquias_sem_regra=hierarquias_sem_regra,
        )

        logger.info(
            f"Comissão calculada para '{colaborador.nome}': "
            f"R$ {comissao_total:,.2f} (Fat={faturamento_total:,.2f}, "
            f"Hierarquias={len(resultados_hierarquia)}, Sem regra={len(hierarquias_sem_regra)})"
        )

        return resultado

    def calcular_simulacao(
        self,
        regra: RegraComissao,
        faturamento: float,
    ) -> Dict[str, Any]:
        """Simula o cálculo de comissão para uma regra e faturamento.
        
        Útil para preview no frontend.
        
        Args:
            regra: Regra de comissão a aplicar.
            faturamento: Valor de faturamento para simular.
            
        Returns:
            Dict com taxa aplicada e comissão calculada.
        """
        taxa = regra.get_taxa_para_faturamento(faturamento)
        comissao = faturamento * (taxa / 100.0)
        
        return {
            "faturamento": faturamento,
            "taxa_aplicada": taxa,
            "comissao": round(comissao, 2),
            "faixa_atingida": self._identificar_faixa(regra, faturamento),
        }

    def _identificar_faixa(self, regra: RegraComissao, faturamento: float) -> int:
        """Identifica qual faixa foi atingida (1-indexado).
        
        Args:
            regra: Regra com faixas.
            faturamento: Valor do faturamento.
            
        Returns:
            Índice da faixa (1-5) ou 0 se sem faixas.
        """
        if not regra.faixas:
            return 0
        
        faixa_idx = 1
        for i, faixa in enumerate(regra.faixas):
            if faturamento >= faixa.limite_inferior:
                faixa_idx = i + 1
        
        return faixa_idx
