"""
Gerador da seção de colaboradores identificados.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import gerar_subtitulo_secao, gerar_legenda
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_colaboradores(story, dados_processo_formatado: dict):
    """
    Gera seção com colaboradores identificados para o processo.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "4. COLABORADORES IDENTIFICADOS")
    
    colaboradores = dados_processo_formatado['colaboradores_formatados']
    
    if not colaboradores or len(colaboradores) == 0:
        msg = Paragraph("Nenhum colaborador identificado.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, 'medio')
        return
    
    # Separar por tipo
    operacionais = [c for c in colaboradores if c['tipo'] == 'operacional']
    gestao = [c for c in colaboradores if c['tipo'] == 'gestao']
    
    # Tabela de colaboradores operacionais
    if operacionais:
        paragrafo = Paragraph("<b>Colaboradores Operacionais:</b>", STYLE_CORPO)
        story.append(paragrafo)
        adicionar_espacamento(story, 'pequeno')
        
        dados_tabela = [['Nome', 'Cargo', 'Origem']]
        for colab in operacionais:
            dados_tabela.append([
                colab['nome'],
                colab['cargo'],
                'Análise Comercial'
            ])
        
        larguras = [200, 150, 150]
        tabela = TableBuilder.criar_tabela_listrada(dados_tabela, larguras=larguras)
        if tabela:
            story.append(tabela)
        
        adicionar_espacamento(story, 'medio')
    
    # Tabela de colaboradores de gestão
    if gestao:
        paragrafo = Paragraph("<b>Colaboradores de Gestão:</b>", STYLE_CORPO)
        story.append(paragrafo)
        adicionar_espacamento(story, 'pequeno')
        
        dados_tabela = [['Nome', 'Cargo', 'Origem']]
        for colab in gestao:
            dados_tabela.append([
                colab['nome'],
                colab['cargo'],
                'ATRIBUICOES.csv'
            ])
        
        larguras = [200, 150, 150]
        tabela = TableBuilder.criar_tabela_listrada(dados_tabela, larguras=larguras)
        if tabela:
            story.append(tabela)
        
        adicionar_espacamento(story, 'medio')
    
    # Legenda
    gerar_legenda(
        story,
        "Colaboradores operacionais: Consultor Interno e Representante-pedido da Análise Comercial. "
        "Colaboradores de gestão: Identificados via ATRIBUICOES.csv por Linha/Grupo/Subgrupo/Tipo."
    )
    
    # Estatísticas
    adicionar_espacamento(story, 'pequeno')
    estatisticas = dados_processo_formatado['estatisticas']
    info_texto = (
        f"<b>Total de colaboradores:</b> {estatisticas['num_colaboradores']} "
        f"({len(operacionais)} operacionais + {len(gestao)} gestão)"
    )
    info = Paragraph(info_texto, STYLE_CORPO)
    story.append(info)
    
    adicionar_espacamento(story, 'medio')

