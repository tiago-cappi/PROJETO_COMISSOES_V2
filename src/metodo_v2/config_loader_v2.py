"""
src.metodo_v2.config_loader_v2 - Carregador de configurações da Metodologia V2

Nova arquitetura: carrega colaboradores (nome + cargo) e suas regras de comissão
baseadas em combinações hierárquicas com faixas de faturamento.
"""

from __future__ import annotations

import os
import logging
from typing import Dict, List, Optional, Set

import pandas as pd
import numpy as np

from .models_v2 import ColaboradorV2, RegraComissao, FaixaComissao, RegraCentroCusto


logger = logging.getLogger(__name__)


class ConfigLoaderV2:
    """Carregador de configurações para a Metodologia V2.
    
    Lê o arquivo REGRAS_COMISSOES_V2.xlsx e transforma em objetos tipados.
    
    Estrutura esperada do Excel:
    
    Aba COLABORADORES_V2:
        - colaborador: str (nome, PK)
        - cargo: str (FK para CARGOS_V2)
    
    Aba REGRAS_COMISSAO_V2:
        - colaborador: str (FK)
        - regra_id: int
        - linha: str (opcional, wildcard se vazio)
        - grupo: str (opcional)
        - subgrupo: str (opcional)
        - tipo_mercadoria: str (opcional)
        - fabricante: str (opcional)
        - faixa_1_limite: float (sempre 0)
        - faixa_1_taxa: float
        - faixa_2_limite: float (opcional)
        - faixa_2_taxa: float (opcional)
        - ... até faixa_5
    """

    DEFAULT_CONFIG_PATH = "config/REGRAS_COMISSOES_V2.xlsx"
    MAX_FAIXAS = 5

    def __init__(self, config_path: Optional[str] = None):
        """Inicializa o loader.
        
        Args:
            config_path: Caminho para o arquivo de configuração.
                        Se None, usa DEFAULT_CONFIG_PATH.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._raw_data: Dict[str, pd.DataFrame] = {}
        self._colaboradores: Dict[str, ColaboradorV2] = {}
        self._cargos: List[str] = []

    def load(self) -> Dict[str, ColaboradorV2]:
        """Carrega e processa todas as configurações.
        
        Returns:
            Dict mapeando nome_colaborador -> ColaboradorV2
            
        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se houver erro de validação nos dados.
        """
        self._load_excel()
        self._load_cargos()
        self._parse_colaboradores()
        self._parse_regras()
        self._parse_regras_cc()  # NOVO: Carregar regras de Centro de Custo
        self._validate()
        return self._colaboradores

    def _load_excel(self) -> None:
        """Carrega o arquivo Excel."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Arquivo de configuração V2 não encontrado: {self.config_path}"
            )

        try:
            self._raw_data = pd.read_excel(self.config_path, sheet_name=None)
            logger.info(f"Carregado {self.config_path} com abas: {list(self._raw_data.keys())}")
        except Exception as e:
            raise ValueError(f"Erro ao carregar {self.config_path}: {e}")

        # Normalizar nomes das colunas (strip)
        for sheet_name, df in self._raw_data.items():
            df.columns = df.columns.astype(str).str.strip()
            self._raw_data[sheet_name] = df

    def _load_cargos(self) -> None:
        """Carrega lista de cargos válidos de CARGOS_V2."""
        sheet_name = "CARGOS_V2"
        
        if sheet_name not in self._raw_data:
            logger.warning(f"Aba '{sheet_name}' não encontrada. Cargos não serão validados.")
            return

        df = self._raw_data[sheet_name]
        
        # Coluna de cargo pode ser 'cargo' ou 'nome_cargo'
        cargo_col = None
        for col in ["cargo", "nome_cargo"]:
            if col in df.columns:
                cargo_col = col
                break
        
        if not cargo_col:
            logger.warning(f"Coluna 'cargo' ou 'nome_cargo' não encontrada em {sheet_name}")
            return

        self._cargos = [
            self._clean_string(c) for c in df[cargo_col].dropna().unique()
            if self._clean_string(c)
        ]
        logger.info(f"Carregados {len(self._cargos)} cargos válidos")

    def _parse_colaboradores(self) -> None:
        """Processa a aba COLABORADORES_V2.
        
        Raises:
            ValueError: Se houver nomes duplicados na aba COLABORADORES_V2.
        """
        sheet_name = "COLABORADORES_V2"
        
        if sheet_name not in self._raw_data:
            logger.warning(f"Aba '{sheet_name}' não encontrada. Tentando criar lista vazia.")
            return

        df = self._raw_data[sheet_name]
        
        # Verificar colunas (suporta 'colaborador' ou 'nome_colaborador')
        nome_col = None
        for col in ["nome_colaborador", "colaborador"]:
            if col in df.columns:
                nome_col = col
                break
        
        if nome_col is None:
            logger.warning(f"Coluna 'colaborador' ou 'nome_colaborador' não encontrada em {sheet_name}")
            return

        # --- Detecção de nomes duplicados (DEVE interromper o cálculo) ---
        nomes_raw = [
            self._clean_string(v) for v in df[nome_col].dropna()
            if self._clean_string(v)
        ]
        nomes_vistos: dict[str, int] = {}
        duplicatas: list[str] = []
        for n in nomes_raw:
            nomes_vistos[n] = nomes_vistos.get(n, 0) + 1
        for n, count in nomes_vistos.items():
            if count > 1:
                duplicatas.append(f"'{n}' ({count}x)")
        
        if duplicatas:
            msg = (
                f"[ERRO CRÍTICO] Nomes duplicados encontrados em {sheet_name}: "
                f"{', '.join(duplicatas)}. "
                f"O nome do colaborador é usado como ID único — cada nome deve "
                f"aparecer exatamente uma vez. Corrija a planilha e re-execute."
            )
            logger.error(msg)
            raise ValueError(msg)
        # --- Fim da detecção de duplicatas ---

        for _, row in df.iterrows():
            nome = self._clean_string(row.get(nome_col))
            if not nome:
                continue

            cargo = self._clean_string(row.get("cargo", ""))
            
            # Validar cargo
            if self._cargos and cargo and cargo not in self._cargos:
                logger.warning(f"Cargo '{cargo}' do colaborador '{nome}' não está em CARGOS_V2")
            
            # Ler tipo_comissao (nova coluna - default: "faturamento")
            tipo_comissao = self._clean_string(row.get("tipo_comissao", "faturamento"))
            if not tipo_comissao:
                tipo_comissao = "faturamento"
            tipo_comissao = tipo_comissao.lower()
            
            # Ler taxa_adiantamento_pct (nova coluna - obrigatória se tipo_comissao = "recebimento")
            taxa_adiantamento_pct = None
            taxa_raw = row.get("taxa_adiantamento_pct")
            if pd.notna(taxa_raw) and taxa_raw != "":
                try:
                    taxa_adiantamento_pct = float(taxa_raw)
                except (ValueError, TypeError):
                    logger.warning(
                        f"taxa_adiantamento_pct inválida para '{nome}': {taxa_raw}. Ignorando."
                    )
            
            # Validar: se tipo_comissao = "recebimento", taxa_adiantamento_pct é obrigatória
            if tipo_comissao == "recebimento" and taxa_adiantamento_pct is None:
                logger.error(
                    f"Colaborador '{nome}' com tipo_comissao='recebimento' "
                    f"DEVE ter taxa_adiantamento_pct definida. Pulando colaborador."
                )
                continue

            self._colaboradores[nome] = ColaboradorV2(
                nome=nome,
                cargo=cargo,
                regras=[],
                tipo_comissao=tipo_comissao,
                taxa_adiantamento_pct=taxa_adiantamento_pct,
            )
        
        # Log de resumo por tipo
        count_fat = sum(1 for c in self._colaboradores.values() if c.tipo_comissao == "faturamento")
        count_rec = sum(1 for c in self._colaboradores.values() if c.tipo_comissao == "recebimento")
        logger.info(
            f"Carregados {len(self._colaboradores)} colaboradores "
            f"({count_fat} faturamento, {count_rec} recebimento)"
        )

    def _parse_regras(self) -> None:
        """Processa a aba REGRAS_COMISSAO_V2 e associa aos colaboradores."""
        sheet_name = "REGRAS_COMISSAO_V2"
        
        if sheet_name not in self._raw_data:
            logger.warning(f"Aba '{sheet_name}' não encontrada. Nenhuma regra será carregada.")
            return

        df = self._raw_data[sheet_name]
        
        # Verificar colunas obrigatórias (suporta formato novo ou antigo)
        # Novo: faixa_1_de, faixa_1_ate, faixa_1_taxa
        # Antigo: faixa_1_limite, faixa_1_taxa
        has_new_format = "faixa_1_de" in df.columns
        has_old_format = "faixa_1_limite" in df.columns
        
        if not has_new_format and not has_old_format:
            logger.warning(f"Colunas de faixas não encontradas em {sheet_name}")
            return
        
        required_cols = {"colaborador", "regra_id"}
        missing = required_cols - set(df.columns)
        if missing:
            logger.warning(f"Colunas obrigatórias ausentes em {sheet_name}: {missing}")
            return

        regras_count = 0
        for _, row in df.iterrows():
            nome = self._clean_string(row.get("colaborador"))
            if not nome:
                continue

            # Criar colaborador se não existir
            if nome not in self._colaboradores:
                logger.info(f"Colaborador '{nome}' criado a partir de REGRAS_COMISSAO_V2")
                self._colaboradores[nome] = ColaboradorV2(nome=nome, cargo="", regras=[])

            # Parse regra_id
            try:
                regra_id = int(row.get("regra_id", 1) or 1)
            except (ValueError, TypeError):
                regra_id = self._colaboradores[nome].get_proxima_regra_id()

            # Parse filtros hierárquicos (None se vazio = wildcard)
            linha = self._clean_string_or_none(row.get("linha"))
            grupo = self._clean_string_or_none(row.get("grupo"))
            subgrupo = self._clean_string_or_none(row.get("subgrupo"))
            tipo_mercadoria = self._clean_string_or_none(row.get("tipo_mercadoria"))
            fabricante = self._clean_string_or_none(row.get("fabricante"))

            # Parse faixas de comissão
            faixas = self._parse_faixas(row)

            if not faixas:
                logger.warning(f"Regra {regra_id} do colaborador '{nome}' não possui faixas válidas")
                continue

            regra = RegraComissao(
                colaborador=nome,
                regra_id=regra_id,
                linha=linha,
                grupo=grupo,
                subgrupo=subgrupo,
                tipo_mercadoria=tipo_mercadoria,
                fabricante=fabricante,
                faixas=faixas,
            )

            self._colaboradores[nome].adicionar_regra(regra)
            regras_count += 1

        logger.info(f"Carregadas {regras_count} regras de comissão")

    def _parse_faixas(self, row: pd.Series) -> List[FaixaComissao]:
        """Extrai as faixas de comissão de uma linha do Excel.
        
        Suporta dois formatos:
        - Novo: faixa_X_de, faixa_X_ate, faixa_X_taxa
        - Antigo: faixa_X_limite, faixa_X_taxa (limite inferior implícito)
        
        No formato antigo, o limite superior de uma faixa é o limite inferior da próxima.
        A última faixa tem limite superior infinito (None).
        
        Caso especial: limite=-1 indica "infinito" - usado quando queremos taxa fixa
        ou quando queremos indicar que uma faixa vai até infinito.
        """
        # Primeiro passo: coletar todas as faixas brutas
        faixas_brutas = []
        
        for i in range(1, self.MAX_FAIXAS + 1):
            # Tentar formato novo primeiro, depois antigo
            if f"faixa_{i}_de" in row.index:
                limite_col = f"faixa_{i}_de"
                ate_col = f"faixa_{i}_ate"
            else:
                limite_col = f"faixa_{i}_limite"
                ate_col = None
            taxa_col = f"faixa_{i}_taxa"
            
            limite_val = row.get(limite_col)
            taxa_val = row.get(taxa_col)
            ate_val = row.get(ate_col) if ate_col else None
            
            # Parar se não houver mais faixas
            if pd.isna(limite_val) and pd.isna(taxa_val):
                break
            
            # Converter valores
            try:
                limite = float(limite_val) if not pd.isna(limite_val) else 0.0
            except (ValueError, TypeError):
                limite = 0.0
            
            try:
                taxa = float(taxa_val) if not pd.isna(taxa_val) else 0.0
            except (ValueError, TypeError):
                taxa = 0.0
            
            # Converter limite_superior explícito (formato novo)
            limite_superior_explicito = None
            if ate_val is not None and not pd.isna(ate_val):
                try:
                    limite_superior_explicito = float(ate_val)
                except (ValueError, TypeError):
                    limite_superior_explicito = None
            
            faixas_brutas.append({
                "limite": limite,
                "taxa": taxa,
                "limite_superior_explicito": limite_superior_explicito,
            })
        
        # Segundo passo: processar faixas e inferir limites superiores
        faixas = []
        
        for i, fb in enumerate(faixas_brutas):
            limite = fb["limite"]
            taxa = fb["taxa"]
            limite_sup_explicito = fb["limite_superior_explicito"]
            
            # Caso especial: limite -1 significa infinito
            # Esta é uma "pseudo-faixa" que indica que a faixa anterior vai até infinito
            if limite == -1:
                logger.debug(f"Limite -1 detectado (infinito) para faixa {i+1}")
                # Atualizar a última faixa para ter limite_superior infinito
                # e usar a taxa desta faixa se especificada
                if faixas and taxa > 0:
                    ultima = faixas[-1]
                    faixas[-1] = FaixaComissao(
                        limite_inferior=ultima.limite_inferior,
                        limite_superior=None,  # Infinito
                        operador_superior=None,
                        taxa_comissao_pct=taxa
                    )
                continue
            
            # Validar limite
            if limite < 0:
                logger.warning(f"Limite negativo ignorado: {limite}")
                continue
            if taxa < 0:
                logger.warning(f"Taxa negativa ignorada: {taxa}")
                continue
            
            # Determinar limite superior
            if limite_sup_explicito is not None:
                # Formato novo com limite superior explícito
                limite_superior = limite_sup_explicito if limite_sup_explicito >= 0 else None
                operador_superior = '<' if limite_superior is not None else None
            else:
                # Formato antigo: limite superior é o limite inferior da próxima faixa
                # ou infinito se for a última
                proxima_faixa = faixas_brutas[i + 1] if i + 1 < len(faixas_brutas) else None
                if proxima_faixa and proxima_faixa["limite"] >= 0:
                    limite_superior = proxima_faixa["limite"]
                    operador_superior = '<'
                else:
                    limite_superior = None  # Infinito
                    operador_superior = None
            
            faixas.append(FaixaComissao(
                limite_inferior=limite, 
                limite_superior=limite_superior,
                operador_superior=operador_superior,
                taxa_comissao_pct=taxa
            ))
        
        # Ordenar por limite
        return sorted(faixas, key=lambda f: f.limite_inferior)

    def _parse_regras_cc(self) -> None:
        """Processa a aba REGRAS_COMISSAO_CC_V2 para regras por Centro de Custo + Fabricante."""
        sheet_name = "REGRAS_COMISSAO_CC_V2"
        
        if sheet_name not in self._raw_data:
            logger.info(f"Aba '{sheet_name}' não encontrada. Modo Centro de Custo não terá regras.")
            return

        df = self._raw_data[sheet_name]
        
        # Verificar colunas obrigatórias
        required_cols = {"colaborador", "centro_custo"}
        missing = required_cols - set(df.columns)
        if missing:
            logger.warning(f"Colunas obrigatórias ausentes em {sheet_name}: {missing}")
            return
        
        # Verificar se tem colunas de faixas
        has_faixas = "faixa_1_limite" in df.columns or "faixa_1_taxa" in df.columns
        if not has_faixas:
            logger.warning(f"Colunas de faixas não encontradas em {sheet_name}")
            return
        
        # Verificar se coluna fabricante existe (opcional)
        has_fabricante = "fabricante" in df.columns

        regras_cc_count = 0
        regras_cc_com_fab = 0
        for _, row in df.iterrows():
            nome = self._clean_string(row.get("colaborador"))
            centro_custo = self._clean_string(row.get("centro_custo"))
            
            if not nome or not centro_custo:
                continue
            
            # Fabricante é opcional (None = todos fabricantes do CC)
            fabricante = None
            if has_fabricante:
                fab_raw = row.get("fabricante")
                if pd.notna(fab_raw):
                    fabricante = self._clean_string(fab_raw)
                    if fabricante:
                        regras_cc_com_fab += 1

            # Split é opcional (None = 100% se único do cargo na regra)
            split = None
            if "split" in df.columns:
                split_raw = row.get("split")
                if pd.notna(split_raw):
                    try:
                        split = float(split_raw)
                    except (ValueError, TypeError):
                        logger.warning(f"Valor de split inválido para '{nome}' em CC '{centro_custo}': {split_raw}")
                        split = None

            # Criar colaborador se não existir
            if nome not in self._colaboradores:
                logger.info(f"Colaborador '{nome}' criado a partir de {sheet_name}")
                self._colaboradores[nome] = ColaboradorV2(nome=nome, cargo="", regras=[], regras_cc=[])

            # Parse faixas de comissão (reutiliza mesmo formato)
            faixas = self._parse_faixas(row)

            if not faixas:
                logger.warning(f"Regra CC '{centro_custo}' do colaborador '{nome}' não possui faixas válidas")
                continue

            regra_cc = RegraCentroCusto(
                colaborador=nome,
                centro_custo=centro_custo,
                fabricante=fabricante,
                split=split,
                faixas=faixas,
            )

            self._colaboradores[nome].adicionar_regra_cc(regra_cc)
            regras_cc_count += 1

        logger.info(
            f"Carregadas {regras_cc_count} regras de Centro de Custo "
            f"({regras_cc_com_fab} com fabricante específico)"
        )

    def _validate(self) -> None:
        """Valida a consistência das configurações."""
        errors = []

        for nome, colab in self._colaboradores.items():
            if not colab.regras:
                errors.append(f"Colaborador '{nome}' não possui regras de comissão configuradas")
            
            if not colab.cargo:
                errors.append(f"Colaborador '{nome}' não possui cargo definido")

            # Validar regras duplicadas (mesmo regra_id)
            regra_ids = [r.regra_id for r in colab.regras]
            if len(regra_ids) != len(set(regra_ids)):
                errors.append(f"Colaborador '{nome}' possui regras com IDs duplicados")

        if errors:
            for err in errors:
                logger.warning(f"Validação V2: {err}")
            # Não levanta exceção, apenas warnings (fail-safe)

    @staticmethod
    def _clean_string(value) -> str:
        """Limpa e normaliza uma string."""
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def _clean_string_or_none(value) -> Optional[str]:
        """Limpa string, retorna None se vazio (wildcard)."""
        if value is None or pd.isna(value):
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def get_colaborador(self, nome: str) -> Optional[ColaboradorV2]:
        """Busca um colaborador pelo nome."""
        return self._colaboradores.get(nome)

    def get_all_colaboradores(self) -> List[ColaboradorV2]:
        """Retorna todos os colaboradores."""
        return list(self._colaboradores.values())

    def get_cargos(self) -> List[str]:
        """Retorna lista de cargos válidos."""
        return self._cargos.copy()

    def exists(self) -> bool:
        """Verifica se o arquivo de configuração existe."""
        return os.path.exists(self.config_path)
