"""
Testes unitários: Motor de Atribuição Unificado (REGRAS_ATRIBUICAO).

Módulo testado: src/regras/atribuicao_engine.py
Funções testadas:
  - preprocessar_regras()
  - buscar_regras_item()       ← lógica per-collaborator selection
  - buscar_taxa_para_cargo()
  - colaborador_tem_atribuicao()
  - obter_linhas_colaborador()
  - validar_cobertura_hierarquias()

Lógica de negócio central:
  TODOS os colaboradores que possuem qualquer regra compatível devem ser
  comissionados, cada um com sua regra mais específica (maior score individual).
  Colaboradores com regras genéricas NÃO são descartados em favor de
  colaboradores com regras mais específicas.

Referência: documentacoes/DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md, Seção 4.9
"""

from pathlib import Path

import pandas as pd
import numpy as np
import pytest

from src.regras.atribuicao_engine import (
    preprocessar_regras,
    buscar_regras_item,
    buscar_taxa_para_cargo,
    colaborador_tem_atribuicao,
    obter_linhas_colaborador,
    validar_cobertura_hierarquias,
    HIERARCHY_FIELDS,
    REQUIRED_COLUMNS,
)
from tests.conftest import load_fixture_csv


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def df_raw():
    """DataFrame bruto lido do CSV de fixture (sem preprocessamento)."""
    return load_fixture_csv(__file__, "regras_atribuicao.csv")


@pytest.fixture(scope="module")
def df_regras(df_raw):
    """DataFrame preprocessado, pronto para uso nas buscas."""
    return preprocessar_regras(df_raw)


# ──────────────────────────────────────────────────────────────────────
# Contextos reutilizáveis
# ──────────────────────────────────────────────────────────────────────

def _ctx_full():
    """Contexto que bate com todos 6 campos (rows 1,2)."""
    return {
        "linha": "INDUSTRIAL",
        "grupo": "EQUIPAMENTOS",
        "subgrupo": "BOMBAS",
        "tipo_mercadoria": "CENTRIFUGAS",
        "fabricante": "KSB",
        "aplicacao": "SANEAMENTO",
    }


def _ctx_valvulas():
    """Contexto INDUSTRIAL+EQUIPAMENTOS+VALVULAS (bate com row 12)."""
    return {
        "linha": "INDUSTRIAL",
        "grupo": "EQUIPAMENTOS",
        "subgrupo": "VALVULAS",
        "tipo_mercadoria": "",
        "fabricante": "",
        "aplicacao": "",
    }


def _ctx_sulzer():
    """Contexto como _ctx_full mas fabricante=SULZER (não KSB)."""
    return {
        "linha": "INDUSTRIAL",
        "grupo": "EQUIPAMENTOS",
        "subgrupo": "BOMBAS",
        "tipo_mercadoria": "CENTRIFUGAS",
        "fabricante": "SULZER",
        "aplicacao": "SANEAMENTO",
    }


def _ctx_desconhecido():
    """Contexto que não bate com nenhuma regra específica (só global score=0)."""
    return {
        "linha": "QUIMICA",
        "grupo": "ESPECIAL",
        "subgrupo": "",
        "tipo_mercadoria": "",
        "fabricante": "",
        "aplicacao": "",
    }


# ======================================================================
# GRUPO A — Pré-processamento (6 testes)
# ======================================================================

