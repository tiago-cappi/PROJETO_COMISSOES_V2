# Banco de Dados de Comissões

Este diretório contém o histórico persistente de todas as comissões calculadas pelo robô.

## Arquivos

- **HISTORICO_COMISSOES_MASTER.xlsx** - Arquivo principal com todas as comissões (append-only audit log).
- **HISTORICO_COMISSOES_MASTER.xlsx.hash** - Hash SHA256 para verificação de integridade.

## Mecanismos de Segurança

1. **Verificação de Lock**: Antes de escrever, o sistema verifica se o arquivo está aberto por outro programa.
2. **Backup Atômico**: Antes de cada escrita, um backup com timestamp é criado em `backups/`.
3. **Integridade (Hash SHA256)**: Após cada escrita, um hash é calculado e salvo para detectar alterações manuais.
4. **Read-Only**: O arquivo é marcado como somente leitura após cada operação para prevenir edições acidentais.
5. **Limpeza Automática**: Backups mais antigos que os últimos 30 são removidos automaticamente.

## Schema do Banco de Dados

| Coluna | Descrição |
|--------|-----------|
| Data_Execucao | Timestamp da execução do cálculo |
| Usuario_Execucao | Usuário do sistema que executou |
| Mes_Referencia | Mês de referência do cálculo |
| Ano_Referencia | Ano de referência do cálculo |
| Tipo_Comissao | FATURAMENTO, ADIANTAMENTO, REGULAR, RECONCILIACAO |
| Processo | Código do processo |
| Nome_Colaborador | Nome do colaborador |
| Cargo | Cargo do colaborador |
| Linha | Linha de negócio |
| Valor_Base | Valor base usado para cálculo |
| TCMP | Taxa de comissão aplicada |
| FC | Fator de correção |
| Comissao_Calculada | Valor final da comissão |
| Cod_Produto | Código do produto |
| Descricao_Produto | Descrição do produto |
| Grupo | Grupo do produto |
| Subgrupo | Subgrupo do produto |
| Tipo_Mercadoria | Tipo de mercadoria |
| Documento | Documento de pagamento (recebimento) |
| Data_Pagamento | Data do pagamento (recebimento) |
| Tipo_Pagamento | ANTECIPACAO, REGULAR (recebimento) |
| Observacao | Observações adicionais |

## Consultas Disponíveis

O módulo `MasterDBManager` oferece métodos para consulta:

```python
from src.io.master_db_manager import MasterDBManager

db = MasterDBManager(base_path=".")

# Consultar histórico com filtros
df = db.get_historico(mes=8, ano=2025, tipo_comissao="FATURAMENTO")

# Resumo por colaborador
resumo = db.get_resumo_por_colaborador(mes=8, ano=2025)

# Resumo por processo
resumo_proc = db.get_resumo_por_processo(mes=8, ano=2025)

# Estatísticas gerais
stats = db.get_estatisticas()
```
