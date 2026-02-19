"""
Constantes com dados reais da empresa para testes.

Todos os nomes de linhas, grupos, subgrupos, fabricantes, consultores e cargos
são baseados nos dados reais do ERP, garantindo que os testes reflitam cenários
plausíveis da operação diária.
"""

# =============================================================================
# LINHAS DE NEGÓCIO
# =============================================================================
LINHAS = [
    "Hidrologia",
    "SSO",
    "Remediação",
    "Saneamento",
    "Locação",
    "Diversos",
]

# =============================================================================
# GRUPOS POR LINHA
# =============================================================================
GRUPOS_POR_LINHA = {
    "Hidrologia": [
        "Sonda Serie EXO",
        "Medidor de Vazão Fixo",
        "Medidor de Vazão Portátil",
        "Sonda Multiparâmetro",
        "Nível",
        "Amostrador",
    ],
    "SSO": [
        "Monitor de Gases Fixo",
        "Monitor de Gases Portátil",
        "Detector Fotoionização",
        "Equipamento de Proteção",
    ],
    "Remediação": [
        "Bomba Submersível",
        "Sistema de Extração",
        "Equipamento de Campo",
    ],
    "Saneamento": [
        "Medidor de Vazão Industrial",
        "Sensor de Qualidade",
    ],
    "Locação": [
        "Equipamento de Locação",
    ],
    "Diversos": [
        "Acessórios",
        "Peças de Reposição",
    ],
}

# =============================================================================
# SUBGRUPOS
# =============================================================================
SUBGRUPOS = {
    "Sonda Serie EXO": ["EXO", "EXO1", "EXO2", "EXO3"],
    "Medidor de Vazão Fixo": ["IQ Standard", "IQ Plus", "IQ Premium"],
    "Monitor de Gases Fixo": ["RAE", "RAE Pro"],
    "Bomba Submersível": ["QED", "QED Plus"],
}

# Subgrupo default quando não há subgrupo específico
SUBGRUPO_DEFAULT = "Geral"

# =============================================================================
# TIPOS DE MERCADORIA
# =============================================================================
TIPOS_MERCADORIA = [
    "Produto",
    "Serviço",
    "Reposição",
    "Insumo",
    "Aluguel",
]

# =============================================================================
# FABRICANTES E MOEDAS
# =============================================================================
FABRICANTES = {
    "YSI": {"moeda": "USD", "linha": "Hidrologia"},
    "ISCO": {"moeda": "USD", "linha": "Hidrologia"},
    "QED": {"moeda": "USD", "linha": "Remediação"},
    "Thermo": {"moeda": "USD", "linha": "SSO"},
    "HON": {"moeda": "USD", "linha": "SSO"},
    "ION": {"moeda": "GBP", "linha": "SSO"},
}

# =============================================================================
# CARGOS
# =============================================================================
CARGOS_GESTAO = [
    "Gerente Linha",
    "Coordenador",
    "Diretor",
]

CARGOS_OPERACIONAL = [
    "Consultor Interno",
    "Consultor Externo",
]

TODOS_CARGOS = CARGOS_GESTAO + CARGOS_OPERACIONAL

# Tipo de comissão por cargo (padrão)
TIPO_COMISSAO_POR_CARGO = {
    "Gerente Linha": "faturamento",
    "Coordenador": "faturamento",
    "Diretor": "faturamento",
    "Consultor Interno": "faturamento",
    "Consultor Externo": "faturamento",
}

# =============================================================================
# COLABORADORES (nomes canônicos)
# =============================================================================
COLABORADORES = {
    # Gestão
    "Andrey Andrade": {"cargo": "Gerente Linha", "tipo": "gestao", "linhas": ["Hidrologia"]},
    "Dener Martins": {"cargo": "Gerente Linha", "tipo": "gestao", "linhas": ["SSO"]},
    "Rosana Martins": {"cargo": "Coordenador", "tipo": "gestao", "linhas": ["Hidrologia", "SSO"]},
    "Juliano Pereira": {"cargo": "Coordenador", "tipo": "gestao", "linhas": ["Remediação"]},
    "Carlos Diretor": {"cargo": "Diretor", "tipo": "gestao", "linhas": ["Hidrologia", "SSO", "Remediação"]},
    # Operacional (internos)
    "Samanta Silva": {"cargo": "Consultor Interno", "tipo": "operacional", "linhas": ["Hidrologia"]},
    "Rafaela Meirelles": {"cargo": "Consultor Interno", "tipo": "operacional", "linhas": ["SSO"]},
    "Rosilene Costa": {"cargo": "Consultor Interno", "tipo": "operacional", "linhas": ["Remediação"]},
    # Operacional (externos)
    "André Camargo": {"cargo": "Consultor Externo", "tipo": "operacional", "linhas": []},
    "Leonardo Carmo": {"cargo": "Consultor Externo", "tipo": "operacional", "linhas": []},
    "Mateus Machado": {"cargo": "Consultor Externo", "tipo": "operacional", "linhas": []},
}