@pytest.mark.unit
class TestPreprocessamento:
    """Testa preprocessar_regras(): normalização, split automático, validação."""

    def test_preprocessar_normaliza_upper(self, df_regras):
        """A1: Campos hierárquicos devem ser normalizados para UPPERCASE.

        Entrada: CSV com valores como 'INDUSTRIAL', 'EQUIPAMENTOS' (já upper
        no fixture, mas o engine deve garantir via .str.upper()).

        Resultado esperado: Todos os campos hierárquicos em uppercase.
        Verifica rows 1,5,8 como amostra representativa.
        """
        # Row 0 (row 1 do CSV): todos os 6 campos preenchidos
        row0 = df_regras.iloc[0]
        assert row0["linha"] == "INDUSTRIAL"
        assert row0["grupo"] == "EQUIPAMENTOS"
        assert row0["subgrupo"] == "BOMBAS"
        assert row0["tipo_mercadoria"] == "CENTRIFUGAS"
        assert row0["fabricante"] == "KSB"
        assert row0["aplicacao"] == "SANEAMENTO"

        # Row 4 (row 5 do CSV): só linha preenchida
        row4 = df_regras.iloc[4]
        assert row4["linha"] == "INDUSTRIAL"

        # Row 7 (row 8 do CSV): AMBIENTAL
        row7 = df_regras.iloc[7]
        assert row7["linha"] == "AMBIENTAL"
        assert row7["grupo"] == "TRATAMENTO"

    def test_preprocessar_nan_para_vazio(self, df_regras):
        """A2: Campos hierárquicos NaN/vazios devem virar string vazia "".

        Entrada: Row 3 (idx=2) tem tipo_mercadoria, fabricante, aplicacao
        vazios no CSV. Row 7 (idx=6) tem TODOS os campos vazios (regra global).

        Resultado esperado: Todos NaN convertidos para "".
        """
        # Row 2 (row 3 do CSV): campos parcialmente vazios
        row2 = df_regras.iloc[2]
        assert row2["tipo_mercadoria"] == ""
        assert row2["fabricante"] == ""
        assert row2["aplicacao"] == ""

        # Row 6 (row 7 do CSV): regra global — tudo vazio
        row6 = df_regras.iloc[6]
        for field in HIERARCHY_FIELDS:
            assert row6[field] == "", f"Campo {field} deveria ser '' mas é '{row6[field]}'"

    def test_preprocessar_auto_split_single(self, df_regras):
        """A3: Colaborador único no cargo+regra → fator_split auto = 1.0.

        Entrada: Row 1 (idx=0, João GL na regra score-6). Maria é Coordenador
        na mesma regra, mas cargo diferente → não conta para auto-split de GL.

        Resultado esperado: João na row 0 tem split=1.0 (único GL na regra 6).
        Maria na row 1 tem split=1.0 (única Coord na regra 6).
        """
        # João GL na regra score-6: único GL nessa regra
        row0 = df_regras.iloc[0]
        assert row0["colaborador"] == "João Silva"
        assert row0["cargo"] == "Gerente Linha"
        assert row0["fator_split"] == pytest.approx(1.0)

        # Maria Coord na mesma regra: única Coord
        row1 = df_regras.iloc[1]
        assert row1["colaborador"] == "Maria Souza"
        assert row1["cargo"] == "Coordenador"
        assert row1["fator_split"] == pytest.approx(1.0)

    def test_preprocessar_auto_split_double(self, df_regras):
        """A4: Dois colaboradores mesmo cargo + mesma regra → split auto = 0.5.

        Entrada: Rows 3-4 (idx=2,3): João GL + Pedro GL na regra
        INDUSTRIAL|EQUIPAMENTOS|BOMBAS (score-3). Ambos sem split explícito.

        Resultado esperado: fator_split = 1/2 = 0.5 para ambos.
        """
        row2 = df_regras.iloc[2]
        row3 = df_regras.iloc[3]
        assert row2["colaborador"] == "João Silva"
        assert row3["colaborador"] == "Pedro Lima"
        assert row2["fator_split"] == pytest.approx(0.5)
        assert row3["fator_split"] == pytest.approx(0.5)

    def test_preprocessar_split_explicito(self, df_regras):
        """A5: Split definido manualmente na planilha é preservado.

        Entrada: Rows 5-6 (idx=4,5): Ana split=0.7, Lucia split=0.3.
        Ambas na mesma regra INDUSTRIAL (score-1) com cargo GL.

        Resultado esperado: Valores explícitos mantidos, não recalculados.
        """
        row4 = df_regras.iloc[4]
        row5 = df_regras.iloc[5]
        assert row4["colaborador"] == "Ana Costa"
        assert row4["fator_split"] == pytest.approx(0.7)
        assert row5["colaborador"] == "Lucia Reis"
        assert row5["fator_split"] == pytest.approx(0.3)

    def test_preprocessar_colunas_faltantes(self):
        """A6: DataFrame sem coluna obrigatória deve levantar ValueError.

        Entrada: DataFrame com apenas 'linha' e 'colaborador' (faltam cargo,
        taxa_rateio_maximo_pct, fatia_cargo_pct, grupo, subgrupo, etc.).

        Resultado esperado: ValueError com mensagem indicando colunas ausentes.
        """
        df_incompleto = pd.DataFrame({
            "linha": ["INDUSTRIAL"],
            "colaborador": ["João"],
        })
        with pytest.raises(ValueError, match="colunas obrigatórias ausentes"):
            preprocessar_regras(df_incompleto)


