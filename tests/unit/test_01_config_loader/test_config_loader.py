"""
Testes unitários: Carga e Validação de Regras do ConfigLoader.

Módulo testado: src/io/config_loader.py
Lógica de negócio:
  - Carregamento de planilhas de configuração via Excel unificado.
  - Normalização de nomes de colunas e valores string.
  - Parsing do DataFrame PARAMS para dicionário Python.
  - Detecção de colaboradores pagos por recebimento por regras explícitas e heurística.

Referência: DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md, Seção 4
"""

from pathlib import Path

import pandas as pd
import pytest

from src.io.config_loader import ConfigLoader
from tests.conftest import load_fixture_csv


FIXTURES_DIR = Path(__file__).parent / "fixtures"

SHEET_TO_FIXTURE = {
    "PARAMS": "config_params.csv",
    "COLABORADORES": "config_colaboradores.csv",
    "CARGOS": "config_cargos.csv",
    "ATRIBUICOES": "config_atribuicoes.csv",
    "PESOS_METAS": "config_pesos_metas.csv",
    "METAS_APLICACAO": "config_metas_aplicacao.csv",
    "METAS_INDIVIDUAIS": "config_metas_individuais.csv",
    "META_RENTABILIDADE": "config_meta_rentabilidade.csv",
    "CONFIG_COMISSAO": "config_comissao.csv",
    "METAS_FORNECEDORES": "config_metas_fornecedores.csv",
    "ALIASES": "config_aliases.csv",
    "FC_ESCADA_CARGOS": "config_fc_escada_cargos.csv",
    "CROSS_SELLING": "config_cross_selling.csv",
}


def _load_fixture_dataframe(filename: str) -> pd.DataFrame:
    """Carrega um CSV de fixture desta pasta de testes."""
    return load_fixture_csv(__file__, filename)


def _build_workbook_data() -> dict[str, pd.DataFrame]:
    """Monta o dicionário de DataFrames que representa o workbook de configuração."""
    return {
        sheet_name: _load_fixture_dataframe(filename)
        for sheet_name, filename in SHEET_TO_FIXTURE.items()
    }


@pytest.fixture
def workbook_path(tmp_path) -> Path:
    """Cria um arquivo Excel temporário a partir dos CSVs de fixture."""
    workbook = tmp_path / "REGRAS_COMISSOES_TESTE.xlsx"
    with pd.ExcelWriter(workbook) as writer:
        for sheet_name, dataframe in _build_workbook_data().items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return workbook


class TestLoadConfigs:
    """Testes do carregamento principal de configurações."""

    def test_load_configs_carrega_abas_do_excel_e_aplica_normalizacoes(self, workbook_path):
        """Deve carregar todas as abas do Excel temporário e aplicar normalizações básicas."""
        loader = ConfigLoader()

        data = loader.load_configs(str(workbook_path))

        assert set(SHEET_TO_FIXTURE).issubset(data.keys())
        assert data["COLABORADORES"].loc[0, "nome_colaborador"] == "João Silva"
        assert data["COLABORADORES"].loc[0, "cargo"] == "Executivo de Contas"
        assert "fornecedor" in data["METAS_FORNECEDORES"].columns
        assert "fabricante" not in data["METAS_FORNECEDORES"].columns

    def test_load_configs_arquivo_inexistente_raise_file_not_found_error(self, tmp_path):
        """Caminho inexistente deve levantar FileNotFoundError com mensagem descritiva."""
        loader = ConfigLoader()
        missing_path = tmp_path / "arquivo_inexistente.xlsx"

        with pytest.raises(FileNotFoundError, match="Arquivo de configuração obrigatório não encontrado"):
            loader.load_configs(str(missing_path))

    def test_load_configs_falha_na_leitura_raise_runtime_error(self, monkeypatch, tmp_path):
        """Falha do pandas.read_excel deve ser encapsulada como RuntimeError."""
        loader = ConfigLoader()
        fake_path = tmp_path / "config.xlsx"
        fake_path.write_text("placeholder", encoding="utf-8")

        def _raise_read_error(*args, **kwargs):
            raise Exception("erro_simulado_excel")

        monkeypatch.setattr(pd, "read_excel", _raise_read_error)

        with pytest.raises(RuntimeError, match="Falha crítica ao carregar"):
            loader.load_configs(str(fake_path))


