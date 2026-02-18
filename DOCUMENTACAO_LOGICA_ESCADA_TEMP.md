# DOCUMENTAÇÃO DA LÓGICA DE COMISSÕES: ESCADA VS. RAMPA

Esta documentação detalha a nova lógica de cálculo de comissões, que introduz o conceito de "Escada" (degraus de atingimento) como alternativa à "Rampa" (proporcionalidade linear).

---

## 1. Visão Geral: O Que Mudou?

Antes, o sistema utilizava exclusivamente a lógica de **RAMPA**:
- O Fator de Correção (FC) era idêntico à performance.
- Exemplo: Se o vendedor atingisse 95% da meta, seu multiplicador era 0.95.

Agora, o sistema suporta a lógica de **ESCADA** configurável por cargo:
- O FC pode ser transformado em degraus fixos.
- Exemplo: Se o vendedor atingir entre 90% e 99% da meta, ele cai numa faixa fixa (ex: 90%), sem ganhar os decimais extras. Para ganhar mais, ele precisa saltar para o próximo degrau (100%).

### 🧪 Diferença Visual

| Performance (Meta) | Modo RAMPA (Antigo) | Modo ESCADA (Novo - Exemplo) |
|--------------------|---------------------|-----------------------------|
| 50%                | Multiplicador = 0.50| Piso (ex: 0.20)             |
| 75%                | Multiplicador = 0.75| Degrau 2 (ex: 0.50)         |
| 99.9%              | Multiplicador = 0.99| Degrau 3 (ex: 0.80)         |
| 100%               | Multiplicador = 1.00| Topo (1.00)                 |

---

## 2. Configuração (Excel)

A regra é definida na aba **`FC_ESCADA_CARGOS`** do arquivo `REGRAS_COMISSOES.xlsx`.

| Coluna        | Descrição                                                                 | Exemplo       |
|---------------|---------------------------------------------------------------------------|---------------|
| `cargo`       | Nome exato do cargo (deve bater com o cadastro de colaboradores).         | Vendedor      |
| `modo`        | `RAMPA` (comportamento padrão) ou `ESCADA`.                               | ESCADA        |
| `num_degraus` | Quantos níveis existem, contando desde o piso até o topo (100%).          | 5             |
| `piso_pct`    | Percentual do teto que representa o primeiro degrau (chão).               | 20 (para 20%) |

---

## 3. Lógica Matemática detalhada

### 3.1. Definições

*   $FC_{rampa}$: A performance calculada (0.0 a ≥1.0), baseada no atingimento de metas.
*   $N$: Número de degraus (`num_degraus`).
*   $P$: Piso (`piso_pct` / 100).
*   $i$: Índice do degrau atual ($0$ a $N-1$).

### 3.2. Fórmula dos Degraus

A escada divide a performance de 0% a 100% em $N-1$ intervalos iguais.

**Passo 1: Encontrar o Índice do Degrau ($i$)**

O sistema é **SEM TOLERÂNCIA**. O índice é calculado arredondando para baixo (floor) a performance ajustada pela quantidade de intervalos.
$$ i = \lfloor FC_{rampa} \times (N - 1) \rfloor $$

*Regras de Borda:*
*   Se $FC_{rampa} \ge 1.0 \implies i = N-1$ (Atinge o Topo).
*   O índice máximo para $FC_{rampa} < 1.0$ é $N-2$ (Penúltimo degrau).

**Passo 2: Calcular o Multiplicador ($M$)**

O multiplicador final é uma interpolação linear entre o Piso ($P$) e o Teto ($1.0$) baseada no degrau atingido.

$$ M = P + i \times \left( \frac{1.0 - P}{N - 1} \right) $$

---

## 4. Aplicação Prática

### Cenário 1: Pagamento por Faturamento
*(Comissão calculada item a item no momento da venda)*

