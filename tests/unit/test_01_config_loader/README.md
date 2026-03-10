# test_01_config_loader — Carga e Validação de Regras

## Objetivo

Validar que o `ConfigLoader` carrega corretamente todas as abas do `REGRAS_COMISSOES.xlsx`, faz parsing dos parâmetros, normaliza strings e detecta colaboradores pagos por recebimento.

## Módulos Testados

- `src/io/config_loader.py` → `ConfigLoader`

## Referência de Negócio

- `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md`, **Seção 4** — Motor de Regras de Negócio

## Estratégia de Implementação

- Os testes usam **CSVs de fixture** para espelhar as abas reais do `REGRAS_COMISSOES.xlsx`
- Para validar `load_configs()`, os CSVs são convertidos em um **Excel temporário** durante o teste
- Erros de leitura são validados com monkeypatch em `pandas.read_excel`
- As regras de detecção de recebimento são testadas separadamente por:
	1. Cargo marcado como recebimento
	2. Colaborador marcado como recebimento
	3. União das duas fontes
	4. Heurística por nome do cargo contendo `receb`

## Testes Planejados

| ID | Teste | O que valida | Resultado Esperado |
|----|-------|-------------|-------------------|
| 01.1 | `test_load_configs_carrega_abas_do_excel_e_aplica_normalizacoes` | Lê workbook temporário com 13 abas e aplica strip + renomeação especial | Dict com abas esperadas, `João Silva` sem espaços e `fornecedor` em `METAS_FORNECEDORES` |
| 01.2 | `test_load_configs_arquivo_inexistente_raise_file_not_found_error` | Valida erro de arquivo ausente | `FileNotFoundError` com mensagem descritiva |
| 01.3 | `test_load_configs_falha_na_leitura_raise_runtime_error` | Valida encapsulamento de falha do `read_excel` | `RuntimeError` com contexto |
| 01.4 | `test_normalize_config_dataframes_strip_colunas_e_strings` | Remove espaços de colunas e strings | `" chave " → "chave"`, `" 10 " → "10"` |
| 01.5 | `test_normalize_config_dataframes_preserva_valores_numericos` | Números não sofrem alteração indevida | `4`, `25.0` preservados |
| 01.6 | `test_process_params_cria_dict_e_aplica_default_cross_selling` | Default `A` quando opção não existe | `params["cross_selling_default_option"] == "A"` |
| 01.7 | `test_process_params_converte_opcao_existente_para_maiuscula` | `b` deve virar `B` | `params["cross_selling_default_option"] == "B"` |
| 01.8 | `test_normalize_special_columns_renomeia_fabricante_para_fornecedor` | Renomeia coluna especial | `fabricante` removida, `fornecedor` criada |
| 01.9 | `test_normalize_special_columns_mantem_fornecedor_quando_ja_existe` | Não renomeia quando já está correto | Colunas preservadas |
| 01.10 | `test_detecta_via_cargo_com_tipo_comissao_recebimento` | Detecta recebimento pela aba CARGOS | `{"Maria Receb"}` |
| 01.11 | `test_detecta_via_tipo_comissao_no_colaborador` | Detecta recebimento pela aba COLABORADORES | `{"Joana Receb"}` |
| 01.12 | `test_detecta_uniao_entre_cargo_e_colaborador_sem_duplicatas` | Une as duas fontes explícitas | `{"Maria", "Joana"}` |
| 01.13 | `test_detecta_por_heuristica_quando_nao_ha_regras_explicitas` | Fallback por nome do cargo contendo `receb` | `{"Carlos Cargo"}` |
| 01.14 | `test_nao_aplica_heuristica_se_set_ja_foi_preenchido` | Heurística não roda se set já foi preenchido | `{"Maria Receb"}` |
| 01.15 | `test_sem_abas_relevantes_retorna_set_vazio` | Robustez com entrada mínima | `set()` |

## Fixtures Necessários (subpasta `fixtures/`)

- `config_params.csv` — Espelho da aba PARAMS (3-5 pares chave/valor)
- `config_colaboradores.csv` — Espelho da aba COLABORADORES (3-5 colaboradores)
- `config_cargos.csv` — Espelho da aba CARGOS (3-4 cargos com TIPO_COMISSAO)
- `config_atribuicoes.csv` — Espelho mínimo da aba ATRIBUICOES
- `config_pesos_metas.csv` — Espelho mínimo da aba PESOS_METAS
- `config_metas_aplicacao.csv` — Espelho mínimo da aba METAS_APLICACAO
- `config_metas_individuais.csv` — Espelho mínimo da aba METAS_INDIVIDUAIS
- `config_meta_rentabilidade.csv` — Espelho mínimo da aba META_RENTABILIDADE
- `config_comissao.csv` — Espelho mínimo da aba CONFIG_COMISSAO
- `config_metas_fornecedores.csv` — Espelho da aba METAS_FORNECEDORES (2 linhas com coluna `fabricante`)
- `config_aliases.csv` — Espelho mínimo da aba ALIASES
- `config_fc_escada_cargos.csv` — Espelho mínimo da aba FC_ESCADA_CARGOS
- `config_cross_selling.csv` — Espelho mínimo da aba CROSS_SELLING

## Cálculos Manuais

Estes testes são de **carga/transformação**, não de cálculo numérico. Os resultados esperados são verificações estruturais (tipos, chaves existentes, valores transformados).

### Resultados esperados principais

- `load_configs()` deve retornar um `dict` contendo as 13 abas fornecidas no workbook temporário
- `" João Silva "` deve ser normalizado para `"João Silva"`
- `cross_selling_default_option = "b"` deve virar `"B"` em `process_params()`
- `fabricante` deve ser renomeada para `fornecedor` apenas quando `fornecedor` ainda não existir
- A detecção de recebimento deve obedecer a cascata:
	1. cargo explícito
	2. colaborador explícito
	3. heurística apenas como fallback

---

> **Status:** ✅ Implementado — Fixtures CSV e suíte unitária criadas em 09/Mar/2026
