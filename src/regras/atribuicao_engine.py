"""
Motor de Atribuição Unificado — REGRAS_ATRIBUICAO
==================================================

Substitui as abas ATRIBUICOES (Wide) + CONFIG_COMISSAO por uma única tabela
em formato Long, com busca baseada em especificidade.

Campos hierárquicos (6):
    linha, grupo, subgrupo, tipo_mercadoria, fabricante, aplicacao

Colunas obrigatórias:
    colaborador, cargo, taxa_rateio_maximo_pct, fatia_cargo_pct

Coluna opcional:
    fator_split  (se vazio → auto-calculado: 1 / qtd_mesmo_cargo_na_regra)

Score de especificidade
-----------------------
Para cada regra (linha do DataFrame):
    - Campo hierárquico VAZIO → genérico, não filtra, score += 0
    - Campo hierárquico PREENCHIDO e BATE com o contexto → score += 1
    - Campo hierárquico PREENCHIDO e NÃO bate → regra EXCLUÍDA

Seleção por colaborador
-----------------------
TODOS os colaboradores que possuem qualquer regra compatível com o item
devem ser comissionados. Para cada colaborador, seleciona-se a regra mais
específica (maior score individual). Se um colaborador empata entre regras
distintas com mesmo score, usa ``resolver_empate``.

Regras rate-only (sem colaborador nomeado) seguem a lógica antiga: apenas
a(s) de maior score global são mantidas.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
HIERARCHY_FIELDS: List[str] = [
    "linha",
    "grupo",
    "subgrupo",
    "tipo_mercadoria",
    "fabricante",
    "aplicacao",
]

REQUIRED_COLUMNS: List[str] = [
    *HIERARCHY_FIELDS,
    "colaborador",
    "cargo",
    "taxa_rateio_maximo_pct",
    "fatia_cargo_pct",
]

_EMPTY_MARKERS = frozenset({"", "nan", "none", "nenhum"})


# ---------------------------------------------------------------------------
# Pré-processamento
# ---------------------------------------------------------------------------
def preprocessar_regras(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Normaliza e valida o DataFrame REGRAS_ATRIBUICAO carregado da planilha.

    Etapas:
        1. Valida colunas obrigatórias.
        2. Normaliza campos hierárquicos (strip + upper; NaN → ``""``).
        3. Normaliza ``colaborador`` e ``cargo`` (strip; NaN → ``""``).
        4. Converte colunas numéricas (taxa/fatia/split) para float.
        5. Calcula ``fator_split`` automático quando a coluna está vazia.

    Args:
        df_raw: DataFrame bruto lido do Excel / CSV.

    Returns:
        DataFrame preprocessado pronto para uso nas buscas.

    Raises:
        ValueError: Se colunas obrigatórias estiverem faltando.
    """
    df = df_raw.copy()

    # --- Validar colunas obrigatórias ---
    df.columns = df.columns.astype(str).str.strip().str.lower()
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"REGRAS_ATRIBUICAO: colunas obrigatórias ausentes: {missing_cols}"
        )

    # --- Normalizar campos hierárquicos ---
    for field in HIERARCHY_FIELDS:
        df[field] = (
            df[field]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )
        # Mapear marcadores de vazio para ""
        df.loc[df[field].str.lower().isin(_EMPTY_MARKERS), field] = ""

    # --- Normalizar colaborador / cargo ---
    df["colaborador"] = df["colaborador"].fillna("").astype(str).str.strip()
    df["cargo"] = df["cargo"].fillna("").astype(str).str.strip()

    # --- Converter numéricas ---
    for col in ("taxa_rateio_maximo_pct", "fatia_cargo_pct"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # --- fator_split: usar valor existente ou auto-calcular ---
    if "fator_split" not in df.columns:
        df["fator_split"] = np.nan

    df["fator_split"] = pd.to_numeric(df["fator_split"], errors="coerce")

    # Criar chave de regra (combinação dos 6 campos hierárquicos)
    df["_regra_key"] = (
        df[HIERARCHY_FIELDS].astype(str).agg("|".join, axis=1)
    )

    # Auto-calcular split para linhas sem valor explícito
    mask_needs_split = df["fator_split"].isna() & (df["colaborador"] != "")
    if mask_needs_split.any():
        # Contar colaboradores com mesmo cargo na mesma regra
        count_df = (
            df[df["colaborador"] != ""]
            .groupby(["_regra_key", "cargo"])
            .size()
            .rename("_count")
            .reset_index()
        )
        df = df.merge(count_df, on=["_regra_key", "cargo"], how="left")
        df.loc[mask_needs_split, "fator_split"] = 1.0 / df.loc[
            mask_needs_split, "_count"
        ].clip(lower=1)
        df.drop(columns=["_count"], inplace=True, errors="ignore")

    # Linhas de taxa-only (sem colaborador) → fator_split = 1.0
    df.loc[(df["colaborador"] == "") & df["fator_split"].isna(), "fator_split"] = 1.0

    # Preencher NaN restantes
    df["fator_split"] = df["fator_split"].fillna(1.0)

    return df


# ---------------------------------------------------------------------------
# Busca por Especificidade
# ---------------------------------------------------------------------------
def _calcular_scores(
    df: pd.DataFrame,
    contexto: Dict[str, str],
) -> Tuple[pd.Series, pd.Series]:
    """Calcula score de especificidade e máscara de validade para cada linha.

    Args:
        df: DataFrame REGRAS_ATRIBUICAO preprocessado.
        contexto: Dict com os 6 campos hierárquicos do item.

    Returns:
        Tupla (mask_valida, scores) — ambas pd.Series indexadas como ``df``.
    """
    mask_valida = pd.Series(True, index=df.index)
    scores = pd.Series(0, index=df.index, dtype=int)

    for field in HIERARCHY_FIELDS:
        regra_val = df[field]  # já está normalizado (upper, stripped)
        ctx_val = str(contexto.get(field, "")).strip().upper()

        is_empty = regra_val == ""
        matches = regra_val == ctx_val

        # Preenchido e NÃO bate → excluir
        mask_valida = mask_valida & (is_empty | matches)

        # Preenchido e bate → score += 1
        scores = scores + (~is_empty & matches).astype(int)

    return mask_valida, scores


def buscar_regras_item(
    df_regras: pd.DataFrame,
    contexto: Dict[str, str],
    cargo_filtro: Optional[str] = None,
    resolver_empate: Optional[Callable] = None,
) -> List[Dict]:
    """Busca regras aplicáveis para um item, retornando TODOS os colaboradores
    que possuem alguma atribuição compatível, cada um com sua regra mais específica.

    Lógica:
        1. Calcula score de especificidade para cada regra.
        2. Exclui regras incompatíveis (campo preenchido que não bate).
        3. Para cada colaborador nomeado, seleciona a regra com MAIOR score
           individual (a mais específica dele para este item).
        4. Para regras rate-only (sem colaborador), seleciona a(s) de maior score.
        5. Em caso de empate entre regras distintas para o mesmo colaborador,
           usa ``resolver_empate`` se fornecido.

    Args:
        df_regras: DataFrame REGRAS_ATRIBUICAO preprocessado.
        contexto: Dict com 6 campos hierárquicos do item.
        cargo_filtro: Se informado, retorna somente entradas deste cargo.
        resolver_empate: Callable(df_empatadas, contexto, score) → df_escolhida.
            Se ``None`` e houver empate, todas as regras empatadas são retornadas.

    Returns:
        Lista de dicts, ordenada por score DESC::

            [
                {
                    "colaborador": str,
                    "cargo": str,
                    "taxa_rateio_maximo_pct": float,
                    "fatia_cargo_pct": float,
                    "fator_split": float,
                    "score": int,
                },
                ...
            ]
    """
    if df_regras.empty:
        return []

    mask_valida, scores = _calcular_scores(df_regras, contexto)

    df_valid = df_regras[mask_valida].copy()
    scores_valid = scores[mask_valida]

    if df_valid.empty:
        return []

    df_valid["_score"] = scores_valid

    # --- Filtro de cargo (aplicar cedo para reduzir trabalho) ---
    if cargo_filtro:
        cargo_upper = cargo_filtro.strip()
        df_valid = df_valid[df_valid["cargo"].str.strip() == cargo_upper]
        if df_valid.empty:
            return []

    # --- Separar colaboradores nomeados vs rate-only ---
    mask_nomeado = df_valid["colaborador"].str.strip() != ""
    df_nomeados = df_valid[mask_nomeado]
    df_rate_only = df_valid[~mask_nomeado]

    resultado: List[Dict] = []

    # --- Colaboradores nomeados: para cada um, manter regra mais específica ---
    if not df_nomeados.empty:
        df_nomeados = df_nomeados.copy()
        df_nomeados["_colab_key"] = (
            df_nomeados["colaborador"].str.strip().str.lower()
        )

        for _colab_key, grupo_colab in df_nomeados.groupby("_colab_key"):
            max_score_colab = int(grupo_colab["_score"].max())
            melhores = grupo_colab[grupo_colab["_score"] == max_score_colab]

            # Empate entre regras DISTINTAS para este colaborador
            if (
                resolver_empate is not None
                and "_regra_key" in melhores.columns
                and melhores["_regra_key"].nunique() > 1
            ):
                melhores = resolver_empate(
                    melhores, contexto, max_score_colab
                )

            for _, row in melhores.iterrows():
                resultado.append(
                    {
                        "colaborador": row["colaborador"],
                        "cargo": row["cargo"],
                        "taxa_rateio_maximo_pct": float(
                            row["taxa_rateio_maximo_pct"]
                        ),
                        "fatia_cargo_pct": float(row["fatia_cargo_pct"]),
                        "fator_split": float(row["fator_split"]),
                        "score": max_score_colab,
                    }
                )

    # --- Rate-only: manter apenas a(s) de maior score ---
    if not df_rate_only.empty:
        max_score_rate = int(df_rate_only["_score"].max())
        melhores_rate = df_rate_only[
            df_rate_only["_score"] == max_score_rate
        ]

        # Empate entre regras rate-only distintas
        if (
            resolver_empate is not None
            and "_regra_key" in melhores_rate.columns
            and melhores_rate["_regra_key"].nunique() > 1
        ):
            melhores_rate = resolver_empate(
                melhores_rate, contexto, max_score_rate
            )

        for _, row in melhores_rate.iterrows():
            resultado.append(
                {
                    "colaborador": row["colaborador"],
                    "cargo": row["cargo"],
                    "taxa_rateio_maximo_pct": float(
                        row["taxa_rateio_maximo_pct"]
                    ),
                    "fatia_cargo_pct": float(row["fatia_cargo_pct"]),
                    "fator_split": float(row["fator_split"]),
                    "score": max_score_rate,
                }
            )

    # --- Ordenar por score DESC (mais específicos primeiro) ---
    resultado.sort(key=lambda r: r["score"], reverse=True)

    return resultado


def buscar_taxa_para_cargo(
    df_regras: pd.DataFrame,
    contexto: Dict[str, str],
    cargo: str,
) -> Optional[Dict]:
    """Busca a taxa de comissão para um cargo específico num dado contexto.

    Útil para colaboradores operacionais cujo nome vem de FATURADOS (não da
    aba de regras). Primeiro tenta encontrar uma regra nomeada; se não houver,
    aceita uma regra rate-only (colaborador vazio).

    Args:
        df_regras: DataFrame REGRAS_ATRIBUICAO preprocessado.
        contexto: Dict com 6 campos hierárquicos.
        cargo: Nome do cargo (ex: ``"Consultor Interno"``).

    Returns:
        Dict com ``taxa_rateio_maximo_pct``, ``fatia_cargo_pct``, ``fator_split``
        ou ``None`` se nenhuma regra for encontrada.
    """
    resultados = buscar_regras_item(df_regras, contexto, cargo_filtro=cargo)
    if resultados:
        r = resultados[0]
        return {
            "taxa_rateio_maximo_pct": r["taxa_rateio_maximo_pct"],
            "fatia_cargo_pct": r["fatia_cargo_pct"],
            "fator_split": r["fator_split"],
        }
    return None


# ---------------------------------------------------------------------------
# Funções Auxiliares (substituem _colaborador_tem_atribuicao_wide, etc.)
# ---------------------------------------------------------------------------
def colaborador_tem_atribuicao(
    df_regras: pd.DataFrame,
    nome_colaborador: str,
    linha: Optional[str] = None,
) -> bool:
    """Verifica se um colaborador possui atribuição em REGRAS_ATRIBUICAO.

    Args:
        df_regras: DataFrame REGRAS_ATRIBUICAO preprocessado.
        nome_colaborador: Nome do colaborador.
        linha: Se informado, restringe a verificação a esta linha de negócio.

    Returns:
        ``True`` se o colaborador possui pelo menos uma entrada.
    """
    if df_regras.empty or not nome_colaborador:
        return False

    nome_norm = str(nome_colaborador).strip().lower()
    mask = df_regras["colaborador"].str.strip().str.lower() == nome_norm

    if linha:
        linha_norm = str(linha).strip().upper()
        mask = mask & (df_regras["linha"] == linha_norm)

    return mask.any()


def obter_linhas_colaborador(
    df_regras: pd.DataFrame,
    nome_colaborador: str,
) -> List[str]:
    """Retorna todas as linhas de negócio onde um colaborador tem atribuição.

    Args:
        df_regras: DataFrame REGRAS_ATRIBUICAO preprocessado.
        nome_colaborador: Nome do colaborador.

    Returns:
        Lista de linhas (strings) distintas.
    """
    if df_regras.empty or not nome_colaborador:
        return []

    nome_norm = str(nome_colaborador).strip().lower()
    mask = df_regras["colaborador"].str.strip().str.lower() == nome_norm
    linhas = df_regras.loc[mask, "linha"].str.strip().unique().tolist()
    return [l for l in linhas if l]  # remover vazios


# ---------------------------------------------------------------------------
# Resolução de Empate (Terminal)
# ---------------------------------------------------------------------------
def resolver_empate_terminal(
    df_empatadas: pd.DataFrame,
    contexto: Dict[str, str],
    score: int,
) -> pd.DataFrame:
    """Resolve empate de regras via prompt interativo no terminal.

    Apresenta as regras empatadas ao operador e solicita escolha numérica.

    Args:
        df_empatadas: DataFrame com todas as entradas das regras empatadas.
        contexto: Dict com os 6 campos hierárquicos do item.
        score: Score de especificidade das regras empatadas.

    Returns:
        DataFrame filtrado contendo apenas as entradas da regra escolhida.
    """
    grupos = list(df_empatadas.groupby("_regra_key"))

    print(f"\n{'=' * 70}")
    print(f"  EMPATE DE REGRAS  (Score de Especificidade: {score})")
    print(f"{'=' * 70}")
    print(f"  Contexto do item:")
    for campo, valor in contexto.items():
        if campo in HIERARCHY_FIELDS:
            print(f"    {campo:20s} = {valor}")
    print(f"\n  {len(grupos)} regras empatadas:\n")

    opcoes: List[pd.DataFrame] = []
    for i, (regra_key, grupo_df) in enumerate(grupos, 1):
        # Mostrar campos preenchidos da regra
        sample = grupo_df.iloc[0]
        campos_preenchidos = {
            f: sample[f] for f in HIERARCHY_FIELDS if sample[f] != ""
        }
        print(f"  [{i}] Regra: {campos_preenchidos}")
        for _, row in grupo_df.iterrows():
            nome = row["colaborador"] if row["colaborador"] else "(taxa-genérica)"
            print(
                f"      • {nome} ({row['cargo']})"
                f"  taxa={row['taxa_rateio_maximo_pct']}%"
                f"  fatia={row['fatia_cargo_pct']}%"
                f"  split={row['fator_split']}"
            )
        opcoes.append(grupo_df)

    print()

    while True:
        try:
            escolha = input(f"  Escolha a regra (1-{len(opcoes)}): ").strip()
            idx = int(escolha) - 1
            if 0 <= idx < len(opcoes):
                print(f"  → Regra [{idx + 1}] selecionada.\n")
                return opcoes[idx]
        except (ValueError, EOFError):
            pass
        print(f"  Opção inválida. Digite um número entre 1 e {len(opcoes)}.")


# ---------------------------------------------------------------------------
# Validação de Cobertura
# ---------------------------------------------------------------------------
def validar_cobertura_hierarquias(
    df_regras: pd.DataFrame,
    hierarquias_ativas: set,
    cargos_gestao: List[str],
) -> List[Dict]:
    """Verifica se todas as hierarquias ativas possuem regras com gestores.

    Args:
        df_regras: DataFrame REGRAS_ATRIBUICAO preprocessado.
        hierarquias_ativas: Set de tuplas (linha, grupo, subgrupo, tipo_mercadoria,
            fabricante, aplicacao) extraídas de FATURADOS.
        cargos_gestao: Lista de nomes de cargos de gestão.

    Returns:
        Lista de dicts com hierarquias sem cobertura adequada. Vazia se tudo OK.
    """
    problemas: List[Dict] = []
    cargos_set = set(c.strip() for c in cargos_gestao)

    for h_key in hierarquias_ativas:
        contexto = dict(zip(HIERARCHY_FIELDS, h_key))
        resultados = buscar_regras_item(df_regras, contexto)

        # Verificar se há pelo menos um gestor nomeado
        gestores = [
            r for r in resultados
            if r["cargo"] in cargos_set and r["colaborador"]
        ]

        if not gestores:
            problemas.append(
                {
                    "hierarquia": h_key,
                    "motivo": (
                        "Nenhum gestor nomeado encontrado em REGRAS_ATRIBUICAO"
                        if resultados
                        else "Hierarquia não coberta por nenhuma regra"
                    ),
                }
            )

    return problemas
