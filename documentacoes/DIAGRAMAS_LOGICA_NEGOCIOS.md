# 📊 Diagramas de Lógica de Negócio — Sistema de Comissões

> **Versão:** 1.0 — Março/2026  
> **Base:** `DOCUMENTACAO_COMPLETA_SISTEMA_COMISSOES.md` v1.1 + código auditado  
> **Uso:** Copie cada bloco `mermaid` individualmente para o [Mermaid Live Editor](https://mermaid.live) ou visualize no GitHub/VS Code.

---

## 1. Fluxo Geral do Sistema (Visão Macro)

```mermaid
flowchart TB
    subgraph ENTRADA["📥 DADOS DE ENTRADA"]
        AC["Análise Comercial Completa\n(Processos / Itens / NF)"]
        AF["Análise Financeira\n(Pagamentos / Baixas)"]
        RC["REGRAS_COMISSOES.xlsx\n(Config Master)"]
        RENT["Rentabilidade Mensal\n(Arquivo Agrupado .xlsx)"]
        DEV["Devoluções.xlsx\n(Devoluções do mês)"]
        CAMBIO["Taxas de Câmbio\n(monthly_avg_rates.json)"]
        MF["METAS_FORNECEDORES.csv"]
    end

    subgraph MOTOR["⚙️ MOTOR DE CÁLCULO (calculo_comissoes.py)"]
        direction TB
        F1["Fase 1: Carregar Dados"]
        F2["Fase 2: Validar Dados"]
        F3["Fase 3: Pré-processar\n(Faturados, Conversões, YTD)"]
        F4["Fase 4: Calcular Realizados\nAgregados"]
        F5["Fase 5: Detecção Cross-Selling"]
        F5B{"Casos Pendentes\nde Decisão?"}
        F5C["Pausar → Enviar JSON\npara Frontend"]
        F5D["Re-execução com\n--decisions"]
        F6["Fase 6: Carregar Estado\nRecebimento"]
        F7["Fase 7: Reconciliação\n+ Métricas TCMP/FCMP"]
        F8["Fase 8: Comissões\npor Recebimento"]
        F9["Fase 9: Comissões\npor Faturamento"]
        F10["Fase 10: Gerar Saídas"]
        F11["Fase 11: Processar\nDevoluções"]

        F1 --> F2 --> F3 --> F4 --> F5
        F5 --> F5B
        F5B -- "Sim" --> F5C --> F5D --> F6
        F5B -- "Não" --> F6
        F6 --> F7 --> F8 --> F9 --> F10 --> F11
    end

    subgraph SAIDA["📤 DADOS DE SAÍDA"]
        REL_FAT["Relatório Comissões\nFaturamento"]
        REL_REC["Relatório Comissões\nRecebimento"]
        ESTADO["Estado_Processos_\nRecebimento.xlsx"]
        MASTER["HISTORICO_COMISSOES_\nMASTER.xlsx"]
        SALDOS["Saldos Negativos\n(Reconciliações + Devoluções)"]
    end

    AC --> F1
    AF --> F1
    RC --> F1
    RENT --> F1
    DEV --> F11
    CAMBIO --> F1
    MF --> F1

    F10 --> REL_FAT
    F10 --> REL_REC
    F8 --> ESTADO
    F10 --> MASTER
    F11 --> MASTER
    F7 --> SALDOS
    F11 --> SALDOS
```

---

## 2. Cálculo de Comissão por Faturamento (Item a Item)

```mermaid
flowchart TB
    START(["Início: Para cada ITEM faturado"])
    
    CTX["Identificar Contexto do Item\nLinha > Grupo > Subgrupo > Tipo Mercadoria"]
    TAXA["Buscar Taxa de Rateio\nna hierarquia de categorias"]
    ATRIB["Buscar Colaboradores\nna aba ATRIBUICOES"]
    
    SPLIT{"Cargo\ncompartilhado?"}
    SPLIT_SIM["Aplicar Fator Split\n(ex: 50% / 50%)"]
    SPLIT_NAO["Fator Split = 100%"]
    
    CS{"Item é\nCross-Selling?"}
    CS_A["Opção A: Taxa Subtraída\nTaxa = Taxa - Taxa CS"]
    CS_B["Opção B: Taxa Adicional\nTaxa original mantida"]
    CS_NAO["Sem ajuste de CS"]

    subgraph FC_CALC["⚙️ Cálculo do FC (por Colaborador)"]
        direction TB
        FC1["Obter Pesos por Cargo\n(aba PESOS_METAS)"]
        FC2["Calcular Atingimento\nde cada Componente"]
        FC3["Aplicar Cap por Componente\n(cap_fc_max, padrão 1.0)"]
        FC4["FC_rampa = Σ(Ating. Capado × Peso)"]
        FC5{"Cargo tem config\nem FC_ESCADA_CARGOS?"}
        FC6["Modo RAMPA:\nFC Aplicado = FC_rampa"]
        FC7["Modo ESCADA:\nConverter em degrau discreto"]
        FC8["FC Aplicado = Multiplicador Final"]

        FC1 --> FC2 --> FC3 --> FC4 --> FC5
        FC5 -- "Não / RAMPA" --> FC6 --> FC8
        FC5 -- "ESCADA" --> FC7 --> FC8
    end

    FORMULA["Comissão Potencial =\nValor Realizado × Taxa Rateio Ajustada\n× Fatia Cargo × Fator Split"]
    FINAL["Comissão Final =\nComissão Potencial × FC Aplicado"]
    SAVE["Gravar no HISTORICO_COMISSOES_MASTER\nTipo_Comissao = FATURAMENTO"]

    START --> CTX --> TAXA --> ATRIB
    ATRIB --> SPLIT
    SPLIT -- "Sim" --> SPLIT_SIM --> CS
    SPLIT -- "Não" --> SPLIT_NAO --> CS
    CS -- "Opção A" --> CS_A --> FC_CALC
    CS -- "Opção B" --> CS_B --> FC_CALC
    CS -- "Não" --> CS_NAO --> FC_CALC
    FC_CALC --> FORMULA --> FINAL --> SAVE
```

---

## 3. Componentes do Fator de Correção (FC)

```mermaid
flowchart LR
    subgraph COMPONENTES["📊 Componentes do FC (até 8)"]
        direction TB
        C1["Faturamento da Linha\n(Peso ex: 25%)"]
        C2["Faturamento Individual\n(Peso ex: 15%)"]
        C3["Conversão da Linha\n(Peso ex: 15%)"]
        C4["Conversão Individual\n(Peso ex: 10%)"]
        C5["Rentabilidade\n(Peso ex: 20%)"]
        C6["Retenção de Clientes\n(Peso ex: 10%)\n⚠️ Apenas Gerente Linha"]
        C7["Meta Fornecedor 1\n(Peso ex: 2.5%)"]
        C8["Meta Fornecedor 2\n(Peso ex: 2.5%)"]
    end

    subgraph ATINGIMENTO["📐 Cálculo de Cada Componente"]
        direction TB
        AT["Atingimento = Realizado / Meta"]
        CAP["Capado = min(Atingimento, cap_fc_max)\nPadrão: cap_fc_max = 1.0"]
        CONTRIB["Contribuição = Capado × Peso"]
    end

    subgraph RESULTADO["🎯 FC Final"]
        direction TB
        SOMA["FC_rampa = Σ Contribuições\n(média ponderada)"]
        ESC{"Modo do Cargo?"}
        RAMPA["RAMPA → FC Aplicado = FC_rampa"]
        ESCADA["ESCADA → Converter\nem degrau com piso/nº degraus"]
        FINAL_FC["FC Aplicado\n(Multiplicador na Comissão)"]
    end

    C1 & C2 & C3 & C4 & C5 & C6 & C7 & C8 --> AT
    AT --> CAP --> CONTRIB --> SOMA
    SOMA --> ESC
    ESC -- "Sem config / RAMPA" --> RAMPA --> FINAL_FC
    ESC -- "ESCADA" --> ESCADA --> FINAL_FC
```

---

## 4. FC Escada — Lógica de Degraus

```mermaid
flowchart TB
    INPUT["FC_rampa calculado\n(ex: 0.73)"]
    
    CONFIG["Configuração do Cargo:\n• modo = ESCADA\n• piso_pct (ex: 0.50)\n• num_degraus (ex: 4)"]
    
    CALC["Tamanho do Degrau =\n(1.0 - piso_pct) / num_degraus\nEx: (1.0 - 0.50) / 4 = 0.125"]
    
    FLOOR["Degrau Atingido =\nfloor((FC_rampa - piso_pct) / tamanho_degrau)\nArredondar para baixo"]
    
    CHECK{"FC_rampa < piso_pct?"}
    BELOW["Multiplicador = 0.0\n(Abaixo do piso)"]
    
    CHECK2{"FC_rampa >= 1.0?"}
    TOP["Multiplicador = 1.0\n(Topo da escada)"]
    
    STEP["Multiplicador =\npiso_pct + (degrau × tamanho_degrau)"]
    
    NOTE["⚠️ SEM TOLERÂNCIA\nCorte exato por degrau\nNão existe regra 95% = 100%"]

    INPUT --> CONFIG --> CALC --> CHECK
    CHECK -- "Sim" --> BELOW
    CHECK -- "Não" --> CHECK2
    CHECK2 -- "Sim" --> TOP
    CHECK2 -- "Não" --> FLOOR --> STEP
    STEP ~~~ NOTE
```

---

## 5. Fluxo de Comissões por Recebimento

```mermaid
flowchart TB
    START(["Início: Recebimento Mensal"])
    
    subgraph CARGA["📥 Carga de Dados"]
        LOAD_AF["Carregar Análise Financeira\nFiltrar: Tipo de Baixa = B\nFiltrar: Data de Baixa = mês/ano"]
        LOAD_AC["Carregar Análise Comercial\n(todos os processos)"]
        LOAD_EST["Carregar Estado Persistente\n(Estado_Processos_Recebimento.xlsx)"]
    end

    subgraph MAPPING["🔗 Mapeamento Documento → Processo"]
        direction TB
        DOC_CHECK{"Documento\ncomeça com COT?"}
        COT["É ADIANTAMENTO\nExtrair nº processo do sufixo"]
        NF_MAP["É PAGAMENTO REGULAR\nExtrair 5-6 primeiros dígitos\nNormalizar zeros à esquerda\nComparar com Numero NF"]
    end

    subgraph METRICAS["📐 Cálculo de Métricas por Processo"]
        direction TB
        PROC_STATUS{"Processo\nFATURADO?"}
        NAO_FAT["TCMP calculado\nFCMP = 1.0 (provisório)\nBase Valor = Valor Orçado"]
        SIM_FAT["TCMP e FCMP reais\ncalculados item a item\nBase Valor = Valor Realizado"]
        
        TCMP["TCMP =\nΣ(Taxa × Valor) / Σ(Valores)"]
        FCMP["FCMP_rampa =\nΣ(FC × Valor) / Σ(Valores)"]
        FCMP_ESC{"Cargo com\nescada?"}
        FCMP_APPLY["FCMP_APLICADO =\naplicar escada sobre FCMP_rampa"]
        FCMP_DIRECT["FCMP_APLICADO =\nFCMP_rampa"]
    end

    subgraph CALC_REC["💰 Cálculo da Comissão"]
        direction TB
        IS_COT{"Tipo de\nPagamento?"}
        COM_ADI["Comissão Adiantamento =\nValor × TCMP × 1.0\n(FC provisório)"]
        COM_REG["Comissão Regular =\nValor × TCMP × FCMP_APLICADO"]
        SAVE_STATE["Atualizar Estado:\n• Total pago\n• Comissão acumulada\n• Saldo a receber\n• Status pagamento"]
    end

    PERSIST["Salvar Estado_Processos_\nRecebimento.xlsx"]
    SAVE_MASTER["Gravar no HISTORICO_COMISSOES_MASTER\nTipo = ADIANTAMENTO ou REGULAR"]

    START --> CARGA
    LOAD_AF --> DOC_CHECK
    DOC_CHECK -- "Sim (COT)" --> COT
    DOC_CHECK -- "Não" --> NF_MAP
    COT --> METRICAS
    NF_MAP --> METRICAS
    LOAD_AC --> METRICAS
    LOAD_EST --> METRICAS
    
    PROC_STATUS -- "Não" --> NAO_FAT
    PROC_STATUS -- "Sim" --> SIM_FAT
    NAO_FAT --> TCMP
    SIM_FAT --> TCMP
    SIM_FAT --> FCMP
    FCMP --> FCMP_ESC
    FCMP_ESC -- "Sim" --> FCMP_APPLY
    FCMP_ESC -- "Não" --> FCMP_DIRECT
    
    TCMP --> IS_COT
    FCMP_APPLY --> IS_COT
    FCMP_DIRECT --> IS_COT
    IS_COT -- "COT (Adiantamento)" --> COM_ADI
    IS_COT -- "Regular" --> COM_REG
    COM_ADI --> SAVE_STATE
    COM_REG --> SAVE_STATE
    SAVE_STATE --> PERSIST
    SAVE_STATE --> SAVE_MASTER
```

---

## 6. Detecção de Cross-Selling

```mermaid
flowchart TB
    START(["Para cada Processo com vários itens"])
    
    CHECK1{"Coluna\n'Gerente Comercial-Pedido'\npreenchida?"}
    SKIP1["❌ Não é Cross-Selling"]
    
    CHECK2{"Nome é de um\nConsultor Externo?"}
    SKIP2["❌ Não é Cross-Selling"]
    
    CHECK3{"Consultor NÃO tem\natribuição para a\nlinha do item?"}
    SKIP3["❌ Não é Cross-Selling\n(tem atribuição própria)"]
    
    CHECK4{"Consultor cadastrado\nna config CROSS_SELLING?"}
    SKIP4["❌ Não é Cross-Selling\n(não elegível)"]
    
    DETECTED["✅ CASO DE CROSS-SELLING\nDETECTADO"]
    
    PENDING{"Já existe decisão\npré-registrada?"}
    
    PAUSE["⏸️ PAUSAR EXECUÇÃO\nEmitir JSON para Frontend\nAguardar decisão do usuário"]
    
    RESUME["Receber decisão\nvia --decisions"]
    
    DECISION{"Opção\nescolhida?"}
    
    OPT_A["Opção A: Taxa Subtraída\nTaxa CS abatida da\ntaxa dos demais"]
    OPT_B["Opção B: Taxa Adicional\nTodos mantêm taxa integral\n+ comissão extra do consultor"]
    
    APPLY["Aplicar decisão no\ncálculo de comissão do processo"]

    START --> CHECK1
    CHECK1 -- "Não" --> SKIP1
    CHECK1 -- "Sim" --> CHECK2
    CHECK2 -- "Não" --> SKIP2
    CHECK2 -- "Sim" --> CHECK3
    CHECK3 -- "Não (tem)" --> SKIP3
    CHECK3 -- "Sim (sem)" --> CHECK4
    CHECK4 -- "Não" --> SKIP4
    CHECK4 -- "Sim" --> DETECTED
    DETECTED --> PENDING
    PENDING -- "Não" --> PAUSE --> RESUME --> DECISION
    PENDING -- "Sim" --> DECISION
    DECISION -- "A" --> OPT_A --> APPLY
    DECISION -- "B" --> OPT_B --> APPLY
```

---

## 7. Adiantamentos e Reconciliação

```mermaid
flowchart TB
    subgraph ADIANTAMENTO["💰 Fluxo de Adiantamento"]
        direction TB
        A1["Cliente paga antes da NF\n(Documento COT)"]
        A2["Processo NÃO FATURADO\nFC real desconhecido"]
        A3["Usar FC = 1.0\n(provisório / integral)"]
        A4["Comissão = Valor × TCMP × 1.0"]
        A5["Registrar no estado:\nadiantamento acumulado"]
        A1 --> A2 --> A3 --> A4 --> A5
    end

    TEMPO["⏳ Tempo passa...\nProcesso é FATURADO"]

    subgraph RECONCILIACAO["🔄 Fluxo de Reconciliação"]
        direction TB
        R1{"Condições\natendidas?"}
        R1_COND["1. Processo tem adiantamento (COT)\n2. Status = FATURADO\n3. Ainda não reconciliado"]
        R2["Calcular FCMP real\n(item a item do processo)"]
        R3["Ajuste = Comissão Adiantada × (FCMP - 1)"]
        R4{"FCMP Real?"}
        R5_ZERO["FCMP = 1.0\n→ Ajuste = R$ 0\n(Sem diferença)"]
        R5_NEG["FCMP < 1.0\n→ Ajuste NEGATIVO\n(Colaborador deve)"]
        R5_POS["FCMP > 1.0\n→ Ajuste POSITIVO\n(Só se config permitir)\n⚠️ Raro com cap=1.0"]
        R6["Registrar no MASTER\nTipo = RECONCILIACAO\nOrigem_Correcao = RECONCILIACAO"]

        R1 --> R1_COND
        R1_COND --> R2 --> R3 --> R4
        R4 -- "= 1.0" --> R5_ZERO
        R4 -- "< 1.0" --> R5_NEG
        R4 -- "> 1.0" --> R5_POS
        R5_ZERO --> R6
        R5_NEG --> R6
        R5_POS --> R6
    end

    ADIANTAMENTO --> TEMPO --> R1

    subgraph EXEMPLO["📋 Exemplo Numérico"]
        direction TB
        EX1["Adiantamento: R$ 10.000\nTCMP: 5% → Comissão: R$ 500\n(FC provisório = 1.0)"]
        EX2["Após faturamento:\nFCMP Real = 0.85"]
        EX3["Reconciliação =\nR$ 500 × (0.85 - 1.0)\n= R$ -75,00\n(DÉBITO)"]
        EX1 --> EX2 --> EX3
    end
```

---

## 8. Processamento de Devoluções

```mermaid
flowchart TB
    START(["Início: Processamento de Devoluções\n(Executado APÓS cálculos de comissão)"])
    
    subgraph LOADER["📂 DevolucaoLoader"]
        L1["Ler dados_entrada/Devoluções.xlsx"]
        L2["Filtrar por Data de Entrada\n= mês/ano de apuração"]
        L3{"Num docorigem\npreenchido?"}
        L3_NO["❌ Ignorar registro\n(~50% dos casos)\nLog: registro sem vínculo"]
        L3_YES["✅ Manter registro"]
        L4{"Valor Produtos > 0?"}
        L4_NO["❌ Descartar"]
        L5["Agrupar devoluções\nmesma NF (somar valores)"]
        
        L1 --> L2 --> L3
        L3 -- "Não" --> L3_NO
        L3 -- "Sim" --> L3_YES --> L4
        L4 -- "Não" --> L4_NO
        L4 -- "Sim" --> L5
    end

    subgraph VINCULACAO["🔗 Vinculação"]
        V1["Buscar Num docorigem\n→ Numero NF na\nAnálise Comercial"]
        V2["Extrair Nº Processo\nvinculado"]
        V3["Obter Valor Realizado\ntotal do processo original"]
    end

    subgraph HISTORICO["🗄️ Consulta Banco Histórico"]
        H1["Buscar comissões pagas\ndo Processo"]
        H2["Filtrar por Tipo_Comissao:\nFATURAMENTO, REGULAR\ne ADIANTAMENTO"]
        H3["Recuperar todos\ncolaboradores afetados"]
    end

    subgraph CALCULATOR["🧮 DevolucaoCalculator"]
        C1["Fator_Devolução =\nValor_Devolvido / Valor_Realizado_Processo"]
        C2["Para CADA colaborador:"]
        C3["Estorno = Comissão_Histórica\n× Fator_Devolução × (-1)"]
        C4["⚠️ Estorno é PROPORCIONAL\nnão item-específico\n(sem granularidade de SKU)"]
    end

    subgraph PERSISTENCIA["💾 Persistência"]
        P1["Salvar no HISTORICO_COMISSOES_MASTER"]
        P2["Tipo_Comissao = DEVOLUCAO"]
        P3["Origem_Correcao = DEVOLUCAO"]
        P4["Processo_Referencia = Processo original"]
        P5["Fator_Devolucao = Fator calculado"]
        P6["Valor = NEGATIVO (débito)"]
    end

    START --> LOADER
    L5 --> V1 --> V2 --> V3
    V3 --> H1 --> H2 --> H3
    H3 --> C1 --> C2 --> C3
    C3 --> P1
    P1 --> P2 & P3 & P4 & P5 & P6
    C3 ~~~ C4
```

---

## 9. Rentabilidade — Componente do FC

```mermaid
flowchart TB
    subgraph PREP["📂 Preparação (Externa)"]
        P1["Arquivo de rentabilidade\nconsolidado externamente"]
        P2["Salvo em:\ndados_entrada/rentabilidades/\n*MM*AAAA*agrupada*.xlsx"]
    end

    subgraph CARGA["📥 Carga no Cálculo"]
        C1["Motor busca arquivo\ncom mês/ano da apuração"]
        C2{"Arquivo\nencontrado?"}
        C3["Carregar DataFrame\nagrupado por hierarquia"]
        C4["DataFrame vazio\n(componente zerado)"]
    end

    subgraph USO["📐 Uso no FC"]
        U1["Para cada item:\nBuscar rentabilidade realizada\nda hierarquia do item"]
        U2["Atingimento =\nRealizado / Meta Rentabilidade"]
        U3["Contribuição =\nmin(Atingimento, cap) × Peso"]
        U4["Entra na soma do FC_rampa"]
    end

    subgraph STATUS["⚠️ Status Atual"]
        S1["Arquivo deve ser entregue\nPRÉ-PROCESSADO"]
        S2["Não há consolidação\nautomática de CSV bruto"]
        S3["📌 FUTURO: Integrar\npreparação ao sistema"]
    end

    P1 --> P2 --> C1 --> C2
    C2 -- "Sim" --> C3 --> U1
    C2 -- "Não" --> C4
    U1 --> U2 --> U3 --> U4
    P1 ~~~ STATUS
```

---

## 10. Taxas de Câmbio — Fornecedores

```mermaid
flowchart TB
    subgraph PRE["🔍 Verificação Prévia (Antes do Cálculo)"]
        direction TB
        P1["Ler METAS_FORNECEDORES.csv"]
        P2["Identificar moedas\n(USD, EUR, etc.)"]
        P3["Verificar JSON de taxas\n(monthly_avg_rates.json)"]
        P4{"Meses faltantes\nno ano atual?"}
        P5["Buscar via API\n(BCB / fallback)"]
        P6["Atualizar JSON"]
        P7["Todas as taxas\npresentes ✅"]
        
        P1 --> P2 --> P3 --> P4
        P4 -- "Sim" --> P5 --> P6 --> P7
        P4 -- "Não" --> P7
    end

    subgraph CALC["💱 Uso no Cálculo do FC"]
        direction TB
        C1["Meta Anual do Fornecedor\n(em moeda original)"]
        C2["Meta YTD proporcional\n= Meta Anual × (mês / 12)"]
        C3["Realizado YTD =\nFaturamento acumulado\npor fornecedor"]
        C4["Converter mês a mês\nusando taxa média mensal"]
        C5["Atingimento =\nRealizado YTD / Meta YTD"]
        C6["Entra no FC como\ncomponente Fornecedor 1 ou 2"]
        
        C1 --> C2
        C3 --> C4 --> C5 --> C6
        C2 --> C5
    end

    P7 --> CALC
```

---

## 11. Estado Persistente de Recebimento

```mermaid
flowchart TB
    subgraph ESTADO["📋 Estado_Processos_Recebimento.xlsx"]
        direction TB
        E1["Por Processo + Colaborador:"]
        E2["• Valor Total do Processo"]
        E3["• Total Adiantamentos (COT)"]
        E4["• Total Pagamentos Regulares"]
        E5["• Comissão Acumulada"]
        E6["• Saldo a Receber"]
        E7["• Status Pagamento"]
        E8["• Status Reconciliação"]
        E9["• Mês/Ano Faturamento"]
        E10["• TCMP / FCMP / FCMP_APLICADO"]
    end

    subgraph CICLO["🔄 Ciclo de Vida do Processo"]
        direction TB
        CV1["Processo criado\n(primeiro pagamento)"]
        CV2["Adiantamentos\nacumulados"]
        CV3["Pagamentos regulares\nacumulados"]
        CV4["Processo FATURADO\n→ Métricas calculadas"]
        CV5["Reconciliação aplicada"]
        CV6["Totalmente pago\n(saldo = 0)"]
        
        CV1 --> CV2 --> CV3 --> CV4 --> CV5 --> CV6
    end

    TRIGGERS["Atualizado a cada\nexecução mensal do motor"]
    TRIGGERS --> ESTADO
    ESTADO --> CICLO
```

---

## 12. Banco Histórico (HISTORICO_COMISSOES_MASTER.xlsx)

```mermaid
flowchart TB
    subgraph TIPOS["📝 Tipos de Registro"]
        direction TB
        T1["FATURAMENTO\n(Comissão por NF emitida)"]
        T2["ADIANTAMENTO\n(Pagamento COT com FC=1.0)"]
        T3["REGULAR\n(Pagamento com FCMP real)"]
        T4["RECONCILIACAO\n(Ajuste pós-faturamento)"]
        T5["DEVOLUCAO\n(Estorno proporcional)"]
    end

    subgraph COLUNAS["📊 Colunas Principais"]
        direction TB
        COL1["Processo / Item / Colaborador"]
        COL2["Cargo / Fatia / FC"]
        COL3["Taxa / Valor / Comissão"]
        COL4["Mês/Ano / Data"]
        COL5["Tipo_Comissao"]
        COL6["Numero_NF"]
        COL7["Origem_Correcao\n(NORMAL / RECONCILIACAO / DEVOLUCAO)"]
        COL8["Processo_Referencia"]
        COL9["Fator_Devolucao"]
    end

    subgraph USOS["🎯 Usos"]
        direction TB
        U1["Consultas históricas"]
        U2["Base para estornos\nem devoluções"]
        U3["Auditoria de\nlongo prazo"]
        U4["Evitar duplic.\nde pagamentos"]
    end

    T1 & T2 & T3 & T4 & T5 --> COLUNAS
    COLUNAS --> USOS
```

---

## 13. Mapa de Decisão do Usuário (Frontend)

```mermaid
flowchart TB
    USER(["👤 Usuário no Frontend"])
    
    subgraph PREP["📤 Preparação"]
        UP1["Upload Análise Comercial"]
        UP2["Upload Análise Financeira"]
        UP3["Garantir Rentabilidade\nagrupada disponível"]
        UP4["Revisar dados carregados"]
    end

    subgraph REGRAS["⚙️ Configuração"]
        R1["Editar Taxas / Pesos"]
        R2["Editar Atribuições"]
        R3["Editar Metas"]
        R4["Configurar Câmbio"]
    end

    EXEC["▶️ Executar Cálculo"]
    
    CS_CHECK{"Cross-Selling\ndetectado?"}
    CS_MODAL["Modal de Decisão:\nProcesso X → Opção A ou B?"]
    RE_EXEC["Re-executar com decisões"]
    
    subgraph RESULTADOS["📊 Resultados"]
        RES1["Comissões Faturamento"]
        RES2["Comissões Recebimento"]
        RES3["Estado dos Processos"]
        RES4["Saldos Negativos"]
    end
    
    EXPORT["📥 Exportar Relatórios"]

    USER --> PREP
    UP1 --> UP2 --> UP3 --> UP4
    USER --> REGRAS
    PREP --> EXEC
    REGRAS --> EXEC
    EXEC --> CS_CHECK
    CS_CHECK -- "Sim" --> CS_MODAL --> RE_EXEC --> RESULTADOS
    CS_CHECK -- "Não" --> RESULTADOS
    RESULTADOS --> EXPORT
```

---

## 14. Diagrama de Saldos Negativos (Consolidação)

```mermaid
flowchart TB
    subgraph FONTES["📍 Fontes de Saldo Negativo"]
        direction TB
        F1["🔄 Reconciliação\n(FCMP < 1.0 após faturamento)"]
        F2["↩️ Devolução\n(Cliente devolveu produtos)"]
    end

    subgraph RECONCILIACAO["Reconciliação"]
        R1["Comissão Adiantada\n(paga com FC=1.0)"]
        R2["FCMP Real < 1.0"]
        R3["Ajuste = Com.Adiant × (FCMP - 1)\n→ NEGATIVO"]
        R1 --> R2 --> R3
    end

    subgraph DEVOLUCAO["Devolução"]
        D1["Valor devolvido pelo cliente"]
        D2["Fator = Devolvido / Realizado"]
        D3["Estorno = Comissão × Fator × (-1)\n→ NEGATIVO"]
        D1 --> D2 --> D3
    end

    subgraph REGISTRO["💾 Registro no MASTER"]
        REG1["Tipo: RECONCILIACAO ou DEVOLUCAO"]
        REG2["Valor: NEGATIVO"]
        REG3["Mês: Apuração corrente"]
        REG4["Colaborador: Identificado"]
    end

    subgraph VISAO["👁️ Visão Consolidada"]
        V1["Frontend: Página Saldos Negativos"]
        V2["Agrupado por colaborador"]
        V3["Detalhado por origem"]
    end

    F1 --> RECONCILIACAO
    F2 --> DEVOLUCAO
    R3 --> REG1
    D3 --> REG1
    REG1 --> REG2 --> REG3 --> REG4
    REG4 --> VISAO
```

---

## 15. Mapa de Módulos do Código (Arquitetura)

```mermaid
flowchart TB
    subgraph ROOT["📁 Raiz (Entry Points)"]
        EP1["calculo_comissoes.py\n(Motor principal ~6480 linhas)"]
        EP2["preparar_dados_mensais.py"]
        EP3["diagnostico_devolucoes.py"]
    end

    subgraph SRC_CORE["📁 src/core"]
        SC1["fc_escada.py\n(Lógica RAMPA/ESCADA)"]
    end

    subgraph SRC_REC["📁 src/recebimento"]
        SR1["recebimento_orchestrator.py"]
        SR2["io/analise_financeira_loader.py"]
        SR3["core/comissao_calculator.py"]
        SR4["reconciliacao/reconciliacao_detector.py"]
        SR5["estado/state_manager.py"]
    end

    subgraph SRC_DEV["📁 src/devolucao"]
        SD1["devolucao_processor.py"]
        SD2["devolucao_loader.py"]
        SD3["devolucao_calculator.py"]
    end

    subgraph SRC_IO["📁 src/io"]
        SI1["config_loader.py\n(Carrega REGRAS_COMISSOES)"]
    end

    subgraph SRC_CURR["📁 src/currency"]
        SCU1["bcb_client.py"]
        SCU2["rate_storage.py"]
        SCU3["rate_fetcher.py"]
        SCU4["rate_validator.py"]
    end

    subgraph FRONTEND["📁 frontend"]
        FE1["adapter/app.py\n(Flask micro-backend)"]
        FE2["src/App.js\n(React SPA)"]
        FE3["src/components/\n(UI Components)"]
    end

    subgraph DATA["📁 Dados"]
        DT1["config/REGRAS_COMISSOES.xlsx"]
        DT2["dados_entrada/*.xlsx"]
        DT3["dados_saida/"]
        DT4["data/currency_rates/*.json"]
    end

    EP1 --> SC1
    EP1 --> SR1
    EP1 --> SD1
    EP1 --> SI1
    EP1 --> SCU1
    SR1 --> SR2 & SR3 & SR4 & SR5
    SD1 --> SD2 & SD3
    FE1 --> EP1
    DT1 --> SI1
    DT2 --> EP1
    EP1 --> DT3
```

---

## 16. ⚠️ Pontos de Atenção / Oportunidades de Melhoria

```mermaid
flowchart TB
    subgraph IMPLEMENTADO["✅ IMPLEMENTADO"]
        direction TB
        I1["Comissões por Faturamento"]
        I2["Comissões por Recebimento"]
        I3["FC Rampa + Escada"]
        I4["Cross-Selling\n(detecção + decisão)"]
        I5["Adiantamentos + Reconciliação"]
        I6["Devoluções Proporcionais"]
        I7["Banco Histórico (MASTER)"]
        I8["Estado Persistente\nRecebimento"]
        I9["Taxas de Câmbio\n(JSON + API BCB)"]
        I10["Rentabilidade como\nComponente do FC"]
    end

    subgraph PENDENTE["🔲 PENDENTE / FUTURO"]
        direction TB
        P1["❌ Tolerância 95% = 100%\n(Regra histórica NÃO ativa)"]
        P2["❌ Processamento Automático\nde Rentabilidade\n(hoje requer arquivo pronto)"]
        P3["❌ PDF Política de\nComissionamento Anual"]
        P4["❌ PDF Auditoria por\nColaborador"]
        P5["❌ Excel Tabela Dinâmica\n(Auditoria)"]
        P6["❌ Dashboard Saldos\nNegativos (Frontend evoluído)"]
    end

    subgraph RISCOS["⚠️ PONTOS DE ATENÇÃO"]
        direction TB
        R1["🔴 Motor monolítico\n(~6480 linhas em 1 arquivo)"]
        R2["🟡 ~50% devoluções sem\nNum docorigem\n(ignoradas silenciosamente)"]
        R3["🟡 Rentabilidade depende\nde arquivo externo pronto"]
        R4["🟡 cap_fc_max = 1.0\nimpede bônus por superação"]
        R5["🟡 Estado de Recebimento\nem Excel\n(risco de corrupção)"]
        R6["🟡 Mapeamento NF→Processo\npor padrão numérico\n(pode falhar em edge cases)"]
    end

    IMPLEMENTADO ~~~ PENDENTE ~~~ RISCOS
```

---

> **Como usar este arquivo:**
> 1. Abra [mermaid.live](https://mermaid.live) ou use a extensão Mermaid no VS Code
> 2. Copie o conteúdo entre os blocos ` ```mermaid ` e ` ``` ` de cada seção
> 3. Cole no editor para gerar a visualização
> 4. Os diagramas são independentes — cada um cobre um aspecto do sistema
