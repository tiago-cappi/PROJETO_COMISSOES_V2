"""
src.metodo_v2.regra_matcher_v2 - Matcher de Regras de Comissão

Responsável por encontrar a regra mais específica que dá match com uma
combinação hierárquica de produto.

Algoritmo de Match:
1. Para cada regra do colaborador, verificar se dá match com a hierarquia
2. Entre as regras que deram match, selecionar a de MAIOR especificidade
3. Especificidade = quantidade de campos definidos (não-wildcard)

Exemplo:
    Hierarquia: (Hidrologia, Amostrador, amostrador, Produto, QED)
    
    Regra 1: (linha=Hidrologia, fabricante=QED) → especificidade=2, MATCH
    Regra 2: (linha=Hidrologia, grupo=Amostrador, ..., fabricante=QED) → especificidade=5, MATCH
    
    Resultado: Regra 2 é selecionada (maior especificidade)
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from .models_v2 import ColaboradorV2, RegraComissao


logger = logging.getLogger(__name__)


class RegraMatcher:
    """Matcher de regras de comissão por especificidade.
    
    Encontra a regra mais específica que dá match com uma hierarquia de produto.
    """

    def encontrar_regra(
        self,
        colaborador: ColaboradorV2,
        linha: str,
        grupo: str,
        subgrupo: str,
        tipo_mercadoria: str,
        fabricante: str,
    ) -> Optional[RegraComissao]:
        """Encontra a regra mais específica para uma combinação hierárquica.
        
        Args:
            colaborador: Colaborador com suas regras configuradas.
            linha, grupo, subgrupo, tipo_mercadoria, fabricante: Hierarquia do produto.
            
        Returns:
            RegraComissao mais específica que dá match, ou None se nenhuma der match.
        """
        if not colaborador.regras:
            logger.debug(f"Colaborador '{colaborador.nome}' não possui regras configuradas")
            return None

        # As regras já estão ordenadas por especificidade (maior primeiro) no ColaboradorV2
        # Então a primeira que der match é a mais específica
        for regra in colaborador.regras:
            if regra.match(linha, grupo, subgrupo, tipo_mercadoria, fabricante):
                logger.debug(
                    f"Match encontrado para '{colaborador.nome}': "
                    f"Regra {regra.regra_id} (especificidade={regra.especificidade})"
                )
                return regra

        logger.debug(
            f"Nenhuma regra encontrada para '{colaborador.nome}' na hierarquia: "
            f"{linha} > {grupo} > {subgrupo} > {tipo_mercadoria} > {fabricante}"
        )
        return None

    def encontrar_regras_candidatas(
        self,
        colaborador: ColaboradorV2,
        linha: str,
        grupo: str,
        subgrupo: str,
        tipo_mercadoria: str,
        fabricante: str,
    ) -> List[Tuple[RegraComissao, int]]:
        """Encontra todas as regras que dão match, ordenadas por especificidade.
        
        Útil para debug e auditoria.
        
        Args:
            colaborador: Colaborador com suas regras.
            linha, grupo, subgrupo, tipo_mercadoria, fabricante: Hierarquia.
            
        Returns:
            Lista de tuplas (regra, especificidade), ordenadas por especificidade desc.
        """
        candidatas = []
        
        for regra in colaborador.regras:
            if regra.match(linha, grupo, subgrupo, tipo_mercadoria, fabricante):
                candidatas.append((regra, regra.especificidade))
        
        # Ordenar por especificidade (maior primeiro)
        candidatas.sort(key=lambda x: x[1], reverse=True)
        return candidatas

    def calcular_cobertura(
        self,
        colaborador: ColaboradorV2,
        hierarquias: List[Tuple[str, str, str, str, str]],
    ) -> dict:
        """Calcula a cobertura das regras do colaborador sobre uma lista de hierarquias.
        
        Útil para identificar hierarquias sem regra configurada.
        
        Args:
            colaborador: Colaborador com suas regras.
            hierarquias: Lista de tuplas (linha, grupo, subgrupo, tipo, fabricante).
            
        Returns:
            Dict com estatísticas de cobertura:
            - total_hierarquias: int
            - cobertas: int
            - sem_cobertura: List[tuple]
            - cobertura_pct: float
        """
        cobertas = 0
        sem_cobertura = []
        
        for h in hierarquias:
            linha, grupo, subgrupo, tipo_mercadoria, fabricante = h
            regra = self.encontrar_regra(
                colaborador, linha, grupo, subgrupo, tipo_mercadoria, fabricante
            )
            if regra:
                cobertas += 1
            else:
                sem_cobertura.append(h)
        
        total = len(hierarquias)
        return {
            "total_hierarquias": total,
            "cobertas": cobertas,
            "sem_cobertura": sem_cobertura,
            "cobertura_pct": (cobertas / total * 100) if total > 0 else 0.0,
        }
