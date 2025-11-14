"""
Detecta processos que necessitam de reconciliação.
"""

from typing import Dict, List

from ..estado.state_manager import StateManager


class ReconciliacaoDetector:
    """
    Detecta processos que necessitam de reconciliação no mês atual.

    Critérios:
    - Processo foi faturado no mês de apuração (STATUS_CALCULO_MEDIAS == "CALCULADO")
    - Processo teve adiantamentos (TOTAL_ANTECIPACOES > 0)
    - Reconciliação ainda não foi calculada (STATUS_RECONCILIACAO != "CALCULADO")
    """

    def __init__(self, state_manager: StateManager, mes: int, ano: int):
        """
        Inicializa o detector.

        Args:
            state_manager: Gerenciador de estado
            mes: Mês de apuração
            ano: Ano de apuração
        """
        self.state_manager = state_manager
        self.mes = mes
        self.ano = ano

    def detectar_processos_para_reconciliar(self) -> List[str]:
        """
        Detecta processos que necessitam reconciliação.

        Returns:
            Lista de IDs de processos
        """
        processos_para_reconciliar: List[str] = []

        todos_processos = self.state_manager.obter_processos_cadastrados()

        for processo_id in todos_processos:
            if self._processo_necessita_reconciliacao(processo_id):
                processos_para_reconciliar.append(str(processo_id))

        return processos_para_reconciliar

    def _processo_necessita_reconciliacao(self, processo_id: str) -> bool:
        """
        Verifica se um processo específico necessita reconciliação.

        Args:
            processo_id: ID do processo

        Returns:
            True se necessita reconciliação
        """
        processo = self.state_manager.obter_processo(processo_id)
        if not processo:
            return False

        # Critério 1: Foi faturado (métricas calculadas)
        if processo.get("STATUS_CALCULO_MEDIAS") != "CALCULADO":
            return False

        # Critério 2: Faturado no mês de apuração
        mes_faturamento = str(processo.get("MES_ANO_FATURAMENTO", "") or "").strip()
        mes_esperado = f"{self.mes:02d}/{self.ano}"
        if mes_faturamento != mes_esperado:
            return False

        # Critério 3: Teve adiantamentos
        try:
            total_adiantamentos = float(processo.get("TOTAL_ANTECIPACOES", 0.0) or 0.0)
        except Exception:
            total_adiantamentos = 0.0

        if total_adiantamentos <= 0:
            return False

        # Critério 4: Reconciliação ainda não calculada
        status_reconciliacao = str(
            processo.get("STATUS_RECONCILIACAO", "PENDENTE") or "PENDENTE"
        ).upper()
        if status_reconciliacao == "CALCULADO":
            return False

        return True

    def obter_dados_para_reconciliacao(self, processo_id: str) -> Dict:
        """
        Obtém todos os dados necessários para reconciliação de um processo.

        Args:
            processo_id: ID do processo

        Returns:
            Dict com dados completos do processo
        """
        processo = self.state_manager.obter_processo(processo_id)
        if not processo:
            return {}

        # Obter métricas
        metricas = self.state_manager.obter_metricas(processo_id)
        tcmp_dict = metricas.get("TCMP", {}) if metricas else {}
        fcmp_dict = metricas.get("FCMP", {}) if metricas else {}

        # Obter comissões adiantadas
        comissoes_adiantadas = self.state_manager.obter_comissoes_adiantadas(
            processo_id
        )

        try:
            valor_total_processo = float(
                processo.get("VALOR_TOTAL_PROCESSO", 0.0) or 0.0
            )
        except Exception:
            valor_total_processo = 0.0

        try:
            total_adiantamentos = float(
                processo.get("TOTAL_ANTECIPACOES", 0.0) or 0.0
            )
        except Exception:
            total_adiantamentos = 0.0

        try:
            total_comissao_adiantamentos = float(
                processo.get("TOTAL_COMISSAO_ANTECIPACOES", 0.0) or 0.0
            )
        except Exception:
            total_comissao_adiantamentos = 0.0

        return {
            "processo": str(processo_id).strip(),
            "valor_total_processo": valor_total_processo,
            "total_adiantamentos": total_adiantamentos,
            "total_comissao_adiantamentos": total_comissao_adiantamentos,
            "tcmp": tcmp_dict,
            "fcmp": fcmp_dict,
            "comissoes_adiantadas": comissoes_adiantadas,
            "mes_faturamento": mes_faturamento,
            "colaboradores_envolvidos": processo.get("COLABORADORES_ENVOLVIDOS", ""),
        }


