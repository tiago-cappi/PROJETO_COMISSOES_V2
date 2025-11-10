"""
Módulo de logging e validação.
Contém a classe ValidationLogger para gerenciar logs de validação do sistema.
"""

from typing import Dict, List, Optional


class ValidationLogger:
    """
    Classe para gerenciar logs de validação do sistema de cálculo de comissões.
    
    Mantém uma lista de entradas de log, cada uma contendo nível, mensagem e contexto.
    Compatível com a interface anterior que usava uma lista de dicionários.
    """
    
    def __init__(self):
        """Inicializa o logger com uma lista vazia de logs."""
        self.validation_log: List[Dict[str, str]] = []
    
    def log(self, nivel: str, mensagem: str, contexto: Optional[Dict] = None):
        """
        Adiciona uma entrada ao log de validação.
        
        Args:
            nivel: Nível do log (ex: "INFO", "AVISO", "ERRO")
            mensagem: Mensagem descritiva do log
            contexto: Dicionário opcional com informações adicionais de contexto
        """
        self.validation_log.append(
            {"Nível": nivel, "Mensagem": mensagem, "Contexto": str(contexto) if contexto else ""}
        )
    
    def info(self, mensagem: str, contexto: Optional[Dict] = None):
        """
        Adiciona um log de nível INFO.
        
        Args:
            mensagem: Mensagem descritiva
            contexto: Dicionário opcional com informações adicionais
        """
        self.log("INFO", mensagem, contexto)
    
    def aviso(self, mensagem: str, contexto: Optional[Dict] = None):
        """
        Adiciona um log de nível AVISO.
        
        Args:
            mensagem: Mensagem descritiva
            contexto: Dicionário opcional com informações adicionais
        """
        self.log("AVISO", mensagem, contexto)
    
    def erro(self, mensagem: str, contexto: Optional[Dict] = None):
        """
        Adiciona um log de nível ERRO.
        
        Args:
            mensagem: Mensagem descritiva
            contexto: Dicionário opcional com informações adicionais
        """
        self.log("ERRO", mensagem, contexto)
    
    def get_logs(self) -> List[Dict[str, str]]:
        """
        Retorna a lista completa de logs de validação.
        
        Returns:
            Lista de dicionários, cada um contendo "Nível", "Mensagem" e "Contexto"
        """
        return self.validation_log.copy()
    
    def clear(self):
        """Limpa todos os logs armazenados."""
        self.validation_log.clear()
    
    def __len__(self) -> int:
        """Retorna o número de logs armazenados."""
        return len(self.validation_log)

