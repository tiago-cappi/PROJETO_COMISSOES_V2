"""
Gerador da seção de resumo final do processo.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO, STYLE_DESTAQUE
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import gerar_subtitulo_secao, gerar_paragrafo
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_resumo(story, dados_processo_formatado: dict):
    """
    Gera seção de resumo consolidado do processo.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "8. RESUMO CONSOLIDADO")
    
    estatisticas = dados_processo_formatado['estatisticas']
    dados_gerais = dados_processo_formatado['dados_gerais_formatados']
    
    # Tabela de resumo geral
    dados_tabela = [
        ('Processo:', dados_gerais['processo_id']),
        ('Cliente:', dados_gerais['cliente']),
        ('Valor Total do Processo:', dados_gerais['valor_total']),
        ('', ''),
        ('<b>PAGAMENTOS</b>', ''),
        ('Total de Adiantamentos:', estatisticas['total_adiantamentos']),
        ('Total de Regulares:', estatisticas['total_regulares']),
        ('Total de Pagamentos:', estatisticas['total_pagamentos']),
        ('Número de Pagamentos:', str(estatisticas['num_pagamentos'])),
        ('', ''),
        ('<b>COMISSÕES</b>', ''),
        ('Comissões de Adiantamentos:', estatisticas['total_comissoes_adiant']),
        ('Comissões Regulares:', estatisticas['total_comissoes_reg']),
        ('Total de Comissões:', estatisticas['total_comissoes']),
        ('Número de Comissões:', str(estatisticas['num_comissoes'])),
        ('', ''),
        ('<b>OUTRAS INFORMAÇÕES</b>', ''),
        ('Número de Itens:', str(estatisticas['num_itens'])),
        ('Número de Colaboradores:', str(estatisticas['num_colaboradores'])),
    ]
    
    tabela = TableBuilder.criar_tabela_chave_valor(dados_tabela, largura_chave=200, largura_valor=250)
    if tabela:
        story.append(tabela)
    
    adicionar_espacamento(story, 'medio')
    
    # Resumo por colaborador
    comissoes = dados_processo_formatado['comissoes_formatadas']
    if comissoes:
        gerar_paragrafo(story, "<b>8.1. Resumo por Colaborador:</b>")
        adicionar_espacamento(story, 'pequeno')
        
        # Agrupar por colaborador
        resumo_colab = {}
        for com in comissoes:
            nome = com['colaborador']
            if nome not in resumo_colab:
                resumo_colab[nome] = {
                    'cargo': com['cargo'],
                    'tcmp': com['tcmp'],
                    'fcmp': com['fcmp'],
                    'total_adiant': 0.0,
                    'total_regular': 0.0,
                    'total_comissao': 0.0
                }
            
            if com['tipo'] == 'Adiantamento':
                resumo_colab[nome]['total_adiant'] += com['comissao_num']
            else:
                resumo_colab[nome]['total_regular'] += com['comissao_num']
            
            resumo_colab[nome]['total_comissao'] += com['comissao_num']
        
        # Tabela de resumo
        from auditoria_pdf.utils.formatters import formatar_moeda
        
        dados_tabela = [['Colaborador', 'Cargo', 'TCMP', 'FCMP', 'Total Comissões']]
        
        for nome, dados in resumo_colab.items():
            dados_tabela.append([
                nome,
                dados['cargo'],
                dados['tcmp'],
                dados['fcmp'],
                formatar_moeda(dados['total_comissao'])
            ])
        
        larguras = [140, 100, 70, 70, 120]
        tabela = TableBuilder.criar_tabela_destaque(dados_tabela, larguras=larguras)
        if tabela:
            story.append(tabela)
    
    adicionar_espacamento(story, 'grande')

