"""
Funções de formatação de valores para o PDF.
"""

from datetime import datetime
from typing import Union
import pandas as pd


def formatar_moeda(valor: Union[float, int, None]) -> str:
    """
    Formata um valor como moeda brasileira.
    
    Args:
        valor: Valor numérico a ser formatado
        
    Returns:
        String formatada como "R$ 1.234,56"
    """
    if valor is None or pd.isna(valor):
        return "R$ 0,00"
    
    try:
        valor_float = float(valor)
        # Formatar com separador de milhares e 2 casas decimais
        if valor_float < 0:
            return f"R$ -{abs(valor_float):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def formatar_percentual(valor: Union[float, int, None], casas: int = 2) -> str:
    """
    Formata um valor como percentual.
    
    Args:
        valor: Valor decimal (ex: 0.1234 para 12,34%)
        casas: Número de casas decimais (default: 2)
        
    Returns:
        String formatada como "12,34%"
    """
    if valor is None or pd.isna(valor):
        return "0,00%"
    
    try:
        valor_float = float(valor) * 100  # Converter para percentual
        formato = f"{{:,.{casas}f}}%"
        return formato.format(valor_float).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00%"


def formatar_data(data: Union[datetime, str, pd.Timestamp, None], formato: str = "%d/%m/%Y") -> str:
    """
    Formata uma data.
    
    Args:
        data: Data a ser formatada (datetime, string ou Timestamp)
        formato: Formato desejado (default: "%d/%m/%Y")
        
    Returns:
        String formatada como "15/09/2025"
    """
    if data is None or pd.isna(data):
        return "-"
    
    try:
        # Se já é datetime ou Timestamp
        if isinstance(data, (datetime, pd.Timestamp)):
            return data.strftime(formato)
        
        # Se é string, tentar converter
        if isinstance(data, str):
            # Tentar diferentes formatos comuns
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt = datetime.strptime(data, fmt)
                    return dt.strftime(formato)
                except ValueError:
                    continue
            return data  # Retornar original se não conseguir converter
        
        return str(data)
    except Exception:
        return "-"


def formatar_numero(valor: Union[float, int, None], casas: int = 2) -> str:
    """
    Formata um número com separadores de milhar e casas decimais.
    
    Args:
        valor: Valor numérico
        casas: Número de casas decimais (default: 2)
        
    Returns:
        String formatada como "1.234,56"
    """
    if valor is None or pd.isna(valor):
        return "0"
    
    try:
        valor_float = float(valor)
        formato = f"{{:,.{casas}f}}"
        return formato.format(valor_float).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0"


def formatar_codigo(codigo: Union[str, int, None], largura: int = 10) -> str:
    """
    Formata um código (processo, documento, etc) com largura fixa.
    
    Args:
        codigo: Código a ser formatado
        largura: Largura mínima (padding à esquerda)
        
    Returns:
        String formatada
    """
    if codigo is None or pd.isna(codigo):
        return "-"
    
    try:
        return str(codigo).strip().ljust(largura)
    except Exception:
        return "-"


def formatar_colaborador(nome: Union[str, None]) -> str:
    """
    Formata nome de colaborador.
    
    Args:
        nome: Nome do colaborador
        
    Returns:
        Nome formatado (capitalizado)
    """
    if nome is None or pd.isna(nome) or str(nome).strip() == "":
        return "-"
    
    try:
        nome_str = str(nome).strip()
        # Se está em MAIÚSCULAS, converter para Title Case
        if nome_str.isupper():
            return nome_str.title()
        return nome_str
    except Exception:
        return "-"


def formatar_boolean(valor: Union[bool, str, int, None]) -> str:
    """
    Formata um valor booleano como Sim/Não.
    
    Args:
        valor: Valor booleano ou string
        
    Returns:
        "Sim" ou "Não"
    """
    if valor is None or pd.isna(valor):
        return "Não"
    
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    
    if isinstance(valor, str):
        valor_upper = str(valor).upper().strip()
        if valor_upper in ["SIM", "TRUE", "1", "S", "YES", "Y"]:
            return "Sim"
    
    if isinstance(valor, (int, float)):
        return "Sim" if valor > 0 else "Não"
    
    return "Não"

