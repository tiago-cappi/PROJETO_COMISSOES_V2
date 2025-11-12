"""
Construtor de dados para auditoria.
Transforma dados brutos em estruturas prontas para renderização no PDF.
"""

from typing import Dict, List
from auditoria_pdf.utils.formatters import (
    formatar_moeda,
    formatar_percentual,
    formatar_data,
    formatar_numero,
    formatar_colaborador
)


class AuditDataBuilder:
    """
    Prepara dados para renderização no PDF de auditoria.
    """
    
    def preparar_dados_processo(self, dados_processo: Dict) -> Dict:
        """
        Prepara dados de um processo para renderização.
        
        Args:
            dados_processo: Dados brutos do processo
            
        Returns:
            Dados formatados e prontos para o PDF
        """
        return {
            'dados_gerais_formatados': self._formatar_dados_gerais(dados_processo['dados_gerais']),
            'itens_formatados': self._formatar_itens(dados_processo['itens']),
            'pagamentos_formatados': self._formatar_pagamentos(dados_processo['pagamentos']),
            'colaboradores_formatados': self._formatar_colaboradores(dados_processo['colaboradores']),
            'tcmp_formatado': self._formatar_tcmp(dados_processo['calculos_tcmp']),
            'fcmp_formatado': self._formatar_fcmp(dados_processo['calculos_fcmp']),
            'comissoes_formatadas': self._formatar_comissoes(dados_processo['comissoes']),
            'estatisticas': self._calcular_estatisticas(dados_processo)
        }
    
    def _formatar_dados_gerais(self, dados_gerais: Dict) -> Dict:
        """Formata dados gerais do processo."""
        return {
            'processo_id': dados_gerais['processo_id'],
            'status': dados_gerais['status'],
            'dt_emissao': formatar_data(dados_gerais.get('dt_emissao')),
            'numero_nf': dados_gerais.get('numero_nf', '-'),
            'cliente': dados_gerais.get('cliente', '-'),
            'operacao': dados_gerais.get('operacao', '-'),
            'valor_total': formatar_moeda(dados_gerais.get('valor_total', 0))
        }
    
    def _formatar_itens(self, itens: List[Dict]) -> List[Dict]:
        """Formata lista de itens do processo."""
        itens_formatados = []
        
        for item in itens:
            itens_formatados.append({
                'codigo_produto': item.get('codigo_produto', '-'),
                'descricao': item.get('descricao', '-'),
                'linha': item.get('linha', '-'),
                'grupo': item.get('grupo', '-'),
                'subgrupo': item.get('subgrupo', '-'),
                'tipo_mercadoria': item.get('tipo_mercadoria', '-'),
                'valor': formatar_moeda(item.get('valor', 0)),
                'valor_num': item.get('valor', 0),  # Manter numérico para cálculos
                'fabricante': item.get('fabricante', '-'),
                'consultor_interno': formatar_colaborador(item.get('consultor_interno')),
                'representante': formatar_colaborador(item.get('representante'))
            })
        
        return itens_formatados
    
    def _formatar_pagamentos(self, pagamentos: List[Dict]) -> List[Dict]:
        """Formata lista de pagamentos."""
        pagamentos_formatados = []
        
        for pag in pagamentos:
            pagamentos_formatados.append({
                'tipo': pag.get('tipo', '-'),
                'documento': pag.get('documento', '-'),
                'data': formatar_data(pag.get('data')),
                'valor': formatar_moeda(pag.get('valor', 0)),
                'valor_num': pag.get('valor', 0)
            })
        
        return pagamentos_formatados
    
    def _formatar_colaboradores(self, colaboradores: List[Dict]) -> List[Dict]:
        """Formata lista de colaboradores."""
        colaboradores_formatados = []
        
        for colab in colaboradores:
            colaboradores_formatados.append({
                'nome': formatar_colaborador(colab.get('nome')),
                'cargo': colab.get('cargo', '-'),
                'tipo': colab.get('tipo', '-')
            })
        
        return colaboradores_formatados
    
    def _formatar_tcmp(self, calculos_tcmp: Dict) -> Dict:
        """Formata cálculos de TCMP."""
        tcmp_final = calculos_tcmp.get('tcmp_final', {})
        detalhes_itens = calculos_tcmp.get('detalhes_itens', [])
        
        # Formatar TCMP final por colaborador
        tcmp_por_colaborador = {}
        for nome, valor in tcmp_final.items():
            tcmp_por_colaborador[formatar_colaborador(nome)] = {
                'tcmp': formatar_percentual(valor),
                'tcmp_num': valor
            }
        
        # Formatar detalhes dos itens
        itens_detalhados = []
        for item_detalhe in detalhes_itens:
            taxas_formatadas = []
            for taxa_colab in item_detalhe.get('taxas_colaboradores', []):
                taxas_formatadas.append({
                    'nome': formatar_colaborador(taxa_colab['nome']),
                    'cargo': taxa_colab['cargo'],
                    'taxa_rateio': formatar_percentual(taxa_colab['taxa_rateio_pct'] / 100),
                    'fatia_cargo': formatar_percentual(taxa_colab['fatia_cargo_pct'] / 100),
                    'taxa_final': formatar_percentual(taxa_colab['taxa_final_pct'] / 100),
                    'taxa_final_num': taxa_colab['taxa_final_pct'] / 100
                })
            
            itens_detalhados.append({
                'linha': item_detalhe.get('linha', '-'),
                'grupo': item_detalhe.get('grupo', '-'),
                'subgrupo': item_detalhe.get('subgrupo', '-'),
                'tipo_mercadoria': item_detalhe.get('tipo_mercadoria', '-'),
                'valor': formatar_moeda(item_detalhe.get('valor', 0)),
                'valor_num': item_detalhe.get('valor', 0),
                'taxas_colaboradores': taxas_formatadas
            })
        
        return {
            'tcmp_por_colaborador': tcmp_por_colaborador,
            'detalhes_itens': itens_detalhados,
            'mes_faturamento': calculos_tcmp.get('mes_faturamento', '-')
        }
    
    def _formatar_fcmp(self, calculos_fcmp: Dict) -> Dict:
        """Formata cálculos de FCMP."""
        fcmp_final = calculos_fcmp.get('fcmp_final', {})
        detalhes_itens = calculos_fcmp.get('detalhes_itens', [])
        
        # Formatar FCMP final por colaborador
        fcmp_por_colaborador = {}
        for nome, valor in fcmp_final.items():
            fcmp_por_colaborador[formatar_colaborador(nome)] = {
                'fcmp': formatar_numero(valor, 4),
                'fcmp_num': valor
            }
        
        # Formatar detalhes dos itens
        itens_detalhados = []
        for item_detalhe in detalhes_itens:
            fcs_formatados = []
            for fc_colab in item_detalhe.get('fcs_colaboradores', []):
                componentes_formatados = []
                for comp in fc_colab.get('componentes', []):
                    componentes_formatados.append({
                        'nome': comp['nome'],
                        'peso': formatar_percentual(comp['peso']),
                        'peso_num': comp['peso'],
                        'realizado': formatar_numero(comp['realizado'], 2),
                        'meta': formatar_numero(comp['meta'], 2),
                        'atingimento': formatar_percentual(comp['atingimento']),
                        'atingimento_num': comp['atingimento'],
                        'comp_fc': formatar_numero(comp['comp_fc'], 4),
                        'comp_fc_num': comp['comp_fc']
                    })
                
                fcs_formatados.append({
                    'nome': formatar_colaborador(fc_colab['nome']),
                    'cargo': fc_colab['cargo'],
                    'fc_final': formatar_numero(fc_colab['fc_final'], 4),
                    'fc_final_num': fc_colab['fc_final'],
                    'componentes': componentes_formatados
                })
            
            itens_detalhados.append({
                'linha': item_detalhe.get('linha', '-'),
                'grupo': item_detalhe.get('grupo', '-'),
                'subgrupo': item_detalhe.get('subgrupo', '-'),
                'tipo_mercadoria': item_detalhe.get('tipo_mercadoria', '-'),
                'valor': formatar_moeda(item_detalhe.get('valor', 0)),
                'valor_num': item_detalhe.get('valor', 0),
                'fcs_colaboradores': fcs_formatados
            })
        
        return {
            'fcmp_por_colaborador': fcmp_por_colaborador,
            'detalhes_itens': itens_detalhados
        }
    
    def _formatar_comissoes(self, comissoes: List[Dict]) -> List[Dict]:
        """Formata comissões calculadas."""
        comissoes_formatadas = []
        
        for com in comissoes:
            comissoes_formatadas.append({
                'tipo': com.get('tipo', '-'),
                'colaborador': formatar_colaborador(com.get('colaborador')),
                'cargo': com.get('cargo', '-'),
                'tcmp': formatar_percentual(com.get('tcmp', 0)),
                'tcmp_num': com.get('tcmp', 0),
                'fcmp': formatar_numero(com.get('fcmp', 1.0), 4),
                'fcmp_num': com.get('fcmp', 1.0),
                'valor_pago': formatar_moeda(com.get('valor_pago', 0)),
                'valor_pago_num': com.get('valor_pago', 0),
                'comissao': formatar_moeda(com.get('comissao', 0)),
                'comissao_num': com.get('comissao', 0),
                'mes_calculo': com.get('mes_calculo', '-')
            })
        
        return comissoes_formatadas
    
    def _calcular_estatisticas(self, dados_processo: Dict) -> Dict:
        """Calcula estatísticas do processo."""
        # Totais de pagamentos
        total_adiantamentos = sum(
            p.get('valor', 0) 
            for p in dados_processo['pagamentos'] 
            if p.get('tipo') == 'Adiantamento'
        )
        
        total_regulares = sum(
            p.get('valor', 0) 
            for p in dados_processo['pagamentos'] 
            if p.get('tipo') == 'Regular'
        )
        
        # Totais de comissões
        total_comissoes_adiant = sum(
            c.get('comissao', 0) 
            for c in dados_processo['comissoes'] 
            if c.get('tipo') == 'Adiantamento'
        )
        
        total_comissoes_reg = sum(
            c.get('comissao', 0) 
            for c in dados_processo['comissoes'] 
            if c.get('tipo') == 'Regular'
        )
        
        # Contadores
        num_itens = len(dados_processo['itens'])
        num_colaboradores = len(dados_processo['colaboradores'])
        num_pagamentos = len(dados_processo['pagamentos'])
        num_comissoes = len(dados_processo['comissoes'])
        
        return {
            'total_adiantamentos': formatar_moeda(total_adiantamentos),
            'total_adiantamentos_num': total_adiantamentos,
            'total_regulares': formatar_moeda(total_regulares),
            'total_regulares_num': total_regulares,
            'total_pagamentos': formatar_moeda(total_adiantamentos + total_regulares),
            'total_pagamentos_num': total_adiantamentos + total_regulares,
            'total_comissoes_adiant': formatar_moeda(total_comissoes_adiant),
            'total_comissoes_adiant_num': total_comissoes_adiant,
            'total_comissoes_reg': formatar_moeda(total_comissoes_reg),
            'total_comissoes_reg_num': total_comissoes_reg,
            'total_comissoes': formatar_moeda(total_comissoes_adiant + total_comissoes_reg),
            'total_comissoes_num': total_comissoes_adiant + total_comissoes_reg,
            'num_itens': num_itens,
            'num_colaboradores': num_colaboradores,
            'num_pagamentos': num_pagamentos,
            'num_comissoes': num_comissoes
        }

