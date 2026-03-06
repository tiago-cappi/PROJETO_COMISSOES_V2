"""
src.metodo_v2.recebimento_v2.recebimento_orchestrator_v2 - Orquestrador de Recebimento V2

Orquestra todo o fluxo de cálculo de comissões por recebimento na V2:

1. Carrega Análise Financeira (pagamentos do mês)
2. Mapeia processos (ADIANTAMENTO vs REGULAR)
3. Identifica colaboradores de tipo "recebimento"
4. Calcula comissões de adiantamento
5. Verifica reconciliações (adiantamentos que foram faturados)
6. Gera arquivo de saída

Suporta ambos os modos: Hierarquia e Centro de Custo.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..models_v2 import ColaboradorV2, RegraComissao
from ..config_loader_v2 import ConfigLoaderV2
from .analise_financeira_loader_v2 import AnaliseFinanceiraLoaderV2
from .process_mapper_v2 import ProcessMapperV2, ProcessoMapeado, TipoProcesso
from .state_manager_v2 import StateManagerV2, EstadoProcesso
from .comissao_recebimento_calculator_v2 import (
    ComissaoRecebimentoCalculatorV2,
    ResultadoComissaoRecebimentoV2
)
from .reconciliacao_calculator_v2 import (
    ReconciliacaoCalculatorV2,
    ResultadoReconciliacaoV2
)
from .output_generator_v2 import OutputGeneratorV2


logger = logging.getLogger(__name__)


class RecebimentoOrchestratorV2:
    """Orquestrador principal de comissões por recebimento V2.
    
    Gerencia todo o fluxo desde carga de dados até geração de saída.
    """
    
    def __init__(
        self,
        base_path: str = ".",
        modo_cc: bool = False
    ):
        """Inicializa o orquestrador.
        
        Args:
            base_path: Caminho base (raiz do projeto).
            modo_cc: Se True, usa modo Centro de Custo.
        """
        self.base_path = Path(base_path)
        self.modo_cc = modo_cc
        
        # Componentes
        self.analise_loader = AnaliseFinanceiraLoaderV2()
        self.process_mapper = ProcessMapperV2()
        self.state_manager = StateManagerV2(str(self.base_path))
        self.output_generator = OutputGeneratorV2(str(self.base_path))
        
        # Dados carregados
        self.colaboradores: Dict[str, ColaboradorV2] = {}
        self.regras: Dict[str, RegraComissao] = {}
        
        # Calculadoras (inicializadas após carga de config)
        self.comissao_calculator: Optional[ComissaoRecebimentoCalculatorV2] = None
        self.reconciliacao_calculator: Optional[ReconciliacaoCalculatorV2] = None
        
        logger.info(f"[V2-REC-ORCH] Inicializado (modo_cc={modo_cc})")
    
    def carregar_configuracao(self) -> bool:
        """Carrega configuração do REGRAS_COMISSOES_V2.xlsx.
        
        Returns:
            True se carregou com sucesso.
        """
        try:
            # ConfigLoaderV2 usa o diretório config/ dentro do base_path
            config_path = str(self.base_path / "config" / "REGRAS_COMISSOES_V2.xlsx")
            config_loader = ConfigLoaderV2(config_path)
            
            # load() retorna Dict[str, ColaboradorV2] onde a chave é o nome
            colaboradores_dict = config_loader.load()
            
            # Na V2, o "ID" do colaborador é o próprio nome
            self.colaboradores = colaboradores_dict
            
            # As regras estão dentro de cada colaborador (não retornadas separadamente)
            # Para o modo CC, usamos regras_cc, para hierarquia usamos regras
            self.regras = {}  # Regras individuais não são carregadas separadamente
            
            # Inicializar calculadoras
            self.comissao_calculator = ComissaoRecebimentoCalculatorV2(
                colaboradores=self.colaboradores,
                regras=self.regras,
                modo_cc=self.modo_cc
            )
            
            self.reconciliacao_calculator = ReconciliacaoCalculatorV2(
                state_manager=self.state_manager,
                comissao_calculator=self.comissao_calculator,
                colaboradores=self.colaboradores,
                modo_cc=self.modo_cc
            )
            
            # Estatísticas
            colab_recebimento = [c for c in self.colaboradores.values() if c.recebe_por_recebimento]
            colab_faturamento = [c for c in self.colaboradores.values() if c.recebe_por_faturamento]
            
            logger.info(f"[V2-REC-ORCH] Colaboradores por recebimento: {len(colab_recebimento)}")
            logger.info(f"[V2-REC-ORCH] Colaboradores por faturamento: {len(colab_faturamento)}")
            
            return True
            
        except Exception as e:
            logger.error(f"[V2-REC-ORCH] Erro ao carregar configuração: {e}")
            return False
    
    def processar_mes(
        self,
        mes: int,
        ano: int,
        df_faturamento: Optional[pd.DataFrame] = None,
        df_margens: Optional[pd.DataFrame] = None
    ) -> Tuple[List[ResultadoComissaoRecebimentoV2], List[ResultadoReconciliacaoV2], str]:
        """Processa comissões por recebimento de um mês.
        
        Args:
            mes: Mês de apuração (1-12).
            ano: Ano de apuração.
            df_faturamento: DataFrame de faturamento (para reconciliação e vínculo CC).
            df_margens: DataFrame de margens (para reconciliação).
            
        Returns:
            Tupla (adiantamentos, reconciliacoes, caminho_arquivo).
        """
        logger.info(f"[V2-REC-ORCH] === Processando {mes:02d}/{ano} (modo_cc={self.modo_cc}) ===")
        
        # Garantir configuração carregada
        if not self.colaboradores:
            if not self.carregar_configuracao():
                logger.error("[V2-REC-ORCH] Falha ao carregar configuração")
                return ([], [], "")
        
        # 1. Carregar Análise Financeira
        logger.info("[V2-REC-ORCH] Etapa 1: Carregando Análise Financeira...")
        df_pagamentos = self.analise_loader.carregar(
            mes=mes,
            ano=ano,
            base_path=str(self.base_path)
        )
        
        if df_pagamentos.empty:
            logger.warning("[V2-REC-ORCH] Nenhum pagamento encontrado no período")
            return ([], [], "")
        
        logger.info(f"[V2-REC-ORCH] Pagamentos carregados: {len(df_pagamentos)}")
        
        # 2. Mapear processos
        logger.info("[V2-REC-ORCH] Etapa 2: Mapeando processos...")
        processos = self.process_mapper.mapear_pagamentos(df_pagamentos)
        logger.info(f"[V2-REC-ORCH] Processos mapeados: {len(processos)}")
        
        # 3. Processar comissões por recebimento
        # No modo CC, vincular pagamentos a colaboradores via regras de Centro de Custo
        logger.info("[V2-REC-ORCH] Etapa 3: Processando comissões por recebimento...")
        adiantamentos = self._processar_pagamentos_recebimento(
            processos=processos,
            df_faturamento=df_faturamento,
            mes=mes,
            ano=ano
        )
        
        # 4. Processar reconciliações
        logger.info("[V2-REC-ORCH] Etapa 4: Processando reconciliações...")
        reconciliacoes = []
        
        if df_faturamento is not None and not df_faturamento.empty:
            reconciliacoes = self.reconciliacao_calculator.processar_reconciliacoes(
                df_faturamento=df_faturamento,
                df_margens=df_margens
            )
        else:
            logger.info("[V2-REC-ORCH] Sem dados de faturamento para reconciliação")
        
        # 5. Gerar arquivo de saída
        logger.info("[V2-REC-ORCH] Etapa 5: Gerando arquivo de saída...")
        output_path = self.output_generator.gerar_arquivo(
            mes=mes,
            ano=ano,
            adiantamentos=adiantamentos,
            reconciliacoes=reconciliacoes,
            state_manager=self.state_manager
        )
        
        # 6. Salvar estado
        self.state_manager.salvar()
        
        # Resumo
        total_adiantamentos = sum(a.comissao_calculada for a in adiantamentos)
        total_ajustes = sum(r.ajuste for r in reconciliacoes)
        
        logger.info(f"[V2-REC-ORCH] === Resumo {mes:02d}/{ano} ===")
        logger.info(f"[V2-REC-ORCH] Adiantamentos: {len(adiantamentos)} = R$ {total_adiantamentos:,.2f}")
        logger.info(f"[V2-REC-ORCH] Reconciliações: {len(reconciliacoes)} = R$ {total_ajustes:,.2f}")
        logger.info(f"[V2-REC-ORCH] Arquivo gerado: {output_path}")
        
        return (adiantamentos, reconciliacoes, output_path)
    
    def _processar_pagamentos_recebimento(
        self,
        processos: List[ProcessoMapeado],
        df_faturamento: Optional[pd.DataFrame],
        mes: int,
        ano: int
    ) -> List[ResultadoComissaoRecebimentoV2]:
        """Processa pagamentos vinculando a colaboradores de recebimento via regras CC.
        
        Lógica para PAGAMENTOS REGULARES (não-COT):
        1. Para cada pagamento, buscar o documento na AC para obter o CC
        2. Encontrar colaboradores tipo "recebimento" com regras para esse CC
        3. Calcular FATURAMENTO total do colaborador no mês (para determinar a faixa)
        4. Usar a taxa da faixa encontrada (não taxa_adiantamento)
        5. Calcular comissão: valor_recebido × taxa_faixa × (split/100)
        
        Para ADIANTAMENTOS (COT):
        - Usa taxa_adiantamento_pct diretamente
        
        Args:
            processos: Lista de processos mapeados (pagamentos).
            df_faturamento: DataFrame da Análise Comercial.
            mes: Mês de apuração.
            ano: Ano de apuração.
            
        Returns:
            Lista de resultados de comissão.
        """
        if not processos:
            logger.info("[V2-REC-ORCH] Nenhum processo para processar")
            return []
        
        if df_faturamento is None or df_faturamento.empty:
            logger.warning("[V2-REC-ORCH] Sem dados de faturamento (AC) para vincular pagamentos")
            return []
        
        # Identificar colaboradores de recebimento
        colabs_recebimento = [
            c for c in self.colaboradores.values() 
            if c.recebe_por_recebimento and c.taxa_adiantamento_pct and c.taxa_adiantamento_pct > 0
        ]
        
        if not colabs_recebimento:
            logger.warning("[V2-REC-ORCH] Nenhum colaborador configurado para recebimento")
            return []
        
        logger.info(f"[V2-REC-ORCH] Colaboradores de recebimento: {[c.nome for c in colabs_recebimento]}")
        
        # Preparar AC para busca por documento
        df_ac = df_faturamento.copy()
        
        # Encontrar coluna de NF/documento na AC
        col_nf = None
        for col_name in ["Numero NF", "NF", "Documento", "documento", "numero_nf"]:
            if col_name in df_ac.columns:
                col_nf = col_name
                break
        
        if not col_nf:
            logger.error(f"[V2-REC-ORCH] Coluna de NF não encontrada na AC. Colunas: {df_ac.columns.tolist()}")
            return []
        
        # Encontrar coluna de Centro de Custo
        col_cc = None
        for col_name in ["Centro Custo-pedido", "Centro de Custo", "CC", "centro_custo"]:
            if col_name in df_ac.columns:
                col_cc = col_name
                break
        
        if not col_cc:
            logger.error(f"[V2-REC-ORCH] Coluna de CC não encontrada na AC. Colunas: {df_ac.columns.tolist()}")
            return []
        
        # Encontrar coluna de Valor
        col_valor = None
        for col_name in ["Valor Realizado", "Faturamento", "valor_realizado"]:
            if col_name in df_ac.columns:
                col_valor = col_name
                break
        
        if not col_valor:
            logger.error(f"[V2-REC-ORCH] Coluna de valor não encontrada na AC. Colunas: {df_ac.columns.tolist()}")
            return []
        
        # Normalizar coluna NF para string (remover .0 de floats e liderar zeros)
        df_ac[col_nf] = (
            df_ac[col_nf]
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)
            .str.lstrip('0')
            .replace('', '0')
            .str.upper()
        )
        
        # Pré-calcular faturamento por CC (para determinar faixas)
        faturamento_por_cc = df_ac.groupby(col_cc)[col_valor].sum().to_dict()
        logger.info(f"[V2-REC-ORCH] Faturamento por CC: {faturamento_por_cc}")
        
        resultados: List[ResultadoComissaoRecebimentoV2] = []
        
        for processo in processos:
            doc_norm = processo.documento_normalizado
            is_adiantamento = processo.tipo == TipoProcesso.ADIANTAMENTO
            
            # Buscar documento na AC
            mask_ac = df_ac[col_nf] == doc_norm
            df_doc = df_ac[mask_ac]
            
            if df_doc.empty:
                logger.debug(f"[V2-REC-ORCH] Documento {doc_norm} não encontrado na AC")
                continue
            
            # Obter Centro de Custo do documento
            cc_doc = str(df_doc.iloc[0][col_cc]).strip() if pd.notna(df_doc.iloc[0][col_cc]) else ""
            
            if not cc_doc:
                logger.debug(f"[V2-REC-ORCH] Documento {doc_norm} sem CC definido")
                continue
            
            # Obter faturamento total do CC para determinar faixa
            faturamento_cc = faturamento_por_cc.get(cc_doc, 0.0)
            
            tipo_doc = "ADIANTAMENTO" if is_adiantamento else "REGULAR"
            logger.debug(f"[V2-REC-ORCH] Doc {doc_norm} ({tipo_doc}): CC={cc_doc}, Valor={processo.valor_liquido}, FaturamentoCC={faturamento_cc}")
            
            # Buscar colaboradores de recebimento com regras para esse CC
            for colab in colabs_recebimento:
                if self.state_manager.registro_existe(doc_norm, colab.nome):
                    logger.debug(f"[V2-REC-ORCH] Registro já processado: {doc_norm} | {colab.nome}")
                    continue
                # Buscar regra CC do colaborador
                regra_cc = colab.get_regra_cc(cc_doc) if hasattr(colab, 'get_regra_cc') else None
                
                if not regra_cc:
                    # Colaborador não tem regra para este CC
                    continue
                
                # Obter split
                split_pct = regra_cc.split if regra_cc.split is not None else 100.0
                
                # Determinar taxa a aplicar
                if is_adiantamento:
                    # Para adiantamentos (COT): usar taxa_adiantamento_pct
                    taxa = colab.taxa_adiantamento_pct or 0.0
                    tipo_calculo = "ADIANTAMENTO_CC"
                    faixa_info = "taxa_adiantamento"
                else:
                    # Para pagamentos regulares: usar faixa baseada no faturamento do CC
                    taxa = self._obter_taxa_faixa(regra_cc, faturamento_cc)
                    tipo_calculo = "RECEBIMENTO_CC"
                    faixa_info = f"faixa_fat_{faturamento_cc:.0f}"
                
                fator_split = split_pct / 100.0
                comissao = processo.valor_liquido * (taxa / 100.0) * fator_split
                
                logger.info(
                    f"[V2-REC-ORCH] Comissão calculada: {colab.nome} | "
                    f"Doc={doc_norm} ({tipo_doc}) | CC={cc_doc} | "
                    f"ValorReceb={processo.valor_liquido:.2f} | FatCC={faturamento_cc:.2f} | "
                    f"Taxa={taxa}% | Split={split_pct}% | Comissão={comissao:.2f}"
                )
                
                resultado = ResultadoComissaoRecebimentoV2(
                    colaborador_id=colab.nome,
                    colaborador_nome=colab.nome,
                    documento=processo.documento,
                    documento_normalizado=doc_norm,
                    valor_base=processo.valor_liquido,
                    percentual_aplicado=taxa,
                    comissao_calculada=comissao,
                    tipo_calculo=tipo_calculo,
                    regra_utilizada=f"CC_{cc_doc}",
                    faixa_utilizada=f"{faixa_info}_split_{split_pct}%"
                )
                
                resultados.append(resultado)
                
                # Registrar no estado APENAS adiantamentos (COT).
                # Pagamentos regulares (NF) já são definitivos e NÃO devem
                # entrar no ciclo de reconciliação.
                if is_adiantamento:
                    self.state_manager.registrar_adiantamento(
                        documento_normalizado=doc_norm,
                        valor_adiantado=processo.valor_liquido,
                        comissao_adiantada=comissao,
                        data_adiantamento=processo.data_baixa or pd.Timestamp.now(),
                        colaborador_id=colab.nome,
                        mes=mes,
                        ano=ano,
                        centro_custo=cc_doc
                    )
        
        logger.info(f"[V2-REC-ORCH] Total de comissões calculadas: {len(resultados)}")
        return resultados
    
    def _obter_taxa_faixa(self, regra_cc, faturamento: float) -> float:
        """Obtém a taxa de comissão baseada no faturamento e nas faixas da regra CC.
        
        Percorre as faixas em ordem reversa (maior limite primeiro) e retorna
        a taxa da primeira faixa cujas condições se aplicam ao faturamento.
        
        Args:
            regra_cc: RegraCentroCusto com lista de faixas.
            faturamento: Faturamento total do CC no mês.
            
        Returns:
            Taxa de comissão em percentual (ex: 2.0 para 2%).
        """
        if not regra_cc.faixas:
            logger.warning(f"[V2-REC-ORCH] Regra CC {regra_cc.centro_custo} sem faixas definidas")
            return 0.0
        
        # Iterar em ordem reversa (faixa mais alta primeiro) para retornar
        # a faixa mais elevada que se aplique ao faturamento.
        for faixa in reversed(regra_cc.faixas):
            if faixa.aplica_ao_faturamento(faturamento):
                logger.debug(
                    f"[V2-REC-ORCH] Faixa encontrada: limite={faixa.limite_inferior}, "
                    f"taxa={faixa.taxa_comissao_pct}% para faturamento={faturamento}"
                )
                return faixa.taxa_comissao_pct
        
        logger.warning(
            f"[V2-REC-ORCH] Nenhuma faixa aplicável para CC={regra_cc.centro_custo}, "
            f"faturamento={faturamento}. Retornando 0%."
        )
        return 0.0
    
    def _processar_adiantamentos(
        self,
        adiantamentos_raw: List[ProcessoMapeado],
        mes: int,
        ano: int
    ) -> List[ResultadoComissaoRecebimentoV2]:
        """Método legado - mantido para compatibilidade.
        
        A lógica principal agora está em _processar_pagamentos_recebimento.
        """
        # Delegar para o novo método se houver dados de faturamento
        return []
    
    def calcular_adiantamento_colaborador(
        self,
        colaborador_nome: str,
        documento: str,
        documento_normalizado: str,
        valor: float,
        mes: int,
        ano: int
    ) -> Optional[ResultadoComissaoRecebimentoV2]:
        """Calcula adiantamento para um colaborador específico.
        
        Este método é chamado quando já sabemos qual colaborador deve receber
        a comissão de um determinado documento.
        
        Args:
            colaborador_nome: Nome do colaborador.
            documento: Documento original.
            documento_normalizado: Documento normalizado.
            valor: Valor do pagamento.
            mes: Mês de apuração.
            ano: Ano de apuração.
            
        Returns:
            ResultadoComissaoRecebimentoV2 ou None.
        """
        # Buscar colaborador
        colaborador = self.comissao_calculator.obter_colaborador_por_nome(colaborador_nome)
        
        if not colaborador:
            logger.warning(f"[V2-REC-ORCH] Colaborador não encontrado: {colaborador_nome}")
            return None
        
        if not colaborador.recebe_por_recebimento:
            logger.debug(f"[V2-REC-ORCH] Colaborador não recebe por recebimento: {colaborador_nome}")
            return None
        
        # Verificar se já processado
        if self.state_manager.registro_existe(documento_normalizado, colaborador.nome):
            logger.debug(f"[V2-REC-ORCH] Registro já processado: {documento_normalizado} | {colaborador.nome}")
            return None
        
        # Calcular comissão
        resultado = self.comissao_calculator.calcular_adiantamento(
            colaborador=colaborador,
            documento=documento,
            documento_normalizado=documento_normalizado,
            valor_pagamento=valor
        )
        
        # Registrar no state - V2 usa nome como ID
        self.state_manager.registrar_adiantamento(
            documento_normalizado=documento_normalizado,
            valor_adiantado=valor,
            comissao_adiantada=resultado.comissao_calculada,
            data_adiantamento=pd.Timestamp.now(),
            colaborador_id=colaborador.nome,  # V2 usa nome como ID
            mes=mes,
            ano=ano
        )
        
        return resultado
    
    def obter_colaboradores_recebimento(self) -> List[ColaboradorV2]:
        """Retorna lista de colaboradores que recebem por recebimento.
        
        Returns:
            Lista de ColaboradorV2.
        """
        return [c for c in self.colaboradores.values() if c.recebe_por_recebimento]
    
    def obter_colaboradores_faturamento(self) -> List[ColaboradorV2]:
        """Retorna lista de colaboradores que recebem por faturamento.
        
        Returns:
            Lista de ColaboradorV2.
        """
        return [c for c in self.colaboradores.values() if c.recebe_por_faturamento]
