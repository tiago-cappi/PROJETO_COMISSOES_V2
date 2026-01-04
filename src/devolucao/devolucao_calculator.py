"""
Calculadora de Saldos Negativos por Devolução.

Aplica o cálculo proporcional para gerar saldos negativos
baseado no fator de devolução (valor_devolvido / valor_realizado).
"""

import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DevolucaoCalculator:
    """
    Calcula saldos negativos proporcionais para devoluções.
    
    Fórmula:
    - Fator = Valor_Devolvido / Valor_Realizado_Processo
    - Saldo_Negativo = Comissão_Histórica × Fator
    
    O valor resultante é NEGATIVO (débito ao colaborador).
    """
    
    def __init__(self):
        """Inicializa a calculadora."""
        self._erros: List[str] = []
        self._avisos: List[str] = []
    
    def calcular_fator_devolucao(
        self,
        valor_devolvido: float,
        valor_realizado: float
    ) -> float:
        """
        Calcula o fator de devolução.
        
        O fator é limitado a 1.0 (100%) para casos onde
        valor_devolvido > valor_realizado (erro de dados).
        
        Args:
            valor_devolvido: Valor total devolvido
            valor_realizado: Valor total do processo
            
        Returns:
            Fator entre 0.0 e 1.0
        """
        if valor_realizado <= 0:
            self._avisos.append(
                f"Valor realizado inválido ({valor_realizado}), fator definido como 0"
            )
            return 0.0
        
        fator = valor_devolvido / valor_realizado
        
        # Limitar a 1.0 (máximo 100%)
        if fator > 1.0:
            self._avisos.append(
                f"Fator de devolução {fator:.4f} > 1.0, limitado a 1.0. "
                f"(Devolvido: {valor_devolvido}, Realizado: {valor_realizado})"
            )
            fator = 1.0
        
        return fator
    
    def calcular_estorno_processo(
        self,
        processo: str,
        numero_nf: str,
        valor_devolvido: float,
        valor_realizado: float,
        comissoes_historicas: pd.DataFrame,
        data_devolucao: datetime,
        mes_apuracao: int,
        ano_apuracao: int,
    ) -> List[Dict]:
        """
        Calcula saldos negativos para um processo com devolução.
        
        Args:
            processo: Identificador do processo
            numero_nf: Número da NF que teve devolução
            valor_devolvido: Valor total devolvido
            valor_realizado: Valor total do processo (soma de Valor Realizado)
            comissoes_historicas: DataFrame com comissões já pagas 
                                  (deve ter: Nome_Colaborador, Comissao_Calculada, etc.)
            data_devolucao: Data em que a devolução ocorreu
            mes_apuracao: Mês de apuração atual
            ano_apuracao: Ano de apuração atual
            
        Returns:
            Lista de dicionários com saldos negativos por colaborador
        """
        saldos_negativos = []
        
        # Calcular fator de devolução
        fator = self.calcular_fator_devolucao(valor_devolvido, valor_realizado)
        
        if fator == 0:
            logger.warning(f"[DEVOLUCAO] Fator zero para processo {processo}, ignorando")
            return []
        
        logger.info(
            f"[DEVOLUCAO] Processo {processo}: "
            f"Devolvido={valor_devolvido:.2f}, Realizado={valor_realizado:.2f}, "
            f"Fator={fator:.4f} ({fator*100:.2f}%)"
        )
        
        # Verificar se há comissões históricas
        if comissoes_historicas.empty:
            self._avisos.append(
                f"Processo {processo}: Sem comissões históricas para estornar"
            )
            logger.warning(f"[DEVOLUCAO] Processo {processo}: Sem comissões históricas")
            return []
        
        # Agrupar comissões por colaborador para totalizar
        # (um colaborador pode ter múltiplas linhas de comissão no mesmo processo)
        col_colaborador = self._encontrar_coluna(
            comissoes_historicas, 
            ["Nome_Colaborador", "nome_colaborador", "NOME_COLABORADOR"]
        )
        col_comissao = self._encontrar_coluna(
            comissoes_historicas,
            ["Comissao_Calculada", "comissao_calculada", "COMISSAO_CALCULADA"]
        )
        col_cargo = self._encontrar_coluna(
            comissoes_historicas,
            ["Cargo", "cargo", "CARGO"]
        )
        col_id = self._encontrar_coluna(
            comissoes_historicas,
            ["id_colaborador", "Id_Colaborador", "ID_COLABORADOR"]
        )
        col_linha = self._encontrar_coluna(
            comissoes_historicas,
            ["Linha", "linha", "LINHA"]
        )
        
        if not col_colaborador or not col_comissao:
            self._erros.append(
                f"Processo {processo}: Colunas de colaborador/comissão não encontradas"
            )
            return []
        
        # Iterar sobre cada linha de comissão histórica
        for _, row in comissoes_historicas.iterrows():
            nome_colaborador = row.get(col_colaborador, "")
            comissao_original = float(row.get(col_comissao, 0) or 0)
            
            if comissao_original <= 0:
                continue
            
            # Calcular saldo negativo (valor absoluto do estorno)
            saldo_negativo_valor = comissao_original * fator
            
            # O valor salvo será NEGATIVO (débito)
            comissao_estorno = -saldo_negativo_valor
            
            # Montar registro de saldo negativo
            registro = {
                # Identificação
                "processo": processo,
                "numero_nf": numero_nf,
                "nome_colaborador": nome_colaborador,
                "cargo": row.get(col_cargo, "") if col_cargo else "",
                "id_colaborador": row.get(col_id, None) if col_id else None,
                "linha": row.get(col_linha, "") if col_linha else "",
                
                # Valores
                "valor_base": valor_devolvido,  # Valor devolvido como base
                "comissao_original": comissao_original,
                "fator_devolucao": fator,
                "comissao_calculada": comissao_estorno,  # NEGATIVO
                
                # Metadados
                "tipo_comissao": "DEVOLUCAO",
                "origem_correcao": "DEVOLUCAO",
                "processo_referencia": processo,
                "data_devolucao": data_devolucao,
                "mes_referencia": mes_apuracao,
                "ano_referencia": ano_apuracao,
                
                # Observação detalhada
                "observacao": (
                    f"Devolução {'parcial' if fator < 1.0 else 'total'} "
                    f"({fator*100:.1f}%) - NF {numero_nf} - "
                    f"Comissão original: R$ {comissao_original:.2f}"
                ),
            }
            
            saldos_negativos.append(registro)
            
            logger.debug(
                f"[DEVOLUCAO] Estorno calculado: {nome_colaborador} | "
                f"Original: R$ {comissao_original:.2f} | "
                f"Estorno: R$ {comissao_estorno:.2f}"
            )
        
        total_estorno = sum(s["comissao_calculada"] for s in saldos_negativos)
        logger.info(
            f"[DEVOLUCAO] Processo {processo}: "
            f"{len(saldos_negativos)} estornos calculados, "
            f"total: R$ {total_estorno:.2f}"
        )
        
        return saldos_negativos
    
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
    
    def get_erros(self) -> List[str]:
        """Retorna lista de erros encontrados."""
        return self._erros.copy()
    
    def get_avisos(self) -> List[str]:
        """Retorna lista de avisos encontrados."""
        return self._avisos.copy()
    
    def limpar_logs(self):
        """Limpa logs de erros e avisos."""
        self._erros = []
        self._avisos = []
