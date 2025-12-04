"""
Exceções customizadas para o módulo de recebimento.
"""


class RecebimentoError(Exception):
    """Classe base para exceções do módulo de recebimento."""
    pass


class InconsistenciaAdiantamentoError(RecebimentoError):
    """
    Erro lançado quando um pagamento COT (adiantamento) está 
    associado a um processo que já está FATURADO na Análise Comercial.
    
    Regra de negócio: Um adiantamento (COT) só pode existir para 
    processos que ainda NÃO foram faturados.
    """
    
    def __init__(self, documento: str, processo: str, status_processo: str):
        self.documento = documento
        self.processo = processo
        self.status_processo = status_processo
        self.message = (
            f"Inconsistência de dados detectada: O documento '{documento}' é um adiantamento (COT), "
            f"mas o processo '{processo}' já possui Status='{status_processo}' na Análise Comercial. "
            f"Adiantamentos só podem existir para processos que ainda não foram faturados."
        )
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Retorna representação em dicionário para resposta HTTP."""
        return {
            "error_type": "InconsistenciaAdiantamentoError",
            "documento": self.documento,
            "processo": self.processo,
            "status_processo": self.status_processo,
            "message": self.message
        }