1.  O robô calcula o **FC do Item** ($FC_{item}$) usando a regra de metas (Rampa).
2.  Consulta a configuração do cargo do vendedor.
3.  Se for `ESCADA`, aplica a função matemática acima:
    $$ FC_{aplicado} = \text{Escada}(FC_{item}, \text{Cargo}) $$
4.  Calcula a comissão final:
    $$ \text{Comissão} = \text{Comissão Potencial} \times FC_{aplicado} $$

### Cenário 2: Pagamento por Recebimento (Financeiro)
*(Comissão paga quando o cliente paga o boleto - parcelado)*

Aqui a lógica é mais sutil para manter a justiça matemática. Não aplicamos a escada em cada item individualmente, mas sim na **média do processo**.

1.  **Cálculo das Métricas (Mês do Faturamento):**
    *   Calcula o $FC_{item}$ de cada produto em modo **RAMPA** (Performance real).
    *   Calcula o **FCMP** (Fator de Correção Médio Ponderado) do processo:
        $$ FCMP_{rampa} = \frac{\sum (Valor_{item} \times FC_{item})}{\sum Valor_{item}} $$
    *   *Nota:* O $FCMP_{rampa}$ é salvo no Banco de Dados (Estado).

2.  **Aplicação do Pagamento (Mês do Recebimento):**
    *   O robô recupera o $FCMP_{rampa}$.
    *   Aplica a regra de Escada sobre a média:
        $$ FCMP_{aplicado} = \text{Escada}(FCMP_{rampa}, \text{Cargo}) $$
    *   Calcula a parcela a pagar:
        $$ \text{Parcela} = \text{Valor Recebido} \times TCMP \times FCMP_{aplicado} $$

**Por que isso é importante?**
Se aplicássemos a escada em cada item antes da média, um vendedor poderia ser prejudicado se tivesse muitos itens pequenos em degraus baixos, mesmo que a venda total fosse ótima. Aplicar a escada na **média final** garante que a "nota final" do vendedor seja avaliada.

---

## 5. Exemplo Numérico

**Configuração:**
- Cargo: Vendedor
- Modo: ESCADA
- Degraus ($N$): 5
- Piso ($P$): 0.20 (20%)

**Intervalos:**
Com 5 degraus, temos $N-1 = 4$ intervalos.
Cada intervalo requer $0.25$ (25%) de performance para subir.

**Mapeamento:**

| Performance Real (Rampa) | Índice ($i$) | Cálculo do Multiplicador                                | Multiplicador Final |
|--------------------------|--------------|---------------------------------------------------------|---------------------|
| 0.00 a 0.249             | 0            | $0.20 + 0 \times 0.20$                                  | **0.20** (Piso)     |
| 0.25 a 0.499             | 1            | $0.20 + 1 \times 0.20$                                  | **0.40**            |
| 0.50 a 0.749             | 2            | $0.20 + 2 \times 0.20$                                  | **0.60**            |
| 0.75 a 0.999             | 3            | $0.20 + 3 \times 0.20$                                  | **0.80**            |
| $\ge$ 1.00               | 4            | $0.20 + 4 \times 0.20$                                  | **1.00** (Topo)     |

*Observe que com 0.74 de performance, o vendedor cai no degrau 0.60. Ele precisa de 0.75 cravado para subir para 0.80.*

---

## 6. Auditoria no Sistema

Para verificar qual regra foi aplicada:

1.  **Nos Relatórios (Excel):**
    *   Procure as colunas `fc_escada_modo`, `fc_escada_degrau_indice` e `fator_correcao_fc_rampa`.
    *   A coluna `fator_correcao_fc` sempre conterá o valor final efetivamente pago.

2.  **No Frontend (Painel Web):**
    *   Abra "Ver Detalhes" de um cálculo.
    *   Se a lógica for Escada, aparecerá um bloco azul **"🪜 Regra de Escada Aplicada"**.
    *   Você verá lado a lado o *FC Rampa* (Performance) e o *FC Final* (Pagamento).
