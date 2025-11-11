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
    
    def __init__(self, calculo_comissao_instance, mes: int, ano: int, base_path: str = "."):
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
        print(f"[RECEBIMENTO] [ETAPA 2.1/6] Parâmetros: mes={self.mes}, ano={self.ano}, base_path={self.base_path}")
        
        df_financeira = self.loader.carregar(
            mes=self.mes,
            ano=self.ano,
            base_path=self.base_path
        )
        
        print(f"[RECEBIMENTO] [ETAPA 2.1/6] Análise Financeira carregada: {len(df_financeira)} linha(s)")
        
        if df_financeira.empty:
            print("[RECEBIMENTO] [ETAPA 2.1/6] AVISO: DataFrame vazio! Gerando arquivo vazio...")
            # Gerar arquivo vazio
            return self._gerar_arquivo_vazio()
        
        # 2. Carregar estado anterior
        print("[RECEBIMENTO] [ETAPA 2.2/6] Carregando estado anterior...")
        arquivo_estado_anterior = f"Comissoes_Recebimento_{self.mes:02d}_{self.ano}.xlsx"
        caminho_estado = os.path.join(self.base_path, arquivo_estado_anterior)
        print(f"[RECEBIMENTO] [ETAPA 2.2/6] Caminho do estado anterior: {caminho_estado}")
        print(f"[RECEBIMENTO] [ETAPA 2.2/6] Arquivo existe? {os.path.exists(caminho_estado)}")
        
        carregou = self.state_manager.carregar_estado_anterior(caminho_estado)
        print(f"[RECEBIMENTO] [ETAPA 2.2/6] Estado carregado: {carregou}")
        print(f"[RECEBIMENTO] [ETAPA 2.2/6] Processos no estado: {len(self.state_manager.estado_df)}")
        
        # 3. Inicializar mapper
        print("[RECEBIMENTO] [ETAPA 2.3/6] Inicializando ProcessMapper...")
        df_comercial = self.calc_comissao.data.get("ANALISE_COMERCIAL_COMPLETA", pd.DataFrame())
        print(f"[RECEBIMENTO] [ETAPA 2.3/6] Análise Comercial carregada: {len(df_comercial)} linha(s)")
        
        mapper = ProcessMapper(df_comercial)
        print("[RECEBIMENTO] [ETAPA 2.3/6] ProcessMapper inicializado")
        
        # 4. Processar cada pagamento
        print(f"[RECEBIMENTO] [ETAPA 2.4/6] Processando {len(df_financeira)} pagamento(s)...")
        cont_adiant = 0
        cont_regular = 0
        cont_nao_mapeado = 0
        
        for idx, (_, row) in enumerate(df_financeira.iterrows(), 1):
            documento = str(row.get("Documento", "")).strip()
            valor = float(row.get("Valor Líquido", 0.0) or 0.0)
            data_pagamento = row.get("Data de Baixa")
            
            if idx <= 5 or idx % 10 == 0:  # Log detalhado para primeiros 5 e depois a cada 10
                print(f"[RECEBIMENTO] [ETAPA 2.4/6] Processando pagamento {idx}/{len(df_financeira)}: documento={documento}, valor={valor}")
            
            if valor <= 0 or not documento:
                if idx <= 5:
                    print(f"[RECEBIMENTO] [ETAPA 2.4/6] Pagamento {idx} ignorado: valor={valor}, documento='{documento}'")
                continue
            
            # Mapear documento → processo
            mapeamento = mapper.mapear_documento(documento)
            
            if not mapeamento.get('mapeado'):
                if idx <= 5:
                    print(f"[RECEBIMENTO] [ETAPA 2.4/6] Pagamento {idx} não mapeado: {mapeamento.get('motivo', 'N/A')}")
                # Registrar em avisos
                self.documentos_nao_mapeados.append({
                    'documento': documento,
                    'documento_6dig': documento[:6] if len(documento) >= 6 else documento,
                    'motivo': mapeamento.get('motivo', 'Não mapeado'),
                    'valor': valor,
                    'data_pagamento': data_pagamento
                })
                cont_nao_mapeado += 1
                continue
            
            processo = mapeamento['processo']
            tipo = mapeamento['tipo']
            
            if idx <= 5:
                print(f"[RECEBIMENTO] [ETAPA 2.4/6] Pagamento {idx} mapeado: processo={processo}, tipo={tipo}")
            
            # Obter ou criar processo no estado
            dados_processo = self.state_manager.obter_processo(processo)
            if not dados_processo:
                # Criar processo no estado
                valor_total = self.calc_comissao._get_valor_total_processo(processo)
                print(f"[RECEBIMENTO] [ETAPA 2.4/6] Criando novo processo no estado: {processo}, valor_total={valor_total}")
                self.state_manager.criar_processo(processo, valor_total)
            
            # Processar conforme tipo
            if tipo == 'ADIANTAMENTO':
                cont_adiant += 1
                self._processar_adiantamento(
                    processo, valor, documento, data_pagamento
                )
            else:  # PAGAMENTO_REGULAR
                cont_regular += 1
                self._processar_pagamento_regular(
                    processo, valor, documento, data_pagamento
                )
        
        print(f"[RECEBIMENTO] [ETAPA 2.4/6] Processamento concluído:")
        print(f"[RECEBIMENTO] [ETAPA 2.4/6]   - Adiantamentos processados: {cont_adiant}")
        print(f"[RECEBIMENTO] [ETAPA 2.4/6]   - Pagamentos regulares processados: {cont_regular}")
        print(f"[RECEBIMENTO] [ETAPA 2.4/6]   - Não mapeados: {cont_nao_mapeado}")
        print(f"[RECEBIMENTO] [ETAPA 2.4/6]   - Total comissões adiantamentos: {len(self.comissoes_adiantamentos)}")
        print(f"[RECEBIMENTO] [ETAPA 2.4/6]   - Total comissões regulares: {len(self.comissoes_regulares)}")
        
        # 5. Calcular métricas para processos faturados no mês
        print("[RECEBIMENTO] [ETAPA 2.5/6] Calculando métricas para processos faturados no mês...")
        self._calcular_metricas_processos_faturados()
        print("[RECEBIMENTO] [ETAPA 2.5/6] Cálculo de métricas concluído")
        
        # 6. Gerar arquivo de saída
        print("[RECEBIMENTO] [ETAPA 2.6/6] Gerando arquivo de saída...")
        arquivo_gerado = self._gerar_arquivo_saida()
        print(f"[RECEBIMENTO] [ETAPA 2.6/6] Arquivo gerado: {arquivo_gerado}")
        
        return arquivo_gerado
    
    def _processar_adiantamento(
        self,
        processo: str,
        valor: float,
        documento: str,
        data_pagamento: datetime
    ):
        """Processa um adiantamento."""
        print(f"[RECEBIMENTO] [ADIANTAMENTO] Processando adiantamento: processo={processo}, valor={valor}, documento={documento}")
        
        # Calcular TCMP temporária (sem FC, pois ainda não foi faturado)
        print(f"[RECEBIMENTO] [ADIANTAMENTO] Calculando TCMP para processo {processo}...")
        metricas = self.metricas_calc.calcular_metricas_processo(
            processo, self.mes, self.ano
        )
        
        tcmp_dict = metricas.get('TCMP', {})
        print(f"[RECEBIMENTO] [ADIANTAMENTO] TCMP calculado: {len(tcmp_dict)} colaborador(es)")
        
        if not tcmp_dict:
            print(f"[RECEBIMENTO] [ADIANTAMENTO] AVISO: TCMP vazio para processo {processo}. Pulando...")
            # Se não conseguir calcular TCMP, pular
            return
        
        # Calcular comissões
        print(f"[RECEBIMENTO] [ADIANTAMENTO] Calculando comissões para {len(tcmp_dict)} colaborador(es)...")
        comissoes = self.comissao_calc.calcular_adiantamento(
            processo=processo,
            valor=valor,
            tcmp_dict=tcmp_dict,
            documento=documento,
            data_pagamento=data_pagamento
        )
        
        print(f"[RECEBIMENTO] [ADIANTAMENTO] {len(comissoes)} comissão(ões) calculada(s)")
        
        # Adicionar mês de cálculo
        mes_calc = f"{self.mes:02d}/{self.ano}"
        for comissao in comissoes:
            comissao['mes_calculo'] = mes_calc
        
        self.comissoes_adiantamentos.extend(comissoes)
        
        # Atualizar estado
        total_comissao = sum(c['comissao_calculada'] for c in comissoes)
        print(f"[RECEBIMENTO] [ADIANTAMENTO] Total de comissão: R$ {total_comissao:.2f}")
        self.state_manager.atualizar_pagamento_adiantamento(
            processo, valor, total_comissao, data_pagamento
        )
        print(f"[RECEBIMENTO] [ADIANTAMENTO] Estado atualizado para processo {processo}")
    
    def _processar_pagamento_regular(
        self,
        processo: str,
        valor: float,
        documento: str,
        data_pagamento: datetime
    ):
        """Processa um pagamento regular."""
        print(f"[RECEBIMENTO] [REGULAR] Processando pagamento regular: processo={processo}, valor={valor}, documento={documento}")
        
        # Verificar se métricas já foram calculadas
        print(f"[RECEBIMENTO] [REGULAR] Verificando métricas salvas para processo {processo}...")
        metricas_salvas = self.state_manager.obter_metricas(processo)
        
        if metricas_salvas:
            print(f"[RECEBIMENTO] [REGULAR] Métricas encontradas no estado")
            tcmp_dict = metricas_salvas['TCMP']
            fcmp_dict = metricas_salvas['FCMP']
            mes_faturamento = self.state_manager.obter_processo(processo).get('MES_ANO_FATURAMENTO')
            print(f"[RECEBIMENTO] [REGULAR] TCMP: {len(tcmp_dict)} colaborador(es), FCMP: {len(fcmp_dict)} colaborador(es)")
        else:
            print(f"[RECEBIMENTO] [REGULAR] Métricas não encontradas. Calculando agora...")
            # Calcular métricas agora (processo foi faturado)
            metricas = self.metricas_calc.calcular_metricas_processo(
                processo, self.mes, self.ano
            )
            
            tcmp_dict = metricas.get('TCMP', {})
            fcmp_dict = metricas.get('FCMP', {})
            
            print(f"[RECEBIMENTO] [REGULAR] Métricas calculadas: TCMP={len(tcmp_dict)}, FCMP={len(fcmp_dict)}")
            
            if not tcmp_dict:
                print(f"[RECEBIMENTO] [REGULAR] AVISO: TCMP vazio para processo {processo}. Pulando...")
                # Se não conseguir calcular métricas, pular
                return
            
            # Salvar no estado
            mes_faturamento = f"{self.mes:02d}/{self.ano}"
            print(f"[RECEBIMENTO] [REGULAR] Salvando métricas no estado (mês faturamento: {mes_faturamento})...")
            self.state_manager.definir_metricas(
                processo, tcmp_dict, fcmp_dict, mes_faturamento
            )
            print(f"[RECEBIMENTO] [REGULAR] Métricas salvas no estado")
        
        # Calcular comissões
        print(f"[RECEBIMENTO] [REGULAR] Calculando comissões para {len(tcmp_dict)} colaborador(es)...")
        comissoes = self.comissao_calc.calcular_regular(
            processo=processo,
            valor=valor,
            tcmp_dict=tcmp_dict,
            fcmp_dict=fcmp_dict,
            documento=documento,
            data_pagamento=data_pagamento,
            mes_faturamento=mes_faturamento
        )
        
        print(f"[RECEBIMENTO] [REGULAR] {len(comissoes)} comissão(ões) calculada(s)")
        
        # Adicionar mês de cálculo
        mes_calc = f"{self.mes:02d}/{self.ano}"
        for comissao in comissoes:
            comissao['mes_calculo'] = mes_calc
        
        self.comissoes_regulares.extend(comissoes)
        
        # Atualizar estado
        total_comissao = sum(c['comissao_calculada'] for c in comissoes)
        print(f"[RECEBIMENTO] [REGULAR] Total de comissão: R$ {total_comissao:.2f}")
        self.state_manager.atualizar_pagamento_regular(
            processo, valor, total_comissao, data_pagamento
        )
        print(f"[RECEBIMENTO] [REGULAR] Estado atualizado para processo {processo}")
    
    def _calcular_metricas_processos_faturados(self):
        """Calcula métricas para processos faturados no mês de apuração."""
        df_comercial = self.calc_comissao.data.get("ANALISE_COMERCIAL_COMPLETA", pd.DataFrame())
        
        if df_comercial.empty:
            return
        
        # Encontrar processos faturados no mês
        proc_col = self._encontrar_coluna(df_comercial, ["processo", "Processo"])
        status_col = self._encontrar_coluna(df_comercial, ["Status Processo", "status processo"])
        data_col = self._encontrar_coluna(df_comercial, ["Dt Emissão", "dt emissão"])
        
        if not proc_col or not status_col:
            return
        
        # Filtrar processos faturados no mês
        mask_faturado = df_comercial[status_col].astype(str).str.strip().str.upper() == "FATURADO"
        
        if data_col:
            try:
                df_comercial[data_col] = pd.to_datetime(df_comercial[data_col], errors='coerce')
                mask_mes = df_comercial[data_col].dt.month == self.mes
                mask_ano = df_comercial[data_col].dt.year == self.ano
                mask = mask_faturado & mask_mes & mask_ano
            except Exception:
                mask = mask_faturado
        else:
            mask = mask_faturado
        
        processos_faturados = df_comercial[mask][proc_col].dropna().unique()
        
        # Calcular métricas para cada processo
        for processo in processos_faturados:
            processo = str(processo).strip()
            
            # Verificar se já tem métricas calculadas
            dados = self.state_manager.obter_processo(processo)
            if dados and dados.get('STATUS_CALCULO_MEDIAS') == 'CALCULADO':
                continue
            
            # Calcular métricas
            metricas = self.metricas_calc.calcular_metricas_processo(
                processo, self.mes, self.ano
            )
            
            tcmp_dict = metricas.get('TCMP', {})
            fcmp_dict = metricas.get('FCMP', {})
            
            if tcmp_dict:
                # Salvar no estado
                mes_faturamento = f"{self.mes:02d}/{self.ano}"
                self.state_manager.definir_metricas(
                    processo, tcmp_dict, fcmp_dict, mes_faturamento
                )
    
    def _gerar_arquivo_saida(self) -> str:
        """Gera arquivo de saída com todas as abas."""
        print("[RECEBIMENTO] [GERAÇÃO] Preparando DataFrames para geração do arquivo...")
        
        # Preparar DataFrames
        df_adiantamentos = pd.DataFrame(self.comissoes_adiantamentos)
        df_regulares = pd.DataFrame(self.comissoes_regulares)
        df_reconciliacoes = pd.DataFrame()  # Vazio para fase futura
        df_estado = self.state_manager.obter_dataframe_estado()
        df_avisos = pd.DataFrame(self.documentos_nao_mapeados)
        
        print(f"[RECEBIMENTO] [GERAÇÃO] DataFrames preparados:")
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Adiantamentos: {len(df_adiantamentos)} linha(s)")
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Regulares: {len(df_regulares)} linha(s)")
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Estado: {len(df_estado)} linha(s)")
        print(f"[RECEBIMENTO] [GERAÇÃO]   - Avisos: {len(df_avisos)} linha(s)")
        
        # Gerar arquivo
        print("[RECEBIMENTO] [GERAÇÃO] Chamando OutputGenerator.gerar()...")
        arquivo_gerado = self.output_gen.gerar(
            mes=self.mes,
            ano=self.ano,
            dados={
                'adiantamentos': df_adiantamentos,
                'regulares': df_regulares,
                'reconciliacoes': df_reconciliacoes,
                'estado': df_estado,
                'avisos': df_avisos
            },
            base_path=self.base_path
        )
        
        print(f"[RECEBIMENTO] [GERAÇÃO] Arquivo gerado com sucesso: {arquivo_gerado}")
        print(f"[RECEBIMENTO] [GERAÇÃO] Arquivo existe? {os.path.exists(arquivo_gerado)}")
        
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
                'adiantamentos': pd.DataFrame(),
                'regulares': pd.DataFrame(),
                'reconciliacoes': pd.DataFrame(),
                'estado': pd.DataFrame(),
                'avisos': pd.DataFrame()
            },
            base_path=self.base_path
        )
        print(f"[RECEBIMENTO] [GERAÇÃO] Arquivo vazio gerado: {arquivo_gerado}")
        return arquivo_gerado
    
    def _encontrar_coluna(self, df: pd.DataFrame, nomes_possiveis: list) -> Optional[str]:
        """Encontra uma coluna no DataFrame."""
        if df.empty:
            return None
        
        colunas_df = {col.lower().strip(): col for col in df.columns}
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_df:
                return colunas_df[nome_norm]
        
        return None

