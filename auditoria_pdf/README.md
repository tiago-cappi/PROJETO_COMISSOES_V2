# Sistema de Auditoria PDF para Comissões por Recebimento

## Visão Geral

Este módulo é responsável por gerar relatórios PDF de auditoria detalhados para as comissões calculadas por recebimento. O PDF contém toda a rastreabilidade dos cálculos, mostrando passo a passo como foram calculados o TCMP (Taxa de Comissão Média Ponderada) e o FCMP (Fator de Correção Médio Ponderado) para cada processo com pagamentos recebidos.

## Estrutura do Projeto

```
auditoria_pdf/
├── __init__.py                    # Pacote principal
├── auditoria_orchestrator.py     # Orquestrador principal
├── core/                          # Lógica de negócio
│   ├── __init__.py
│   ├── data_collector.py          # Coleta dados dos processos
│   └── audit_data_builder.py      # Formata dados para o PDF
├── generators/                    # Geradores de seções do PDF
│   ├── __init__.py
│   ├── pdf_generator.py           # Gerador principal
│   ├── section_header.py          # Capa, índice, separadores
│   ├── section_processo.py        # Dados do processo e itens
│   ├── section_pagamentos.py      # Pagamentos recebidos
│   ├── section_colaboradores.py   # Colaboradores identificados
│   ├── section_tcmp.py            # Cálculo detalhado de TCMP
│   ├── section_fcmp.py            # Cálculo detalhado de FCMP
│   ├── section_comissoes.py       # Comissões calculadas
│   └── section_resumo.py          # Resumo consolidado
├── styles/                        # Estilos visuais
│   ├── __init__.py
│   ├── pdf_styles.py              # Cores, fontes, estilos
│   └── table_builder.py           # Construtor de tabelas
└── utils/                         # Utilitários
    ├── __init__.py
    ├── formatters.py              # Formatação de valores
    └── pdf_utils.py               # Helpers gerais
```

## Fluxo de Geração do PDF

### 1. Coleta de Dados (`AuditoriaDataCollector`)

O `AuditoriaDataCollector` é responsável por reunir todos os dados necessários:

- **Processos com comissões**: Identifica processos que tiveram comissões calculadas no mês
- **Dados comerciais**: Busca informações completas na `Analise_Comercial_Completa.csv`
- **Pagamentos**: Extrai pagamentos do arquivo `ESTADO`
- **Colaboradores**: Identifica todos os colaboradores envolvidos (operacionais e gestão)
- **Cálculos de TCMP**: Coleta detalhes do cálculo de taxa por item
- **Cálculos de FCMP**: Coleta detalhes do FC por item com componentes
- **Comissões**: Extrai comissões calculadas do estado

### 2. Preparação dos Dados (`AuditDataBuilder`)

O `AuditDataBuilder` transforma dados brutos em estruturas formatadas:

- Aplica formatação de moeda (R$ 1.234,56)
- Aplica formatação de percentual (12,34%)
- Aplica formatação de datas (15/09/2025)
- Calcula estatísticas agregadas
- Prepara dados para tabelas

### 3. Geração do PDF (`AuditoriaPDFGenerator`)

O gerador constrói o PDF em seções:

#### 3.1. Capa
- Título do relatório
- Período de apuração
- Data/hora de geração
- Descrição do relatório

#### 3.2. Índice
- Lista de todos os processos auditados
- Informações resumidas (cliente, valor)

#### 3.3. Para Cada Processo

**Seção 1: Dados do Processo**
- Processo, Status, Data de Emissão
- Número NF, Cliente, Operação, Valor Total
- Fonte: Análise Comercial

**Seção 2: Itens do Processo**
- Tabela com todos os itens
- Código, Linha, Grupo, Subgrupo, Tipo, Valor
- Fonte: Análise Comercial

**Seção 3: Pagamentos Recebidos**
- Tipo (Adiantamento/Regular)
- Documento, Data de Baixa, Valor
- Total de pagamentos
- Fonte: Análise Financeira

**Seção 4: Colaboradores Identificados**
- Colaboradores operacionais (da Análise Comercial)
- Colaboradores de gestão (de ATRIBUICOES.csv)
- Nome, Cargo, Origem

**Seção 5: Cálculo de TCMP**
- Detalhamento por item
- Taxas por colaborador (taxa_rateio × fatia_cargo)
- Fórmula da média ponderada
- TCMP final por colaborador
- Fonte: CONFIG_COMISSAO.csv

**Seção 6: Cálculo de FCMP**
- Detalhamento por item
- Componentes do FC (apenas com peso > 0)
  - Peso, Realizado, Meta, Atingimento, Componente FC
- FC do item por colaborador
- Fórmula da média ponderada
- FCMP final por colaborador
- Fontes: Faturados.xlsx, Conversoes.xlsx, etc.

**Seção 7: Comissões Calculadas**
- Fórmulas aplicadas
  - Adiantamento: `Comissão = Valor × TCMP × 1,0`
  - Regular: `Comissão = Valor × TCMP × FCMP`
- Tabelas de comissões por tipo
- Total geral de comissões

**Seção 8: Resumo Consolidado**
- Resumo geral do processo
- Totais de pagamentos e comissões
- Resumo por colaborador

## Como Usar

### Integração Automática

O PDF é gerado automaticamente ao final do cálculo de comissões por recebimento, se:

