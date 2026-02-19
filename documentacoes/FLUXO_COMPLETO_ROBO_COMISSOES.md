# Fluxo Completo do Robô de Comissões — Documentação Técnica

> **Escopo:** Metodologia principal (`calculo_comissoes.py` + módulos `src/`).  
> A Metodologia V2 (`src/metodo_v2/`) **não** é coberta por este documento.  
> Última revisão baseada na leitura direta do código-fonte em fevereiro de 2026.

---

## Índice

1. [Visão Geral e Arquitetura](#1-visão-geral-e-arquitetura)  
2. [Fontes de Dados de Entrada](#2-fontes-de-dados-de-entrada)  
3. [Arquivo de Configuração — `REGRAS_COMISSOES.xlsx`](#3-arquivo-de-configuração--regras_comissoesxlsx)  
4. [Inicialização e Preparação dos Dados](#4-inicialização-e-preparação-dos-dados)  
5. [Hierarquia de Atribuições (Formato Wide)](#5-hierarquia-de-atribuições-formato-wide)  
6. [Cálculo de Realizado](#6-cálculo-de-realizado)  
7. [Busca de Regra de Comissão (`_get_regra_comissao`)](#7-busca-de-regra-de-comissão-_get_regra_comissao)  
8. [Fator de Correção — FC (`_calcular_fc_para_item`)](#8-fator-de-correção--fc-_calcular_fc_para_item)  
9. [Regra de Escada do FC (`fc_escada.py`)](#9-regra-de-escada-do-fc-fc_escadapy)  
10. [Comissões por Faturamento (`_calcular_comissoes`)](#10-comissões-por-faturamento-_calcular_comissoes)  
11. [Cross-Selling — Detecção e Decisões](#11-cross-selling--detecção-e-decisões)  
12. [Comissões por Recebimento — Arquitetura Geral](#12-comissões-por-recebimento--arquitetura-geral)  
13. [TCMP — Taxa de Comissão Média Ponderada](#13-tcmp--taxa-de-comissão-média-ponderada)  
14. [FCMP — Fator de Correção Médio Ponderado](#14-fcmp--fator-de-correção-médio-ponderado)  
15. [Adiantamentos (Pagamentos COT)](#15-adiantamentos-pagamentos-cot)  
16. [Pagamentos Regulares](#16-pagamentos-regulares)  
17. [Reconciliação](#17-reconciliação)  
18. [Devoluções — Estorno Proporcional](#18-devoluções--estorno-proporcional)  
19. [Banco de Dados Master (`MasterDBManager`)](#19-banco-de-dados-master-masterdbmanager)  
20. [Geração de Arquivos de Saída](#20-geração-de-arquivos-de-saída)  
21. [Taxas de Câmbio e Metas de Fornecedores](#21-taxas-de-câmbio-e-metas-de-fornecedores)  
22. [Retenção de Clientes (Gerente Linha)](#22-retenção-de-clientes-gerente-linha)  
23. [Aliases de Colaboradores](#23-aliases-de-colaboradores)  
24. [Fluxo de Execução Completo (Passo a Passo)](#24-fluxo-de-execução-completo-passo-a-passo)  
25. [Glossário de Fórmulas](#25-glossário-de-fórmulas)

---

## 1. Visão Geral e Arquitetura

O robô de comissões é um **monólito modular em Python** cujo ponto de entrada principal é `calculo_comissoes.py`. A classe central é `CalculoComissao`, que orquestra todas as etapas do ciclo de apuração.

### Mapa de Arquivos Fundamentais

| Arquivo / Módulo | Responsabilidade |
|---|---|
| `calculo_comissoes.py` | Orquestrador principal; contém `CalculoComissao` |
| `preparar_dados_mensais.py` | Filtra e agrupa dados do ERP para o mês/ano |
| `src/io/config_loader.py` | Lê e normaliza `REGRAS_COMISSOES.xlsx` |
| `src/io/data_loader.py` | Lê arquivos de entrada (`Faturados.xlsx`, etc.) |
| `src/io/master_db_manager.py` | Gerencia o banco de dados histórico de comissões |
| `src/core/fc_escada.py` | Aplica regra de rampa ou escada ao FC/FCMP |
| `src/recebimento/recebimento_orchestrator.py` | Orquestra comissões por recebimento |
| `src/recebimento/core/metricas_calculator.py` | Calcula TCMP e FCMP por processo |
| `src/recebimento/core/comissao_calculator.py` | Aplica fórmulas de comissão (adiantamento / regular) |
| `src/recebimento/reconciliacao/` | Detecta, calcula, agrega e valida reconciliações |
| `src/devolucao/devolucao_processor.py` | Orquestra estorno por devolução |
| `src/devolucao/devolucao_calculator.py` | Calcula saldo negativo proporcional |
| `src/currency/` | Busca, armazena e converte taxas de câmbio |
| `src/utils/normalization.py` | `normalize_text`, `calcular_atingimento` |
| `models/process_state.py` | Define estrutura do estado de processos de recebimento |

### Diagrama de Fluxo de Alto Nível

```
[REGRAS_COMISSOES.xlsx]  [dados_entrada/]  [Estado_Processos_Recebimento.xlsx]
         |                      |                         |
         v                      v                         v
   ConfigLoader           DataLoader + preparador    StateManager
         \                      /                         |
          \___________________/                           |
                    |                                     |
                    v                                     v
           CalculoComissao.__init__          RecebimentoOrchestrator
                    |                                     |
        ____________|_____________             ___________|___________
       |            |             |           |           |           |
       v            v             v           v           v           v
  _carregar   _validar      _preprocessar  Adiant.   Regular   Reconciliação
  _dados      _dados        _dados         (TCMP×1)  (TCMP×FCMP)  (FCMP-1)
       |
       v
  _calcular_realizado
       |
       v
  _calcular_comissoes   <-- loop item a item em FATURADOS
  (faturamento)
       |
       v
  _processar_devolucoes  <-- estorno proporcional
       |
       v
  _gerar_saida           <-- Excel multi-aba + PDF + Master DB
```

---

## 2. Fontes de Dados de Entrada

### 2.1 Arquivos Gerados pelo Preparador de Dados

O script `preparar_dados_mensais.py` (executado automaticamente ao início de cada rodada) filtra os dados brutos do ERP para o mês/ano de apuração e gera:

| Arquivo Gerado | Conteúdo |
|---|---|
| `Faturados.xlsx` | Itens faturados no mês selecionado (Status = FATURADO) |
| `Conversões.xlsx` | Processos em prospecção/conversão no mês |
| `Faturados_YTD.xlsx` | Faturamento acumulado desde janeiro até o mês (para metas de fornecedores) |

### 2.2 Arquivos Fixos (Input Manual)

| Arquivo / Caminho | Conteúdo |
|---|---|
| `dados_entrada/Analise_Comercial_Completa.xlsx` (ou `.csv`) | Histórico completo de todos os processos comerciais com status, NF, datas e valores |
| `dados_entrada/Análise Financeira.xlsx` | Pagamentos recebidos: adiantamentos (COT) e pagamentos regulares (por NF) |
| `dados_entrada/Devoluções.xlsx` | Notas de devolução do período |
| `dados_entrada/rentabilidades/rentabilidade_MM_AAAA_agrupada.xlsx` | Rentabilidade por (linha, grupo, subgrupo, tipo de mercadoria) do mês |
| `config/REGRAS_COMISSOES.xlsx` | **Única fonte de verdade das regras** (ver seção 3) |
| `data/currency_rates/monthly_avg_rates.json` | Cache persistente de taxas de câmbio mensais |
| `Estado_Processos_Recebimento.xlsx` | Estado histórico de adiantamentos e métricas por processo |

---

## 3. Arquivo de Configuração — `REGRAS_COMISSOES.xlsx`

Toda regra de negócio é lida exclusivamente deste arquivo via `ConfigLoader.load_configs()`. Qualquer valor ausente nele impede a execução. As abas relevantes são:

### Aba `CONFIG_COMISSAO` — Regras de Rateio por Hierarquia

É a tabela central de taxas. Cada linha define uma combinação de dimensões e cargo, com dois percentuais fundamentais:

| Coluna | Significado |
|---|---|
| `linha` | Linha de negócio (ex.: "Tecnologia", "Industria") |
| `grupo` | Grupo de produto dentro da linha |
| `subgrupo` | Subgrupo do produto |
| `tipo_mercadoria` | Tipo de mercadoria / segmento |
| `cargo` | Cargo do colaborador ao qual a regra se aplica |
| `taxa_rateio_maximo_pct` | **Taxa de Rateio Máxima (%)** — percentual máximo do valor faturado que pode ser rateado como comissão |
| `fatia_cargo_pct` | **Fatia do Cargo (PE — Percentual de Elegibilidade) (%)** — fração da Taxa de Rateio que cabe a este cargo específico |

> **Exemplo prático:**  
> `taxa_rateio_maximo_pct = 3%`, `fatia_cargo_pct = 40%`  
> → A taxa efetiva deste cargo é `3% × 40% = 1,2%` do valor faturado (antes do FC).

A pesquisa da regra implementa **fallback hierárquico em 4 níveis** (do mais específico para o mais genérico):

1. `(linha, grupo, subgrupo, tipo_mercadoria)` — match exato
2. `(linha, grupo, *, tipo_mercadoria)` — sem subgrupo
3. `(linha, *, *, tipo_mercadoria)` — sem grupo/subgrupo
4. `(legacy_token, *, *, legacy_token)` — regra global de fallback

### Aba `COLABORADORES`

Lista todos os colaboradores ativos:

| Coluna | Significado |
|---|---|
| `id_colaborador` | Identificador único |
| `nome_colaborador` | Nome canônico (usado como chave em todo o sistema) |
| `cargo` | Cargo (deve existir em `CARGOS`) |
| `TIPO_COMISSAO` (opcional) | `"faturamento"` ou `"recebimento"` — define em qual fluxo o colaborador é remunerado |

### Aba `CARGOS`

| Coluna | Significado |
|---|---|
| `nome_cargo` | Nome do cargo |
| `tipo_cargo` | `"Gestão"` ou `"Operacional"` |
| `TIPO_COMISSAO` (opcional) | Define o fluxo de pagamento para todos os colaboradores daquele cargo |

> A função `ConfigLoader.detect_recebimento_colaboradores()` analisa as abas `CARGOS` e `COLABORADORES` para construir o conjunto `recebe_por_recebimento`, que determina quais colaboradores são processados pelo fluxo de recebimento em vez do de faturamento.

### Aba `ATRIBUICOES` — Formato Wide

Define quem são os responsáveis por cada hierarquia de produto:

| Coluna | Significado |
|---|---|
| `linha` | Linha de negócio |
| `grupo` | Grupo |
| `subgrupo` | Subgrupo |
| `tipo_mercadoria` | Tipo de mercadoria |
| `Gerente Linha 1` | Primeiro Gerente de Linha responsável |
| `Gerente Linha 2` | Segundo Gerente de Linha (split 50/50 por default, ou pelo `fator_split_gerente`) |
| `Coordenador 1` | Primeiro Coordenador |
| `Coordenador 2` | Segundo Coordenador (split 50/50 por default) |
| `fator_split_gerente` | Fator de divisão explícito para gerentes (ex.: 0.6 e 0.4) |
| `fator_split_coordenador` | Fator de divisão explícito para coordenadores |
| `[outros cargos]` | Colunas livres para outros cargos de gestão; múltiplos nomes por `;` |

> **Wildcard genérico:** Uma linha com `grupo = "[Todos os grupos]"` serve como fallback para qualquer hierarquia daquela linha que não tenha atribuição específica.

### Aba `PESOS_METAS` — Pesos do FC por Cargo

Define o peso de cada componente do FC para cada cargo:

| Coluna | Significado |
|---|---|
| `cargo` | Cargo |
| `faturamento_linha` | Peso (%) do componente de faturamento da linha no FC |
| `conversao_linha` | Peso (%) do componente de conversão da linha no FC |
| `faturamento_individual` | Peso (%) do faturamento individual do colaborador |
| `conversao_individual` | Peso (%) da conversão individual do colaborador |
| `rentabilidade` | Peso (%) da rentabilidade da hierarquia |
| `retencao_clientes` | Peso (%) da retenção de clientes (somente `Gerente Linha`) |
| `meta_fornecedor_1` | Peso (%) da meta do fornecedor 1 |
| `meta_fornecedor_2` | Peso (%) da meta do fornecedor 2 |

> A soma de todos os pesos de um cargo **deve ser 100%**. O sistema valida e emite aviso caso não seja.

### Aba `METAS_APLICACAO` — Metas de Linha/Hierarquia

Contém as metas para componentes coletivos (faturamento e conversão da linha):

| Coluna | Significado |
|---|---|
| `linha` | Linha de negócio |
| `grupo` | Grupo (pode ser vazio para meta geral da linha) |
| `subgrupo` | Subgrupo (pode ser vazio) |
| `tipo_mercadoria` | Tipo de mercadoria (pode ser vazio) |
| `tipo_meta` | `"faturamento"` ou `"conversao"` |
| `valor_meta` | Valor da meta em R$ para o período |

A busca desta meta também implementa **5 níveis de fallback** hierárquico (exato → apenas linha).

### Aba `METAS_INDIVIDUAIS`

Metas por colaborador para faturamento e conversão individuais:

| Coluna | Significado |
|---|---|
| `colaborador` | Nome do colaborador |
| `tipo_meta` | `"faturamento"` ou `"conversao"` |
| `valor_meta` | Valor da meta em R$ |

### Aba `META_RENTABILIDADE`

Metas de rentabilidade por hierarquia completa:

| Coluna | Significado |
|---|---|
| `linha`, `grupo`, `subgrupo`, `tipo_mercadoria` | Chave da hierarquia |
| `meta_rentabilidade_alvo_pct` | Percentual de rentabilidade alvo (ex.: 0.12 para 12%) |

### Aba `METAS_FORNECEDORES`

Metas anuais de faturamento junto a fornecedores específicos, em moeda estrangeira:

| Coluna | Significado |
|---|---|
| `linha` | Linha onde o fornecedor opera |
| `fornecedor` (ou `fabricante`) | Nome do fornecedor |
| `meta_anual` | Meta anual na moeda indicada |
| `moeda` | Código da moeda (ex.: `USD`, `EUR`, `BRL`) |

### Aba `FC_ESCADA_CARGOS`

Configuração da regra de degraus (escada) do FC por cargo:

| Coluna | Significado |
|---|---|
| `cargo` | Cargo |
| `modo` | `RAMPA` (linear) ou `ESCADA` (degraus) |
| `num_degraus` | Número de degraus (mínimo 2) |
| `piso_pct` | Percentual mínimo do teto que o piso representa (ex.: 50 = 50% do teto) |

### Outras Abas

| Aba | Conteúdo |
|---|---|
| `PARAMS` | Parâmetros gerais: `mes_apuracao`, `ano_apuracao`, `cap_atingimento_max`, `cap_fc_max`, `cross_selling_default_option`, `legacy_scope_token`, `base_path` |
| `ALIASES` | Mapeamento de variantes de nomes de colaboradores para o nome canônico |
| `CROSS_SELLING` | Consultores externos elegíveis a comissão de cross-selling com suas respectivas taxas |

---

## 4. Inicialização e Preparação dos Dados

### 4.1 `__main__` — Ponto de Entrada

Ao ser executado diretamente, `calculo_comissoes.py` segue esta sequência:

1. **Verificação/atualização de câmbio** — `_atualizar_taxas_cambio_iniciais()` garante que o JSON de taxas tenha todas as taxas mensais do ano corrente até o último mês fechado, para cada moeda presente em `METAS_FORNECEDORES`. Se uma taxa não puder ser obtida via API, é gerado um fallback baseado na média do ano.

2. **Leitura de mês/ano** — Via argumento `--mes`/`--ano`, variáveis de ambiente (`MES_APURACAO`, `ANO_APURACAO`, `COMISSOES_MES`, `COMISSOES_ANO`) ou input interativo.

3. **Preparador de dados** — `preparar_dados_mensais.run_preparador(mes, ano)` gera os arquivos `Faturados.xlsx`, `Conversões.xlsx` e `Faturados_YTD.xlsx`. O processo **aborta** se o preparador falhar.

4. **Seleção do arquivo de rentabilidade** — Busca em `dados_entrada/rentabilidades/` ou `rentabilidades/` pelo padrão `*MM*AAAA*agrupada*.xlsx`.

5. **Parsing de decisões de cross-selling via CLI** — `--decisions '[{"processo":"X","decision":"A"}]'`

6. **Instanciação e execução de `CalculoComissao`** — `calculadora.executar(decisoes_cross_selling=...)`

### 4.2 Método `executar()`

Orquestra todas as fases em ordem, usando timers e um `ProgressTracker` opcional:

```
Fase 1:  _carregar_dados()
Fase 2:  _validar_dados()
Fase 3:  _preprocessar_dados()
Fase 4:  _calcular_realizado()
Fase 5.1 (se há colaboradores por recebimento):
         RecebimentoOrchestrator.executar()   ← arquivo separado gerado aqui
Fase 5.3: _calcular_comissoes()               ← loop item a item em FATURADOS
Fase 6:  _gerar_saida()
```

> **Importante:** O fluxo de recebimento (Fase 5.1) é executado **antes** do cálculo de faturamento (Fase 5.3). Isso porque os dados da Análise Comercial e os realizados precisam estar carregados, mas as comissões de recebimento são geradas em arquivo separado e não interferem no DataFrame de comissões de faturamento.

### 4.3 `_carregar_dados()`

```python
config_loader = ConfigLoader(validation_logger=...)
config_data = config_loader.load_configs("config/REGRAS_COMISSOES.xlsx")
self.data.update(config_data)
# → carrega: CONFIG_COMISSAO, COLABORADORES, CARGOS, ATRIBUICOES, PESOS_METAS,
#            METAS_APLICACAO, METAS_INDIVIDUAIS, META_RENTABILIDADE, METAS_FORNECEDORES,
#            ALIASES, PARAMS, CROSS_SELLING, FC_ESCADA_CARGOS, etc.

data_loader = DataLoader(...)
input_data = data_loader.load_input_data(mes, ano, ...)
self.data.update(input_data)
# → carrega: FATURADOS, CONVERSOES, FATURADOS_YTD, RENTABILIDADE_REALIZADA,
#            ANALISE_COMERCIAL_COMPLETA, RECEBIMENTOS, PAGAMENTOS_REGULARES
```

Após o carregamento, `detect_recebimento_colaboradores()` constrói o conjunto `self.recebe_por_recebimento` com todos os nomes de colaboradores que devem ser processados no fluxo de recebimento.

### 4.4 `_validar_dados()`

- Verifica que a soma dos pesos de cada cargo em `PESOS_METAS` é 100%
- Verifica que todos os colaboradores em `ATRIBUICOES` existem em `COLABORADORES`
- Executa `_validar_preenchimento_hierarquias()`: para cada combinação `(linha, grupo, subgrupo, tipo_mercadoria)` presente em `FATURADOS`, verifica se há uma atribuição com os cargos de gestão obrigatórios preenchidos; usa fallback hierárquico para atribuição genérica
- Se houver hierarquias não cobertas, lança `MissingAssignmentsError` (exceção tipada que interrompe a execução com lista detalhada dos problemas)

### 4.5 `_preprocessar_dados()`

- Mantém `ATRIBUICOES` no formato Wide (sem conversão para Vertical)
- Aplica mapa de aliases em `FATURADOS.Consultor Interno` e `FATURADOS.Representante-pedido`
- Faz join de `COLABORADORES` com `CARGOS` para adicionar `tipo_cargo` a cada colaborador

---

## 5. Hierarquia de Atribuições (Formato Wide)

A aba `ATRIBUICOES` usa formato Wide: uma linha por `(linha, grupo, subgrupo, tipo_mercadoria)`, com uma coluna por cargo.

### 5.1 Busca de Atribuição com Fallback (`_buscar_atribuicao_wide`)

```
1. Busca match exato: (linha, grupo, subgrupo, tipo_mercadoria)
   - Se encontrou E tem pelo menos 1 cargo de gestão preenchido → usa esta linha
   - Se encontrou mas todos os cargos de gestão estão vazios:
     → tenta buscar linha genérica (grupo contém "[Todos")
     → se genérica também estiver vazia → retorna a específica (mesmo vazia)

2. Se não encontrou específica:
   → tenta linha genérica (linha, [Todos os grupos], ...)
   → se não encontrou nenhuma → retorna None
```

### 5.2 Extração de Colaboradores (`_extrair_colaboradores_wide`)

Para cada linha Wide encontrada, esta função retorna uma lista de dicts:

```python
[
  {"colaborador": "João Silva", "cargo": "Gerente Linha", "fator_split": 0.5},
  {"colaborador": "Maria Souza", "cargo": "Gerente Linha", "fator_split": 0.5},
  {"colaborador": "Pedro Costa", "cargo": "Coordenador",  "fator_split": 1.0},
  ...
]
```

**Regras de `fator_split`:**
- `Gerente Linha 1` e `Gerente Linha 2` presentes → `fator_split = fator_split_gerente` (se definido) ou `0.5` para cada
- `Gerente Linha 1` apenas → `fator_split = 1.0`
- Mesmo lógica para `Coordenador 1`/`Coordenador 2`
- Todos os outros cargos: `fator_split = 1.0` sempre
- Múltiplos nomes separados por `;` em uma coluna → `fator_split = 1.0` para cada

---

## 6. Cálculo de Realizado

`_calcular_realizado()` agrega os dados de entrada em séries indexadas que serão consultadas durante o cálculo do FC.

| Chave em `self.realizado` | Fonte | Agregação |
|---|---|---|
| `faturamento_linha` | `FATURADOS.Valor Realizado` | `groupby("Negócio").sum()` |
| `faturamento_individual` | `FATURADOS` (Consultor Interno + Representante-pedido) | `sum()` dos dois campos combinados por nome |
| `conversao_linha` | `CONVERSOES.Valor Orçado` | `groupby("Negócio").sum()` |
| `conversao_individual` | `CONVERSOES` (Consultor Interno + Representante-pedido) | `sum()` dos dois campos combinados por nome |
| `rentabilidade` | `RENTABILIDADE_REALIZADA.rentabilidade_realizada_pct` | MultiIndex `(linha, Grupo, Subgrupo, Tipo de Mercadoria)` |

> **Bug histórico corrigido:** Faturamento e conversão individuais somam tanto `Consultor Interno` quanto `Representante-pedido` para incluir consultores externos que aparecem apenas na segunda coluna.

---

## 7. Busca de Regra de Comissão (`_get_regra_comissao`)

Signature: `_get_regra_comissao(linha, grupo, subgrupo, tipo_mercadoria, cargo)`

Consulta a aba `CONFIG_COMISSAO` usando **4 filtros em cascata** (do mais específico para o mais genérico):

```
Filtro 1: linha + grupo + subgrupo + tipo_mercadoria  (match exato)
Filtro 2: linha + grupo + subgrupo == NaN/legacy      + tipo_mercadoria
Filtro 3: linha + grupo == NaN/legacy + subgrupo == NaN/legacy + tipo_mercadoria
Filtro 4: linha == legacy_token + tipo_mercadoria == legacy_token (regra global)
```

> O `legacy_token` é lido do parâmetro `legacy_scope_token` em `PARAMS` (default `"__legacy__"`).

O resultado é **cacheado** em `self.cache_regras` para evitar releituras durante o loop de itens.

---

## 8. Fator de Correção — FC (`_calcular_fc_para_item`)

O FC é um multiplicador entre `0` e `cap_fc_max` (default `1.0`) que ajusta a comissão potencial com base no desempenho do colaborador e da empresa.

### 8.1 Estrutura Geral

O FC é a **soma ponderada do atingimento de cada componente de meta**, com teto individual por `cap_atingimento_max` (default `1.0`):

$$FC_{total} = \sum_{i} \min\left(\frac{Realizado_i}{Meta_i},\, cap\right) \times Peso_i$$

$$FC_{final} = \min(FC_{total},\, cap\_fc\_max)$$

Os pesos são lidos de `PESOS_METAS` para o cargo do colaborador. Componentes com peso zero são ignorados completamente.

### 8.2 Componentes do FC

#### 8.2.1 Faturamento da Linha (`faturamento_linha`)

- **Realizado:** `self.realizado["faturamento_linha"].get(item["Negócio"], 0)`
- **Meta:** `METAS_APLICACAO` com busca hierárquica de 5 níveis pelo campo `(linha, grupo, subgrupo, tipo_mercadoria)` onde `tipo_meta = "faturamento"`
- **Atingimento:** `realizado_linha / meta_faturamento_linha`

#### 8.2.2 Conversão da Linha (`conversao_linha`)

- **Realizado:** `self.realizado["conversao_linha"].get(item["Negócio"], 0)`
- **Meta:** `METAS_APLICACAO` onde `tipo_meta = "conversao"`
- **Atingimento:** `realizado_conversao_linha / meta_conversao_linha`

#### 8.2.3 Faturamento Individual (`faturamento_individual`)

- **Realizado:** `self.realizado["faturamento_individual"].get(nome_colab, 0)`
- **Meta:** `METAS_INDIVIDUAIS` onde `colaborador = nome_colab` e `tipo_meta = "faturamento"`
- **Atingimento:** `realizado_individual / meta_individual`

#### 8.2.4 Conversão Individual (`conversao_individual`)

- **Realizado:** `self.realizado["conversao_individual"].get(nome_colab, 0)`
- **Meta:** `METAS_INDIVIDUAIS` onde `colaborador = nome_colab` e `tipo_meta = "conversao"`
- **Atingimento:** `realizado_conversao_individual / meta_conversao_individual`

#### 8.2.5 Rentabilidade (`rentabilidade`)

- **Realizado:** `self.realizado["rentabilidade"].get((linha, grupo, subgrupo, tipo_merc), 0)` — busca normalizada + fallback para chave original
- Se o valor retornado for > 1, é dividido por 100 (conversão de % para decimal)
- **Meta:** `META_RENTABILIDADE` com match exato de (linha, grupo, subgrupo, tipo_mercadoria)
- **Atingimento:** `realizado_rentab / meta_rentab`

#### 8.2.6 Retenção de Clientes (`retencao_clientes`) — Somente Gerente Linha

Veja [Seção 22](#22-retenção-de-clientes-gerente-linha) para detalhes completos.

#### 8.2.7 Meta Fornecedor 1 e 2 (`meta_fornecedor_1`, `meta_fornecedor_2`)

Veja [Seção 21](#21-taxas-de-câmbio-e-metas-de-fornecedores) para detalhes completos.

### 8.3 Utilidade `_calcular_atingimento`

```python
def _calcular_atingimento(realizado, meta):
    if meta is None or meta == 0:
        return 0.0
    return realizado / meta
```

### 8.4 Cap de Atingimento

Cada componente é individualmente **capado** antes de multiplicar pelo peso:

```python
atingimento_cap = min(atingimento, cap_atingimento_max)  # default 1.0
componente = atingimento_cap * peso
```

Isto significa que atingir 120% da meta não gera mais FC do que atingir 100% (a menos que `cap_atingimento_max` seja definido como > 1.0 em `PARAMS`).

---

## 9. Regra de Escada do FC (`fc_escada.py`)

O FC calculado em `_calcular_fc_para_item` é inicialmente em **modo Rampa** (linear). A aba `FC_ESCADA_CARGOS` pode sobrepor este comportamento com o modo **Escada** para cargos específicos.

### 9.1 Modo RAMPA (default)

$$multiplicador = performance$$

O FC é usado diretamente como multiplicador, sem alteração.

### 9.2 Modo ESCADA

O performance (FC em rampa) é mapeado para um **degrau discreto** entre `piso` e `1.0`:

```
Degraus: n degraus uniformemente distribuídos entre piso e 1.0
Índice do degrau: i = floor(performance × (n-1))   [sem tolerância]
Topo (i = n-1) somente quando performance >= 1.0

multiplicador = piso + (i × (1 - piso) / (n - 1))
```

**Exemplo:** `n=4 degraus`, `piso=0.5`

| Performance | Índice | Multiplicador |
|---|---|---|
| 0.00 – 0.33 | 0 | 0.50 (piso) |
| 0.33 – 0.67 | 1 | 0.667 |
| 0.67 – 1.00 | 2 | 0.833 |
| ≥ 1.00 | 3 | 1.00 (teto) |

> **Sem tolerância:** Para subir de degrau, o colaborador precisa atingir exatamente o limiar; não há margem de tolerância configurável.

### 9.3 Aplicação

- **Faturamento:** `aplicar_fc_escada(fc_rampa, cargo, configs_por_cargo)` é chamado dentro de `_calcular_comissoes()` para cada item/colaborador
- **Recebimento (FCMP):** `aplicar_fc_escada(fcmp_rampa, cargo, configs_por_cargo)` é chamado em `MetricasCalculator` depois do cálculo da média ponderada

---

## 10. Comissões por Faturamento (`_calcular_comissoes`)

Este é o loop principal do cálculo de faturamento, iterando sobre cada linha de `FATURADOS`.

### 10.1 Fluxo por Item Faturado

Para cada `item_faturado` em `FATURADOS`:

```
1. Buscar atribuição (Wide) → gestao_list
2. Extrair colaboradores do item (Consultor Interno, Representante-pedido) → operacional_list
3. Combinar gestão + operacional em um único DataFrame
4. Deduplicar: se mesmo nome + cargo → somar fator_split, capar em 1.0
5. Verificar cross-selling para este processo (cs_info)
   → Se for cross-selling: gerar linha de comissão especial para o Consultor Externo
   → Remover Consultor Externo do rateio normal

Para cada colaborador na lista combinada:
   a. Se for colaborador de "recebimento" → pular (será tratado pelo RecebimentoOrchestrator)
   b. Buscar regra de comissão → taxa_rateio_maximo_pct, fatia_cargo_pct
   c. Calcular FC em rampa → _calcular_fc_para_item(nome, cargo, item)
   d. Aplicar escada → aplicar_fc_escada(fc_rampa, cargo)
   e. Aplicar fator_split
   f. Calcular comissão:
      comissao = Valor_Realizado × taxa_rateio × PE × fator_split × FC_aplicado
   g. Armazenar linha com todos os detalhes de auditoria
```

### 10.2 Fórmula da Comissão de Faturamento

$$Comissao = V \times \frac{TR}{100} \times \frac{PE}{100} \times s \times FC$$

Onde:
- $V$ = Valor Realizado do item faturado
- $TR$ = `taxa_rateio_maximo_pct` (Taxa de Rateio Máxima)
- $PE$ = `fatia_cargo_pct` (Percentual de Elegibilidade / Fatia do Cargo)
- $s$ = `fator_split` (1.0 se cargo único, < 1.0 se dividido)
- $FC$ = Fator de Correção após escada aplicada

### 10.3 Impacto do Cross-Selling (Decisão A)

Quando o processo é cross-selling e a decisão é **A** (subtrair):

```
taxa_rateio_efetiva = max(0, taxa_rateio_original - taxa_cross_selling)
```

Os demais colaboradores recebem uma taxa de rateio **reduzida** em exatamente o percentual pago ao consultor externo.

### 10.4 Colunas de Auditoria Geradas

Cada linha de comissão calculada contém:

| Coluna | Conteúdo |
|---|---|
| `nome_colaborador`, `cargo`, `id_colaborador` | Identificação |
| `cod_produto`, `descricao_produto`, `processo` | Item |
| `linha`, `grupo`, `subgrupo`, `tipo_mercadoria` | Hierarquia |
| `faturamento_item` | Valor Realizado do item |
| `taxa_rateio_aplicada` | Taxa de rateio efetiva (após ajuste cross-selling) |
| `percentual_elegibilidade_pe` | Fatia do cargo (PE) |
| `fator_split_cargo` | Fator de divisão aplicado |
| `fator_correcao_fc` | FC final (após escada) |
| `fator_correcao_fc_rampa` | FC antes da escada |
| `fc_escada_modo`, `fc_escada_degrau_indice`, `fc_escada_num_degraus`, `fc_escada_piso` | Detalhes da escada |
| `comissao_potencial_maxima` | Comissão sem o FC |
| `comissao_calculada` | Comissão final |
| `peso_fat_linha`, `realizado_fat_linha`, `meta_fat_linha`, `ating_fat_linha`, `ating_cap_fat_linha`, `comp_fc_fat_linha` | Componente de faturamento da linha |
| `peso_conv_linha`, `realizado_conv_linha`, ... | Componente de conversão da linha |
| `peso_fat_ind`, `realizado_fat_ind`, ... | Componente de faturamento individual |
| `peso_conv_ind`, `realizado_conv_ind`, ... | Componente de conversão individual |
| `peso_rentab`, `realizado_rentab`, ... | Componente de rentabilidade |

---

## 11. Cross-Selling — Detecção e Decisões

### 11.1 Critério de Detecção

Um item de `FATURADOS` é considerado cross-selling quando:

1. `Gerente Comercial-Pedido` está preenchido no item
2. Esse nome corresponde a um colaborador com cargo `"Consultor Externo"` (ou `tipo_cargo = "externo"`)
3. O consultor **não** possui atribuição na aba `ATRIBUICOES` para a linha daquele item específico
4. O consultor **está cadastrado** na aba `CROSS_SELLING` com `taxa_cross_selling_pct > 0`

Se todas as condições forem satisfeitas, o processo entra em `self.casos_cross_selling_detectados`.

### 11.2 Opções de Decisão (A ou B)

A decisão é determinada, em ordem de prioridade:
1. Decisão passada via CLI (`--decisions`) ou API (`decisoes_passadas`)
2. Parâmetro `cross_selling_default_option` em `PARAMS` (default: `"A"`)
3. Prompt interativo no terminal (somente em execução interativa)

| Opção | Efeito nos Outros | Efeito no Consultor Externo |
|---|---|---|
| **A** — Subtrair | Taxa de rateio **reduzida** em `taxa_cross_selling_pct` para todos os demais | Recebe comissão separada com `taxa = taxa_cross_selling × Valor_Realizado × 1.0` |
| **B** — Pagar Separadamente | Taxa de rateio **mantida intacta** para todos os demais; consultor externo removido do rateio normal | Recebe comissão separada com `taxa = taxa_cross_selling × Valor_Realizado × 1.0` |

Em ambas as opções, a comissão do consultor externo é sempre:
$$Comissao_{CS} = Valor\_Realizado \times \frac{taxa\_cross\_selling\_pct}{100}$$

O FC do consultor externo é sempre **1.0** para comissões de cross-selling.

---

## 12. Comissões por Recebimento — Arquitetura Geral

Colaboradores marcados como `recebimento` são ignorados no loop de faturamento e processados pelo `RecebimentoOrchestrator`. Este orquestrador gera um arquivo Excel separado.

### 12.1 Fontes de Pagamento

O arquivo `dados_entrada/Análise Financeira.xlsx` é a fonte de todos os pagamentos. A classe `AnaliseFinanceiraLoader` normaliza o arquivo e classifica cada linha como:

| `TIPO_PAGAMENTO` | Critério | Processo Vinculado |
|---|---|---|
| `Antecipação` | Documento começa com `COT` | O número após `COT` é o processo |
| `Pagamento Regular` | Documento é número de NF | Vinculado via `ANALISE_COMERCIAL_COMPLETA.Numero NF → Processo` |

Linhas com `Valor Líquido ≤ 0` ou `Documento` vazio são ignoradas.

### 12.2 Identificação de Colaboradores Elegíveis

`IdentificadorColaboradores` encontra quais colaboradores de "recebimento" estão associados a um processo específico:

1. Busca todos os itens do processo em `ANALISE_COMERCIAL_COMPLETA`
2. Para cada item, consulta a atribuição Wide para a hierarquia `(linha, grupo, subgrupo, tipo_mercadoria)`
3. Retorna apenas os colaboradores cujos nomes estão em `recebe_por_recebimento`

---

## 13. TCMP — Taxa de Comissão Média Ponderada

A TCMP é a taxa efetiva de comissão de um colaborador sobre o valor de um processo, calculada como **média ponderada das taxas individuais de cada item** do processo.

### 13.1 Taxa por Item

Para cada item do processo e cada colaborador elegível:

$$taxa_{item} = \frac{taxa\_rateio\_maximo\_pct}{100} \times \frac{fatia\_cargo\_pct}{100}$$

A regra de comissão é buscada pelo mesmo método `_get_regra_comissao` descrito na [Seção 7](#7-busca-de-regra-de-comissão-_get_regra_comissao).

### 13.2 Cálculo da Média Ponderada

$$TCMP = \frac{\sum_{i} taxa_{i} \times Valor_{i}}{\sum_{i} Valor_{i}}$$

Onde `Valor_i` é o `Valor Realizado` do item (ou `Valor Orçado` se o primeiro for zero).

> A TCMP é calculada **uma vez quando o processo é faturado** e persistida no estado. Ela não muda com o tempo — representa a taxa efetiva definitiva daquele processo para aquele colaborador.

---

## 14. FCMP — Fator de Correção Médio Ponderado

O FCMP é o equivalente do FC para o fluxo de recebimento: mede o desempenho médio do colaborador, ponderado pelos valores dos itens do processo.

### 14.1 FC por Item (Modo Rampa)

Para cada item do processo (quando o processo está FATURADO):

$$FC_{item} = calcular\_fc\_para\_item(nome, cargo, item, mes\_faturamento, ano\_faturamento)$$

O cálculo usa os **realizados do mês de faturamento** do processo, não necessariamente do mês atual de apuração.

> Se o processo **não está FATURADO** ainda (status ≠ FATURADO), o FC de todos os itens é forçado a `1.0` — não há penalidade ou bônus de performance em adiantamentos pré-faturamento.

### 14.2 Cálculo da Média Ponderada (Rampa)

$$FCMP_{rampa} = \frac{\sum_{i} FC_{i} \times Valor_{i}}{\sum_{i} Valor_{i}}$$

### 14.3 Aplicação da Escada

Após calcular o FCMP em modo rampa, a escada é aplicada:

```python
fcmp_aplicado, detalhes_escada = aplicar_fc_escada(
    performance=fcmp_rampa,
    cargo=cargo_colab,
    configs_por_cargo=fc_escada_configs
)
```

O `fcmp_aplicado` é o valor definitivo usado nos cálculos de comissão de pagamentos regulares.

### 14.4 Persistência

Todos os valores são salvos no estado (`Estado_Processos_Recebimento.xlsx`):
- `TCMP` — por colaborador
- `FCMP` (rampa) — por colaborador  
- `FCMP_APLICADO` (após escada) — por colaborador
- `MES_ANO_FATURAMENTO` — quando o processo foi faturado

---

## 15. Adiantamentos (Pagamentos COT)

### 15.1 Definição

Adiantamentos (também chamados de COT, pré-pagamento ou antecipação) são pagamentos recebidos **antes do faturamento** do processo. Identificados pelo prefixo `COT` no documento da Análise Financeira.

### 15.2 Fórmula

$$Comissao_{adiantamento} = Valor \times TCMP \times \mathbf{1.0}$$

O FC é sempre `1.0` para adiantamentos, pois ainda não há faturamento — logo, não há como calcular o desempenho real.

### 15.3 Fluxo no `RecebimentoOrchestrator`

```python
def _processar_adiantamento(processo, valor, documento, data_pagamento):
    # 1. Calcular TCMP (com FC=1.0 forçado pelo status não-FATURADO)
    metricas = metricas_calc.calcular_metricas_processo(processo, mes, ano, status="PENDENTE")
    tcmp_dict = metricas["TCMP"]
    
    # 2. Salvar métricas no estado (FCMP=1.0 neste momento)
    state_manager.salvar_metricas(processo, tcmp_dict, fcmp={})
    
    # 3. Calcular comissões
    comissoes = comissao_calc.calcular_adiantamento(processo, valor, tcmp_dict)
    # → comissao = valor × tcmp × 1.0 para cada colaborador
    
    # 4. Armazenar comissões adiantadas por colaborador (para futura reconciliação)
    state_manager.armazenar_comissoes_adiantadas(processo, {colab: comissao})
    
    # 5. Atualizar estado: VALOR_ADIANTADO_TOTAL, TOTAL_ADIANTADO_COMISSAO
    state_manager.atualizar_pagamento_adiantamento(processo, valor, total_comissao)
```

### 15.4 Múltiplos Adiantamentos

Se um mesmo processo receber múltiplos adiantamentos em meses diferentes, **cada um gera comissão independente**. Os valores são acumulados no estado (`VALOR_ADIANTADO_TOTAL`, `TOTAL_ADIANTADO_COMISSAO`). A reconciliação futura considerará a soma total adiantada.

---

## 16. Pagamentos Regulares

### 16.1 Definição

Pagamentos regulares são recebimentos pós-faturamento, identificados por números de NF na Análise Financeira e vinculados ao processo via `ANALISE_COMERCIAL_COMPLETA`.

### 16.2 Fórmula

$$Comissao_{regular} = Valor \times TCMP \times FCMP_{aplicado}$$

### 16.3 Fluxo no `RecebimentoOrchestrator`

```python
def _processar_pagamento_regular(processo, valor, documento, data_pagamento):
    # 1. Verificar se métricas já foram calculadas
    metricas_salvas = state_manager.obter_metricas(processo)
    
    if metricas_salvas:
        # Usar TCMP e FCMP do estado (calculado quando processo foi faturado)
        tcmp_dict = metricas_salvas["TCMP"]
        fcmp_dict = metricas_salvas["FCMP_APLICADO"] or metricas_salvas["FCMP"]
    else:
        # Calcular agora (processo faturado, métricas ainda não persistidas)
        metricas = metricas_calc.calcular_metricas_processo(processo, mes, ano)
        tcmp_dict = metricas["TCMP"]
        fcmp_dict = metricas["FCMP_APLICADO"]
        state_manager.definir_metricas(processo, tcmp_dict, fcmp_dict, mes_faturamento)
    
    # 2. Calcular comissões: comissao = valor × TCMP × FCMP
    comissoes = comissao_calc.calcular_regular(processo, valor, tcmp_dict, fcmp_dict)
    
    # 3. Atualizar estado
    state_manager.atualizar_pagamento_regular(processo, valor, total_comissao)
```

### 16.4 FCMP Indisponível

Se o `FCMP` não estiver disponível (ex.: colaborador novo ou processo sem métricas), o sistema usa `fcmp = 1.0` como fallback seguro. Isso é registrado nas observações.

---

## 17. Reconciliação

### 17.1 O Problema que a Reconciliação Resolve

Na data do adiantamento, o FC foi forçado a `1.0` (sem dados de performance). Quando o processo é faturado, o FC real é calculado e pode ser diferente de `1.0`. A reconciliação é o **ajuste da comissão** entre o que foi pago com FC=1.0 e o que deveria ter sido pago com o FC real.

### 17.2 Critérios para Reconciliação

Um processo é elegível para reconciliação quando:
1. Teve pelo menos um adiantamento registrado (`TOTAL_ADIANTADO_COMISSAO > 0`)
2. Foi faturado no mês de apuração atual (Status = FATURADO + Numero NF preenchido)
3. Ainda não foi marcado como reconciliado no estado

### 17.3 Fórmula da Reconciliação

$$Reconciliacao_{colaborador} = Comissao\_Adiantada_{colaborador} \times (FCMP_{colaborador} - 1.0)$$

Ou equivalentemente:

$$Reconciliacao = Valor\_que\_deveria\_ter\_sido\_pago - Valor\_que\_foi\_pago$$

$$= Comissao\_Adiantada \times FCMP - Comissao\_Adiantada \times 1.0$$

$$= Comissao\_Adiantada \times (FCMP - 1.0)$$

**Casos:**
- `FCMP > 1.0` → Reconciliação **positiva** (crédito adicional ao colaborador)
- `FCMP < 1.0` → Reconciliação **negativa** (débito/desconto do colaborador)
- `FCMP = 1.0` → Reconciliação **zero** (nenhum ajuste necessário)

### 17.4 Fluxo de Reconciliação

```python
# ReconciliacaoDetector
processos_para_reconciliar = detector.detectar_processos_para_reconciliar()

for processo_id in processos_para_reconciliar:
    dados = detector.obter_dados_para_reconciliacao(processo_id)
    # dados contém: processo, comissoes_adiantadas (por colab), tcmp, fcmp, mes_faturamento
    
    # ReconciliacaoValidator
    valido, mensagem = validator.validar_dados_processo(dados)
    
    # ReconciliacaoCalculator
    reconciliacoes = calc.calcular_reconciliacao_processo(
        processo_id=dados["processo"],
        comissoes_adiantadas=dados["comissoes_adiantadas"],  # {colab: valor}
        tcmp_dict=dados["tcmp"],
        fcmp_dict=dados["fcmp"],
        mes_faturamento=dados["mes_faturamento"]
    )
    # Para cada colaborador:
    # ajuste = comissao_adiantada × (fcmp - 1.0)
    
    # Marcar como reconciliado no estado
    state_manager.marcar_reconciliacao_calculada(processo_id)
```

### 17.5 Reconciliação na Lógica Legacy (Dentro de `_reconciliar_e_calcular_metricas_do_mes`)

A lógica legacy (ainda presente no código como complemento) calcula o saldo total agregado do processo:

$$saldo_{total} = \sum_{colab} Adiantado_{total} \times w_{colab} \times (FCMP_{colab} - 1.0)$$

Onde $w_{colab}$ é o peso proporcional do TCMP do colaborador:

$$w_{colab} = \frac{TCMP_{colab}}{\sum_{j} TCMP_j}$$

---

## 18. Devoluções — Estorno Proporcional

### 18.1 Visão Geral

Quando um cliente devolve uma mercadoria, a comissão correspondente deve ser estornada. O processamento de devoluções ocorre **após** o cálculo de faturamento e após salvar as comissões no banco de dados.

### 18.2 Arquivo de Entrada

`dados_entrada/Devoluções.xlsx` — carregado pelo `DevolucaoLoader`, que filtra por `data_entrada` dentro do mês/ano de apuração.

Colunas esperadas: `numero_nf_original`, `valor_devolvido`, `data_entrada`.

### 18.3 Fórmula do Estorno

$$Fator_{devolucao} = \min\left(\frac{Valor\_Devolvido}{Valor\_Realizado\_Processo},\, 1.0\right)$$

$$Estorno_{colaborador} = -\left(Comissao\_Historica_{colaborador} \times Fator_{devolucao}\right)$$

O resultado é sempre **negativo** (débito).

### 18.4 Fluxo Completo

```
DevolucaoProcessor.processar(mes, ano):
│
├─ DevolucaoLoader.carregar(mes, ano)
│   → Filtra Devoluções.xlsx pelo mês de apuração
│
├─ Para cada devolução:
│   ├─ _vincular_nf_com_processo(numero_nf, df_comercial)
│   │   → Busca Numero NF em ANALISE_COMERCIAL_COMPLETA
│   │   → Retorna (processo, valor_realizado_total_do_processo)
│   │
│   ├─ _buscar_comissoes_historicas(processo)
│   │   → Consulta MasterDBManager para comissões FATURAMENTO + REGULAR + ADIANTAMENTO
│   │
│   ├─ DevolucaoCalculator.calcular_estorno_processo(...)
│   │   → fator = valor_devolvido / valor_realizado_processo
│   │   → Agrupa comissões históricas por colaborador (sum)
│   │   → Para cada colaborador: estorno = -(comissao_acumulada × fator)
│   │
│   └─ Registros negativos adicionados à lista de saldos
│
└─ _salvar_no_banco_historico(mes, ano)
    → MasterDBManager.append_comissoes(..., tipo_comissao="DEVOLUCAO")
```

### 18.5 Comportamento com Múltiplas Devoluções do Mesmo Processo

Cada devolução é processada independentemente. O `Valor_Realizado_Processo` é sempre a soma completa de todos os itens do processo na Análise Comercial. Isso garante que o fator seja proporcional ao total do processo, não ao que já foi devolvido anteriormente.

### 18.6 Tratamento de Erros

- `Valor_Realizado ≤ 0` → fator definido como 0, devolução ignorada com aviso
- `Fator > 1.0` → limitado a 1.0 (caso de dado inválido onde devolvido > realizado)
- NF não encontrada na Análise Comercial → aviso registrado, devolução ignorada
- Sem comissões históricas → aviso registrado, devolução ignorada

---

## 19. Banco de Dados Master (`MasterDBManager`)

### 19.1 Finalidade

O banco de dados master é um arquivo Excel (`data/banco_dados/`) que funciona como **audit log imutável** de todas as comissões calculadas. Permite buscar histórico de comissões por processo para cálculo de estornos e reconciliações.

### 19.2 Tipos de Registro

| `tipo_comissao` | Gerado por |
|---|---|
| `FATURAMENTO` | `_salvar_no_banco_dados_master()` em `CalculoComissao` (comissões de faturamento) |
| `ADIANTAMENTO` | `RecebimentoOrchestrator._salvar_no_banco_dados_master()` |
| `REGULAR` | `RecebimentoOrchestrator._salvar_no_banco_dados_master()` |
| `RECONCILIACAO` | `RecebimentoOrchestrator._salvar_no_banco_dados_master()` |
| `DEVOLUCAO` | `DevolucaoProcessor._salvar_no_banco_historico()` |

### 19.3 Protocolo de Escrita Segura

1. Verificação de lock (evita escrita concorrente)
2. Backup atômico do arquivo antes de modificar
3. Append dos novos registros (nunca sobrescreve)
4. Cálculo de hash de integridade
5. Proteção read-only após escrita

### 19.4 Método de Leitura

`MasterDBManager.get_historico(processo=proc)` retorna todas as comissões históricas de um processo específico, usado pelo módulo de devoluções.

---

## 20. Geração de Arquivos de Saída

### 20.1 Arquivo de Faturamento

Gerado por `_gerar_saida()` → Excel com múltiplas abas:

| Aba | Conteúdo |
|---|---|
| `COMISSOES_CALCULADAS` | Detalhe item a item de cada comissão de faturamento |
| `RESUMO_COLABORADORES` | Soma de comissões por colaborador/cargo |
| `RESUMO_LINHAS` | Soma por linha de negócio |
| `RECONCILIACAO` | Detalhamento de reconciliações (lista + resumo) |
| `ESTADO` | Snapshot do estado dos processos de recebimento |
| `CROSS_SELLING_DECISIONS` | Decisões A/B por processo cross-selling |
| `VALIDACAO` | Log de erros, avisos e informações do processamento |
| `DEBUG_FORNECEDORES` | Detalhamento do cálculo de metas de fornecedores por item |
| `DEBUG_ANALISE_INFO` | Colunas disponíveis em Análise Comercial |
| `DEBUG_ENV` | Variáveis de ambiente e contexto de execução |

Nome do arquivo: `Calculo_Comissoes_MM_AAAA.xlsx` (gerado dinamicamente pelo preparador ou em `_gerar_saida()`).

Adicionalmente, se `reportlab` estiver instalado: **PDF de auditoria** com uma página por comissão detalhando cada componente do FC.

### 20.2 Arquivo de Recebimento

Gerado pelo `RecebimentoOutputGenerator` como arquivo separado `Comissoes_Recebimento_MM_AAAA.xlsx`:

| Aba | Conteúdo |
|---|---|
| `Adiantamentos` | Comissões de adiantamentos (COT) do período |
| `Pagamentos_Regulares` | Comissões de pagamentos regulares |
| `Reconciliacoes` | Ajustes de reconciliação calculados |
| `Estado` | Estado completo dos processos (TCMP, FCMP, valores pagos, status) |
| `Avisos` | Documentos não mapeados (NF não encontrada na Análise Comercial) |

---

## 21. Taxas de Câmbio e Metas de Fornecedores

### 21.1 Armazenamento

As taxas são persistidas em `data/currency_rates/monthly_avg_rates.json` com a seguinte estrutura por moeda/ano/mês:

```json
{
  "USD": {
    "2025": {
      "1": {"taxa_media": 4.9500, "fonte": "BCB", "fallback": false},
      "2": {"taxa_media": 4.9812, ...}
    }
  }
}
```

### 21.2 Fontes e Fallback

O `RateFetcher` busca taxas via API do Banco Central do Brasil (BCB). Se a busca falhar, é calculada a média do ano até o mês anterior como fallback. O JSON é atualizado automaticamente ao iniciar o cálculo (somente para meses já fechados do ano corrente).

### 21.3 Cálculo do Componente FC do Fornecedor

Para cada fornecedor da linha (até 2):

```
meta_ytd = (meta_anual / 12) × mes_apuracao

Para cada mês m de 1 até mes_apuracao:
    soma_brl_mes = FATURADOS_YTD[Fabricante == fornecedor_nome][mes == m]["Valor Realizado"].sum()
    faturamento_convertido_mes = soma_brl_mes / taxa_cambio[moeda][ano][m]

faturamento_ytd_na_moeda = Σ faturamento_convertido_mes

atingimento = min(faturamento_ytd / meta_ytd, cap_atingimento_max)
componente_fc_fornecedor = atingimento × peso_meta_fornecedor_N
```

> A conversão divide o valor em BRL pela taxa de câmbio mensal média (obtida do JSON) para obter o equivalente na moeda da meta.

---

## 22. Retenção de Clientes (Gerente Linha)

O componente `retencao_clientes` é calculado **somente para colaboradores com cargo `"Gerente Linha"`** e somente se o peso correspondente for > 0 em `PESOS_METAS`.

### 22.1 Lógica

A taxa de retenção compara clientes ativos em duas janelas de 24 meses consecutivas:

- **Janela Atual:** `[M-23, M]` (24 meses até o mês de apuração)
- **Janela Anterior:** `[M-24, M-1]` (os 24 meses antes)

$$Taxa\_Retencao = \frac{Clientes\_Unicos_{atual}}{Clientes\_Unicos_{anterior}}$$

Se não houver clientes na janela anterior, a taxa é:
- `1.0` se houver clientes na janela atual
- `0.0` se não houver clientes em nenhuma janela

A fonte de dados é `ANALISE_COMERCIAL_COMPLETA` filtrada por `Status = FATURADO` e pela linha de negócio do gerente.

### 22.2 Linha do Gerente

A linha usada para calcular a retenção é determinada consultando `ATRIBUICOES` e buscando a linha onde o gerente está atribuído como `"Gerente Linha"`. Se o gerente estiver em múltiplas linhas, a **primeira** linha encontrada é usada.

---

## 23. Aliases de Colaboradores

A aba `ALIASES` resolve variantes de nomes para o nome canônico:

```
alias: "J. Silva" → padrao: "João Silva"
alias: "joão silva" → padrao: "João Silva"
```

A aplicação ocorre em `_preprocessar_dados()` sobre as colunas `Consultor Interno` e `Representante-pedido` de `FATURADOS` e `CONVERSOES`. Isso garante que o mesmo colaborador seja reconhecido independente de como o ERP registrou o nome.

---

## 24. Fluxo de Execução Completo (Passo a Passo)

```
[INÍCIO]
    │
    ▼
1. Verificar/atualizar taxas de câmbio (JSON)
    │
    ▼
2. Obter mês/ano (CLI / ENV / input)
    │
    ▼
3. preparar_dados_mensais.run_preparador(mes, ano)
   → gera Faturados.xlsx, Conversões.xlsx, Faturados_YTD.xlsx
    │
    ▼
4. CalculoComissao().executar(decisoes_cross_selling)
    │
    ├─▶ _carregar_dados()
    │   ├─ ConfigLoader → REGRAS_COMISSOES.xlsx (todas as abas)
    │   ├─ DataLoader → Faturados, Conversões, YTD, Rentabilidade, Análise Comercial
    │   └─ detect_recebimento_colaboradores() → set recebe_por_recebimento
    │
    ├─▶ _validar_dados()
    │   ├─ Soma de pesos por cargo == 100%
    │   ├─ Colaboradores de ATRIBUICOES existem em COLABORADORES
    │   └─ Hierarquias de FATURADOS cobertas por ATRIBUICOES
    │       └─ MissingAssignmentsError se falhar (bloqueante)
    │
    ├─▶ _preprocessar_dados()
    │   ├─ Normalizar ATRIBUICOES (formato Wide)
    │   ├─ Aplicar aliases em FATURADOS e CONVERSOES
    │   └─ Join COLABORADORES + CARGOS
    │
    ├─▶ _calcular_realizado()
    │   └─ Agregar faturamento_linha, conversao_linha, individuais, rentabilidade
    │
    ├─▶ [SE há colaboradores por recebimento]
    │   RecebimentoOrchestrator(mes, ano).executar()
    │   │
    │   ├─ AnaliseFinanceiraLoader.carregar(mes, ano)
    │   │   → Classifica cada linha como Antecipação ou Pagamento Regular
    │   │
    │   ├─ StateManager.carregar_estado_anterior()
    │   │   → Estado_Processos_Recebimento.xlsx
    │   │
    │   ├─ ProcessMapper → mapeia documento → processo
    │   │
    │   ├─ Para cada pagamento da Análise Financeira:
    │   │   ├─ [ADIANTAMENTO] → _processar_adiantamento()
    │   │   │   ├─ calcular_metricas_processo(status=PENDENTE) → TCMP (FC=1.0)
    │   │   │   ├─ calcular_adiantamento() → comissao = valor × TCMP × 1.0
    │   │   │   └─ armazenar_comissoes_adiantadas()
    │   │   │
    │   │   └─ [PAGAMENTO REGULAR] → _processar_pagamento_regular()
    │   │       ├─ obter/calcular_metricas_processo(status=FATURADO) → TCMP, FCMP
    │   │       ├─ aplicar_fc_escada(FCMP_rampa) → FCMP_aplicado
    │   │       └─ calcular_regular() → comissao = valor × TCMP × FCMP_aplicado
    │   │
    │   ├─ _calcular_metricas_processos_faturados()
    │   │   → Para processos no estado que foram faturados no mês:
    │   │   → Calcula e persiste TCMP + FCMP
    │   │
    │   ├─ _calcular_reconciliacoes()
    │   │   → Detecta processos com adiantamento + faturados no mês
    │   │   → Reconciliacao = Comissao_Adiantada × (FCMP - 1.0)
    │   │
    │   ├─ _gerar_arquivo_saida()
    │   │   └─ Comissoes_Recebimento_MM_AAAA.xlsx
    │   │
    │   └─ _salvar_no_banco_dados_master()
    │       └─ ADIANTAMENTO + REGULAR + RECONCILIACAO → Master DB
    │
    ├─▶ _calcular_comissoes()   [FATURAMENTO]
    │   │
    │   ├─ _detectar_cross_selling()
    │   │   → Para cada item: verificar Gerente Comercial-Pedido
    │   │   → Se Consultor Externo sem atribuição na linha → candidato CS
    │   │   → Se cadastrado em CROSS_SELLING com taxa > 0 → caso confirmado
    │   │
    │   ├─ Definir decisões A/B por processo CS
    │   │
    │   └─ Para cada item_faturado:
    │       ├─ Buscar atribuição Wide (com fallback genérico)
    │       ├─ Extrair colaboradores de gestão e operacional
    │       ├─ Combinar e deduplicar (somar fator_split)
    │       ├─ [CS] Gerar linha especial para Consultor Externo
    │       │
    │       └─ Para cada colaborador:
    │           ├─ [SE recebimento] → pular
    │           ├─ _get_regra_comissao() → taxa_rateio, PE
    │           ├─ _calcular_fc_para_item():
    │           │   ├─ fat_linha: realizado_linha / meta_linha × peso
    │           │   ├─ conv_linha: realizado_conv / meta_conv × peso
    │           │   ├─ fat_ind: realizado_ind / meta_ind × peso
    │           │   ├─ conv_ind: realizado_conv_ind / meta_conv_ind × peso
    │           │   ├─ rentabilidade: realizado_rent / meta_rent × peso
    │           │   ├─ [SE Gerente Linha] retencao_clientes × peso_ret
    │           │   └─ [SE linha tem fornecedores] meta_fornecedor_N × peso_forn_N
    │           │       └─ YTD em moeda / taxa_cambio vs meta_ytd
    │           │
    │           ├─ aplicar_fc_escada(FC_rampa, cargo) → FC_aplicado
    │           │
    │           └─ comissao = V × TR × PE × fator_split × FC_aplicado
    │
    ├─▶ _processar_devolucoes()
    │   └─ DevolucaoProcessor.processar(mes, ano):
    │       ├─ Carregar Devoluções.xlsx → filtrar pelo mês
    │       ├─ Para cada devolução: NF → Processo → comissões históricas
    │       ├─ fator = devolvido / realizado_processo
    │       ├─ estorno = -(comissao_historica × fator)   [negativo]
    │       └─ Salvar como DEVOLUCAO no Master DB
    │
    └─▶ _gerar_saida()
        ├─ Calculo_Comissoes_MM_AAAA.xlsx (múltiplas abas)
        ├─ Salvar no Master DB (tipo FATURAMENTO)
        └─ [SE reportlab] Relatório PDF de auditoria

[FIM]
```

---

## 25. Glossário de Fórmulas

### Comissão de Faturamento (por item)

$$\boxed{C_{fat} = V \times \frac{TR}{100} \times \frac{PE}{100} \times s \times FC}$$

| Símbolo | Nome | Fonte |
|---|---|---|
| $V$ | Valor Realizado do item | `FATURADOS.Valor Realizado` |
| $TR$ | Taxa de Rateio Máxima (%) | `CONFIG_COMISSAO.taxa_rateio_maximo_pct` |
| $PE$ | Percentual de Elegibilidade / Fatia do Cargo (%) | `CONFIG_COMISSAO.fatia_cargo_pct` |
| $s$ | Fator Split | `ATRIBUICOES.fator_split_gerente` / 0.5 / 1.0 |
| $FC$ | Fator de Correção (após escada) | Calculado em `_calcular_fc_para_item` + `aplicar_fc_escada` |

---

### Fator de Correção (FC) — Soma Ponderada

$$\boxed{FC_{total} = \sum_{k} \min\!\left(\frac{R_k}{M_k},\, cap\right) \times p_k}$$

$$\boxed{FC = \min(FC_{total},\, cap\_fc\_max)}$$

| Símbolo | Descrição |
|---|---|
| $R_k$ | Realizado do componente $k$ |
| $M_k$ | Meta do componente $k$ |
| $cap$ | `cap_atingimento_max` em `PARAMS` (default 1.0) |
| $p_k$ | Peso do componente $k$ (de `PESOS_METAS`, em decimal) |
| $cap\_fc\_max$ | `cap_fc_max` em `PARAMS` (default 1.0) |

---

### FC Escada — Multiplicador por Degrau

$$\boxed{multiplicador_{escada} = piso + \left\lfloor perf \times (n-1) \right\rfloor \times \frac{1 - piso}{n-1}}$$

Para $perf \geq 1.0$: $multiplicador = 1.0$ (teto).

---

### TCMP — Taxa de Comissão Média Ponderada

$$\boxed{TCMP = \frac{\sum_{i} \left(\frac{TR_i}{100} \times \frac{PE_i}{100}\right) \times V_i}{\sum_{i} V_i}}$$

---

### FCMP — Fator de Correção Médio Ponderado (Rampa)

$$\boxed{FCMP_{rampa} = \frac{\sum_{i} FC_i \times V_i}{\sum_{i} V_i}}$$

O `FCMP_aplicado` = `aplicar_fc_escada(FCMP_rampa, cargo)`.

---

### Comissão de Adiantamento

$$\boxed{C_{adiant} = Valor\_recebido \times TCMP \times 1.0}$$

---

### Comissão de Pagamento Regular

$$\boxed{C_{regular} = Valor\_recebido \times TCMP \times FCMP_{aplicado}}$$

---

### Reconciliação

$$\boxed{Reconciliacao = C_{adiantada} \times (FCMP_{aplicado} - 1.0)}$$

Positiva quando $FCMP > 1.0$, negativa quando $FCMP < 1.0$.

---

### Estorno por Devolução

$$\boxed{fator_{dev} = \min\!\left(\frac{V_{devolvido}}{V_{realizado\,processo}},\; 1.0\right)}$$

$$\boxed{Estorno = -\left(C_{historica\_colaborador} \times fator_{dev}\right)}$$

---

### Retenção de Clientes (Gerente Linha)

$$\boxed{Taxa\_Retencao = \frac{Clientes_{[M-23,\,M]}}{Clientes_{[M-24,\,M-1]}}}$$

Onde os clientes são contados como únicos com faturamento (Status = FATURADO) na linha de negócio.

---

### Meta YTD de Fornecedor

$$\boxed{Meta_{ytd} = \frac{Meta_{anual}}{12} \times mes\_apuracao}$$

$$\boxed{Faturamento_{ytd,\,moeda} = \sum_{m=1}^{mes} \frac{Faturamento_{BRL,\,m}}{taxa\_cambio_{moeda,\,m}}}$$

$$\boxed{Componente_{FC,\,fornecedor} = \min\!\left(\frac{Faturamento_{ytd,\,moeda}}{Meta_{ytd}},\, cap\right) \times p_{fornecedor}}$$

---

*Fim do documento. Baseado na leitura direta do código-fonte em fevereiro de 2026.*
