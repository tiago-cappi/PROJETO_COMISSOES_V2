"""
src.metodo_v2.recebimento_v2.reconciliacao_calculator_v2 - Calculadora de Reconciliação

Calcula ajustes de reconciliação quando um processo que teve adiantamento é faturado.

Fórmula:
    Ajuste = Comissão_Real - Comissão_Adiantada

Onde:
- Comissão_Adiantada: Calculada no momento do pagamento usando taxa_adiantamento_pct
- Comissão_Real: Calculada no faturamento usando regras/faixas normais

O ajuste pode ser:
- Positivo: Colaborador recebe complemento
- Negativo: Colaborador deve devolver diferença
- Zero: Adiantamento foi correto
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from ..models_v2 import ColaboradorV2, RegraComissao
from .state_manager_v2 import EstadoProcesso, RegistroEstado, StateManagerV2
from .comissao_recebimento_calculator_v2 import (
    ComissaoRecebimentoCalculatorV2,
    ResultadoComissaoRecebimentoV2
)


logger = logging.getLogger(__name__)


@dataclass
class ResultadoReconciliacaoV2:
    """Resultado de uma reconciliação.
    
    Attributes:
        documento_normalizado: Chave do processo.
        colaborador_id: ID do colaborador.
        colaborador_nome: Nome do colaborador.
        valor_adiantado: Valor do adiantamento original.
        comissao_adiantada: Comissão paga no adiantamento.
        valor_faturado: Valor faturado.
        comissao_real: Comissão calculada no faturamento.
        ajuste: Diferença (comissao_real - comissao_adiantada).
        tipo_ajuste: "COMPLEMENTO", "DEVOLUÇÃO" ou "ZERO".
        data_reconciliacao: Data da reconciliação.
    """
    documento_normalizado: str
    colaborador_id: str
    colaborador_nome: str
    valor_adiantado: float
    comissao_adiantada: float
    valor_faturado: float
    comissao_real: float
    ajuste: float
    tipo_ajuste: str
    data_reconciliacao: pd.Timestamp
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "Documento Normalizado": self.documento_normalizado,
            "Colaborador ID": self.colaborador_id,
            "Colaborador Nome": self.colaborador_nome,
            "Valor Adiantado": self.valor_adiantado,
            "Comissão Adiantada": self.comissao_adiantada,
            "Valor Faturado": self.valor_faturado,
            "Comissão Real": self.comissao_real,
            "Ajuste": self.ajuste,
            "Tipo Ajuste": self.tipo_ajuste,
            "Data Reconciliação": self.data_reconciliacao
        }


class ReconciliacaoCalculatorV2:
    """Calculadora de reconciliações para V2.
    
    Processa ajustes quando processos com adiantamento são faturados.
    Suporta modo Hierarquia e modo Centro de Custo.
    """
    
    def __init__(
        self,
        state_manager: StateManagerV2,
        comissao_calculator: ComissaoRecebimentoCalculatorV2,
        colaboradores: Dict[str, ColaboradorV2],
        modo_cc: bool = False
    ):
        """Inicializa a calculadora.
        
        Args:
            state_manager: Gerenciador de estado.
            comissao_calculator: Calculadora de comissões.
            colaboradores: Dicionário de colaboradores.
            modo_cc: Se True, usa regras de Centro de Custo na reconciliação.
        """
        self.state_manager = state_manager
        self.comissao_calculator = comissao_calculator
        self.colaboradores = colaboradores
        self.modo_cc = modo_cc
        
        # Índice por nome
        self._colab_por_nome = {
            c.nome.upper(): c for c in colaboradores.values()
        }
    
    def verificar_faturamentos_pendentes(
        self,
        df_faturamento: pd.DataFrame,
        coluna_documento: str = "N° NF",
        coluna_valor: str = "Valor Faturado"
    ) -> List[RegistroEstado]:
        """Verifica quais adiantamentos foram faturados.
        
        Args:
            df_faturamento: DataFrame de faturamento do mês.
            coluna_documento: Nome da coluna de documento.
            coluna_valor: Nome da coluna de valor.
            
        Returns:
            Lista de registros que foram faturados.
        """
        # Obter adiantamentos pendentes
        pendentes = self.state_manager.listar_adiantamentos_pendentes()
        
        if not pendentes:
            logger.info("[V2-REC-RECONC] Nenhum adiantamento pendente")
            return []
        
        # Normalizar documentos do faturamento
        docs_faturamento = set()
        valores_faturamento: Dict[str, float] = {}
        
        for _, row in df_faturamento.iterrows():
            doc = str(row.get(coluna_documento, "")).strip().upper()
            valor = float(row.get(coluna_valor, 0) or 0)
            
            if doc and doc != "NAN":
                # Normalizar para 6 dígitos
                doc_norm = doc.zfill(6) if doc.isdigit() else doc
                docs_faturamento.add(doc_norm)
                valores_faturamento[doc_norm] = valores_faturamento.get(doc_norm, 0) + valor
        
        logger.info(f"[V2-REC-RECONC] {len(docs_faturamento)} documentos no faturamento")
        logger.info(f"[V2-REC-RECONC] {len(pendentes)} adiantamentos pendentes")
        
        # Encontrar matches
        faturados = []
        for registro in pendentes:
            doc_norm = registro.documento_normalizado
            
            if doc_norm in docs_faturamento:
                # Atualizar registro com valor faturado
                valor_faturado = valores_faturamento.get(doc_norm, 0)
                self.state_manager.marcar_faturado(
                    documento_normalizado=doc_norm,
                    valor_faturado=valor_faturado,
                    comissao_real=0.0,  # Será calculado na reconciliação
                    data_faturamento=pd.Timestamp.now(),
                    colaborador_id=registro.colaborador_id
                )
                faturados.append(registro)
                logger.debug(f"[V2-REC-RECONC] Match encontrado: {doc_norm}")
        
        logger.info(f"[V2-REC-RECONC] {len(faturados)} adiantamentos faturados encontrados")
        
        return faturados
    
    def calcular_reconciliacao(
        self,
        registro: RegistroEstado,
        margem_pct: Optional[float] = None
    ) -> Optional[ResultadoReconciliacaoV2]:
        """Calcula reconciliação para um registro.
        
        No modo CC, usa regras de Centro de Custo (RegraCentroCusto) para
        determinar a comissão real. No modo hierarquia, usa regras hierárquicas.
        
        Args:
            registro: Registro de estado (deve estar FATURADO).
            margem_pct: Margem para cálculo da comissão real.
            
        Returns:
            ResultadoReconciliacaoV2 ou None se erro.
        """
        if registro.estado != EstadoProcesso.FATURADO:
            logger.warning(f"[V2-REC-RECONC] Registro não está FATURADO: {registro.documento_normalizado}")
            return None
        
        # Obter colaborador - na V2, colaborador_id é o nome
        colaborador = self.colaboradores.get(registro.colaborador_id)
        if not colaborador:
            # Tentar por nome diretamente
            for c in self.colaboradores.values():
                if c.nome == registro.colaborador_id:
                    colaborador = c
                    break
        
        if not colaborador:
            logger.warning(f"[V2-REC-RECONC] Colaborador não encontrado: {registro.colaborador_id}")
            return None
        
        # Calcular comissão real conforme o modo
        if self.modo_cc and registro.centro_custo:
            comissao_real = self._calcular_comissao_real_cc(
                colaborador=colaborador,
                registro=registro
            )
        else:
            # Modo hierarquia: usar calcular_regular existente
            resultado_comissao = self.comissao_calculator.calcular_regular(
                colaborador=colaborador,
                documento=registro.documento_normalizado,
                documento_normalizado=registro.documento_normalizado,
                valor_faturado=registro.valor_faturado,
                margem_pct=margem_pct
            )
            comissao_real = resultado_comissao.comissao_calculada
        
        # Atualizar registro com comissão real
        registro.comissao_real = comissao_real
        
        # Calcular ajuste: Real - Adiantada
        ajuste = comissao_real - registro.comissao_adiantada
        
        # Determinar tipo de ajuste
        if abs(ajuste) < 0.01:
            tipo_ajuste = "ZERO"
        elif ajuste > 0:
            tipo_ajuste = "COMPLEMENTO"
        else:
            tipo_ajuste = "DEVOLUÇÃO"
        
        resultado = ResultadoReconciliacaoV2(
            documento_normalizado=registro.documento_normalizado,
            colaborador_id=colaborador.nome,  # V2 usa nome como ID
            colaborador_nome=colaborador.nome,
            valor_adiantado=registro.valor_adiantado,
            comissao_adiantada=registro.comissao_adiantada,
            valor_faturado=registro.valor_faturado,
            comissao_real=comissao_real,
            ajuste=ajuste,
            tipo_ajuste=tipo_ajuste,
            data_reconciliacao=pd.Timestamp.now()
        )
        
        logger.info(
            f"[V2-REC-RECONC] Reconciliação: {resultado.documento_normalizado} | "
            f"{resultado.colaborador_nome} | "
            f"Adiant={resultado.comissao_adiantada:.2f} | "
            f"Real={resultado.comissao_real:.2f} | "
            f"Ajuste={resultado.ajuste:.2f} ({resultado.tipo_ajuste})"
        )
        
        return resultado
    
    def _calcular_comissao_real_cc(
        self,
        colaborador: ColaboradorV2,
        registro: RegistroEstado
    ) -> float:
        """Calcula a comissão real usando regras de Centro de Custo.
        
        Busca a RegraCentroCusto do colaborador para o CC do documento
        e aplica a faixa correspondente ao valor faturado.
        
        Args:
            colaborador: Colaborador com regras_cc.
            registro: Registro com centro_custo e valor_faturado.
            
        Returns:
            Valor da comissão real (R$).
        """
        cc = registro.centro_custo
        regra_cc = colaborador.get_regra_cc(cc)
        
        if not regra_cc:
            logger.warning(
                f"[V2-REC-RECONC] Colaborador '{colaborador.nome}' sem regra CC "
                f"para '{cc}'. Usando taxa_adiantamento como fallback."
            )
            taxa = colaborador.taxa_adiantamento_pct or 0.0
            return registro.valor_faturado * (taxa / 100.0)
        
        # Obter taxa da faixa baseada no valor faturado
        taxa = regra_cc.get_taxa_para_faturamento(registro.valor_faturado)
        split_decimal = regra_cc.get_split_decimal()
        
        comissao = registro.valor_faturado * (taxa / 100.0) * split_decimal
        
        logger.debug(
            f"[V2-REC-RECONC] Comissão real CC: {colaborador.nome} | "
            f"CC={cc} | ValorFat={registro.valor_faturado:.2f} | "
            f"Taxa={taxa}% | Split={split_decimal*100:.0f}% | Comissão={comissao:.2f}"
        )
        
        return comissao
    
    def processar_reconciliacoes(
        self,
        df_faturamento: pd.DataFrame,
        df_margens: Optional[pd.DataFrame] = None
    ) -> List[ResultadoReconciliacaoV2]:
        """Processa todas as reconciliações pendentes.
        
        Args:
            df_faturamento: DataFrame de faturamento.
            df_margens: DataFrame de margens (opcional).
            
        Returns:
            Lista de resultados de reconciliação.
        """
        # Verificar quais adiantamentos foram faturados
        faturados = self.verificar_faturamentos_pendentes(df_faturamento)
        
        if not faturados:
            return []
        
        # Preparar índice de margens
        margens_por_doc: Dict[str, float] = {}
        if df_margens is not None and not df_margens.empty:
            for _, row in df_margens.iterrows():
                doc = str(row.get("N° NF", "")).strip().upper()
                margem = float(row.get("Margem (%)", 0) or 0)
                if doc:
                    margens_por_doc[doc.zfill(6) if doc.isdigit() else doc] = margem
        
        # Processar reconciliações
        resultados = []
        
        # Buscar registros FATURADOS
        registros_faturados = self.state_manager.listar_faturados_pendentes()
        
        for registro in registros_faturados:
            margem = margens_por_doc.get(registro.documento_normalizado)
            
            resultado = self.calcular_reconciliacao(registro, margem)
            
            if resultado:
                # Marcar como reconciliado no state
                self.state_manager.marcar_reconciliado(
                    documento_normalizado=registro.documento_normalizado,
                    ajuste_aplicado=resultado.ajuste,
                    colaborador_id=registro.colaborador_id
                )
                resultados.append(resultado)
        
        # Salvar estado
        self.state_manager.salvar()
        
        logger.info(f"[V2-REC-RECONC] {len(resultados)} reconciliações processadas")
        
        return resultados
    
    def to_dataframe(
        self, 
        resultados: List[ResultadoReconciliacaoV2]
    ) -> pd.DataFrame:
        """Converte resultados para DataFrame.
        
        Args:
            resultados: Lista de resultados.
            
        Returns:
            DataFrame com resultados.
        """
        if not resultados:
            return pd.DataFrame(columns=[
                "Documento Normalizado", "Colaborador ID", "Colaborador Nome",
                "Valor Adiantado", "Comissão Adiantada", "Valor Faturado",
                "Comissão Real", "Ajuste", "Tipo Ajuste", "Data Reconciliação"
            ])
        
        return pd.DataFrame([r.to_dict() for r in resultados])
