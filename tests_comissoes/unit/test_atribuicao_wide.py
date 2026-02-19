"""
Testes unitários para funções de atribuição Wide.

Testa:
- _extrair_colaboradores_wide: parsing de cargos, fator_split, filtros
- _buscar_atribuicao_wide: fallback hierárquico específico → genérico
- _colaborador_tem_atribuicao_wide: verificação de existência
- _obter_linhas_colaborador_wide: mapeamento colaborador → linhas

Todas as funções são standalone (não dependem da classe CalculoComissao).
"""

import pytest
import pandas as pd
import numpy as np

from calculo_comissoes import (
    _extrair_colaboradores_wide,
    _buscar_atribuicao_wide,
    _colaborador_tem_atribuicao_wide,
    _obter_linhas_colaborador_wide,
)
from tests_comissoes.fixtures.config_factory import ConfigFactory


# =========================================================================
# HELPERS
# =========================================================================

def _criar_row_wide(**kwargs) -> pd.Series:
    """Cria uma pd.Series simulando uma linha Wide de ATRIBUICOES."""
    base = {
        "linha": "Hidrologia",
        "grupo": "Sonda Serie EXO",
        "subgrupo": "EXO",
        "tipo_mercadoria": "Produto",
        "Gerente Linha 1": None,
        "Gerente Linha 2": None,
        "Coordenador 1": None,
        "Coordenador 2": None,
        "Diretor": None,
        "Consultor Interno": None,
        "Consultor Externo": None,
    }
    base.update(kwargs)
    return pd.Series(base)


