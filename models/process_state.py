"""
Módulo para gerenciamento de estado dos processos.
Implementação mínima para permitir execução do cálculo de comissões.
"""

import pandas as pd
import os
from typing import Dict, Optional, Any


# Colunas esperadas no DataFrame de estado
ESTADO_COLUMNS = [
    "PROCESSO",
    "VALOR_TOTAL_PROCESSO",
    "TOTAL_ANTECIPACOES",
    "TOTAL_PAGAMENTOS_REGULARES",
    "TOTAL_PAGO_ACUMULADO",
    "TOTAL_ADIANTADO_COMISSAO",
    "STATUS_PAGAMENTO",
    "STATUS_RECONCILIACAO",
    "STATUS_PROCESSO_ANALISE",
    "STATUS_CALCULO_MEDIAS",
    "MES_ANO_FATURAMENTO",
    "TCMP",
    "FCMP",
    "ULTIMA_ATUALIZACAO",
]


class ProcessStateManager:
    """
    Gerencia o estado dos processos (adiantamentos, pagamentos, métricas).
    Implementação mínima para compatibilidade.
    """

    def __init__(self):
        """Inicializa o gerenciador de estado."""
        self.estado = pd.DataFrame(columns=ESTADO_COLUMNS)

    def load_from_file(self, filepath: str):
        """
        Carrega o estado de um arquivo Excel.

        Args:
            filepath: Caminho para o arquivo Excel
        """
        try:
            if os.path.exists(filepath):
                self.estado = pd.read_excel(filepath, sheet_name="ESTADO")
                # Normalizar colunas
                self.estado = self._normalize_estado(self.estado)
            else:
                # Criar DataFrame vazio com colunas esperadas
                self.estado = pd.DataFrame(columns=ESTADO_COLUMNS)
        except Exception:
            # Em caso de erro, criar DataFrame vazio
            self.estado = pd.DataFrame(columns=ESTADO_COLUMNS)

    def save_to_file(self, filepath: str):
        """
        Salva o estado em um arquivo Excel.

        Args:
            filepath: Caminho para o arquivo Excel
        """
        try:
            # Normalizar antes de salvar
            self.estado = self._normalize_estado(self.estado)

            # Criar diretório se não existir
            os.makedirs(
                os.path.dirname(filepath) if os.path.dirname(filepath) else ".",
                exist_ok=True,
            )

            # Salvar em Excel
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                self.estado.to_excel(writer, sheet_name="ESTADO", index=False)
        except Exception as e:
            # Log do erro mas não quebrar execução
            print(f"[AVISO] Falha ao salvar estado: {e}")

    def _normalize_estado(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza o DataFrame de estado garantindo que todas as colunas esperadas existam.

        Args:
            df: DataFrame a normalizar

        Returns:
            DataFrame normalizado
        """
        if df.empty:
            return pd.DataFrame(columns=ESTADO_COLUMNS)

        # Garantir que todas as colunas esperadas existam
        for col in ESTADO_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Manter apenas colunas esperadas + colunas extras que possam ter sido adicionadas
        return df

    def get_process_state(self, processo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o estado de um processo específico.

        Args:
            processo: ID do processo

        Returns:
            Dicionário com o estado do processo ou None se não encontrado
        """
        if self.estado.empty:
            return None

        processo_str = str(processo).strip()
        mask = self.estado["PROCESSO"].astype(str).str.strip() == processo_str
        matches = self.estado[mask]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()

    def get_process_metrics(self, processo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém as métricas (TCMP/FCMP) de um processo.

        Args:
            processo: ID do processo

        Returns:
            Dicionário com TCMP e FCMP ou None se não encontrado
        """
        state = self.get_process_state(processo)
        if state is None:
            return None

        import json

        tcmp = {}
        fcmp = {}

        try:
            if pd.notna(state.get("TCMP")):
                tcmp = (
                    json.loads(str(state["TCMP"]))
                    if isinstance(state["TCMP"], str)
                    else state["TCMP"]
                )
        except Exception:
            pass

        try:
            if pd.notna(state.get("FCMP")):
                fcmp = (
                    json.loads(str(state["FCMP"]))
                    if isinstance(state["FCMP"], str)
                    else state["FCMP"]
                )
        except Exception:
            pass

        return {"TCMP": tcmp, "FCMP": fcmp}

    def update_process_metrics(
        self,
        processo: str,
        mes_ano: Optional[str],
        tcmp_dict: Dict[str, float],
        fcmp_dict: Dict[str, float],
        status_calculo_medias: str = "PENDENTE",
    ):
        """
        Atualiza as métricas (TCMP/FCMP) de um processo.

        Args:
            processo: ID do processo
            mes_ano: Mês/ano do faturamento (formato "YYYY-MM")
            tcmp_dict: Dicionário com TCMP por colaborador
            fcmp_dict: Dicionário com FCMP por colaborador
            status_calculo_medias: Status do cálculo
        """
        import json

        processo_str = str(processo).strip()

        # Garantir que o processo existe no estado
        self._ensure_process_exists(processo_str)

        # Atualizar métricas
        mask = self.estado["PROCESSO"].astype(str).str.strip() == processo_str
        indices = self.estado[mask].index

        if len(indices) > 0:
            idx = indices[0]
            self.estado.loc[idx, "TCMP"] = json.dumps(tcmp_dict, ensure_ascii=False)
            self.estado.loc[idx, "FCMP"] = json.dumps(fcmp_dict, ensure_ascii=False)
            self.estado.loc[idx, "STATUS_CALCULO_MEDIAS"] = status_calculo_medias
            if mes_ano:
                self.estado.loc[idx, "MES_ANO_FATURAMENTO"] = mes_ano

    def update_payment_advanced(self, processo: str, valor: float):
        """
        Atualiza o valor de adiantamento de um processo.

        Args:
            processo: ID do processo
            valor: Valor do adiantamento
        """
        processo_str = str(processo).strip()
        self._ensure_process_exists(processo_str)

        mask = self.estado["PROCESSO"].astype(str).str.strip() == processo_str
        indices = self.estado[mask].index

        if len(indices) > 0:
            idx = indices[0]
            atual = float(self.estado.loc[idx, "TOTAL_ANTECIPACOES"] or 0.0)
            self.estado.loc[idx, "TOTAL_ANTECIPACOES"] = atual + valor

            # Atualizar total pago acumulado
            total_pago = float(self.estado.loc[idx, "TOTAL_PAGO_ACUMULADO"] or 0.0)
            self.estado.loc[idx, "TOTAL_PAGO_ACUMULADO"] = total_pago + valor

    def update_commission_advanced(self, processo: str, valor: float):
        """
        Atualiza o valor de comissão adiantada de um processo.

        Args:
            processo: ID do processo
            valor: Valor da comissão adiantada
        """
        processo_str = str(processo).strip()
        self._ensure_process_exists(processo_str)

        mask = self.estado["PROCESSO"].astype(str).str.strip() == processo_str
        indices = self.estado[mask].index

        if len(indices) > 0:
            idx = indices[0]
            atual = float(self.estado.loc[idx, "TOTAL_ADIANTADO_COMISSAO"] or 0.0)
            self.estado.loc[idx, "TOTAL_ADIANTADO_COMISSAO"] = atual + valor

    def update_payment_regular(self, processo: str, valor: float):
        """
        Atualiza o valor de pagamento regular de um processo.

        Args:
            processo: ID do processo
            valor: Valor do pagamento regular
        """
        processo_str = str(processo).strip()
        self._ensure_process_exists(processo_str)

        mask = self.estado["PROCESSO"].astype(str).str.strip() == processo_str
        indices = self.estado[mask].index

        if len(indices) > 0:
            idx = indices[0]
            atual = float(self.estado.loc[idx, "TOTAL_PAGAMENTOS_REGULARES"] or 0.0)
            self.estado.loc[idx, "TOTAL_PAGAMENTOS_REGULARES"] = atual + valor

            # Atualizar total pago acumulado
            total_pago = float(self.estado.loc[idx, "TOTAL_PAGO_ACUMULADO"] or 0.0)
            self.estado.loc[idx, "TOTAL_PAGO_ACUMULADO"] = total_pago + valor

    def _ensure_process_exists(self, processo: str):
        """
        Garante que um processo existe no estado, criando uma entrada se necessário.

        Args:
            processo: ID do processo
        """
        if self.estado.empty:
            self.estado = pd.DataFrame(columns=ESTADO_COLUMNS)

        processo_str = str(processo).strip()
        mask = self.estado["PROCESSO"].astype(str).str.strip() == processo_str

        if mask.sum() == 0:
            # Criar nova entrada
            nova_linha = {col: None for col in ESTADO_COLUMNS}
            nova_linha["PROCESSO"] = processo_str
            nova_linha["TOTAL_ANTECIPACOES"] = 0.0
            nova_linha["TOTAL_PAGAMENTOS_REGULARES"] = 0.0
            nova_linha["TOTAL_PAGO_ACUMULADO"] = 0.0
            nova_linha["TOTAL_ADIANTADO_COMISSAO"] = 0.0
            nova_linha["STATUS_PAGAMENTO"] = "PENDENTE"
            nova_linha["STATUS_RECONCILIACAO"] = "PENDENTE"
            nova_linha["STATUS_CALCULO_MEDIAS"] = "PENDENTE"

            self.estado = pd.concat(
                [self.estado, pd.DataFrame([nova_linha])], ignore_index=True
            )