class TestNormalizeConfigDataframes:
    """Testes de normalização de nomes de coluna e valores string."""

    def test_normalize_config_dataframes_strip_colunas_e_strings(self):
        """Deve remover espaços nas bordas dos nomes de colunas e dos valores string."""
        loader = ConfigLoader()
        data = {
            "PARAMS": pd.DataFrame(
                {
                    " chave ": [" mes_apuracao ", " cross_selling_default_option "],
                    " valor ": [" 10 ", " b "],
                }
            )
        }

        normalized = loader.normalize_config_dataframes(data)

        assert list(normalized["PARAMS"].columns) == ["chave", "valor"]
        assert normalized["PARAMS"].loc[0, "chave"] == "mes_apuracao"
        assert normalized["PARAMS"].loc[1, "valor"] == "b"

    def test_normalize_config_dataframes_preserva_valores_numericos(self):
        """Valores numéricos não devem ser alterados pela normalização de strings."""
        loader = ConfigLoader()
        data = {
            "CONFIG_COMISSAO": pd.DataFrame(
                {
                    " taxa_rateio_maximo_pct ": [4, 5],
                    " fatia_cargo_pct ": [50.0, 25.0],
                }
            )
        }

        normalized = loader.normalize_config_dataframes(data)

        assert list(normalized["CONFIG_COMISSAO"].columns) == ["taxa_rateio_maximo_pct", "fatia_cargo_pct"]
        assert normalized["CONFIG_COMISSAO"].loc[0, "taxa_rateio_maximo_pct"] == 4
        assert normalized["CONFIG_COMISSAO"].loc[1, "fatia_cargo_pct"] == 25.0


class TestProcessParams:
    """Testes da conversão da aba PARAMS para dicionário Python."""

    def test_process_params_cria_dict_e_aplica_default_cross_selling(self):
        """Quando a opção default não existe, deve inserir 'A'."""
        loader = ConfigLoader()
        params_df = pd.DataFrame(
            {
                "chave": ["mes_apuracao", "ano_apuracao"],
                "valor": [10, 2025],
            }
        )

        params = loader.process_params(params_df)

        assert params["mes_apuracao"] == 10
        assert params["ano_apuracao"] == 2025
        assert params["cross_selling_default_option"] == "A"

    def test_process_params_converte_opcao_existente_para_maiuscula(self):
        """Quando a opção existe em minúsculas, deve ser convertida para upper."""
        loader = ConfigLoader()
        params_df = _load_fixture_dataframe("config_params.csv")

        params = loader.process_params(params_df)

        assert str(params["mes_apuracao"]) == "10"
        assert str(params["ano_apuracao"]) == "2025"
        assert params["cross_selling_default_option"] == "B"


class TestNormalizeSpecialColumns:
    """Testes da normalização de colunas especiais do workbook."""

    def test_normalize_special_columns_renomeia_fabricante_para_fornecedor(self):
        """Se existir 'fabricante' e não existir 'fornecedor', deve renomear."""
        loader = ConfigLoader()
        data = {
            "METAS_FORNECEDORES": _load_fixture_dataframe("config_metas_fornecedores.csv")
        }

        normalized = loader._normalize_special_columns(data)

        assert "fornecedor" in normalized["METAS_FORNECEDORES"].columns
        assert "fabricante" not in normalized["METAS_FORNECEDORES"].columns

    def test_normalize_special_columns_mantem_fornecedor_quando_ja_existe(self):
        """Se a coluna 'fornecedor' já existir, nada deve ser renomeado."""
        loader = ConfigLoader()
        data = {
            "METAS_FORNECEDORES": pd.DataFrame(
                {
                    "linha": ["Linha A"],
                    "fornecedor": ["Fornecedor XPTO"],
                    "meta_anual": [100000],
                    "moeda": ["BRL"],
                }
            )
        }

        normalized = loader._normalize_special_columns(data)

        assert list(normalized["METAS_FORNECEDORES"].columns) == [
            "linha",
            "fornecedor",
            "meta_anual",
            "moeda",
        ]