# =========================================================================
# TESTES: _extrair_colaboradores_wide
# =========================================================================
class TestExtrairColaboradoresWide:
    """Testes de parsing da linha Wide para lista de colaboradores."""

    def test_gerente_unico(self, audit):
        """Apenas Gerente Linha 1 preenchido → fator_split = 1.0."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Gerente único")
        row = _criar_row_wide(**{"Gerente Linha 1": "Andrey Andrade"})
        result = _extrair_colaboradores_wide(row)

        gerentes = [c for c in result if c["cargo"] == "Gerente Linha"]
        audit.verificar(
            descricao="1 gerente → fator_split=1.0",
            formula="se GL2 is None → fator_split = 1.0",
            entradas={"GL1": "Andrey Andrade", "GL2": None},
            esperado=1.0,
            real=gerentes[0]["fator_split"],
            tolerancia=0.0,
        )
        assert len(gerentes) == 1
        assert gerentes[0]["colaborador"] == "Andrey Andrade"

    def test_dois_gerentes_split_automatico(self, audit):
        """Dois Gerentes Linha sem coluna de split → 0.5/0.5."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Dois gerentes auto-split")
        row = _criar_row_wide(
            **{"Gerente Linha 1": "Andrey Andrade", "Gerente Linha 2": "Dener Martins"}
        )
        result = _extrair_colaboradores_wide(row)

        gerentes = [c for c in result if c["cargo"] == "Gerente Linha"]
        assert len(gerentes) == 2

        for g in gerentes:
            audit.verificar(
                descricao=f"Split automático 50/50 para {g['colaborador']}",
                formula="GL1 e GL2 preenchidos, sem fator_split_gerente → 0.5",
                entradas={"GL1": "Andrey Andrade", "GL2": "Dener Martins"},
                esperado=0.5,
                real=g["fator_split"],
                tolerancia=0.0,
            )

    def test_dois_gerentes_split_customizado(self, audit):
        """Dois Gerentes Linha com fator_split_gerente explícito."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Gerentes split customizado")
        row = _criar_row_wide(
            **{
                "Gerente Linha 1": "Andrey Andrade",
                "Gerente Linha 2": "Dener Martins",
                "fator_split_gerente": "0.7",
            }
        )
        result = _extrair_colaboradores_wide(row)

        gerentes = [c for c in result if c["cargo"] == "Gerente Linha"]
        assert len(gerentes) == 2

        # Ambos usam o mesmo fator_split_gerente
        for g in gerentes:
            audit.verificar(
                descricao=f"Split customizado 70% para {g['colaborador']}",
                formula="fator_split_gerente=0.7 da coluna explícita",
                entradas={"fator_split_gerente": 0.7},
                esperado=0.7,
                real=g["fator_split"],
                tolerancia=0.001,
            )

    def test_coordenador_unico(self, audit):
        """Apenas Coordenador 1 → fator_split = 1.0."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Coordenador único")
        row = _criar_row_wide(**{"Coordenador 1": "Rosana Martins"})
        result = _extrair_colaboradores_wide(row)

        coords = [c for c in result if c["cargo"] == "Coordenador"]
        assert len(coords) == 1
        audit.verificar(
            descricao="1 coordenador → fator_split=1.0",
            formula="se C2 is None → fator_split = 1.0",
            entradas={"C1": "Rosana Martins", "C2": None},
            esperado=1.0,
            real=coords[0]["fator_split"],
            tolerancia=0.0,
        )

    def test_dois_coordenadores_split(self, audit):
        """Dois Coordenadores sem coluna de split → 0.5/0.5."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Dois coordenadores auto-split")
        row = _criar_row_wide(
            **{"Coordenador 1": "Rosana Martins", "Coordenador 2": "Juliano Pereira"}
        )
        result = _extrair_colaboradores_wide(row)

        coords = [c for c in result if c["cargo"] == "Coordenador"]
        assert len(coords) == 2

        for c in coords:
            audit.verificar(
                descricao=f"Split automático 50/50 para {c['colaborador']}",
                formula="C1 e C2 preenchidos → 0.5",
                entradas={"C1": "Rosana Martins", "C2": "Juliano Pereira"},
                esperado=0.5,
                real=c["fator_split"],
                tolerancia=0.0,
            )

    def test_outros_cargos_sem_split(self, audit):
        """Diretor e Consultor Interno → fator_split sempre 1.0."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Cargos sem split")
        row = _criar_row_wide(
            **{"Diretor": "Carlos Diretor", "Consultor Interno": "Samanta Silva"}
        )
        result = _extrair_colaboradores_wide(row)

        for c in result:
            audit.verificar(
                descricao=f"{c['cargo']} ({c['colaborador']}) → fator_split=1.0",
                formula="Cargos fora de Gerente Linha/Coordenador → fator_split=1.0",
                entradas={"cargo": c["cargo"]},
                esperado=1.0,
                real=c["fator_split"],
                tolerancia=0.0,
            )

    def test_filtro_cargo(self, audit):
        """Filtro por cargo retorna apenas os colaboradores daquele cargo."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Filtro por cargo")
        row = _criar_row_wide(
            **{
                "Gerente Linha 1": "Andrey Andrade",
                "Coordenador 1": "Rosana Martins",
                "Diretor": "Carlos Diretor",
            }
        )
        result = _extrair_colaboradores_wide(row, cargo_filtro="Coordenador")

        audit.verificar(
            descricao="Filtro cargo=Coordenador retorna apenas coordenadores",
            formula="cargo_filtro='Coordenador' → exclui Gerente e Diretor",
            entradas={"cargo_filtro": "Coordenador"},
            esperado=1,
            real=len(result),
            tolerancia=0,
        )
        assert result[0]["cargo"] == "Coordenador"
        assert result[0]["colaborador"] == "Rosana Martins"

    def test_valores_vazios_ignorados(self, audit):
        """Colunas com NaN, 'Nenhum', '' são ignoradas."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Valores vazios")
        row = _criar_row_wide(
            **{
                "Gerente Linha 1": "Andrey Andrade",
                "Gerente Linha 2": "Nenhum",
                "Coordenador 1": np.nan,
                "Coordenador 2": "",
                "Diretor": "nan",
            }
        )
        result = _extrair_colaboradores_wide(row)

        # Apenas Andrey deve aparecer
        nomes = [c["colaborador"] for c in result]
        audit.verificar(
            descricao="Valores nulos/vazios/Nenhum/nan são ignorados",
            formula="get_val retorna None para NaN, 'Nenhum', '', 'nan'",
            entradas={"GL2": "Nenhum", "C1": "NaN", "C2": "", "Dir": "nan"},
            esperado=1,
            real=len(nomes),
            tolerancia=0,
        )
        assert "Andrey Andrade" in nomes

    def test_fallback_coluna_unica_gerente(self, audit):
        """Se 'Gerente Linha 1/2' não existem, usa 'Gerente Linha'."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Fallback coluna única")
        data = {
            "linha": "Hidrologia",
            "grupo": "Sonda Serie EXO",
            "subgrupo": "EXO",
            "tipo_mercadoria": "Produto",
            "Gerente Linha": "Andrey Andrade",  # Coluna única
            "Coordenador": "Rosana Martins",     # Coluna única
        }
        row = pd.Series(data)
        result = _extrair_colaboradores_wide(row)

        gerentes = [c for c in result if c["cargo"] == "Gerente Linha"]
        coords = [c for c in result if c["cargo"] == "Coordenador"]

        audit.verificar(
            descricao="Fallback para 'Gerente Linha' (coluna única)",
            formula="GL1 e GL2 None → usa 'Gerente Linha'",
            entradas={"Gerente Linha": "Andrey Andrade"},
            esperado=1,
            real=len(gerentes),
            tolerancia=0,
        )
        assert gerentes[0]["colaborador"] == "Andrey Andrade"
        assert len(coords) == 1

    def test_multiplos_nomes_ponto_virgula(self, audit):
        """Nomes separados por ponto e vírgula em um cargo genérico."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Múltiplos nomes com ;")
        row = _criar_row_wide(
            **{"Consultor Interno": "Samanta Silva; Rafaela Meirelles"}
        )
        result = _extrair_colaboradores_wide(row)

        consultores = [c for c in result if c["cargo"] == "Consultor Interno"]
        audit.verificar(
            descricao="Ponto e vírgula separa múltiplos nomes",
            formula="split(';') → 2 entradas, fator_split=1.0 cada",
            entradas={"valor": "Samanta Silva; Rafaela Meirelles"},
            esperado=2,
            real=len(consultores),
            tolerancia=0,
        )
        nomes = {c["colaborador"] for c in consultores}
        assert "Samanta Silva" in nomes
        assert "Rafaela Meirelles" in nomes

    def test_row_vazia_retorna_lista_vazia(self, audit):
        """Linha sem nenhum colaborador → lista vazia."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Row totalmente vazia")
        row = _criar_row_wide()
        result = _extrair_colaboradores_wide(row)

        audit.verificar(
            descricao="Nenhum colaborador preenchido → lista vazia",
            formula="todos os campos de cargo são None → []",
            entradas={},
            esperado=0,
            real=len(result),
            tolerancia=0,
        )


# =========================================================================
# TESTES: _buscar_atribuicao_wide
# =========================================================================
class TestBuscarAtribuicaoWide:
    """Testes do fallback hierárquico de busca de atribuição."""

    @staticmethod
    def _df_atribuicoes_com_fallback():
        """Cria DataFrame com atribuição específica e genérica para Hidrologia."""
        rows = [
            {
                "linha": "Hidrologia",
                "grupo": "Sonda Serie EXO",
                "subgrupo": "EXO",
                "tipo_mercadoria": "Produto",
                "Gerente Linha 1": "Andrey Andrade",
                "Coordenador 1": "Rosana Martins",
                "Diretor": "Carlos Diretor",
            },
            {
                "linha": "Hidrologia",
                "grupo": "[Todos os grupos]",
                "subgrupo": "",
                "tipo_mercadoria": "",
                "Gerente Linha 1": "Andrey Andrade",
                "Gerente Linha 2": "Dener Martins",
                "Coordenador 1": "Rosana Martins",
                "Diretor": "Carlos Diretor",
            },
            {
                "linha": "SSO",
                "grupo": "[Todos os grupos]",
                "subgrupo": "",
                "tipo_mercadoria": "",
                "Gerente Linha 1": "Dener Martins",
                "Coordenador 1": "Rosana Martins",
                "Diretor": "Carlos Diretor",
            },
        ]
        return pd.DataFrame(rows)

    def test_match_especifico(self, audit):
        """Busca com match exato (linha+grupo+subgrupo+tipo) encontra a específica."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Match específico")
        df = self._df_atribuicoes_com_fallback()
        row = _buscar_atribuicao_wide(df, "Hidrologia", "Sonda Serie EXO", "EXO", "Produto")

        assert row is not None
        audit.verificar(
            descricao="Match exato retorna atribuição específica",
            formula="filtro: linha=Hidro, grupo=EXO, subgrupo=EXO, tipo=Produto",
            entradas={"linha": "Hidrologia", "grupo": "Sonda Serie EXO"},
            esperado="Sonda Serie EXO",
            real=str(row["grupo"]).strip(),
            tolerancia=0,
        )

    def test_fallback_para_generico(self, audit):
        """Busca sem match específico cai para [Todos os grupos]."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Fallback genérico")
        df = self._df_atribuicoes_com_fallback()
        # Buscar grupo que NÃO existe na específica
        row = _buscar_atribuicao_wide(df, "Hidrologia", "Medidor de Vazão Fixo", "IQ Standard", "Produto")

        assert row is not None
        audit.verificar(
            descricao="Sem match específico → fallback para [Todos os grupos]",
            formula="busca falha → tenta grupo contendo '[Todos'",
            entradas={"grupo_buscado": "Medidor de Vazão Fixo"},
            esperado="[Todos os grupos]",
            real=str(row["grupo"]).strip(),
            tolerancia=0,
        )

    def test_nenhum_match(self, audit):
        """Linha inexistente → retorna None."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Nenhum match")
        df = self._df_atribuicoes_com_fallback()
        row = _buscar_atribuicao_wide(df, "Locação", "Grupo Inexistente", "Sub", "Tipo")

        audit.verificar(
            descricao="Linha inexistente → retorna None",
            formula="nenhum filtro correspondeu",
            entradas={"linha": "Locação"},
            esperado="None",
            real=str(row),
            tolerancia=0,
        )

    def test_df_vazio(self, audit):
        """DataFrame vazio → retorna None."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="DataFrame vazio")
        df = pd.DataFrame()
        row = _buscar_atribuicao_wide(df, "Hidrologia", "Sonda", "EXO", "Produto")

        audit.verificar(
            descricao="DataFrame vazio → None",
            formula="df.empty → return None",
            entradas={},
            esperado="None",
            real=str(row),
            tolerancia=0,
        )

    def test_especifica_vazia_fallback_generica_com_gestao(self, audit):
        """Específica sem gestão → fallback para genérica que tem gestão."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Específica vazia → genérica")
        rows = [
            {
                "linha": "Hidrologia",
                "grupo": "Sonda Serie EXO",
                "subgrupo": "EXO",
                "tipo_mercadoria": "Produto",
                # Sem nenhum cargo de gestão
                "Gerente Linha 1": None,
                "Coordenador 1": None,
                "Diretor": None,
            },
            {
                "linha": "Hidrologia",
                "grupo": "[Todos os grupos]",
                "subgrupo": "",
                "tipo_mercadoria": "",
                "Gerente Linha 1": "Andrey Andrade",
                "Coordenador 1": "Rosana Martins",
                "Diretor": "Carlos Diretor",
            },
        ]
        df = pd.DataFrame(rows)
        row = _buscar_atribuicao_wide(df, "Hidrologia", "Sonda Serie EXO", "EXO", "Produto")

        # Deve retornar a genérica pois a específica não tem gestão
        audit.verificar(
            descricao="Específica sem gestão → usa genérica com gestão",
            formula="_has_any_gestao(especifica)=False → tenta genérica",
            entradas={"GL1_espec": None, "GL1_gen": "Andrey Andrade"},
            esperado="[Todos os grupos]",
            real=str(row["grupo"]).strip(),
            tolerancia=0,
        )

    def test_case_insensitive_linha(self, audit):
        """Busca de linha é case-insensitive (HIDROLOGIA == Hidrologia)."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Case insensitive")
        df = self._df_atribuicoes_com_fallback()
        row = _buscar_atribuicao_wide(df, "HIDROLOGIA", "Sonda Serie EXO", "EXO", "Produto")

        assert row is not None
        audit.verificar(
            descricao="Busca case-insensitive na linha",
            formula="str.upper() == str.upper()",
            entradas={"busca": "HIDROLOGIA", "df": "Hidrologia"},
            esperado="Sonda Serie EXO",
            real=str(row["grupo"]).strip(),
            tolerancia=0,
        )


# =========================================================================
# TESTES: _colaborador_tem_atribuicao_wide
# =========================================================================
class TestColaboradorTemAtribuicaoWide:
    """Testes da verificação de existência de colaborador em atribuições."""

    def test_colaborador_existente(self, audit):
        """Colaborador que existe nas atribuições → True."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Colaborador existente")
        df = ConfigFactory.criar_atribuicoes_wide()
        result = _colaborador_tem_atribuicao_wide(df, "Andrey Andrade")

        audit.verificar(
            descricao="Andrey Andrade existe em Hidrologia → True",
            formula="busca nome em todas as linhas Wide",
            entradas={"nome": "Andrey Andrade"},
            esperado=True,
            real=result,
            tolerancia=0,
        )

    def test_colaborador_inexistente(self, audit):
        """Colaborador que NÃO existe → False."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Colaborador inexistente")
        df = ConfigFactory.criar_atribuicoes_wide()
        result = _colaborador_tem_atribuicao_wide(df, "João Ninguém")

        audit.verificar(
            descricao="João Ninguém não está em nenhuma atribuição → False",
            formula="nenhum match em nenhuma row Wide",
            entradas={"nome": "João Ninguém"},
            esperado=False,
            real=result,
            tolerancia=0,
        )

    def test_filtro_por_linha(self, audit):
        """Colaborador existe em Hidrologia mas não em SSO."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Filtro por linha")
        df = ConfigFactory.criar_atribuicoes_wide()

        # Andrey é GL de Hidrologia, NÃO de SSO
        result_hidro = _colaborador_tem_atribuicao_wide(df, "Andrey Andrade", "Hidrologia")
        result_sso = _colaborador_tem_atribuicao_wide(df, "Andrey Andrade", "SSO")

        audit.verificar(
            descricao="Andrey em Hidrologia → True",
            formula="filtro por linha + busca nome",
            entradas={"nome": "Andrey Andrade", "linha": "Hidrologia"},
            esperado=True,
            real=result_hidro,
            tolerancia=0,
        )
        audit.verificar(
            descricao="Andrey em SSO → False",
            formula="filtro por linha + busca nome",
            entradas={"nome": "Andrey Andrade", "linha": "SSO"},
            esperado=False,
            real=result_sso,
            tolerancia=0,
        )

    def test_df_vazio(self, audit):
        """DataFrame vazio → False para qualquer nome."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="DF vazio")
        result = _colaborador_tem_atribuicao_wide(pd.DataFrame(), "Andrey Andrade")

        audit.verificar(
            descricao="DataFrame vazio → sempre False",
            formula="df.empty → return False",
            entradas={},
            esperado=False,
            real=result,
            tolerancia=0,
        )

    def test_case_insensitive(self, audit):
        """Busca de nome é case-insensitive."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Case insensitive nome")
        df = ConfigFactory.criar_atribuicoes_wide()
        result = _colaborador_tem_atribuicao_wide(df, "andrey andrade")

        audit.verificar(
            descricao="Busca case-insensitive para nome",
            formula="str.lower() == str.lower()",
            entradas={"busca": "andrey andrade", "real": "Andrey Andrade"},
            esperado=True,
            real=result,
            tolerancia=0,
        )


