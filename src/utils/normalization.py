"""
Módulo de normalização de dados.
Contém funções para normalização de texto e cálculos de atingimento de metas.
"""

import pandas as pd
import unicodedata


def normalize_text(s):
    """
    Normaliza uma string removendo acentos, BOM e espaços extras.
    
    Args:
        s: String ou valor a ser normalizado (pode ser NaN)
    
    Returns:
        String normalizada em maiúsculas, sem acentos e sem espaços extras.
        Retorna string vazia se o valor for NaN.
    
    Exemplos:
        >>> normalize_text("José da Silva")
        'JOSE DA SILVA'
        >>> normalize_text("\ufeffTexto com BOM")
        'TEXTO COM BOM'
        >>> normalize_text(pd.NA)
        ''
    """
    if pd.isna(s):
        return ""
    s = str(s)
    # Remover BOM (Byte Order Mark) se presente
    s = s.replace("\ufeff", "")
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
    return " ".join(s.strip().upper().split())


def calcular_atingimento(realizado, meta):
    """
    Calcula o atingimento de uma meta com tratamento correto para meta zero.
    
    A lógica é:
    - Se meta == 0 e realizado > 0: retorna 1.0 (superou a meta)
    - Se meta == 0 e realizado == 0: retorna 0.0
    - Se meta > 0: retorna realizado / meta
    
    Args:
        realizado: Valor realizado (pode ser None, NaN ou número)
        meta: Valor da meta (pode ser None, NaN ou número)
    
    Returns:
        Float representando o atingimento (0.0 a infinito, teoricamente).
        Retorna 0.0 em caso de erro.
    
    Exemplos:
        >>> calcular_atingimento(100, 50)
        2.0
        >>> calcular_atingimento(0, 0)
        0.0
        >>> calcular_atingimento(10, 0)
        1.0
        >>> calcular_atingimento(None, 100)
        0.0
    """
    try:
        realizado = float(realizado) if realizado is not None else 0.0
        meta = float(meta) if meta is not None else 0.0

        if meta == 0:
            # Meta zero: se realizou algo, atingiu 100%; se não, 0%
            return 1.0 if realizado > 0 else 0.0
        else:
            # Meta positiva: calcula proporção normal
            return realizado / meta
    except Exception:
        return 0.0

