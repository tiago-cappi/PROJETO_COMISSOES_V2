"""
Orquestrador principal para cálculo de comissões por recebimento.
Integra todos os módulos e executa o fluxo completo.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional

from .io.analise_financeira_loader import AnaliseFinanceiraLoader
from .core.process_mapper import ProcessMapper
from .estado.state_manager import StateManager
from .core.metricas_calculator import MetricasCalculator
from .core.comissao_calculator import ComissaoCalculator
from .io.output_generator import RecebimentoOutputGenerator


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

        # DataFrames de saída
        self.comissoes_adiantamentos = []
        self.comissoes_regulares = []
        self.documentos_nao_mapeados = []

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
            # Gerar PDF de auditoria mesmo sem pagamentos (pode ter processos no estado)
            print(
                "[RECEBIMENTO] [ETAPA 2.7/6] Verificando se deve gerar PDF de auditoria (arquivo vazio)..."
            )
            self._gerar_pdf_auditoria()
            return arquivo_gerado

        # 2. Carregar estado anterior
        print("[RECEBIMENTO] [ETAPA 2.2/6] Carregando estado anterior...")
        arquivo_estado_anterior = (
            f"Comissoes_Recebimento_{self.mes:02d}_{self.ano}.xlsx"
        )
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
                # Criar processo no estado
                valor_total = self.calc_comissao._get_valor_total_processo(processo)
                print(
                    f"[RECEBIMENTO] [ETAPA 2.4/6] Criando novo processo no estado: {processo}, valor_total={valor_total}"
                )
                self.state_manager.criar_processo(processo, valor_total)

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

        # 6. Gerar arquivo de saída
        print("[RECEBIMENTO] [ETAPA 2.6/6] Gerando arquivo de saída...")
        arquivo_gerado = self._gerar_arquivo_saida()
        print(f"[RECEBIMENTO] [ETAPA 2.6/6] Arquivo gerado: {arquivo_gerado}")

        # 7. Gerar PDF de auditoria (opcional)
        print(
            "[RECEBIMENTO] [ETAPA 2.7/6] Verificando se deve gerar PDF de auditoria..."
        )
        self._gerar_pdf_auditoria()

        return arquivo_gerado

    def _processar_adiantamento(
        self, processo: str, valor: float, documento: str, data_pagamento: datetime
    ):
        """Processa um adiantamento."""
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Processando adiantamento: processo={processo}, valor={valor}, documento={documento}"
        )

        # Calcular TCMP temporária (sem FC, pois ainda não foi faturado)
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] Calculando TCMP para processo {processo}..."
        )
        metricas = self.metricas_calc.calcular_metricas_processo(
            processo, self.mes, self.ano
        )

        tcmp_dict = metricas.get("TCMP", {})
        print(
            f"[RECEBIMENTO] [ADIANTAMENTO] TCMP calculado: {len(tcmp_dict)} colaborador(es)"
        )

        if not tcmp_dict:
            print(
                f"[RECEBIMENTO] [ADIANTAMENTO] AVISO: TCMP vazio para processo {processo}. Pulando..."
            )
            # Se não conseguir calcular TCMP, pular
            return

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

        if metricas_salvas:
            print(f"[RECEBIMENTO] [REGULAR] Métricas encontradas no estado")
            tcmp_dict = metricas_salvas["TCMP"]
            fcmp_dict = metricas_salvas["FCMP"]
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
            fcmp_dict = metricas.get("FCMP", {})

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
                processo, tcmp_dict, fcmp_dict, mes_faturamento
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
            fcmp_dict = metricas.get("FCMP", {})

            print(
                f"[RECEBIMENTO] [MÉTRICAS] Processo {processo}: TCMP={len(tcmp_dict)} colab(s), FCMP={len(fcmp_dict)} colab(s)"
            )

            if tcmp_dict:
                # Salvar no estado
                mes_faturamento = f"{self.mes:02d}/{self.ano}"
                self.state_manager.definir_metricas(
                    processo, tcmp_dict, fcmp_dict, mes_faturamento
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

    def _gerar_arquivo_saida(self) -> str:
        """Gera arquivo de saída com todas as abas."""
        print(
            "[RECEBIMENTO] [GERAÇÃO] Preparando DataFrames para geração do arquivo..."
        )

        # Preparar DataFrames
        df_adiantamentos = pd.DataFrame(self.comissoes_adiantamentos)
        df_regulares = pd.DataFrame(self.comissoes_regulares)
        df_reconciliacoes = pd.DataFrame()  # Vazio para fase futura
        df_estado = self.state_manager.obter_dataframe_estado()
        df_avisos = pd.DataFrame(self.documentos_nao_mapeados)

        print(f"[RECEBIMENTO] [GERAÇÃO] DataFrames preparados:")
        print(
            f"[RECEBIMENTO] [GERAÇÃO]   - Adiantamentos: {len(df_adiantamentos)} linha(s)"
        )
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Regulares: {len(df_regulares)} linha(s)")
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

    def _gerar_pdf_auditoria(self):
        """Gera PDF de auditoria (opcional)."""
        print(
            "[RECEBIMENTO] [AUDITORIA] ===== INÍCIO DO MÉTODO _gerar_pdf_auditoria ====="
        )
        try:
            # Verificar se ReportLab está disponível
            print(
                "[RECEBIMENTO] [AUDITORIA] Verificando disponibilidade do ReportLab..."
            )
            try:
                from reportlab.platypus import SimpleDocTemplate

                reportlab_disponivel = True
                print("[RECEBIMENTO] [AUDITORIA] ReportLab disponível!")
            except ImportError as e:
                reportlab_disponivel = False
                print(f"[RECEBIMENTO] [AUDITORIA] ReportLab não disponível. Erro: {e}")
                print("[RECEBIMENTO] [AUDITORIA] Pulando geração de PDF.")
                return

            # Verificar parâmetro
            print(
                "[RECEBIMENTO] [AUDITORIA] Verificando parâmetro gerar_pdf_auditoria..."
            )
            print(
                f"[RECEBIMENTO] [AUDITORIA] Params disponíveis: {list(self.calc_comissao.params.keys())}"
            )
            gerar_pdf = self.calc_comissao.params.get("gerar_pdf_auditoria", True)
            print(
                f"[RECEBIMENTO] [AUDITORIA] Valor do parâmetro gerar_pdf_auditoria: {gerar_pdf} (tipo: {type(gerar_pdf)})"
            )

            # Converter string "True"/"False" para boolean se necessário
            if isinstance(gerar_pdf, str):
                gerar_pdf = gerar_pdf.strip().lower() in ["true", "1", "yes", "sim"]
                print(
                    f"[RECEBIMENTO] [AUDITORIA] Parâmetro convertido de string para boolean: {gerar_pdf}"
                )

            if not gerar_pdf:
                print(
                    "[RECEBIMENTO] [AUDITORIA] Geração de PDF desativada por parâmetro. Pulando..."
                )
                return

            if not reportlab_disponivel:
                print(
                    "[RECEBIMENTO] [AUDITORIA] ReportLab não está instalado. Pulando geração de PDF."
                )
                return

            print("[RECEBIMENTO] [AUDITORIA] Iniciando geração de PDF de auditoria...")

            # Tentar importar o módulo de auditoria
            try:
                from auditoria_pdf import AuditoriaOrchestrator

                print(
                    "[RECEBIMENTO] [AUDITORIA] Módulo auditoria_pdf importado com sucesso!"
                )
            except ImportError as e:
                print(
                    f"[RECEBIMENTO] [AUDITORIA] ERRO ao importar módulo auditoria_pdf: {e}"
                )
                print(
                    "[RECEBIMENTO] [AUDITORIA] Verifique se o módulo está no caminho correto."
                )
                import traceback

                traceback.print_exc()
                return
            except Exception as e:
                print(
                    f"[RECEBIMENTO] [AUDITORIA] ERRO inesperado ao importar auditoria_pdf: {e}"
                )
                import traceback

                traceback.print_exc()
                return

            print(
                "[RECEBIMENTO] [AUDITORIA] Criando instância do AuditoriaOrchestrator..."
            )
            try:
                auditoria = AuditoriaOrchestrator(
                    recebimento_orchestrator=self,
                    calc_comissao=self.calc_comissao,
                    mes=self.mes,
                    ano=self.ano,
                    base_path=self.base_path,
                )
                print(
                    "[RECEBIMENTO] [AUDITORIA] AuditoriaOrchestrator criado com sucesso!"
                )
            except Exception as e:
                print(
                    f"[RECEBIMENTO] [AUDITORIA] ERRO ao criar AuditoriaOrchestrator: {e}"
                )
                import traceback

                traceback.print_exc()
                return

            print("[RECEBIMENTO] [AUDITORIA] Chamando método gerar_auditoria()...")
            try:
                arquivo_pdf = auditoria.gerar_auditoria()

                if arquivo_pdf:
                    print(
                        f"[RECEBIMENTO] [AUDITORIA] PDF de auditoria gerado: {arquivo_pdf}"
                    )
                else:
                    print(
                        "[RECEBIMENTO] [AUDITORIA] PDF não gerado (sem dados ou erro)."
                    )
            except Exception as e:
                print(
                    f"[RECEBIMENTO] [AUDITORIA] ERRO ao chamar gerar_auditoria(): {e}"
                )
                import traceback

                traceback.print_exc()

        except Exception as e:
            print(
                f"[RECEBIMENTO] [AUDITORIA] ERRO GERAL ao gerar PDF de auditoria: {e}"
            )
            import traceback

            traceback.print_exc()
        finally:
            print(
                "[RECEBIMENTO] [AUDITORIA] ===== FIM DO MÉTODO _gerar_pdf_auditoria ====="
            )

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
