# Adapter FastAPI - Robô de Comissões

Backend adapter que orquestra o robô de comissões sem alterar a lógica existente.

## Características

- **Apenas orquestração**: Não contém regras de negócio
- **Subprocesso**: Dispara `calculo_comissoes.py` como subprocesso
- **Preservação**: Mantém ordem de colunas e abas do Excel
- **Progresso**: Sistema de progresso via JSON

## Configuração

1. Instalar dependências:
```powershell
pip install -r requirements.txt
```

2. Configurar variável de ambiente (opcional):
```powershell
$env:ROBO_ROOT_PATH="C:\caminho\para\PROJETO_COMISSOES_V2"
```

Ou criar `.env` na pasta `adapter/`:
```env
ROBO_ROOT_PATH=C:\caminho\para\PROJETO_COMISSOES_V2
```

**Nota**: Se não configurar, o adapter usará automaticamente o diretório pai (raiz do projeto).

## Estrutura de Arquivos Esperada

O adapter espera a seguinte estrutura:
```
PROJETO_COMISSOES_V2/
├── config/
│   └── REGRAS_COMISSOES.xlsx  # Arquivo de regras
├── dados_entrada/
│   ├── Analise_Comercial_Completa.xlsx
│   ├── Análise Financeira.xlsx
│   └── rentabilidades/
│       └── rentabilidade_MM_AAAA_agrupada.xlsx
├── calculo_comissoes.py
└── preparar_dados_mensais.py
```

## Execução

```powershell
uvicorn app:app --reload --port 8000
```

Documentação: `http://localhost:8000/docs`

## Endpoints Principais

### Regras
- `GET /regras/abas` - Lista abas disponíveis
- `GET /regras/aba/{nome}` - Lê aba com paginação
- `POST /regras/aba/{nome}/save` - Salva alterações
- `POST /regras/aba/{nome}/apply-bulk` - Aplicação em massa

### Uploads
- `POST /upload/analise` - Analise_Comercial_Completa (salvo em `dados_entrada/`)
- `POST /upload/fin_adcli` - fin_adcli_pg_m3.xls
- `POST /upload/fin_conci` - fin_conci_adcli_m3.xls
- `POST /upload/analise_financeira` - Análise Financeira.xlsx (salvo em `dados_entrada/`)
- `POST /upload/devolucoes` - Devoluções.xlsx (salvo em `dados_entrada/`)

### Execução
- `POST /calcular?mes=MM&ano=AAAA` - Inicia cálculo
- `GET /progresso/{jobId}` - Consulta progresso

### Resultados
- `GET /resultado/abas` - Lista abas do resultado
- `GET /resultado/aba/{nome}` - Lê aba com paginação
- `GET /baixar/resultado` - Download do Excel completo

