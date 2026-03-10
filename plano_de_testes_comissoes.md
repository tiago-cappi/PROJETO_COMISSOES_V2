# Plano de Testes Exaustivo — Robô de Comissões V1 e V2

> **Projeto**: PROJETO_COMISSOES_V2
> **Data**: 2026-03-10
> **Autor**: Arquiteto de Software Líder
> **Objetivo**: Cobrir 100% dos cenários de cálculo de comissões, validações, edge cases e fluxo completo end-to-end.

---

## Índice

1. [Módulo: Normalização e Utilitários](#1-módulo-normalização-e-utilitários)
2. [Módulo: Carregamento de Configurações (V1)](#2-módulo-carregamento-de-configurações-v1)
3. [Módulo: Carregamento de Dados de Entrada](#3-módulo-carregamento-de-dados-de-entrada)
4. [Módulo: Engine de Atribuição (REGRAS_ATRIBUICAO)](#4-módulo-engine-de-atribuição-regras_atribuicao)
5. [Módulo: Lookup Hierárquico de Metas](#5-módulo-lookup-hierárquico-de-metas)
6. [Módulo: Cálculo do FC (Fator de Correção)](#6-módulo-cálculo-do-fc-fator-de-correção)
7. [Módulo: FC Escada / Rampa](#7-módulo-fc-escada--rampa)
8. [Módulo: Cálculo de Atingimento](#8-módulo-cálculo-de-atingimento)
9. [Módulo: Cálculo de Comissão por Faturamento (V1)](#9-módulo-cálculo-de-comissão-por-faturamento-v1)
10. [Módulo: Retenção de Clientes](#10-módulo-retenção-de-clientes)
11. [Módulo: Conversão Cambial (Metas Fornecedores)](#11-módulo-conversão-cambial-metas-fornecedores)
12. [Módulo: Devoluções](#12-módulo-devoluções)
13. [Módulo: Recebimento — Process Mapper](#13-módulo-recebimento--process-mapper)
14. [Módulo: Recebimento — Identificador de Colaboradores](#14-módulo-recebimento--identificador-de-colaboradores)
15. [Módulo: Recebimento — Métricas (TCMP / FCMP)](#15-módulo-recebimento--métricas-tcmp--fcmp)
16. [Módulo: Recebimento — Cálculo de Comissão](#16-módulo-recebimento--cálculo-de-comissão)
17. [Módulo: Recebimento — Reconciliação](#17-módulo-recebimento--reconciliação)
18. [Módulo: Recebimento — Orquestrador](#18-módulo-recebimento--orquestrador)
19. [Módulo: Recebimento — State Manager](#19-módulo-recebimento--state-manager)
20. [Módulo: Recebimento — Analise Financeira Loader](#20-módulo-recebimento--analise-financeira-loader)
21. [Módulo: Master DB Manager](#21-módulo-master-db-manager)
22. [Módulo: Preparador de Dados Mensais](#22-módulo-preparador-de-dados-mensais)
23. [Módulo: Metodologia V2 — Modelos](#23-módulo-metodologia-v2--modelos)
24. [Módulo: Metodologia V2 — Config Loader](#24-módulo-metodologia-v2--config-loader)
25. [Módulo: Metodologia V2 — Regra Matcher](#25-módulo-metodologia-v2--regra-matcher)
26. [Módulo: Metodologia V2 — Atribuição Service](#26-módulo-metodologia-v2--atribuição-service)
27. [Módulo: Metodologia V2 — Comissão Calculator (Hierarquia)](#27-módulo-metodologia-v2--comissão-calculator-hierarquia)
28. [Módulo: Metodologia V2 — CC Calculator (Centro de Custo)](#28-módulo-metodologia-v2--cc-calculator-centro-de-custo)
29. [Módulo: Metodologia V2 — Orquestrador](#29-módulo-metodologia-v2--orquestrador)
30. [Testes de Integração](#30-testes-de-integração)
31. [Testes End-to-End (E2E)](#31-testes-end-to-end-e2e)

---

## 1. Módulo: Normalização e Utilitários

**Arquivo**: `src/utils/normalization.py`

### T1.1 — normalize_text: texto com acentos
- **Cenário**: Texto com acentos e cedilha (ex: "Aplicação", "Comissão") deve ser normalizado para maiúsculo sem acentos.
- **Estrutura do teste**: Chamar `normalize_text("Aplicação Mat./Serv.")` e assertar resultado `"APLICACAO MAT./SERV."`.
- **Resultado esperado**: String em maiúsculo, sem acentos, sem BOM.

### T1.2 — normalize_text: texto com BOM (byte order mark)
- **Cenário**: Texto iniciando com `\ufeff` (BOM do Excel) deve ter o BOM removido.
- **Estrutura do teste**: `normalize_text("\ufeffNegócio")` → `"NEGOCIO"`.
- **Resultado esperado**: BOM removido, texto normalizado.

### T1.3 — normalize_text: texto None ou vazio
- **Cenário**: Entrada `None`, `""` ou apenas espaços.
- **Estrutura do teste**: Chamar com `None`, `""`, `"   "` e verificar retorno `""`.
- **Resultado esperado**: String vazia sem erro.

### T1.4 — normalize_text: texto já normalizado
- **Cenário**: Texto que já está em maiúsculo sem acentos não deve ser alterado.
- **Estrutura do teste**: `normalize_text("HIDROLOGIA")` → `"HIDROLOGIA"`.
- **Resultado esperado**: Idempotência garantida.

### T1.5 — calcular_atingimento: caso normal
- **Cenário**: Realizado=80000, Meta=100000 → atingimento = 0.8.
- **Estrutura do teste**: `calcular_atingimento(80000, 100000)` → `0.8`.
- **Resultado esperado**: Razão correta.

### T1.6 — calcular_atingimento: meta zero
- **Cenário**: Meta=0 (sem meta definida) deve retornar 1.0 (100%).
- **Estrutura do teste**: `calcular_atingimento(50000, 0)` → `1.0`.
- **Resultado esperado**: 1.0 (sem penalidade).

### T1.7 — calcular_atingimento: realizado zero
- **Cenário**: Realizado=0 com meta > 0 deve retornar 0.0.
- **Estrutura do teste**: `calcular_atingimento(0, 100000)` → `0.0`.
- **Resultado esperado**: 0.0.

### T1.8 — calcular_atingimento: realizado negativo
- **Cenário**: Realizado negativo deve retornar 0.0 (validação estrita).
- **Estrutura do teste**: `calcular_atingimento(-5000, 100000)` → `0.0`.
- **Resultado esperado**: 0.0 (valor inválido tratado).

### T1.9 — calcular_atingimento: meta negativa
- **Cenário**: Meta negativa deve retornar 0.0 (proteção contra dados inválidos).
- **Estrutura do teste**: `calcular_atingimento(80000, -100000)` → `0.0`.
- **Resultado esperado**: 0.0.

### T1.10 — calcular_atingimento: superação da meta
- **Cenário**: Realizado=150000, Meta=100000 → atingimento = 1.5 (150%).
- **Estrutura do teste**: `calcular_atingimento(150000, 100000)` → `1.5`.
- **Resultado esperado**: Valor > 1.0 permitido (sem cap aqui; cap é aplicado no FC).

---

## 2. Módulo: Carregamento de Configurações (V1)

**Arquivo**: `src/io/config_loader.py`

### T2.1 — Carregar REGRAS_COMISSOES.xlsx com todas as abas
- **Cenário**: Arquivo com todas as abas esperadas (PARAMS, COLABORADORES, CARGOS, REGRAS_ATRIBUICAO, PESOS_METAS, etc.) é carregado corretamente.
- **Estrutura do teste**: Criar Excel em memória (openpyxl) com as abas mínimas. Chamar `ConfigLoader.load_configs()`. Assertar que cada DataFrame retornado não está vazio e tem as colunas esperadas.
- **Resultado esperado**: Dict com DataFrames válidos para cada aba.

### T2.2 — Normalização de colunas (strip/lowercase)
- **Cenário**: Colunas com espaços extras (ex: " Nome_Colaborador ") devem ser normalizadas.
- **Estrutura do teste**: Criar aba COLABORADORES com coluna `"  nome_colaborador  "`. Verificar que após load, a coluna é acessível como `"nome_colaborador"`.
- **Resultado esperado**: Colunas stripped.

### T2.3 — Detecção de colaboradores por recebimento (Método 1: TIPO_COMISSAO em CARGOS)
- **Cenário**: Aba CARGOS tem coluna `TIPO_COMISSAO` com valor `"recebimento"` para cargo "Consultor Externo".
- **Estrutura do teste**: Criar config com CARGOS contendo `tipo_comissao=recebimento` para um cargo. Verificar que colaboradores com esse cargo aparecem no set `recebe_por_recebimento`.
- **Resultado esperado**: Todos colaboradores do cargo detectados.

### T2.4 — Detecção de colaboradores por recebimento (Método 2: TIPO_COMISSAO em COLABORADORES)
- **Cenário**: Aba COLABORADORES tem coluna `TIPO_COMISSAO` com valor `"recebimento"` direto no colaborador.
- **Estrutura do teste**: Criar config com COLABORADORES tendo `tipo_comissao=recebimento` para "JOAO". Verificar que "JOAO" está no set.
- **Resultado esperado**: Colaborador específico detectado.

### T2.5 — Detecção de colaboradores por recebimento (Método 3: heurístico)
- **Cenário**: Sem coluna TIPO_COMISSAO, detecta por convenção (cargos que tipicamente recebem por recebimento).
- **Estrutura do teste**: Criar config sem coluna TIPO_COMISSAO. Verificar se heurístico identifica cargos padrão.
- **Resultado esperado**: Heurístico funcional (ou set vazio se não aplicável).

### T2.6 — Arquivo de configuração inexistente
- **Cenário**: Caminho para REGRAS_COMISSOES.xlsx não existe.
- **Estrutura do teste**: Chamar `load_configs("caminho_invalido.xlsx")`. Assertar exceção `FileNotFoundError` ou equivalente.
- **Resultado esperado**: Exceção clara indicando arquivo não encontrado.

### T2.7 — Aba ausente no arquivo de configuração
- **Cenário**: REGRAS_COMISSOES.xlsx existe mas falta a aba PESOS_METAS.
- **Estrutura do teste**: Criar Excel sem a aba PESOS_METAS. Verificar comportamento (erro ou DataFrame vazio).
- **Resultado esperado**: Tratamento gracioso (warning ou DataFrame vazio).

### T2.8 — ALIASES: resolução de apelidos
- **Cenário**: Aba ALIASES mapeia "JOÃO DA SILVA" → "JOAO SILVA". Ao buscar regras por "JOÃO DA SILVA", deve resolver para "JOAO SILVA".
- **Estrutura do teste**: Criar aba ALIASES com mapeamento. Verificar que preprocessamento aplica alias corretamente.
- **Resultado esperado**: Nomes unificados após resolução de alias.

---

## 3. Módulo: Carregamento de Dados de Entrada

**Arquivo**: `src/io/data_loader.py`

### T3.1 — Carregar Análise Comercial Completa
- **Cenário**: Arquivo `analise-comercial-ultimos-4-meses-2025.xlsx` existe em `dados_entrada/`.
- **Estrutura do teste**: Mock do arquivo com colunas esperadas (Negócio, Grupo, Subgrupo, etc.). Chamar `load_input_data()`. Verificar DataFrame não vazio com colunas corretas.
- **Resultado esperado**: DataFrame com todas colunas da AC.

### T3.2 — Carregar Rentabilidade com busca por padrão
- **Cenário**: Arquivo `rentabilidade_10_2025_agrupada.xlsx` existe na pasta `dados_entrada/rentabilidades/`.
- **Estrutura do teste**: Criar arquivo com nome no padrão. Chamar `load_rentabilidade(10, 2025)`. Verificar que o arquivo correto é encontrado.
- **Resultado esperado**: DataFrame com colunas `Negocio`, `Grupo`, `Subgrupo`, `Tipo de Mercadoria`, `rentabilidade_realizada_pct`.

### T3.3 — Rentabilidade: arquivo não encontrado → DataFrame vazio
- **Cenário**: Nenhum arquivo de rentabilidade para o mês/ano solicitado.
- **Estrutura do teste**: Chamar `load_rentabilidade(99, 2025)`. Verificar retorno de DataFrame vazio com colunas padrão.
- **Resultado esperado**: DataFrame vazio sem exceção.

### T3.4 — Carregar Análise Financeira
- **Cenário**: Arquivo `analise-financeira-2025-2026-meses-fechados.xlsx` existente.
- **Estrutura do teste**: Mock do arquivo. Verificar colunas: Documento, Valor Liquido, Data de Baixa, Tipo de Baixa.
- **Resultado esperado**: DataFrame filtrado por Tipo de Baixa = 'B'.

### T3.5 — Carregar Devoluções
- **Cenário**: Arquivo `devolucoes.xlsx` em `dados_entrada/`.
- **Estrutura do teste**: Mock com colunas Num docorigem, Data de Entrada, Valor Produtos. Verificar carregamento.
- **Resultado esperado**: DataFrame com NFs de devolução.

### T3.6 — Fallback de caminhos de arquivo
- **Cenário**: Arquivo não encontrado no caminho primário (`dados_entrada/`) mas presente na raiz.
- **Estrutura do teste**: Colocar arquivo apenas na raiz. Verificar que o fallback o encontra.
- **Resultado esperado**: Arquivo encontrado no caminho alternativo.

### T3.7 — Coluna com BOM no Excel
- **Cenário**: Primeira coluna do Excel tem `\ufeff` prefixado (comportamento comum de CSVs salvos pelo Excel).
- **Estrutura do teste**: Criar DataFrame com coluna `"\ufeffNegocio"`. Verificar que normalização remove BOM.
- **Resultado esperado**: Coluna acessível como `"Negocio"`.

### T3.8 — Conversões e Faturados YTD
- **Cenário**: Carregar Faturados_YTD.xlsx com colunas Dt Emissao, Fabricante, Valor Realizado.
- **Estrutura do teste**: Mock do arquivo. Verificar parsing de datas e tipos numéricos.
- **Resultado esperado**: DataFrame com tipos corretos.

---

## 4. Módulo: Engine de Atribuição (REGRAS_ATRIBUICAO)

**Arquivo**: `src/regras/atribuicao_engine.py`

### T4.1 — preprocessar_regras: normalização de texto
- **Cenário**: REGRAS_ATRIBUICAO com valores contendo acentos (ex: "Automação") devem ser normalizados para "AUTOMACAO".
- **Estrutura do teste**: Criar DataFrame com `linha="Automação"`. Chamar `preprocessar_regras()`. Verificar que valor ficou normalizado.
- **Resultado esperado**: Todos campos hierárquicos normalizados.

### T4.2 — preprocessar_regras: cálculo automático de fator_split
- **Cenário**: Dois colaboradores com mesmo cargo atribuídos à mesma hierarquia sem fator_split definido → auto-cálculo (0.5 cada).
- **Estrutura do teste**: Criar 2 regras para mesma hierarquia sem fator_split. Verificar que `preprocessar_regras()` calcula 0.5 para cada.
- **Resultado esperado**: fator_split = 0.5 para cada colaborador.

### T4.3 — preprocessar_regras: fator_split manual respeitado
- **Cenário**: Colaborador tem fator_split=0.7 definido manualmente. Não deve ser sobrescrito.
- **Estrutura do teste**: Criar regra com fator_split=0.7. Verificar que permanece 0.7 após preprocessamento.
- **Resultado esperado**: Valor manual preservado.

### T4.4 — buscar_regras_item: match exato (máxima especificidade)
- **Cenário**: Item com linha="HIDROLOGIA", grupo="QED", subgrupo="BOMBAS". Regra existe com exatamente esses 3 campos.
- **Estrutura do teste**: Criar regra com score=3. Criar item com contexto correspondente. Chamar `buscar_regras_item()`. Verificar match.
- **Resultado esperado**: Regra retornada com score máximo.

### T4.5 — buscar_regras_item: match por fallback (hierarquia genérica)
- **Cenário**: Item com linha="HIDROLOGIA", grupo="QED", subgrupo="MOTORES". Não existe regra específica, mas existe regra para linha="HIDROLOGIA" (wildcard em grupo/subgrupo).
- **Estrutura do teste**: Criar regra genérica (apenas linha). Verificar que match ocorre com score menor.
- **Resultado esperado**: Regra genérica retornada como fallback.

### T4.6 — buscar_regras_item: nenhum match
- **Cenário**: Item com hierarquia sem nenhuma regra correspondente.
- **Estrutura do teste**: Criar item com hierarquia "XYZ" sem regras. Verificar lista vazia.
- **Resultado esperado**: Lista vazia (sem match).

### T4.7 — buscar_regras_item: múltiplos colaboradores para mesma hierarquia
- **Cenário**: Dois colaboradores (Gerente + Coordenador) com regras para mesma hierarquia.
- **Estrutura do teste**: Criar 2 regras (diferentes cargos) para mesma hierarquia. Verificar que ambos são retornados.
- **Resultado esperado**: Lista com 2 entradas (um por colaborador).

### T4.8 — buscar_taxa_para_cargo: taxa encontrada
- **Cenário**: Buscar taxa de "Gerente de Linha" para hierarquia específica.
- **Estrutura do teste**: Criar regra com cargo e taxa. Chamar `buscar_taxa_para_cargo()`. Verificar taxa retornada.
- **Resultado esperado**: Taxa correta (ex: 0.5%).

### T4.9 — buscar_taxa_para_cargo: cargo sem regra
- **Cenário**: Buscar taxa de "Diretor" para hierarquia onde não há regra de Diretor.
- **Estrutura do teste**: Chamar sem regra correspondente. Verificar retorno None ou 0.
- **Resultado esperado**: None (sem taxa).

### T4.10 — colaborador_tem_atribuicao: verificação positiva e negativa
- **Cenário**: Verificar se "MARIA" tem atribuição para hierarquia X (sim) e hierarquia Y (não).
- **Estrutura do teste**: Criar regras para MARIA em hierarquia X. Testar ambas.
- **Resultado esperado**: True para X, False para Y.

### T4.11 — validar_cobertura_hierarquias: hierarquia sem gerente
- **Cenário**: Hierarquia "ELETRICA > MOTORES" sem nenhum Gerente de Linha atribuído.
- **Estrutura do teste**: Criar dados comerciais com essa hierarquia e regras sem Gerente para ela. Chamar validação.
- **Resultado esperado**: Warning/erro indicando hierarquia sem cobertura.

### T4.12 — buscar_regras_item: campos com wildcard "[Todos]"
- **Cenário**: Regra com campo grupo="[Todos os grupos]" deve dar match com qualquer grupo.
- **Estrutura do teste**: Criar regra com wildcard. Testar com diferentes valores de grupo.
- **Resultado esperado**: Match em todos os casos.

### T4.13 — resolver_empate_terminal: empate entre regras de mesma especificidade
- **Cenário**: Duas regras com score idêntico para mesmo item — requer resolução.
- **Estrutura do teste**: Criar 2 regras com mesma especificidade. Verificar que o sistema detecta empate.
- **Resultado esperado**: Solicitação de resolução (terminal) ou erro controlado.

### T4.14 — especificidade: score correto com 6 campos
- **Cenário**: Regra com todos 6 campos (linha, grupo, subgrupo, tipo_mercadoria, fabricante, aplicacao) preenchidos → score=6.
- **Estrutura do teste**: Criar regra completa. Verificar cálculo de score.
- **Resultado esperado**: Score = 6.

### T4.15 — especificidade: score com campos parciais
- **Cenário**: Regra com apenas linha e fabricante → score=2.
- **Estrutura do teste**: Criar regra parcial. Verificar score.
- **Resultado esperado**: Score = 2.

---

## 5. Módulo: Lookup Hierárquico de Metas

**Arquivo**: `calculo_comissoes.py` (método `_get_meta`)

### T5.1 — Meta encontrada no nível mais específico (linha + grupo + subgrupo)
- **Cenário**: Meta definida para HIDROLOGIA > QED > BOMBAS = R$ 500.000.
- **Estrutura do teste**: Criar DataFrame de metas com entrada específica. Chamar `_get_meta("faturamento", "HIDROLOGIA", "QED", "BOMBAS")`.
- **Resultado esperado**: R$ 500.000.

### T5.2 — Fallback nível 2: linha + grupo
- **Cenário**: Sem meta para subgrupo, mas existe para HIDROLOGIA > QED.
- **Estrutura do teste**: Criar meta apenas para linha+grupo. Buscar com subgrupo inexistente.
- **Resultado esperado**: Meta do nível linha+grupo.

### T5.3 — Fallback nível 3: linha apenas
- **Cenário**: Sem meta específica por grupo, mas existe para HIDROLOGIA.
- **Estrutura do teste**: Criar meta apenas para linha. Buscar com grupo inexistente.
- **Resultado esperado**: Meta da linha.

### T5.4 — Fallback nível 4: meta global
- **Cenário**: Nenhuma meta hierárquica, existe meta global/default.
- **Estrutura do teste**: Criar apenas meta global. Buscar qualquer hierarquia.
- **Resultado esperado**: Meta global.

### T5.5 — Sem meta em nenhum nível
- **Cenário**: Nenhuma meta definida para a hierarquia em nenhum nível.
- **Estrutura do teste**: DataFrame de metas vazio ou sem match. Buscar hierarquia.
- **Resultado esperado**: 0 ou None (sem meta).

### T5.6 — Meta de rentabilidade (4 níveis: linha+grupo+subgrupo+tipo_mercadoria)
- **Cenário**: Meta de rentabilidade usa 4 campos em vez de 3.
- **Estrutura do teste**: Criar meta de rentabilidade com 4 campos. Verificar lookup com fallback.
- **Resultado esperado**: Meta correta no nível mais específico disponível.

### T5.7 — Meta individual vs meta de linha
- **Cenário**: Colaborador tem meta individual de faturamento que sobrepõe meta da linha.
- **Estrutura do teste**: Criar meta individual para "JOAO" na hierarquia X. Verificar que _get_meta retorna a individual.
- **Resultado esperado**: Meta individual priorizada.

### T5.8 — Metas de aplicação (grupo + subgrupo)
- **Cenário**: Meta definida por Aplicação Mat./Serv. → grupo+subgrupo.
- **Estrutura do teste**: Criar METAS_APLICACAO com grupo+subgrupo. Verificar lookup.
- **Resultado esperado**: Meta da aplicação encontrada.

---

## 6. Módulo: Cálculo do FC (Fator de Correção)

**Arquivo**: `calculo_comissoes.py` (método `_calcular_fc_para_item`)

### T6.1 — FC com todos componentes no peso correto
- **Cenário**: PESOS_METAS define: faturamento_linha=30%, conversao_linha=20%, faturamento_individual=15%, conversao_individual=15%, rentabilidade=10%, retencao_clientes=10%. Todos atingimentos = 100%.
- **Estrutura do teste**: Mock de dados com todos atingimentos=1.0. Verificar FC resultante = 1.0.
- **Resultado esperado**: FC = 1.0 (todos 100%).

### T6.2 — FC com atingimento parcial em faturamento_linha
- **Cenário**: faturamento_linha com atingimento=80% (peso=40%), demais 100%.
- **Estrutura do teste**: Mock com faturamento_linha.realizado = 80k, meta = 100k. Calcular FC.
- **Resultado esperado**: FC = (0.8×0.4 + 1.0×0.6) = 0.92.

### T6.3 — FC com cap_atingimento_max
- **Cenário**: Atingimento de 200% mas cap_atingimento_max = 150%.
- **Estrutura do teste**: Realizado=200k, Meta=100k, cap=1.5. Verificar que atingimento é limitado a 1.5.
- **Resultado esperado**: Atingimento capped em 1.5.

### T6.4 — FC com cap_fc_max
- **Cenário**: FC calculado seria 1.8 mas cap_fc_max = 1.5.
- **Estrutura do teste**: Configurar componentes para FC > 1.5 com cap=1.5.
- **Resultado esperado**: FC final = 1.5 (capped).

### T6.5 — FC com componente de peso zero
- **Cenário**: Componente rentabilidade com peso=0% (desabilitado).
- **Estrutura do teste**: Peso rentabilidade=0. Verificar que não influencia FC.
- **Resultado esperado**: Componente ignorado no cálculo.

### T6.6 — FC com meta zero em um componente
- **Cenário**: Meta de conversão = 0 → atingimento default = 1.0 (100%).
- **Estrutura do teste**: Meta=0 para conversao_linha. Verificar atingimento=1.0.
- **Resultado esperado**: Atingimento = 1.0 (sem penalidade por meta inexistente).

### T6.7 — FC com realizado zero
- **Cenário**: Nenhum faturamento realizado no mês → atingimento=0.
- **Estrutura do teste**: Realizado=0 para todos componentes. Verificar FC.
- **Resultado esperado**: FC = 0 (ou mínimo se houver piso).

### T6.8 — FC: validação de pesos somando 100%
- **Cenário**: Pesos que não somam 100% devem gerar erro de validação.
- **Estrutura do teste**: PESOS_METAS com soma=90%. Chamar validação.
- **Resultado esperado**: Erro: "Pesos não somam 100%".

### T6.9 — FC com componente meta_fornecedor_1
- **Cenário**: Meta de fornecedor definida em USD. Realizado convertido via taxa BCB.
- **Estrutura do teste**: Meta_fornecedor=100k USD, realizado=80k BRL, taxa=5.0 → realizado_convertido=16k USD → atingimento=0.16.
- **Resultado esperado**: Atingimento calculado com conversão cambial.

### T6.10 — FC com componente meta_fornecedor_2
- **Cenário**: Segundo meta de fornecedor (outro fabricante).
- **Estrutura do teste**: Similar ao T6.9 para segundo fornecedor.
- **Resultado esperado**: Componente calculado independentemente.

### T6.11 — FC: componente retencao_clientes
- **Cenário**: Gerente de Linha com retenção calculada (clientes mantidos vs período anterior).
- **Estrutura do teste**: Mock de dados de retenção com atingimento=0.9. Verificar peso correto no FC.
- **Resultado esperado**: Componente retencao_clientes com atingimento=0.9.

### T6.12 — FC: colaborador sem algum componente configurado
- **Cenário**: Colaborador não tem meta_fornecedor → componente ignorado, peso redistribuído.
- **Estrutura do teste**: Configurar sem meta_fornecedor. Verificar que demais pesos compensam.
- **Resultado esperado**: FC calculado apenas com componentes disponíveis.

---

## 7. Módulo: FC Escada / Rampa

**Arquivo**: `src/core/fc_escada.py`

### T7.1 — Modo ESCADA: FC no primeiro degrau (piso)
- **Cenário**: FC=0.5, num_degraus=5, piso=0.7. Degrau 1 = multiplicador mínimo.
- **Estrutura do teste**: Chamar `aplicar_fc_escada(fc=0.1, config=ESCADA(5, 0.7))`.
- **Resultado esperado**: Multiplicador = piso (0.7).

### T7.2 — Modo ESCADA: FC no último degrau (topo)
- **Cenário**: FC >= 1.0, degrau máximo → multiplicador = 1.0.
- **Estrutura do teste**: `aplicar_fc_escada(fc=1.2, config=ESCADA(5, 0.7))`.
- **Resultado esperado**: Multiplicador = 1.0.

### T7.3 — Modo ESCADA: FC intermediário
- **Cenário**: FC=0.6 com 5 degraus. Calcular degrau correto.
- **Estrutura do teste**: `aplicar_fc_escada(fc=0.6, config=ESCADA(5, 0.7))`. Fórmula: `piso + (i × (1.0 - piso) / (n - 1))`.
- **Resultado esperado**: Multiplicador do degrau correspondente.

### T7.4 — Modo RAMPA: interpolação linear
- **Cenário**: FC=0.75 → multiplicador = interpolação linear entre piso e 1.0.
- **Estrutura do teste**: `aplicar_fc_escada(fc=0.75, config=RAMPA(piso=0.5))`.
- **Resultado esperado**: Multiplicador proporcional (ex: 0.5 + 0.75 × (1.0 - 0.5) = 0.875).

### T7.5 — Modo RAMPA: FC >= 1.0
- **Cenário**: FC=1.3 no modo RAMPA.
- **Estrutura do teste**: Verificar que multiplicador = 1.0 (capped).
- **Resultado esperado**: Multiplicador = 1.0.

### T7.6 — Modo RAMPA: FC = 0
- **Cenário**: FC=0 → multiplicador = piso.
- **Estrutura do teste**: `aplicar_fc_escada(fc=0, config=RAMPA(piso=0.6))`.
- **Resultado esperado**: Multiplicador = piso (0.6).

### T7.7 — Cargo sem configuração de escada
- **Cenário**: Cargo não presente na aba FC_ESCADA_CARGOS → FC usado diretamente (sem escada).
- **Estrutura do teste**: Chamar sem config de escada para o cargo.
- **Resultado esperado**: FC original mantido (bypass da escada).

### T7.8 — load_fc_escada_cargos: carregar configuração
- **Cenário**: Aba FC_ESCADA_CARGOS com 3 cargos configurados.
- **Estrutura do teste**: Criar DataFrame com cargos e params. Chamar loader.
- **Resultado esperado**: Dict[cargo → FcEscadaCargoConfig].

### T7.9 — ESCADA com 2 degraus (mínimo)
- **Cenário**: Apenas 2 degraus (binário: piso ou 1.0).
- **Estrutura do teste**: Config com num_degraus=2. Testar FC < 0.5 e FC >= 0.5.
- **Resultado esperado**: Degrau 0 → piso, Degrau 1 → 1.0.

### T7.10 — ESCADA com num_degraus = 1
- **Cenário**: Edge case com apenas 1 degrau → sempre multiplicador = 1.0.
- **Estrutura do teste**: Config com num_degraus=1.
- **Resultado esperado**: Multiplicador = 1.0 sempre.

---

## 8. Módulo: Cálculo de Atingimento

**Arquivo**: `src/utils/normalization.py` (função `calcular_atingimento`)

> Testes já cobertos em T1.5–T1.10. Esta seção adiciona cenários complementares.

### T8.1 — Atingimento com valores float de precisão
- **Cenário**: Realizado=33333.33, Meta=100000 → atingimento deve preservar precisão.
- **Estrutura do teste**: Verificar que resultado é `pytest.approx(0.3333333)`.
- **Resultado esperado**: Precisão float preservada.

### T8.2 — Atingimento com valores muito grandes
- **Cenário**: Realizado=999999999, Meta=1000000000.
- **Estrutura do teste**: Verificar cálculo sem overflow.
- **Resultado esperado**: 0.999999999.

---

## 9. Módulo: Cálculo de Comissão por Faturamento (V1)

**Arquivo**: `calculo_comissoes.py`

### T9.1 — Comissão básica por faturamento
- **Cenário**: Item faturado R$ 100.000, taxa=1%, FC=1.0, fator_split=1.0.
- **Estrutura do teste**: `comissao = 100000 × 0.01 × 1.0 × 1.0 = R$ 1.000`.
- **Resultado esperado**: R$ 1.000,00.

### T9.2 — Comissão com fator_split (rateio entre colaboradores)
- **Cenário**: 2 Gerentes com split 60/40. Item R$ 100.000, taxa=1%, FC=1.0.
- **Estrutura do teste**: Gerente A: `100000 × 0.01 × 1.0 × 0.6 = 600`. Gerente B: `100000 × 0.01 × 1.0 × 0.4 = 400`.
- **Resultado esperado**: A=R$ 600, B=R$ 400.

### T9.3 — Comissão com FC < 1 (penalização)
- **Cenário**: FC=0.7 penaliza comissão. Item R$ 100.000, taxa=1%.
- **Estrutura do teste**: `100000 × 0.01 × 0.7 = R$ 700`.
- **Resultado esperado**: R$ 700,00.

### T9.4 — Comissão com FC > 1 (bonificação)
- **Cenário**: FC=1.3 (superou metas). Item R$ 50.000, taxa=0.5%.
- **Estrutura do teste**: `50000 × 0.005 × 1.3 = R$ 325`.
- **Resultado esperado**: R$ 325,00.

### T9.5 — Cross-selling: item vendido em linha diferente
- **Cenário**: Consultor de "HIDROLOGIA" vendeu item de "ELÉTRICA" → tratamento especial.
- **Estrutura do teste**: Criar item com linha diferente da linha do colaborador. Verificar regra de cross-selling.
- **Resultado esperado**: Comissão calculada conforme regra de cross-selling.

### T9.6 — Taxa de rateio por cargo (fatia_cargo)
- **Cenário**: Cargo "Consultor Interno" tem fatia=60% do comissionamento do item.
- **Estrutura do teste**: Faturamento=100k, taxa_total=2%, fatia_cargo=0.6 → `100k × 0.02 × 0.6 = R$ 1.200`.
- **Resultado esperado**: R$ 1.200.

### T9.7 — Item com Status diferente de FATURADO
- **Cenário**: Item com Status="CANCELADO" não deve gerar comissão.
- **Estrutura do teste**: Incluir item cancelado nos dados. Verificar que é filtrado.
- **Resultado esperado**: Comissão = 0 (item ignorado).

### T9.8 — Item com Operação inválida
- **Cenário**: Operação "XXXX" fora do set válido (FLOC, IMO2, OR19, P205, PSEM, PSER, SERV, PVEN, PVMA).
- **Estrutura do teste**: Item com operação inválida. Verificar filtragem.
- **Resultado esperado**: Item excluído do cálculo.

### T9.9 — Múltiplos itens no mesmo processo
- **Cenário**: Processo com 5 itens de diferentes hierarquias, cada um com taxa/FC diferente.
- **Estrutura do teste**: Criar 5 itens. Verificar que cada item tem cálculo independente.
- **Resultado esperado**: Comissão total = soma das comissões individuais.

### T9.10 — Item com valor faturado zero
- **Cenário**: Item com Valor Realizado = 0.
- **Estrutura do teste**: Criar item com valor 0.
- **Resultado esperado**: Comissão = 0.

### T9.11 — Item com valor faturado negativo
- **Cenário**: Nota de crédito com valor negativo.
- **Estrutura do teste**: Criar item com valor < 0.
- **Resultado esperado**: Tratamento adequado (ignorar ou comissão negativa conforme regra).

### T9.12 — Cálculo de realizado agregado por linha
- **Cenário**: Somatório de faturamento da linha "HIDROLOGIA" para cálculo de FC.
- **Estrutura do teste**: 3 itens da mesma linha com valores diferentes. Verificar soma correta.
- **Resultado esperado**: Realizado_linha = soma dos 3 itens.

### T9.13 — Cálculo de realizado individual (por colaborador)
- **Cenário**: Faturamento individual do "JOAO" em todas as linhas.
- **Estrutura do teste**: Filtrar itens onde JOAO é consultor. Somar valores.
- **Resultado esperado**: Realizado_individual correto.

---

## 10. Módulo: Retenção de Clientes

**Arquivo**: `calculo_comissoes.py` (método `_calcular_retencao_clientes`)

### T10.1 — Retenção 100%: todos clientes mantidos
- **Cenário**: 50 clientes únicos no período anterior, 50 mantidos no período atual.
- **Estrutura do teste**: Mock de 24 meses de dados com todos clientes presentes. Atingimento=1.0.
- **Resultado esperado**: Retenção = 1.0 (100%).

### T10.2 — Retenção parcial: perda de clientes
- **Cenário**: 100 clientes antes, 80 mantidos → retenção = 0.8.
- **Estrutura do teste**: Mock com 20 clientes ausentes no período atual.
- **Resultado esperado**: Retenção = 0.8.

### T10.3 — Retenção com novos clientes (não contam)
- **Cenário**: 50 clientes antes, 50 mantidos + 20 novos. Novos NÃO contam para retenção.
- **Estrutura do teste**: Adicionar clientes novos. Verificar que retenção continua 1.0 (baseada apenas nos antigos).
- **Resultado esperado**: Retenção = 1.0 (novos ignorados).

### T10.4 — Retenção: janela de 24 meses
- **Cenário**: Usar dados de 24 meses atrás até 12 meses atrás como "período anterior", e últimos 12 meses como "período atual".
- **Estrutura do teste**: Verificar que a janela correta é utilizada.
- **Resultado esperado**: Períodos corretos na comparação.

### T10.5 — Retenção: aplicável apenas a Gerente de Linha
- **Cenário**: Componente retencao_clientes só se aplica a cargos de gestão (Gerente de Linha).
- **Estrutura do teste**: Calcular FC para Consultor Interno → sem componente retenção.
- **Resultado esperado**: Componente ausente para cargos não-gestão.

### T10.6 — Retenção: sem histórico suficiente (< 24 meses)
- **Cenário**: Empresa nova, dados de apenas 6 meses.
- **Estrutura do teste**: Mock com poucos meses de dados.
- **Resultado esperado**: Retenção = 1.0 (default) ou tratamento gracioso.

---

## 11. Módulo: Conversão Cambial (Metas Fornecedores)

**Arquivo**: `src/currency/rate_calculator.py`

### T11.1 — Conversão BRL → USD com taxa mensal
- **Cenário**: Faturamento BRL=500.000, taxa média do mês=5.0 → USD=100.000.
- **Estrutura do teste**: Mock de taxa BCB. Chamar `calcular_faturamento_convertido_ytd()`.
- **Resultado esperado**: 100.000 USD.

### T11.2 — Conversão YTD (acumulado no ano)
- **Cenário**: Jan=100k, Fev=120k, Mar=80k BRL com taxas diferentes por mês.
- **Estrutura do teste**: 3 meses de dados com taxas: 5.0, 5.2, 4.8. Verificar soma convertida.
- **Resultado esperado**: (100k/5.0 + 120k/5.2 + 80k/4.8) = total YTD em USD.

### T11.3 — Taxa de câmbio não disponível
- **Cenário**: Mês sem taxa armazenada no JSON.
- **Estrutura do teste**: Chamar sem taxa para o mês.
- **Resultado esperado**: Fallback ou erro indicando taxa ausente.

### T11.4 — Múltiplos fornecedores com moedas diferentes
- **Cenário**: Fornecedor A em USD, Fornecedor B em EUR.
- **Estrutura do teste**: Configurar metas em moedas diferentes. Verificar conversão correta para cada.
- **Resultado esperado**: Conversões independentes por moeda.

### T11.5 — Faturamento YTD filtrado por fabricante
- **Cenário**: Faturamento total do ano filtrado apenas pelo fabricante da meta.
- **Estrutura do teste**: Criar Faturados_YTD com múltiplos fabricantes. Filtrar por um.
- **Resultado esperado**: Soma apenas do fabricante específico.

---

## 12. Módulo: Devoluções

**Arquivo**: `src/devolucao/devolucao_processor.py`, `devolucao_calculator.py`, `devolucao_loader.py`

### T12.1 — Carregar devoluções: filtro por mês/ano
- **Cenário**: Arquivo com devoluções de vários meses. Filtrar apenas mês 10/2025.
- **Estrutura do teste**: Criar DataFrame com datas variadas. Chamar loader com mes=10, ano=2025.
- **Resultado esperado**: Apenas registros de outubro/2025.

### T12.2 — Carregar devoluções: remoção de Num docorigem vazio
- **Cenário**: Linhas com Num docorigem vazio ou NaN.
- **Estrutura do teste**: Incluir linhas com docorigem vazio. Verificar remoção.
- **Resultado esperado**: Linhas sem docorigem removidas.

### T12.3 — Carregar devoluções: valor <= 0 removido
- **Cenário**: Devoluções com Valor Produtos = 0 ou negativo.
- **Estrutura do teste**: Incluir linhas com valor 0 e negativo. Verificar remoção.
- **Resultado esperado**: Apenas devoluções com valor > 0.

### T12.4 — Carregar devoluções: agrupamento por NF
- **Cenário**: Múltiplas linhas com mesma NF (itens diferentes) → soma de valores.
- **Estrutura do teste**: 3 linhas com NF="12345", valores 100, 200, 300.
- **Resultado esperado**: NF="12345" com Valor=600.

### T12.5 — Calcular fator_devolucao: caso normal
- **Cenário**: Valor devolvido=30.000, realizado=100.000 → fator=0.3.
- **Estrutura do teste**: `calcular_fator_devolucao(30000, 100000)` → `0.3`.
- **Resultado esperado**: 0.3.

### T12.6 — Calcular fator_devolucao: cap em 1.0
- **Cenário**: Devolvido > realizado → fator capped em 1.0.
- **Estrutura do teste**: `calcular_fator_devolucao(150000, 100000)` → `1.0`.
- **Resultado esperado**: 1.0 (nunca > 100%).

### T12.7 — Calcular fator_devolucao: realizado = 0
- **Cenário**: Nenhum realizado para o processo.
- **Estrutura do teste**: `calcular_fator_devolucao(5000, 0)`.
- **Resultado esperado**: 0 ou tratamento de divisão por zero.

### T12.8 — Calcular estorno proporcional por colaborador
- **Cenário**: Processo com 2 colaboradores: JOAO (comissão=1000), MARIA (comissão=500). Devolução de 50% → estornos proporcionais.
- **Estrutura do teste**: `calcular_estorno_processo()` com fator=0.5.
- **Resultado esperado**: JOAO=-500, MARIA=-250.

### T12.9 — Link NF → Processo via Análise Comercial
- **Cenário**: NF da devolução encontrada na AC vinculada ao processo "P12345".
- **Estrutura do teste**: Criar AC com NF="999" → Processo="P12345". Devolução com docorigem="999".
- **Resultado esperado**: Devolução vinculada ao processo P12345.

### T12.10 — Devolução sem NF correspondente na AC
- **Cenário**: NF da devolução não encontrada em nenhum processo.
- **Estrutura do teste**: NF inexistente na AC.
- **Resultado esperado**: Devolução ignorada (warning).

### T12.11 — Devolução sem comissões históricas no Master DB
- **Cenário**: Processo encontrado mas sem comissões no histórico.
- **Estrutura do teste**: Processo existe na AC mas não no Master DB.
- **Resultado esperado**: Estorno = 0 (nada a estornar).

### T12.12 — Salvar estornos no Master DB
- **Cenário**: Estornos calculados devem ser persistidos como tipo DEVOLUCAO.
- **Estrutura do teste**: Processar devolução completa. Verificar que Master DB recebe registros tipo DEVOLUCAO.
- **Resultado esperado**: Registros com valores negativos salvos.

---

## 13. Módulo: Recebimento — Process Mapper

**Arquivo**: `src/recebimento/core/process_mapper.py`

### T13.1 — Documento COT → Adiantamento
- **Cenário**: Documento com prefixo "COT" (ex: "COT-12345") mapeado como adiantamento.
- **Estrutura do teste**: `mapear_documento("COT-12345")` → tipo=ADIANTAMENTO, processo=sufixo.
- **Resultado esperado**: Tipo adiantamento, processo extraído do sufixo.

### T13.2 — Documento regular → NF lookup
- **Cenário**: Documento "ABC123456XYZ" → extrai 6 primeiros dígitos → busca NF na AC.
- **Estrutura do teste**: Documento com dígitos. Mock da AC com NF correspondente.
- **Resultado esperado**: Processo encontrado via NF.

### T13.3 — Documento COT associado a processo FATURADO → erro
- **Cenário**: COT referencia processo que já está FATURADO → inconsistência.
- **Estrutura do teste**: Criar COT para processo com status FATURADO.
- **Resultado esperado**: Erro/warning: COT não pode ser adiantamento para processo já faturado.

### T13.4 — Documento sem dígitos suficientes
- **Cenário**: Documento "AB12" com menos de 6 dígitos.
- **Estrutura do teste**: Mapear documento curto.
- **Resultado esperado**: Documento não mapeado (erro controlado).

### T13.5 — NF com zeros à esquerda
- **Cenário**: NF="000123" na AC, documento extraído="123" → normalização com zero-padding.
- **Estrutura do teste**: NF com zeros na AC. Documento sem zeros. Verificar match.
- **Resultado esperado**: Match via normalização de zeros.

### T13.6 — Documento não encontrado em nenhum processo
- **Cenário**: Dígitos extraídos não correspondem a nenhuma NF.
- **Estrutura do teste**: Documento sem match.
- **Resultado esperado**: Mapeamento falha (warning, documento ignorado).

---

## 14. Módulo: Recebimento — Identificador de Colaboradores

**Arquivo**: `src/recebimento/core/identificador_colaboradores.py`

### T14.1 — Identificar colaboradores operacionais (Consultor Interno + Representante-pedido)
- **Cenário**: Processo com Consultor Interno="JOAO" e Representante-pedido="MARIA", ambos recebem por recebimento.
- **Estrutura do teste**: Criar AC com ambas colunas preenchidas. Set recebimento contendo ambos.
- **Resultado esperado**: Lista com JOAO e MARIA.

### T14.2 — Identificar colaboradores de gestão via REGRAS_ATRIBUICAO
- **Cenário**: Hierarquia do processo tem Gerente "CARLOS" configurado em REGRAS_ATRIBUICAO.
- **Estrutura do teste**: Criar regras com CARLOS para hierarquia do item. Set recebimento contendo CARLOS.
- **Resultado esperado**: CARLOS incluído na lista.

### T14.3 — Filtrar apenas quem recebe por recebimento
- **Cenário**: JOAO recebe por faturamento (não por recebimento) → excluído.
- **Estrutura do teste**: JOAO não está no set `recebe_por_recebimento_ids`.
- **Resultado esperado**: JOAO não aparece na lista.

### T14.4 — Processo inexistente na AC
- **Cenário**: Processo "P99999" não encontrado na Análise Comercial.
- **Estrutura do teste**: Chamar com processo inexistente.
- **Resultado esperado**: Lista vazia.

### T14.5 — Colaborador com nome NaN/None/vazio
- **Cenário**: Coluna Consultor Interno com valor NaN em algum item.
- **Estrutura do teste**: Item com NaN no consultor. Verificar que é ignorado.
- **Resultado esperado**: NaN excluído da lista.

### T14.6 — Deduplicação de colaboradores
- **Cenário**: JOAO aparece como Consultor Interno E Representante-pedido no mesmo processo.
- **Estrutura do teste**: Ambas colunas com "JOAO".
- **Resultado esperado**: JOAO aparece apenas 1 vez.

### T14.7 — Obter cargo do colaborador
- **Cenário**: JOAO com cargo "Consultor Interno" no DataFrame de colaboradores.
- **Estrutura do teste**: Mock colaboradores_df com JOAO. Verificar cargo retornado.
- **Resultado esperado**: cargo = "Consultor Interno".

### T14.8 — Colaborador sem cargo definido
- **Cenário**: JOAO não encontrado no DataFrame de colaboradores.
- **Estrutura do teste**: colaboradores_df sem JOAO.
- **Resultado esperado**: cargo = "N/A".

---

## 15. Módulo: Recebimento — Métricas (TCMP / FCMP)

**Arquivo**: `src/recebimento/core/metricas_calculator.py`

### T15.1 — TCMP: média ponderada de taxas
- **Cenário**: 3 itens no processo: Item1 (valor=60k, taxa=1%), Item2 (valor=30k, taxa=2%), Item3 (valor=10k, taxa=0.5%).
- **Estrutura do teste**: `TCMP = (60k×0.01 + 30k×0.02 + 10k×0.005) / (60k+30k+10k) = (600+600+50)/100000 = 0.0125 = 1.25%`.
- **Resultado esperado**: TCMP = 1.25%.

### T15.2 — FCMP: média ponderada de FCs
- **Cenário**: 3 itens: Item1 (valor=60k, FC=0.9), Item2 (valor=30k, FC=1.1), Item3 (valor=10k, FC=0.8).
- **Estrutura do teste**: `FCMP = (60k×0.9 + 30k×1.1 + 10k×0.8) / (60k+30k+10k) = (54k+33k+8k)/100k = 0.95`.
- **Resultado esperado**: FCMP = 0.95.

### T15.3 — FCMP: aplicação da escada após cálculo
- **Cenário**: FCMP calculado=0.85, cargo tem FC_ESCADA configurado.
- **Estrutura do teste**: Calcular FCMP ponderado, depois aplicar escada.
- **Resultado esperado**: FCMP ajustado pela escada.

### T15.4 — FCMP forçado a 1.0 para processos não-FATURADO
- **Cenário**: Processo com status != "FATURADO" → FCMP = 1.0 (sem penalização).
- **Estrutura do teste**: Processo com status "EM ANDAMENTO". Verificar FCMP=1.0.
- **Resultado esperado**: FCMP = 1.0.

### T15.5 — Processo com único item
- **Cenário**: Processo com apenas 1 item → TCMP = taxa do item, FCMP = FC do item.
- **Estrutura do teste**: Processo com 1 item (taxa=1.5%, FC=0.9).
- **Resultado esperado**: TCMP=1.5%, FCMP=0.9.

### T15.6 — Processo com itens de valor zero
- **Cenário**: Alguns itens com valor=0 no processo.
- **Estrutura do teste**: Incluir item com valor 0. Verificar que não influencia média.
- **Resultado esperado**: Itens com valor 0 ignorados na ponderação.

### T15.7 — Métricas por colaborador
- **Cenário**: Cada colaborador pode ter FC diferente para o mesmo processo.
- **Estrutura do teste**: 2 colaboradores com taxas/FCs diferentes.
- **Resultado esperado**: TCMP e FCMP separados por colaborador.

### T15.8 — Cálculo de FC por item no contexto de recebimento
- **Cenário**: Para cada item do processo, calcular FC usando mesma lógica do faturamento.
- **Estrutura do teste**: Item com hierarquia e componentes. Verificar FC calculado.
- **Resultado esperado**: FC consistente com cálculo de faturamento.

---

## 16. Módulo: Recebimento — Cálculo de Comissão

**Arquivo**: `src/recebimento/core/comissao_calculator.py`

### T16.1 — Adiantamento (COT): comissão com FC=1.0
- **Cenário**: Pagamento COT de R$ 50.000. TCMP=1.5%. FC forçado = 1.0.
- **Estrutura do teste**: `calcular_adiantamento(50000, 0.015)` → `50000 × 0.015 × 1.0 = R$ 750`.
- **Resultado esperado**: R$ 750,00.

### T16.2 — Pagamento regular: comissão com FCMP
- **Cenário**: Pagamento regular de R$ 80.000. TCMP=1.2%. FCMP=0.9.
- **Estrutura do teste**: `calcular_regular(80000, 0.012, 0.9)` → `80000 × 0.012 × 0.9 = R$ 864`.
- **Resultado esperado**: R$ 864,00.

### T16.3 — Pagamento regular: FCMP <= 0 → fallback para 1.0
- **Cenário**: FCMP calculado como 0 ou negativo.
- **Estrutura do teste**: `calcular_regular(80000, 0.012, 0)` → usa FCMP=1.0.
- **Resultado esperado**: Comissão com FCMP=1.0 (fallback).

### T16.4 — Pagamento com TCMP zero
- **Cenário**: Nenhuma taxa encontrada → TCMP=0.
- **Estrutura do teste**: `calcular_regular(80000, 0, 0.9)`.
- **Resultado esperado**: Comissão = 0.

### T16.5 — Valor de pagamento zero
- **Cenário**: Documento com valor=0.
- **Estrutura do teste**: `calcular_adiantamento(0, 0.015)`.
- **Resultado esperado**: Comissão = 0.

---

## 17. Módulo: Recebimento — Reconciliação

**Arquivo**: `src/recebimento/reconciliacao/reconciliacao_calculator.py`

### T17.1 — Reconciliação positiva (FCMP > 1.0)
- **Cenário**: Comissão adiantada=R$ 1.000, FCMP=1.2 → ajuste = 1000 × (1.2 - 1.0) = R$ 200.
- **Estrutura do teste**: `calcular_reconciliacao_processo(1000, 1.2)` → `R$ 200`.
- **Resultado esperado**: Ajuste positivo (colaborador recebe mais).

### T17.2 — Reconciliação negativa (FCMP < 1.0)
- **Cenário**: Comissão adiantada=R$ 1.000, FCMP=0.8 → ajuste = 1000 × (0.8 - 1.0) = -R$ 200.
- **Estrutura do teste**: `calcular_reconciliacao_processo(1000, 0.8)` → `-R$ 200`.
- **Resultado esperado**: Ajuste negativo (colaborador deve devolver).

### T17.3 — Reconciliação zero (FCMP = 1.0)
- **Cenário**: FCMP=1.0 → sem ajuste necessário.
- **Estrutura do teste**: `calcular_reconciliacao_processo(1000, 1.0)` → `0`.
- **Resultado esperado**: Ajuste = 0.

### T17.4 — Reconciliação com comissão adiantada zero
- **Cenário**: Nenhuma comissão adiantada → nenhum ajuste.
- **Estrutura do teste**: `calcular_reconciliacao_processo(0, 1.5)` → `0`.
- **Resultado esperado**: Ajuste = 0.

### T17.5 — Múltiplos colaboradores: reconciliação individual
- **Cenário**: JOAO adiantou R$ 500, MARIA adiantou R$ 800. FCMP=0.9. Ajustes individuais.
- **Estrutura do teste**: Calcular reconciliação por colaborador.
- **Resultado esperado**: JOAO=-50, MARIA=-80.

---

## 18. Módulo: Recebimento — Orquestrador

**Arquivo**: `src/recebimento/recebimento_orchestrator.py`

### T18.1 — Fluxo completo de adiantamento (COT)
- **Cenário**: Documento COT recebido → mapear processo → identificar colaboradores → calcular TCMP → comissão = valor × TCMP × 1.0 → salvar estado.
- **Estrutura do teste**: Mock de todos componentes. Executar fluxo completo para COT.
- **Resultado esperado**: Comissão de adiantamento calculada e estado atualizado.

### T18.2 — Fluxo completo de pagamento regular
- **Cenário**: Pagamento regular → mapear NF → identificar colaboradores → obter TCMP/FCMP → comissão = valor × TCMP × FCMP → salvar.
- **Estrutura do teste**: Mock com processo FATURADO. Executar fluxo.
- **Resultado esperado**: Comissão regular calculada com FCMP aplicado.

### T18.3 — Processo com adiantamento seguido de faturamento → reconciliação
- **Cenário**: 1) COT recebido (FCMP=1.0), 2) Processo faturado (FCMP=0.85) → reconciliação necessária.
- **Estrutura do teste**: Simular sequência: adiantamento → faturamento → reconciliação.
- **Resultado esperado**: Ajuste = comissão_adiantada × (0.85 - 1.0).

### T18.4 — Processo já faturado recebendo pagamento regular
- **Cenário**: Processo FATURADO com TCMP/FCMP já calculados. Pagamento chega → usar métricas salvas.
- **Estrutura do teste**: Estado com métricas CALCULADO. Processar pagamento.
- **Resultado esperado**: Métricas do estado reutilizadas (sem recalcular).

### T18.5 — Múltiplos pagamentos no mesmo mês
- **Cenário**: 3 pagamentos para o mesmo processo no mesmo mês.
- **Estrutura do teste**: Processar 3 documentos para mesmo processo.
- **Resultado esperado**: Comissões acumuladas, estado atualizado cumulativamente.

### T18.6 — Salvar no Master DB (adiantamentos + regulares + reconciliações)
- **Cenário**: Todos os tipos de comissão devem ser persistidos separadamente.
- **Estrutura do teste**: Verificar chamadas ao Master DB com tipos corretos.
- **Resultado esperado**: 3 tipos de registros salvos.

### T18.7 — Processo sem colaboradores de recebimento
- **Cenário**: Nenhum colaborador do processo recebe por recebimento.
- **Estrutura do teste**: Set recebimento vazio para o processo.
- **Resultado esperado**: Nenhuma comissão calculada, documento ignorado.

### T18.8 — Documento já processado (deduplicação)
- **Cenário**: Mesmo documento processado duas vezes.
- **Estrutura do teste**: Processar documento, depois processar novamente.
- **Resultado esperado**: Sem duplicação (idempotência).

---

## 19. Módulo: Recebimento — State Manager

**Arquivo**: `src/recebimento/estado/state_manager.py`

### T19.1 — Criar novo processo com defaults
- **Cenário**: Processo "P123" não existe no estado → criar com valores iniciais.
- **Estrutura do teste**: `criar_processo("P123", status="EM ANDAMENTO")`. Verificar valores default.
- **Resultado esperado**: Novo registro com TOTAL_PAGO=0, STATUS=criado.

### T19.2 — SALDO_A_RECEBER: definido apenas para FATURADO
- **Cenário**: Processo FATURADO com valor_total=100k → SALDO=100k. Processo não-FATURADO → SALDO=None.
- **Estrutura do teste**: Criar processos com status diferentes. Verificar SALDO.
- **Resultado esperado**: SALDO só preenchido para FATURADO.

### T19.3 — Atualizar pagamento de adiantamento
- **Cenário**: Adiantamento de R$ 10k → TOTAL_ANTECIPACOES += 10k.
- **Estrutura do teste**: `atualizar_pagamento_adiantamento("P123", 10000)`. Verificar acumulação.
- **Resultado esperado**: TOTAL_ANTECIPACOES = 10000.

### T19.4 — Atualizar pagamento regular com saldo
- **Cenário**: Pagamento regular R$ 30k → TOTAL_PAGAMENTOS_REGULARES += 30k, SALDO_A_RECEBER -= 30k.
- **Estrutura do teste**: Processo FATURADO com SALDO=100k. Pagar 30k. Verificar saldo.
- **Resultado esperado**: SALDO = 70k.

### T19.5 — STATUS_PAGAMENTO: COMPLETO quando total pago >= valor processo
- **Cenário**: Valor processo=100k, total pago=100k → COMPLETO.
- **Estrutura do teste**: Pagar valor total. Verificar status.
- **Resultado esperado**: STATUS_PAGAMENTO = "COMPLETO".

### T19.6 — Salvar e carregar métricas (TCMP/FCMP) como JSON
- **Cenário**: TCMP/FCMP armazenados como JSON string no estado.
- **Estrutura do teste**: Salvar métricas, recarregar, verificar deserialização.
- **Resultado esperado**: Métricas preservadas após save/load.

### T19.7 — Status PARCIAL vs CALCULADO das médias
- **Cenário**: Adiantamento → status=PARCIAL. Faturamento → status=CALCULADO.
- **Estrutura do teste**: Salvar via `salvar_metricas` (PARCIAL) vs `definir_metricas` (CALCULADO).
- **Resultado esperado**: Status correto em cada caso.

### T19.8 — Armazenar e recuperar comissões adiantadas por colaborador
- **Cenário**: JOAO=500, MARIA=300 acumulados como JSON.
- **Estrutura do teste**: Armazenar comissões. Recuperar. Verificar valores.
- **Resultado esperado**: Dict{"JOAO": 500, "MARIA": 300}.

### T19.9 — Carregar estado anterior de arquivo Excel
- **Cenário**: Arquivo com aba "ESTADO" de mês anterior.
- **Estrutura do teste**: Criar Excel com aba ESTADO. Carregar.
- **Resultado esperado**: Estado anterior restaurado.

### T19.10 — Salvar estado para arquivo Excel
- **Cenário**: Exportar estado atual para aba "ESTADO" em Excel.
- **Estrutura do teste**: Popular estado. Salvar. Recarregar. Comparar.
- **Resultado esperado**: Dados preservados (round-trip).

---

## 20. Módulo: Recebimento — Analise Financeira Loader

**Arquivo**: `src/recebimento/io/analise_financeira_loader.py`

### T20.1 — Filtro por Tipo de Baixa = 'B'
- **Cenário**: Arquivo com tipos A, B, C. Apenas B deve ser carregado.
- **Estrutura do teste**: DataFrame com 3 tipos. Verificar filtro.
- **Resultado esperado**: Apenas registros com tipo 'B'.

### T20.2 — Filtro por mês/ano da Data de Baixa
- **Cenário**: Dados de jan/2025 a dez/2025. Filtrar apenas out/2025.
- **Estrutura do teste**: DataFrame com datas variadas. Filtrar mes=10, ano=2025.
- **Resultado esperado**: Apenas outubro/2025.

### T20.3 — Filtro por Valor Líquido > 0
- **Cenário**: Valores zero e negativos devem ser removidos.
- **Estrutura do teste**: Incluir valores 0, -100, 500. Verificar.
- **Resultado esperado**: Apenas 500 permanece.

### T20.4 — Documento como string (preservar zeros à esquerda)
- **Cenário**: Documento "00012345" deve manter zeros.
- **Estrutura do teste**: Carregar com `converters=str`. Verificar tipo string.
- **Resultado esperado**: "00012345" (não 12345).

### T20.5 — Arquivo não encontrado
- **Cenário**: Arquivo de análise financeira inexistente.
- **Estrutura do teste**: Caminho inválido.
- **Resultado esperado**: Exceção ou DataFrame vazio com warning.

### T20.6 — Colunas com acentos (Valor Líquido vs Valor Liquido)
- **Cenário**: Arquivo com acentos nos nomes de colunas.
- **Estrutura do teste**: Coluna "Valor Líquido" (com acento). Verificar busca case-insensitive.
- **Resultado esperado**: Coluna encontrada via normalização.

---

## 21. Módulo: Master DB Manager

**Arquivo**: `src/io/master_db_manager.py`

### T21.1 — Append de comissões com deduplicação (FATURAMENTO)
- **Cenário**: Inserir comissão FATURAMENTO. Inserir novamente → deve substituir (deduplicar por Processo+Colaborador+CodProduto+Tipo+Mes/Ano).
- **Estrutura do teste**: Inserir 1 registro. Inserir o mesmo. Verificar que DB tem apenas 1.
- **Resultado esperado**: Deduplicação por chave composta.

### T21.2 — Append de comissões REGULAR (deduplicação sem CodProduto)
- **Cenário**: Comissão REGULAR: deduplicação por Processo+Colaborador+Tipo+Mes/Ano (sem CodProduto).
- **Estrutura do teste**: Inserir REGULAR duplicada.
- **Resultado esperado**: Apenas 1 registro no DB.

### T21.3 — Backup automático antes de escrita
- **Cenário**: Antes de salvar, o manager cria backup do arquivo existente.
- **Estrutura do teste**: Verificar que backup é criado com timestamp.
- **Resultado esperado**: Arquivo de backup existe.

### T21.4 — Restauração em caso de falha de escrita
- **Cenário**: Erro durante salvamento → restaurar do backup.
- **Estrutura do teste**: Simular falha de IO. Verificar restauração.
- **Resultado esperado**: Arquivo original restaurado.

### T21.5 — Lock detection (arquivo aberto por outro programa)
- **Cenário**: Arquivo Excel aberto no Excel → lock detectado.
- **Estrutura do teste**: Simular lock de arquivo. Verificar que manager detecta.
- **Resultado esperado**: Erro indicando arquivo em uso.

### T21.6 — Integridade via hash
- **Cenário**: Hash calculado e armazenado ao salvar. Verificado ao carregar.
- **Estrutura do teste**: Salvar com hash. Alterar arquivo manualmente. Recarregar.
- **Resultado esperado**: Falha de integridade detectada.

### T21.7 — Schema completo (59 colunas)
- **Cenário**: DataFrame salvo deve ter todas 59 colunas padrão.
- **Estrutura do teste**: Inserir registro com poucas colunas. Verificar que colunas faltantes são preenchidas com None.
- **Resultado esperado**: 59 colunas presentes.

### T21.8 — Consulta com filtros (get_historico)
- **Cenário**: Filtrar por mês=10, ano=2025, tipo=FATURAMENTO, colaborador="JOAO".
- **Estrutura do teste**: Inserir vários registros. Consultar com filtros.
- **Resultado esperado**: Apenas registros matching.

### T21.9 — Resumo por colaborador (get_resumo_por_colaborador)
- **Cenário**: JOAO com 5 comissões totalizando R$ 3.000.
- **Estrutura do teste**: Inserir 5 registros para JOAO. Chamar resumo.
- **Resultado esperado**: Total = R$ 3.000.

### T21.10 — Metadados automáticos (Data_Execucao, Usuario_Execucao)
- **Cenário**: Ao inserir, metadados são preenchidos automaticamente.
- **Estrutura do teste**: Inserir registro. Verificar que Data_Execucao e Usuario estão preenchidos.
- **Resultado esperado**: Metadados presentes com valores corretos.

---

## 22. Módulo: Preparador de Dados Mensais

**Arquivo**: `preparar_dados_mensais.py`

### T22.1 — Filtrar dados ERP por mês/ano
- **Cenário**: Dados com datas de jan-dez/2025. Filtrar mês=10, ano=2025.
- **Estrutura do teste**: Mock com datas variadas. Chamar `run_preparador(10, 2025)`.
- **Resultado esperado**: Apenas dados de outubro/2025.

### T22.2 — Parsing de datas em múltiplos formatos
- **Cenário**: Datas em formato "DD/MM/YYYY", "YYYY-MM-DD", datetime objects.
- **Estrutura do teste**: Criar dados com cada formato. Verificar parsing correto.
- **Resultado esperado**: Todas datas parseadas corretamente.

### T22.3 — Dados vazios para o mês
- **Cenário**: Nenhum dado para mês solicitado.
- **Estrutura do teste**: DataFrame sem dados do mês 12/2025.
- **Resultado esperado**: Retorno False ou DataFrame vazio.

### T22.4 — Filtragem de operações válidas
- **Cenário**: Apenas operações do set válido devem ser mantidas.
- **Estrutura do teste**: Mix de operações válidas e inválidas.
- **Resultado esperado**: Apenas válidas no resultado.

---

## 23. Módulo: Metodologia V2 — Modelos

**Arquivo**: `src/metodo_v2/models_v2.py`

### T23.1 — FaixaComissao: condição simples (>= limite)
- **Cenário**: Faixa com limite_inferior=100000, taxa=1.5%.
- **Estrutura do teste**: `faixa.aplica_ao_faturamento(150000)` → True. `faixa.aplica_ao_faturamento(50000)` → False.
- **Resultado esperado**: Match correto.

### T23.2 — FaixaComissao: condição composta (>= e <)
- **Cenário**: Faixa com limite_inferior=100000 (>=) e limite_superior=200000 (<).
- **Estrutura do teste**: 90k → False. 150k → True. 200k → False.
- **Resultado esperado**: Faixa delimitada corretamente.

### T23.3 — FaixaComissao: operadores variados (>, <=)
- **Cenário**: Testar combinações de operadores: >, >=, <, <=.
- **Estrutura do teste**: Valores exatamente nos limites.
- **Resultado esperado**: Operadores respeitados.

### T23.4 — FaixaComissao: validação de limites negativos
- **Cenário**: Limite inferior negativo → erro de validação.
- **Estrutura do teste**: Criar faixa com limite_inferior=-1000.
- **Resultado esperado**: ValueError ou exceção.

### T23.5 — RegraComissao: especificidade com 5 campos
- **Cenário**: Regra com todos 5 campos preenchidos → especificidade=5.
- **Estrutura do teste**: Criar regra completa. Verificar `regra.especificidade`.
- **Resultado esperado**: 5.

### T23.6 — RegraComissao: especificidade com wildcards
- **Cenário**: Regra com apenas `linha` preenchida → especificidade=1.
- **Estrutura do teste**: Criar regra parcial.
- **Resultado esperado**: 1.

### T23.7 — RegraComissao: match hierárquico
- **Cenário**: Regra com linha="HIDROLOGIA", grupo=None (wildcard). Item com linha="HIDROLOGIA", grupo="QED".
- **Estrutura do teste**: `regra.match("HIDROLOGIA", "QED", ...)` → True.
- **Resultado esperado**: Match (wildcard aceita qualquer valor).

### T23.8 — RegraComissao: get_taxa_para_faturamento com múltiplas faixas
- **Cenário**: Faixa1: 0-100k → 1%. Faixa2: 100k-200k → 1.5%. Faixa3: 200k+ → 2%.
- **Estrutura do teste**: Faturamento=150k → taxa=1.5%.
- **Resultado esperado**: Taxa da faixa correta.

### T23.9 — RegraCentroCusto: match com fabricante
- **Cenário**: Regra CC="CC001", fabricante="PARKER". Item com CC001+PARKER → match.
- **Estrutura do teste**: Criar regra CC com fabricante. Testar match.
- **Resultado esperado**: Match com especificidade=2.

### T23.10 — RegraCentroCusto: match genérico (sem fabricante)
- **Cenário**: Regra CC="CC001", fabricante=None. Match com qualquer fabricante.
- **Estrutura do teste**: Testar com diferentes fabricantes.
- **Resultado esperado**: Match genérico (especificidade=1).

### T23.11 — RegraCentroCusto: get_split_decimal
- **Cenário**: Split=60 → 0.6. Split=None → 1.0.
- **Estrutura do teste**: Verificar conversão.
- **Resultado esperado**: Valores decimais corretos.

### T23.12 — ColaboradorV2: tipo_comissao recebimento requer taxa_adiantamento
- **Cenário**: tipo_comissao="recebimento" sem taxa_adiantamento_pct → erro.
- **Estrutura do teste**: Criar ColaboradorV2 com recebimento mas sem taxa.
- **Resultado esperado**: ValueError.

### T23.13 — ColaboradorV2: get_regra_cc com fallback
- **Cenário**: Buscar regra para CC+Fabricante. Se não encontrar, fallback para CC genérica.
- **Estrutura do teste**: Regra genérica apenas. Buscar com fabricante específico.
- **Resultado esperado**: Regra genérica retornada.

### T23.14 — ResultadoColaboradorV2: taxa_media calculada
- **Cenário**: Faturamento=200k, comissão=3k → taxa_media=1.5%.
- **Estrutura do teste**: Criar resultado com valores. Verificar propriedade.
- **Resultado esperado**: 1.5%.

---

## 24. Módulo: Metodologia V2 — Config Loader

**Arquivo**: `src/metodo_v2/config_loader_v2.py`

### T24.1 — Carregar REGRAS_COMISSOES_V2.xlsx completo
- **Cenário**: Arquivo com todas abas: COLABORADORES_V2, CARGOS_V2, REGRAS_COMISSAO_V2, REGRAS_COMISSAO_CC_V2.
- **Estrutura do teste**: Criar Excel. Chamar `ConfigLoaderV2.load()`.
- **Resultado esperado**: Dict[nome → ColaboradorV2] com regras carregadas.

### T24.2 — Formato novo de faixas (faixa_X_de, faixa_X_ate, faixa_X_taxa)
- **Cenário**: Formato com limites explícitos de/até.
- **Estrutura do teste**: Criar aba com formato novo. Verificar parsing.
- **Resultado esperado**: Faixas com limites corretos.

### T24.3 — Formato antigo de faixas (faixa_X_limite, faixa_X_taxa)
- **Cenário**: Formato com apenas limite inferior (superior inferido da próxima faixa).
- **Estrutura do teste**: Criar aba com formato antigo.
- **Resultado esperado**: Faixas com limite_superior inferido.

### T24.4 — Limite -1 significa infinito (última faixa)
- **Cenário**: Última faixa com faixa_5_limite=-1 → sem limite superior.
- **Estrutura do teste**: Criar faixa com -1. Verificar que FaixaComissao não tem limite_superior.
- **Resultado esperado**: Faixa aberta (aceita qualquer valor >= limite_inferior).

### T24.5 — Detecção de colaboradores duplicados → ValueError
- **Cenário**: "JOAO" aparece 2 vezes em COLABORADORES_V2.
- **Estrutura do teste**: Criar aba com duplicata. Chamar load.
- **Resultado esperado**: ValueError: colaborador duplicado.

### T24.6 — tipo_comissao "recebimento" com taxa_adiantamento obrigatória
- **Cenário**: Colaborador com tipo="recebimento" e taxa_adiantamento_pct=5%.
- **Estrutura do teste**: Criar com valores corretos. Verificar.
- **Resultado esperado**: ColaboradorV2 com recebe_por_recebimento=True.

### T24.7 — tipo_comissao "recebimento" SEM taxa_adiantamento → erro
- **Cenário**: tipo="recebimento" mas sem coluna taxa_adiantamento_pct.
- **Estrutura do teste**: Criar com tipo recebimento sem taxa.
- **Resultado esperado**: Exceção ou erro de validação.

### T24.8 — Colaborador em regras mas não em COLABORADORES_V2 → criação automática
- **Cenário**: "PEDRO" aparece em REGRAS_COMISSAO_V2 mas não em COLABORADORES_V2.
- **Estrutura do teste**: Criar regra para PEDRO sem entrada em COLABORADORES_V2.
- **Resultado esperado**: ColaboradorV2 criado automaticamente com defaults.

### T24.9 — Cargo validado contra CARGOS_V2
- **Cenário**: Colaborador com cargo="Estagiário" não presente em CARGOS_V2.
- **Estrutura do teste**: Cargo inexistente na aba CARGOS_V2.
- **Resultado esperado**: Warning ou erro de validação.

### T24.10 — Regras CC com split e fabricante
- **Cenário**: Regra CC com centro_custo="CC001", fabricante="PARKER", split=60.
- **Estrutura do teste**: Criar aba REGRAS_COMISSAO_CC_V2 com esses campos.
- **Resultado esperado**: RegraCentroCusto com split=60 e fabricante="PARKER".

---

## 25. Módulo: Metodologia V2 — Regra Matcher

**Arquivo**: `src/metodo_v2/regra_matcher_v2.py`

### T25.1 — Encontrar regra mais específica
- **Cenário**: Colaborador com regra genérica (linha) e específica (linha+grupo+subgrupo). Item da hierarquia específica.
- **Estrutura do teste**: `encontrar_regra()` deve retornar a mais específica.
- **Resultado esperado**: Regra com maior especificidade.

### T25.2 — Fallback para regra genérica
- **Cenário**: Sem regra específica para grupo. Regra genérica (apenas linha) existe.
- **Estrutura do teste**: Item com grupo sem regra. Verificar fallback.
- **Resultado esperado**: Regra genérica retornada.

### T25.3 — Nenhuma regra encontrada
- **Cenário**: Hierarquia sem nenhuma regra configurada.
- **Estrutura do teste**: Item de hierarquia sem regras.
- **Resultado esperado**: None (sem match).

### T25.4 — Calcular cobertura (hierarquias sem regra)
- **Cenário**: 10 hierarquias únicas, 8 com regras → 2 sem cobertura.
- **Estrutura do teste**: `calcular_cobertura()` com 10 hierarquias.
- **Resultado esperado**: Lista de 2 hierarquias sem regra.

### T25.5 — Ordenação por especificidade descendente
- **Cenário**: 3 regras candidatas com especificidade 1, 3, 5.
- **Estrutura do teste**: `encontrar_regras_candidatas()`. Verificar ordenação.
- **Resultado esperado**: Ordem: 5, 3, 1.

---

## 26. Módulo: Metodologia V2 — Atribuição Service

**Arquivo**: `src/metodo_v2/atribuicao_service_v2.py`

### T26.1 — Atribuição de operacional (Consultor Interno)
- **Cenário**: Item com Consultor Interno="JOAO". JOAO tem regra para hierarquia do item.
- **Estrutura do teste**: Criar item e regras. `get_colaboradores_para_item()`.
- **Resultado esperado**: JOAO na lista com tipo_cargo=OPERACIONAL.

### T26.2 — Operacional sem regra → erro
- **Cenário**: JOAO na AC mas sem regra em REGRAS_COMISSAO_V2 para a hierarquia.
- **Estrutura do teste**: Item com JOAO sem regra correspondente.
- **Resultado esperado**: ResultadoAtribuicao.sucesso = False, erro de validação.

### T26.3 — Atribuição de gestão (Gerente, Coordenador)
- **Cenário**: CARLOS (Gerente de Linha) tem regra para hierarquia → atribuído automaticamente.
- **Estrutura do teste**: Regra de CARLOS para hierarquia do item.
- **Resultado esperado**: CARLOS na lista com tipo_cargo=GESTAO.

### T26.4 — Gestão: múltiplos gestores com split
- **Cenário**: 2 Coordenadores com split 50/50 para mesma hierarquia.
- **Estrutura do teste**: 2 regras de coordenadores. Verificar fator_split=0.5.
- **Resultado esperado**: Ambos na lista com split correto.

### T26.5 — Wildcard "[Todos os..." aceita qualquer valor
- **Cenário**: Regra com grupo="[Todos os grupos]" → match com qualquer grupo.
- **Estrutura do teste**: Item com grupo="QED". Regra com wildcard.
- **Resultado esperado**: Match.

### T26.6 — Fonte AC vs REGRAS_COMISSAO_V2
- **Cenário**: Operacionais têm fonte="AC", gestão tem fonte="REGRAS_COMISSAO_V2".
- **Estrutura do teste**: Verificar campo `fonte` em cada ColaboradorAtribuido.
- **Resultado esperado**: Fontes corretas.

### T26.7 — Normalização de nomes (strip, case-insensitive)
- **Cenário**: AC tem "  João  ", regras têm "JOAO". Deve dar match.
- **Estrutura do teste**: Nomes com variações de espaço/case.
- **Resultado esperado**: Match após normalização.

---

## 27. Módulo: Metodologia V2 — Comissão Calculator (Hierarquia)

**Arquivo**: `src/metodo_v2/comissao_calculator_v2.py`

### T27.1 — Comissão por faixa: faturamento na faixa 1
- **Cenário**: Faturamento=50k. Faixa 1: 0-100k → 1%. Comissão = 50k × 0.01 = R$ 500.
- **Estrutura do teste**: Calcular comissão com faixa aplicável.
- **Resultado esperado**: R$ 500.

### T27.2 — Comissão por faixa: faturamento na faixa 3
- **Cenário**: Faturamento=250k. Faixa 3: 200k-300k → 2%. Comissão = 250k × 0.02 = R$ 5.000.
- **Estrutura do teste**: Verificar seleção da faixa correta.
- **Resultado esperado**: R$ 5.000.

### T27.3 — Comissão com fator_split
- **Cenário**: Faturamento=100k, taxa=1.5%, split=0.6.
- **Estrutura do teste**: `100k × 0.015 × 0.6 = R$ 900`.
- **Resultado esperado**: R$ 900.

### T27.4 — Hierarquia sem regra → comissão zero
- **Cenário**: Item sem regra correspondente → não comissiona.
- **Estrutura do teste**: Item com hierarquia sem cobertura.
- **Resultado esperado**: Comissão = 0, hierarquia registrada como "sem regra".

### T27.5 — Cálculo por hierarquia (não por item)
- **Cenário**: Faturamento agregado por hierarquia antes de aplicar faixa.
- **Estrutura do teste**: 3 itens da mesma hierarquia → soma → aplica faixa sobre soma.
- **Resultado esperado**: Faixa baseada no faturamento agregado.

### T27.6 — Múltiplas hierarquias para mesmo colaborador
- **Cenário**: JOAO com regras para HIDROLOGIA e ELETRICA. Faturou em ambas.
- **Estrutura do teste**: Calcular comissão separada por hierarquia. Somar.
- **Resultado esperado**: Comissão total = soma das hierarquias.

---

## 28. Módulo: Metodologia V2 — CC Calculator (Centro de Custo)

**Arquivo**: `src/metodo_v2/cc_calculator_v2.py`

### T28.1 — Comissão por CC: regra específica (CC + Fabricante)
- **Cenário**: Regra para CC001+PARKER com faixa 100k+ → 2%. Faturamento CC001+PARKER = 150k.
- **Estrutura do teste**: Calcular com regra específica.
- **Resultado esperado**: Comissão = 150k × 0.02 × split.

### T28.2 — Comissão por CC: regra genérica (CC sem fabricante)
- **Cenário**: Regra para CC001 (qualquer fabricante). Faturamento total do CC = 300k → faixa 2%.
- **Estrutura do teste**: Nenhuma regra específica por fabricante. Usar genérica.
- **Resultado esperado**: Faixa baseada no faturamento TOTAL do CC.

### T28.3 — Faturamento usado para faixa: específica vs genérica
- **Cenário**: Regra específica → faturamento do par (CC,Fab). Regra genérica → faturamento total CC.
- **Estrutura do teste**: Criar ambas situações. Comparar base de faixa.
- **Resultado esperado**: Bases diferentes conforme tipo de regra.

### T28.4 — Split efetivo entre múltiplos do mesmo cargo
- **Cenário**: 2 Coordenadores no CC001: SAMANTA split=60%, JOÃO split=40%.
- **Estrutura do teste**: Calcular comissão com splits.
- **Resultado esperado**: SAMANTA=60%, JOÃO=40% da comissão total.

### T28.5 — Split não definido + único do cargo → 100%
- **Cenário**: Apenas 1 Gerente no CC sem split definido → 100%.
- **Estrutura do teste**: 1 regra sem split.
- **Resultado esperado**: Split = 1.0.

### T28.6 — Múltiplos sem split → divisão igualitária + warning
- **Cenário**: 3 Gerentes sem split definido → 33.3% cada + warning.
- **Estrutura do teste**: 3 regras sem split.
- **Resultado esperado**: Split = 0.333 cada + warning gerado.

### T28.7 — Operacional: verificar nome na AC + vínculo CC
- **Cenário**: JOAO é Consultor Interno no CC001. Item do CC001 com JOAO → comissiona. Item do CC002 → não.
- **Estrutura do teste**: Itens de CCs diferentes.
- **Resultado esperado**: Comissão apenas no CC vinculado.

### T28.8 — Exclusão de colaboradores de recebimento
- **Cenário**: MARIA com tipo_comissao="recebimento" → excluída do cálculo de faturamento.
- **Estrutura do teste**: MARIA na regra CC mas com tipo recebimento.
- **Resultado esperado**: MARIA ignorada no cálculo V2.

### T28.9 — Faturamento <= 0 ignorado
- **Cenário**: Item com valor 0 ou negativo.
- **Estrutura do teste**: Incluir item com valor 0.
- **Resultado esperado**: Item excluído da acumulação.

### T28.10 — Geração de DataFrame resumo e detalhes
- **Cenário**: Após cálculo, gerar df_resumo (por colaborador+CC) e df_detalhes (por item).
- **Estrutura do teste**: Executar cálculo completo. Verificar DataFrames de saída.
- **Resultado esperado**: DataFrames com colunas corretas e valores consistentes.

---

## 29. Módulo: Metodologia V2 — Orquestrador

**Arquivo**: `src/metodo_v2/orchestrator_v2.py`

### T29.1 — Modo HIERARQUIA: fluxo completo
- **Cenário**: Configuração em modo hierarquia. Dados da AC filtrados. Comissões calculadas por hierarquia.
- **Estrutura do teste**: Mock completo. Executar orquestrador em modo HIERARQUIA.
- **Resultado esperado**: DataFrame com comissões por hierarquia.

### T29.2 — Modo CENTRO_CUSTO: fluxo completo
- **Cenário**: Configuração em modo CC. Comissões calculadas por centro de custo.
- **Estrutura do teste**: Mock completo. Executar em modo CC.
- **Resultado esperado**: DataFrame com comissões por CC.

### T29.3 — Filtro por Status='FATURADO'
- **Cenário**: Apenas itens com status FATURADO devem ser processados.
- **Estrutura do teste**: Incluir itens com status CANCELADO, EM ANDAMENTO, FATURADO.
- **Resultado esperado**: Apenas FATURADO processados.

### T29.4 — Filtro por operações válidas
- **Cenário**: Operações: FLOC, IMO2, OR19, P205, PSEM, PSER, SERV, PVEN, PVMA.
- **Estrutura do teste**: Incluir operação inválida "XXXX".
- **Resultado esperado**: "XXXX" excluído.

### T29.5 — Filtro por mês/ano (Dt Emissao)
- **Cenário**: Filtrar itens pela data de emissão dentro do mês/ano de apuração.
- **Estrutura do teste**: Itens de meses diferentes.
- **Resultado esperado**: Apenas itens do mês correto.

### T29.6 — Hierarquia com 5 níveis de especificidade
- **Cenário**: Match por 5 campos: linha, grupo, subgrupo, tipo_mercadoria, fabricante.
- **Estrutura do teste**: Verificar que orquestrador usa 5 campos (V2 inclui fabricante no match).
- **Resultado esperado**: Regra mais específica (5 campos) vence.

### T29.7 — Colaboradores excluídos do cálculo por recebimento
- **Cenário**: Colaboradores com tipo_comissao="recebimento" são excluídos.
- **Estrutura do teste**: Mix de colaboradores faturamento e recebimento.
- **Resultado esperado**: Apenas faturamento calcula comissões.

---

## 30. Testes de Integração

### T30.1 — Integração: Config Loader + Atribuição Engine
- **Cenário**: Carregar REGRAS_COMISSOES.xlsx → preprocessar → buscar regras para item real.
- **Estrutura do teste**: Usar dados reais (anonimizados). Verificar que a cadeia funciona sem erros.
- **Resultado esperado**: Regras encontradas para todos itens configurados.

### T30.2 — Integração: Data Loader + Preparador + Cálculo FC
- **Cenário**: Carregar dados de entrada → preparar dados mensais → calcular FC para item.
- **Estrutura do teste**: Pipeline completo de dados até FC.
- **Resultado esperado**: FC calculado corretamente com dados reais.

### T30.3 — Integração: Recebimento Completo (mapper → identificador → métricas → comissão)
- **Cenário**: Análise Financeira → mapear documentos → identificar colaboradores → calcular TCMP/FCMP → comissão.
- **Estrutura do teste**: Pipeline de recebimento end-to-end.
- **Resultado esperado**: Comissões de recebimento calculadas e salvas no estado.

### T30.4 — Integração: Devolução Completa (loader → linker → calculator → master DB)
- **Cenário**: Devoluções → vincular NFs → buscar histórico → calcular estornos → salvar.
- **Estrutura do teste**: Pipeline de devoluções end-to-end.
- **Resultado esperado**: Estornos salvos no Master DB com valores negativos.

### T30.5 — Integração: Faturamento + Recebimento para mesmo colaborador
- **Cenário**: JOAO recebe por faturamento E por recebimento (cenário misto).
- **Estrutura do teste**: Colaborador com tipo_comissao configurado. Verificar que recebe nos dois fluxos.
- **Resultado esperado**: Comissões de ambos tipos calculadas.

### T30.6 — Integração: FC Escada aplicada no FCMP do recebimento
- **Cenário**: FCMP calculado → aplicar escada → usar FCMP ajustado na comissão.
- **Estrutura do teste**: Cargo com FC_ESCADA. Calcular FCMP. Verificar ajuste.
- **Resultado esperado**: FCMP passa pela escada antes de ser usado.

### T30.7 — Integração: Reconciliação após faturamento de processo com adiantamento
- **Cenário**: 1) COT pago (FCMP=1.0), 2) Processo faturado (FCMP=0.85), 3) Reconciliação automática.
- **Estrutura do teste**: Executar sequência completa no orquestrador.
- **Resultado esperado**: Reconciliação = adiantada × (0.85 - 1.0).

### T30.8 — Integração: State Manager persistência entre execuções
- **Cenário**: Salvar estado → nova execução → carregar estado → continuar processamento.
- **Estrutura do teste**: Salvar. Criar nova instância. Carregar. Verificar continuidade.
- **Resultado esperado**: Estado restaurado corretamente.

### T30.9 — Integração: V2 Config + Calculator + Orquestrador
- **Cenário**: Carregar config V2 → calcular comissões → gerar output completo.
- **Estrutura do teste**: Pipeline V2 end-to-end com dados mock.
- **Resultado esperado**: DataFrame de comissões V2 completo.

### T30.10 — Integração: Conversão cambial + Meta fornecedor no FC
- **Cenário**: Meta em USD → converter faturamento BRL → calcular atingimento → componente FC.
- **Estrutura do teste**: Mock de taxas BCB + faturamento YTD.
- **Resultado esperado**: Componente meta_fornecedor correto no FC.

---

## 31. Testes End-to-End (E2E)

### T31.1 — E2E V1: Execução completa do robô de comissões (faturamento)
- **Cenário**: Dados de entrada completos → preparar dados → carregar configs → validar → calcular FC → calcular comissões → salvar Master DB.
- **Estrutura do teste**:
  1. Criar dados de entrada mock (AC, rentabilidade, conversões, faturados).
  2. Criar config mock (REGRAS_COMISSOES.xlsx com todas abas).
  3. Instanciar `CalculoComissao()`.
  4. Executar `calculadora.executar()`.
  5. Verificar Master DB com comissões esperadas.
- **Resultado esperado**: Comissões calculadas corretamente para todos colaboradores, todos itens, todos processos.

### T31.2 — E2E V1: Execução com recebimento
- **Cenário**: Dados de faturamento + análise financeira (pagamentos) → comissões por recebimento.
- **Estrutura do teste**:
  1. Criar dados mock incluindo análise financeira e status de pagamentos.
  2. Executar robô com fluxo de recebimento habilitado.
  3. Verificar comissões de adiantamento, regulares e reconciliações.
- **Resultado esperado**: 3 tipos de comissão no Master DB.

### T31.3 — E2E V1: Execução com devoluções
- **Cenário**: Mês com devoluções → estornos calculados e salvos.
- **Estrutura do teste**:
  1. Criar devoluções para NFs existentes.
  2. Criar histórico no Master DB.
  3. Executar.
  4. Verificar estornos.
- **Resultado esperado**: Registros tipo DEVOLUCAO com valores negativos.

### T31.4 — E2E V2: Execução completa modo HIERARQUIA
- **Cenário**: Pipeline V2 completo no modo hierarquia.
- **Estrutura do teste**:
  1. Criar REGRAS_COMISSOES_V2.xlsx mock.
  2. Criar dados de AC filtrados.
  3. Executar `OrchestratorV2()`.
  4. Verificar DataFrame de saída.
- **Resultado esperado**: Comissões V2 por hierarquia.

### T31.5 — E2E V2: Execução completa modo CENTRO_CUSTO
- **Cenário**: Pipeline V2 completo no modo centro de custo.
- **Estrutura do teste**:
  1. Config V2 com regras CC.
  2. AC com coluna Centro de Custo.
  3. Executar.
  4. Verificar comissões por CC.
- **Resultado esperado**: Comissões V2 por centro de custo.

### T31.6 — E2E: Mês sem dados (nenhum faturamento)
- **Cenário**: Mês sem nenhum item faturado → robô deve executar sem erros e gerar output vazio.
- **Estrutura do teste**: Dados vazios para o mês. Executar.
- **Resultado esperado**: Execução limpa, sem comissões geradas, sem exceções.

### T31.7 — E2E: Mês com dados parciais (sem rentabilidade)
- **Cenário**: Arquivo de rentabilidade não existe para o mês → componente de rentabilidade ignorado.
- **Estrutura do teste**: Dados sem arquivo de rentabilidade. Executar.
- **Resultado esperado**: FC calculado sem componente rentabilidade (peso redistribuído ou atingimento=1.0).

### T31.8 — E2E: Múltiplos meses consecutivos
- **Cenário**: Executar robô para 3 meses consecutivos. Verificar acumulação no Master DB e estado de recebimento.
- **Estrutura do teste**: Executar para mês 10, 11, 12/2025 sequencialmente.
- **Resultado esperado**: Histórico acumulado, métricas de retenção atualizadas, estado correto.

### T31.9 — E2E: Validação de pesos → erro antes do cálculo
- **Cenário**: PESOS_METAS não somam 100% → execução abortada com erro claro.
- **Estrutura do teste**: Config com pesos somando 90%. Executar.
- **Resultado esperado**: Exceção: "Pesos não somam 100%".

### T31.10 — E2E: Colaborador inexistente em REGRAS_ATRIBUICAO
- **Cenário**: AC referencia "JOAO" como Consultor Interno, mas JOAO não tem nenhuma regra de atribuição.
- **Estrutura do teste**: AC com JOAO sem regras.
- **Resultado esperado**: Warning ou tratamento de erro (comissão zero ou erro de validação).

### T31.11 — E2E: run_comissoes.py com argumentos CLI
- **Cenário**: `python run_comissoes.py --mes 10 --ano 2025 --verbose`.
- **Estrutura do teste**: Executar via subprocess com argumentos. Verificar exit code.
- **Resultado esperado**: Exit code 0, execução completa.

### T31.12 — E2E: Idempotência — reexecução do mesmo mês
- **Cenário**: Executar robô 2 vezes para o mesmo mês → Master DB sem duplicatas (deduplicação).
- **Estrutura do teste**: Executar. Executar novamente. Contar registros.
- **Resultado esperado**: Mesmo número de registros (deduplicação funcionando).

---

## Apêndice A: Matriz de Cobertura

| Módulo | Unitários | Integração | E2E |
|--------|-----------|------------|-----|
| Normalização | T1.1-T1.10, T8.1-T8.2 | — | — |
| Config Loader V1 | T2.1-T2.8 | T30.1 | T31.1, T31.9 |
| Data Loader | T3.1-T3.8 | T30.2 | T31.1 |
| Atribuição Engine | T4.1-T4.15 | T30.1 | T31.1, T31.10 |
| Meta Lookup | T5.1-T5.8 | T30.2 | T31.1 |
| FC Calculation | T6.1-T6.12 | T30.2, T30.10 | T31.1, T31.7 |
| FC Escada | T7.1-T7.10 | T30.6 | T31.1 |
| Atingimento | T8.1-T8.2 | — | — |
| Comissão Faturamento V1 | T9.1-T9.13 | T30.2 | T31.1 |
| Retenção Clientes | T10.1-T10.6 | — | T31.8 |
| Conversão Cambial | T11.1-T11.5 | T30.10 | T31.1 |
| Devoluções | T12.1-T12.12 | T30.4 | T31.3 |
| Process Mapper | T13.1-T13.6 | T30.3 | T31.2 |
| Identificador Colaboradores | T14.1-T14.8 | T30.3 | T31.2 |
| Métricas TCMP/FCMP | T15.1-T15.8 | T30.3, T30.6 | T31.2 |
| Comissão Recebimento | T16.1-T16.5 | T30.3 | T31.2 |
| Reconciliação | T17.1-T17.5 | T30.7 | T31.2 |
| Recebimento Orquestrador | T18.1-T18.8 | T30.3, T30.7 | T31.2 |
| State Manager | T19.1-T19.10 | T30.8 | T31.2 |
| Analise Financeira Loader | T20.1-T20.6 | T30.3 | T31.2 |
| Master DB Manager | T21.1-T21.10 | T30.4 | T31.1, T31.12 |
| Preparador Dados | T22.1-T22.4 | T30.2 | T31.1 |
| V2 Modelos | T23.1-T23.14 | — | — |
| V2 Config Loader | T24.1-T24.10 | T30.9 | T31.4 |
| V2 Regra Matcher | T25.1-T25.5 | T30.9 | T31.4 |
| V2 Atribuição Service | T26.1-T26.7 | T30.9 | T31.4 |
| V2 Comissão Calculator | T27.1-T27.6 | T30.9 | T31.4 |
| V2 CC Calculator | T28.1-T28.10 | T30.9 | T31.5 |
| V2 Orquestrador | T29.1-T29.7 | T30.9 | T31.4, T31.5 |

**Total de testes planejados**: ~220 cenários

## Apêndice B: Fórmulas de Referência

| Fórmula | Expressão |
|---------|-----------|
| Comissão Faturamento V1 | `valor_faturado × taxa_rateio × fatia_cargo × FC × fator_split` |
| FC (Fator de Correção) | `Σ(peso_i × atingimento_i)` para cada componente |
| Atingimento | `realizado / meta` (meta=0 → 1.0, realizado≤0 → 0.0) |
| FC Escada (multiplicador) | `piso + (degrau × (1.0 - piso) / (num_degraus - 1))` |
| TCMP | `Σ(taxa_i × valor_i) / Σ(valor_i)` |
| FCMP | `Σ(fc_i × valor_i) / Σ(valor_i)`, depois escada |
| Comissão Adiantamento | `valor × TCMP × 1.0` |
| Comissão Regular | `valor × TCMP × FCMP` |
| Reconciliação | `comissão_adiantada × (FCMP - 1.0)` |
| Fator Devolução | `min(valor_devolvido / valor_realizado, 1.0)` |
| Estorno | `comissão_original × fator_devolução` (negativo) |
| Comissão V2 (Hierarquia) | `faturamento × taxa_faixa × fator_split` |
| Comissão V2 (CC) | `faturamento_item × (taxa/100) × split_efetivo` |
| Retenção Clientes | `clientes_mantidos / clientes_periodo_anterior` |
| Conversão Cambial | `faturamento_brl / taxa_cambio_media_mensal` |

---

*Fim do Plano de Testes*