# =========================================================================
# TESTES: _obter_linhas_colaborador_wide
# =========================================================================
class TestObterLinhasColaboradorWide:
    """Testes do mapeamento colaborador → linhas de negócio."""

    def test_colaborador_uma_linha(self, audit):
        """Colaborador atribuído a uma única linha."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Uma linha")
        df = ConfigFactory.criar_atribuicoes_wide()
        linhas = _obter_linhas_colaborador_wide(df, "Andrey Andrade")

        audit.verificar(
            descricao="Andrey só está em Hidrologia",
            formula="busca todas as rows Wide → linhas distintas",
            entradas={"nome": "Andrey Andrade"},
            esperado=1,
            real=len(linhas),
            tolerancia=0,
        )
        assert "Hidrologia" in linhas

    def test_colaborador_multiplas_linhas(self, audit):
        """Rosana Martins é Coordenadora em Hidrologia e SSO."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Múltiplas linhas")
        df = ConfigFactory.criar_atribuicoes_wide()
        linhas = _obter_linhas_colaborador_wide(df, "Rosana Martins")

        audit.verificar(
            descricao="Rosana está em Hidrologia e SSO",
            formula="Coordenador 1 em ambas as rows",
            entradas={"nome": "Rosana Martins"},
            esperado=2,
            real=len(linhas),
            tolerancia=0,
        )
        assert "Hidrologia" in linhas
        assert "SSO" in linhas

    def test_colaborador_inexistente(self, audit):
        """Colaborador não atribuído → lista vazia."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="Inexistente → vazio")
        df = ConfigFactory.criar_atribuicoes_wide()
        linhas = _obter_linhas_colaborador_wide(df, "João Ninguém")

        audit.verificar(
            descricao="Colaborador inexistente → lista vazia",
            formula="nenhum match → []",
            entradas={"nome": "João Ninguém"},
            esperado=0,
            real=len(linhas),
            tolerancia=0,
        )

    def test_df_vazio(self, audit):
        """DataFrame vazio → lista vazia."""
        audit.set_contexto(modulo="Atribuição Wide", cenario="DF vazio")
        linhas = _obter_linhas_colaborador_wide(pd.DataFrame(), "Andrey Andrade")

        audit.verificar(
            descricao="DataFrame vazio → []",
            formula="df.empty → return []",
            entradas={},
            esperado=0,
            real=len(linhas),
            tolerancia=0,
        )
