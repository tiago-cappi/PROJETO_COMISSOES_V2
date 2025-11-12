"""
Gerador principal de PDF de auditoria.
"""

import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

from auditoria_pdf.styles.pdf_styles import (
    MARGEM_SUPERIOR,
    MARGEM_INFERIOR,
    MARGEM_ESQUERDA,
    MARGEM_DIREITA
)
from auditoria_pdf.generators import section_header
from auditoria_pdf.generators import section_processo
from auditoria_pdf.generators import section_pagamentos
from auditoria_pdf.generators import section_colaboradores
from auditoria_pdf.generators import section_tcmp
from auditoria_pdf.generators import section_fcmp
from auditoria_pdf.generators import section_comissoes
from auditoria_pdf.generators import section_resumo


class AuditoriaPDFGenerator:
    """
    Gerador de PDF de auditoria para comissões por recebimento.
    """
    
    def gerar_pdf(self, dados_auditoria: dict, filepath: str) -> str:
        """
        Gera o PDF de auditoria.
        
        Args:
            dados_auditoria: Dicionário com dados completos para auditoria
            filepath: Caminho onde o PDF será salvo
            
        Returns:
            Caminho do arquivo PDF gerado
        """
        print(f"[AUDITORIA] [PDF] Iniciando geração do PDF: {filepath}")
        
        # Criar documento
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=MARGEM_DIREITA,
            leftMargin=MARGEM_ESQUERDA,
            topMargin=MARGEM_SUPERIOR,
            bottomMargin=MARGEM_INFERIOR
        )
        
        # Story (lista de elementos do PDF)
        story = []
        
        # 1. Capa
        print("[AUDITORIA] [PDF] Gerando capa...")
        section_header.gerar_capa(
            story,
            dados_auditoria['mes'],
            dados_auditoria['ano'],
            dados_auditoria['data_geracao']
        )
        
        # 2. Índice
        print("[AUDITORIA] [PDF] Gerando índice...")
        section_header.gerar_indice(story, dados_auditoria['processos'])
        
        # 3. Seções de cada processo
        processos = dados_auditoria.get('processos', [])
        print(f"[AUDITORIA] [PDF] Gerando seções para {len(processos)} processo(s)...")
        
        for idx, processo_dados in enumerate(processos, 1):
            print(f"[AUDITORIA] [PDF] Processando processo {idx}/{len(processos)}...")
            
            processo_id = processo_dados['dados_gerais']['processo_id']
            
            # Separador de processo
            section_header.gerar_separador_processo(story, processo_id, idx)
            
            # Seção 1: Dados do processo
            section_processo.gerar_secao_dados_processo(story, processo_dados)
            
            # Seção 2: Itens do processo
            section_processo.gerar_secao_itens_processo(story, processo_dados)
            
            # Seção 3: Pagamentos
            section_pagamentos.gerar_secao_pagamentos(story, processo_dados)
            
            # Seção 4: Colaboradores
            section_colaboradores.gerar_secao_colaboradores(story, processo_dados)
            
            # Seção 5: TCMP
            section_tcmp.gerar_secao_tcmp(story, processo_dados)
            
            # Seção 6: FCMP
            section_fcmp.gerar_secao_fcmp(story, processo_dados)
            
            # Seção 7: Comissões
            section_comissoes.gerar_secao_comissoes(story, processo_dados)
            
            # Seção 8: Resumo
            section_resumo.gerar_secao_resumo(story, processo_dados)
        
        # Construir PDF
        print("[AUDITORIA] [PDF] Construindo PDF final...")
        try:
            doc.build(story)
            print(f"[AUDITORIA] [PDF] PDF gerado com sucesso: {filepath}")
            
            # Verificar tamanho do arquivo
            if os.path.exists(filepath):
                tamanho = os.path.getsize(filepath)
                print(f"[AUDITORIA] [PDF] Tamanho do arquivo: {tamanho / 1024:.2f} KB")
            
            return filepath
        except Exception as e:
            print(f"[AUDITORIA] [PDF] ERRO ao construir PDF: {e}")
            import traceback
            traceback.print_exc()
            raise

