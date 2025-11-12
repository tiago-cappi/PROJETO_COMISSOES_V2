"""
Geradores de cabeçalhos e elementos estruturais do PDF.
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.units import inch
from datetime import datetime
from auditoria_pdf.styles.pdf_styles import (
    STYLE_TITULO_PRINCIPAL,
    STYLE_SUBTITULO_CAPA,
    STYLE_TITULO_SECAO,
    STYLE_CORPO,
    STYLE_LEGENDA,
    COR_PRIMARIA,
    COR_DESTAQUE
)
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento, adicionar_quebra_pagina


def gerar_capa(story, mes: int, ano: int, data_geracao: datetime):
    """
    Gera a capa do relatório de auditoria.
    
    Args:
        story: Lista de elementos do PDF
        mes: Mês de apuração
        ano: Ano de apuração
        data_geracao: Data de geração do relatório
    """
    # Espaço no topo
    story.append(Spacer(1, 2 * inch))
    
    # Título principal
    titulo = Paragraph(
        "RELATÓRIO DE AUDITORIA<br/>COMISSÕES POR RECEBIMENTO",
        STYLE_TITULO_PRINCIPAL
    )
    story.append(titulo)
    
    adicionar_espacamento(story, 'grande')
    
    # Período
    periodo = Paragraph(
        f"Período: {mes:02d}/{ano}",
        STYLE_SUBTITULO_CAPA
    )
    story.append(periodo)
    
    adicionar_espacamento(story, 'extra')
    
    # Informações adicionais
    info = Paragraph(
        f"Relatório gerado em: {data_geracao.strftime('%d/%m/%Y às %H:%M:%S')}",
        STYLE_CORPO
    )
    story.append(KeepTogether([info]))
    
    adicionar_espacamento(story, 'medio')
    
    # Descrição
    descricao = Paragraph(
        "Este relatório apresenta a auditoria detalhada dos cálculos de comissões "
        "por recebimento, incluindo o passo a passo do cálculo de TCMP (Taxa de "
        "Comissão Média Ponderada) e FCMP (Fator de Correção Médio Ponderado) "
        "para cada processo com pagamentos recebidos no período.",
        STYLE_CORPO
    )
    story.append(descricao)
    
    # Quebra de página
    adicionar_quebra_pagina(story)


def gerar_indice(story, processos: list):
    """
    Gera o índice do relatório.
    
    Args:
        story: Lista de elementos do PDF
        processos: Lista de dados dos processos
    """
    # Título do índice
    titulo = Paragraph("ÍNDICE DE PROCESSOS", STYLE_TITULO_SECAO)
    story.append(titulo)
    
    adicionar_espacamento(story, 'medio')
    
    if not processos or len(processos) == 0:
        msg = Paragraph(
            "Nenhum processo com comissões calculadas no período.",
            STYLE_CORPO
        )
        story.append(msg)
        adicionar_quebra_pagina(story)
        return
    
    # Lista de processos
    for idx, processo_dados in enumerate(processos, 1):
        dados_gerais = processo_dados.get('dados_gerais', {})
        processo_id = dados_gerais.get('processo_id', '-')
        cliente = dados_gerais.get('cliente', '-')
        valor_total = dados_gerais.get('valor_total', 'R$ 0,00')
        
        # Truncar nome do cliente se muito longo
        if len(cliente) > 50:
            cliente = cliente[:47] + "..."
        
        item_texto = f"{idx}. <b>Processo {processo_id}</b> - {cliente} - {valor_total}"
        item = Paragraph(item_texto, STYLE_CORPO)
        story.append(item)
        adicionar_espacamento(story, 'pequeno')
    
    # Quebra de página após índice
    adicionar_quebra_pagina(story)


def gerar_separador_processo(story, processo_id: str, numero: int = None):
    """
    Gera separador visual entre processos.
    
    Args:
        story: Lista de elementos do PDF
        processo_id: ID do processo
        numero: Número sequencial do processo (opcional)
    """
    # Quebra de página antes de novo processo
    adicionar_quebra_pagina(story)
    
    # Título do processo
    if numero:
        titulo_texto = f"PROCESSO {numero}: {processo_id}"
    else:
        titulo_texto = f"PROCESSO: {processo_id}"
    
    titulo = Paragraph(titulo_texto, STYLE_TITULO_SECAO)
    story.append(titulo)
    
    adicionar_espacamento(story, 'medio')


def gerar_subtitulo_secao(story, texto: str):
    """
    Gera um subtítulo de seção.
    
    Args:
        story: Lista de elementos do PDF
        texto: Texto do subtítulo
    """
    from auditoria_pdf.styles.pdf_styles import STYLE_SUBTITULO_SECAO
    
    subtitulo = Paragraph(texto, STYLE_SUBTITULO_SECAO)
    story.append(subtitulo)
    adicionar_espacamento(story, 'pequeno')


def gerar_paragrafo(story, texto: str, estilo=None):
    """
    Gera um parágrafo simples.
    
    Args:
        story: Lista de elementos do PDF
        texto: Texto do parágrafo
        estilo: Estilo do parágrafo (default: STYLE_CORPO)
    """
    if estilo is None:
        estilo = STYLE_CORPO
    
    paragrafo = Paragraph(texto, estilo)
    story.append(paragrafo)


def gerar_legenda(story, texto: str):
    """
    Gera uma legenda (texto pequeno em itálico).
    
    Args:
        story: Lista de elementos do PDF
        texto: Texto da legenda
    """
    legenda = Paragraph(texto, STYLE_LEGENDA)
    story.append(legenda)

