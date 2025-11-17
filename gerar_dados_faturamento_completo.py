"""
Script para gerar dados de teste COMPLETOS para comissões por FATURAMENTO,
CROSS-SELLING e FC de FORNECEDORES.

Este script adiciona NOVOS processos (300001-500015) SEM ALTERAR os 57 processos
existentes (100001-100010 e 200001-200050) que testam comissões por recebimento.

Arquivos gerados:
- dados_entrada/Faturados_08_2025.xlsx
- dados_entrada/Faturados_09_2025.xlsx
- dados_entrada/Conversões_08_2025.xlsx
- dados_entrada/Conversões_09_2025.xlsx
- dados_entrada/vendas_fornecedores_moeda_nativa.xlsx
- dados_entrada/faturamento_ytd_08_2025.xlsx
- dados_entrada/faturamento_ytd_09_2025.xlsx
"""

import pandas as pd
from datetime import datetime, timedelta
import os

def gerar_dados_faturamento_completo():
    """
    Gera dados de teste completos para comissões por FATURAMENTO.
    """
    
    print("=" * 80)
    print("GERADOR DE DADOS DE TESTE - COMISSÕES POR FATURAMENTO")
    print("=" * 80)
    print()
    print("📊 Este script irá gerar:")
    print("   - 50 processos para FATURAMENTO (300001-300050)")
    print("   - 10 processos para CROSS-SELLING (400001-400010)")
    print("   - 15 processos para FC FORNECEDORES (500001-500015)")
    print("   - Total: 75 novos processos")
    print()
    
    # ==================== ESTRUTURAS DE DADOS ====================
    faturados_ago = []
    faturados_set = []
    conversoes_ago = []
    conversoes_set = []
    vendas_fornecedores = []
    
    # ==================== HELPER FUNCTIONS ====================
    
    def criar_item_faturado(
        processo,
        numero_nf,
        dt_emissao,
        data_aceite,
        valor_realizado,
        consultor_interno="",
        representante="",
        gerente_comercial="",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto",
        aplicacao="Industrial",
        fabricante="",
    ):
        """Cria um item de Faturamento."""
        return {
            "Processo": str(processo),
            "Status Processo": "FATURADO",
            "Numero NF": numero_nf,
            "Dt Emissão": dt_emissao,
            "Data Aceite": data_aceite,
            "Valor Realizado": valor_realizado,
            "Consultor Interno": consultor_interno,
            "Representante-pedido": representante,
            "Gerente Comercial-Pedido": gerente_comercial,
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
    
    def criar_conversao(
        processo,
        data_aceite,
        valor_orcado,
        negocio="SSO",
        consultor_interno="",
    ):
        """Cria um item de Conversão."""
        return {
            "Processo": str(processo),
            "Data Aceite": data_aceite,
            "Valor Orçado": valor_orcado,
            "Negócio": negocio,
            "Consultor Interno": consultor_interno,
        }
    
    # ==================== BLOCO 1: COMISSÕES POR FATURAMENTO (300001-300050) ====================
    print("📦 BLOCO 1: Comissões por Faturamento (300001-300050)")
    
    # GRUPO A: Diferentes Colaboradores e Cargos (10 processos)
    print("   📋 Grupo A: Diferentes Colaboradores e Cargos...")
    
    # Processo 300001: Consultor Interno + Diretor
    faturados_ago.append(criar_item_faturado(
        "300001", "348001", "2025-08-15", "2025-07-05",
        50000.00,
        consultor_interno="ANDREY.ANDRADE",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300001", "2025-07-05", 50000.00, "SSO", "ANDREY.ANDRADE"))
    
    # Processo 300002: Consultor Interno + Consultor Externo + Gerente Geral
    faturados_ago.append(criar_item_faturado(
        "300002", "348002", "2025-08-18", "2025-07-08",
        30000.00,
        consultor_interno="MATEUS.MACHADO",
        representante="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="ISCO",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300002", "2025-07-08", 30000.00, "Hidrologia", "MATEUS.MACHADO"))
    
    # Processo 300003: Apenas Consultor Externo + Coordenador
    faturados_ago.append(criar_item_faturado(
        "300003", "348003", "2025-08-20", "2025-07-10",
        20000.00,
        representante="LEONARDO CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300003", "2025-07-10", 20000.00, "Remediação", ""))
    
    # Processo 300004: Consultor Interno + Supervisor
    faturados_ago.append(criar_item_faturado(
        "300004", "348004", "2025-08-22", "2025-07-12",
        15000.00,
        consultor_interno="ANDREY.ANDRADE",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="MicroClip",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300004", "2025-07-12", 15000.00, "SSO", "ANDREY.ANDRADE"))
    
    # Processo 300005: Consultor Interno + Consultor Externo (sem gestor específico)
    faturados_ago.append(criar_item_faturado(
        "300005", "348005", "2025-08-25", "2025-07-15",
        25000.00,
        consultor_interno="MATEUS.MACHADO",
        representante="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Hidrologia",
        grupo="Sonda Multiparâmetros",
        subgrupo="EXO",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300005", "2025-07-15", 25000.00, "Hidrologia", "MATEUS.MACHADO"))
    
    # Processo 300006: Múltiplos itens (mesmo processo, diferentes consultores)
    # Item 1
    faturados_ago.append(criar_item_faturado(
        "300006", "348006", "2025-08-28", "2025-07-18",
        20000.00,
        consultor_interno="ANDREY.ANDRADE",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto"
    ))
    # Item 2
    faturados_ago.append(criar_item_faturado(
        "300006", "348006", "2025-08-28", "2025-07-18",
        20000.00,
        consultor_interno="MATEUS.MACHADO",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="MicroClip",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300006", "2025-07-18", 40000.00, "SSO", "ANDREY.ANDRADE"))
    
    # Processo 300007: Múltiplos consultores externos
    faturados_set.append(criar_item_faturado(
        "300007", "348007", "2025-09-05", "2025-07-25",
        35000.00,
        representante="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="Thermo",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300007", "2025-07-25", 35000.00, "Remediação", ""))
    
    # Processo 300008: Consultor Interno + Externo + Diretor
    faturados_set.append(criar_item_faturado(
        "300008", "348008", "2025-09-08", "2025-07-28",
        45000.00,
        consultor_interno="ANDREY.ANDRADE",
        representante="LEONARDO CAMARGO",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="YSI",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("300008", "2025-07-28", 45000.00, "Hidrologia", "ANDREY.ANDRADE"))
    
    # Processo 300009: Consultor Interno + Coordenador
    faturados_set.append(criar_item_faturado(
        "300009", "348009", "2025-09-10", "2025-08-01",
        28000.00,
        consultor_interno="MATEUS.MACHADO",
        negocio="SSO",
        grupo="Analisador Portátil",
        subgrupo="Innova",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("300009", "2025-08-01", 28000.00, "SSO", "MATEUS.MACHADO"))
    
    # Processo 300010: Consultor Interno + Externo + Supervisor
    faturados_set.append(criar_item_faturado(
        "300010", "348010", "2025-09-12", "2025-08-03",
        32000.00,
        consultor_interno="ANDREY.ANDRADE",
        representante="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("300010", "2025-08-03", 32000.00, "Remediação", "ANDREY.ANDRADE"))
    
    print(f"   ✅ Grupo A: 10 processos criados")
    
    # GRUPO B: Variações de Negócio/Grupo/Subgrupo/Tipo (15 processos)
    print("   📋 Grupo B: Variações de Negócio/Grupo/Subgrupo/Tipo...")
    
    configs_grupo_b = [
        # (processo, nf, dt_emissao, data_aceite, valor, negocio, grupo, subgrupo, tipo, mes)
        ("300011", "348011", "2025-08-05", "2025-06-25", 15000, "SSO", "Analisador Fixo", "Falco", "Produto", "ago"),
        ("300012", "348012", "2025-08-08", "2025-06-28", 8000, "SSO", "Detector Portátil", "MicroClip", "Reposição", "ago"),
        ("300013", "348013", "2025-08-10", "2025-07-01", 5000, "Hidrologia", "Equipamento Amostragem", "ISCO", "Serviço", "ago"),
        ("300014", "348014", "2025-08-12", "2025-07-03", 3000, "Hidrologia", "Sonda Multiparâmetros", "EXO", "Aluguel", "ago"),
        ("300015", "348015", "2025-08-15", "2025-07-05", 25000, "Remediação", "Sistema Remediação", "QED", "Produto", "ago"),
        ("300016", "348016", "2025-08-18", "2025-07-08", 7000, "SSO", "Analisador Fixo", "Falco", "Serviço", "ago"),
        ("300017", "348017", "2025-08-20", "2025-07-10", 12000, "SSO", "Detector Portátil", "MicroClip", "Produto", "ago"),
        ("300018", "348018", "2025-08-22", "2025-07-12", 18000, "Hidrologia", "Equipamento Amostragem", "ISCO", "Produto", "ago"),
        ("300019", "348019", "2025-09-05", "2025-07-25", 9000, "Remediação", "Sistema Remediação", "QED", "Reposição", "set"),
        ("300020", "348020", "2025-09-08", "2025-07-28", 20000, "SSO", "Analisador Portátil", "Innova", "Produto", "set"),
        ("300021", "348021", "2025-09-10", "2025-08-01", 22000, "Hidrologia", "Sonda Multiparâmetros", "EXO", "Produto", "set"),
        ("300022", "348022", "2025-09-12", "2025-08-03", 30000, "Remediação", "Sistema Remediação", "Thermo", "Produto", "set"),
        ("300023", "348023", "2025-09-15", "2025-08-05", 11000, "SSO", "Detector Portátil", "QRAE", "Produto", "set"),
        ("300024", "348024", "2025-09-18", "2025-08-08", 16000, "Hidrologia", "Equipamento Amostragem", "YSI", "Produto", "set"),
        ("300025", "348025", "2025-09-20", "2025-08-10", 6000, "Remediação", "Sistema Remediação", "QED", "Serviço", "set"),
    ]
    
    for config in configs_grupo_b:
        processo, nf, dt_emissao, data_aceite, valor, negocio, grupo, subgrupo, tipo, mes = config
        item = criar_item_faturado(
            processo, nf, dt_emissao, data_aceite, valor,
            consultor_interno="ANDREY.ANDRADE",
            negocio=negocio,
            grupo=grupo,
            subgrupo=subgrupo,
            tipo_merc=tipo
        )
        conversao = criar_conversao(processo, data_aceite, valor, negocio, "ANDREY.ANDRADE")
        
        if mes == "ago":
            faturados_ago.append(item)
            conversoes_ago.append(conversao)
        else:
            faturados_set.append(item)
            conversoes_set.append(conversao)
    
    print(f"   ✅ Grupo B: 15 processos criados")
    
    # GRUPO C: Variação de FC - Componentes Específicos (15 processos)
    print("   📋 Grupo C: Variação de FC - Componentes Específicos...")
    
    # Nota: Os valores de FC serão testados através das metas e realizados nos arquivos YTD
    configs_grupo_c = [
        # Processos para testar faturamento_linha e rentabilidade (Diretor)
        ("300026", "348026", "2025-09-05", "2025-07-25", 15000, "SSO", "Analisador Fixo", "Falco", "Produto", "ANDREY.ANDRADE"),
        ("300027", "348027", "2025-09-08", "2025-07-28", 15000, "SSO", "Detector Portátil", "MicroClip", "Produto", "ANDREY.ANDRADE"),
        ("300028", "348028", "2025-09-10", "2025-08-01", 15000, "Hidrologia", "Equipamento Amostragem", "ISCO", "Produto", "ANDREY.ANDRADE"),
        ("300029", "348029", "2025-09-12", "2025-08-03", 15000, "Remediação", "Sistema Remediação", "QED", "Produto", "ANDREY.ANDRADE"),
        
        # Processos para testar conversao_linha (Gerente Geral)
        ("300030", "348030", "2025-09-15", "2025-08-05", 20000, "SSO", "Analisador Fixo", "Falco", "Produto", "MATEUS.MACHADO"),
        ("300031", "348031", "2025-09-18", "2025-08-08", 20000, "Hidrologia", "Equipamento Amostragem", "YSI", "Produto", "MATEUS.MACHADO"),
        
        # Processos para testar faturamento_individual (Consultor Interno)
        ("300032", "348032", "2025-09-20", "2025-08-10", 10000, "SSO", "Detector Portátil", "MicroClip", "Produto", "ANDREY.ANDRADE"),
        ("300033", "348033", "2025-09-22", "2025-08-12", 10000, "SSO", "Analisador Portátil", "Innova", "Produto", "ANDREY.ANDRADE"),
        
        # Processos para testar conversao_individual (Consultor Interno)
        ("300034", "348034", "2025-09-25", "2025-08-15", 12000, "Hidrologia", "Sonda Multiparâmetros", "EXO", "Produto", "MATEUS.MACHADO"),
        ("300035", "348035", "2025-09-28", "2025-08-18", 12000, "Remediação", "Sistema Remediação", "Thermo", "Produto", "MATEUS.MACHADO"),
        
        # Processos para testar faturamento_individual (Consultor Externo)
        ("300036", "348036", "2025-08-10", "2025-06-30", 18000, "SSO", "Analisador Fixo", "Falco", "Produto", ""),
        ("300037", "348037", "2025-08-15", "2025-07-05", 18000, "Hidrologia", "Equipamento Amostragem", "ISCO", "Produto", ""),
        
        # Processos para testar conversao_individual (Consultor Externo)
        ("300038", "348038", "2025-08-20", "2025-07-10", 14000, "Remediação", "Sistema Remediação", "QED", "Produto", ""),
        ("300039", "348039", "2025-08-25", "2025-07-15", 14000, "SSO", "Detector Portátil", "MicroClip", "Produto", ""),
        
        # Processo mix (Coordenador)
        ("300040", "348040", "2025-08-28", "2025-07-18", 25000, "SSO", "Analisador Fixo", "Falco", "Produto", "ANDREY.ANDRADE"),
    ]
    
    for config in configs_grupo_c:
        processo, nf, dt_emissao, data_aceite, valor, negocio, grupo, subgrupo, tipo, consultor = config
        mes = "ago" if dt_emissao.startswith("2025-08") else "set"
        
        # Para consultores externos, usar representante
        if not consultor:
            consultor_param = ""
            representante_param = "ANDRÉ LUIS GONCALVES CAMARGO"
        else:
            consultor_param = consultor
            representante_param = ""
        
        item = criar_item_faturado(
            processo, nf, dt_emissao, data_aceite, valor,
            consultor_interno=consultor_param,
            representante=representante_param,
            negocio=negocio,
            grupo=grupo,
            subgrupo=subgrupo,
            tipo_merc=tipo
        )
        conversao = criar_conversao(processo, data_aceite, valor, negocio, consultor_param)
        
        if mes == "ago":
            faturados_ago.append(item)
            conversoes_ago.append(conversao)
        else:
            faturados_set.append(item)
            conversoes_set.append(conversao)
    
    print(f"   ✅ Grupo C: 15 processos criados")
    
    # GRUPO D: Valores Extremos e Limites (10 processos)
    print("   📋 Grupo D: Valores Extremos e Limites...")
    
    configs_grupo_d = [
        ("300041", "348041", "2025-08-05", "2025-06-25", 100, "SSO", "Analisador Fixo", "Falco", "Produto"),
        ("300042", "348042", "2025-08-08", "2025-06-28", 10000, "SSO", "Detector Portátil", "MicroClip", "Produto"),
        ("300043", "348043", "2025-08-10", "2025-07-01", 100000, "Hidrologia", "Equipamento Amostragem", "ISCO", "Produto"),
        ("300044", "348044", "2025-08-12", "2025-07-03", 500000, "Remediação", "Sistema Remediação", "QED", "Produto"),
        ("300045", "348045", "2025-08-15", "2025-07-05", 15000, "SSO", "Analisador Fixo", "Falco", "Produto"),
        ("300046", "348046", "2025-08-18", "2025-07-08", 15000, "Hidrologia", "Equipamento Amostragem", "YSI", "Produto"),
        ("300047", "348047", "2025-08-20", "2025-07-10", 15000, "Remediação", "Sistema Remediação", "Thermo", "Produto"),
        ("300048", "348048", "2025-08-22", "2025-07-12", 15000, "SSO", "Detector Portátil", "QRAE", "Produto"),
        ("300049", "348049", "2025-08-25", "2025-07-15", 15000, "Hidrologia", "Sonda Multiparâmetros", "EXO", "Produto"),
        ("300050", "348050", "2025-08-28", "2025-07-18", 20000, "SSO", "Analisador Fixo", "Falco", "Produto"),
    ]
    
    for config in configs_grupo_d:
        processo, nf, dt_emissao, data_aceite, valor, negocio, grupo, subgrupo, tipo = config
        item = criar_item_faturado(
            processo, nf, dt_emissao, data_aceite, valor,
            consultor_interno="ANDREY.ANDRADE",
            negocio=negocio,
            grupo=grupo,
            subgrupo=subgrupo,
            tipo_merc=tipo
        )
        conversao = criar_conversao(processo, data_aceite, valor, negocio, "ANDREY.ANDRADE")
        faturados_ago.append(item)
        conversoes_ago.append(conversao)
    
    print(f"   ✅ Grupo D: 10 processos criados")
    print(f"✅ BLOCO 1 COMPLETO: 50 processos de faturamento criados")
    print()
    
    # ==================== BLOCO 2: CROSS-SELLING (400001-400010) ====================
    print("📦 BLOCO 2: Cross-Selling (400001-400010)")
    
    # Processo 400001: SSO + Hidrologia (André Camargo como Gerente Comercial)
    faturados_ago.append(criar_item_faturado(
        "400001", "448001", "2025-08-10", "2025-06-30",
        10000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto"
    ))
    faturados_ago.append(criar_item_faturado(
        "400001", "448001", "2025-08-10", "2025-06-30",
        8000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="ISCO",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("400001", "2025-06-30", 18000, "SSO", "ANDREY.ANDRADE"))
    
    # Processo 400002: SSO + Remediação (Leonardo Camargo)
    faturados_ago.append(criar_item_faturado(
        "400002", "448002", "2025-08-15", "2025-07-05",
        12000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="LEONARDO CAMARGO",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="MicroClip",
        tipo_merc="Produto"
    ))
    faturados_ago.append(criar_item_faturado(
        "400002", "448002", "2025-08-15", "2025-07-05",
        10000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="LEONARDO CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("400002", "2025-07-05", 22000, "SSO", "MATEUS.MACHADO"))
    
    # Processo 400003: Hidrologia + SSO + Remediação (Mateus Machado - 3 linhas!)
    faturados_ago.append(criar_item_faturado(
        "400003", "448003", "2025-08-20", "2025-07-10",
        15000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="MATEUS.MACHADO",
        negocio="Hidrologia",
        grupo="Sonda Multiparâmetros",
        subgrupo="EXO",
        tipo_merc="Produto"
    ))
    faturados_ago.append(criar_item_faturado(
        "400003", "448003", "2025-08-20", "2025-07-10",
        5000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="MATEUS.MACHADO",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto"
    ))
    faturados_ago.append(criar_item_faturado(
        "400003", "448003", "2025-08-20", "2025-07-10",
        8000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="MATEUS.MACHADO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="Thermo",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("400003", "2025-07-10", 28000, "Hidrologia", "ANDREY.ANDRADE"))
    
    # Processo 400004: SSO + Hidrologia (André Camargo)
    faturados_set.append(criar_item_faturado(
        "400004", "448004", "2025-09-05", "2025-07-25",
        20000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="SSO",
        grupo="Analisador Portátil",
        subgrupo="Innova",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400004", "448004", "2025-09-05", "2025-07-25",
        15000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="YSI",
        tipo_merc="Produto"
    ))
    conversoes_ago.append(criar_conversao("400004", "2025-07-25", 35000, "SSO", "MATEUS.MACHADO"))
    
    # Processo 400005: Remediação + SSO (Leonardo Camargo)
    faturados_set.append(criar_item_faturado(
        "400005", "448005", "2025-09-10", "2025-08-01",
        18000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="LEONARDO CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400005", "448005", "2025-09-10", "2025-08-01",
        7000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="LEONARDO CAMARGO",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="QRAE",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("400005", "2025-08-01", 25000, "Remediação", "ANDREY.ANDRADE"))
    
    # Processo 400006: SSO + SSO + Hidrologia (Mateus Machado)
    faturados_set.append(criar_item_faturado(
        "400006", "448006", "2025-09-15", "2025-08-05",
        10000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="MATEUS.MACHADO",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400006", "448006", "2025-09-15", "2025-08-05",
        10000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="MATEUS.MACHADO",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="MicroClip",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400006", "448006", "2025-09-15", "2025-08-05",
        10000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="MATEUS.MACHADO",
        negocio="Hidrologia",
        grupo="Sonda Multiparâmetros",
        subgrupo="EXO",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("400006", "2025-08-05", 30000, "SSO", "MATEUS.MACHADO"))
    
    # Processo 400007: Hidrologia + Remediação (André Camargo)
    faturados_set.append(criar_item_faturado(
        "400007", "448007", "2025-09-20", "2025-08-10",
        12000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="ISCO",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400007", "448007", "2025-09-20", "2025-08-10",
        12000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="Thermo",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("400007", "2025-08-10", 24000, "Hidrologia", "ANDREY.ANDRADE"))
    
    # Processo 400008: SSO apenas (Leonardo Camargo - teste de não cross-selling)
    faturados_set.append(criar_item_faturado(
        "400008", "448008", "2025-09-22", "2025-08-12",
        25000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="LEONARDO CAMARGO",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("400008", "2025-08-12", 25000, "SSO", "MATEUS.MACHADO"))
    
    # Processo 400009: Hidrologia + SSO + Remediação (Mateus Machado - 3 linhas)
    faturados_set.append(criar_item_faturado(
        "400009", "448009", "2025-09-25", "2025-08-15",
        8000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="MATEUS.MACHADO",
        negocio="Hidrologia",
        grupo="Sonda Multiparâmetros",
        subgrupo="EXO",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400009", "448009", "2025-09-25", "2025-08-15",
        8000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="MATEUS.MACHADO",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="QRAE",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400009", "448009", "2025-09-25", "2025-08-15",
        8000,
        consultor_interno="ANDREY.ANDRADE",
        gerente_comercial="MATEUS.MACHADO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("400009", "2025-08-15", 24000, "Hidrologia", "ANDREY.ANDRADE"))
    
    # Processo 400010: Remediação + Hidrologia (André Camargo)
    faturados_set.append(criar_item_faturado(
        "400010", "448010", "2025-09-28", "2025-08-18",
        20000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto"
    ))
    faturados_set.append(criar_item_faturado(
        "400010", "448010", "2025-09-28", "2025-08-18",
        15000,
        consultor_interno="MATEUS.MACHADO",
        gerente_comercial="ANDRÉ LUIS GONCALVES CAMARGO",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="YSI",
        tipo_merc="Produto"
    ))
    conversoes_set.append(criar_conversao("400010", "2025-08-18", 35000, "Remediação", "MATEUS.MACHADO"))
    
    print(f"✅ BLOCO 2 COMPLETO: 10 processos de cross-selling criados")
    print()
    
    # ==================== BLOCO 3: FC FORNECEDORES (500001-500015) ====================
    print("📦 BLOCO 3: FC Fornecedores (500001-500015)")
    
    # Taxa de câmbio média (simulada)
    taxa_usd = 5.0  # 1 USD = 5 BRL
    taxa_gbp = 6.5  # 1 GBP = 6.5 BRL
    
    configs_fornecedores = [
        # (processo, nf, dt_emissao, data_aceite, valor_brl, fabricante, moeda, negocio, grupo, subgrupo, mes)
        ("500001", "548001", "2025-08-15", "2025-07-05", 30000, "YSI", "USD", "Hidrologia", "Equipamento Amostragem", "YSI", "ago"),
        ("500002", "548002", "2025-08-18", "2025-07-08", 25000, "ISCO", "USD", "Hidrologia", "Equipamento Amostragem", "ISCO", "ago"),
        ("500003", "548003", "2025-08-20", "2025-07-10", 35000, "QED", "USD", "Remediação", "Sistema Remediação", "QED", "ago"),
        ("500004", "548004", "2025-08-22", "2025-07-12", 40000, "Thermo", "USD", "Remediação", "Sistema Remediação", "Thermo", "ago"),
        ("500005", "548005", "2025-08-25", "2025-07-15", 28000, "HON", "USD", "SSO", "Analisador Fixo", "Falco", "ago"),
        ("500006", "548006", "2025-08-28", "2025-07-18", 32000, "ION", "GBP", "SSO", "Detector Portátil", "MicroClip", "ago"),
        ("500007", "548007", "2025-09-05", "2025-07-25", 50000, "YSI", "USD", "Hidrologia", "Equipamento Amostragem", "YSI", "set"),
        ("500008", "548008", "2025-09-08", "2025-07-28", 45000, "ISCO", "USD", "Hidrologia", "Equipamento Amostragem", "ISCO", "set"),
        ("500009", "548009", "2025-09-10", "2025-08-01", 60000, "QED", "USD", "Remediação", "Sistema Remediação", "QED", "set"),
        ("500010", "548010", "2025-09-12", "2025-08-03", 55000, "Thermo", "USD", "Remediação", "Sistema Remediação", "Thermo", "set"),
        ("500011", "548011", "2025-09-15", "2025-08-05", 38000, "HON", "USD", "SSO", "Analisador Fixo", "Falco", "set"),
        ("500012", "548012", "2025-09-18", "2025-08-08", 42000, "ION", "GBP", "SSO", "Detector Portátil", "MicroClip", "set"),
    ]
    
    for config in configs_fornecedores:
        processo, nf, dt_emissao, data_aceite, valor_brl, fabricante, moeda, negocio, grupo, subgrupo, mes = config
        
        # Adicionar item faturado (sempre com Alessandro Cappi para testar FC de fornecedores - Gerente Linha)
        item = criar_item_faturado(
            processo, nf, dt_emissao, data_aceite, valor_brl,
            consultor_interno="Alessandro Cappi",
            negocio=negocio,
            grupo=grupo,
            subgrupo=subgrupo,
            tipo_merc="Produto",
            fabricante=fabricante
        )
        conversao = criar_conversao(processo, data_aceite, valor_brl, negocio, "Alessandro Cappi")
        
        if mes == "ago":
            faturados_ago.append(item)
            conversoes_ago.append(conversao)
        else:
            faturados_set.append(item)
            conversoes_set.append(conversao)
        
        # Adicionar venda de fornecedor em moeda nativa
        valor_moeda_nativa = valor_brl / (taxa_usd if moeda == "USD" else taxa_gbp)
        vendas_fornecedores.append({
            "mes_ano": f"08/2025" if mes == "ago" else "09/2025",
            "fabricante": fabricante,
            "moeda": moeda,
            "valor_moeda_nativa": round(valor_moeda_nativa, 2),
            "valor_brl": valor_brl,
            "taxa_cambio": taxa_usd if moeda == "USD" else taxa_gbp
        })
    
    # Processos 500013-500015: Múltiplos fabricantes no mesmo processo
    # Processo 500013: YSI + ISCO (ambos USD, Hidrologia)
    faturados_set.append(criar_item_faturado(
        "500013", "548013", "2025-09-20", "2025-08-10",
        35000,
        consultor_interno="Alessandro Cappi",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="YSI",
        tipo_merc="Produto",
        fabricante="YSI"
    ))
    faturados_set.append(criar_item_faturado(
        "500013", "548013", "2025-09-20", "2025-08-10",
        35000,
        consultor_interno="Alessandro Cappi",
        negocio="Hidrologia",
        grupo="Equipamento Amostragem",
        subgrupo="ISCO",
        tipo_merc="Produto",
        fabricante="ISCO"
    ))
    conversoes_set.append(criar_conversao("500013", "2025-08-10", 70000, "Hidrologia", "Alessandro Cappi"))
    vendas_fornecedores.append({
        "mes_ano": "09/2025",
        "fabricante": "YSI",
        "moeda": "USD",
        "valor_moeda_nativa": round(35000 / taxa_usd, 2),
        "valor_brl": 35000,
        "taxa_cambio": taxa_usd
    })
    vendas_fornecedores.append({
        "mes_ano": "09/2025",
        "fabricante": "ISCO",
        "moeda": "USD",
        "valor_moeda_nativa": round(35000 / taxa_usd, 2),
        "valor_brl": 35000,
        "taxa_cambio": taxa_usd
    })
    
    # Processo 500014: QED + Thermo (ambos USD, Remediação)
    faturados_set.append(criar_item_faturado(
        "500014", "548014", "2025-09-22", "2025-08-12",
        40000,
        consultor_interno="Alessandro Cappi",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="QED",
        tipo_merc="Produto",
        fabricante="QED"
    ))
    faturados_set.append(criar_item_faturado(
        "500014", "548014", "2025-09-22", "2025-08-12",
        40000,
        consultor_interno="Alessandro Cappi",
        negocio="Remediação",
        grupo="Sistema Remediação",
        subgrupo="Thermo",
        tipo_merc="Produto",
        fabricante="Thermo"
    ))
    conversoes_set.append(criar_conversao("500014", "2025-08-12", 80000, "Remediação", "Alessandro Cappi"))
    vendas_fornecedores.append({
        "mes_ano": "09/2025",
        "fabricante": "QED",
        "moeda": "USD",
        "valor_moeda_nativa": round(40000 / taxa_usd, 2),
        "valor_brl": 40000,
        "taxa_cambio": taxa_usd
    })
    vendas_fornecedores.append({
        "mes_ano": "09/2025",
        "fabricante": "Thermo",
        "moeda": "USD",
        "valor_moeda_nativa": round(40000 / taxa_usd, 2),
        "valor_brl": 40000,
        "taxa_cambio": taxa_usd
    })
    
    # Processo 500015: HON (USD) + ION (GBP) - Mix de moedas, SSO
    faturados_set.append(criar_item_faturado(
        "500015", "548015", "2025-09-25", "2025-08-15",
        37500,
        consultor_interno="Alessandro Cappi",
        negocio="SSO",
        grupo="Analisador Fixo",
        subgrupo="Falco",
        tipo_merc="Produto",
        fabricante="HON"
    ))
    faturados_set.append(criar_item_faturado(
        "500015", "548015", "2025-09-25", "2025-08-15",
        37500,
        consultor_interno="Alessandro Cappi",
        negocio="SSO",
        grupo="Detector Portátil",
        subgrupo="MicroClip",
        tipo_merc="Produto",
        fabricante="ION"
    ))
    conversoes_set.append(criar_conversao("500015", "2025-08-15", 75000, "SSO", "Alessandro Cappi"))
    vendas_fornecedores.append({
        "mes_ano": "09/2025",
        "fabricante": "HON",
        "moeda": "USD",
        "valor_moeda_nativa": round(37500 / taxa_usd, 2),
        "valor_brl": 37500,
        "taxa_cambio": taxa_usd
    })
    vendas_fornecedores.append({
        "mes_ano": "09/2025",
        "fabricante": "ION",
        "moeda": "GBP",
        "valor_moeda_nativa": round(37500 / taxa_gbp, 2),
        "valor_brl": 37500,
        "taxa_cambio": taxa_gbp
    })
    
    print(f"✅ BLOCO 3 COMPLETO: 15 processos de FC fornecedores criados")
    print()
    
    # ==================== CRIAR DATAFRAMES ====================
    print("📊 Criando DataFrames...")
    
    df_faturados_ago = pd.DataFrame(faturados_ago)
    df_faturados_set = pd.DataFrame(faturados_set)
    df_conversoes_ago = pd.DataFrame(conversoes_ago)
    df_conversoes_set = pd.DataFrame(conversoes_set)
    df_vendas_fornecedores = pd.DataFrame(vendas_fornecedores)
    
    print(f"   ✅ Faturados Agosto: {len(df_faturados_ago)} linhas")
    print(f"   ✅ Faturados Setembro: {len(df_faturados_set)} linhas")
    print(f"   ✅ Conversões Agosto: {len(df_conversoes_ago)} linhas")
    print(f"   ✅ Conversões Setembro: {len(df_conversoes_set)} linhas")
    print(f"   ✅ Vendas Fornecedores: {len(df_vendas_fornecedores)} linhas")
    print()
    
    # ==================== SALVAR ARQUIVOS ====================
    print("💾 Salvando arquivos...")
    
    # Criar diretório
    os.makedirs("dados_entrada", exist_ok=True)
    
    # Salvar Faturados
    df_faturados_ago.to_excel("dados_entrada/Faturados_08_2025.xlsx", index=False, sheet_name="Dados")
    print(f"   ✅ Faturados Agosto salvos: dados_entrada/Faturados_08_2025.xlsx")
    
    df_faturados_set.to_excel("dados_entrada/Faturados_09_2025.xlsx", index=False, sheet_name="Dados")
    print(f"   ✅ Faturados Setembro salvos: dados_entrada/Faturados_09_2025.xlsx")
    
    # Salvar Conversões
    df_conversoes_ago.to_excel("dados_entrada/Conversões_08_2025.xlsx", index=False, sheet_name="Dados")
    print(f"   ✅ Conversões Agosto salvas: dados_entrada/Conversões_08_2025.xlsx")
    
    df_conversoes_set.to_excel("dados_entrada/Conversões_09_2025.xlsx", index=False, sheet_name="Dados")
    print(f"   ✅ Conversões Setembro salvas: dados_entrada/Conversões_09_2025.xlsx")
    
    # Salvar Vendas Fornecedores
    df_vendas_fornecedores.to_excel("dados_entrada/vendas_fornecedores_moeda_nativa.xlsx", index=False, sheet_name="Dados")
    print(f"   ✅ Vendas Fornecedores salvas: dados_entrada/vendas_fornecedores_moeda_nativa.xlsx")
    
    print()
    print("=" * 80)
    print("✅ ARQUIVOS GERADOS COM SUCESSO!")
    print("=" * 80)
    print()
    print("📊 RESUMO:")
    print(f"   - Total de processos NOVOS: 75")
    print(f"     • Faturamento: 50 processos (300001-300050)")
    print(f"     • Cross-Selling: 10 processos (400001-400010)")
    print(f"     • FC Fornecedores: 15 processos (500001-500015)")
    print(f"   - Total de linhas (Faturados Agosto): {len(df_faturados_ago)}")
    print(f"   - Total de linhas (Faturados Setembro): {len(df_faturados_set)}")
    print(f"   - Total de linhas (Conversões Agosto): {len(df_conversoes_ago)}")
    print(f"   - Total de linhas (Conversões Setembro): {len(df_conversoes_set)}")
    print()
    print("🎯 PRÓXIMOS PASSOS:")
    print("   1. Executar: python calculo_comissoes.py --mes 8 --ano 2025")
    print("   2. Executar: python calculo_comissoes.py --mes 9 --ano 2025")
    print("   3. Validar comissões por faturamento")
    print("   4. Validar cross-selling")
    print("   5. Validar FC de fornecedores nas reconciliações")
    print()
    print("=" * 80)


if __name__ == "__main__":
    gerar_dados_faturamento_completo()

