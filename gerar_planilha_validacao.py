"""
Gera planilha com valores esperados para validação dos testes.
"""

import pandas as pd
from datetime import datetime

def gerar_planilha_validacao():
    """Gera planilha Excel com valores esperados para cada cenário."""
    
    print("Gerando planilha de validação...")
    
    # ==================== CENÁRIOS ====================
    cenarios = [
        {
            "Cenário": 1,
            "Processo": "100001",
            "Descrição": "Adiantamento simples (não faturado)",
            "Mês_Teste": "Agosto",
            "Valor_Adiantamento": 5000.00,
            "Qtd_Adiantamentos": 1,
            "Valor_Pagamento_Regular": 0,
            "Qtd_Pagamentos_Regulares": 0,
            "Status_Faturamento": "PENDENTE",
            "Tem_Reconciliação": "Não",
            "Reconciliação_Esperada": 0,
            "Observações": "Processo não faturado. SEM reconciliação."
        },
        {
            "Cenário": 2,
            "Processo": "100002",
            "Descrição": "Adiantamento + Faturamento (mesmo mês)",
            "Mês_Teste": "Agosto",
            "Valor_Adiantamento": 7500.00,
            "Qtd_Adiantamentos": 1,
            "Valor_Pagamento_Regular": 7500.00,
            "Qtd_Pagamentos_Regulares": 1,
            "Status_Faturamento": "FATURADO",
            "Tem_Reconciliação": "Sim",
            "Reconciliação_Esperada": "Negativa",
            "Observações": "FCMP < 1.0 (RENTAL). Reconciliação negativa."
        },
        {
            "Cenário": 3,
            "Processo": "100003",
            "Descrição": "Adiantamento (Ago) + Faturamento (Set)",
            "Mês_Teste": "Ago→Set",
            "Valor_Adiantamento": 10000.00,
            "Qtd_Adiantamentos": 1,
            "Valor_Pagamento_Regular": 10000.00,
            "Qtd_Pagamentos_Regulares": 1,
            "Status_Faturamento": "FATURADO (Set)",
            "Tem_Reconciliação": "Sim (Set)",
            "Reconciliação_Esperada": "Negativa",
            "Observações": "Reconciliação aparece SOMENTE em Setembro."
        },
        {
            "Cenário": 4,
            "Processo": "100004",
            "Descrição": "Múltiplos adiantamentos",
            "Mês_Teste": "Ago→Set",
            "Valor_Adiantamento": 15000.00,
            "Qtd_Adiantamentos": 2,
            "Valor_Pagamento_Regular": 10000.00,
            "Qtd_Pagamentos_Regulares": 1,
            "Status_Faturamento": "FATURADO (Set)",
            "Tem_Reconciliação": "Sim (Set)",
            "Reconciliação_Esperada": "Negativa",
            "Observações": "Soma de 2 adiantamentos: R$ 8k + R$ 7k = R$ 15k"
        },
        {
            "Cenário": 5,
            "Processo": "100005",
            "Descrição": "Pagamento regular direto",
            "Mês_Teste": "Agosto",
            "Valor_Adiantamento": 0,
            "Qtd_Adiantamentos": 0,
            "Valor_Pagamento_Regular": 12000.00,
            "Qtd_Pagamentos_Regulares": 2,
            "Status_Faturamento": "FATURADO",
            "Tem_Reconciliação": "Não",
            "Reconciliação_Esperada": 0,
            "Observações": "Sem adiantamento prévio. SEM reconciliação."
        },
        {
            "Cenário": 6,
            "Processo": "100006",
            "Descrição": "Múltiplos colaboradores",
            "Mês_Teste": "Ago→Set",
            "Valor_Adiantamento": 15000.00,
            "Qtd_Adiantamentos": 1,
            "Valor_Pagamento_Regular": 15000.00,
            "Qtd_Pagamentos_Regulares": 1,
            "Status_Faturamento": "FATURADO (Set)",
            "Tem_Reconciliação": "Sim (Set)",
            "Reconciliação_Esperada": "2 linhas (uma por colab)",
            "Observações": "Alessandro Cappi + Leandro Daher"
        },
        {
            "Cenário": 7,
            "Processo": "100007",
            "Descrição": "FC = 1.0 (sem reconciliação)",
            "Mês_Teste": "Ago→Set",
            "Valor_Adiantamento": 15000.00,
            "Qtd_Adiantamentos": 1,
            "Valor_Pagamento_Regular": 15000.00,
            "Qtd_Pagamentos_Regulares": 1,
            "Status_Faturamento": "FATURADO (Set)",
            "Tem_Reconciliação": "Não",
            "Reconciliação_Esperada": 0,
            "Observações": "VENDA pura. FCMP = 1.0. SEM reconciliação."
        },
        {
            "Cenário": 8,
            "Processo": "100008",
            "Descrição": "Múltiplos pagamentos regulares",
            "Mês_Teste": "Agosto",
            "Valor_Adiantamento": 0,
            "Qtd_Adiantamentos": 0,
            "Valor_Pagamento_Regular": 50000.00,
            "Qtd_Pagamentos_Regulares": 3,
            "Status_Faturamento": "FATURADO",
            "Tem_Reconciliação": "Não",
            "Reconciliação_Esperada": 0,
            "Observações": "3 parcelas: R$ 15k, R$ 20k, R$ 15k"
        },
        {
            "Cenário": 9,
            "Processo": "100009",
            "Descrição": "NF com 5 dígitos",
            "Mês_Teste": "Agosto",
            "Valor_Adiantamento": 0,
            "Qtd_Adiantamentos": 0,
            "Valor_Pagamento_Regular": 8000.00,
            "Qtd_Pagamentos_Regulares": 2,
            "Status_Faturamento": "FATURADO",
            "Tem_Reconciliação": "Não",
            "Reconciliação_Esperada": 0,
            "Observações": "NF: 12345 (5 dígitos). Teste de mapeamento."
        },
        {
            "Cenário": 10,
            "Processo": "100010",
            "Descrição": "Múltiplos itens (média ponderada)",
            "Mês_Teste": "Ago→Set",
            "Valor_Adiantamento": 45000.00,
            "Qtd_Adiantamentos": 1,
            "Valor_Pagamento_Regular": 45000.00,
            "Qtd_Pagamentos_Regulares": 1,
            "Status_Faturamento": "FATURADO (Set)",
            "Tem_Reconciliação": "Sim (Set)",
            "Reconciliação_Esperada": "Negativa",
            "Observações": "3 itens: R$ 40k + R$ 30k + R$ 20k. TCMP e FCMP ponderados."
        },
    ]
    
    df_cenarios = pd.DataFrame(cenarios)
    
    # ==================== DOCUMENTOS ====================
    documentos = [
        {
            "Documento": "COT100001",
            "Tipo": "Adiantamento",
            "Valor": 5000.00,
            "Data": "2025-08-10",
            "Processo": "100001",
            "Mapeado": "Sim",
            "Observação": "Adiantamento simples"
        },
        {
            "Documento": "COT100002",
            "Tipo": "Adiantamento",
            "Valor": 7500.00,
            "Data": "2025-08-05",
            "Processo": "100002",
            "Mapeado": "Sim",
            "Observação": ""
        },
        {
            "Documento": "048001",
            "Tipo": "Pagamento Regular",
            "Valor": 7500.00,
            "Data": "2025-08-28",
            "Processo": "100002",
            "Mapeado": "Sim",
            "Observação": "NF 6 dígitos"
        },
        {
            "Documento": "COT100003",
            "Tipo": "Adiantamento",
            "Valor": 10000.00,
            "Data": "2025-08-12",
            "Processo": "100003",
            "Mapeado": "Sim",
            "Observação": ""
        },
        {
            "Documento": "048002",
            "Tipo": "Pagamento Regular",
            "Valor": 10000.00,
            "Data": "2025-09-15",
            "Processo": "100003",
            "Mapeado": "Sim",
            "Observação": ""
        },
        {
            "Documento": "COT100004",
            "Tipo": "Adiantamento",
            "Valor": 8000.00,
            "Data": "2025-08-08",
            "Processo": "100004",
            "Mapeado": "Sim",
            "Observação": "1º adiantamento"
        },
        {
            "Documento": "COT100004",
            "Tipo": "Adiantamento",
            "Valor": 7000.00,
            "Data": "2025-08-15",
            "Processo": "100004",
            "Mapeado": "Sim",
            "Observação": "2º adiantamento (mesmo processo)"
        },
        {
            "Documento": "048003",
            "Tipo": "Pagamento Regular",
            "Valor": 10000.00,
            "Data": "2025-09-20",
            "Processo": "100004",
            "Mapeado": "Sim",
            "Observação": ""
        },
        {
            "Documento": "12345",
            "Tipo": "Pagamento Regular",
            "Valor": 4000.00,
            "Data": "2025-08-20",
            "Processo": "100009",
            "Mapeado": "Sim",
            "Observação": "NF com 5 dígitos (1ª parcela)"
        },
        {
            "Documento": "12345",
            "Tipo": "Pagamento Regular",
            "Valor": 4000.00,
            "Data": "2025-08-25",
            "Processo": "100009",
            "Mapeado": "Sim",
            "Observação": "NF com 5 dígitos (2ª parcela)"
        },
        {
            "Documento": "XYZ999",
            "Tipo": "Não Mapeado",
            "Valor": 1000.00,
            "Data": "2025-08-15",
            "Processo": "-",
            "Mapeado": "Não",
            "Observação": "Documento inválido (deve aparecer em AVISOS)"
        },
        {
            "Documento": "COT",
            "Tipo": "Não Mapeado",
            "Valor": 500.00,
            "Data": "2025-08-16",
            "Processo": "-",
            "Mapeado": "Não",
            "Observação": "COT sem número (deve aparecer em AVISOS)"
        },
    ]
    
    df_documentos = pd.DataFrame(documentos)
    
    # ==================== RECONCILIAÇÕES ESPERADAS ====================
    reconciliacoes = [
        {
            "Processo": "100002",
            "Mês_Reconciliação": "Agosto/2025",
            "Colaborador": "Alessandro Cappi",
            "Total_Adiantado": 7500.00,
            "FCMP_Esperado": "< 1.0",
            "Reconciliação": "Negativa",
            "Fórmula": "7500 × (FCMP - 1.0)",
            "Observações": "Único processo com reconciliação em Agosto"
        },
        {
            "Processo": "100003",
            "Mês_Reconciliação": "Setembro/2025",
            "Colaborador": "Alessandro Cappi",
            "Total_Adiantado": 10000.00,
            "FCMP_Esperado": "< 1.0",
            "Reconciliação": "Negativa",
            "Fórmula": "10000 × (FCMP - 1.0)",
            "Observações": ""
        },
        {
            "Processo": "100004",
            "Mês_Reconciliação": "Setembro/2025",
            "Colaborador": "Alessandro Cappi",
            "Total_Adiantado": 15000.00,
            "FCMP_Esperado": "< 1.0",
            "Reconciliação": "Negativa",
            "Fórmula": "15000 × (FCMP - 1.0)",
            "Observações": "Soma de 2 adiantamentos: 8000 + 7000"
        },
        {
            "Processo": "100006",
            "Mês_Reconciliação": "Setembro/2025",
            "Colaborador": "Alessandro Cappi",
            "Total_Adiantado": "~9000",
            "FCMP_Esperado": "< 1.0",
            "Reconciliação": "Negativa",
            "Fórmula": "proporcional",
            "Observações": "Proporcional ao valor do item dele (R$ 18k de R$ 30k total)"
        },
        {
            "Processo": "100006",
            "Mês_Reconciliação": "Setembro/2025",
            "Colaborador": "André Caramello",
            "Total_Adiantado": "~6000",
            "FCMP_Esperado": "< 1.0",
            "Reconciliação": "Negativa",
            "Fórmula": "proporcional",
            "Observações": "Proporcional ao valor do item dele (R$ 12k de R$ 30k total)"
        },
        {
            "Processo": "100010",
            "Mês_Reconciliação": "Setembro/2025",
            "Colaborador": "Alessandro Cappi",
            "Total_Adiantado": 45000.00,
            "FCMP_Esperado": "< 1.0 (ponderado)",
            "Reconciliação": "Negativa",
            "Fórmula": "45000 × (FCMP_ponderado - 1.0)",
            "Observações": "FCMP = média ponderada de 3 itens (RENTAL + VENDA + RENTAL)"
        },
    ]
    
    df_reconciliacoes = pd.DataFrame(reconciliacoes)
    
    # ==================== VALIDAÇÕES RÁPIDAS ====================
    validacoes = [
        {
            "Item": "Arquivo Agosto gerado",
            "Esperado": "Comissoes_Recebimento_08_2025.xlsx",
            "Como_Validar": "Verificar se arquivo existe na raiz",
            "Status": ""
        },
        {
            "Item": "Arquivo Setembro gerado",
            "Esperado": "Comissoes_Recebimento_09_2025.xlsx",
            "Como_Validar": "Verificar se arquivo existe na raiz",
            "Status": ""
        },
        {
            "Item": "Estado criado",
            "Esperado": "Estado_Processos_Recebimento.xlsx",
            "Como_Validar": "Verificar se arquivo existe na raiz",
            "Status": ""
        },
        {
            "Item": "Reconciliações em Agosto",
            "Esperado": "1 processo (100002)",
            "Como_Validar": "Aba RECONCILIACOES em Comissoes_Recebimento_08_2025.xlsx",
            "Status": ""
        },
        {
            "Item": "Reconciliações em Setembro",
            "Esperado": "4 processos, 5 linhas total",
            "Como_Validar": "Aba RECONCILIACOES em Comissoes_Recebimento_09_2025.xlsx",
            "Status": ""
        },
        {
            "Item": "Processo 100006 - múltiplos colabs",
            "Esperado": "2 linhas (Alessandro + Leandro)",
            "Como_Validar": "Aba RECONCILIACOES em Setembro",
            "Status": ""
        },
        {
            "Item": "Processo 100007 - sem reconciliação",
            "Esperado": "NÃO deve aparecer em RECONCILIACOES",
            "Como_Validar": "Aba RECONCILIACOES em Setembro (processo ausente)",
            "Status": ""
        },
        {
            "Item": "Documentos não mapeados",
            "Esperado": "2 documentos (XYZ999, COT)",
            "Como_Validar": "Aba AVISOS em ambos os arquivos",
            "Status": ""
        },
        {
            "Item": "Estado - processo 100002",
            "Esperado": "STATUS_RECONCILIACAO = RECONCILIADO",
            "Como_Validar": "Aba ESTADO em Agosto ou Setembro",
            "Status": ""
        },
        {
            "Item": "Estado - processo 100007",
            "Esperado": "STATUS_RECONCILIACAO ≠ RECONCILIADO",
            "Como_Validar": "Aba ESTADO em Setembro",
            "Status": ""
        },
    ]
    
    df_validacoes = pd.DataFrame(validacoes)
    
    # ==================== SALVAR ====================
    filepath = "PLANILHA_VALIDACAO_TESTES.xlsx"
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df_cenarios.to_excel(writer, sheet_name='Cenários', index=False)
        df_documentos.to_excel(writer, sheet_name='Documentos', index=False)
        df_reconciliacoes.to_excel(writer, sheet_name='Reconciliações Esperadas', index=False)
        df_validacoes.to_excel(writer, sheet_name='Checklist Validação', index=False)
    
    print(f"✓ Planilha criada: {filepath}")
    print()
    print("Abas:")
    print("  - Cenários: 10 cenários de teste")
    print("  - Documentos: 23 documentos (incluindo não mapeados)")
    print("  - Reconciliações Esperadas: 6 linhas esperadas")
    print("  - Checklist Validação: 10 itens para validar")
    print()
    print("Use esta planilha para comparar com os resultados obtidos!")


if __name__ == "__main__":
    gerar_planilha_validacao()

