"""
Gerador da seção de cálculo de FCMP.
"""

from reportlab.platypus import Paragraph
from auditoria_pdf.styles.pdf_styles import STYLE_CORPO, STYLE_FORMULA
from auditoria_pdf.styles.table_builder import TableBuilder
from auditoria_pdf.generators.section_header import (
    gerar_subtitulo_secao,
    gerar_legenda,
    gerar_paragrafo,
)
from auditoria_pdf.utils.pdf_utils import adicionar_espacamento


def gerar_secao_fcmp(story, dados_processo_formatado: dict):
    """
    Gera seção com cálculo detalhado de FCMP.

    Args:
        story: Lista de elementos do PDF
        dados_processo_formatado: Dados formatados do processo
    """
    # Exibir FCMP apenas para processos FATURADOS
    status_proc = dados_processo_formatado.get("dados_gerais", {}).get(
        "status"
    ) or dados_processo_formatado.get("dados_gerais_formatados", {}).get("status")
    if str(status_proc).strip().upper() != "FATURADO":
        return

    gerar_subtitulo_secao(
        story, "6. CÁLCULO DE FCMP (Fator de Correção Médio Ponderado)"
    )

    fcmp_dados = dados_processo_formatado["fcmp_formatado"]
    detalhes_itens = fcmp_dados.get("detalhes_itens", [])
    fcmp_por_colaborador = fcmp_dados.get("fcmp_por_colaborador", {})

    if not detalhes_itens or len(detalhes_itens) == 0:
        msg = Paragraph("FCMP não calculado para este processo.", STYLE_CORPO)
        story.append(msg)
        adicionar_espacamento(story, "medio")
        return

    # Explicação
    gerar_paragrafo(
        story,
        "O FCMP é calculado como média ponderada dos Fatores de Correção (FC) de cada item do processo, "
        "usando o valor de cada item como peso. O FC de cada item depende do atingimento de múltiplas "
        "metas (Rentabilidade, Faturamento Linha, Conversão, etc.), cada uma com seu peso específico.",
    )
    adicionar_espacamento(story, "pequeno")

    # Detalhamento por item
    gerar_paragrafo(story, "<b>6.1. Fatores de Correção por Item:</b>")
    adicionar_espacamento(story, "pequeno")

    for idx, item in enumerate(detalhes_itens, 1):
        # Cabeçalho do item
        item_titulo = (
            f"<b>Item {idx}:</b> {item['linha']} / {item['grupo']} / "
            f"{item['subgrupo']} / {item['tipo_mercadoria']} - <b>{item['valor']}</b>"
        )
        gerar_paragrafo(story, item_titulo)
        adicionar_espacamento(story, "pequeno")

        # FCs por colaborador
        fcs_colab = item.get("fcs_colaboradores", [])
        for fc_colab in fcs_colab:
            gerar_paragrafo(story, f"<b>{fc_colab['nome']}</b> ({fc_colab['cargo']}):")
            adicionar_espacamento(story, "pequeno")

            # Tabela de componentes
            componentes = fc_colab.get("componentes", [])
            if componentes:
                dados_tabela = [
                    ["Componente", "Peso", "Realizado", "Meta", "Ating.", "Comp. FC"]
                ]

                for comp in componentes:
                    dados_tabela.append(
                        [
                            comp["nome"],
                            comp["peso"],
                            comp["realizado"],
                            comp["meta"],
                            comp["atingimento"],
                            comp["comp_fc"],
                        ]
                    )

                larguras = [100, 60, 80, 80, 70, 80]
                tabela = TableBuilder.criar_tabela_simples(
                    dados_tabela, larguras=larguras, repetir_header=False
                )
                if tabela:
                    story.append(tabela)

                adicionar_espacamento(story, "pequeno")

                # FC final do item para esse colaborador
                fc_final_texto = f"<b>FC do Item:</b> {fc_colab['fc_final']}"
                gerar_paragrafo(story, fc_final_texto)
            else:
                gerar_paragrafo(story, "Nenhum componente com peso > 0")

            adicionar_espacamento(story, "medio")

    # Fórmula da média ponderada
    gerar_paragrafo(story, "<b>6.2. Fórmula da Média Ponderada:</b>")
    adicionar_espacamento(story, "pequeno")

    formula = Paragraph(
        "FCMP<sub>colaborador</sub> = Σ (FC<sub>item,colab</sub> × Valor<sub>item</sub>) / Σ Valor<sub>item</sub>",
        STYLE_FORMULA,
    )
    story.append(formula)
    adicionar_espacamento(story, "medio")

    # Resultado final
    gerar_paragrafo(story, "<b>6.3. FCMP Final por Colaborador:</b>")
    adicionar_espacamento(story, "pequeno")

    if fcmp_por_colaborador:
        dados_tabela = [["Colaborador", "FCMP"]]

        for nome, dados in fcmp_por_colaborador.items():
            dados_tabela.append([nome, dados["fcmp"]])

        larguras = [300, 150]
        tabela = TableBuilder.criar_tabela_destaque(
            dados_tabela, larguras=larguras, repetir_header=False
        )
        if tabela:
            story.append(tabela)
    else:
        msg = Paragraph("FCMP não disponível.", STYLE_CORPO)
        story.append(msg)

    # Cálculo matemático detalhado (novo subtópico)
    adicionar_espacamento(story, "medio")
    gerar_paragrafo(story, "<b>6.4. Cálculo Matemático Detalhado:</b>")
    adicionar_espacamento(story, "pequeno")

    print(f"[AUDITORIA] [PDF] [FCMP] Gerando cálculo matemático detalhado...")

    if fcmp_por_colaborador and detalhes_itens:
        from auditoria_pdf.utils.formatters import formatar_moeda, formatar_numero

        # Agrupar dados por colaborador
        for nome_colab, dados_colab in fcmp_por_colaborador.items():
            gerar_paragrafo(story, f"<b>{nome_colab}:</b>")
            adicionar_espacamento(story, "pequeno")

            # Coletar contribuições de cada item para este colaborador
            contribuicoes = []
            soma_numerador = 0.0
            soma_denominador = 0.0

            for idx, item in enumerate(detalhes_itens, 1):
                valor_item = item["valor_num"]

                # Encontrar FC deste colaborador neste item
                fcs_colab = item.get("fcs_colaboradores", [])
                fc_encontrado = None

                for fc in fcs_colab:
                    if fc["nome"] == nome_colab:
                        fc_encontrado = fc
                        break

                if fc_encontrado:
                    fc_final_num = fc_encontrado["fc_final_num"]
                    contribuicao = valor_item * fc_final_num

                    contribuicoes.append(
                        {
                            "item_num": idx,
                            "valor": valor_item,
                            "fc": fc_final_num,
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
                        f"{formatar_numero(contrib['fc'], 4)} = "
                        f"{formatar_moeda(contrib['contribuicao'])}"
                    )
                    gerar_paragrafo(story, linha_calc)

                adicionar_espacamento(story, "pequeno")

                # Cálculo final
                fcmp_calculado = (
                    soma_numerador / soma_denominador if soma_denominador > 0 else 0
                )
                calculo_final = (
                    f"<b>FCMP = ({formatar_moeda(soma_numerador)}) / "
                    f"({formatar_moeda(soma_denominador)}) = "
                    f"{formatar_numero(fcmp_calculado, 4)}</b>"
                )
                gerar_paragrafo(story, calculo_final)

                print(
                    f"[AUDITORIA] [PDF] [FCMP] {nome_colab}: {len(contribuicoes)} item(ns), FCMP={fcmp_calculado:.4f}"
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
        "Fontes: Faturados.xlsx, Conversoes.xlsx, Faturados_YTD.xlsx, Retencao_Clientes.xlsx, "
        "Rentabilidades/Rentabilidade_Realizada_MM_AAAA.xlsx, PESOS_METAS.csv",
    )

    adicionar_espacamento(story, "medio")
