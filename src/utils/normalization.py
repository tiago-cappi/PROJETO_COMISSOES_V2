"""
Módulo de normalização de dados.
Contém funções para normalização de texto e cálculos de atingimento de metas.
"""

import math

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
    Calcula o atingimento de uma meta com validação estrita de entradas.

    Comportamento fail-fast: entradas inválidas levantam ValueError imediatamente,
    abortando o cálculo de comissões. Strings numéricas (ex: "90000") são aceitas.

    Regras de validação:
    - realizado deve ser > 0 (zero é inválido — ausência de faturamento real)
    - realizado não pode ser negativo
    - meta pode ser zero, mas não pode ser negativa
    - Entradas não-numéricas (exceto strings numéricas) levantam ValueError
    - Se meta == 0 e realizado > 0: retorna 1.0 (meta atingida por definição)
    - Se meta > 0: retorna realizado / meta

    Args:
        realizado: Valor realizado. Aceita int, float ou string numérica. Deve ser > 0.
        meta: Valor da meta. Aceita int, float ou string numérica. Deve ser >= 0.

    Returns:
        Float representando o atingimento proporcional (ex: 0.9, 1.2, 1.0).

    Raises:
        ValueError: Se realizado ou meta forem inválidos (não numéricos, realizado <= 0,
                    meta negativa). O erro inclui descrição do problema para diagnóstico.

    Exemplos:
        >>> calcular_atingimento(90000, 100000)
        0.9
        >>> calcular_atingimento(50000, 0)
        1.0
        >>> calcular_atingimento("90000", "100000")
        0.9
        >>> calcular_atingimento(0, 100000)
        ValueError: Valor 'realizado' não pode ser zero...
    """
    # --- Conversão e validação de 'realizado' ---
    try:
        realizado = float(realizado)
    except (TypeError, ValueError):
        raise ValueError(
            f"Valor inválido para 'realizado': {realizado!r}. "
            f"Deve ser um número ou string numérica. Cálculo de comissões abortado."
        )

    if math.isnan(realizado):
        raise ValueError(
            f"Valor inválido para 'realizado': NaN não é um valor numérico aceito. "
            f"Cálculo de comissões abortado."
        )

    if realizado == 0:
        raise ValueError(
            f"Valor 'realizado' não pode ser zero. "
            f"Um realizado igual a zero indica ausência de faturamento válido. "
            f"Cálculo de comissões abortado."
        )

    if realizado < 0:
        raise ValueError(
            f"Valor 'realizado' não pode ser negativo: {realizado}. "
            f"Cálculo de comissões abortado."
        )

    # --- Conversão e validação de 'meta' ---
    try:
        meta = float(meta)
    except (TypeError, ValueError):
        raise ValueError(
            f"Valor inválido para 'meta': {meta!r}. "
            f"Deve ser um número ou string numérica. Cálculo de comissões abortado."
        )

    if math.isnan(meta):
        raise ValueError(
            f"Valor inválido para 'meta': NaN não é um valor numérico aceito. "
            f"Cálculo de comissões abortado."
        )

    if meta < 0:
        raise ValueError(
            f"Valor 'meta' não pode ser negativo: {meta}. "
            f"Cálculo de comissões abortado."
        )

    # --- Cálculo do atingimento ---
    if meta == 0:
        # Meta zero com realizado positivo = meta atingida por definição
        return 1.0

    return realizado / meta