# ======================================================================
# GRUPO B — Busca por Especificidade Per-Collaborator (8 testes)
# ======================================================================

@pytest.mark.unit
class TestBuscaEspecificidade:
    """Testa buscar_regras_item(): seleção per-collaborator, rate-only,
    exclusão por mismatch, filtro de cargo, resolver_empate."""

    def test_busca_retorna_todos_colaboradores_diferentes_scores(self, df_regras):
        """B1: O TESTE CENTRAL — todos colaboradores com qualquer regra
        compatível são retornados, cada um com seu melhor score individual.

        Entrada: Contexto IND+EQUIP+BOMBAS+CENTR+KSB+SANEA (bate com score-6).

        Cálculo de scores por row do fixture:
          Row 1  João   GL    → 6/6 campos batem      → score=6  ✓
          Row 2  Maria  Coord → 6/6 campos batem      → score=6  ✓
          Row 3  João   GL    → 3/3 campos batem + 3 vazios → score=3  ✓
          Row 4  Pedro  GL    → 3/3 campos batem + 3 vazios → score=3  ✓
          Row 5  Ana    GL    → 1/1 campo bate + 5 vazios   → score=1  ✓
          Row 6  Lucia  GL    → 1/1 campo bate + 5 vazios   → score=1  ✓
          Row 7  Roberto Dir  → 0 campos (all empty)        → score=0  ✓
          Row 8  Felipe GL    → AMBIENTAL≠INDUSTRIAL        → EXCLUÍDA
          Row 9  (rate) CI    → 1/1 campo bate              → score=1  ✓
          Row 10 (rate) CI    → 0 campos                    → score=0  ✓
          Row 11 Bruno  Coord → AMBIENTAL≠INDUSTRIAL        → EXCLUÍDA
          Row 12 João   GL    → VALVULAS≠BOMBAS             → EXCLUÍDA

        Seleção per-collaborator (maior score individual):
          João    → rows 1(s6) vs 3(s3) → row 1: score=6, taxa=5.0, split=1.0
          Maria   → row 2(s6)           → row 2: score=6, taxa=3.0, split=1.0
          Pedro   → row 4(s3)           → row 4: score=3, taxa=4.0, split=0.5
          Ana     → row 5(s1)           → row 5: score=1, taxa=3.0, split=0.7
          Lucia   → row 6(s1)           → row 6: score=1, taxa=3.0, split=0.3
          Roberto → row 7(s0)           → row 7: score=0, taxa=2.0, split=1.0

        Seleção rate-only (maior score global entre rate-only):
          Row 9(s1) vs Row 10(s0) → row 9: score=1, taxa=2.5, split=1.0

        Resultado esperado: 7 resultados, ordenados por score DESC.
        """
        ctx = _ctx_full()
        resultados = buscar_regras_item(df_regras, ctx)

        # Deve haver 7 resultados (6 nomeados + 1 rate-only)
        assert len(resultados) == 7, (
            f"Esperado 7 resultados, obteve {len(resultados)}: "
            f"{[r['colaborador'] or '(rate-only)' for r in resultados]}"
        )

        # Construir lookup por colaborador (nomeados)
        por_nome = {}
        rate_only_list = []
        for r in resultados:
            if r["colaborador"].strip():
                por_nome[r["colaborador"].strip().lower()] = r
            else:
                rate_only_list.append(r)

        # João Silva → score=6, taxa=5.0, split=1.0
        joao = por_nome["joão silva"]
        assert joao["score"] == 6
        assert joao["taxa_rateio_maximo_pct"] == pytest.approx(5.0)
        assert joao["fator_split"] == pytest.approx(1.0)

        # Maria Souza → score=6, taxa=3.0, split=1.0
        maria = por_nome["maria souza"]
        assert maria["score"] == 6
        assert maria["taxa_rateio_maximo_pct"] == pytest.approx(3.0)

        # Pedro Lima → score=3, taxa=4.0, split=0.5
        pedro = por_nome["pedro lima"]
        assert pedro["score"] == 3
        assert pedro["taxa_rateio_maximo_pct"] == pytest.approx(4.0)
        assert pedro["fator_split"] == pytest.approx(0.5)

        # Ana Costa → score=1, taxa=3.0, split=0.7
        ana = por_nome["ana costa"]
        assert ana["score"] == 1
        assert ana["taxa_rateio_maximo_pct"] == pytest.approx(3.0)
        assert ana["fator_split"] == pytest.approx(0.7)

        # Lucia Reis → score=1, taxa=3.0, split=0.3
        lucia = por_nome["lucia reis"]
        assert lucia["score"] == 1
        assert lucia["fator_split"] == pytest.approx(0.3)

        # Roberto Neto → score=0, taxa=2.0, split=1.0
        roberto = por_nome["roberto neto"]
        assert roberto["score"] == 0
        assert roberto["taxa_rateio_maximo_pct"] == pytest.approx(2.0)

        # Rate-only → score=1, taxa=2.5 (row 9 vence row 10)
        assert len(rate_only_list) == 1
        assert rate_only_list[0]["score"] == 1
        assert rate_only_list[0]["taxa_rateio_maximo_pct"] == pytest.approx(2.5)

        # Verificar ordenação por score DESC
        scores = [r["score"] for r in resultados]
        assert scores == sorted(scores, reverse=True), (
            f"Resultado não está ordenado por score DESC: {scores}"
        )

    def test_busca_regra_mais_especifica_individual(self, df_regras):
        """B2: Contexto VALVULAS — João tem regra score-3 (row 12), as regras
        de BOMBAS (rows 1,3) são excluídas por mismatch em subgrupo.

        Entrada: Contexto IND+EQUIP+VALVULAS (demais vazio).

        Cálculo:
          Rows 1,2 → BOMBAS≠VALVULAS           → EXCLUÍDAS
          Rows 3,4 → BOMBAS≠VALVULAS           → EXCLUÍDAS
          Row 5  Ana    GL → IND match, rest vazio → score=1
          Row 6  Lucia  GL → IND match, rest vazio → score=1
          Row 7  Roberto Dir → all empty           → score=0
          Row 8  Felipe → AMBIENTAL≠INDUSTRIAL   → EXCLUÍDA
          Row 9  (rate) CI → IND match             → score=1
          Row 10 (rate) CI → all empty             → score=0
          Row 11 Bruno → AMBIENTAL≠INDUSTRIAL     → EXCLUÍDA
          Row 12 João GL → IND+EQUIP+VALVULAS all match → score=3

        Per-collaborator: João(s3), Ana(s1), Lucia(s1), Roberto(s0)
        Rate-only: row 9(s1)

        Resultado esperado: 5 resultados.
        """
        ctx = _ctx_valvulas()
        resultados = buscar_regras_item(df_regras, ctx)

        assert len(resultados) == 5

        por_nome = {
            r["colaborador"].strip().lower(): r
            for r in resultados if r["colaborador"].strip()
        }

        # João usa row 12 (score=3, taxa=4.5)
        assert por_nome["joão silva"]["score"] == 3
        assert por_nome["joão silva"]["taxa_rateio_maximo_pct"] == pytest.approx(4.5)

        # Ana (score=1), Lucia (score=1), Roberto (score=0) presentes
        assert por_nome["ana costa"]["score"] == 1
        assert por_nome["lucia reis"]["score"] == 1
        assert por_nome["roberto neto"]["score"] == 0

    def test_busca_exclusao_mismatch_com_fallback(self, df_regras):
        """B3: Fabricante SULZER (não KSB) — rows 1,2 excluídas, João cai
        para sua regra score-3 (row 3). Maria desaparece completamente.

        Entrada: Contexto IND+EQUIP+BOMBAS+CENTR+SULZER+SANEA.

        Cálculo:
          Row 1  João GL  → KSB≠SULZER             → EXCLUÍDA
          Row 2  Maria Coord → KSB≠SULZER           → EXCLUÍDA
          Row 3  João GL  → 3/3 match + 3 empty     → score=3
          Row 4  Pedro GL → 3/3 match + 3 empty     → score=3
          Row 5  Ana GL   → 1/1 match               → score=1
          Row 6  Lucia GL → 1/1 match               → score=1
          Row 7  Roberto Dir → all empty             → score=0
          Row 8  Felipe   → AMBIENTAL≠INDUSTRIAL    → EXCLUÍDA
          Row 9  (rate) CI → IND match               → score=1
          Row 10 (rate) CI → all empty               → score=0
          Row 11 Bruno    → AMBIENTAL≠INDUSTRIAL     → EXCLUÍDA
          Row 12 João GL  → VALVULAS≠BOMBAS          → EXCLUÍDA

        Per-collaborator: João(s3, taxa=4.0), Pedro(s3), Ana(s1), Lucia(s1), Roberto(s0)
        Rate-only: row 9(s1)

        Resultado esperado: 6 resultados, Maria NÃO aparece.
        """
        ctx = _ctx_sulzer()
        resultados = buscar_regras_item(df_regras, ctx)

        assert len(resultados) == 6

        nomes = {r["colaborador"].strip().lower() for r in resultados if r["colaborador"].strip()}
        assert "maria souza" not in nomes, "Maria deveria ser excluída (KSB≠SULZER)"

        por_nome = {
            r["colaborador"].strip().lower(): r
            for r in resultados if r["colaborador"].strip()
        }

        # João cai para score=3, taxa=4.0, split=0.5 (row 3 — divide com Pedro)
        assert por_nome["joão silva"]["score"] == 3
        assert por_nome["joão silva"]["taxa_rateio_maximo_pct"] == pytest.approx(4.0)
        assert por_nome["joão silva"]["fator_split"] == pytest.approx(0.5)

        # Pedro score=3
        assert por_nome["pedro lima"]["score"] == 3

    def test_busca_generica_fallback_score_0(self, df_regras):
        """B4: Contexto totalmente desconhecido — apenas regras genéricas
        (score=0) são compatíveis.

        Entrada: Contexto QUIMICA+ESPECIAL (nenhuma regra preenchida bate).

        Cálculo:
          Rows 1-6 → INDUSTRIAL≠QUIMICA      → EXCLUÍDAS
          Row 7  Roberto Dir → all empty       → score=0  ✓
          Row 8  Felipe → AMBIENTAL≠QUIMICA    → EXCLUÍDA
          Row 9  (rate) → INDUSTRIAL≠QUIMICA   → EXCLUÍDA
          Row 10 (rate) → all empty            → score=0  ✓
          Row 11 Bruno → AMBIENTAL≠QUIMICA     → EXCLUÍDA
          Row 12 João → INDUSTRIAL≠QUIMICA     → EXCLUÍDA

        Per-collaborator: Roberto(s0)
        Rate-only: row 10(s0)

        Resultado esperado: 2 resultados.
        """
        ctx = _ctx_desconhecido()
        resultados = buscar_regras_item(df_regras, ctx)

        assert len(resultados) == 2

        por_nome = {
            r["colaborador"].strip().lower(): r
            for r in resultados if r["colaborador"].strip()
        }

        assert "roberto neto" in por_nome
        assert por_nome["roberto neto"]["score"] == 0
        assert por_nome["roberto neto"]["taxa_rateio_maximo_pct"] == pytest.approx(2.0)

        # Rate-only score=0
        rate_only = [r for r in resultados if not r["colaborador"].strip()]
        assert len(rate_only) == 1
        assert rate_only[0]["score"] == 0
        assert rate_only[0]["taxa_rateio_maximo_pct"] == pytest.approx(2.0)

    def test_busca_dataframe_vazio_retorna_lista_vazia(self):
        """B5: DataFrame vazio → retorna lista vazia imediatamente.

        Entrada: DataFrame vazio (0 rows) com colunas corretas.
        Resultado esperado: []
        """
        df_vazio = pd.DataFrame(columns=REQUIRED_COLUMNS + ["_regra_key", "fator_split"])
        resultado = buscar_regras_item(df_vazio, _ctx_full())
        assert resultado == []

    def test_busca_filtro_cargo_gerente_linha(self, df_regras):
        """B6: cargo_filtro restringe resultado apenas a Gerente Linha.

        Entrada: Contexto IND+EQUIP+BOMBAS+CENTR+KSB+SANEA, cargo_filtro="Gerente Linha".

        Cálculo (mesmos scores de B1, mas filtrando só GL):
          João(s6), Pedro(s3), Ana(s1), Lucia(s1) — todos GL

        Excluídos por filtro: Maria(Coord), Roberto(Dir), rate-only(CI)

        Resultado esperado: 4 resultados, todos com cargo "Gerente Linha".
        """
        ctx = _ctx_full()
        resultados = buscar_regras_item(
            df_regras, ctx, cargo_filtro="Gerente Linha"
        )

        assert len(resultados) == 4

        # Todos devem ter cargo "Gerente Linha"
        for r in resultados:
            assert r["cargo"].strip() == "Gerente Linha"

        nomes = {r["colaborador"].strip().lower() for r in resultados}
        assert nomes == {"joão silva", "pedro lima", "ana costa", "lucia reis"}

    def test_busca_rate_only_maior_score(self, df_regras):
        """B7: cargo_filtro="Consultor Interno" retorna apenas rate-only de
        maior score.

        Entrada: Contexto INDUSTRIAL+..., cargo_filtro="Consultor Interno".

        Cálculo rate-only:
          Row 9  → linha=INDUSTRIAL match → score=1, taxa=2.5
          Row 10 → all empty             → score=0, taxa=2.0

        Rate-only mantém apenas maior score → row 9.

        Resultado esperado: 1 resultado, taxa=2.5, score=1.
        """
        ctx = _ctx_full()
        resultados = buscar_regras_item(
            df_regras, ctx, cargo_filtro="Consultor Interno"
        )

        assert len(resultados) == 1
        assert resultados[0]["taxa_rateio_maximo_pct"] == pytest.approx(2.5)
        assert resultados[0]["score"] == 1
        assert resultados[0]["fatia_cargo_pct"] == pytest.approx(50.0)

    def test_busca_resolver_empate_por_colaborador(self):
        """B8: resolver_empate é chamado PER-COLLABORATOR quando o mesmo
        colaborador empata entre regras distintas com mesmo score.

        Entrada: DataFrame inline com 2 regras distintas (score=1 cada) para
        o mesmo colaborador "Carlos" com cargo "GL":
          Regra X: linha=INDUSTRIAL, grupo="" → score=1
          Regra Y: linha="", grupo=EQUIPAMENTOS → score=1

        resolver_empate mock: sempre retorna a primeira regra.

        Resultado esperado: Carlos aparece 1 vez (regra X escolhida pelo mock).
        """
        df_inline = pd.DataFrame({
            "linha": ["INDUSTRIAL", ""],
            "grupo": ["", "EQUIPAMENTOS"],
            "subgrupo": ["", ""],
            "tipo_mercadoria": ["", ""],
            "fabricante": ["", ""],
            "aplicacao": ["", ""],
            "colaborador": ["Carlos Nunes", "Carlos Nunes"],
            "cargo": ["Gerente Linha", "Gerente Linha"],
            "taxa_rateio_maximo_pct": [3.0, 4.0],
            "fatia_cargo_pct": [100, 100],
        })
        df_prep = preprocessar_regras(df_inline)

        # Mock: sempre escolhe a primeira regra_key
        chamadas = []

        def mock_resolver(df_emp, ctx, score):
            chamadas.append({"score": score, "n_regras": df_emp["_regra_key"].nunique()})
            primeiro_key = df_emp["_regra_key"].iloc[0]
            return df_emp[df_emp["_regra_key"] == primeiro_key]

        ctx = {"linha": "INDUSTRIAL", "grupo": "EQUIPAMENTOS",
               "subgrupo": "", "tipo_mercadoria": "",
               "fabricante": "", "aplicacao": ""}

        resultados = buscar_regras_item(
            df_prep, ctx, resolver_empate=mock_resolver
        )

        # resolver_empate deve ter sido chamado para Carlos (empate de score=1)
        assert len(chamadas) == 1, f"resolver_empate deveria ser chamado 1 vez, foi {len(chamadas)}"
        assert chamadas[0]["score"] == 1
        assert chamadas[0]["n_regras"] == 2  # 2 regras distintas empatadas

        # Carlos aparece 1 vez com a regra X (taxa=3.0)
        carlos_results = [r for r in resultados if r["colaborador"] == "Carlos Nunes"]
        assert len(carlos_results) == 1
        assert carlos_results[0]["taxa_rateio_maximo_pct"] == pytest.approx(3.0)


