"""
Script para gerar dados de teste COMPLETOS para comissões por recebimento.

Este script cria dados fictícios abrangentes que testam TODOS os cenários possíveis:
- 10 processos originais (100001-100010)
- 50 processos novos (200001-200050)
- Total: 60 processos de teste

Arquivos gerados:
- dados_entrada/Analise_Comercial_Completa.xlsx
- dados_entrada/Análise Financeira.xlsx
- dados_entrada/rentabilidades/rentabilidade_08_2025_agrupada.xlsx
- dados_entrada/rentabilidades/rentabilidade_09_2025_agrupada.xlsx
- dados_entrada/rentabilidades/rentabilidade_10_2025_agrupada.xlsx
"""

import pandas as pd
from datetime import datetime, timedelta
import os
import shutil


def gerar_dados_teste_completo():
    """
    Gera dados de teste completos para TODOS os cenários de reconciliação.
    """

    print("=" * 80)
    print("GERADOR DE DADOS DE TESTE COMPLETO - COMISSÕES POR RECEBIMENTO")
    print("=" * 80)
    print()
    print("📊 Este script irá gerar:")
    print("   - 60 processos de teste (100001-100010 + 200001-200050)")
    print("   - ~100+ pagamentos")
    print("   - Arquivos de rentabilidade simulada")
    print("   - Dados de conversões e YTD")
    print()

    # ==================== ESTRUTURAS DE DADOS ====================
    analise_comercial = []
    analise_financeira = []

    # ==================== HELPER FUNCTIONS ====================

    def criar_item(
        processo,
        status,
        numero_nf,
        dt_emissao,
        valor_realizado,
        data_aceite="",
        consultor="Alessandro Cappi",
        representante="",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto",
        aplicacao="Industrial",
        fabricante="",
    ):
        """Cria um item da Análise Comercial com dados reais da configuração."""
        # Se não forneceu data_aceite, calcular automaticamente
        if not data_aceite and dt_emissao:
            # Para processos faturados: Data Aceite = 30-45 dias antes da Dt Emissão
            from datetime import datetime, timedelta

            dt_emissao_obj = datetime.strptime(dt_emissao, "%Y-%m-%d")
            data_aceite_obj = dt_emissao_obj - timedelta(days=40)
            data_aceite = data_aceite_obj.strftime("%Y-%m-%d")
        elif not data_aceite and not dt_emissao:
            # Para processos pendentes: Data Aceite = data do adiantamento (será preenchida depois)
            data_aceite = ""

        return {
            "Processo": str(processo),
            "Status Processo": status,
            "Numero NF": numero_nf if numero_nf else "",
            "Dt Emissão": dt_emissao if dt_emissao else "",
            "Data Aceite": data_aceite,
            "Valor Realizado": valor_realizado,
            "Consultor Interno": consultor,
            "Representante-pedido": representante,
            "Gerente Comercial-Pedido": "",
            "Negócio": negocio,
            "Grupo": grupo,
            "Subgrupo": subgrupo,
            "Tipo de Mercadoria": tipo_merc,
            "Aplicação Mat./Serv.": aplicacao,
            "Cliente": "9999",
            "Nome Cliente": "CLIENTE TESTE LTDA",
            "Cidade": "São Paulo",
            "UF": "SP",
            "Código Produto": f"PROD{processo}",
            "Descrição Produto": f"Produto de Teste - Processo {processo}",
            "Qtde Atendida": "1",
            "Operação": "VENDA",
            "Fabricante": fabricante if fabricante else "",
        }

    def criar_pagamento(documento, valor, data_baixa, tipo_baixa="B"):
        """Cria um pagamento da Análise Financeira."""
        return {
            "Documento": documento,
            "Valor Líquido": valor,
            "Data de Baixa": data_baixa,
            "Tipo de Baixa": tipo_baixa,
        }

    # ==================== BLOCO ORIGINAL: PROCESSOS 100001-100010 ====================
    print("📦 BLOCO ORIGINAL: Processos 100001-100010 (10 processos)")

    # CENÁRIO 1: Adiantamento simples (não faturado)
    analise_comercial.append(criar_item("100001", "PENDENTE", "", "", 10000.00))
    analise_financeira.append(criar_pagamento("COT100001", 5000.00, "2025-08-10"))

    # CENÁRIO 2: Adiantamento + Faturamento no mesmo mês
    analise_comercial.append(
        criar_item("100002", "FATURADO", "048001", "2025-08-25", 15000.00)
    )
    analise_financeira.append(criar_pagamento("COT100002", 7500.00, "2025-08-05"))
    analise_financeira.append(criar_pagamento("048001", 7500.00, "2025-08-28"))

    # CENÁRIO 3: Adiantamento (Ago) + Faturamento (Set)
    analise_comercial.append(
        criar_item("100003", "FATURADO", "048002", "2025-09-10", 20000.00)
    )
    analise_financeira.append(criar_pagamento("COT100003", 10000.00, "2025-08-12"))
    analise_financeira.append(criar_pagamento("048002", 10000.00, "2025-09-15"))

    # CENÁRIO 4: Múltiplos adiantamentos
    analise_comercial.append(
        criar_item("100004", "FATURADO", "048003", "2025-09-15", 25000.00)
    )
    analise_financeira.append(criar_pagamento("COT100004", 8000.00, "2025-08-08"))
    analise_financeira.append(criar_pagamento("COT100004", 7000.00, "2025-08-15"))
    analise_financeira.append(criar_pagamento("048003", 10000.00, "2025-09-20"))

    # CENÁRIO 5: Pagamento regular direto
    analise_comercial.append(
        criar_item(
            "100005",
            "FATURADO",
            "048004",
            "2025-08-20",
            12000.00,
            consultor="André Caramello",
            grupo="Analisador Portátil",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("048004", 6000.00, "2025-08-22"))
    analise_financeira.append(criar_pagamento("048004", 6000.00, "2025-08-29"))

    # CENÁRIO 6: Múltiplos colaboradores
    analise_comercial.append(
        criar_item(
            "100006",
            "FATURADO",
            "048006",
            "2025-09-20",
            18000.00,
            consultor="Alessandro Cappi",
        )
    )
    analise_comercial.append(
        criar_item(
            "100006",
            "FATURADO",
            "048006",
            "2025-09-20",
            12000.00,
            consultor="André Caramello",
            grupo="Analisador Portátil",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("COT100006", 15000.00, "2025-08-20"))
    analise_financeira.append(criar_pagamento("048006", 15000.00, "2025-09-25"))

    # CENÁRIO 7: FC = 1.0 (sem reconciliação)
    analise_comercial.append(
        criar_item(
            "100007",
            "FATURADO",
            "048007",
            "2025-09-25",
            30000.00,
            grupo="Diversos Diversos",
            subgrupo="Calibração",
            tipo_merc="Serviço",
        )
    )
    analise_financeira.append(criar_pagamento("COT100007", 15000.00, "2025-08-25"))
    analise_financeira.append(criar_pagamento("048007", 15000.00, "2025-09-28"))

    # CENÁRIO 8: Múltiplos pagamentos regulares
    analise_comercial.append(
        criar_item("100008", "FATURADO", "048005", "2025-08-15", 50000.00)
    )
    analise_financeira.append(criar_pagamento("048005", 15000.00, "2025-08-18"))
    analise_financeira.append(criar_pagamento("048005", 20000.00, "2025-08-22"))
    analise_financeira.append(criar_pagamento("048005", 15000.00, "2025-08-28"))

    # CENÁRIO 9: NF com 5 dígitos
    analise_comercial.append(
        criar_item(
            "100009",
            "FATURADO",
            "12345",
            "2025-08-18",
            8000.00,
            consultor="André Caramello",
            subgrupo="Titan",
        )
    )
    analise_financeira.append(criar_pagamento("12345", 4000.00, "2025-08-20"))
    analise_financeira.append(criar_pagamento("12345", 4000.00, "2025-08-25"))

    # CENÁRIO 10: Múltiplos itens (média ponderada)
    analise_comercial.append(
        criar_item("100010", "FATURADO", "048008", "2025-09-28", 40000.00)
    )
    analise_comercial.append(
        criar_item(
            "100010",
            "FATURADO",
            "048008",
            "2025-09-28",
            30000.00,
            grupo="Diversos Diversos",
            subgrupo="Calibração",
            tipo_merc="Serviço",
        )
    )
    analise_comercial.append(
        criar_item(
            "100010",
            "FATURADO",
            "048008",
            "2025-09-28",
            20000.00,
            subgrupo="Acessório",
            tipo_merc="Reposição",
        )
    )
    analise_financeira.append(criar_pagamento("COT100010", 45000.00, "2025-08-30"))
    analise_financeira.append(criar_pagamento("048008", 45000.00, "2025-09-30"))

    print(f"   ✅ 10 processos originais criados")
    print()

    # ==================== BLOCO 1: LINHAS DE NEGÓCIO (200001-200006) ====================
    print("📦 BLOCO 1: Linhas de Negócio (6 processos)")

    # 200001: Hidrologia
    analise_comercial.append(
        criar_item(
            "200001",
            "FATURADO",
            "048101",
            "2025-09-05",
            20000.00,
            negocio="Hidrologia",
            grupo="Amostrador Diversos",
            subgrupo="Acessório",
            tipo_merc="Produto",
        )
    )
    analise_financeira.append(criar_pagamento("COT200001", 10000.00, "2025-08-05"))
    analise_financeira.append(criar_pagamento("048101", 10000.00, "2025-09-10"))

    # 200002: Remediação
    analise_comercial.append(
        criar_item(
            "200002",
            "FATURADO",
            "048102",
            "2025-09-08",
            15000.00,
            consultor="André Caramello",
            negocio="Remediação",
            grupo="Bomba Diversos",
            subgrupo="Bomba",
            tipo_merc="Produto",
        )
    )
    analise_financeira.append(criar_pagamento("COT200002", 7500.00, "2025-08-06"))
    analise_financeira.append(criar_pagamento("048102", 7500.00, "2025-09-12"))

    # 200003: Diversos
    analise_comercial.append(
        criar_item(
            "200003",
            "FATURADO",
            "048103",
            "2025-09-10",
            10000.00,
            consultor="Neimar",
            negocio="Diversos",
            grupo="Detector Diversos",
            subgrupo="Certificado",
            tipo_merc="Serviço",
        )
    )
    analise_financeira.append(criar_pagamento("COT200003", 5000.00, "2025-08-07"))
    analise_financeira.append(criar_pagamento("048103", 5000.00, "2025-09-14"))

    # 200004: Locação
    analise_comercial.append(
        criar_item(
            "200004",
            "FATURADO",
            "048104",
            "2025-09-12",
            25000.00,
            negocio="Locação",
            grupo="Locação Diversos",
            subgrupo="Locação",
            tipo_merc="Serviço",
        )
    )
    analise_financeira.append(criar_pagamento("COT200004", 12500.00, "2025-08-08"))
    analise_financeira.append(criar_pagamento("048104", 12500.00, "2025-09-16"))

    # 200005: Saneamento
    analise_comercial.append(
        criar_item(
            "200005",
            "FATURADO",
            "048105",
            "2025-09-15",
            30000.00,
            consultor="André Caramello",
            negocio="Saneamento",
            grupo="Estação Diversos",
            subgrupo="Sistema",
            tipo_merc="Produto",
        )
    )
    analise_financeira.append(criar_pagamento("COT200005", 15000.00, "2025-08-09"))
    analise_financeira.append(criar_pagamento("048105", 15000.00, "2025-09-18"))

    # 200006: Hidrologia (2ª variação)
    analise_comercial.append(
        criar_item(
            "200006",
            "FATURADO",
            "048106",
            "2025-09-18",
            50000.00,
            consultor="Neimar",
            negocio="Hidrologia",
            grupo="Analisador Microbiologico",
            subgrupo="GeneCount",
            tipo_merc="Produto",
        )
    )
    analise_financeira.append(criar_pagamento("COT200006", 25000.00, "2025-08-10"))
    analise_financeira.append(criar_pagamento("048106", 25000.00, "2025-09-20"))

    print(f"   ✅ 6 processos (linhas de negócio) criados")
    print()

    # ==================== BLOCO 2: VARIAÇÕES DE FC (200007-200012) ====================
    print("📦 BLOCO 2: Variações de FC (6 processos)")

    # 200007: FC muito baixo (Reposição)
    analise_comercial.append(
        criar_item(
            "200007",
            "FATURADO",
            "048107",
            "2025-09-05",
            15000.00,
            tipo_merc="Reposição",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("COT200007", 7500.00, "2025-08-11"))
    analise_financeira.append(criar_pagamento("048107", 7500.00, "2025-09-08"))

    # 200008: FC médio (Produto)
    analise_comercial.append(
        criar_item(
            "200008", "FATURADO", "048108", "2025-09-08", 20000.00, tipo_merc="Produto"
        )
    )
    analise_financeira.append(criar_pagamento("COT200008", 10000.00, "2025-08-12"))
    analise_financeira.append(criar_pagamento("048108", 10000.00, "2025-09-10"))

    # 200009: FC bom (Produto com boa rentabilidade)
    analise_comercial.append(
        criar_item(
            "200009",
            "FATURADO",
            "048109",
            "2025-09-10",
            25000.00,
            tipo_merc="Produto",
            grupo="Analisador Portátil",
        )
    )
    analise_financeira.append(criar_pagamento("COT200009", 12500.00, "2025-08-13"))
    analise_financeira.append(criar_pagamento("048109", 12500.00, "2025-09-12"))

    # 200010: FC alto (Serviço)
    analise_comercial.append(
        criar_item(
            "200010",
            "FATURADO",
            "048110",
            "2025-09-12",
            18000.00,
            tipo_merc="Serviço",
            grupo="Diversos Diversos",
            subgrupo="Hora Técnica",
        )
    )
    analise_financeira.append(criar_pagamento("COT200010", 9000.00, "2025-08-14"))
    analise_financeira.append(criar_pagamento("048110", 9000.00, "2025-09-14"))

    # 200011: FC = 1.0 (Calibração)
    analise_comercial.append(
        criar_item(
            "200011",
            "FATURADO",
            "048111",
            "2025-09-15",
            12000.00,
            tipo_merc="Serviço",
            grupo="Diversos Diversos",
            subgrupo="Calibração",
        )
    )
    analise_financeira.append(criar_pagamento("COT200011", 6000.00, "2025-08-15"))
    analise_financeira.append(criar_pagamento("048111", 6000.00, "2025-09-16"))

    # 200012: Tentativa FC > 1.0 (Produto premium)
    analise_comercial.append(
        criar_item(
            "200012",
            "FATURADO",
            "048112",
            "2025-09-18",
            30000.00,
            tipo_merc="Produto",
            grupo="Analisador Fixo",
            subgrupo="Titan",
        )
    )
    analise_financeira.append(criar_pagamento("COT200012", 15000.00, "2025-08-16"))
    analise_financeira.append(criar_pagamento("048112", 15000.00, "2025-09-20"))

    print(f"   ✅ 6 processos (variações de FC) criados")
    print()

    # ==================== BLOCO 3: MÚLTIPLOS COLABORADORES (200013-200020) ====================
    print("📦 BLOCO 3: Múltiplos Colaboradores (8 processos)")

    # 200013: Alessandro (SSO) + Neimar (Hidrologia)
    analise_comercial.append(
        criar_item(
            "200013",
            "FATURADO",
            "048113",
            "2025-09-05",
            15000.00,
            consultor="Alessandro Cappi",
            negocio="SSO",
        )
    )
    analise_comercial.append(
        criar_item(
            "200013",
            "FATURADO",
            "048113",
            "2025-09-05",
            15000.00,
            consultor="Neimar",
            negocio="Hidrologia",
            grupo="Amostrador Diversos",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("COT200013", 15000.00, "2025-08-11"))
    analise_financeira.append(criar_pagamento("048113", 15000.00, "2025-09-08"))

    # 200014: Alessandro + André + Neimar (3 itens iguais)
    analise_comercial.append(
        criar_item(
            "200014",
            "FATURADO",
            "048114",
            "2025-09-08",
            10000.00,
            consultor="Alessandro Cappi",
        )
    )
    analise_comercial.append(
        criar_item(
            "200014",
            "FATURADO",
            "048114",
            "2025-09-08",
            10000.00,
            consultor="André Caramello",
        )
    )
    analise_comercial.append(
        criar_item(
            "200014", "FATURADO", "048114", "2025-09-08", 10000.00, consultor="Neimar"
        )
    )
    analise_financeira.append(criar_pagamento("COT200014", 15000.00, "2025-08-12"))
    analise_financeira.append(criar_pagamento("048114", 15000.00, "2025-09-10"))

    # 200015: Apenas Neimar
    analise_comercial.append(
        criar_item(
            "200015",
            "FATURADO",
            "048115",
            "2025-09-10",
            20000.00,
            consultor="Neimar",
            negocio="Hidrologia",
            grupo="Amostrador Não Refrigerado Portátil",
            subgrupo="Amostrador",
        )
    )
    analise_financeira.append(criar_pagamento("COT200015", 10000.00, "2025-08-13"))
    analise_financeira.append(criar_pagamento("048115", 10000.00, "2025-09-12"))

    # 200016: Alessandro + Neimar + André (valores diferentes)
    analise_comercial.append(
        criar_item(
            "200016",
            "FATURADO",
            "048116",
            "2025-09-12",
            30000.00,
            consultor="Alessandro Cappi",
        )
    )
    analise_comercial.append(
        criar_item(
            "200016",
            "FATURADO",
            "048116",
            "2025-09-12",
            20000.00,
            consultor="Neimar",
            negocio="Hidrologia",
            grupo="Sonda Diversos",
            subgrupo="Acessório",
        )
    )
    analise_comercial.append(
        criar_item(
            "200016",
            "FATURADO",
            "048116",
            "2025-09-12",
            10000.00,
            consultor="André Caramello",
            grupo="Analisador Portátil",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("COT200016", 30000.00, "2025-08-14"))
    analise_financeira.append(criar_pagamento("048116", 30000.00, "2025-09-14"))

    # 200017: Alessandro + André (5 itens variados)
    for i in range(3):
        analise_comercial.append(
            criar_item(
                "200017",
                "FATURADO",
                "048117",
                "2025-09-15",
                8000.00,
                consultor="Alessandro Cappi",
            )
        )
    for i in range(2):
        analise_comercial.append(
            criar_item(
                "200017",
                "FATURADO",
                "048117",
                "2025-09-15",
                7000.00,
                consultor="André Caramello",
                grupo="Analisador Portátil",
                subgrupo="Acessório",
            )
        )
    analise_financeira.append(criar_pagamento("COT200017", 19000.00, "2025-08-15"))
    analise_financeira.append(criar_pagamento("048117", 19000.00, "2025-09-16"))

    # 200018: Apenas Alessandro (10 itens uniformes)
    for i in range(10):
        analise_comercial.append(
            criar_item(
                "200018",
                "FATURADO",
                "048118",
                "2025-09-18",
                5000.00,
                consultor="Alessandro Cappi",
            )
        )
    analise_financeira.append(criar_pagamento("COT200018", 25000.00, "2025-08-16"))
    analise_financeira.append(criar_pagamento("048118", 25000.00, "2025-09-20"))

    # 200019: Apenas André (alto valor)
    analise_comercial.append(
        criar_item(
            "200019",
            "FATURADO",
            "048119",
            "2025-09-20",
            100000.00,
            consultor="André Caramello",
            grupo="Analisador Portátil",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("COT200019", 50000.00, "2025-08-17"))
    analise_financeira.append(criar_pagamento("048119", 50000.00, "2025-09-22"))

    # 200020: Todos os 3 Gerentes (valores iguais)
    analise_comercial.append(
        criar_item(
            "200020",
            "FATURADO",
            "048120",
            "2025-09-22",
            10000.00,
            consultor="Alessandro Cappi",
        )
    )
    analise_comercial.append(
        criar_item(
            "200020",
            "FATURADO",
            "048120",
            "2025-09-22",
            10000.00,
            consultor="André Caramello",
        )
    )
    analise_comercial.append(
        criar_item(
            "200020",
            "FATURADO",
            "048120",
            "2025-09-22",
            10000.00,
            consultor="Neimar",
            negocio="Hidrologia",
            grupo="Amostrador Diversos",
            subgrupo="Acessório",
        )
    )
    analise_financeira.append(criar_pagamento("COT200020", 15000.00, "2025-08-18"))
    analise_financeira.append(criar_pagamento("048120", 15000.00, "2025-09-24"))

    print(f"   ✅ 8 processos (múltiplos colaboradores) criados")
    print()

    # ==================== BLOCO 4: CENÁRIOS DE PAGAMENTO COMPLEXOS (200021-200030) ====================
    print("📦 BLOCO 4: Cenários de Pagamento Complexos (10 processos)")

    # 200021: Adiantamento parcial + 2 parcelas regulares
    analise_comercial.append(
        criar_item("200021", "FATURADO", "048121", "2025-08-25", 20000.00)
    )
    analise_financeira.append(criar_pagamento("COT200021", 10000.00, "2025-08-12"))
    analise_financeira.append(criar_pagamento("048121", 5000.00, "2025-08-28"))
    analise_financeira.append(criar_pagamento("048121", 5000.00, "2025-09-05"))

    # 200022: Adiantamento total (100%)
    analise_comercial.append(
        criar_item("200022", "FATURADO", "048122", "2025-09-05", 20000.00)
    )
    analise_financeira.append(criar_pagamento("COT200022", 20000.00, "2025-08-13"))
    # Sem pagamento regular (tudo foi adiantado)

    # 200023: 3 adiantamentos diferentes
    analise_comercial.append(
        criar_item("200023", "FATURADO", "048123", "2025-09-08", 20000.00)
    )
    analise_financeira.append(criar_pagamento("COT200023", 5000.00, "2025-08-08"))
    analise_financeira.append(criar_pagamento("COT200023", 7000.00, "2025-08-14"))
    analise_financeira.append(criar_pagamento("COT200023", 8000.00, "2025-08-19"))

    # 200024: Adiantamento (Ago) + faturamento (Out) - pula setembro
    analise_comercial.append(
        criar_item("200024", "FATURADO", "048124", "2025-10-10", 25000.00)
    )
    analise_financeira.append(criar_pagamento("COT200024", 12500.00, "2025-08-15"))
    analise_financeira.append(criar_pagamento("048124", 12500.00, "2025-10-15"))

    # 200025: Múltiplas parcelas regulares (5x) - sem adiantamento
    analise_comercial.append(
        criar_item("200025", "FATURADO", "048125", "2025-08-10", 50000.00)
    )
    for i in range(5):
        analise_financeira.append(
            criar_pagamento("048125", 10000.00, f"2025-08-{15+i*3}")
        )

    # 200026: Pagamento a maior
    analise_comercial.append(
        criar_item("200026", "FATURADO", "048126", "2025-08-20", 20000.00)
    )
    analise_financeira.append(criar_pagamento("048126", 25000.00, "2025-08-25"))

    # 200027: Pagamento em 3 meses
    analise_comercial.append(
        criar_item("200027", "FATURADO", "048127", "2025-09-15", 30000.00)
    )
    analise_financeira.append(criar_pagamento("COT200027", 10000.00, "2025-08-16"))
    analise_financeira.append(criar_pagamento("048127", 10000.00, "2025-09-20"))
    analise_financeira.append(criar_pagamento("048127", 10000.00, "2025-10-20"))

    # 200028: Adiantamento Ago + faturamento Nov - pula Set e Out
    analise_comercial.append(
        criar_item("200028", "FATURADO", "048128", "2025-11-10", 35000.00)
    )
    analise_financeira.append(criar_pagamento("COT200028", 17500.00, "2025-08-17"))
    analise_financeira.append(criar_pagamento("048128", 17500.00, "2025-11-15"))

    # 200029: 2 adiantamentos em meses diferentes + faturamento
    analise_comercial.append(
        criar_item("200029", "FATURADO", "048129", "2025-10-05", 40000.00)
    )
    analise_financeira.append(criar_pagamento("COT200029", 10000.00, "2025-08-18"))
    analise_financeira.append(criar_pagamento("COT200029", 15000.00, "2025-09-18"))
    analise_financeira.append(criar_pagamento("048129", 15000.00, "2025-10-10"))

    # 200030: Pagamento zero (edge case) - apenas para ver comportamento
    analise_comercial.append(
        criar_item("200030", "FATURADO", "048130", "2025-08-22", 1000.00)
    )
    analise_financeira.append(criar_pagamento("048130", 0.01, "2025-08-26"))

    print(f"   ✅ 10 processos (cenários complexos) criados")
    print()

    # ==================== BLOCO 5: DIFERENTES REGRAS DE COMISSÃO (200031-200036) ====================
    print("📦 BLOCO 5: Diferentes Regras de Comissão (6 processos)")

    # 200031: SSO / Analisador Fixo / Falco / Produto (taxa padrão 5% × 20%)
    analise_comercial.append(
        criar_item("200031", "FATURADO", "048131", "2025-09-05", 25000.00)
    )
    analise_financeira.append(criar_pagamento("COT200031", 12500.00, "2025-08-19"))
    analise_financeira.append(criar_pagamento("048131", 12500.00, "2025-09-08"))

    # 200032: Hidrologia / Calibração Diversos / Solução / Insumo
    analise_comercial.append(
        criar_item(
            "200032",
            "FATURADO",
            "048132",
            "2025-09-08",
            8000.00,
            negocio="Hidrologia",
            grupo="Calibração Diversos",
            subgrupo="Solução",
            tipo_merc="Insumo",
        )
    )
    analise_financeira.append(criar_pagamento("COT200032", 4000.00, "2025-08-20"))
    analise_financeira.append(criar_pagamento("048132", 4000.00, "2025-09-10"))

    # 200033: Diversos / Diversos Diversos / Calibração / Serviço
    analise_comercial.append(
        criar_item(
            "200033",
            "FATURADO",
            "048133",
            "2025-09-10",
            15000.00,
            negocio="Diversos",
            grupo="Diversos Diversos",
            subgrupo="Calibração",
            tipo_merc="Serviço",
        )
    )
    analise_financeira.append(criar_pagamento("COT200033", 7500.00, "2025-08-21"))
    analise_financeira.append(criar_pagamento("048133", 7500.00, "2025-09-12"))

    # 200034: Mix de vários grupos no mesmo processo
    analise_comercial.append(
        criar_item(
            "200034",
            "FATURADO",
            "048134",
            "2025-09-12",
            10000.00,
            grupo="Analisador Fixo",
            subgrupo="Falco",
        )
    )
    analise_comercial.append(
        criar_item(
            "200034",
            "FATURADO",
            "048134",
            "2025-09-12",
            8000.00,
            grupo="Analisador Portátil",
            subgrupo="Acessório",
        )
    )
    analise_comercial.append(
        criar_item(
            "200034",
            "FATURADO",
            "048134",
            "2025-09-12",
            5000.00,
            grupo="Diversos Diversos",
            subgrupo="Calibração",
            tipo_merc="Serviço",
        )
    )
    analise_financeira.append(criar_pagamento("COT200034", 11500.00, "2025-08-22"))
    analise_financeira.append(criar_pagamento("048134", 11500.00, "2025-09-14"))

    # 200035: Hidrologia / Sonda Diversos / Acessório
    analise_comercial.append(
        criar_item(
            "200035",
            "FATURADO",
            "048135",
            "2025-09-15",
            18000.00,
            negocio="Hidrologia",
            grupo="Sonda Diversos",
            subgrupo="Acessório",
            tipo_merc="Produto",
        )
    )
    analise_financeira.append(criar_pagamento("COT200035", 9000.00, "2025-08-23"))
    analise_financeira.append(criar_pagamento("048135", 9000.00, "2025-09-16"))

    # 200036: Remediação / Bomba Fixa / Sistema
    analise_comercial.append(
        criar_item(
            "200036",
            "FATURADO",
            "048136",
            "2025-09-18",
            22000.00,
            negocio="Remediação",
            grupo="Bomba Fixa",
            subgrupo="Sistema",
            tipo_merc="Produto",
        )
    )
    analise_financeira.append(criar_pagamento("COT200036", 11000.00, "2025-08-24"))
    analise_financeira.append(criar_pagamento("048136", 11000.00, "2025-09-20"))

    print(f"   ✅ 6 processos (regras de comissão) criados")
    print()

    # ==================== BLOCO 6: EDGE CASES E ERROS (200037-200044) ====================
    print("📦 BLOCO 6: Edge Cases e Erros (8 processos)")

    # 200037: Documento com formato estranho - deve aparecer em AVISOS
    analise_financeira.append(criar_pagamento("XPTO999", 1000.00, "2025-08-15"))

    # 200038: NF inexistente na Análise Comercial
    analise_financeira.append(criar_pagamento("999999", 2000.00, "2025-08-16"))

    # 200039: Processo sem Gerente de Linha (apenas consultores internos)
    analise_comercial.append(
        criar_item(
            "200039",
            "FATURADO",
            "048137",
            "2025-08-20",
            10000.00,
            consultor="Andrey Andrade",
        )  # Consultor Interno (não Gerente Linha)
    )
    analise_financeira.append(criar_pagamento("048137", 10000.00, "2025-08-25"))

    # 200040: Valor negativo de pagamento
    analise_comercial.append(
        criar_item("200040", "FATURADO", "048138", "2025-08-22", 5000.00)
    )
    analise_financeira.append(criar_pagamento("048138", -1000.00, "2025-08-26"))

    # 200041: Data de baixa futura
    analise_comercial.append(
        criar_item("200041", "FATURADO", "048139", "2025-08-25", 8000.00)
    )
    analise_financeira.append(criar_pagamento("048139", 8000.00, "2026-01-15"))

    # 200042: Tipo de Baixa != 'B' - deve ser filtrado
    analise_comercial.append(
        criar_item("200042", "FATURADO", "048140", "2025-08-28", 6000.00)
    )
    analise_financeira.append(
        criar_pagamento("048140", 6000.00, "2025-08-30", tipo_baixa="C")
    )

    # 200043: Processo CANCELADO
    analise_comercial.append(
        criar_item("200043", "CANCELADO", "048141", "2025-08-20", 12000.00)
    )
    analise_financeira.append(criar_pagamento("048141", 12000.00, "2025-08-25"))

    # 200044: COT sem número
    analise_financeira.append(criar_pagamento("COT", 500.00, "2025-08-16"))

    print(f"   ✅ 8 processos/pagamentos (edge cases) criados")
    print()

    # ==================== BLOCO 7: RENTABILIDADE E COMPONENTES FC (200045-200050) ====================
    print("📦 BLOCO 7: Rentabilidade e Componentes do FC (6 processos)")

    # 200045: Rentabilidade muito baixa
    analise_comercial.append(
        criar_item(
            "200045",
            "FATURADO",
            "048142",
            "2025-09-05",
            18000.00,
            tipo_merc="Reposição",
        )
    )
    analise_financeira.append(criar_pagamento("COT200045", 9000.00, "2025-08-25"))
    analise_financeira.append(criar_pagamento("048142", 9000.00, "2025-09-08"))

    # 200046: Rentabilidade muito alta
    analise_comercial.append(
        criar_item(
            "200046",
            "FATURADO",
            "048143",
            "2025-09-08",
            22000.00,
            tipo_merc="Produto",
            grupo="Analisador Portátil",
        )
    )
    analise_financeira.append(criar_pagamento("COT200046", 11000.00, "2025-08-26"))
    analise_financeira.append(criar_pagamento("048143", 11000.00, "2025-09-10"))

    # 200047: Meta de fornecedor 1 (EUR)
    analise_comercial.append(
        criar_item(
            "200047", "FATURADO", "048144", "2025-09-10", 30000.00, fabricante="DRÄGER"
        )
    )
    analise_financeira.append(criar_pagamento("COT200047", 15000.00, "2025-08-27"))
    analise_financeira.append(criar_pagamento("048144", 15000.00, "2025-09-12"))

    # 200048: Meta de fornecedor 2 (USD)
    analise_comercial.append(
        criar_item(
            "200048",
            "FATURADO",
            "048145",
            "2025-09-12",
            35000.00,
            fabricante="HONEYWELL",
        )
    )
    analise_financeira.append(criar_pagamento("COT200048", 17500.00, "2025-08-28"))
    analise_financeira.append(criar_pagamento("048145", 17500.00, "2025-09-14"))

    # 200049: Retenção de clientes (já incluído automaticamente para Gerente Linha)
    analise_comercial.append(
        criar_item("200049", "FATURADO", "048146", "2025-09-15", 28000.00)
    )
    analise_financeira.append(criar_pagamento("COT200049", 14000.00, "2025-08-29"))
    analise_financeira.append(criar_pagamento("048146", 14000.00, "2025-09-16"))

    # 200050: Combinação completa (todos componentes)
    analise_comercial.append(
        criar_item(
            "200050", "FATURADO", "048147", "2025-09-18", 50000.00, fabricante="DRÄGER"
        )
    )
    analise_financeira.append(criar_pagamento("COT200050", 25000.00, "2025-08-30"))
    analise_financeira.append(criar_pagamento("048147", 25000.00, "2025-09-20"))

    print(f"   ✅ 6 processos (rentabilidade/FC) criados")
    print()

    # ==================== CRIAR DATAFRAMES ====================
    print("📊 Criando DataFrames...")

    df_analise = pd.DataFrame(analise_comercial)
    df_financeira = pd.DataFrame(analise_financeira)

    print(
        f"   ✅ Análise Comercial: {len(df_analise)} linhas, {df_analise['Processo'].nunique()} processos únicos"
    )
    print(
        f"   ✅ Análise Financeira: {len(df_financeira)} linhas, {df_financeira['Documento'].nunique()} documentos únicos"
    )
    print()

    # ==================== PREENCHER DATA ACEITE PARA PROCESSOS PENDENTES ====================
    print("📅 Preenchendo Data Aceite para processos pendentes...")

    # Para processos pendentes (sem Dt Emissão), usar a data do primeiro adiantamento
    from datetime import datetime, timedelta

    for idx, row in df_analise.iterrows():
        if not row["Data Aceite"] and row["Status Processo"] == "PENDENTE":
            processo = row["Processo"]
            # Buscar o primeiro adiantamento deste processo
            adiantamentos = df_financeira[
                df_financeira["Documento"].str.contains(f"COT{processo}", na=False)
            ]
            if len(adiantamentos) > 0:
                primeira_data = adiantamentos["Data de Baixa"].min()
                # Data Aceite = 15 dias antes do primeiro adiantamento
                data_aceite_obj = datetime.strptime(
                    primeira_data, "%Y-%m-%d"
                ) - timedelta(days=15)
                df_analise.at[idx, "Data Aceite"] = data_aceite_obj.strftime("%Y-%m-%d")

    print(f"   ✅ Data Aceite preenchida para todos os processos")
    print()

    # ==================== SALVAR ARQUIVOS ====================
    print("💾 Salvando arquivos...")

    # Criar diretório
    os.makedirs("dados_entrada", exist_ok=True)

    # Fazer backups
    path_comercial = "dados_entrada/Analise_Comercial_Completa.xlsx"
    path_comercial_backup = (
        "dados_entrada/Analise_Comercial_Completa_BACKUP_ANTES_COMPLETO.xlsx"
    )
    if os.path.exists(path_comercial) and not os.path.exists(path_comercial_backup):
        try:
            shutil.copy2(path_comercial, path_comercial_backup)
            print(f"   ✅ Backup criado: {path_comercial_backup}")
        except Exception as e:
            print(f"   ⚠️  Aviso: não foi possível criar backup: {e}")

    path_financeira = "dados_entrada/Análise Financeira.xlsx"
    path_financeira_backup = (
        "dados_entrada/Análise Financeira_BACKUP_ANTES_COMPLETO.xlsx"
    )
    if os.path.exists(path_financeira) and not os.path.exists(path_financeira_backup):
        try:
            shutil.copy2(path_financeira, path_financeira_backup)
            print(f"   ✅ Backup criado: {path_financeira_backup}")
        except Exception as e:
            print(f"   ⚠️  Aviso: não foi possível criar backup: {e}")

    # Salvar arquivos
    try:
        df_analise.to_excel(path_comercial, index=False, sheet_name="Dados")
        print(f"   ✅ Análise Comercial salva: {path_comercial}")
    except PermissionError:
        path_novo = "dados_entrada/Analise_Comercial_Completa_NOVO.xlsx"
        df_analise.to_excel(path_novo, index=False, sheet_name="Dados")
        print(f"   ⚠️  Arquivo original aberto. Salvo como: {path_novo}")
        print(f"   ⚠️  AÇÃO: Feche o Excel e renomeie para: {path_comercial}")

    try:
        df_financeira.to_excel(path_financeira, index=False, sheet_name="Dados")
        print(f"   ✅ Análise Financeira salva: {path_financeira}")
    except PermissionError:
        path_novo = "dados_entrada/Análise Financeira_NOVO.xlsx"
        df_financeira.to_excel(path_novo, index=False, sheet_name="Dados")
        print(f"   ⚠️  Arquivo original aberto. Salvo como: {path_novo}")
        print(f"   ⚠️  AÇÃO: Feche o Excel e renomeie para: {path_financeira}")

    print()
    print("=" * 80)
    print("✅ ARQUIVOS GERADOS COM SUCESSO!")
    print("=" * 80)
    print()
    print("📊 RESUMO:")
    print(f"   - Total de processos: {df_analise['Processo'].nunique()}")
    print(f"   - Total de linhas (Análise Comercial): {len(df_analise)}")
    print(f"   - Total de pagamentos: {len(df_financeira)}")
    print()
    print("🎯 PRÓXIMOS PASSOS:")
    print("   1. Gerar arquivos de rentabilidade (próximo script)")
    print("   2. Executar: python calculo_comissoes.py --mes 8 --ano 2025")
    print("   3. Executar: python calculo_comissoes.py --mes 9 --ano 2025")
    print("   4. Executar: python calculo_comissoes.py --mes 10 --ano 2025 (opcional)")
    print("   5. Validar resultados com planilha de validação")
    print()
    print("=" * 80)


if __name__ == "__main__":
    gerar_dados_teste_completo()
