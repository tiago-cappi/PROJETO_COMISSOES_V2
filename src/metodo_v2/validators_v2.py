"""
src.metodo_v2.validators_v2 - Validadores para Metodologia V2

Validação de regras de negócio e consistência de dados para o cálculo de comissões V2.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, TYPE_CHECKING

import pandas as pd
import numpy as np

# Type checking import para evitar circular import
if TYPE_CHECKING:
    from .models_v2 import ColaboradorV2


logger = logging.getLogger(__name__)


# =============================================================================
# DATACLASSES DE RESULTADO
# =============================================================================
@dataclass
class ErroValidacao:
    """Representa um erro de validação."""
    
    tipo: str  # "ERRO", "AVISO"
    codigo: str  # Código único do erro
    mensagem: str
    contexto: Dict = field(default_factory=dict)  # Dados adicionais
    
    def __str__(self) -> str:
        return f"[{self.tipo}] {self.codigo}: {self.mensagem}"


@dataclass
class ResultadoValidacao:
    """Resultado consolidado de validações."""
    
    erros: List[ErroValidacao] = field(default_factory=list)
    
    @property
    def valido(self) -> bool:
        return not any(e.tipo == "ERRO" for e in self.erros)
    
    @property
    def tem_avisos(self) -> bool:
        return any(e.tipo == "AVISO" for e in self.erros)
    
    def adicionar_erro(
        self, 
        codigo: str, 
        mensagem: str, 
        contexto: Optional[Dict] = None
    ) -> None:
        self.erros.append(ErroValidacao(
            tipo="ERRO",
            codigo=codigo,
            mensagem=mensagem,
            contexto=contexto or {}
        ))
    
    def adicionar_aviso(
        self, 
        codigo: str, 
        mensagem: str, 
        contexto: Optional[Dict] = None
    ) -> None:
        self.erros.append(ErroValidacao(
            tipo="AVISO",
            codigo=codigo,
            mensagem=mensagem,
            contexto=contexto or {}
        ))
    
    def merge(self, outro: "ResultadoValidacao") -> None:
        """Combina resultados de validação."""
        self.erros.extend(outro.erros)
    
    def resumo(self) -> str:
        """Retorna resumo textual."""
        n_erros = sum(1 for e in self.erros if e.tipo == "ERRO")
        n_avisos = sum(1 for e in self.erros if e.tipo == "AVISO")
        status = "VÁLIDO" if self.valido else "INVÁLIDO"
        return f"{status}: {n_erros} erro(s), {n_avisos} aviso(s)"


# =============================================================================
# VALIDADORES DE CONFIGURAÇÃO
# =============================================================================
class ValidadorConfigV2:
    """Valida a configuração do arquivo REGRAS_COMISSOES_V2.xlsx."""
    
    ABAS_OBRIGATORIAS = [
        "COLABORADORES_V2",
        "REGRAS_COMISSAO_V2", 
        "CARGOS_V2"
    ]
    
    COLUNAS_COLABORADORES = ["colaborador", "cargo"]
    
    COLUNAS_REGRAS = [
        "colaborador", "regra_id",
        "linha", "grupo", "subgrupo", "tipo_mercadoria", "fabricante",
        "faixa_1_de", "faixa_1_ate", "faixa_1_taxa"
    ]
    
    COLUNAS_CARGOS = [
        "nome_cargo", "tipo"
    ]
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._data: Dict[str, pd.DataFrame] = {}
    
    def validar(self) -> ResultadoValidacao:
        """Executa todas as validações de configuração."""
        resultado = ResultadoValidacao()
        
        # Carregar arquivo
        try:
            self._data = pd.read_excel(self.config_path, sheet_name=None)
        except FileNotFoundError:
            resultado.adicionar_erro(
                "CONFIG_NOT_FOUND",
                f"Arquivo de configuração não encontrado: {self.config_path}"
            )
            return resultado
        except Exception as e:
            resultado.adicionar_erro(
                "CONFIG_LOAD_ERROR",
                f"Erro ao carregar configuração: {e}"
            )
            return resultado
        
        # Validar abas obrigatórias
        resultado.merge(self._validar_abas_obrigatorias())
        
        # Validar estrutura de cada aba
        if "COLABORADORES_V2" in self._data:
            resultado.merge(self._validar_colaboradores())
        
        if "REGRAS_COMISSAO_V2" in self._data:
            resultado.merge(self._validar_regras())
        
        if "CARGOS_V2" in self._data:
            resultado.merge(self._validar_cargos())
        
        # Validar consistência cruzada
        resultado.merge(self._validar_consistencia_cruzada())
        
        return resultado
    
    def _validar_abas_obrigatorias(self) -> ResultadoValidacao:
        """Verifica se todas as abas obrigatórias existem."""
        resultado = ResultadoValidacao()
        
        for aba in self.ABAS_OBRIGATORIAS:
            if aba not in self._data:
                resultado.adicionar_erro(
                    "ABA_AUSENTE",
                    f"Aba obrigatória '{aba}' não encontrada no arquivo de configuração"
                )
        
        return resultado
    
    def _validar_colaboradores(self) -> ResultadoValidacao:
        """Valida a aba COLABORADORES_V2."""
        resultado = ResultadoValidacao()
        df = self._data.get("COLABORADORES_V2", pd.DataFrame())
        
        # Verificar colunas (aceita 'colaborador' ou 'nome_colaborador')
        has_nome = "colaborador" in df.columns or "nome_colaborador" in df.columns
        if not has_nome:
            resultado.adicionar_erro(
                "COL_AUSENTE",
                "Coluna 'colaborador' ou 'nome_colaborador' ausente em COLABORADORES_V2"
            )
        
        if "cargo" not in df.columns:
            resultado.adicionar_aviso(
                "COL_AUSENTE",
                "Coluna 'cargo' ausente em COLABORADORES_V2"
            )
        
        # Verificar duplicatas de nome
        nome_col = "colaborador" if "colaborador" in df.columns else "nome_colaborador"
        if nome_col in df.columns:
            duplicados = df[nome_col].dropna()
            duplicados = duplicados[duplicados.duplicated()]
            if len(duplicados) > 0:
                resultado.adicionar_erro(
                    "COLABORADOR_DUPLICADO",
                    f"Colaboradores duplicados em COLABORADORES_V2: {list(duplicados.unique())}"
                )
        
        return resultado
    
    def _validar_regras(self) -> ResultadoValidacao:
        """Valida a aba REGRAS_COMISSAO_V2."""
        resultado = ResultadoValidacao()
        df = self._data.get("REGRAS_COMISSAO_V2", pd.DataFrame())
        
        # Verificar coluna de colaborador
        if "colaborador" not in df.columns:
            resultado.adicionar_erro(
                "COL_AUSENTE",
                "Coluna 'colaborador' ausente em REGRAS_COMISSAO_V2"
            )
            return resultado
        
        # Verificar se há pelo menos uma coluna de faixa
        faixa_cols = [c for c in df.columns if c.startswith("faixa_")]
        if not faixa_cols:
            resultado.adicionar_erro(
                "FAIXAS_AUSENTES",
                "Nenhuma coluna de faixa encontrada em REGRAS_COMISSAO_V2"
            )
        
        # Validar cada linha de regra
        for idx, row in df.iterrows():
            colaborador = row.get("colaborador", "")
            if pd.isna(colaborador) or str(colaborador).strip() == "":
                continue
            
            # Validar faixas
            resultado.merge(self._validar_faixas_linha(row, idx))
        
        return resultado
    
    def _validar_faixas_linha(self, row: pd.Series, idx: int) -> ResultadoValidacao:
        """Valida as faixas de uma linha de regra."""
        resultado = ResultadoValidacao()
        colaborador = str(row.get("colaborador", ""))
        
        # Coletar faixas
        faixas = []
        for i in range(1, 6):  # Até 5 faixas
            # Tentar formato novo (de/ate/taxa)
            de_col = f"faixa_{i}_de"
            ate_col = f"faixa_{i}_ate"
            taxa_col = f"faixa_{i}_taxa"
            
            # Tentar formato antigo (limite/taxa)
            limite_col = f"faixa_{i}_limite"
            
            de_val = row.get(de_col) if de_col in row.index else row.get(limite_col)
            ate_val = row.get(ate_col) if ate_col in row.index else None
            taxa_val = row.get(taxa_col)
            
            if pd.notna(de_val) or pd.notna(taxa_val):
                faixas.append({
                    "idx": i,
                    "de": de_val,
                    "ate": ate_val,
                    "taxa": taxa_val
                })
        
        if not faixas:
            resultado.adicionar_aviso(
                "SEM_FAIXAS",
                f"Linha {idx}: Colaborador '{colaborador}' não possui faixas definidas"
            )
            return resultado
        
        # Validar gaps entre faixas
        for i, faixa in enumerate(faixas):
            if faixa["de"] is not None and not pd.isna(faixa["de"]) and float(faixa["de"]) < 0:
                resultado.adicionar_erro(
                    "FAIXA_NEGATIVA",
                    f"Linha {idx}: Faixa {faixa['idx']} tem limite inferior negativo",
                    {"colaborador": colaborador, "faixa": faixa}
                )
            
            if faixa["taxa"] is not None and not pd.isna(faixa["taxa"]) and float(faixa["taxa"]) < 0:
                resultado.adicionar_erro(
                    "TAXA_NEGATIVA",
                    f"Linha {idx}: Faixa {faixa['idx']} tem taxa negativa",
                    {"colaborador": colaborador, "faixa": faixa}
                )
            
            # Verificar continuidade (se faixa anterior tem 'ate', próxima deve ter 'de' igual)
            if i > 0 and faixas[i-1].get("ate") is not None:
                ate_anterior = faixas[i-1]["ate"]
                de_atual = faixa["de"]
                if pd.notna(ate_anterior) and pd.notna(de_atual):
                    if float(de_atual) != float(ate_anterior):
                        resultado.adicionar_aviso(
                            "GAP_FAIXAS",
                            f"Linha {idx}: Gap entre faixa {faixas[i-1]['idx']} (até {ate_anterior}) "
                            f"e faixa {faixa['idx']} (de {de_atual})",
                            {"colaborador": colaborador}
                        )
        
        return resultado
    
    def _validar_cargos(self) -> ResultadoValidacao:
        """Valida a aba CARGOS_V2."""
        resultado = ResultadoValidacao()
        df = self._data.get("CARGOS_V2", pd.DataFrame())
        
        # Verificar coluna de nome
        if "nome_cargo" not in df.columns:
            resultado.adicionar_erro(
                "COL_AUSENTE",
                "Coluna 'nome_cargo' ausente em CARGOS_V2"
            )
        
        # Verificar coluna de tipo
        if "tipo" not in df.columns:
            resultado.adicionar_aviso(
                "COL_AUSENTE",
                "Coluna 'tipo' ausente em CARGOS_V2 - será inferido automaticamente"
            )
        else:
            # Validar valores de tipo
            tipos_validos = {"OPERACIONAL", "GESTAO"}
            for idx, row in df.iterrows():
                tipo = str(row.get("tipo", "") or "").strip().upper()
                if tipo and tipo not in tipos_validos:
                    resultado.adicionar_erro(
                        "TIPO_CARGO_INVALIDO",
                        f"Linha {idx}: Tipo '{tipo}' inválido. Valores válidos: {tipos_validos}"
                    )
        
        return resultado
    
    def _validar_consistencia_cruzada(self) -> ResultadoValidacao:
        """Valida consistência entre abas."""
        resultado = ResultadoValidacao()
        
        df_colabs = self._data.get("COLABORADORES_V2", pd.DataFrame())
        df_regras = self._data.get("REGRAS_COMISSAO_V2", pd.DataFrame())
        df_cargos = self._data.get("CARGOS_V2", pd.DataFrame())
        
        # Extrair nomes de colaboradores cadastrados
        nome_col = "colaborador" if "colaborador" in df_colabs.columns else "nome_colaborador"
        if nome_col in df_colabs.columns:
            colaboradores_cadastrados = set(
                str(n).strip().lower() 
                for n in df_colabs[nome_col].dropna() 
                if str(n).strip()
            )
        else:
            colaboradores_cadastrados = set()
        
        # Verificar se colaboradores em REGRAS_COMISSAO_V2 estão cadastrados
        if "colaborador" in df_regras.columns and colaboradores_cadastrados:
            for nome in df_regras["colaborador"].dropna().unique():
                nome_lower = str(nome).strip().lower()
                if nome_lower and nome_lower not in colaboradores_cadastrados:
                    resultado.adicionar_aviso(
                        "COLAB_NAO_CADASTRADO",
                        f"Colaborador '{nome}' em REGRAS_COMISSAO_V2 não está em COLABORADORES_V2"
                    )
        
        # Verificar se cargos dos colaboradores estão cadastrados em CARGOS_V2
        if "cargo" in df_colabs.columns:
            cargos_cadastrados = set()
            cargo_col = "nome_cargo" if "nome_cargo" in df_cargos.columns else "cargo"
            if cargo_col in df_cargos.columns:
                cargos_cadastrados = set(
                    str(c).strip().lower() 
                    for c in df_cargos[cargo_col].dropna() 
                    if str(c).strip()
                )
            
            for cargo in df_colabs["cargo"].dropna().unique():
                cargo_lower = str(cargo).strip().lower()
                if cargo_lower and cargo_lower not in cargos_cadastrados:
                    resultado.adicionar_aviso(
                        "CARGO_NAO_CADASTRADO",
                        f"Cargo '{cargo}' em COLABORADORES_V2 não está em CARGOS_V2"
                    )
        
        return resultado


# =============================================================================
# VALIDADORES DE DADOS DE ENTRADA
# =============================================================================
class ValidadorAnaliseComercial:
    """Valida os dados da Análise Comercial."""
    
    COLUNAS_OBRIGATORIAS = [
        "Negócio",  # linha
        "Grupo",
        "Subgrupo",
        "Tipo de Mercadoria",
        "Fabricante",
        "Valor Realizado",  # faturamento
    ]
    
    COLUNAS_OPERACIONAL = [
        "Consultor Interno",
        "Representante-pedido",  # Consultor Externo
    ]
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def validar(self) -> ResultadoValidacao:
        """Executa validações nos dados comerciais."""
        resultado = ResultadoValidacao()
        
        # Verificar colunas obrigatórias
        resultado.merge(self._validar_colunas())
        
        # Verificar dados vazios
        resultado.merge(self._validar_dados_vazios())
        
        # Validar valores numéricos
        resultado.merge(self._validar_valores_numericos())
        
        return resultado
    
    def _validar_colunas(self) -> ResultadoValidacao:
        """Verifica se colunas obrigatórias existem."""
        resultado = ResultadoValidacao()
        
        for col in self.COLUNAS_OBRIGATORIAS:
            if col not in self.df.columns:
                resultado.adicionar_erro(
                    "COL_AC_AUSENTE",
                    f"Coluna obrigatória '{col}' ausente na Análise Comercial"
                )
        
        for col in self.COLUNAS_OPERACIONAL:
            if col not in self.df.columns:
                resultado.adicionar_aviso(
                    "COL_AC_AUSENTE",
                    f"Coluna operacional '{col}' ausente na Análise Comercial"
                )
        
        return resultado
    
    def _validar_dados_vazios(self) -> ResultadoValidacao:
        """Verifica dados vazios em colunas críticas."""
        resultado = ResultadoValidacao()
        
        # Hierarquia não pode ter todas vazias
        hier_cols = ["Negócio", "Grupo", "Subgrupo", "Tipo de Mercadoria", "Fabricante"]
        hier_cols_presentes = [c for c in hier_cols if c in self.df.columns]
        
        if hier_cols_presentes:
            todas_vazias = self.df[hier_cols_presentes].isna().all(axis=1)
            n_vazias = todas_vazias.sum()
            if n_vazias > 0:
                resultado.adicionar_aviso(
                    "HIERARQUIA_VAZIA",
                    f"{n_vazias} linha(s) com hierarquia completamente vazia"
                )
        
        return resultado
    
    def _validar_valores_numericos(self) -> ResultadoValidacao:
        """Valida valores numéricos (faturamento)."""
        resultado = ResultadoValidacao()
        
        if "Valor Realizado" in self.df.columns:
            faturamento = pd.to_numeric(self.df["Valor Realizado"], errors="coerce")
            
            # Valores negativos
            n_negativos = (faturamento < 0).sum()
            if n_negativos > 0:
                resultado.adicionar_aviso(
                    "FATURAMENTO_NEGATIVO",
                    f"{n_negativos} linha(s) com faturamento negativo"
                )
            
            # Valores nulos
            n_nulos = faturamento.isna().sum()
            if n_nulos > 0:
                resultado.adicionar_aviso(
                    "FATURAMENTO_NULO",
                    f"{n_nulos} linha(s) com faturamento nulo/inválido"
                )
        
        return resultado


# =============================================================================
# VALIDADOR DE SPLITS PARA REGRAS CC (GERENTE LINHA / COORDENADOR)
# =============================================================================

# Cargos que usam split por regra (CC, Fab) - soma deve ser 100%
CARGOS_COM_SPLIT = {"Gerente Linha", "Coordenador"}


def validar_splits_regras_cc(
    colaboradores: Dict[str, "ColaboradorV2"]
) -> ResultadoValidacao:
    """Valida que splits de mesmo cargo em mesma regra (CC, Fab) somam 100%.
    
    Para Gerente Linha e Coordenador, quando há múltiplos do mesmo cargo
    na mesma regra (CC, Fabricante), os splits devem somar exatamente 100%.
    
    Args:
        colaboradores: Dict nome -> ColaboradorV2 carregado do config.
        
    Returns:
        ResultadoValidacao com erros/avisos encontrados.
        
    Example:
        # Configuração válida:
        SAMANTA (Coordenador) CC=2.5.031, Fab=null, split=60
        JOÃO (Coordenador) CC=2.5.031, Fab=null, split=40
        # Soma = 100% ✓
        
        # Configuração inválida:
        SAMANTA (Coordenador) CC=2.5.031, Fab=null, split=60
        JOÃO (Coordenador) CC=2.5.031, Fab=null, split=60
        # Soma = 120% ✗
    """
    resultado = ResultadoValidacao()
    
    # Estrutura: {(CC, Fab, Cargo): [(nome, split), ...]}
    grupos: Dict[Tuple[str, Optional[str], str], List[Tuple[str, float]]] = {}
    
    for nome, colab in colaboradores.items():
        # Só processar cargos que usam split por regra
        if colab.cargo not in CARGOS_COM_SPLIT:
            continue
        
        for regra in colab.regras_cc:
            chave = (regra.centro_custo, regra.fabricante, colab.cargo)
            
            # Se split não definido, assume 100% (será verificado depois)
            split = regra.split if regra.split is not None else 100.0
            
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append((nome, split))
    
    # Verificar soma para grupos com múltiplos membros
    for chave, membros in grupos.items():
        cc, fab, cargo = chave
        fab_str = fab if fab else "TODOS"
        
        if len(membros) == 1:
            # Único do cargo na regra - split deveria ser 100% ou None
            nome, split = membros[0]
            if split != 100.0:
                resultado.adicionar_aviso(
                    "SPLIT_UNICO_NAO_100",
                    f"'{nome}' ({cargo}) é único na regra CC={cc}/Fab={fab_str} "
                    f"mas split={split}% (deveria ser 100% ou vazio)",
                    {"cc": cc, "fabricante": fab, "cargo": cargo, "split": split}
                )
        else:
            # Múltiplos do mesmo cargo - soma deve ser 100%
            soma = sum(s for _, s in membros)
            
            # Verificar se algum membro tem split=None (não definido)
            membros_sem_split = [n for n, s in membros if s == 100.0]
            
            # Tolerância numérica de 0.01%
            if abs(soma - 100.0) > 0.01:
                nomes_str = ", ".join(f"{n}({s}%)" for n, s in membros)
                resultado.adicionar_erro(
                    "SPLIT_SOMA_INVALIDA",
                    f"Splits para CC={cc}, Fab={fab_str}, Cargo={cargo} "
                    f"somam {soma:.1f}% (deveria ser 100%). "
                    f"Membros: {nomes_str}",
                    {"cc": cc, "fabricante": fab, "cargo": cargo, "membros": membros, "soma": soma}
                )
    
    # Log resumo
    if resultado.valido:
        logger.info(f"Validação de splits CC: {len(grupos)} grupos verificados, todos OK")
    else:
        n_erros = sum(1 for e in resultado.erros if e.tipo == "ERRO")
        logger.warning(f"Validação de splits CC: {n_erros} erro(s) encontrado(s)")
    
    return resultado


# =============================================================================
# FUNÇÃO PRINCIPAL DE VALIDAÇÃO
# =============================================================================
def validar_ambiente_v2(
    config_path: str = "config/REGRAS_COMISSOES_V2.xlsx",
    comercial_path: Optional[str] = None
) -> ResultadoValidacao:
    """Executa todas as validações do ambiente V2.
    
    Args:
        config_path: Caminho do arquivo de configuração
        comercial_path: Caminho da Análise Comercial (opcional)
        
    Returns:
        ResultadoValidacao consolidado
    """
    resultado = ResultadoValidacao()
    
    # Validar configuração
    logger.info("Validando configuração V2...")
    validador_config = ValidadorConfigV2(config_path)
    resultado.merge(validador_config.validar())
    
    # Validar dados comerciais se fornecido
    if comercial_path:
        logger.info("Validando Análise Comercial...")
        try:
            if comercial_path.endswith(".csv"):
                df_comercial = pd.read_csv(comercial_path, encoding="utf-8")
            else:
                df_comercial = pd.read_excel(comercial_path)
            
            validador_ac = ValidadorAnaliseComercial(df_comercial)
            resultado.merge(validador_ac.validar())
        except Exception as e:
            resultado.adicionar_erro(
                "AC_LOAD_ERROR",
                f"Erro ao carregar Análise Comercial: {e}"
            )
    
    logger.info(f"Validação concluída: {resultado.resumo()}")
    return resultado