# ======================================================================
# GRUPO C — Funções Auxiliares (8 testes)
# ======================================================================

@pytest.mark.unit
class TestFuncoesAuxiliares:
    """Testa colaborador_tem_atribuicao, obter_linhas_colaborador,
    buscar_taxa_para_cargo, validar_cobertura_hierarquias."""

    def test_colaborador_tem_atribuicao_true(self, df_regras):
        """C1: Colaborador existente retorna True.

        Entrada: "João Silva" — presente em rows 1, 3, 12.
        Resultado esperado: True.
        """
        assert colaborador_tem_atribuicao(df_regras, "João Silva")

    def test_colaborador_tem_atribuicao_false(self, df_regras):
        """C2: Colaborador inexistente retorna False.

        Entrada: "Zé Ninguém" — não existe no fixture.
        Resultado esperado: False.
        """
        assert not colaborador_tem_atribuicao(df_regras, "Zé Ninguém")

    def test_colaborador_tem_atribuicao_por_linha(self, df_regras):
        """C3: Filtro por linha de negócio.

        Entrada: "Felipe Gomes" — presente apenas na linha AMBIENTAL (row 8).

        Resultado esperado:
          - linha="AMBIENTAL" → True
          - linha="INDUSTRIAL" → False
        """
        assert colaborador_tem_atribuicao(df_regras, "Felipe Gomes", linha="AMBIENTAL")
        assert not colaborador_tem_atribuicao(df_regras, "Felipe Gomes", linha="INDUSTRIAL")

    def test_obter_linhas_colaborador(self, df_regras):
        """C4: Retorna todas as linhas de negócio distintas do colaborador.

        Entrada: "João Silva" — rows 1, 3, 12 todas com linha=INDUSTRIAL.

        Resultado esperado: ["INDUSTRIAL"] (única, sem duplicatas).
        """
        linhas = obter_linhas_colaborador(df_regras, "João Silva")
        assert sorted(linhas) == ["INDUSTRIAL"]

    def test_obter_linhas_colaborador_multiplas(self, df_regras):
        """C4b: Colaborador com 2 linhas distintas via fixture in-memory.

        Entrada: DataFrame inline com "Carlos" em INDUSTRIAL e AMBIENTAL.
        Resultado esperado: ["AMBIENTAL", "INDUSTRIAL"] (sorted).
        """
        df_multi = pd.DataFrame({
            "linha": ["INDUSTRIAL", "AMBIENTAL"],
            "grupo": ["", ""],
            "subgrupo": ["", ""],
            "tipo_mercadoria": ["", ""],
            "fabricante": ["", ""],
            "aplicacao": ["", ""],
            "colaborador": ["Carlos", "Carlos"],
            "cargo": ["GL", "GL"],
            "taxa_rateio_maximo_pct": [3.0, 3.0],
            "fatia_cargo_pct": [100, 100],
        })
        df_prep = preprocessar_regras(df_multi)
        linhas = obter_linhas_colaborador(df_prep, "Carlos")
        assert sorted(linhas) == ["AMBIENTAL", "INDUSTRIAL"]

    def test_buscar_taxa_para_cargo(self, df_regras):
        """C5: Busca taxa para cargo "Consultor Interno" em contexto INDUSTRIAL.

        Entrada: Contexto IND+EQUIP+BOMBAS+CENTR+KSB+SANEA, cargo="Consultor Interno".

        Cálculo: Row 9 (rate-only CI com linha=INDUSTRIAL, score=1) vence
        Row 10 (rate-only CI score=0). Resultado vem de buscar_regras_item[0].

        Resultado esperado: taxa=2.5, fatia=50.0, split=1.0.
        """
        ctx = _ctx_full()
        resultado = buscar_taxa_para_cargo(df_regras, ctx, "Consultor Interno")

        assert resultado is not None
        assert resultado["taxa_rateio_maximo_pct"] == pytest.approx(2.5)
        assert resultado["fatia_cargo_pct"] == pytest.approx(50.0)
        assert resultado["fator_split"] == pytest.approx(1.0)

    def test_buscar_taxa_para_cargo_sem_match(self, df_regras):
        """C6: Cargo inexistente retorna None.

        Entrada: cargo="Estagiario" (não existe no fixture).
        Resultado esperado: None.
        """
        ctx = _ctx_full()
        resultado = buscar_taxa_para_cargo(df_regras, ctx, "Estagiario")
        assert resultado is None

    def test_validar_cobertura_ok(self, df_regras):
        """C7: Hierarquia coberta por regra com gestor → sem problemas.

        Entrada:
          - hierarquia: (INDUSTRIAL, EQUIPAMENTOS, BOMBAS, CENTRIFUGAS, KSB, SANEAMENTO)
          - cargos_gestao: ["Gerente Linha", "Coordenador", "Diretor"]

        A busca retorna João(GL), Maria(Coord), Pedro(GL), Ana(GL), Lucia(GL),
        Roberto(Dir) — todos gestores nomeados.

        Resultado esperado: lista vazia (nenhum problema).
        """
        hierarquias = {
            ("INDUSTRIAL", "EQUIPAMENTOS", "BOMBAS", "CENTRIFUGAS", "KSB", "SANEAMENTO"),
        }
        cargos = ["Gerente Linha", "Coordenador", "Diretor"]
        problemas = validar_cobertura_hierarquias(df_regras, hierarquias, cargos)
        assert problemas == []

    def test_validar_cobertura_gap(self, df_regras):
        """C8: Hierarquia sem gestor nomeado → problema detectado.

        Entrada:
          - hierarquia: (QUIMICA, ESPECIAL, "", "", "", "")
          - cargos_gestao: ["Gerente Linha", "Coordenador"]
            (Diretor NÃO está na lista de cargos_gestao para este teste)

        A busca retorna apenas Roberto(Diretor, score=0) e rate-only(CI).
        Nenhum deles é GL ou Coord.

        Resultado esperado: lista com 1 problema.
        """
        hierarquias = {
            ("QUIMICA", "ESPECIAL", "", "", "", ""),
        }
        # Diretor propositalmente NÃO incluído na lista de cargos gestão
        cargos = ["Gerente Linha", "Coordenador"]
        problemas = validar_cobertura_hierarquias(df_regras, hierarquias, cargos)
        assert len(problemas) == 1
        assert problemas[0]["hierarquia"] == ("QUIMICA", "ESPECIAL", "", "", "", "")
