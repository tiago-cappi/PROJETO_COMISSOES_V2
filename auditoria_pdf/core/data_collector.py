"""
Coletor de dados para auditoria.
Responsável por reunir todos os dados necessários para o relatório de auditoria.
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class AuditoriaDataCollector:
    """
    Coleta dados completos para auditoria de comissões por recebimento.
    """

    def __init__(self, recebimento_orchestrator, calc_comissao):
        """
        Inicializa o coletor de dados.

        Args:
            recebimento_orchestrator: Instância do RecebimentoOrchestrator
            calc_comissao: Instância do CalculoComissao
        """
        self.receb_orch = recebimento_orchestrator
        self.calc_comissao = calc_comissao
        self.state_manager = recebimento_orchestrator.state_manager
        self.metricas_calc = recebimento_orchestrator.metricas_calc

    def coletar_dados_auditoria(self, mes: int, ano: int) -> dict:
        """
        Coleta todos os dados necessários para auditoria do mês/ano.

        Args:
            mes: Mês de apuração (1-12)
            ano: Ano de apuração (ex: 2025)

        Returns:
            Dicionário com estrutura de dados para auditoria
        """
        print(f"[AUDITORIA] [COLETA] Iniciando coleta de dados para {mes:02d}/{ano}...")

        # Carregar DataFrames principais
        df_comercial = self.calc_comissao.data.get(
            "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
        )
        df_estado = self.state_manager.estado_df

        if df_estado.empty:
            print("[AUDITORIA] [COLETA] Estado vazio. Sem dados para auditar.")
            return self._estrutura_vazia(mes, ano)

        # Identificar processos com comissões no mês
        processos_com_comissoes = self._identificar_processos_com_comissoes(
            df_estado, mes, ano
        )
        print(
            f"[AUDITORIA] [COLETA] {len(processos_com_comissoes)} processo(s) com comissões no mês"
        )

        if not processos_com_comissoes:
            print(
                "[AUDITORIA] [COLETA] Nenhum processo com comissões. Gerando relatório vazio."
            )
            return self._estrutura_vazia(mes, ano)

        # Coletar dados de cada processo
        processos_dados = []
        for processo_id in processos_com_comissoes:
            print(f"[AUDITORIA] [COLETA] Coletando dados do processo {processo_id}...")
            dados_processo = self._coletar_dados_processo(
                processo_id, df_comercial, df_estado, mes, ano
            )
            if dados_processo:
                processos_dados.append(dados_processo)

        print(
            f"[AUDITORIA] [COLETA] Coleta concluída: {len(processos_dados)} processo(s)"
        )

        return {
            "mes": mes,
            "ano": ano,
            "data_geracao": datetime.now(),
            "processos": processos_dados,
            "total_processos": len(processos_dados),
        }

    def _estrutura_vazia(self, mes: int, ano: int) -> dict:
        """Retorna estrutura vazia para quando não há dados."""
        return {
            "mes": mes,
            "ano": ano,
            "data_geracao": datetime.now(),
            "processos": [],
            "total_processos": 0,
        }

    def _identificar_processos_com_comissoes(
        self, df_estado: pd.DataFrame, mes: int, ano: int
    ) -> List[str]:
        """
        Identifica processos que tiveram comissões calculadas no mês.

        Args:
            df_estado: DataFrame do estado
            mes: Mês de apuração
            ano: Ano de apuração

        Returns:
            Lista de IDs de processos
        """
        print(f"[AUDITORIA] [COLETA] Verificando processos no DataFrame de estado...")
        print(f"[AUDITORIA] [COLETA] Estado vazio? {df_estado.empty}")

        if df_estado.empty or "PROCESSO" not in df_estado.columns:
            print("[AUDITORIA] [COLETA] DataFrame vazio ou sem coluna PROCESSO")
            return []

        print(f"[AUDITORIA] [COLETA] Total de linhas no estado: {len(df_estado)}")
        print(f"[AUDITORIA] [COLETA] Colunas do estado: {list(df_estado.columns)}")

        # Filtrar processos com comissões calculadas (TCMP preenchido OU comissões registradas)
        processos = []
        for idx, row in df_estado.iterrows():
            processo_id = str(row.get("PROCESSO", "")).strip()
            if not processo_id:
                continue

            print(f"[AUDITORIA] [COLETA] Analisando processo {processo_id}...")

            # Verificar se tem TCMP calculado (coluna pode ser 'TCMP' ou 'TCMP_JSON')
            tcmp_str = str(row.get("TCMP_JSON", row.get("TCMP", ""))).strip()
            print(f"[AUDITORIA] [COLETA]   - TCMP_JSON: '{tcmp_str}'")

            # Verificar totais de comissões (colunas de totais no estado)
            total_comissao_adiant = float(
                row.get("TOTAL_COMISSAO_ANTECIPACOES", 0) or 0
            )
            total_comissao_reg = float(row.get("TOTAL_COMISSAO_REGULARES", 0) or 0)

            print(
                f"[AUDITORIA] [COLETA]   - Total Comissões Adiantamento: R$ {total_comissao_adiant:.2f}"
            )
            print(
                f"[AUDITORIA] [COLETA]   - Total Comissões Regulares: R$ {total_comissao_reg:.2f}"
            )

            # Incluir processo se tiver TCMP OU se tiver comissões calculadas (totais > 0)
            tem_tcmp = tcmp_str and tcmp_str not in ["", "{}", "nan", "NaN", "None"]
            tem_comissoes_adiant = total_comissao_adiant > 0
            tem_comissoes_reg = total_comissao_reg > 0

            if tem_tcmp or tem_comissoes_adiant or tem_comissoes_reg:
                print(
                    f"[AUDITORIA] [COLETA]   - ✓ Processo incluído (TCMP={tem_tcmp}, Adiant={tem_comissoes_adiant}, Reg={tem_comissoes_reg})"
                )
                processos.append(processo_id)
            else:
                print(f"[AUDITORIA] [COLETA]   - ✗ Processo excluído (sem comissões)")

        processos_unicos = list(set(processos))  # Remover duplicatas
        print(
            f"[AUDITORIA] [COLETA] Total de processos identificados: {len(processos_unicos)}"
        )
        return processos_unicos

    def _coletar_dados_processo(
        self,
        processo_id: str,
        df_comercial: pd.DataFrame,
        df_estado: pd.DataFrame,
        mes: int,
        ano: int,
    ) -> Optional[Dict]:
        """
        Coleta todos os dados de um processo específico.

        Args:
            processo_id: ID do processo
            df_comercial: DataFrame da análise comercial
            df_estado: DataFrame do estado
            mes: Mês de apuração
            ano: Ano de apuração

        Returns:
            Dicionário com dados do processo ou None se não encontrado
        """
        # Buscar processo na análise comercial
        proc_col = self._encontrar_coluna(df_comercial, ["Processo", "processo"])
        if not proc_col:
            print(
                f"[AUDITORIA] [COLETA] Coluna 'Processo' não encontrada na Análise Comercial"
            )
            return None

        itens_processo = df_comercial[
            df_comercial[proc_col].astype(str).str.strip() == str(processo_id).strip()
        ]

        if itens_processo.empty:
            print(
                f"[AUDITORIA] [COLETA] Processo {processo_id} não encontrado na Análise Comercial"
            )
            return None

        # Buscar no estado
        dados_estado = self.state_manager.obter_processo(processo_id)
        if not dados_estado:
            print(
                f"[AUDITORIA] [COLETA] Processo {processo_id} não encontrado no estado"
            )
            return None

        # Dados gerais do processo (primeira linha)
        primeira_linha = itens_processo.iloc[0]

        dados_gerais = {
            "processo_id": processo_id,
            "status": str(primeira_linha.get("Status Processo", "-")).strip(),
            "dt_emissao": primeira_linha.get("Dt Emissão"),
            "numero_nf": str(primeira_linha.get("Numero NF", "-")).strip(),
            "cliente": str(primeira_linha.get("Cliente", "-")).strip(),
            "operacao": str(primeira_linha.get("Operação", "-")).strip(),
            "valor_total": self._calcular_valor_total_processo(itens_processo),
        }

        # Itens do processo
        itens = self._coletar_itens_processo(itens_processo)

        # Pagamentos (do estado)
        pagamentos = self._coletar_pagamentos(dados_estado)

        # Colaboradores identificados
        colaboradores = self._coletar_colaboradores_processo(itens_processo)

        # Cálculos de TCMP
        calculos_tcmp = self._coletar_calculos_tcmp(
            processo_id, itens_processo, dados_estado
        )
        tcmp_dict = calculos_tcmp.get("tcmp_final", {})

        # Cálculos de FCMP
        calculos_fcmp = self._coletar_calculos_fcmp(
            processo_id, itens_processo, dados_estado
        )
        fcmp_dict = calculos_fcmp.get("fcmp_final", {})

        # Comissões calculadas (usar TCMP e FCMP coletados)
        comissoes = self._coletar_comissoes(
            dados_estado, tcmp_dict, fcmp_dict, mes, ano
        )

        return {
            "dados_gerais": dados_gerais,
            "itens": itens,
            "pagamentos": pagamentos,
            "colaboradores": colaboradores,
            "calculos_tcmp": calculos_tcmp,
            "calculos_fcmp": calculos_fcmp,
            "comissoes": comissoes,
        }

    def _calcular_valor_total_processo(self, itens_processo: pd.DataFrame) -> float:
        """Calcula valor total do processo somando todos os itens."""
        valor_col = self._encontrar_coluna(
            itens_processo, ["Valor Realizado", "valor realizado"]
        )
        if not valor_col:
            return 0.0

        try:
            return float(itens_processo[valor_col].sum())
        except Exception:
            return 0.0

    def _coletar_itens_processo(self, itens_processo: pd.DataFrame) -> List[Dict]:
        """Coleta detalhes de cada item do processo."""
        itens = []

        for idx, row in itens_processo.iterrows():
            item = {
                "codigo_produto": str(row.get("Código Produto", "-")).strip(),
                "descricao": str(row.get("Descrição Produto", "-")).strip(),
                "linha": str(row.get("Negócio", "-")).strip(),
                "grupo": str(row.get("Grupo", "-")).strip(),
                "subgrupo": str(row.get("Subgrupo", "-")).strip(),
                "tipo_mercadoria": str(row.get("Tipo de Mercadoria", "-")).strip(),
                "valor": float(row.get("Valor Realizado", 0)),
                "fabricante": str(row.get("Fabricante", "-")).strip(),
                "consultor_interno": str(row.get("Consultor Interno", "-")).strip(),
                "representante": str(row.get("Representante-pedido", "-")).strip(),
            }
            itens.append(item)

        return itens

    def _coletar_pagamentos(self, dados_estado: Dict) -> List[Dict]:
        """Coleta informações de pagamentos do estado."""
        pagamentos = []

        # O estado armazena apenas totais, não listas individuais
        # Vamos usar os totais e datas disponíveis

        # Adiantamentos
        total_adiant = float(dados_estado.get("TOTAL_ANTECIPACOES", 0) or 0)
        if total_adiant > 0:
            pagamentos.append(
                {
                    "tipo": "Adiantamento",
                    "documento": "COT*",  # Adiantamentos começam com COT
                    "data": dados_estado.get("DATA_PRIMEIRO_PAGAMENTO", "-"),
                    "valor": total_adiant,
                }
            )

        # Regulares
        total_reg = float(dados_estado.get("TOTAL_PAGAMENTOS_REGULARES", 0) or 0)
        if total_reg > 0:
            pagamentos.append(
                {
                    "tipo": "Regular",
                    "documento": "NF*",  # Pagamentos regulares são por NF
                    "data": dados_estado.get(
                        "DATA_ULTIMO_PAGAMENTO",
                        dados_estado.get("DATA_PRIMEIRO_PAGAMENTO", "-"),
                    ),
                    "valor": total_reg,
                }
            )

        return pagamentos

    def _coletar_colaboradores_processo(
        self, itens_processo: pd.DataFrame
    ) -> List[Dict]:
        """Coleta colaboradores envolvidos no processo."""
        from src.recebimento.core.identificador_colaboradores import (
            IdentificadorColaboradores,
        )

        # Obter primeiro item para pegar o processo
        if itens_processo.empty:
            return []

        primeiro_item = itens_processo.iloc[0]
        proc_col = self._encontrar_coluna(itens_processo, ["Processo", "processo"])
        if not proc_col:
            return []

        processo_id = str(primeiro_item.get(proc_col, "")).strip()
        if not processo_id:
            return []

        # Inicializar identificador com os argumentos corretos
        df_comercial = self.calc_comissao.data.get(
            "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
        )
        colaboradores_df = self.calc_comissao.data.get("COLABORADORES", pd.DataFrame())
        atribuicoes_df = self.calc_comissao.data.get("ATRIBUICOES", pd.DataFrame())
        recebe_por_recebimento_ids = getattr(
            self.calc_comissao, "recebe_por_recebimento", set()
        )

        identificador = IdentificadorColaboradores(
            df_analise_comercial=df_comercial,
            colaboradores_df=colaboradores_df,
            atribuicoes_df=atribuicoes_df,
            recebe_por_recebimento_ids=recebe_por_recebimento_ids,
        )

        # Identificar colaboradores do processo
        colaboradores = identificador.identificar_colaboradores(processo_id)

        # Converter para formato esperado
        colaboradores_formatados = []
        for colab in colaboradores:
            # Determinar tipo (operacional ou gestao)
            # Se está na análise comercial diretamente, é operacional
            # Se veio de ATRIBUICOES, é gestao
            tipo = "operacional"  # Default
            nome = colab.get("nome", "")

            # Verificar se é de gestão (está em ATRIBUICOES mas não aparece diretamente nos itens)
            consultor_col = self._encontrar_coluna(
                itens_processo, ["Consultor Interno", "consultor interno"]
            )
            representante_col = self._encontrar_coluna(
                itens_processo, ["Representante-pedido", "representante-pedido"]
            )

            eh_operacional = False
            if consultor_col:
                consultores = (
                    itens_processo[consultor_col].astype(str).str.strip().unique()
                )
                if nome in consultores:
                    eh_operacional = True
            if representante_col:
                representantes = (
                    itens_processo[representante_col].astype(str).str.strip().unique()
                )
                if nome in representantes:
                    eh_operacional = True

            if not eh_operacional:
                tipo = "gestao"

            colaboradores_formatados.append(
                {"nome": nome, "cargo": colab.get("cargo", ""), "tipo": tipo}
            )

        return colaboradores_formatados

    def _coletar_calculos_tcmp(
        self, processo_id: str, itens_processo: pd.DataFrame, dados_estado: Dict
    ) -> Dict:
        """Coleta detalhes do cálculo de TCMP."""
        import json

        # TCMP final do estado (coluna pode ser 'TCMP' ou 'TCMP_JSON')
        tcmp_json = dados_estado.get("TCMP_JSON", dados_estado.get("TCMP", "{}"))
        if isinstance(tcmp_json, str):
            try:
                tcmp_dict = json.loads(tcmp_json)
            except Exception:
                tcmp_dict = {}
        else:
            tcmp_dict = tcmp_json if isinstance(tcmp_json, dict) else {}

        # Calcular detalhes por item
        detalhes_itens = []
        for idx, item in itens_processo.iterrows():
            detalhes_item = self._calcular_taxa_item(item)
            if detalhes_item:
                detalhes_itens.append(detalhes_item)

        return {
            "tcmp_final": tcmp_dict,
            "detalhes_itens": detalhes_itens,
            "mes_faturamento": dados_estado.get("MES_FATURAMENTO", "-"),
        }

    def _coletar_calculos_fcmp(
        self, processo_id: str, itens_processo: pd.DataFrame, dados_estado: Dict
    ) -> Dict:
        """Coleta detalhes do cálculo de FCMP."""
        import json

        print(
            f"[AUDITORIA] [COLETA] [FCMP] Coletando FCMP para processo {processo_id}..."
        )

        # FCMP final do estado (coluna pode ser 'FCMP' ou 'FCMP_JSON')
        fcmp_json = dados_estado.get("FCMP_JSON", dados_estado.get("FCMP", "{}"))
        if isinstance(fcmp_json, str):
            try:
                fcmp_dict = json.loads(fcmp_json)
            except Exception:
                fcmp_dict = {}
        else:
            fcmp_dict = fcmp_json if isinstance(fcmp_json, dict) else {}

        print(f"[AUDITORIA] [COLETA] [FCMP] FCMP do estado: {fcmp_dict}")
        print(
            f"[AUDITORIA] [COLETA] [FCMP] Número de itens no processo: {len(itens_processo)}"
        )

        # Calcular detalhes por item - SEMPRE calcular, mesmo se FCMP já estiver no estado
        detalhes_itens = []
        for idx, item in itens_processo.iterrows():
            print(
                f"[AUDITORIA] [COLETA] [FCMP] Calculando FCMP detalhado para item {idx + 1}..."
            )
            detalhes_fc = self._calcular_fc_item_detalhado(item)
            if detalhes_fc:
                print(
                    f"[AUDITORIA] [COLETA] [FCMP] Item {idx + 1}: {len(detalhes_fc.get('fcs_colaboradores', []))} colaborador(es) com FC calculado"
                )
                detalhes_itens.append(detalhes_fc)
            else:
                print(
                    f"[AUDITORIA] [COLETA] [FCMP] Item {idx + 1}: Nenhum detalhe calculado (erro ou sem colaboradores)"
                )

        print(
            f"[AUDITORIA] [COLETA] [FCMP] Total de itens com detalhes: {len(detalhes_itens)}"
        )

        return {"fcmp_final": fcmp_dict, "detalhes_itens": detalhes_itens}

    def _calcular_taxa_item(self, item: pd.Series) -> Optional[Dict]:
        """Calcula taxa de comissão para um item (detalhado)."""
        try:
            linha = str(item.get("Negócio", "")).strip()
            grupo = str(item.get("Grupo", "")).strip()
            subgrupo = str(item.get("Subgrupo", "")).strip()
            tipo_merc = str(item.get("Tipo de Mercadoria", "")).strip()
            valor = float(item.get("Valor Realizado", 0))

            # Obter processo do item
            proc_col = self._encontrar_coluna(
                pd.DataFrame([item]), ["Processo", "processo"]
            )
            if not proc_col:
                return None

            processo_id = str(item.get(proc_col, "")).strip()
            if not processo_id:
                return None

            # Obter colaboradores do processo
            from src.recebimento.core.identificador_colaboradores import (
                IdentificadorColaboradores,
            )

            df_comercial = self.calc_comissao.data.get(
                "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
            )
            colaboradores_df = self.calc_comissao.data.get(
                "COLABORADORES", pd.DataFrame()
            )
            atribuicoes_df = self.calc_comissao.data.get("ATRIBUICOES", pd.DataFrame())
            recebe_por_recebimento_ids = getattr(
                self.calc_comissao, "recebe_por_recebimento", set()
            )

            identificador = IdentificadorColaboradores(
                df_analise_comercial=df_comercial,
                colaboradores_df=colaboradores_df,
                atribuicoes_df=atribuicoes_df,
                recebe_por_recebimento_ids=recebe_por_recebimento_ids,
            )
            colaboradores = identificador.identificar_colaboradores(processo_id)

            taxas_colaboradores = []
            for colab in colaboradores:
                # Obter regra de comissão
                regra = self.calc_comissao._get_regra_comissao(
                    linha=linha,
                    grupo=grupo,
                    subgrupo=subgrupo,
                    tipo_mercadoria=tipo_merc,
                    cargo=colab["cargo"],
                )

                taxa_rateio = (
                    float(regra.get("taxa_rateio_maximo_pct", 0.0) or 0.0) / 100.0
                )
                fatia_cargo = float(regra.get("fatia_cargo_pct", 0.0) or 0.0) / 100.0
                taxa = taxa_rateio * fatia_cargo

                taxas_colaboradores.append(
                    {
                        "nome": colab["nome"],
                        "cargo": colab["cargo"],
                        "taxa_rateio_pct": taxa_rateio * 100,
                        "fatia_cargo_pct": fatia_cargo * 100,
                        "taxa_final_pct": taxa * 100,
                    }
                )

            return {
                "linha": linha,
                "grupo": grupo,
                "subgrupo": subgrupo,
                "tipo_mercadoria": tipo_merc,
                "valor": valor,
                "taxas_colaboradores": taxas_colaboradores,
            }
        except Exception as e:
            print(f"[AUDITORIA] [COLETA] Erro ao calcular taxa de item: {e}")
            return None

    def _calcular_fc_item_detalhado(self, item: pd.Series) -> Optional[Dict]:
        """Calcula FC para um item com detalhamento dos componentes."""
        try:
            # Obter processo do item
            proc_col = self._encontrar_coluna(
                pd.DataFrame([item]), ["Processo", "processo"]
            )
            if not proc_col:
                return None

            processo_id = str(item.get(proc_col, "")).strip()
            if not processo_id:
                return None

            # Obter colaboradores do processo
            from src.recebimento.core.identificador_colaboradores import (
                IdentificadorColaboradores,
            )

            df_comercial = self.calc_comissao.data.get(
                "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
            )
            colaboradores_df = self.calc_comissao.data.get(
                "COLABORADORES", pd.DataFrame()
            )
            atribuicoes_df = self.calc_comissao.data.get("ATRIBUICOES", pd.DataFrame())
            recebe_por_recebimento_ids = getattr(
                self.calc_comissao, "recebe_por_recebimento", set()
            )

            identificador = IdentificadorColaboradores(
                df_analise_comercial=df_comercial,
                colaboradores_df=colaboradores_df,
                atribuicoes_df=atribuicoes_df,
                recebe_por_recebimento_ids=recebe_por_recebimento_ids,
            )
            colaboradores = identificador.identificar_colaboradores(processo_id)

            fcs_colaboradores = []
            for colab in colaboradores:
                # Calcular FC
                fc_resultado = self.calc_comissao._calcular_fc_para_item(
                    nome_colab=colab["nome"],
                    cargo_colab=colab["cargo"],
                    item_faturado=item,
                )

                # Normalizar retorno: pode ser tupla (fc_final, detalhes) ou dict com detalhes
                fc_final = 1.0
                detalhes_dict = {}
                try:
                    if isinstance(fc_resultado, tuple) and len(fc_resultado) >= 2:
                        # (fc_final, detalhes)
                        fc_final = float(fc_resultado[0] or 1.0)
                        detalhes_dict = (
                            fc_resultado[1] if isinstance(fc_resultado[1], dict) else {}
                        )
                    elif isinstance(fc_resultado, dict):
                        detalhes_dict = fc_resultado
                        fc_final = float(detalhes_dict.get("fc_final", 1.0) or 1.0)
                    else:
                        fc_final = (
                            float(fc_resultado) if fc_resultado is not None else 1.0
                        )
                except Exception:
                    fc_final = 1.0
                    detalhes_dict = {}

                # Extrair componentes com peso > 0 a partir do dict de detalhes
                componentes = []
                if isinstance(detalhes_dict, dict):
                    pesos_metas = detalhes_dict.get("pesos_metas", None)
                    for componente, dados in detalhes_dict.items():
                        if componente in ("pesos_metas", "fc_final"):
                            continue
                        if isinstance(dados, dict):
                            # Preferir peso por componente; fallback para mapa 'pesos_metas'
                            if isinstance(pesos_metas, dict):
                                peso = pesos_metas.get(componente, dados.get("peso", 0))
                            else:
                                peso = dados.get("peso", 0)
                            if peso > 0:
                                componentes.append(
                                    {
                                        "nome": componente,
                                        "peso": peso,
                                        "realizado": dados.get("realizado", 0),
                                        "meta": dados.get("meta", 0),
                                        "atingimento": dados.get("atingimento", 0),
                                        "comp_fc": dados.get(
                                            "comp_fc", dados.get("componente_fc", 0)
                                        ),
                                    }
                                )

                fcs_colaboradores.append(
                    {
                        "nome": colab["nome"],
                        "cargo": colab["cargo"],
                        "fc_final": fc_final,
                        "componentes": componentes,
                    }
                )

            return {
                "linha": str(item.get("Negócio", "")).strip(),
                "grupo": str(item.get("Grupo", "")).strip(),
                "subgrupo": str(item.get("Subgrupo", "")).strip(),
                "tipo_mercadoria": str(item.get("Tipo de Mercadoria", "")).strip(),
                "valor": float(item.get("Valor Realizado", 0)),
                "fcs_colaboradores": fcs_colaboradores,
            }
        except Exception as e:
            print(f"[AUDITORIA] [COLETA] Erro ao calcular FC de item: {e}")
            return None

    def _coletar_comissoes(
        self, dados_estado: Dict, tcmp_dict: Dict, fcmp_dict: Dict, mes: int, ano: int
    ) -> List[Dict]:
        """Coleta comissões calculadas usando TCMP/FCMP e totais do estado."""
        import json

        processo_id = dados_estado.get("PROCESSO", "N/A")
        print(
            f"[AUDITORIA] [COLETA] [COMISSOES] Coletando comissões para processo {processo_id}..."
        )

        comissoes = []

        # Obter totais do estado
        total_adiant = float(dados_estado.get("TOTAL_ANTECIPACOES", 0) or 0)
        total_reg = float(dados_estado.get("TOTAL_PAGAMENTOS_REGULARES", 0) or 0)
        total_comissao_adiant = float(
            dados_estado.get("TOTAL_COMISSAO_ANTECIPACOES", 0) or 0
        )
        total_comissao_reg = float(dados_estado.get("TOTAL_COMISSAO_REGULARES", 0) or 0)

        print(
            f"[AUDITORIA] [COLETA] [COMISSOES] Total Adiantamentos: R$ {total_adiant:.2f}, Comissão: R$ {total_comissao_adiant:.2f}"
        )
        print(
            f"[AUDITORIA] [COLETA] [COMISSOES] Total Regulares: R$ {total_reg:.2f}, Comissão: R$ {total_comissao_reg:.2f}"
        )
        print(
            f"[AUDITORIA] [COLETA] [COMISSOES] TCMP disponível: {bool(tcmp_dict)}, FCMP disponível: {bool(fcmp_dict)}"
        )

        # Comissões de adiantamentos (usar TCMP * 1.0, sem FCMP)
        # IMPORTANTE: Mostrar adiantamentos MESMO SEM TCMP (para processos PENDENTES)
        if total_adiant > 0:
            if tcmp_dict and any(tcmp > 0 for tcmp in tcmp_dict.values()):
                # Tem TCMP calculado, usar normalmente
                print(
                    f"[AUDITORIA] [COLETA] [COMISSOES] Processando adiantamentos com TCMP calculado..."
                )
                for colaborador, tcmp in tcmp_dict.items():
                    if tcmp > 0:
                        # Calcular comissão proporcional ao TCMP
                        total_tcmp = sum(tcmp_dict.values())
                        proporcao = tcmp / total_tcmp if total_tcmp > 0 else 1.0
                        comissao = total_comissao_adiant * proporcao

                        print(
                            f"[AUDITORIA] [COLETA] [COMISSOES]   - {colaborador}: TCMP={tcmp:.4f}, Comissão=R$ {comissao:.2f}"
                        )

                        comissoes.append(
                            {
                                "tipo": "Adiantamento",
                                "colaborador": colaborador,
                                "cargo": self._obter_cargo_colaborador(colaborador),
                                "tcmp": tcmp,
                                "fcmp": 1.0,  # Adiantamentos não usam FCMP
                                "valor_pago": total_adiant * proporcao,
                                "comissao": comissao,
                                "mes_calculo": f"{mes:02d}/{ano}",
                            }
                        )
            else:
                # SEM TCMP: usar total de comissão diretamente (já foi calculado no estado)
                # Isso acontece para processos PENDENTES que recebem adiantamento
                print(
                    f"[AUDITORIA] [COLETA] [COMISSOES] Processando adiantamentos SEM TCMP (processo PENDENTE)..."
                )

                if total_comissao_adiant > 0:
                    # Buscar colaboradores envolvidos do estado
                    colaboradores_envolvidos = dados_estado.get(
                        "COLABORADORES_ENVOLVIDOS", ""
                    )
                    print(
                        f"[AUDITORIA] [COLETA] [COMISSOES] Colaboradores do estado: '{colaboradores_envolvidos}'"
                    )

                    # Tentar obter colaboradores do estado ou diretamente da análise comercial
                    nomes_colab = []

                    if (
                        colaboradores_envolvidos
                        and str(colaboradores_envolvidos).strip()
                    ):
                        # Pode ter múltiplos colaboradores separados por vírgula
                        nomes_colab = [
                            c.strip()
                            for c in str(colaboradores_envolvidos).split(",")
                            if c.strip()
                        ]
                        print(
                            f"[AUDITORIA] [COLETA] [COMISSOES] {len(nomes_colab)} colaborador(es) obtido(s) do estado"
                        )

                    # Se não há colaboradores, buscar da análise comercial
                    if not nomes_colab:
                        print(
                            f"[AUDITORIA] [COLETA] [COMISSOES] Buscando colaboradores da análise comercial..."
                        )
                        try:
                            from src.recebimento.core.identificador_colaboradores import (
                                IdentificadorColaboradores,
                            )

                            df_comercial = self.calc_comissao.data.get(
                                "ANALISE_COMERCIAL_COMPLETA", pd.DataFrame()
                            )
                            colaboradores_df = self.calc_comissao.data.get(
                                "COLABORADORES", pd.DataFrame()
                            )
                            atribuicoes_df = self.calc_comissao.data.get(
                                "ATRIBUICOES", pd.DataFrame()
                            )
                            recebe_por_recebimento_ids = getattr(
                                self.calc_comissao, "recebe_por_recebimento", set()
                            )

                            identificador = IdentificadorColaboradores(
                                df_analise_comercial=df_comercial,
                                colaboradores_df=colaboradores_df,
                                atribuicoes_df=atribuicoes_df,
                                recebe_por_recebimento_ids=recebe_por_recebimento_ids,
                            )
                            colaboradores_info = (
                                identificador.identificar_colaboradores(processo_id)
                            )
                            nomes_colab = [c["nome"] for c in colaboradores_info]
                            print(
                                f"[AUDITORIA] [COLETA] [COMISSOES] {len(nomes_colab)} colaborador(es) identificado(s) da análise comercial"
                            )
                        except Exception as e:
                            print(
                                f"[AUDITORIA] [COLETA] [COMISSOES] Erro ao buscar colaboradores: {e}"
                            )

                    if nomes_colab:
                        # Distribuir comissão igualmente entre colaboradores
                        num_colab = len(nomes_colab)
                        comissao_por_colab = total_comissao_adiant / num_colab
                        valor_por_colab = total_adiant / num_colab

                        for colaborador in nomes_colab:
                            print(
                                f"[AUDITORIA] [COLETA] [COMISSOES]   - {colaborador}: Comissão=R$ {comissao_por_colab:.2f} (sem TCMP)"
                            )

                            comissoes.append(
                                {
                                    "tipo": "Adiantamento",
                                    "colaborador": colaborador,
                                    "cargo": self._obter_cargo_colaborador(colaborador),
                                    "tcmp": 0.0,  # Não calculado para PENDENTE
                                    "fcmp": 1.0,
                                    "valor_pago": valor_por_colab,
                                    "comissao": comissao_por_colab,
                                    "mes_calculo": f"{mes:02d}/{ano}",
                                }
                            )
                    else:
                        # Fallback final: criar entrada genérica
                        print(
                            f"[AUDITORIA] [COLETA] [COMISSOES]   - AVISO: Colaboradores não identificados. Comissão=R$ {total_comissao_adiant:.2f}"
                        )
                        comissoes.append(
                            {
                                "tipo": "Adiantamento",
                                "colaborador": "Colaborador(es)",
                                "cargo": "N/A",
                                "tcmp": 0.0,
                                "fcmp": 1.0,
                                "valor_pago": total_adiant,
                                "comissao": total_comissao_adiant,
                                "mes_calculo": f"{mes:02d}/{ano}",
                            }
                        )

        # Comissões regulares (usar TCMP * FCMP)
        if total_reg > 0 and tcmp_dict and fcmp_dict:
            print(
                f"[AUDITORIA] [COLETA] [COMISSOES] Processando pagamentos regulares..."
            )
            for colaborador, tcmp in tcmp_dict.items():
                if tcmp > 0:
                    fcmp = fcmp_dict.get(colaborador, 1.0)
                    if fcmp <= 0:
                        fcmp = 1.0

                    # Calcular comissão proporcional
                    total_tcmp = sum(tcmp_dict.values())
                    proporcao = tcmp / total_tcmp if total_tcmp > 0 else 1.0
                    comissao = total_comissao_reg * proporcao

                    print(
                        f"[AUDITORIA] [COLETA] [COMISSOES]   - {colaborador}: TCMP={tcmp:.4f}, FCMP={fcmp:.4f}, Comissão=R$ {comissao:.2f}"
                    )

                    comissoes.append(
                        {
                            "tipo": "Regular",
                            "colaborador": colaborador,
                            "cargo": self._obter_cargo_colaborador(colaborador),
                            "tcmp": tcmp,
                            "fcmp": fcmp,
                            "valor_pago": total_reg * proporcao,
                            "comissao": comissao,
                            "mes_calculo": f"{mes:02d}/{ano}",
                        }
                    )

        print(
            f"[AUDITORIA] [COLETA] [COMISSOES] Total de comissões coletadas: {len(comissoes)}"
        )
        return comissoes

    def _obter_cargo_colaborador(self, nome: str) -> str:
        """Obtém o cargo de um colaborador."""
        try:
            colaboradores_df = self.calc_comissao.data.get(
                "COLABORADORES", pd.DataFrame()
            )
            if colaboradores_df.empty:
                return "N/A"

            mask = (
                colaboradores_df["nome_colaborador"].astype(str).str.strip()
                == nome.strip()
            )
            row = colaboradores_df[mask]
            if not row.empty:
                return str(row.iloc[0].get("cargo", "N/A"))
        except Exception:
            pass
        return "N/A"

    def _encontrar_coluna(
        self, df: pd.DataFrame, nomes_possiveis: List[str]
    ) -> Optional[str]:
        """
        Encontra uma coluna no DataFrame por nomes possíveis (case-insensitive).
        Remove BOM characters se presentes.
        """
        if df.empty:
            return None

        # Normalizar colunas do DataFrame (remover BOM)
        colunas_normalizadas = {
            col.replace("\ufeff", "").strip().lower(): col for col in df.columns
        }

        for nome in nomes_possiveis:
            nome_norm = nome.strip().lower()
            if nome_norm in colunas_normalizadas:
                return colunas_normalizadas[nome_norm]

        return None
