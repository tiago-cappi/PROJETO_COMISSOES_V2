"""
Valida cálculos de reconciliação.
"""

from typing import Dict, List, Tuple


class ReconciliacaoValidator:
    """
    Valida dados e cálculos de reconciliação.
    """

    def __init__(self) -> None:
        """Inicializa o validador."""

    def validar_dados_processo(self, dados: Dict) -> Tuple[bool, str]:
        """
        Valida se um processo tem todos os dados necessários para reconciliação.

        Args:
            dados: Dict com dados do processo

        Returns:
            (valido: bool, mensagem: str)
        """
        if not dados.get("processo"):
            return False, "ID do processo ausente"

        if not dados.get("tcmp"):
            return False, "TCMP não calculado"

        if not dados.get("fcmp"):
            return False, "FCMP não calculado"

        if not dados.get("comissoes_adiantadas"):
            return False, "Comissões adiantadas não encontradas"

        total_adiantamentos = float(dados.get("total_adiantamentos", 0.0) or 0.0)
        if total_adiantamentos <= 0:
            return False, "Não há adiantamentos para reconciliar"

        return True, "OK"

    def validar_reconciliacao(self, reconciliacao: Dict) -> Tuple[bool, str]:
        """
        Valida uma reconciliação calculada.

        Args:
            reconciliacao: Dict com dados da reconciliação

        Returns:
            (valido: bool, mensagem: str)
        """
        # Verificar campos obrigatórios
        campos_obrigatorios = [
            "processo",
            "colaborador",
            "fcmp",
            "comissao_adiantada_fc_1",
            "ajuste_reconciliacao",
        ]

        for campo in campos_obrigatorios:
            if campo not in reconciliacao:
                return False, f"Campo obrigatório '{campo}' ausente"

        try:
            fcmp = float(reconciliacao.get("fcmp", 0.0) or 0.0)
        except Exception:
            return False, "FCMP inválido"

        if fcmp < 0 or fcmp > 2.0:
            return False, f"FCMP fora da faixa esperada: {fcmp}"

        try:
            comissao_adiantada = float(
                reconciliacao.get("comissao_adiantada_fc_1", 0.0) or 0.0
            )
        except Exception:
            return False, "Comissão adiantada inválida"

        if comissao_adiantada < 0:
            return False, f"Comissão adiantada negativa: {comissao_adiantada}"

        # Validar consistência do cálculo
        try:
            diferenca_fc = float(reconciliacao.get("diferenca_fc", 0.0) or 0.0)
            ajuste = float(reconciliacao.get("ajuste_reconciliacao", 0.0) or 0.0)
        except Exception:
            return False, "Valores numéricos inválidos na reconciliação"

        ajuste_esperado = comissao_adiantada * diferenca_fc

        if abs(ajuste - ajuste_esperado) > 0.01:  # Tolerância de R$ 0,01
            return (
                False,
                f"Cálculo inconsistente: ajuste={ajuste} diferente do esperado={ajuste_esperado}",
            )

        return True, "OK"

    def validar_todas_reconciliacoes(
        self, reconciliacoes: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Valida todas as reconciliações.

        Args:
            reconciliacoes: Lista de reconciliações

        Returns:
            (todas_validas: bool, mensagens_erro: List[str])
        """
        erros: List[str] = []

        for idx, rec in enumerate(reconciliacoes):
            valido, mensagem = self.validar_reconciliacao(rec)
            if not valido:
                erros.append(
                    f"Reconciliação {idx + 1} (processo {rec.get('processo', '?')}): {mensagem}"
                )

        return len(erros) == 0, erros


