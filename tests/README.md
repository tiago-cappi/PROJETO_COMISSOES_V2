# Testes de Lógica de Cálculos

Esta pasta contém testes para validar a lógica de cálculo de comissões.

## Estrutura de Testes

### Testes de Utilitários (`test_utils.py`)
Testa funções utilitárias básicas:
- Normalização de texto
- Cálculo de atingimento
- Funções de estilização

### Testes de Loaders (`test_loaders.py`)
Testa os módulos de carregamento de dados:
- `ConfigLoader`: carregamento de configurações
- `DataLoader`: carregamento de dados de entrada
- Integração entre loaders

### Testes do Preparador (`test_preparador_dados.py`)
Valida o script `preparar_dados_mensais.py`:
- Geração de arquivos mensais
- Detecção automática de mês/ano
- Validação de arquivos de saída

### Testes de Validação de Comissões (`test_validar_comissoes_faturamento.py`)
Valida o cálculo de comissões por faturamento:
- Estrutura do arquivo de saída
- Cálculo item a item
- Validação de fórmulas

## Como Executar

```bash
# Executar todos os testes
python -m pytest tests/

# Executar teste específico
python tests/test_utils.py
python tests/test_loaders.py
python tests/test_preparador_dados.py
python tests/test_validar_comissoes_faturamento.py
```

## Convenções

- Testes devem ser independentes e não dependerem de ordem de execução
- Testes devem limpar dados temporários após execução
- Testes devem fornecer mensagens claras de erro
- Testes devem validar tanto casos de sucesso quanto de falha

