"""
Gerador da seção de cálculo de TCMP.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO, STYLE_FORMULA, STYLE_DESTAQUE
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import gerar_subtitulo_secao, gerar_legenda, gerar_paragrafo
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_tcmp(story, dados_processo_formatado: dict):
    """
    Gera seção com cálculo detalhado de TCMP.
    
    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(story, "5. CÁLCULO DE TCMP (Taxa de Comissão Média Ponderada)")
    
    tcmp_dados = dados_processo_formatado['tcmp_formatado']
    detalhes_itens = tcmp_dados.get('detalhes_itens', [])
    tcmp_por_colaborador = tcmp_dados.get('tcmp_por_colaborador', {})
    
    if not detalhes_itens or len(detalhes_itens) == 0:
        msg = Paragraph("TCMP não calculado para este processo.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, 'medio')
        return
    
    # Explicação
    gerar_paragrafo(
        story,
        "A TCMP é calculada como média ponderada das taxas de comissão de cada item do processo, "
        "usando o valor de cada item como peso. Para cada item, a taxa é determinada pela regra "
        "de comissão correspondente à sua classificação (Linha/Grupo/Subgrupo/Tipo) e cargo do colaborador."
    )
    adicionar_espacamento(story, 'pequeno')
    
    # Detalhamento por item
    gerar_paragrafo(story, "<b>5.1. Taxas por Item:</b>")
    adicionar_espacamento(story, 'pequeno')
    
    for idx, item in enumerate(detalhes_itens, 1):
        # Cabeçalho do item
        item_titulo = (
            f"<b>Item {idx}:</b> {item['linha']} / {item['grupo']} / "
            f"{item['subgrupo']} / {item['tipo_mercadoria']} - <b>{item['valor']}</b>"
        )
        gerar_paragrafo(story, item_titulo)
        adicionar_espacamento(story, 'pequeno')
        
        # Tabela de taxas por colaborador
        taxas_colab = item.get('taxas_colaboradores', [])
        if taxas_colab:
            dados_tabela = [['Colaborador', 'Cargo', 'Taxa Rateio', 'Fatia Cargo', 'Taxa Final']]
            
            for taxa in taxas_colab:
                dados_tabela.append([
                    taxa['nome'],
                    taxa['cargo'],
                    taxa['taxa_rateio'],
                    taxa['fatia_cargo'],
                    taxa['taxa_final']
                ])
            
            larguras = [140, 100, 80, 80, 80]
            tabela = TableBuilder.criar_tabela_simples(dados_tabela, larguras=larguras, repetir_header=False)
            if tabela:
                story.append(tabela)
        
        adicionar_espacamento(story, 'medio')
    
    # Fórmula da média ponderada
    gerar_paragrafo(story, "<b>5.2. Fórmula da Média Ponderada:</b>")
    adicionar_espacamento(story, 'pequeno')
    
    formula = Paragraph(
        "TCMP<sub>colaborador</sub> = Σ (Taxa<sub>item,colab</sub> × Valor<sub>item</sub>) / Σ Valor<sub>item</sub>",
        STYLE_FORMULA
    )
    story.append(formula)
    adicionar_espacamento(story, 'medio')
    
    # Resultado final
    gerar_paragrafo(story, "<b>5.3. TCMP Final por Colaborador:</b>")
    adicionar_espacamento(story, 'pequeno')
    
    if tcmp_por_colaborador:
        dados_tabela = [['Colaborador', 'TCMP']]
        
        for nome, dados in tcmp_por_colaborador.items():
            dados_tabela.append([
                nome,
                dados['tcmp']
            ])
        
        larguras = [300, 150]
        tabela = TableBuilder.criar_tabela_destaque(dados_tabela, larguras=larguras, repetir_header=False)
        if tabela:
            story.append(tabela)
    else:
        msg = Paragraph("TCMP não disponível.", STYLE_CORPO)
        story.append(msg)
    
    # Informação adicional
    adicionar_espacamento(story, 'pequeno')
    mes_faturamento = tcmp_dados.get('mes_faturamento', '-')
    info_texto = f"<b>Mês de Faturamento:</b> {mes_faturamento}"
    gerar_paragrafo(story, info_texto)
    
    # Legenda
    adicionar_espacamento(story, 'pequeno')
    gerar_legenda(
        story,
        "Fonte: CONFIG_COMISSAO.csv (regras de comissão por Linha/Grupo/Subgrupo/Tipo e Cargo)"
    )
    
    adicionar_espacamento(story, 'medio')

