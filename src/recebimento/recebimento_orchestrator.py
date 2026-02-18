"""
Orquestrador principal para cálculo de comissões por recebimento.
Integra todos os módulos e executa o fluxo completo.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional

from .core.comissao_calculator import ComissaoCalculator
from .core.metricas_calculator import MetricasCalculator
from .core.process_mapper import ProcessMapper
from .estado.state_manager import StateManager
from .io.analise_financeira_loader import AnaliseFinanceiraLoader
from .io.output_generator import RecebimentoOutputGenerator
from .reconciliacao import (
    ReconciliacaoAggregator,
    ReconciliacaoCalculator,
    ReconciliacaoDetector,
    ReconciliacaoValidator,
)

# Import do banco de dados master de comissões
from src.io.master_db_manager import MasterDBManager


class RecebimentoOrchestrator:
    """
    Orquestra todo o fluxo de cálculo de comissões por recebimento.
    """

    def __init__(
        self, calculo_comissao_instance, mes: int, ano: int, base_path: str = "."
    ):
        """
        Inicializa o orquestrador.

        Args:
            calculo_comissao_instance: Instância da classe CalculoComissao
            mes: Mês de apuração (1-12)
            ano: Ano de apuração (ex: 2025)
            base_path: Caminho base para arquivos
        """
        self.calc_comissao = calculo_comissao_instance
        self.mes = mes
        self.ano = ano
        self.base_path = base_path

        # Inicializar componentes
        self.loader = AnaliseFinanceiraLoader()
        self.state_manager = StateManager()
        self.metricas_calc = MetricasCalculator(calculo_comissao_instance)
        self.comissao_calc = ComissaoCalculator()
        self.output_gen = RecebimentoOutputGenerator()

        # Componentes de reconciliação
        self.reconciliacao_detector = ReconciliacaoDetector(self.state_manager, mes, ano)
        self.reconciliacao_calc = ReconciliacaoCalculator()
        self.reconciliacao_aggregator = ReconciliacaoAggregator()
        self.reconciliacao_validator = ReconciliacaoValidator()

        # DataFrames / listas de saída
        self.comissoes_adiantamentos = []
        self.comissoes_regulares = []
        self.reconciliacoes_calculadas = []
        self.documentos_nao_mapeados = []

    def _obter_dados_processo_comercial(self, processo_id: str) -> dict:
        """
        Obtém dados do processo da Análise Comercial de forma inteligente.
        
        Regras:
        - Se Status != FATURADO: usa Valor Orçado
        - Se Status == FATURADO: usa Valor Realizado
        
        Args:
            processo_id: ID do processo
            
        Returns:
            Dict com: valor_total, status_processo
        """
        df_comercial = self.calc_comissao.data.get("ANALISE_COMERCIAL_COMPLETA", pd.DataFrame())
        
        if df_comercial.empty:
            return {"valor_total": 0.0, "status_processo": "DESCONHECIDO"}
        
        # Encontrar colunas
        proc_col = self._encontrar_coluna(df_comercial, ["processo", "Processo"])
        status_col = self._encontrar_coluna(df_comercial, ["Status Processo", "status processo"])
        valor_realizado_col = self._encontrar_coluna(df_comercial, ["Valor Realizado", "valor realizado"])
        valor_orcado_col = self._encontrar_coluna(df_comercial, ["Valor Orçado", "valor orçado", "Valor Orcado"])
        
        if not proc_col:
            return {"valor_total": 0.0, "status_processo": "DESCONHECIDO"}
        
        # Filtrar pelo processo
        processo_str = str(processo_id).strip()
        mask = df_comercial[proc_col].astype(str).str.strip() == processo_str
        itens = df_comercial[mask]
        
        if itens.empty:
            return {"valor_total": 0.0, "status_processo": "DESCONHECIDO"}
        
        # Obter status (pegar do primeiro item)
        status = "DESCONHECIDO"
        if status_col:
            status_raw = itens.iloc[0].get(status_col, "")
            status = str(status_raw).strip().upper() if pd.notna(status_raw) and str(status_raw).strip() else "DESCONHECIDO"
        
        # Determinar qual coluna de valor usar baseado no status
        valor_total = 0.0
        
        if status == "FATURADO":
            # Processo faturado: usar Valor Realizado
            if valor_realizado_col:
                try:
                    valor_total = float(pd.to_numeric(itens[valor_realizado_col], errors="coerce").fillna(0.0).sum())
                except Exception:
                    pass
        else:
            # Processo não faturado (PENDENTE, ORCAMENTO, etc.): usar Valor Orçado
            if valor_orcado_col:
                try:
                    valor_total = float(pd.to_numeric(itens[valor_orcado_col], errors="coerce").fillna(0.0).sum())
                except Exception:
                    pass
        
        return {"valor_total": valor_total, "status_processo": status}

    def executar(self) -> str:
        """
        Executa o fluxo completo de cálculo de comissões por recebimento.

        Returns:
            Caminho do arquivo de saída gerado
        """
        print("[RECEBIMENTO] [ETAPA 2/6] Método executar() iniciado")

        # 1. Carregar Análise Financeira
        print("[RECEBIMENTO] [ETAPA 2.1/6] Carregando Análise Financeira...")
        print(
            f"[RECEBIMENTO] [ETAPA 2.1/6] Parâmetros: mes={self.mes}, ano={self.ano}, base_path={self.base_path}"
        )

        df_financeira = self.loader.carregar(
            mes=self.mes, ano=self.ano, base_path=self.base_path
        )

        print(
            f"[RECEBIMENTO] [ETAPA 2.1/6] Análise Financeira carregada: {len(df_financeira)} linha(s)"
        )

        if df_financeira.empty:
            print(
                "[RECEBIMENTO] [ETAPA 2.1/6] AVISO: DataFrame vazio! Gerando arquivo vazio..."
            )
            # Gerar arquivo vazio
            arquivo_gerado = self._gerar_arquivo_vazio()
            return arquivo_gerado

        # 2. Carregar estado anterior
        print("[RECEBIMENTO] [ETAPA 2.2/6] Carregando estado anterior...")
        arquivo_estado_anterior = "Estado_Processos_Recebimento.xlsx"
        caminho_estado = os.path.join(self.base_path, arquivo_estado_anterior)
        print(
            f"[RECEBIMENTO] [ETAPA 2.2/6] Caminho do estado anterior: {caminho_estado}"
        )
        print(
            f"[RECEBIMENTO] [ETAPA 2.2/6] Arquivo existe? {os.path.exists(caminho_estado)}"
        )

        carregou = self.state_manager.carregar_estado_anterior(caminho_estado)
        print(f"[RECEBIMENTO] [ETAPA 2.2/6] Estado carregado: {carregou}")
        print(
            f"[RECEBIMENTO] [ETAPA 2.2/6] Processos no estado: {len(self.state_manager.estado_df)}"
        )

        # 3. Inicializar mapper
        print("[RECEBIMENTO] [ETAPA 2.3/6] Inicializando ProcessMapper...")
        df_comercial = self.calc_comissao.data.get(
            "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
        )
        print(
            f"[RECEBIMENTO] [ETAPA 2.3/6] Análise Comercial carregada: {len(df_comercial)} linha(s)"
        )

        mapper = ProcessMapper(df_comercial)
        print("[RECEBIMENTO] [ETAPA 2.3/6] ProcessMapper inicializado")

        # 4. Processar cada pagamento
        print(
            f"[RECEBIMENTO] [ETAPA 2.4/6] Processando {len(df_financeira)} pagamento(s)..."
        )
        cont_adiant = 0
        cont_regular = 0
        cont_nao_mapeado = 0

        for idx, (_, row) in enumerate(df_financeira.iterrows(), 1):
            documento = str(row.get("Documento", "")).strip()
            valor = float(row.get("Valor Líquido", 0.0) or 0.0)
            data_pagamento = row.get("Data de Baixa")

            if (
                idx <= 5 or idx % 10 == 0
            ):  # Log detalhado para primeiros 5 e depois a cada 10
                print(
                    f"[RECEBIMENTO] [ETAPA 2.4/6] Processando pagamento {idx}/{len(df_financeira)}: documento={documento}, valor={valor}"
                )

            if valor <= 0 or not documento:
                if idx <= 5:
                    print(
                        f"[RECEBIMENTO] [ETAPA 2.4/6] Pagamento {idx} ignorado: valor={valor}, documento='{documento}'"
                    )
                continue

            # Mapear documento → processo
            mapeamento = mapper.mapear_documento(documento)

            if not mapeamento.get("mapeado"):
                if idx <= 5:
                    print(
                        f"[RECEBIMENTO] [ETAPA 2.4/6] Pagamento {idx} não mapeado: {mapeamento.get('motivo', 'N/A')}"
                    )
                # Registrar em avisos
                self.documentos_nao_mapeados.append(
                    {
                        "documento": documento,
                        "documento_6dig": (
                            documento[:6] if len(documento) >= 6 else documento
                        ),
                        "motivo": mapeamento.get("motivo", "Não mapeado"),
                        "valor": valor,
                        "data_pagamento": data_pagamento,
                    }
                )
                cont_nao_mapeado += 1
                continue

            processo = mapeamento["processo"]
            tipo = mapeamento["tipo"]

            if idx <= 5:
                print(
                    f"[RECEBIMENTO] [ETAPA 2.4/6] Pagamento {idx} mapeado: processo={processo}, tipo={tipo}"
                )

            # Obter ou criar processo no estado
            dados_processo = self.state_manager.obter_processo(processo)
            if not dados_processo:
                # Obter dados do processo da Análise Comercial (valor e status corretos)
                dados_comercial = self._obter_dados_processo_comercial(processo)
                valor_total = dados_comercial["valor_total"]
                status_processo = dados_comercial["status_processo"]
                
                print(
                    f"[RECEBIMENTO] [ETAPA 2.4/6] Criando novo processo no estado: {processo}, "
                    f"valor_total={valor_total}, status={status_processo}"
                )
                self.state_manager.criar_processo(processo, valor_total, status_processo)

            # Processar conforme tipo
            if tipo == "ADIANTAMENTO":
                cont_adiant += 1
                self._processar_adiantamento(processo, valor, documento, data_pagamento)
            else:  # PAGAMENTO_REGULAR
                cont_regular += 1
                self._processar_pagamento_regular(
                    processo, valor, documento, data_pagamento
                )

        print(f"[RECEBIMENTO] [ETAPA 2.4/6] Processamento concluído:")
        print(
            f"[RECEBIMENTO] [ETAPA 2.4/6]   - Adiantamentos processados: {cont_adiant}"
        )
        print(
            f"[RECEBIMENTO] [ETAPA 2.4/6]   - Pagamentos regulares processados: {cont_regular}"
        )
        print(f"[RECEBIMENTO] [ETAPA 2.4/6]   - Não mapeados: {cont_nao_mapeado}")
        print(
            f"[RECEBIMENTO] [ETAPA 2.4/6]   - Total comissões adiantamentos: {len(self.comissoes_adiantamentos)}"
        )
        print(
            f"[RECEBIMENTO] [ETAPA 2.4/6]   - Total comissões regulares: {len(self.comissoes_regulares)}"
        )

        # 5. Calcular métricas para processos faturados no mês
        print(
            "[RECEBIMENTO] [ETAPA 2.5/6] Calculando métricas para processos faturados no mês..."
        )
        self._calcular_metricas_processos_faturados()
        print("[RECEBIMENTO] [ETAPA 2.5/6] Cálculo de métricas concluído")

        # 6. Calcular reconciliações para processos faturados com adiantamentos
        print(
            "[RECEBIMENTO] [ETAPA 2.6/6] Calculando reconciliações para processos faturados..."
        )
        self._calcular_reconciliacoes()
        print("[RECEBIMENTO] [ETAPA 2.6/6] Cálculo de reconciliações concluído")

        # 7. Gerar arquivo de saída
        print("[RECEBIMENTO] [ETAPA 2.7/6] Gerando arquivo de saída...")
        arquivo_gerado = self._gerar_arquivo_saida()
        print(f"[RECEBIMENTO] [ETAPA 2.7/6] Arquivo gerado: {arquivo_gerado}")

        return arquivo_gerado

    def _processar_adiantamento(
        self, processo: str, valor: float, documento: str, data_pagamento: datetime
    ):
        """Processa um adiantamento."""
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Processando adiantamento: processo={processo}, valor={valor}, documento={documento}"
        )

        # Obter status do processo para passar ao cálculo de métricas
        dados_comercial = self._obter_dados_processo_comercial(processo)
        status_processo = dados_comercial.get("status_processo", "")

        # Calcular TCMP (FCMP será forçado a 1.0 pois ainda não foi faturado)
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Calculando TCMP para processo {processo} (status={status_processo})..."
        )
        metricas = self.metricas_calc.calcular_metricas_processo(
            processo, self.mes, self.ano, status_processo=status_processo
        )

        tcmp_dict = metricas.get("TCMP", {})
        fcmp_dict = metricas.get("FCMP", {})
        tcmp_detalhes = metricas.get("TCMP_DETALHES", {})
        fcmp_detalhes = metricas.get("FCMP_DETALHES", {})
        
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] TCMP calculado: {len(tcmp_dict)} colaborador(es)"
        )

        if not tcmp_dict:
            print(
                f"[RECEBIMENTO] [ADIANTAMENTO] AVISO: TCMP vazio para processo {processo}. Pulando..."
            )
            # Se não conseguir calcular TCMP, pular
            return

        # SALVAR MÉTRICAS NO ESTADO (importante para adiantamentos também!)
        # Mesmo sem faturamento, salvamos o TCMP calculado e FCMP=1.0
        print(f"[RECEBIMENTO] [ADIANTAMENTO] Salvando métricas no estado...")
        self.state_manager.salvar_metricas(
            processo, tcmp_dict, fcmp_dict, tcmp_detalhes, fcmp_detalhes
        )
        
        # Listar colaboradores envolvidos
        colaboradores_nomes = list(tcmp_dict.keys())
        self.state_manager.atualizar_colaboradores_envolvidos(processo, colaboradores_nomes)

        # Calcular comissões
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Calculando comissões para {len(tcmp_dict)} colaborador(es)..."
        )
        comissoes = self.comissao_calc.calcular_adiantamento(
            processo=processo,
            valor=valor,
            tcmp_dict=tcmp_dict,
            documento=documento,
            data_pagamento=data_pagamento,
        )

        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] {len(comissoes)} comissão(ões) calculada(s)"
        )

        # Adicionar mês de cálculo
        mes_calc = f"{self.mes:02d}/{self.ano}"
        for comissao in comissoes:
            comissao["mes_calculo"] = mes_calc

        self.comissoes_adiantamentos.extend(comissoes)

        # Atualizar estado
        total_comissao = sum(c["comissao_calculada"] for c in comissoes)
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Total de comissão: R$ {total_comissao:.2f}"
        )
        # Armazenar comissões adiantadas por colaborador (para futuras reconciliações)
        comissoes_por_colaborador = {
            c["nome_colaborador"]: c["comissao_calculada"] for c in comissoes
        }
        self.state_manager.armazenar_comissoes_adiantadas(
            processo, comissoes_por_colaborador
        )
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Comissões adiantadas armazenadas por colaborador: {comissoes_por_colaborador}"
        )

        self.state_manager.atualizar_pagamento_adiantamento(
            processo, valor, total_comissao, data_pagamento
        )
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Estado atualizado para processo {processo}"
        )

    def _processar_pagamento_regular(
        self, processo: str, valor: float, documento: str, data_pagamento: datetime
    ):
        """Processa um pagamento regular."""
        print(
            f"[RECEBIMENTO] [REGULAR] Processando pagamento regular: processo={processo}, valor={valor}, documento={documento}"
        )

        # Verificar se métricas já foram calculadas
        print(
            f"[RECEBIMENTO] [REGULAR] Verificando métricas salvas para processo {processo}..."
        )
        metricas_salvas = self.state_manager.obter_metricas(processo)

        # Inicializar mes_faturamento antes do if
        mes_faturamento = None
        
        if metricas_salvas:
            print(f"[RECEBIMENTO] [REGULAR] Métricas encontradas no estado")
            tcmp_dict = metricas_salvas["TCMP"]
            fcmp_rampa_dict = metricas_salvas.get("FCMP", {})
            fcmp_aplicado_dict = metricas_salvas.get("FCMP_APLICADO", {})
            fcmp_dict = fcmp_aplicado_dict if fcmp_aplicado_dict else fcmp_rampa_dict
            mes_faturamento = self.state_manager.obter_processo(processo).get(
                "MES_ANO_FATURAMENTO"
            )
            print(
                f"[RECEBIMENTO] [REGULAR] TCMP: {len(tcmp_dict)} colaborador(es), FCMP: {len(fcmp_dict)} colaborador(es)"
            )
        else:
            print(
                f"[RECEBIMENTO] [REGULAR] Métricas não encontradas. Calculando agora..."
            )
            # Calcular métricas agora (processo foi faturado)
            metricas = self.metricas_calc.calcular_metricas_processo(
                processo, self.mes, self.ano
            )

            tcmp_dict = metricas.get("TCMP", {})
            fcmp_rampa_dict = metricas.get("FCMP", {})
            fcmp_aplicado_dict = metricas.get("FCMP_APLICADO", {})
            fcmp_escada_detalhes = metricas.get("FCMP_ESCADA_DETALHES", {})
            fcmp_dict = fcmp_aplicado_dict if fcmp_aplicado_dict else fcmp_rampa_dict
            tcmp_detalhes = metricas.get("TCMP_DETALHES", {})
            fcmp_detalhes = metricas.get("FCMP_DETALHES", {})

            print(
                f"[RECEBIMENTO] [REGULAR] Métricas calculadas: TCMP={len(tcmp_dict)}, FCMP={len(fcmp_dict)}"
            )

            if not tcmp_dict:
                print(
                    f"[RECEBIMENTO] [REGULAR] AVISO: TCMP vazio para processo {processo}. Pulando..."
                )
                # Se não conseguir calcular métricas, pular
                return

            # Salvar no estado
            mes_faturamento = f"{self.mes:02d}/{self.ano}"
            print(
                f"[RECEBIMENTO] [REGULAR] Salvando métricas no estado (mês faturamento: {mes_faturamento})..."
            )
            self.state_manager.definir_metricas(
                processo,
                tcmp_dict,
                fcmp_rampa_dict,
                fcmp_aplicado_dict,
                mes_faturamento,
                tcmp_detalhes=tcmp_detalhes,
                fcmp_detalhes=fcmp_detalhes,
                fcmp_escada_detalhes=fcmp_escada_detalhes,
            )
            print(f"[RECEBIMENTO] [REGULAR] Métricas salvas no estado")

        # Calcular comissões
        print(
            f"[RECEBIMENTO] [REGULAR] Calculando comissões para {len(tcmp_dict)} colaborador(es)..."
        )
        comissoes = self.comissao_calc.calcular_regular(
            processo=processo,
            valor=valor,
            tcmp_dict=tcmp_dict,
            fcmp_dict=fcmp_dict,
            documento=documento,
            data_pagamento=data_pagamento,
            mes_faturamento=mes_faturamento,
        )

        print(f"[RECEBIMENTO] [REGULAR] {len(comissoes)} comissão(ões) calculada(s)")

        # Adicionar mês de cálculo
        mes_calc = f"{self.mes:02d}/{self.ano}"
        for comissao in comissoes:
            comissao["mes_calculo"] = mes_calc

        self.comissoes_regulares.extend(comissoes)

        # Atualizar estado
        total_comissao = sum(c["comissao_calculada"] for c in comissoes)
        print(f"[RECEBIMENTO] [REGULAR] Total de comissão: R$ {total_comissao:.2f}")
        self.state_manager.atualizar_pagamento_regular(
            processo, valor, total_comissao, data_pagamento
        )
        print(f"[RECEBIMENTO] [REGULAR] Estado atualizado para processo {processo}")

    def _calcular_metricas_processos_faturados(self):
        """
        Calcula métricas (TCMP/FCMP) para processos que:
        1. JÁ estão no ESTADO (apareceram em Análise Financeira)
        2. Foram faturados no mês de apuração (Status=FATURADO e Numero NF preenchido)
        """
        print(
            "[RECEBIMENTO] [MÉTRICAS] Iniciando cálculo de métricas para processos faturados..."
        )

        # Obter processos que estão no ESTADO
        processos_no_estado = self.state_manager.obter_processos_cadastrados()
        print(
            f"[RECEBIMENTO] [MÉTRICAS] Processos no ESTADO: {len(processos_no_estado)}"
        )

        if not processos_no_estado:
            print(
                "[RECEBIMENTO] [MÉTRICAS] Nenhum processo no ESTADO. Pulando cálculo de métricas."
            )
            return

        df_comercial = self.calc_comissao.data.get(
            "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
        )

        if df_comercial.empty:
            print(
                "[RECEBIMENTO] [MÉTRICAS] Análise Comercial vazia. Pulando cálculo de métricas."
            )
            return

        # Encontrar colunas
        proc_col = self._encontrar_coluna(df_comercial, ["processo", "Processo"])
        status_col = self._encontrar_coluna(
            df_comercial, ["Status Processo", "status processo"]
        )
        nf_col = self._encontrar_coluna(
            df_comercial, ["Numero NF", "numero nf", "número nf", "num nf"]
        )
        data_col = self._encontrar_coluna(df_comercial, ["Dt Emissão", "dt emissão"])

        print(
            f"[RECEBIMENTO] [MÉTRICAS] Colunas encontradas: proc_col={proc_col}, status_col={status_col}, nf_col={nf_col}, data_col={data_col}"
        )

        if not proc_col or not status_col or not nf_col:
            print(
                "[RECEBIMENTO] [MÉTRICAS] Colunas essenciais não encontradas. Pulando cálculo de métricas."
            )
            return

        # Para cada processo no ESTADO, verificar se foi faturado
        processos_calculados = 0
        for processo in processos_no_estado:
            # Verificar se já tem métricas calculadas
            dados = self.state_manager.obter_processo(processo)
            if dados and dados.get("STATUS_CALCULO_MEDIAS") == "CALCULADO":
                print(
                    f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: métricas já calculadas. Pulando..."
                )
                continue

            # Buscar processo na análise comercial
            itens_processo = df_comercial[
                df_comercial[proc_col].astype(str).str.strip() == str(processo).strip()
            ]

            if itens_processo.empty:
                print(
                    f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: não encontrado na Análise Comercial. Pulando..."
                )
                continue

            # Verificar se foi faturado
            primeiro_item = itens_processo.iloc[0]
            status = str(primeiro_item.get(status_col, "")).strip().upper()
            numero_nf = str(primeiro_item.get(nf_col, "")).strip()

            print(
                f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: status={status}, numero_nf={numero_nf}"
            )

            # Critério: Status == FATURADO E Numero NF não vazio
            eh_faturado = (status == "FATURADO") and (
                numero_nf not in ["", "nan", "NaN", "None"]
            )

            # Verificar data de emissão (se disponível)
            if eh_faturado and data_col:
                try:
                    dt_emissao = pd.to_datetime(
                        primeiro_item.get(data_col), errors="coerce"
                    )
                    if pd.notna(dt_emissao):
                        # Verificar se é do mês/ano de apuração
                        if dt_emissao.month != self.mes or dt_emissao.year != self.ano:
                            print(
                                f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: faturado em {dt_emissao.month:02d}/{dt_emissao.year}, diferente do mês de apuração {self.mes:02d}/{self.ano}. Pulando..."
                            )
                            eh_faturado = False
                except Exception as e:
                    print(
                        f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: erro ao verificar data de emissão: {e}"
                    )

            if not eh_faturado:
                print(
                    f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: não foi faturado no mês de apuração. Pulando..."
                )
                continue

            # Calcular métricas
            print(
                f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: calculando métricas..."
            )
            metricas = self.metricas_calc.calcular_metricas_processo(
                processo, self.mes, self.ano
            )

            tcmp_dict = metricas.get("TCMP", {})
            fcmp_rampa_dict = metricas.get("FCMP", {})
            fcmp_aplicado_dict = metricas.get("FCMP_APLICADO", {})
            fcmp_escada_detalhes = metricas.get("FCMP_ESCADA_DETALHES", {})
            tcmp_detalhes = metricas.get("TCMP_DETALHES", {})
            fcmp_detalhes = metricas.get("FCMP_DETALHES", {})

            fcmp_dict = fcmp_aplicado_dict if fcmp_aplicado_dict else fcmp_rampa_dict

            print(
                f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: TCMP={len(tcmp_dict)} colab(s), FCMP={len(fcmp_dict)} colab(s)"
            )

            if tcmp_dict:
                # Salvar no estado
                mes_faturamento = f"{self.mes:02d}/{self.ano}"
                self.state_manager.definir_metricas(
                    processo,
                    tcmp_dict,
                    fcmp_rampa_dict,
                    fcmp_aplicado_dict,
                    mes_faturamento,
                    tcmp_detalhes=tcmp_detalhes,
                    fcmp_detalhes=fcmp_detalhes,
                    fcmp_escada_detalhes=fcmp_escada_detalhes,
                )
                processos_calculados += 1
                print(
                    f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: métricas salvas no estado"
                )
            else:
                print(
                    f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: TCMP vazio, não salvando métricas"
                )

        print(
            f"[RECEBIMENTO] [MÉTRICAS] Cálculo de métricas concluído: {processos_calculados} processo(s) com métricas calculadas"
        )

    def _calcular_reconciliacoes(self):
        """
        Calcula reconciliações para processos faturados no mês que tiveram adiantamentos.
        """
        print("[RECEBIMENTO] [RECONCILIACAO] Iniciando cálculo de reconciliações...")

        processos_para_reconciliar = (
            self.reconciliacao_detector.detectar_processos_para_reconciliar()
        )

        print(
            f"[RECEBIMENTO] [RECONCILIACAO] {len(processos_para_reconciliar)} processo(s) detectado(s) para reconciliação"
        )

        if not processos_para_reconciliar:
            print(
                "[RECEBIMENTO] [RECONCILIACAO] Nenhum processo elegível para reconciliação."
            )
            return

        total_reconciliacoes = 0
        for processo_id in processos_para_reconciliar:
            print(
                f"[RECEBIMENTO] [RECONCILIACAO] Processando reconciliação do processo {processo_id}..."
            )

            dados = self.reconciliacao_detector.obter_dados_para_reconciliacao(
                processo_id
            )
            if not dados:
                print(
                    f"[RECEBIMENTO] [RECONCILIACAO] AVISO: Dados não encontrados para processo {processo_id}"
                )
                continue

            valido, mensagem = self.reconciliacao_validator.validar_dados_processo(
                dados
            )
            if not valido:
                print(
                    f"[RECEBIMENTO] [RECONCILIACAO] AVISO: Dados inválidos para processo {processo_id}: {mensagem}"
                )
                continue

            reconciliacoes_processo = (
                self.reconciliacao_calc.calcular_reconciliacao_processo(
                    processo_id=dados["processo"],
                    comissoes_adiantadas=dados["comissoes_adiantadas"],
                    tcmp_dict=dados["tcmp"],
                    fcmp_dict=dados["fcmp"],
                    mes_faturamento=dados["mes_faturamento"],
                )
            )

            if not reconciliacoes_processo:
                print(
                    f"[RECEBIMENTO] [RECONCILIACAO] Nenhuma reconciliação calculada para processo {processo_id}"
                )
                continue

            todas_validas, erros = (
                self.reconciliacao_validator.validar_todas_reconciliacoes(
                    reconciliacoes_processo
                )
            )
            if not todas_validas:
                print(
                    f"[RECEBIMENTO] [RECONCILIACAO] ERROS de validação no processo {processo_id}:"
                )
                for erro in erros:
                    print(f"[RECEBIMENTO] [RECONCILIACAO]   - {erro}")
                continue

            saldo_total = self.reconciliacao_calc.calcular_saldo_total_processo(
                reconciliacoes_processo
            )

            print(
                f"[RECEBIMENTO] [RECONCILIACAO] Processo {processo_id}: {len(reconciliacoes_processo)} reconciliação(ões), saldo total: R$ {saldo_total:.2f}"
            )

            self.reconciliacoes_calculadas.extend(reconciliacoes_processo)
            total_reconciliacoes += len(reconciliacoes_processo)

            # Marcar processo como reconciliado no estado
            self.state_manager.marcar_reconciliacao_calculada(processo_id)
            print(
                f"[RECEBIMENTO] [RECONCILIACAO] Processo {processo_id} marcado como reconciliado no ESTADO"
            )

        print(
            f"[RECEBIMENTO] [RECONCILIACAO] Reconciliações concluídas: {total_reconciliacoes} ajuste(s) calculado(s)"
        )

    def _gerar_arquivo_saida(self) -> str:
        """Gera arquivo de saída com todas as abas."""
        print(
            "[RECEBIMENTO] [GERAÇÃO] Preparando DataFrames para geração do arquivo..."
        )

        # Preparar DataFrames
        df_adiantamentos = pd.DataFrame(self.comissoes_adiantamentos)
        df_regulares = pd.DataFrame(self.comissoes_regulares)

        if self.reconciliacoes_calculadas:
            df_reconciliacoes = self.reconciliacao_aggregator.criar_dataframe_reconciliacoes(
                self.reconciliacoes_calculadas
            )
        else:
            df_reconciliacoes = pd.DataFrame()

        df_estado = self.state_manager.obter_dataframe_estado()
        df_avisos = pd.DataFrame(self.documentos_nao_mapeados)

        print(f"[RECEBIMENTO] [GERAÇÃO] DataFrames preparados:")
        print(
            f"[RECEBIMENTO] [GERAÇÃO]   - Adiantamentos: {len(df_adiantamentos)} linha(s)"
        )
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Regulares: {len(df_regulares)} linha(s)")
        print(
            f"[RECEBIMENTO] [GERAÇÃO]   - Reconciliações: {len(df_reconciliacoes)} linha(s)"
        )
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Estado: {len(df_estado)} linha(s)")
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Avisos: {len(df_avisos)} linha(s)")

        # Gerar arquivo
        print("[RECEBIMENTO] [GERAÇÃO] Chamando OutputGenerator.gerar()...")
        arquivo_gerado = self.output_gen.gerar(
            mes=self.mes,
            ano=self.ano,
            dados={
                "adiantamentos": df_adiantamentos,
                "regulares": df_regulares,
                "reconciliacoes": df_reconciliacoes,
                "estado": df_estado,
                "avisos": df_avisos,
            },
            base_path=self.base_path,
        )

        print(f"[RECEBIMENTO] [GERAÇÃO] Arquivo gerado com sucesso: {arquivo_gerado}")
        print(
            f"[RECEBIMENTO] [GERAÇÃO] Arquivo existe? {os.path.exists(arquivo_gerado)}"
        )

        if os.path.exists(arquivo_gerado):
            tamanho = os.path.getsize(arquivo_gerado)
            print(f"[RECEBIMENTO] [GERAÇÃO] Tamanho do arquivo: {tamanho} bytes")

        # === INTEGRAÇÃO: Salvar no Banco de Dados Master ===
        self._salvar_no_banco_dados_master(
            df_adiantamentos=df_adiantamentos,
            df_regulares=df_regulares,
            df_reconciliacoes=df_reconciliacoes,
        )

        return arquivo_gerado

    def _gerar_arquivo_vazio(self) -> str:
        """Gera arquivo vazio quando não há pagamentos."""
        print("[RECEBIMENTO] [GERAÇÃO] Gerando arquivo vazio (sem pagamentos)...")
        arquivo_gerado = self.output_gen.gerar(
            mes=self.mes,
            ano=self.ano,
            dados={
                "adiantamentos": pd.DataFrame(),
                "regulares": pd.DataFrame(),
                "reconciliacoes": pd.DataFrame(),
                "estado": pd.DataFrame(),
                "avisos": pd.DataFrame(),
            },
            base_path=self.base_path,
        )
        print(f"[RECEBIMENTO] [GERAÇÃO] Arquivo vazio gerado: {arquivo_gerado}")
        return arquivo_gerado

    def _encontrar_coluna(
        self, df: pd.DataFrame, nomes_possiveis: list
    ) -> Optional[str]:
        """Encontra uma coluna no DataFrame."""
        if df.empty:
            return None

        # Remover BOM (\ufeff) e normalizar
        colunas_df = {
            col.lower().strip().replace("\ufeff", ""): col for col in df.columns
        }

        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_df:
                return colunas_df[nome_norm]

        return None

    def salvar_estado_processos(self) -> bool:
        """
        Salva o estado dos processos no arquivo dedicado Estado_Processos_Recebimento.xlsx.
        
        Este método deve ser chamado após executar() para persistir o estado dos processos
        que tiveram ao menos um recebimento (adiantamento ou pagamento regular).
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        filepath = os.path.join(self.base_path, "Estado_Processos_Recebimento.xlsx")
        print(f"[RECEBIMENTO] [ESTADO] Salvando estado dos processos em: {filepath}")
        return self.state_manager.salvar_estado(filepath)

    def _salvar_no_banco_dados_master(
        self,
        df_adiantamentos: pd.DataFrame,
        df_regulares: pd.DataFrame,
        df_reconciliacoes: pd.DataFrame,
    ) -> None:
        """
        Salva as comissões de recebimento no banco de dados master (audit log).
        
        Implementa o protocolo de escrita segura:
        1. Verificação de lock
        2. Backup atômico
        3. Append dos novos registros
        4. Cálculo de hash de integridade
        5. Proteção read-only
        
        Args:
            df_adiantamentos: DataFrame com comissões de adiantamentos.
            df_regulares: DataFrame com comissões de pagamentos regulares.
            df_reconciliacoes: DataFrame com reconciliações calculadas.
        """
        try:
            # Inicializar o gerenciador do banco de dados
            master_db = MasterDBManager(base_path=self.base_path)
            
            total_salvos = 0
            
            # 1. Salvar Adiantamentos
            if not df_adiantamentos.empty:
                print(f"[MASTER_DB] Salvando {len(df_adiantamentos)} adiantamentos...")
                success, msg = master_db.append_comissoes(
                    df_comissoes=df_adiantamentos,
                    mes=self.mes,
                    ano=self.ano,
                    tipo_comissao="ADIANTAMENTO",
                )
                if success:
                    total_salvos += len(df_adiantamentos)
                    print(f"[MASTER_DB] Adiantamentos: {msg}")
                else:
                    print(f"[MASTER_DB] ERRO em adiantamentos: {msg}")
            
            # 2. Salvar Pagamentos Regulares
            if not df_regulares.empty:
                print(f"[MASTER_DB] Salvando {len(df_regulares)} pagamentos regulares...")
                success, msg = master_db.append_comissoes(
                    df_comissoes=df_regulares,
                    mes=self.mes,
                    ano=self.ano,
                    tipo_comissao="REGULAR",
                )
                if success:
                    total_salvos += len(df_regulares)
                    print(f"[MASTER_DB] Regulares: {msg}")
                else:
                    print(f"[MASTER_DB] ERRO em regulares: {msg}")
            
            # 3. Salvar Reconciliações
            if not df_reconciliacoes.empty:
                print(f"[MASTER_DB] Salvando {len(df_reconciliacoes)} reconciliações...")
                success, msg = master_db.append_comissoes(
                    df_comissoes=df_reconciliacoes,
                    mes=self.mes,
                    ano=self.ano,
                    tipo_comissao="RECONCILIACAO",
                )
                if success:
                    total_salvos += len(df_reconciliacoes)
                    print(f"[MASTER_DB] Reconciliações: {msg}")
                else:
                    print(f"[MASTER_DB] ERRO em reconciliações: {msg}")
            
            # Estatísticas finais
            if total_salvos > 0:
                stats = master_db.get_estatisticas()
                print(f"[MASTER_DB] === Resumo do Banco de Dados ===")
                print(f"[MASTER_DB]   - Total de registros: {stats.get('total_registros', 0)}")
                print(f"[MASTER_DB]   - Processos distintos: {stats.get('processos_distintos', 0)}")
                print(f"[MASTER_DB]   - Colaboradores distintos: {stats.get('colaboradores_distintos', 0)}")
            else:
                print("[MASTER_DB] Nenhuma comissão para salvar no banco de dados master.")
                
        except Exception as e:
            print(f"[MASTER_DB] ERRO inesperado ao salvar no banco de dados: {str(e)}")
