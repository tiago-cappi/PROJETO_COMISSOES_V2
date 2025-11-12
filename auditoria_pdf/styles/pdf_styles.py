"""
Estilos, cores e constantes de layout para PDF.
"""

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.units import inch

# ============================================================================
# CORES
# ============================================================================

COR_PRIMARIA = HexColor('#2C3E50')      # Azul escuro
COR_SECUNDARIA = HexColor('#34495E')    # Azul acinzentado
COR_DESTAQUE = HexColor('#3498DB')      # Azul claro
COR_SUCESSO = HexColor('#27AE60')       # Verde
COR_ALERTA = HexColor('#F39C12')        # Laranja
COR_ERRO = HexColor('#E74C3C')          # Vermelho
COR_INFO = HexColor('#5DADE2')          # Azul claro info
COR_CINZA_CLARO = HexColor('#ECF0F1')   # Cinza muito claro
COR_CINZA_MEDIO = HexColor('#95A5A6')   # Cinza médio
COR_CINZA_ESCURO = HexColor('#7F8C8D')  # Cinza escuro

# ============================================================================
# CONSTANTES DE LAYOUT
# ============================================================================

MARGEM_SUPERIOR = 0.75 * inch
MARGEM_INFERIOR = 0.75 * inch
MARGEM_ESQUERDA = 0.75 * inch
MARGEM_DIREITA = 0.75 * inch

ESPACAMENTO_PEQUENO = 0.1 * inch
ESPACAMENTO_MEDIO = 0.2 * inch
ESPACAMENTO_GRANDE = 0.3 * inch
ESPACAMENTO_EXTRA = 0.5 * inch

# ============================================================================
# ESTILOS DE TEXTO
# ============================================================================

# Obter estilos base do ReportLab
_base_styles = getSampleStyleSheet()

# Estilo: Título Principal (Capa)
STYLE_TITULO_PRINCIPAL = ParagraphStyle(
    'TituloPrincipal',
    parent=_base_styles['Heading1'],
    fontSize=24,
    textColor=COR_PRIMARIA,
    alignment=TA_CENTER,
    spaceAfter=20,
    fontName='Helvetica-Bold',
    leading=28
)

# Estilo: Subtítulo (Capa)
STYLE_SUBTITULO_CAPA = ParagraphStyle(
    'SubtituloCapa',
    parent=_base_styles['Heading2'],
    fontSize=16,
    textColor=COR_SECUNDARIA,
    alignment=TA_CENTER,
    spaceAfter=12,
    fontName='Helvetica',
    leading=20
)

# Estilo: Título de Seção
STYLE_TITULO_SECAO = ParagraphStyle(
    'TituloSecao',
    parent=_base_styles['Heading1'],
    fontSize=18,
    textColor=COR_PRIMARIA,
    alignment=TA_LEFT,
    spaceAfter=16,
    spaceBefore=20,
    fontName='Helvetica-Bold',
    leading=22,
    borderPadding=(5, 5, 5, 5),
    borderColor=COR_PRIMARIA,
    borderWidth=0,
    leftIndent=0
)

# Estilo: Subtítulo de Seção
STYLE_SUBTITULO_SECAO = ParagraphStyle(
    'SubtituloSecao',
    parent=_base_styles['Heading2'],
    fontSize=14,
    textColor=COR_SECUNDARIA,
    alignment=TA_LEFT,
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold',
    leading=17
)

# Estilo: Texto Corpo Normal
STYLE_CORPO = ParagraphStyle(
    'Corpo',
    parent=_base_styles['Normal'],
    fontSize=10,
    textColor=black,
    alignment=TA_LEFT,
    spaceAfter=6,
    fontName='Helvetica',
    leading=14
)

# Estilo: Texto Corpo Justificado
STYLE_CORPO_JUSTIFICADO = ParagraphStyle(
    'CorpoJustificado',
    parent=STYLE_CORPO,
    alignment=TA_JUSTIFY
)

