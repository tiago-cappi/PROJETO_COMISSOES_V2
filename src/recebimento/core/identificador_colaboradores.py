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
        
        # 3. Identificar colaboradores de gestão (via ATRIBUICOES - formato Wide)
        colaboradores_gestao = set()
        
        if not self.atribuicoes_df.empty and not itens.empty:
            # Pegar contexto do primeiro item (todos os itens do mesmo processo têm mesmo contexto)
            primeiro_item = itens.iloc[0]
            
            linha = str(primeiro_item.get("Negócio", "")).strip()
            grupo = str(primeiro_item.get("Grupo", "")).strip()
            subgrupo = str(primeiro_item.get("Subgrupo", "")).strip()
            tipo_mercadoria = str(primeiro_item.get("Tipo de Mercadoria", "")).strip()
            
            # Buscar atribuições de gestão para este contexto (formato Wide)
            mask = (
                (self.atribuicoes_df["linha"].astype(str).str.strip() == linha) &
                (self.atribuicoes_df["grupo"].astype(str).str.strip() == grupo) &
                (self.atribuicoes_df["subgrupo"].astype(str).str.strip() == subgrupo) &
                (self.atribuicoes_df["tipo_mercadoria"].astype(str).str.strip() == tipo_mercadoria)
            )
            
            atribuidos_gestao = self.atribuicoes_df[mask]
            
            # --- FALLBACK: Se linha específica tem gestores vazios, buscar na genérica ---
            gestores_encontrados = []
            if not atribuidos_gestao.empty:
                for _, row in atribuidos_gestao.iterrows():
                    gestores_encontrados = self._extrair_colaboradores_wide(row)
                    if gestores_encontrados:
                        break
            
            # Se não encontrou gestores na linha específica, tentar fallback para genérica
            if not gestores_encontrados:
                # Buscar linha genérica [Todos os ...]
                mask_generic = (
                    (self.atribuicoes_df["linha"].astype(str).str.strip() == linha) &
                    (self.atribuicoes_df["grupo"].astype(str).str.strip().str.contains(r"\[Todos", regex=True, na=False))
                )
                atribuidos_generic = self.atribuicoes_df[mask_generic]
                
                if not atribuidos_generic.empty:
                    for _, row in atribuidos_generic.iterrows():
                        gestores_encontrados = self._extrair_colaboradores_wide(row)
                        if gestores_encontrados:
                            break
            
            # Adicionar gestores encontrados ao set
            for g in gestores_encontrados:
                nome = g.get("colaborador", "")
                if nome:
                    colaboradores_gestao.add(nome)
        
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
    
    def _extrair_colaboradores_wide(self, row_wide: pd.Series) -> List[Dict[str, str]]:
        """
        Extrai colaboradores de uma linha Wide do ATRIBUICOES.
        
        Args:
            row_wide: Uma linha (pd.Series) do DataFrame ATRIBUICOES em formato Wide.
        
        Returns:
            Lista de dicts: [{'colaborador': str, 'cargo': str}, ...]
        """
        resultado = []
        keys = ["linha", "grupo", "subgrupo", "tipo_mercadoria", "_h_key"]
        
        def get_val(col_name):
            if col_name not in row_wide.index:
                return None
            val = row_wide[col_name]
            if pd.isna(val) or val is None:
                return None
            s = str(val).strip()
            if s.lower() in ("nenhum", "nan", "", "none"):
                return None
            return s
        
        # Gerente Linha
        gl1 = get_val("Gerente Linha 1")
        gl2 = get_val("Gerente Linha 2")
        if gl1 is None and gl2 is None:
            gl1 = get_val("Gerente Linha")
        
        if gl1:
            resultado.append({"colaborador": gl1, "cargo": "Gerente Linha"})
        if gl2:
            resultado.append({"colaborador": gl2, "cargo": "Gerente Linha"})
        
        # Coordenador
        c1 = get_val("Coordenador 1")
        c2 = get_val("Coordenador 2")
        if c1 is None and c2 is None:
            c1 = get_val("Coordenador")
        
        if c1:
            resultado.append({"colaborador": c1, "cargo": "Coordenador"})
        if c2:
            resultado.append({"colaborador": c2, "cargo": "Coordenador"})
        
        # Outros Cargos
        special_cols = [
            "Gerente Linha 1", "Gerente Linha 2", "Coordenador 1", "Coordenador 2",
            "Gerente Linha", "Coordenador", "fator_split_gerente", "fator_split_coordenador"
        ] + keys
        
        for col in row_wide.index:
            if col in special_cols or str(col).startswith("_"):
                continue
            if str(col).lower() in ("nan", "none", ""):
                continue
                
            val = get_val(col)
            if val:
                # Suporte a múltiplos nomes separados por ponto e vírgula
                nomes = [n.strip() for n in val.split(";") if n.strip()]
                for nome in nomes:
                    resultado.append({"colaborador": nome, "cargo": col})
        
        return resultado

