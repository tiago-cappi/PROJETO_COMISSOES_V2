"""
Gerador da seção de dados do processo.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import gerar_subtitulo_secao, gerar_legenda
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_dados_processo(story, dados_processo_formatado: dict):
    """
    Gera seção com dados gerais do processo.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "1. DADOS DO PROCESSO")
    
    dados_gerais = dados_processo_formatado['dados_gerais_formatados']
    
    # Tabela chave-valor com dados gerais
    dados_tabela = [
        ('Processo:', dados_gerais['processo_id']),
        ('Status:', dados_gerais['status']),
        ('Data de Emissão:', dados_gerais['dt_emissao']),
        ('Número NF:', dados_gerais['numero_nf']),
        ('Cliente:', dados_gerais['cliente']),
        ('Operação:', dados_gerais['operacao']),
        ('Valor Total:', dados_gerais['valor_total'])
    ]
    
    tabela = TableBuilder.criar_tabela_chave_valor(dados_tabela)
    if tabela:
        story.append(tabela)
    
    # Legenda
    adicionar_espacamento(story, 'pequeno')
    gerar_legenda(story, "Fonte: Análise Comercial (Analise_Comercial_Completa.csv)")
    
    adicionar_espacamento(story, 'medio')


def gerar_secao_itens_processo(story, dados_processo_formatado: dict):
    """
    Gera seção com itens do processo.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "2. ITENS DO PROCESSO")
    
    itens = dados_processo_formatado['itens_formatados']
    
    if not itens or len(itens) == 0:
        msg = Paragraph("Nenhum item encontrado.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, 'medio')
        return
    
    # Preparar dados para tabela
    dados_tabela = [
        ['Cód', 'Linha', 'Grupo', 'Subgrupo', 'Tipo', 'Valor']
    ]
    
    for item in itens:
        # Truncar textos longos
        codigo = item['codigo_produto'][:15] if len(item['codigo_produto']) > 15 else item['codigo_produto']
        linha = item['linha'][:12] if len(item['linha']) > 12 else item['linha']
        grupo = item['grupo'][:15] if len(item['grupo']) > 15 else item['grupo']
        subgrupo = item['subgrupo'][:15] if len(item['subgrupo']) > 15 else item['subgrupo']
        tipo = item['tipo_mercadoria'][:12] if len(item['tipo_mercadoria']) > 12 else item['tipo_mercadoria']
        
        dados_tabela.append([
            codigo,
            linha,
            grupo,
            subgrupo,
            tipo,
            item['valor']
        ])
    
    # Definir larguras das colunas (total ~500 pontos)
    larguras = [60, 80, 90, 90, 80, 100]
    
    tabela = TableBuilder.criar_tabela_listrada(dados_tabela, larguras=larguras)
    if tabela:
        story.append(tabela)
    
    # Legenda
    adicionar_espacamento(story, 'pequeno')
    gerar_legenda(story, "Fonte: Análise Comercial (Analise_Comercial_Completa.csv)")
    
    # Estatísticas
    adicionar_espacamento(story, 'pequeno')
    estatisticas = dados_processo_formatado['estatisticas']
    info_texto = f"<b>Total de itens:</b> {estatisticas['num_itens']}"
    info = Paragraph(info_texto, STYLE_CORPO)
    story.append(info)
    
    adicionar_espacamento(story, 'medio')

