"""
Identifica colaboradores envolvidos em um processo que recebem por recebimento.
"""

import pandas as pd
from typing import List, Dict, Set


class IdentificadorColaboradores:
    """
    Identifica todos os colaboradores envolvidos em um processo
    que recebem comissão por recebimento.
    """
    
    def __init__(
        self,
        df_analise_comercial: pd.DataFrame,
        colaboradores_df: pd.DataFrame,
        atribuicoes_df: pd.DataFrame,
        recebe_por_recebimento_ids: Set[str]
    ):
        """
        Inicializa o identificador.
        
        Args:
            df_analise_comercial: DataFrame da Análise Comercial Completa
            colaboradores_df: DataFrame de colaboradores (com cargo)
            atribuicoes_df: DataFrame de atribuições (gestão)
            recebe_por_recebimento_ids: Set com nomes de colaboradores que recebem por recebimento
        """
        self.df_comercial = df_analise_comercial
        self.colaboradores_df = colaboradores_df
        self.atribuicoes_df = atribuicoes_df
        self.recebe_por_recebimento_ids = recebe_por_recebimento_ids
    
    def identificar_colaboradores(self, processo: str) -> List[Dict[str, str]]:
        """
        Identifica todos os colaboradores envolvidos em um processo que recebem por recebimento.
        
        Args:
            processo: ID do processo
        
        Returns:
            Lista de dicts com {'nome': str, 'cargo': str}
        """
        processo = str(processo).strip()
        
        # 1. Buscar todos os itens do processo
        if self.df_comercial.empty:
            return []
        
        # Encontrar coluna de processo
        proc_col = self._encontrar_coluna(["processo", "Processo", "PROCESSO"])
        if not proc_col:
            return []
        
        itens = self.df_comercial[
            self.df_comercial[proc_col].astype(str).str.strip() == processo
        ]
        
        if itens.empty:
            return []
        
        # 2. Identificar colaboradores operacionais (Consultor Interno, Representante-pedido)
        colaboradores_operacionais = set()
        
        col_consultor = self._encontrar_coluna_item(
            itens, ["Consultor Interno", "consultor interno", "CONSULTOR INTERNO"]
        )
        col_representante = self._encontrar_coluna_item(
            itens, ["Representante-pedido", "representante-pedido", "REPRESENTANTE-PEDIDO"]
        )
        
        if col_consultor:
            consultores = itens[col_consultor].dropna().astype(str).str.strip().unique()
            colaboradores_operacionais.update(consultores)
        
        if col_representante:
            representantes = itens[col_representante].dropna().astype(str).str.strip().unique()
            colaboradores_operacionais.update(representantes)
        
        # 3. Identificar colaboradores de gestão (via ATRIBUICOES)
        colaboradores_gestao = set()
        
        if not self.atribuicoes_df.empty and not itens.empty:
            # Pegar contexto do primeiro item (todos os itens do mesmo processo têm mesmo contexto)
            primeiro_item = itens.iloc[0]
            
            linha = str(primeiro_item.get("Negócio", "")).strip()
            grupo = str(primeiro_item.get("Grupo", "")).strip()
            subgrupo = str(primeiro_item.get("Subgrupo", "")).strip()
            tipo_mercadoria = str(primeiro_item.get("Tipo de Mercadoria", "")).strip()
            
            # Buscar atribuições de gestão para este contexto
            mask = (
                (self.atribuicoes_df["linha"] == linha) &
                (self.atribuicoes_df["grupo"] == grupo) &
                (self.atribuicoes_df["subgrupo"] == subgrupo) &
                (self.atribuicoes_df["tipo_mercadoria"] == tipo_mercadoria)
            )
            
            atribuidos_gestao = self.atribuicoes_df[mask]
            
            if not atribuidos_gestao.empty:
                if "colaborador" in atribuidos_gestao.columns:
                    gestores = atribuidos_gestao["colaborador"].dropna().astype(str).str.strip().unique()
                    colaboradores_gestao.update(gestores)
                elif "id_colaborador" in atribuidos_gestao.columns and not self.colaboradores_df.empty:
                    ids = atribuidos_gestao["id_colaborador"].dropna().astype(str).str.strip().unique()
                    # Mapear IDs -> nomes via COLABORADORES
                    mapa = self.colaboradores_df[["id_colaborador", "nome_colaborador"]].copy()
                    mapa["id_colaborador"] = mapa["id_colaborador"].astype(str).str.strip()
                    nomes = (
                        mapa[mapa["id_colaborador"].isin(ids)]["nome_colaborador"]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .unique()
                    )
                    colaboradores_gestao.update(nomes)
        
        # 4. Combinar todos os colaboradores
        todos_colaboradores = colaboradores_operacionais.union(colaboradores_gestao)
        
        # 5. Filtrar apenas os que recebem por recebimento
        colaboradores_filtrados = []
        
        for nome in todos_colaboradores:
            if not nome or nome == "" or nome.lower() == "nan":
                continue
            
            # Verificar se está na lista de recebimento
            nome_normalizado = nome.strip()
            if nome_normalizado in self.recebe_por_recebimento_ids:
                # Obter cargo do colaborador
                cargo = self._obter_cargo(nome_normalizado)
                
                colaboradores_filtrados.append({
                    'nome': nome_normalizado,
                    'cargo': cargo or "N/A"
                })
        
        # Remover duplicatas (mesmo nome e cargo)
        colaboradores_unicos = []
        vistos = set()
        
        for colab in colaboradores_filtrados:
            chave = (colab['nome'].lower(), colab['cargo'].lower())
            if chave not in vistos:
                vistos.add(chave)
                colaboradores_unicos.append(colab)
        
        return colaboradores_unicos
    
    def _obter_cargo(self, nome: str) -> str:
        """
        Obtém o cargo de um colaborador.
        
        Args:
            nome: Nome do colaborador
        
        Returns:
            Nome do cargo ou None
        """
        if self.colaboradores_df.empty or not nome:
            return None
        
        mask = self.colaboradores_df["nome_colaborador"].astype(str).str.strip() == nome.strip()
        row = self.colaboradores_df[mask]
        
        if not row.empty and "cargo" in row.columns:
            return str(row.iloc[0]["cargo"]).strip()
        
        return None
    
    def _encontrar_coluna(self, nomes_possiveis: List[str]) -> str:
        """
        Encontra uma coluna no DataFrame comercial.
        
        Args:
            nomes_possiveis: Lista de nomes possíveis
        
        Returns:
            Nome da coluna encontrada ou None
        """
        if self.df_comercial.empty:
            return None
        
        # Remover BOM (\ufeff) e normalizar
        colunas_df = {
            col.lower().strip().replace("\ufeff", ""): col for col in self.df_comercial.columns
        }
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_df:
                return colunas_df[nome_norm]
        
        return None
    
    def _encontrar_coluna_item(self, df_item: pd.DataFrame, nomes_possiveis: List[str]) -> str:
        """
        Encontra uma coluna no DataFrame de itens.
        
        Args:
            df_item: DataFrame de itens
            nomes_possiveis: Lista de nomes possíveis
        
        Returns:
            Nome da coluna encontrada ou None
        """
        if df_item.empty:
            return None
        
        # Remover BOM (\ufeff) e normalizar
        colunas_df = {str(col).lower().strip().replace("\ufeff", ""): col for col in df_item.columns}
        
        for nome in nomes_possiveis:
            nome_norm = nome.lower().strip()
            if nome_norm in colunas_df:
                return colunas_df[nome_norm]
        
        return None

