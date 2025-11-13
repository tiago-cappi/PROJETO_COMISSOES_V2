"""
Gerador da seção de cálculo de TCMP.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO, STYLE_FORMULA, STYLE_DESTAQUE
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import (
    gerar_subtitulo_secao,
    gerar_legenda,
    gerar_paragrafo,
)
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_tcmp(story, dados_processo_formatado: dict):
    """
    Gera seção com cálculo detalhado de TCMP.

    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    gerar_subtitulo_secao(
        story, "5. CÁLCULO DE TCMP (Taxa de Comissão Média Ponderada)"
    )

    tcmp_dados = dados_processo_formatado["tcmp_formatado"]
    detalhes_itens = tcmp_dados.get("detalhes_itens", [])
    tcmp_por_colaborador = tcmp_dados.get("tcmp_por_colaborador", {})

    # Fallback: se TCMP final não estiver no estado, calcular a partir dos detalhes dos itens
    if (not tcmp_por_colaborador) and detalhes_itens:
        # Construir TCMP calculado por colaborador usando média ponderada por valor do item
        contrib_por_colab = {}  # nome -> {'num': soma(valor*taxa), 'den': soma(valor)}
        for item in detalhes_itens:
            valor_item = item.get("valor_num", 0) or 0
            for taxa in item.get("taxas_colaboradores", []):
                nome = taxa.get("nome")
                taxa_num = taxa.get("taxa_final_num", 0) or 0
                if nome:
                    acc = contrib_por_colab.setdefault(nome, {"num": 0.0, "den": 0.0})
                    acc["num"] += valor_item * taxa_num
                    acc["den"] += valor_item
        # Formatar fallback
        if contrib_por_colab:
            from auditoria_pdf.utils.formatters import formatar_percentual

            tcmp_por_colaborador = {}
            for nome, acc in contrib_por_colab.items():
                tcmp_calc = (acc["num"] / acc["den"]) if acc["den"] > 0 else 0.0
                tcmp_por_colaborador[nome] = {
                    "tcmp": formatar_percentual(tcmp_calc),
                    "tcmp_num": tcmp_calc,
                }

    if not detalhes_itens or len(detalhes_itens) == 0:
        msg = Paragraph("TCMP não calculado para este processo.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, "medio")
        return

    # Explicação
    gerar_paragrafo(
        story,
        "A TCMP é calculada como média ponderada das taxas de comissão de cada item do processo, "
        "usando o valor de cada item como peso. Para cada item, a taxa é determinada pela regra "
        "de comissão correspondente à sua classificação (Linha/Grupo/Subgrupo/Tipo) e cargo do colaborador.",
    )
    adicionar_espacamento(story, "pequeno")

    # Detalhamento por item
    gerar_paragrafo(story, "<b>5.1. Taxas por Item:</b>")
    adicionar_espacamento(story, "pequeno")

    for idx, item in enumerate(detalhes_itens, 1):
        # Cabeçalho do item
        item_titulo = (
            f"<b>Item {idx}:</b> {item['linha']} / {item['grupo']} / "
            f"{item['subgrupo']} / {item['tipo_mercadoria']} - <b>{item['valor']}</b>"
        )
        gerar_paragrafo(story, item_titulo)
        adicionar_espacamento(story, "pequeno")

        # Tabela de taxas por colaborador
        taxas_colab = item.get("taxas_colaboradores", [])
        if taxas_colab:
            dados_tabela = [
                ["Colaborador", "Cargo", "Taxa Rateio", "Fatia Cargo", "Taxa Final"]
            ]

            for taxa in taxas_colab:
                dados_tabela.append(
                    [
                        taxa["nome"],
                        taxa["cargo"],
                        taxa["taxa_rateio"],
                        taxa["fatia_cargo"],
                        taxa["taxa_final"],
                    ]
                )

            larguras = [140, 100, 80, 80, 80]
            tabela = TableBuilder.criar_tabela_simples(
                dados_tabela, larguras=larguras, repetir_header=False
            )
            if tabela:
                story.append(tabela)

        adicionar_espacamento(story, "medio")

    # Fórmula da média ponderada
    gerar_paragrafo(story, "<b>5.2. Fórmula da Média Ponderada:</b>")
    adicionar_espacamento(story, "pequeno")

    formula = Paragraph(
        "TCMP<sub>colaborador</sub> = Σ (Taxa<sub>item,colab</sub> × Valor<sub>item</sub>) / Σ Valor<sub>item</sub>",
        STYLE_FORMULA,
    )
    story.append(formula)
    adicionar_espacamento(story, "medio")

    # Informação do mês de faturamento (ANTES do resultado final)
    mes_faturamento = tcmp_dados.get("mes_faturamento", "-")
    if mes_faturamento and mes_faturamento != "-":
        info_texto = f"<b>Mês de Faturamento:</b> {mes_faturamento}"
        gerar_paragrafo(story, info_texto)
        adicionar_espacamento(story, "pequeno")

    # Resultado final
    gerar_paragrafo(story, "<b>5.3. TCMP Final por Colaborador:</b>")
    adicionar_espacamento(story, "pequeno")

    if tcmp_por_colaborador:
        dados_tabela = [["Colaborador", "TCMP"]]

        for nome, dados in tcmp_por_colaborador.items():
            dados_tabela.append([nome, dados["tcmp"]])

        larguras = [300, 150]
        tabela = TableBuilder.criar_tabela_destaque(
            dados_tabela, larguras=larguras, repetir_header=False
        )
        if tabela:
            story.append(tabela)
    else:
        msg = Paragraph("TCMP não disponível.", STYLE_CORPO)
        story.append(msg)

    # Cálculo matemático detalhado (novo subtópico)
    adicionar_espacamento(story, "medio")
    gerar_paragrafo(story, "<b>5.4. Cálculo Matemático Detalhado:</b>")
    adicionar_espacamento(story, "pequeno")

    print(f"[AUDITORIA] [PDF] [TCMP] Gerando cálculo matemático detalhado...")

    if tcmp_por_colaborador and detalhes_itens:
        from auditoria_pdf.utils.formatters import formatar_moeda, formatar_percentual

        # Agrupar dados por colaborador
        for nome_colab, dados_colab in tcmp_por_colaborador.items():
            gerar_paragrafo(story, f"<b>{nome_colab}:</b>")
            adicionar_espacamento(story, "pequeno")

            # Coletar contribuições de cada item para este colaborador
            contribuicoes = []
            soma_numerador = 0.0
            soma_denominador = 0.0

            for idx, item in enumerate(detalhes_itens, 1):
                valor_item = item["valor_num"]

                # Encontrar taxa deste colaborador neste item
                taxas_colab = item.get("taxas_colaboradores", [])
                taxa_encontrada = None

                for taxa in taxas_colab:
                    if taxa["nome"] == nome_colab:
                        taxa_encontrada = taxa
                        break

                if taxa_encontrada:
                    taxa_final_num = taxa_encontrada["taxa_final_num"]
                    contribuicao = valor_item * taxa_final_num

                    contribuicoes.append(
                        {
                            "item_num": idx,
                            "valor": valor_item,
                            "taxa": taxa_final_num,
                            "contribuicao": contribuicao,
                        }
                    )

                    soma_numerador += contribuicao
                    soma_denominador += valor_item

            if contribuicoes:
                # Mostrar cálculo passo a passo
                for contrib in contribuicoes:
                    linha_calc = (
                        f"Item {contrib['item_num']}: "
                        f"{formatar_moeda(contrib['valor'])} × "
                        f"{formatar_percentual(contrib['taxa'])} = "
                        f"{formatar_moeda(contrib['contribuicao'])}"
                    )
                    gerar_paragrafo(story, linha_calc)

                adicionar_espacamento(story, "pequeno")

                # Cálculo final
                tcmp_calculado = (
                    soma_numerador / soma_denominador if soma_denominador > 0 else 0
                )
                calculo_final = (
                    f"<b>TCMP = ({formatar_moeda(soma_numerador)}) / "
                    f"({formatar_moeda(soma_denominador)}) = "
                    f"{formatar_percentual(tcmp_calculado)}</b>"
                )
                gerar_paragrafo(story, calculo_final)

                print(
                    f"[AUDITORIA] [PDF] [TCMP] {nome_colab}: {len(contribuicoes)} item(ns), TCMP={tcmp_calculado:.4f}"
                )
            else:
                gerar_paragrafo(
                    story, "Nenhuma contribuição encontrada para este colaborador."
                )

            adicionar_espacamento(story, "medio")
    else:
        msg = Paragraph("Dados insuficientes para cálculo detalhado.", STYLE_CORPO)
        story.append(msg)

    # Legenda
    adicionar_espacamento(story, "pequeno")
    gerar_legenda(
        story,
        "Fonte: CONFIG_COMISSAO.csv (regras de comissão por Linha/Grupo/Subgrupo/Tipo e Cargo)",
    )

    adicionar_espacamento(story, "medio")
