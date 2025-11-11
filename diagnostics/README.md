# Scripts de Diagnóstico e Depuração

Esta pasta contém scripts para diagnosticar problemas e depurar o sistema de cálculo de comissões.

## Scripts Disponíveis

### `diagnostico_rentabilidade.py`

Script para diagnosticar problemas no cálculo do Fator de Correção (FC) de rentabilidade.

**Uso:**
```bash
# Diagnóstico para mês/ano específico
python diagnostics/diagnostico_rentabilidade.py --mes 9 --ano 2025

# Salvar relatório em arquivo
python diagnostics/diagnostico_rentabilidade.py --mes 9 --ano 2025 --output relatorio_rentabilidade.txt
```

**O que verifica:**
1. Se o arquivo de rentabilidade realizada foi carregado corretamente
2. Se as colunas esperadas estão presentes
3. Se o processamento em `_calcular_realizado()` funciona corretamente
4. Se as chaves (linha, grupo, subgrupo, tipo_mercadoria) correspondem entre dados e metas
5. Se há problemas de normalização ou correspondência de valores
6. Exemplos específicos de itens para identificar problemas

**Saída:**
- Relatório detalhado no console
- Opcionalmente salvo em arquivo de texto

## Estrutura

Todos os scripts de diagnóstico devem:
- Ser executáveis independentemente
- Gerar relatórios claros e detalhados
- Não modificar dados do sistema
- Ser seguros para execução em produção (somente leitura)

