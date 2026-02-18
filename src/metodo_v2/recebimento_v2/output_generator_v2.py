"""
src.metodo_v2.recebimento_v2.output_generator_v2 - Gerador de Saídas

Gera arquivo Excel consolidado com resultados de comissões por recebimento.

Arquivo de saída: Comissoes_Recebimento_V2_MM_YYYY.xlsx

Abas:
- Resumo: Totais por colaborador
- Adiantamentos: Detalhes de adiantamentos do período
- Reconciliações: Detalhes de reconciliações do período
- Histórico: Processos ainda pendentes
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .comissao_recebimento_calculator_v2 import ResultadoComissaoRecebimentoV2
from .reconciliacao_calculator_v2 import ResultadoReconciliacaoV2
from .state_manager_v2 import EstadoProcesso, StateManagerV2


logger = logging.getLogger(__name__)


class OutputGeneratorV2:
    """Gerador de arquivos de saída para comissões por recebimento V2."""
    
    def __init__(self, base_path: str = "."):
        """Inicializa o gerador.
        
        Args:
            base_path: Caminho base (raiz do projeto).
        """
        self.base_path = Path(base_path)
        self.output_path = self.base_path / "dados_saida"
    
    def gerar_arquivo(
        self,
        mes: int,
        ano: int,
        adiantamentos: List[ResultadoComissaoRecebimentoV2],
        reconciliacoes: List[ResultadoReconciliacaoV2],
        state_manager: StateManagerV2
    ) -> str:
        """Gera arquivo Excel consolidado.
        
        Args:
            mes: Mês de apuração.
            ano: Ano de apuração.
            adiantamentos: Lista de adiantamentos do período.
            reconciliacoes: Lista de reconciliações do período.
            state_manager: Gerenciador de estado.
            
        Returns:
            Caminho do arquivo gerado.
        """
        # Garantir diretório existe
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo
        filename = f"Comissoes_Recebimento_V2_{mes:02d}_{ano}.xlsx"
        filepath = self.output_path / filename
        
        logger.info(f"[V2-REC-OUT] Gerando arquivo: {filepath}")
        
        # Criar DataFrames
        df_resumo = self._gerar_resumo(adiantamentos, reconciliacoes)
        df_adiantamentos = self._gerar_detalhes_adiantamentos(adiantamentos)
        df_reconciliacoes = self._gerar_detalhes_reconciliacoes(reconciliacoes)
        df_historico = self._gerar_historico_pendentes(state_manager)
        
        # Escrever Excel com múltiplas abas
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
            df_adiantamentos.to_excel(writer, sheet_name='Adiantamentos', index=False)
            df_reconciliacoes.to_excel(writer, sheet_name='Reconciliações', index=False)
            df_historico.to_excel(writer, sheet_name='Histórico Pendente', index=False)
            
            # Adicionar aba de metadata
            df_meta = pd.DataFrame([{
                "Mês Apuração": mes,
                "Ano Apuração": ano,
                "Data Geração": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Total Adiantamentos": len(adiantamentos),
                "Total Reconciliações": len(reconciliacoes),
                "Valor Total Adiantamentos": sum(a.comissao_calculada for a in adiantamentos),
                "Valor Total Ajustes": sum(r.ajuste for r in reconciliacoes)
            }])
            df_meta.to_excel(writer, sheet_name='Metadata', index=False)
        
        logger.info(f"[V2-REC-OUT] Arquivo gerado com sucesso: {filepath}")
        
        return str(filepath)
    
    def _gerar_resumo(
        self,
        adiantamentos: List[ResultadoComissaoRecebimentoV2],
        reconciliacoes: List[ResultadoReconciliacaoV2]
    ) -> pd.DataFrame:
        """Gera aba de resumo por colaborador.
        
        Args:
            adiantamentos: Lista de adiantamentos.
            reconciliacoes: Lista de reconciliações.
            
        Returns:
            DataFrame com resumo.
        """
        # Agrupar por colaborador
        resumo: Dict[str, dict] = {}
        
        # Processar adiantamentos
        for adiante in adiantamentos:
            colab = adiante.colaborador_nome
            if colab not in resumo:
                resumo[colab] = {
                    "Colaborador": colab,
                    "ID": adiante.colaborador_id,
                    "Qtd Adiantamentos": 0,
                    "Total Adiantamentos": 0.0,
                    "Qtd Reconciliações": 0,
                    "Total Ajustes": 0.0,
                    "Complementos": 0.0,
                    "Devoluções": 0.0,
                    "Comissão Líquida": 0.0
                }
            
            resumo[colab]["Qtd Adiantamentos"] += 1
            resumo[colab]["Total Adiantamentos"] += adiante.comissao_calculada
        
        # Processar reconciliações
        for reconc in reconciliacoes:
            colab = reconc.colaborador_nome
            if colab not in resumo:
                resumo[colab] = {
                    "Colaborador": colab,
                    "ID": reconc.colaborador_id,
                    "Qtd Adiantamentos": 0,
                    "Total Adiantamentos": 0.0,
                    "Qtd Reconciliações": 0,
                    "Total Ajustes": 0.0,
                    "Complementos": 0.0,
                    "Devoluções": 0.0,
                    "Comissão Líquida": 0.0
                }
            
            resumo[colab]["Qtd Reconciliações"] += 1
            resumo[colab]["Total Ajustes"] += reconc.ajuste
            
            if reconc.tipo_ajuste == "COMPLEMENTO":
                resumo[colab]["Complementos"] += reconc.ajuste
            elif reconc.tipo_ajuste == "DEVOLUÇÃO":
                resumo[colab]["Devoluções"] += abs(reconc.ajuste)
        
        # Calcular comissão líquida
        for colab in resumo:
            resumo[colab]["Comissão Líquida"] = (
                resumo[colab]["Total Adiantamentos"] + 
                resumo[colab]["Total Ajustes"]
            )
        
        df = pd.DataFrame(list(resumo.values()))
        
        if df.empty:
            df = pd.DataFrame(columns=[
                "Colaborador", "ID", "Qtd Adiantamentos", "Total Adiantamentos",
                "Qtd Reconciliações", "Total Ajustes", "Complementos",
                "Devoluções", "Comissão Líquida"
            ])
        
        # Ordenar por comissão líquida
        df = df.sort_values("Comissão Líquida", ascending=False).reset_index(drop=True)
        
        return df
    
    def _gerar_detalhes_adiantamentos(
        self,
        adiantamentos: List[ResultadoComissaoRecebimentoV2]
    ) -> pd.DataFrame:
        """Gera aba de detalhes de adiantamentos.
        
        Args:
            adiantamentos: Lista de adiantamentos.
            
        Returns:
            DataFrame com detalhes.
        """
        if not adiantamentos:
            return pd.DataFrame(columns=[
                "Colaborador", "Documento", "Documento Normalizado",
                "Valor Base", "Taxa (%)", "Comissão"
            ])
        
        dados = []
        for adiante in adiantamentos:
            dados.append({
                "Colaborador": adiante.colaborador_nome,
                "Documento": adiante.documento,
                "Documento Normalizado": adiante.documento_normalizado,
                "Valor Base": adiante.valor_base,
                "Taxa (%)": adiante.percentual_aplicado,
                "Comissão": adiante.comissao_calculada
            })
        
        return pd.DataFrame(dados)
    
    def _gerar_detalhes_reconciliacoes(
        self,
        reconciliacoes: List[ResultadoReconciliacaoV2]
    ) -> pd.DataFrame:
        """Gera aba de detalhes de reconciliações.
        
        Args:
            reconciliacoes: Lista de reconciliações.
            
        Returns:
            DataFrame com detalhes.
        """
        if not reconciliacoes:
            return pd.DataFrame(columns=[
                "Colaborador", "Documento", "Valor Adiantado",
                "Comissão Adiantada", "Valor Faturado", "Comissão Real",
                "Ajuste", "Tipo Ajuste"
            ])
        
        dados = []
        for reconc in reconciliacoes:
            dados.append({
                "Colaborador": reconc.colaborador_nome,
                "Documento": reconc.documento_normalizado,
                "Valor Adiantado": reconc.valor_adiantado,
                "Comissão Adiantada": reconc.comissao_adiantada,
                "Valor Faturado": reconc.valor_faturado,
                "Comissão Real": reconc.comissao_real,
                "Ajuste": reconc.ajuste,
                "Tipo Ajuste": reconc.tipo_ajuste
            })
        
        return pd.DataFrame(dados)
    
    def _gerar_historico_pendentes(
        self,
        state_manager: StateManagerV2
    ) -> pd.DataFrame:
        """Gera aba com processos ainda pendentes.
        
        Args:
            state_manager: Gerenciador de estado.
            
        Returns:
            DataFrame com pendentes.
        """
        pendentes = state_manager.listar_adiantamentos_pendentes()
        
        if not pendentes:
            return pd.DataFrame(columns=[
                "Documento", "Colaborador ID", "Estado",
                "Valor Adiantado", "Comissão Adiantada", "Data Adiantamento"
            ])
        
        dados = []
        for registro in pendentes:
            dados.append({
                "Documento": registro.documento_normalizado,
                "Colaborador ID": registro.colaborador_id,
                "Estado": registro.estado.value,
                "Valor Adiantado": registro.valor_adiantado,
                "Comissão Adiantada": registro.comissao_adiantada,
                "Data Adiantamento": registro.data_adiantamento
            })
        
        return pd.DataFrame(dados)
