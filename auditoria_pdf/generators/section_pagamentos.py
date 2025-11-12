"""
Gerador da seção de pagamentos.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import gerar_subtitulo_secao, gerar_legenda
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_pagamentos(story, dados_processo_formatado: dict):
    """
    Gera seção com pagamentos do processo.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "3. PAGAMENTOS RECEBIDOS")
    
    pagamentos = dados_processo_formatado['pagamentos_formatados']
    
    if not pagamentos or len(pagamentos) == 0:
        msg = Paragraph("Nenhum pagamento registrado.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, 'medio')
        return
    
    # Preparar dados para tabela
    dados_tabela = [
        ['Tipo', 'Documento', 'Data Baixa', 'Valor']
    ]
    
    for pag in pagamentos:
        dados_tabela.append([
            pag['tipo'],
            pag['documento'],
            pag['data'],
            pag['valor']
        ])
    
    # Linha de total
    estatisticas = dados_processo_formatado['estatisticas']
    dados_tabela.append([
        '<b>TOTAL</b>',
        '',
        '',
        f"<b>{estatisticas['total_pagamentos']}</b>"
    ])
    
    # Definir larguras das colunas
    larguras = [100, 120, 100, 120]
    
    # Criar tabela com última linha destacada
    tabela = TableBuilder.criar_tabela_resumo(
        dados_tabela,
        larguras=larguras,
        linhas_destaque=[len(dados_tabela) - 1]  # Última linha (total)
    )
    
    if tabela:
        story.append(tabela)
    
    # Legenda
    adicionar_espacamento(story, 'pequeno')
    gerar_legenda(story, "Fonte: Análise Financeira (Análise Financeira.xlsx) - Tipo de Baixa = 'B'")
    
    # Estatísticas detalhadas
    adicionar_espacamento(story, 'pequeno')
    info_texto = (
        f"<b>Adiantamentos:</b> {estatisticas['total_adiantamentos']} | "
        f"<b>Regulares:</b> {estatisticas['total_regulares']} | "
        f"<b>Total de pagamentos:</b> {estatisticas['num_pagamentos']}"
    )
    info = Paragraph(info_texto, STYLE_CORPO)
    story.append(info)
    
    adicionar_espacamento(story, 'medio')

