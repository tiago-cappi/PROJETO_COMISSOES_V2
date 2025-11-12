"""
Calcula comissões para adiantamentos e pagamentos regulares.
"""

from typing import Dict, List
from datetime import datetime


class ComissaoCalculator:
    """
    Calcula comissões para adiantamentos e pagamentos regulares.
    """
    
    def __init__(self):
        """Inicializa o calculador de comissões."""
        pass
    
    def calcular_adiantamento(
        self,
        processo: str,
        valor: float,
        tcmp_dict: Dict[str, float],
        documento: str,
        data_pagamento: datetime = None
    ) -> List[Dict]:
        """
        Calcula comissões para um adiantamento (COT).
        
        Para adiantamentos, o FC é sempre 1.0, então:
        comissao = valor * TCMP * 1.0
        
        Args:
            processo: ID do processo
            valor: Valor do adiantamento
            tcmp_dict: Dict {nome_colaborador: tcmp}
            documento: Documento original (ex: "COT123456")
            data_pagamento: Data do pagamento
        
        Returns:
            Lista de dicts com comissões calculadas
        """
        comissoes = []
        
        for colaborador, tcmp in tcmp_dict.items():
            if tcmp <= 0:
                continue
            
            # FC sempre 1.0 para adiantamentos
            fc = 1.0
            comissao = valor * tcmp * fc
            
            comissoes.append({
                'processo': str(processo).strip(),
                'documento': str(documento).strip(),
                'data_pagamento': data_pagamento,
                'valor_pago': valor,
                'nome_colaborador': colaborador,
                'cargo': None,  # Será preenchido depois se necessário
                'tcmp': tcmp,
                'fc': fc,
                'fcmp': None,  # Não aplicável para adiantamentos
                'comissao_calculada': comissao,
                'tipo_lancamento': 'Adiantamento',
                'mes_calculo': None  # Será preenchido depois
            })
        
        return comissoes
    
    def calcular_regular(
        self,
        processo: str,
        valor: float,
        tcmp_dict: Dict[str, float],
        fcmp_dict: Dict[str, float],
        documento: str,
        data_pagamento: datetime = None,
        mes_faturamento: str = None
    ) -> List[Dict]:
        """
        Calcula comissões para um pagamento regular (pós-faturamento).
        
        Para pagamentos regulares, usa TCMP e FCMP salvos no estado:
        comissao = valor * TCMP * FCMP
        
        Args:
            processo: ID do processo
            valor: Valor do pagamento regular
            tcmp_dict: Dict {nome_colaborador: tcmp}
            fcmp_dict: Dict {nome_colaborador: fcmp}
            documento: Documento original
            data_pagamento: Data do pagamento
            mes_faturamento: Mês/ano em que o processo foi faturado (ex: "09/2025")
        
        Returns:
            Lista de dicts com comissões calculadas
        """
        print(f"[RECEBIMENTO] [COMISSAO_CALC] calcular_regular chamado:")
        print(f"[RECEBIMENTO] [COMISSAO_CALC]   - processo={processo}")
        print(f"[RECEBIMENTO] [COMISSAO_CALC]   - valor={valor}")
        print(f"[RECEBIMENTO] [COMISSAO_CALC]   - tcmp_dict={tcmp_dict}")
        print(f"[RECEBIMENTO] [COMISSAO_CALC]   - fcmp_dict={fcmp_dict}")
        print(f"[RECEBIMENTO] [COMISSAO_CALC]   - mes_faturamento={mes_faturamento}")
        
        comissoes = []
        
        for colaborador, tcmp in tcmp_dict.items():
            print(f"[RECEBIMENTO] [COMISSAO_CALC] Processando colaborador: {colaborador}, tcmp={tcmp}")
            
            if tcmp <= 0:
                print(f"[RECEBIMENTO] [COMISSAO_CALC]   - TCMP <= 0. Pulando...")
                continue
            
            # Obter FCMP do colaborador
            fcmp = fcmp_dict.get(colaborador, 0.0)
            print(f"[RECEBIMENTO] [COMISSAO_CALC]   - FCMP obtido: {fcmp}")
            
            if fcmp <= 0:
                # Se FCMP não estiver disponível, usar 1.0 como fallback
                print(f"[RECEBIMENTO] [COMISSAO_CALC]   - FCMP <= 0. Usando fallback 1.0")
                fcmp = 1.0
            
            comissao = valor * tcmp * fcmp
            print(f"[RECEBIMENTO] [COMISSAO_CALC]   - Comissão calculada: {valor} * {tcmp} * {fcmp} = {comissao}")
            
            comissoes.append({
                'processo': str(processo).strip(),
                'documento': str(documento).strip(),
                'data_pagamento': data_pagamento,
                'valor_pago': valor,
                'nome_colaborador': colaborador,
                'cargo': None,  # Será preenchido depois se necessário
                'tcmp': tcmp,
                'fc': None,  # Não aplicável para pagamentos regulares
                'fcmp': fcmp,
                'comissao_calculada': comissao,
                'tipo_lancamento': 'Pagamento Regular',
                'mes_faturamento': mes_faturamento,
                'mes_calculo': None  # Será preenchido depois
            })
            print(f"[RECEBIMENTO] [COMISSAO_CALC]   - Comissão adicionada à lista")
        
        print(f"[RECEBIMENTO] [COMISSAO_CALC] Total de comissões geradas: {len(comissoes)}")
        return comissoes

