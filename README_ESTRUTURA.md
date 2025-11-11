# Estrutura do Projeto de Cálculo de Comissões

Este documento descreve a organização do projeto após a refatoração.

## Estrutura de Diretórios

```
PROJETO_COMISSOES_V2/
├── config/                    # Arquivos de configuração
│   ├── REGRAS_COMISSOES.xlsx # Arquivo principal de regras
│   ├── PARAMS.csv            # Parâmetros gerais
│   ├── CONFIG_COMISSAO.csv   # Regras de comissão
│   ├── PESOS_METAS.csv       # Pesos das metas por cargo
│   ├── META_RENTABILIDADE.csv # Metas de rentabilidade
│   └── ...                    # Outros arquivos de configuração
│
├── dados_entrada/             # Arquivos de dados de entrada
│   ├── Analise_Comercial_Completa.xlsx
│   ├── Análise Financeira.xlsx
│   └── rentabilidades/        # Arquivos de rentabilidade por mês
│       ├── rentabilidade_07_2025_agrupada.xlsx
│       ├── rentabilidade_08_2025_agrupada.xlsx
│       └── rentabilidade_09_2025_agrupada.xlsx
│
├── dados_saida/               # Arquivos gerados (opcional)
├── dados_processados/         # Dados processados (opcional)
│
├── src/                       # Código fonte refatorado
│   ├── core/                  # Lógica de negócio central
│   │   └── currency_rates.py  # Gerenciamento de taxas de câmbio
│   ├── io/                     # Entrada/saída de dados
│   │   ├── config_loader.py    # Carregamento de configurações
│   │   └── data_loader.py     # Carregamento de dados de entrada
│   └── utils/                  # Utilitários
│       ├── normalization.py   # Normalização de texto
│       ├── styling.py          # Estilização de Excel
│       └── logging.py          # Logging de validação
│
├── tests/                      # Testes de lógica
│   ├── test_utils.py           # Testes de utilitários
│   ├── test_loaders.py         # Testes de loaders
│   ├── test_preparador_dados.py # Testes do preparador
│   ├── test_validar_comissoes_faturamento.py # Validação de comissões
│   └── README.md              # Documentação dos testes
│
├── diagnostics/               # Scripts de diagnóstico
│   ├── diagnostico_rentabilidade.py # Diagnóstico de rentabilidade
│   └── README.md              # Documentação dos diagnósticos
│
├── models/                     # Modelos de dados (mock/placeholder)
│   └── process_state.py        # Gerenciamento de estado
│
├── calculo_comissoes.py       # Script principal (legado, em refatoração)
├── preparar_dados_mensais.py  # Preparador de dados mensais
│
└── *.xlsx, *.csv              # Arquivos gerados na raiz
```

## Scripts Principais

### `calculo_comissoes.py`
Script principal para cálculo de comissões. Executa o fluxo completo:
1. Carrega configurações e dados
2. Valida dados
3. Calcula valores realizados
4. Calcula comissões por faturamento e recebimento
5. Gera arquivos de saída

**Uso:**
```bash
python calculo_comissoes.py
# Ou com mês/ano via CLI
python calculo_comissoes.py --mes 9 --ano 2025
```

### `preparar_dados_mensais.py`
Prepara os arquivos mensais a partir do arquivo completo de análise comercial.

**Uso:**
```bash
python preparar_dados_mensais.py
```

## Testes

Ver `tests/README.md` para detalhes sobre os testes.

## Diagnósticos

Ver `diagnostics/README.md` para detalhes sobre os scripts de diagnóstico.

## Fluxo de Dados

1. **Entrada:**
   - `dados_entrada/Analise_Comercial_Completa.xlsx` → Processado por `preparar_dados_mensais.py`
   - `dados_entrada/Análise Financeira.xlsx` → Carregado diretamente
   - `dados_entrada/rentabilidades/rentabilidade_{MM}_{AAAA}_agrupada.xlsx` → Carregado por `DataLoader`
   - `config/*.csv` → Carregado por `ConfigLoader`

2. **Processamento:**
   - `calculo_comissoes.py` orquestra todo o cálculo
   - Usa módulos em `src/` para carregamento e processamento

3. **Saída:**
   - `Comissoes_Calculadas_{timestamp}.xlsx` → Arquivo principal com todas as abas
   - `Detalhamento_Comissoes_{timestamp}.pdf` → PDF detalhado (opcional)

## Convenções

- **Configurações:** Sempre em `config/`
- **Dados de entrada:** Sempre em `dados_entrada/`
- **Testes:** Sempre em `tests/`
- **Diagnósticos:** Sempre em `diagnostics/`
- **Código fonte:** Sempre em `src/`

