"""
Utilitários gerais para geração de PDF.
"""

from reportlab.platypus import Spacer, PageBreak
from reportlab.lib.units import inch
from auditoria_pdf.styles.pdf_styles import (
    ESPACAMENTO_PEQUENO,
    ESPACAMENTO_MEDIO,
    ESPACAMENTO_GRANDE,
    ESPACAMENTO_EXTRA
)


def adicionar_espacamento(story, tamanho='medio'):
    """
    Adiciona espaçamento à story.
    
    Args:
        story: Lista de elementos do PDF
        tamanho: 'pequeno', 'medio', 'grande', ou 'extra'
    """
    espacamentos = {
        'pequeno': ESPACAMENTO_PEQUENO,
        'medio': ESPACAMENTO_MEDIO,
        'grande': ESPACAMENTO_GRANDE,
        'extra': ESPACAMENTO_EXTRA
    }
    
    altura = espacamentos.get(tamanho, ESPACAMENTO_MEDIO)
    story.append(Spacer(1, altura))


def adicionar_quebra_pagina(story):
    """
    Adiciona quebra de página à story.
    
    Args:
        story: Lista de elementos do PDF
    """
    story.append(PageBreak())


def truncar_texto(texto: str, max_chars: int = 50, sufixo: str = "...") -> str:
    """
    Trunca um texto se exceder o tamanho máximo.
    
    Args:
        texto: Texto a truncar
        max_chars: Número máximo de caracteres
        sufixo: Sufixo a adicionar quando truncado
        
    Returns:
        Texto truncado
    """
    if not texto:
        return ""
    
    texto_str = str(texto)
    if len(texto_str) <= max_chars:
        return texto_str
    
    return texto_str[:max_chars - len(sufixo)] + sufixo


def sanitizar_texto(texto: str) -> str:
    """
    Remove caracteres especiais que podem causar problemas no PDF.
    
    Args:
        texto: Texto a sanitizar
        
    Returns:
        Texto sanitizado
    """
    if not texto:
        return ""
    
    texto_str = str(texto)
    
    # Substituir caracteres problemáticos
    substituicoes = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '\x00': '',  # Null character
        '\ufeff': '',  # BOM
    }
    
    for original, substituto in substituicoes.items():
        texto_str = texto_str.replace(original, substituto)
    
    return texto_str

