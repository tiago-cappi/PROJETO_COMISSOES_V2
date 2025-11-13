"""
Construtor de tabelas formatadas para PDF.
"""

from typing import List, Tuple, Optional
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from auditoria_pdf.styles.pdf_styles import (
    TABLE_STYLE_DEFAULT,
    TABLE_STYLE_LISTRADA,
    TABLE_STYLE_DESTAQUE,
    COR_PRIMARIA,
    COR_CINZA_CLARO,
    COR_CINZA_MEDIO,
    white
)


class TableBuilder:
    """
    Construtor de tabelas formatadas para ReportLab.
    """
    
    @staticmethod
    def criar_tabela_simples(
        dados: List[List[str]],
        larguras: Optional[List[float]] = None,
        repetir_header: bool = True
    ) -> Table:
        """
        Cria uma tabela simples com estilo padrão.
        
        Args:
            dados: Lista de listas com os dados (primeira linha = header)
            larguras: Lista de larguras das colunas (opcional)
            repetir_header: Se True, repete o header em novas páginas
            
        Returns:
            Objeto Table do ReportLab
        """
        if not dados or len(dados) == 0:
            return None
        
        # Criar tabela
        tabela = Table(dados, colWidths=larguras, repeatRows=1 if repetir_header else 0)
        
        # Aplicar estilo padrão
        tabela.setStyle(TableStyle(TABLE_STYLE_DEFAULT))
        
        return tabela
    
    @staticmethod
    def criar_tabela_listrada(
        dados: List[List[str]],
        larguras: Optional[List[float]] = None,
        repetir_header: bool = True
    ) -> Table:
        """
        Cria uma tabela com linhas alternadas (zebrada).
        
        Args:
            dados: Lista de listas com os dados (primeira linha = header)
            larguras: Lista de larguras das colunas (opcional)
            repetir_header: Se True, repete o header em novas páginas
            
        Returns:
            Objeto Table do ReportLab
        """
        if not dados or len(dados) == 0:
            return None
        
        # Criar tabela
        tabela = Table(dados, colWidths=larguras, repeatRows=1 if repetir_header else 0)
        
        # Aplicar estilo listrado
        tabela.setStyle(TableStyle(TABLE_STYLE_LISTRADA))
        
        return tabela
    
    @staticmethod
    def criar_tabela_destaque(
        dados: List[List[str]],
        larguras: Optional[List[float]] = None,
        repetir_header: bool = True
    ) -> Table:
        """
        Cria uma tabela com estilo de destaque (borda mais grossa).
        
        Args:
            dados: Lista de listas com os dados (primeira linha = header)
            larguras: Lista de larguras das colunas (opcional)
            repetir_header: Se True, repete o header em novas páginas
            
        Returns:
            Objeto Table do ReportLab
        """
        if not dados or len(dados) == 0:
            return None
        
        # Criar tabela
        tabela = Table(dados, colWidths=larguras, repeatRows=1 if repetir_header else 0)
        
        # Aplicar estilo de destaque
        tabela.setStyle(TableStyle(TABLE_STYLE_DESTAQUE))
        
        return tabela
    
    @staticmethod
    def criar_tabela_chave_valor(
        dados: List[Tuple[str, str]],
        largura_chave: float = 150,
        largura_valor: float = 350
    ) -> Table:
        """
        Cria uma tabela de chave-valor (2 colunas).
        
        Args:
            dados: Lista de tuplas (chave, valor) - pode conter strings ou objetos Paragraph
            largura_chave: Largura da coluna de chaves
            largura_valor: Largura da coluna de valores
            
        Returns:
            Objeto Table do ReportLab
        """
        if not dados or len(dados) == 0:
            return None
        
        from reportlab.platypus import Paragraph
        from auditoria_pdf.styles.pdf_styles import STYLE_CORPO, STYLE_DESTAQUE
        
        # Converter tuplas em lista de listas, processando HTML quando necessário
        dados_tabela = []
        for chave, valor in dados:
            # Processar chave
            if isinstance(chave, str) and ('<b>' in chave or '<i>' in chave):
                # Tem HTML, converter para Paragraph
                chave_processada = Paragraph(chave, STYLE_DESTAQUE)
            else:
                chave_processada = chave
            
            # Processar valor
            if isinstance(valor, str) and ('<b>' in valor or '<i>' in valor):
                # Tem HTML, converter para Paragraph
                valor_processado = Paragraph(valor, STYLE_CORPO)
            else:
                valor_processado = valor
            
            dados_tabela.append([chave_processada, valor_processado])
        
        # Criar tabela sem header
        tabela = Table(dados_tabela, colWidths=[largura_chave, largura_valor])
        
        # Estilo customizado para tabela chave-valor
        estilo = [
            ('BACKGROUND', (0, 0), (0, -1), COR_CINZA_CLARO),  # Coluna de chaves com fundo cinza
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Chaves em negrito
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, COR_CINZA_MEDIO),
        ]
        
        tabela.setStyle(TableStyle(estilo))
        
        return tabela
    
    @staticmethod
    def criar_tabela_resumo(
        dados: List[List[str]],
        larguras: Optional[List[float]] = None,
        linhas_destaque: Optional[List[int]] = None
    ) -> Table:
        """
        Cria uma tabela de resumo com linhas específicas destacadas.
        
        Args:
            dados: Lista de listas com os dados (primeira linha = header)
            larguras: Lista de larguras das colunas (opcional)
            linhas_destaque: Índices das linhas a destacar (ex: linha de total)
            
        Returns:
            Objeto Table do ReportLab
        """
        if not dados or len(dados) == 0:
            return None
        
        # Criar tabela
        tabela = Table(dados, colWidths=larguras, repeatRows=1)
        
        # Começar com estilo padrão
        estilo = list(TABLE_STYLE_DEFAULT)
        
        # Adicionar destaque em linhas específicas
        if linhas_destaque:
            for linha_idx in linhas_destaque:
                if linha_idx < len(dados):
                    estilo.extend([
                        ('BACKGROUND', (0, linha_idx), (-1, linha_idx), COR_PRIMARIA),
                        ('TEXTCOLOR', (0, linha_idx), (-1, linha_idx), white),
                        ('FONTNAME', (0, linha_idx), (-1, linha_idx), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, linha_idx), (-1, linha_idx), 10),
                    ])
        
        tabela.setStyle(TableStyle(estilo))
        
        return tabela