1. **ReportLab está instalado**: A biblioteca `reportlab` deve estar disponível
2. **Parâmetro ativado**: `gerar_pdf_auditoria = True` em `config/PARAMS.csv`

### Uso Programático

```python
from auditoria_pdf import AuditoriaOrchestrator

# Criar orquestrador
auditoria = AuditoriaOrchestrator(
    recebimento_orchestrator=receb_orch,
    calc_comissao=calc_instance,
    mes=9,
    ano=2025,
    base_path="."
)

# Gerar PDF
arquivo_pdf = auditoria.gerar_auditoria()

if arquivo_pdf:
    print(f"PDF gerado: {arquivo_pdf}")
```

### Arquivo Gerado

- **Nome**: `Auditoria_Recebimento_MM_AAAA.pdf`
- **Local**: Mesmo diretório dos outros arquivos de saída
- **Exemplo**: `Auditoria_Recebimento_09_2025.pdf`

## Configuração

### Parâmetro em `config/PARAMS.csv`

```csv
chave;valor;observacao
gerar_pdf_auditoria;True;Gerar PDF de auditoria para comissões por recebimento
```

- **True**: Gera o PDF automaticamente
- **False**: Não gera o PDF

### Dependências

O módulo requer a biblioteca **ReportLab**:

```bash
pip install reportlab
```

Se ReportLab não estiver disponível, o sistema continuará funcionando normalmente, apenas não gerará o PDF de auditoria.

## Estilos e Personalização

### Cores

Definidas em `styles/pdf_styles.py`:

- `COR_PRIMARIA`: #2C3E50 (Azul escuro) - Headers
- `COR_DESTAQUE`: #3498DB (Azul claro) - Destaques
- `COR_SUCESSO`: #27AE60 (Verde) - Valores positivos
- `COR_ALERTA`: #F39C12 (Laranja) - Alertas
- `COR_ERRO`: #E74C3C (Vermelho) - Erros

### Estilos de Texto

- `STYLE_TITULO_PRINCIPAL`: Título da capa (24pt, negrito)
- `STYLE_TITULO_SECAO`: Títulos de seção (18pt, negrito)
- `STYLE_SUBTITULO_SECAO`: Subtítulos (14pt, negrito)
- `STYLE_CORPO`: Texto normal (10pt)
- `STYLE_MONO`: Código/números (9pt, monospace)
- `STYLE_FORMULA`: Fórmulas matemáticas (10pt, fundo cinza)

### Tabelas

Três estilos disponíveis via `TableBuilder`:

1. **Simples**: Tabela básica com grid
2. **Listrada**: Linhas alternadas (zebrada)
3. **Destaque**: Borda destacada para valores importantes

## Logs de Depuração

O sistema gera logs detalhados prefixados com `[AUDITORIA]`:

```
[AUDITORIA] [COLETA] Iniciando coleta de dados...
[AUDITORIA] [COLETA] 3 processo(s) com comissões no mês
[AUDITORIA] [PDF] Gerando capa...
[AUDITORIA] [PDF] Gerando seções para 3 processo(s)...
[AUDITORIA] [PDF] PDF gerado com sucesso: Auditoria_Recebimento_09_2025.pdf
```

## Tratamento de Erros

O sistema é resiliente a erros:

- Se não houver processos com comissões, retorna `None` sem gerar PDF
- Se houver erro na geração, loga o traceback completo mas não interrompe o fluxo principal
- Se ReportLab não estiver disponível, apenas loga aviso

## Extensibilidade

### Adicionar Nova Seção

1. Criar arquivo em `generators/section_nova.py`
2. Implementar função `gerar_secao_nova(story, dados)`
3. Importar e chamar em `pdf_generator.py`

### Adicionar Novo Estilo

1. Definir em `styles/pdf_styles.py`
2. Exportar via `styles/__init__.py`
3. Usar nos geradores de seção

### Adicionar Nova Formatação

1. Implementar em `utils/formatters.py`
2. Exportar via `utils/__init__.py`
3. Usar em `audit_data_builder.py`

## Limitações Conhecidas

1. **Tamanho do PDF**: PDFs grandes (>100 páginas) podem demorar para gerar
2. **Componentes FC**: Apenas componentes com peso > 0 são mostrados
3. **Idioma**: Textos fixos em português
4. **Layout**: Otimizado para A4, pode não funcionar bem em outros tamanhos

## Exemplos de Uso

### Desativar Geração de PDF

Em `config/PARAMS.csv`:

```csv
gerar_pdf_auditoria;False;
```

### Gerar Apenas para Processos Específicos

Atualmente não há filtro. Para implementar:

1. Modificar `AuditoriaDataCollector._identificar_processos_com_comissoes()`
2. Adicionar parâmetro de filtro
3. Aplicar filtro na lista de processos

## Manutenção

### Verificar Logs

Buscar por `[AUDITORIA]` nos logs do terminal:

```bash
python calculo_comissoes.py | grep "\[AUDITORIA\]"
```

### Testar Geração

```python
# Em um ambiente de teste
from auditoria_pdf import AuditoriaOrchestrator

# ... configurar objetos necessários ...

arquivo = auditoria.gerar_auditoria()
```

## Suporte

Para problemas ou dúvidas:

1. Verificar logs com prefixo `[AUDITORIA]`
2. Confirmar que ReportLab está instalado
3. Verificar parâmetro em `PARAMS.csv`
4. Consultar documentação em `documentacoes/COMISSOES_POR_RECEBIMENTO_DETALHADO.md`