# Estilo: Texto Monoespaçado (para números, códigos)
STYLE_MONO = ParagraphStyle(
    'Monoespaco',
    parent=_base_styles['Code'],
    fontSize=9,
    textColor=COR_CINZA_ESCURO,
    alignment=TA_LEFT,
    fontName='Courier',
    leading=11,
    leftIndent=10,
    rightIndent=10
)

# Estilo: Destaque (para valores importantes)
STYLE_DESTAQUE = ParagraphStyle(
    'Destaque',
    parent=STYLE_CORPO,
    fontSize=12,
    textColor=COR_DESTAQUE,
    fontName='Helvetica-Bold',
    leading=16
)

# Estilo: Sucesso (para valores positivos)
STYLE_SUCESSO = ParagraphStyle(
    'Sucesso',
    parent=STYLE_CORPO,
    fontSize=11,
    textColor=COR_SUCESSO,
    fontName='Helvetica-Bold'
)

# Estilo: Alerta
STYLE_ALERTA = ParagraphStyle(
    'Alerta',
    parent=STYLE_CORPO,
    fontSize=11,
    textColor=COR_ALERTA,
    fontName='Helvetica-Bold'
)

# Estilo: Erro
STYLE_ERRO = ParagraphStyle(
    'Erro',
    parent=STYLE_CORPO,
    fontSize=11,
    textColor=COR_ERRO,
    fontName='Helvetica-Bold'
)

# Estilo: Item de Lista
STYLE_LISTA = ParagraphStyle(
    'ItemLista',
    parent=STYLE_CORPO,
    leftIndent=20,
    bulletIndent=10,
    spaceAfter=4
)

# Estilo: Fórmula (texto matemático)
STYLE_FORMULA = ParagraphStyle(
    'Formula',
    parent=STYLE_MONO,
    fontSize=10,
    textColor=COR_SECUNDARIA,
    alignment=TA_CENTER,
    leftIndent=30,
    rightIndent=30,
    spaceBefore=8,
    spaceAfter=8,
    backColor=COR_CINZA_CLARO
)

# Estilo: Legenda (para tabelas e figuras)
STYLE_LEGENDA = ParagraphStyle(
    'Legenda',
    parent=STYLE_CORPO,
    fontSize=8,
    textColor=COR_CINZA_MEDIO,
    alignment=TA_CENTER,
    spaceAfter=10,
    fontName='Helvetica-Oblique'
)

# ============================================================================
# ESTILOS DE TABELA (configs base)
# ============================================================================

# Estilo padrão para tabelas
TABLE_STYLE_DEFAULT = [
    ('BACKGROUND', (0, 0), (-1, 0), COR_PRIMARIA),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('TOPPADDING', (0, 0), (-1, 0), 8),
    ('BACKGROUND', (0, 1), (-1, -1), white),
    ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA_MEDIO),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('TOPPADDING', (0, 1), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
]

# Estilo para tabelas listradas (alternando cores)
TABLE_STYLE_LISTRADA = [
    ('BACKGROUND', (0, 0), (-1, 0), COR_PRIMARIA),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('TOPPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA_MEDIO),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('TOPPADDING', (0, 1), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    # Linhas pares com fundo cinza claro
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COR_CINZA_CLARO]),
]

# Estilo para tabelas de destaque (com borda destacada)
TABLE_STYLE_DESTAQUE = [
    ('BACKGROUND', (0, 0), (-1, 0), COR_DESTAQUE),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('TOPPADDING', (0, 0), (-1, 0), 10),
    ('BACKGROUND', (0, 1), (-1, -1), white),
    ('BOX', (0, 0), (-1, -1), 2, COR_DESTAQUE),
    ('GRID', (0, 1), (-1, -1), 0.5, COR_CINZA_MEDIO),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('TOPPADDING', (0, 1), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
]