# =============================================================================
# ALIASES (ERP → canônico)
# =============================================================================
ALIASES = {
    "ANDREY.ANDRADE": "Andrey Andrade",
    "DENER.MARTINS": "Dener Martins",
    "SAMANTA": "Samanta Silva",
    "ROSANA.MARTINS": "Rosana Martins",
    "JULIANO": "Juliano Pereira",
    "RAFAELA.MEIRELLES": "Rafaela Meirelles",
    "ROSILENE": "Rosilene Costa",
    "ANDRÉ LUIS GONCALVES CAMARGO": "André Camargo",
    "LEONARDO DO CARMO": "Leonardo Carmo",
    "MATEUS BORRO MACHADO": "Mateus Machado",
}

# =============================================================================
# TAXAS DE CÂMBIO DE TESTE (mensais, média BCB simulada)
# =============================================================================
TAXAS_CAMBIO_TESTE = {
    "USD": {
        "2025": {
            "1": 4.95, "2": 4.98, "3": 5.01, "4": 5.10,
            "5": 5.05, "6": 5.12, "7": 5.08, "8": 5.15,
            "9": 5.20, "10": 5.18, "11": 5.22, "12": 5.25,
        }
    },
    "GBP": {
        "2025": {
            "1": 6.20, "2": 6.25, "3": 6.30, "4": 6.35,
            "5": 6.28, "6": 6.32, "7": 6.40, "8": 6.38,
            "9": 6.45, "10": 6.42, "11": 6.50, "12": 6.55,
        }
    },
}

# =============================================================================
# PARÂMETROS PADRÃO (PARAMS)
# =============================================================================
PARAMS_DEFAULT = {
    "cap_atingimento_max": 1.0,
    "cap_fc_max": 1.0,
    "cross_selling_default_option": "A",
    "legacy_scope_token": "__legacy__",
}

# =============================================================================
# PESOS PADRÃO DO FC POR CARGO (somam 100%)
# =============================================================================
PESOS_FC_POR_CARGO = {
    "Gerente Linha": {
        "faturamento_linha": 0.30,
        "conversao_linha": 0.20,
        "faturamento_individual": 0.0,
        "conversao_individual": 0.0,
        "rentabilidade": 0.25,
        "retencao_clientes": 0.10,
        "meta_fornecedor_1": 0.10,
        "meta_fornecedor_2": 0.05,
    },
    "Coordenador": {
        "faturamento_linha": 0.25,
        "conversao_linha": 0.20,
        "faturamento_individual": 0.0,
        "conversao_individual": 0.0,
        "rentabilidade": 0.30,
        "retencao_clientes": 0.0,
        "meta_fornecedor_1": 0.15,
        "meta_fornecedor_2": 0.10,
    },
    "Diretor": {
        "faturamento_linha": 0.30,
        "conversao_linha": 0.20,
        "faturamento_individual": 0.0,
        "conversao_individual": 0.0,
        "rentabilidade": 0.30,
        "retencao_clientes": 0.0,
        "meta_fornecedor_1": 0.10,
        "meta_fornecedor_2": 0.10,
    },
    "Consultor Interno": {
        "faturamento_linha": 0.15,
        "conversao_linha": 0.10,
        "faturamento_individual": 0.25,
        "conversao_individual": 0.15,
        "rentabilidade": 0.20,
        "retencao_clientes": 0.0,
        "meta_fornecedor_1": 0.10,
        "meta_fornecedor_2": 0.05,
    },
    "Consultor Externo": {
        "faturamento_linha": 0.10,
        "conversao_linha": 0.05,
        "faturamento_individual": 0.30,
        "conversao_individual": 0.20,
        "rentabilidade": 0.15,
        "retencao_clientes": 0.0,
        "meta_fornecedor_1": 0.10,
        "meta_fornecedor_2": 0.10,
    },
}

# =============================================================================
# CONFIGURAÇÃO DE ESCADA POR CARGO (para testes)
# =============================================================================
FC_ESCADA_CONFIGS = {
    "Gerente Linha": {"modo": "ESCADA", "num_degraus": 4, "piso_pct": 50},
    "Coordenador": {"modo": "ESCADA", "num_degraus": 3, "piso_pct": 60},
    "Diretor": {"modo": "RAMPA", "num_degraus": 2, "piso_pct": 0},
    "Consultor Interno": {"modo": "ESCADA", "num_degraus": 5, "piso_pct": 40},
    "Consultor Externo": {"modo": "RAMPA", "num_degraus": 2, "piso_pct": 0},
}
