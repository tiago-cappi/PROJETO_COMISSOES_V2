"""
Script para gerar dados de teste completos para comissões por recebimento e reconciliações.

Este script cria dados fictícios nos arquivos:
- dados_entrada/Analise_Comercial_Completa.xlsx
- dados_entrada/Análise Financeira.xlsx

Os dados testam TODOS os cenários possíveis de reconciliações.
"""

import pandas as pd
from datetime import datetime, timedelta
import os


def gerar_dados_teste():
    """
    Gera dados de teste completos para todos os cenários de reconciliação.
    """

    print("=" * 80)
    print("GERADOR DE DADOS DE TESTE PARA RECONCILIAÇÕES")
    print("=" * 80)
    print()

    # ==================== ANÁLISE COMERCIAL COMPLETA ====================
    print("1. Gerando dados da Análise Comercial Completa...")

    # CENÁRIO 1: Processo 100001 - Adiantamento simples (não faturado ainda)
    # - Receberá COT100001 em Agosto
    # - Não deve gerar reconciliação (ainda não faturado)

    # CENÁRIO 2: Processo 100002 - Adiantamento + Faturamento no mesmo mês
    # - Receberá COT100002 em Agosto
    # - Será faturado em Agosto (NF 048001)
    # - Deve gerar reconciliação em Agosto
    # - FC < 1.0 para gerar reconciliação negativa

    # CENÁRIO 3: Processo 100003 - Adiantamento em Agosto, Faturamento em Setembro
    # - Receberá COT100003 em Agosto
    # - Será faturado em Setembro (NF 048002)
    # - Deve gerar reconciliação em Setembro

    # CENÁRIO 4: Processo 100004 - Múltiplos adiantamentos + Faturamento
    # - Receberá COT100004 duas vezes em Agosto
    # - Será faturado em Setembro (NF 048003)
    # - Reconciliação deve considerar SOMA dos adiantamentos

    # CENÁRIO 5: Processo 100005 - Pagamento regular direto (sem adiantamento)
    # - Será faturado em Agosto (NF 048004)
    # - Receberá pagamento regular em Agosto
    # - NÃO deve gerar reconciliação (sem adiantamento prévio)

    # CENÁRIO 6: Processo 100006 - Múltiplos colaboradores
    # - 2 colaboradores (Alessandro Cappi e Leandro Daher)
    # - Cada um com TCMP e FCMP diferentes
    # - Reconciliação individual por colaborador

    # CENÁRIO 7: Processo 100007 - FC = 1.0 (sem reconciliação)
    # - Adiantamento em Agosto
    # - Faturamento em Setembro com FC = 1.0
    # - NÃO deve gerar reconciliação (FC = 1.0)

    # CENÁRIO 8: Processo 100008 - Múltiplos pagamentos regulares
    # - Faturado em Agosto (NF 048005)
    # - Recebe 3 parcelas regulares em Agosto
    # - Comissão correta em cada parcela

    # CENÁRIO 9: Processo 100009 - NF com 5 dígitos
    # - Para testar mapeamento com NF menor
    # - NF 12345

    # CENÁRIO 10: Processo 100010 - Múltiplos itens (média ponderada)
    # - 3 itens com valores e FCs diferentes
    # - Deve calcular TCMP e FCMP ponderados corretamente

    analise_comercial = []

    # Helper para criar itens - USANDO DADOS REAIS DA CONFIGURAÇÃO
    def criar_item(
        processo,
        status,
        numero_nf,
        dt_emissao,
        valor_realizado,
        consultor="Alessandro Cappi",  # Colaborador REAL (C018)
        representante="",
        negocio="SSO",  # Linha REAL = Negócio REAL
        grupo="Analisador Fixo",  # Grupo REAL
        subgrupo="Falco",  # Subgrupo REAL
        tipo_merc="Produto",  # Tipo de Mercadoria REAL
        aplicacao="Industrial",
    ):
        return {
            "Processo": str(processo),
            "Status Processo": status,
            "Numero NF": numero_nf if numero_nf else "",
            "Dt Emissão": dt_emissao if dt_emissao else "",
            "Valor Realizado": valor_realizado,
            "Consultor Interno": consultor,
            "Representante-pedido": representante,
            "Gerente Comercial-Pedido": "",
            "Negócio": negocio,  # = Linha (são sinônimos)
            "Grupo": grupo,
            "Subgrupo": subgrupo,
            "Tipo de Mercadoria": tipo_merc,
            "Aplicação Mat./Serv.": aplicacao,
            "Cliente": "9999",
            "Nome Cliente": "CLIENTE TESTE LTDA",
            "Cidade": "São Paulo",
            "UF": "SP",
            "Código Produto": "PROD001",
            "Descrição Produto": "Produto de Teste",
            "Qtde Atendida": "1",
            "Operação": "VENDA",
        }

    # CENÁRIO 1: Processo 100001 - Adiantamento simples (PENDENTE)
    analise_comercial.append(
        criar_item("100001", "PENDENTE", "", "", 10000.00, consultor="Alessandro Cappi")
    )

    # CENÁRIO 2: Processo 100002 - Adiantamento + Faturamento em Agosto
    # Item com FC baixo para gerar reconciliação negativa (usando Produto)
    analise_comercial.append(
        criar_item(
            "100002",
            "FATURADO",
            "048001",
            "2025-08-25",
            15000.00,
            consultor="Alessandro Cappi",
            negocio="SSO",  # Linha REAL
            grupo="Analisador Fixo",
            subgrupo="Falco",
            tipo_merc="Produto",  # FC < 1.0
        )
    )

    # CENÁRIO 3: Processo 100003 - Adiantamento em Agosto, Faturamento em Setembro
    analise_comercial.append(
        criar_item(
            "100003",
            "FATURADO",
            "048002",
            "2025-09-10",
            20000.00,
            consultor="Alessandro Cappi",
        )
    )

    # CENÁRIO 4: Processo 100004 - Múltiplos adiantamentos
    analise_comercial.append(
        criar_item(
            "100004",
            "FATURADO",
            "048003",
            "2025-09-15",
            25000.00,
            consultor="Alessandro Cappi",
        )
    )

    # CENÁRIO 5: Processo 100005 - Pagamento regular direto
    analise_comercial.append(
        criar_item(
            "100005",
            "FATURADO",
            "048004",
            "2025-08-20",
            12000.00,
            consultor="André Caramello",  # Gerente Linha REAL (C003)
            negocio="SSO",
            grupo="Analisador Portátil",
            subgrupo="Acessório",
            tipo_merc="Produto",
        )
    )

    # CENÁRIO 6: Processo 100006 - Múltiplos colaboradores (2 itens)
    # Alessandro Cappi (Gerente Linha REAL) + André Caramello (Gerente Linha REAL)
    analise_comercial.append(
        criar_item(
            "100006",
            "FATURADO",
            "048006",
            "2025-09-20",
            18000.00,
            consultor="Alessandro Cappi",  # Gerente Linha (C018)
            negocio="SSO",
            grupo="Analisador Fixo",
            subgrupo="Falco",
            tipo_merc="Produto",
        )
    )
    analise_comercial.append(
        criar_item(
            "100006",
            "FATURADO",
            "048006",
            "2025-09-20",
            12000.00,
            consultor="André Caramello",  # Gerente Linha (C003)
            negocio="SSO",
            grupo="Analisador Portátil",
            subgrupo="Acessório",
            tipo_merc="Produto",
        )
    )

    # CENÁRIO 7: Processo 100007 - FC = 1.0 (usando Serviço para FC próximo a 1.0)
    analise_comercial.append(
        criar_item(
            "100007",
            "FATURADO",
            "048007",
            "2025-09-25",
            30000.00,
            consultor="Alessandro Cappi",
            negocio="SSO",
            grupo="Diversos Diversos",
            subgrupo="Calibração",
            tipo_merc="Serviço",  # Serviço pode ter FC próximo ou = 1.0
        )
    )

    # CENÁRIO 8: Processo 100008 - Múltiplos pagamentos regulares
    analise_comercial.append(
        criar_item(
            "100008",
            "FATURADO",
            "048005",
            "2025-08-15",
            50000.00,
            consultor="Alessandro Cappi",
        )
    )

    # CENÁRIO 9: Processo 100009 - NF com 5 dígitos
    analise_comercial.append(
        criar_item(
            "100009",
            "FATURADO",
            "12345",
            "2025-08-18",
            8000.00,
            consultor="André Caramello",  # Gerente Linha REAL
            negocio="SSO",
            grupo="Analisador Fixo",
            subgrupo="Titan",
            tipo_merc="Produto",
        )
    )

    # CENÁRIO 10: Processo 100010 - Múltiplos itens (média ponderada)
    # 3 itens com valores e tipos diferentes para testar média ponderada de TCMP/FCMP
    analise_comercial.append(
        criar_item(
            "100010",
            "FATURADO",
            "048008",
            "2025-09-28",
            40000.00,
            consultor="Alessandro Cappi",
            negocio="SSO",
            grupo="Analisador Fixo",
            subgrupo="Falco",
            tipo_merc="Produto",  # FC baixo
        )
    )
    analise_comercial.append(
        criar_item(
            "100010",
            "FATURADO",
            "048008",
            "2025-09-28",
            30000.00,
            consultor="Alessandro Cappi",
            negocio="SSO",
            grupo="Diversos Diversos",
            subgrupo="Calibração",
            tipo_merc="Serviço",  # FC médio/alto
        )
    )
    analise_comercial.append(
        criar_item(
            "100010",
            "FATURADO",
            "048008",
            "2025-09-28",
            20000.00,
            consultor="Alessandro Cappi",
            negocio="SSO",
            grupo="Analisador Fixo",
            subgrupo="Acessório",
            tipo_merc="Reposição",  # FC muito baixo
        )
    )

    df_analise = pd.DataFrame(analise_comercial)

    print(f"   - {len(df_analise)} linhas criadas")
    print(f"   - {df_analise['Processo'].nunique()} processos únicos")
    print()

    # ==================== ANÁLISE FINANCEIRA ====================
    print("2. Gerando dados da Análise Financeira...")

    analise_financeira = []

    # Helper para criar pagamentos
    def criar_pagamento(documento, valor, data_baixa, tipo_baixa="B"):
        return {
            "Documento": documento,
            "Valor Líquido": valor,
            "Data de Baixa": data_baixa,
            "Tipo de Baixa": tipo_baixa,
        }

    # CENÁRIO 1: COT100001 em Agosto (processo não faturado)
    analise_financeira.append(criar_pagamento("COT100001", 5000.00, "2025-08-10"))

    # CENÁRIO 2: COT100002 em Agosto + Pagamento regular em Agosto
    analise_financeira.append(criar_pagamento("COT100002", 7500.00, "2025-08-05"))
    analise_financeira.append(criar_pagamento("048001", 7500.00, "2025-08-28"))

    # CENÁRIO 3: COT100003 em Agosto + Pagamento regular em Setembro
    analise_financeira.append(criar_pagamento("COT100003", 10000.00, "2025-08-12"))
    analise_financeira.append(criar_pagamento("048002", 10000.00, "2025-09-15"))

    # CENÁRIO 4: Múltiplos COT100004 em Agosto + Pagamento regular em Setembro
    analise_financeira.append(criar_pagamento("COT100004", 8000.00, "2025-08-08"))
    analise_financeira.append(criar_pagamento("COT100004", 7000.00, "2025-08-15"))
    analise_financeira.append(criar_pagamento("048003", 10000.00, "2025-09-20"))

    # CENÁRIO 5: Pagamento regular direto (sem COT)
    analise_financeira.append(criar_pagamento("048004", 6000.00, "2025-08-22"))
    analise_financeira.append(criar_pagamento("048004", 6000.00, "2025-08-29"))

    # CENÁRIO 6: COT100006 + Pagamento regular (múltiplos colaboradores)
    analise_financeira.append(criar_pagamento("COT100006", 15000.00, "2025-08-20"))
    analise_financeira.append(criar_pagamento("048006", 15000.00, "2025-09-25"))

    # CENÁRIO 7: COT100007 + Pagamento regular (FC = 1.0)
    analise_financeira.append(criar_pagamento("COT100007", 15000.00, "2025-08-25"))
    analise_financeira.append(criar_pagamento("048007", 15000.00, "2025-09-28"))

    # CENÁRIO 8: Múltiplos pagamentos regulares (3 parcelas)
    analise_financeira.append(criar_pagamento("048005", 15000.00, "2025-08-18"))
    analise_financeira.append(criar_pagamento("048005", 20000.00, "2025-08-22"))
    analise_financeira.append(criar_pagamento("048005", 15000.00, "2025-08-28"))

    # CENÁRIO 9: NF com 5 dígitos
    analise_financeira.append(criar_pagamento("12345", 4000.00, "2025-08-20"))
    analise_financeira.append(criar_pagamento("12345", 4000.00, "2025-08-25"))

    # CENÁRIO 10: COT100010 + Pagamento regular (média ponderada)
    analise_financeira.append(criar_pagamento("COT100010", 45000.00, "2025-08-30"))
    analise_financeira.append(criar_pagamento("048008", 45000.00, "2025-09-30"))

    # EXTRA: Documento não mapeável (para teste de AVISOS)
    analise_financeira.append(criar_pagamento("XYZ999", 1000.00, "2025-08-15"))
    analise_financeira.append(
        criar_pagamento("COT", 500.00, "2025-08-16")  # COT sem número
    )

    df_financeira = pd.DataFrame(analise_financeira)

    print(f"   - {len(df_financeira)} linhas criadas")
    print(f"   - {df_financeira['Documento'].nunique()} documentos únicos")
    print()

    # ==================== SALVAR ARQUIVOS ====================
    print("3. Salvando arquivos Excel...")

    # Criar diretório se não existir
    os.makedirs("dados_entrada", exist_ok=True)

    # Fazer backup dos arquivos existentes se necessário
    path_comercial_backup = (
        "dados_entrada/Analise_Comercial_Completa_BACKUP_ORIGINAL.xlsx"
    )
    path_comercial = "dados_entrada/Analise_Comercial_Completa.xlsx"
    if os.path.exists(path_comercial) and not os.path.exists(path_comercial_backup):
        try:
            import shutil

            shutil.copy2(path_comercial, path_comercial_backup)
            print(f"   ✓ Backup criado: {path_comercial_backup}")
        except Exception as e:
            print(f"   ! Aviso: não foi possível criar backup: {e}")

    path_financeira_backup = "dados_entrada/Análise Financeira_BACKUP_ORIGINAL.xlsx"
    path_financeira = "dados_entrada/Análise Financeira.xlsx"
    if os.path.exists(path_financeira) and not os.path.exists(path_financeira_backup):
        try:
            import shutil

            shutil.copy2(path_financeira, path_financeira_backup)
            print(f"   ✓ Backup criado: {path_financeira_backup}")
        except Exception as e:
            print(f"   ! Aviso: não foi possível criar backup: {e}")

    # Tentar salvar (avisa se arquivo estiver aberto)
    try:
        df_analise.to_excel(path_comercial, index=False, sheet_name="Dados")
        print(f"   ✓ Análise Comercial salva em: {path_comercial}")
    except PermissionError:
        path_comercial_novo = "dados_entrada/Analise_Comercial_Completa_NOVO_TESTE.xlsx"
        df_analise.to_excel(path_comercial_novo, index=False, sheet_name="Dados")
        print(
            f"   ! AVISO: Arquivo original está aberto. Salvo como: {path_comercial_novo}"
        )
        print(
            f"   ! AÇÃO NECESSÁRIA: Feche o Excel e renomeie '{path_comercial_novo}' para '{path_comercial}'"
        )

    try:
        df_financeira.to_excel(path_financeira, index=False, sheet_name="Dados")
        print(f"   ✓ Análise Financeira salva em: {path_financeira}")
    except PermissionError:
        path_financeira_novo = "dados_entrada/Análise Financeira_NOVO_TESTE.xlsx"
        df_financeira.to_excel(path_financeira_novo, index=False, sheet_name="Dados")
        print(
            f"   ! AVISO: Arquivo original está aberto. Salvo como: {path_financeira_novo}"
        )
        print(
            f"   ! AÇÃO NECESSÁRIA: Feche o Excel e renomeie '{path_financeira_novo}' para '{path_financeira}'"
        )

    print()
    print("=" * 80)
    print("ARQUIVOS GERADOS COM SUCESSO!")
    print("=" * 80)
    print()

    # ==================== RESUMO DOS CENÁRIOS ====================
    print("RESUMO DOS CENÁRIOS DE TESTE:")
    print("-" * 80)
    print()

    cenarios = [
        {
            "id": 1,
            "processo": "100001",
            "descricao": "Adiantamento simples (processo não faturado)",
            "iteracoes": 1,
            "mes_iter1": "Agosto/2025",
            "resultado_esperado": "Comissão de adiantamento calculada com FC=1.0. SEM reconciliação.",
        },
        {
            "id": 2,
            "processo": "100002",
            "descricao": "Adiantamento + Faturamento no mesmo mês",
            "iteracoes": 1,
            "mes_iter1": "Agosto/2025",
            "resultado_esperado": "Adiantamento + Reconciliação negativa no mesmo mês.",
        },
        {
            "id": 3,
            "processo": "100003",
            "descricao": "Adiantamento em Agosto, Faturamento em Setembro",
            "iteracoes": 2,
            "mes_iter1": "Agosto/2025",
            "mes_iter2": "Setembro/2025",
            "modificacoes": "Nenhuma (já configurado)",
            "resultado_esperado": "Agosto: adiantamento. Setembro: reconciliação + pagamento regular.",
        },
        {
            "id": 4,
            "processo": "100004",
            "descricao": "Múltiplos adiantamentos + Faturamento",
            "iteracoes": 2,
            "mes_iter1": "Agosto/2025",
            "mes_iter2": "Setembro/2025",
            "modificacoes": "Nenhuma (já configurado)",
            "resultado_esperado": "Agosto: soma de 2 adiantamentos. Setembro: reconciliação baseada na soma.",
        },
        {
            "id": 5,
            "processo": "100005",
            "descricao": "Pagamento regular direto (sem adiantamento)",
            "iteracoes": 1,
            "mes_iter1": "Agosto/2025",
            "resultado_esperado": "Apenas comissões regulares. SEM reconciliação.",
        },
        {
            "id": 6,
            "processo": "100006",
            "descricao": "Múltiplos colaboradores (Alessandro Cappi e André Caramello)",
            "iteracoes": 2,
            "mes_iter1": "Agosto/2025",
            "mes_iter2": "Setembro/2025",
            "modificacoes": "Nenhuma (já configurado)",
            "resultado_esperado": "Reconciliação individual para cada colaborador.",
        },
        {
            "id": 7,
            "processo": "100007",
            "descricao": "FC = 1.0 (sem reconciliação)",
            "iteracoes": 2,
            "mes_iter1": "Agosto/2025",
            "mes_iter2": "Setembro/2025",
            "modificacoes": "Nenhuma (já configurado)",
            "resultado_esperado": "Agosto: adiantamento. Setembro: SEM reconciliação (FC=1.0).",
        },
        {
            "id": 8,
            "processo": "100008",
            "descricao": "Múltiplos pagamentos regulares (3 parcelas)",
            "iteracoes": 1,
            "mes_iter1": "Agosto/2025",
            "resultado_esperado": "3 comissões regulares calculadas corretamente.",
        },
        {
            "id": 9,
            "processo": "100009",
            "descricao": "NF com 5 dígitos",
            "iteracoes": 1,
            "mes_iter1": "Agosto/2025",
            "resultado_esperado": "Mapeamento correto e comissões calculadas.",
        },
        {
            "id": 10,
            "processo": "100010",
            "descricao": "Múltiplos itens (média ponderada TCMP/FCMP)",
            "iteracoes": 2,
            "mes_iter1": "Agosto/2025",
            "mes_iter2": "Setembro/2025",
            "modificacoes": "Nenhuma (já configurado)",
            "resultado_esperado": "TCMP e FCMP calculados como média ponderada. Reconciliação correta.",
        },
    ]

    for c in cenarios:
        print(f"CENÁRIO {c['id']}: {c['descricao']}")
        print(f"   Processo: {c['processo']}")
        print(f"   Iterações: {c['iteracoes']}")
        print(f"   1ª Rodada: {c['mes_iter1']}")
        if c.get("mes_iter2"):
            print(f"   2ª Rodada: {c['mes_iter2']}")
        if c.get("modificacoes"):
            print(f"   Modificações entre rodadas: {c['modificacoes']}")
        print(f"   Resultado esperado: {c['resultado_esperado']}")
        print()

    print("-" * 80)
    print()

    # ==================== INSTRUÇÕES DE TESTE ====================
    print("INSTRUÇÕES PARA EXECUTAR OS TESTES:")
    print("=" * 80)
    print()
    print("1. TESTE ÚNICO (Agosto/2025):")
    print("   Execute: python calculo_comissoes.py --mes 8 --ano 2025")
    print("   Validar:")
    print("      - Cenários 1, 2, 5, 8, 9: comissões e reconciliações")
    print("      - Arquivo: Comissoes_Recebimento_08_2025.xlsx")
    print(
        "      - Abas: COMISSOES_ADIANTAMENTOS, COMISSOES_REGULARES, RECONCILIACOES, ESTADO"
    )
    print()
    print("2. TESTE DUPLO (Agosto + Setembro):")
    print("   a) Primeira rodada:")
    print("      Execute: python calculo_comissoes.py --mes 8 --ano 2025")
    print(
        "      Resultado: Adiantamentos calculados, processos ainda não faturados no estado"
    )
    print()
    print("   b) Segunda rodada:")
    print("      Execute: python calculo_comissoes.py --mes 9 --ano 2025")
    print("      Resultado: Reconciliações para processos que foram faturados")
    print("      Validar:")
    print(
        "         - Cenários 3, 4, 6, 7, 10: reconciliações aparecem na aba RECONCILIACOES"
    )
    print("         - Estado atualizado com TCMP_JSON, FCMP_JSON, STATUS_RECONCILIACAO")
    print()
    print("3. DOCUMENTOS NÃO MAPEADOS:")
    print("   Verificar aba 'AVISOS' para documentos: XYZ999, COT (sem número)")
    print()
    print("=" * 80)
    print()
    print("OBSERVAÇÕES IMPORTANTES:")
    print("-" * 80)
    print(
        "• O arquivo 'Estado_Processos_Recebimento.xlsx' será criado/atualizado automaticamente"
    )
    print("• Entre rodadas, NÃO delete o arquivo de estado (ele mantém o histórico)")
    print(
        "• Para resetar testes: delete 'Estado_Processos_Recebimento.xlsx' e recomece"
    )
    print("• Reconciliações aparecem APENAS no mês do faturamento")
    print("• FCMP < 1.0 gera reconciliação negativa (desconto)")
    print("• FCMP = 1.0 NÃO gera reconciliação")
    print("=" * 80)
    print()


if __name__ == "__main__":
    gerar_dados_teste()
