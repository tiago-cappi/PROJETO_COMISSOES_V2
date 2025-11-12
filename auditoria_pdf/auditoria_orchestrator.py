"""
Orquestrador principal da auditoria PDF.
Coordena coleta de dados, preparação e geração do PDF.
"""

import os
from datetime import datetime
from typing import Optional

from auditoria_pdf.core.data_collector import AuditoriaDataCollector
from auditoria_pdf.core.audit_data_builder import AuditDataBuilder
from auditoria_pdf.generators.pdf_generator import AuditoriaPDFGenerator


class AuditoriaOrchestrator:
    """
    Orquestra todo o processo de geração de auditoria PDF.
    """
    
    def __init__(
        self,
        recebimento_orchestrator,
        calc_comissao,
        mes: int,
        ano: int,
        base_path: str = "."
    ):
        """
        Inicializa o orquestrador de auditoria.
        
        Args:
            recebimento_orchestrator: Instância do RecebimentoOrchestrator
            calc_comissao: Instância do CalculoComissao
            mes: Mês de apuração (1-12)
            ano: Ano de apuração (ex: 2025)
            base_path: Caminho base para salvar o arquivo
        """
        self.receb_orch = recebimento_orchestrator
        self.calc_comissao = calc_comissao
        self.mes = mes
        self.ano = ano
        self.base_path = base_path
        
        # Inicializar componentes
        self.data_collector = AuditoriaDataCollector(recebimento_orchestrator, calc_comissao)
        self.data_builder = AuditDataBuilder()
        self.pdf_generator = AuditoriaPDFGenerator()
    
    def gerar_auditoria(self) -> Optional[str]:
        """
        Gera relatório de auditoria em PDF.
        
        Returns:
            Caminho do arquivo PDF gerado, ou None se houver erro
        """
        print("\n" + "="*80)
        print("[AUDITORIA] ===== INÍCIO DA GERAÇÃO DE AUDITORIA PDF =====")
        print("="*80)
        
        try:
            # 1. Coletar dados
            print(f"[AUDITORIA] [ETAPA 1/4] Coletando dados para auditoria ({self.mes:02d}/{self.ano})...")
            dados_brutos = self.data_collector.coletar_dados_auditoria(self.mes, self.ano)
            
            if not dados_brutos or dados_brutos.get('total_processos', 0) == 0:
                print("[AUDITORIA] [ETAPA 1/4] Nenhum processo com comissões. Pulando geração de PDF.")
                return None
            
            print(f"[AUDITORIA] [ETAPA 1/4] Dados coletados: {dados_brutos['total_processos']} processo(s)")
            
            # 2. Preparar dados (formatar)
            print("[AUDITORIA] [ETAPA 2/4] Preparando dados para renderização...")
            processos_formatados = []
            
            for processo_dados in dados_brutos['processos']:
                processo_formatado = self.data_builder.preparar_dados_processo(processo_dados)
                processos_formatados.append(processo_formatado)
            
            print(f"[AUDITORIA] [ETAPA 2/4] {len(processos_formatados)} processo(s) formatado(s)")
            
            # Atualizar estrutura com dados formatados
            dados_auditoria = {
                'mes': dados_brutos['mes'],
                'ano': dados_brutos['ano'],
                'data_geracao': dados_brutos['data_geracao'],
                'processos': processos_formatados,
                'total_processos': len(processos_formatados)
            }
            
            # 3. Gerar PDF
            print("[AUDITORIA] [ETAPA 3/4] Gerando arquivo PDF...")
            
            # Definir nome do arquivo
            filename = f"Auditoria_Recebimento_{self.mes:02d}_{self.ano}.pdf"
            filepath = os.path.join(self.base_path, filename)
            
            print(f"[AUDITORIA] [ETAPA 3/4] Nome do arquivo: {filename}")
            print(f"[AUDITORIA] [ETAPA 3/4] Caminho completo: {filepath}")
            
            # Gerar PDF
            arquivo_gerado = self.pdf_generator.gerar_pdf(dados_auditoria, filepath)
            
            # 4. Verificar resultado
            print("[AUDITORIA] [ETAPA 4/4] Verificando arquivo gerado...")
            
            if os.path.exists(arquivo_gerado):
                tamanho = os.path.getsize(arquivo_gerado)
                print(f"[AUDITORIA] [ETAPA 4/4] Arquivo gerado com sucesso!")
                print(f"[AUDITORIA] [ETAPA 4/4] Tamanho: {tamanho / 1024:.2f} KB")
                print(f"[AUDITORIA] [ETAPA 4/4] Local: {arquivo_gerado}")
            else:
                print(f"[AUDITORIA] [ETAPA 4/4] ERRO: Arquivo não encontrado após geração!")
                arquivo_gerado = None
            
            print("="*80)
            print("[AUDITORIA] ===== FIM DA GERAÇÃO DE AUDITORIA PDF =====")
            print("="*80 + "\n")
            
            return arquivo_gerado
            
        except Exception as e:
            print("\n" + "="*80)
            print("[AUDITORIA] ===== ERRO NA GERAÇÃO DE AUDITORIA PDF =====")
            print(f"[AUDITORIA] Erro: {str(e)}")
            print(f"[AUDITORIA] Tipo do erro: {type(e).__name__}")
            print("[AUDITORIA] Traceback completo:")
            
            import traceback
            traceback.print_exc()
            
            print("="*80 + "\n")
            
            return None

