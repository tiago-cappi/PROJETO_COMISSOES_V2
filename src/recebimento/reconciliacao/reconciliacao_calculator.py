"""
Calcula ajustes de reconciliação por colaborador.
"""

from typing import Dict, List


class ReconciliacaoCalculator:
    """
    Calcula ajustes de reconciliação para cada colaborador.

    Fórmula:
        Reconciliação = Comissao_Adiantada × (FCMP - 1.0)
    """

    def __init__(self) -> None:
        """Inicializa o calculador."""

    def calcular_reconciliacao_processo(
        self,
        processo_id: str,
        comissoes_adiantadas: Dict[str, float],
        tcmp_dict: Dict[str, float],
        fcmp_dict: Dict[str, float],
        mes_faturamento: str,
    ) -> List[Dict]:
        """
        Calcula reconciliações para todos os colaboradores de um processo.

        Args:
            processo_id: ID do processo
            comissoes_adiantadas: Dict {nome_colaborador: comissao_adiantada}
            tcmp_dict: Dict {nome_colaborador: tcmp}
            fcmp_dict: Dict {nome_colaborador: fcmp}
            mes_faturamento: Mês/ano do faturamento

        Returns:
            Lista de dicts com reconciliações calculadas
        """
        reconciliacoes: List[Dict] = []

        # Para cada colaborador que recebeu adiantamento
        for colaborador, comissao_adiantada in comissoes_adiantadas.items():
            valor_adiantado = float(comissao_adiantada or 0.0)
            if valor_adiantado <= 0:
                continue

            # Obter FCMP (default 1.0 se não encontrado)
            fcmp = float(fcmp_dict.get(colaborador, 1.0) or 1.0)
            tcmp = float(tcmp_dict.get(colaborador, 0.0) or 0.0)

            # Calcular ajuste
            diferenca_fc = fcmp - 1.0
            ajuste_reconciliacao = valor_adiantado * diferenca_fc

            # Comissão que deveria ter sido paga com FCMP real
            comissao_deveria = valor_adiantado * fcmp

            reconciliacoes.append(
                {
                    "processo": str(processo_id).strip(),
                    "colaborador": colaborador,
                    "tcmp": tcmp,
                    "fcmp": fcmp,
                    "comissao_adiantada_fc_1": valor_adiantado,
                    "comissao_deveria_fc_real": comissao_deveria,
                    "diferenca_fc": diferenca_fc,
                    "ajuste_reconciliacao": ajuste_reconciliacao,
                    "mes_faturamento": mes_faturamento,
                }
            )

        return reconciliacoes

    def calcular_saldo_total_processo(self, reconciliacoes: List[Dict]) -> float:
        """
        Calcula saldo total de reconciliação do processo (soma dos ajustes).

        Args:
            reconciliacoes: Lista de reconciliações do processo

        Returns:
            Saldo total (geralmente negativo)
        """
        return float(
            sum(float(r.get("ajuste_reconciliacao", 0.0) or 0.0) for r in reconciliacoes)
        )