class TestDetectRecebimentoColaboradores:
    """Testes da identificação de colaboradores pagos por recebimento."""

    def test_detecta_via_cargo_com_tipo_comissao_recebimento(self):
        """Deve identificar colaboradores cujo cargo foi marcado como recebimento em CARGOS."""
        loader = ConfigLoader()
        data = {
            "CARGOS": _load_fixture_dataframe("config_cargos.csv"),
            "COLABORADORES": _load_fixture_dataframe("config_colaboradores.csv"),
        }

        recebimento = loader.detect_recebimento_colaboradores(data)

        assert recebimento == {"Maria Receb"}

    def test_detecta_via_tipo_comissao_no_colaborador(self):
        """Deve identificar diretamente pela coluna TIPO_COMISSAO em COLABORADORES."""
        loader = ConfigLoader()
        data = {
            "COLABORADORES": pd.DataFrame(
                {
                    "nome_colaborador": ["Joana Receb", "Pedro Fat"],
                    "cargo": ["Executivo", "Coordenador"],
                    "TIPO_COMISSAO": ["RECEBIMENTO", "faturamento"],
                }
            )
        }

        recebimento = loader.detect_recebimento_colaboradores(data)

        assert recebimento == {"Joana Receb"}

    def test_detecta_uniao_entre_cargo_e_colaborador_sem_duplicatas(self):
        """As duas fontes explícitas devem ser cumulativas, formando união sem duplicatas."""
        loader = ConfigLoader()
        data = {
            "CARGOS": pd.DataFrame(
                {
                    "nome_cargo": ["Cargo Recebimento"],
                    "TIPO_COMISSAO": ["recebimento"],
                }
            ),
            "COLABORADORES": pd.DataFrame(
                {
                    "nome_colaborador": ["Maria", "Joana"],
                    "cargo": ["Cargo Recebimento", "Executivo"],
                    "TIPO_COMISSAO": ["faturamento", "recebimento"],
                }
            ),
        }

        recebimento = loader.detect_recebimento_colaboradores(data)

        assert recebimento == {"Maria", "Joana"}

    def test_detecta_por_heuristica_quando_nao_ha_regras_explicitas(self):
        """Se nenhum mecanismo explícito detectar, deve usar cargo contendo 'receb'."""
        loader = ConfigLoader()
        data = {
            "CARGOS": pd.DataFrame(
                {
                    "nome_cargo": ["Especialista Recebimento", "Executivo Comercial"],
                }
            ),
            "COLABORADORES": pd.DataFrame(
                {
                    "nome_colaborador": ["Carlos Cargo", "Ana Comercial"],
                    "cargo": ["Especialista Recebimento", "Executivo Comercial"],
                }
            ),
        }

        recebimento = loader.detect_recebimento_colaboradores(data)

        assert recebimento == {"Carlos Cargo"}

    def test_nao_aplica_heuristica_se_set_ja_foi_preenchido(self):
        """A heurística só entra como fallback quando o set ainda está vazio."""
        loader = ConfigLoader()
        data = {
            "CARGOS": pd.DataFrame(
                {
                    "nome_cargo": ["Analista de Recebimento", "Especialista Recebimento"],
                    "TIPO_COMISSAO": ["recebimento", None],
                }
            ),
            "COLABORADORES": pd.DataFrame(
                {
                    "nome_colaborador": ["Maria Receb", "Carlos Heuristico"],
                    "cargo": ["Analista de Recebimento", "Especialista Recebimento"],
                }
            ),
        }

        recebimento = loader.detect_recebimento_colaboradores(data)

        assert recebimento == {"Maria Receb"}

    def test_sem_abas_relevantes_retorna_set_vazio(self):
        """Ausência de CARGOS e COLABORADORES deve retornar set vazio sem erro."""
        loader = ConfigLoader()

        recebimento = loader.detect_recebimento_colaboradores({})

        assert recebimento == set()