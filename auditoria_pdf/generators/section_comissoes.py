"""
Gerador da seção de comissões calculadas.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO, STYLE_FORMULA
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import gerar_subtitulo_secao, gerar_legenda, gerar_paragrafo
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_comissoes(story, dados_processo_formatado: dict):
    """
    Gera seção com comissões calculadas.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "7. COMISSÕES CALCULADAS")
    
    comissoes = dados_processo_formatado['comissoes_formatadas']
    
    if not comissoes or len(comissoes) == 0:
        msg = Paragraph("Nenhuma comissão calculada.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, 'medio')
        return
    
    # Separar por tipo
    adiantamentos = [c for c in comissoes if c['tipo'] == 'Adiantamento']
    regulares = [c for c in comissoes if c['tipo'] == 'Regular']
    
    # Fórmulas
    gerar_paragrafo(story, "<b>7.1. Fórmulas Aplicadas:</b>")
    adicionar_espacamento(story, 'pequeno')
    
    formula_adiant = Paragraph(
        "<b>Adiantamento:</b> Comissão = Valor Pago × TCMP × 1,0",
        STYLE_CORPO
    )
    story.append(formula_adiant)
    
    formula_regular = Paragraph(
        "<b>Regular:</b> Comissão = Valor Pago × TCMP × FCMP",
        STYLE_CORPO
    )
    story.append(formula_regular)
    
    adicionar_espacamento(story, 'medio')
    
    # Comissões de adiantamentos
    if adiantamentos:
        gerar_paragrafo(story, "<b>7.2. Comissões de Adiantamentos:</b>")
        adicionar_espacamento(story, 'pequeno')
        
        dados_tabela = [['Colaborador', 'Cargo', 'TCMP', 'Valor Pago', 'Comissão']]
        
        for com in adiantamentos:
            dados_tabela.append([
                com['colaborador'],
                com['cargo'],
                com['tcmp'],
                com['valor_pago'],
                com['comissao']
            ])
        
        # Linha de total
        total_adiant = sum(c['comissao_num'] for c in adiantamentos)
        total_valor_adiant = sum(c['valor_pago_num'] for c in adiantamentos)
        from auditoria_pdf.utils.formatters import formatar_moeda
        
        dados_tabela.append([
            '<b>TOTAL</b>',
            '',
            '',
            f"<b>{formatar_moeda(total_valor_adiant)}</b>",
            f"<b>{formatar_moeda(total_adiant)}</b>"
        ])
        
        larguras = [140, 100, 70, 100, 100]
        tabela = TableBuilder.criar_tabela_resumo(
            dados_tabela,
            larguras=larguras,
            linhas_destaque=[len(dados_tabela) - 1]
        )
        if tabela:
            story.append(tabela)
        
        adicionar_espacamento(story, 'medio')
    
    # Comissões regulares
    if regulares:
        gerar_paragrafo(story, "<b>7.3. Comissões Regulares:</b>")
        adicionar_espacamento(story, 'pequeno')
        
        dados_tabela = [['Colaborador', 'Cargo', 'TCMP', 'FCMP', 'Valor Pago', 'Comissão']]
        
        for com in regulares:
            dados_tabela.append([
                com['colaborador'],
                com['cargo'],
                com['tcmp'],
                com['fcmp'],
                com['valor_pago'],
                com['comissao']
            ])
        
        # Linha de total
        total_regular = sum(c['comissao_num'] for c in regulares)
        total_valor_regular = sum(c['valor_pago_num'] for c in regulares)
        from auditoria_pdf.utils.formatters import formatar_moeda
        
        dados_tabela.append([
            '<b>TOTAL</b>',
            '',
            '',
            '',
            f"<b>{formatar_moeda(total_valor_regular)}</b>",
            f"<b>{formatar_moeda(total_regular)}</b>"
        ])
        
        larguras = [110, 90, 60, 60, 90, 90]
        tabela = TableBuilder.criar_tabela_resumo(
            dados_tabela,
            larguras=larguras,
            linhas_destaque=[len(dados_tabela) - 1]
        )
        if tabela:
            story.append(tabela)
        
        adicionar_espacamento(story, 'medio')
    
    # Total geral
    estatisticas = dados_processo_formatado['estatisticas']
    gerar_paragrafo(
        story,
        f"<b>TOTAL GERAL DE COMISSÕES:</b> {estatisticas['total_comissoes']}"
    )
    
    # Legenda
    adicionar_espacamento(story, 'pequeno')
    gerar_legenda(story, "Fonte: Estado (aba ESTADO do arquivo Comissoes_Recebimento_MM_AAAA.xlsx)")
    
    adicionar_espacamento(story, 'medio')

