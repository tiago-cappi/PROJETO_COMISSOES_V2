/**
 * TabelaEstadoRaw.js
 * 
 * Componente de tabela para exibição completa do estado dos processos.
 * Mostra TODAS as colunas do arquivo Estado_Processos_Recebimento,
 * com tratamento especial para colunas JSON (exibidas como botões clicáveis).
 */

import React, { useState } from 'react';
import {
  Table,
  Tag,
  Button,
  Input,
  Select,
  Space,
  Tooltip,
  Typography,
} from 'antd';
import {
  SearchOutlined,
  FileTextOutlined,
  ReloadOutlined,
  UserOutlined,
} from '@ant-design/icons';
import JsonViewerModal from './JsonViewerModal';

const { Text } = Typography;
const { Option } = Select;

/**
 * Formata valor monetário para exibição.
 */
const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
  }).format(value);
};

/**
 * Formata data para exibição.
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR');
  } catch {
    return dateStr;
  }
};

/**
 * Formata data e hora para exibição.
 */
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
};

/**
 * Configuração das colunas com metadados para renderização.
 */
const COLUMN_CONFIG = {
  PROCESSO: { title: 'Processo', width: 100, fixed: 'left', type: 'text' },
  VALOR_TOTAL_PROCESSO: { title: 'Valor Total', width: 120, type: 'currency', align: 'right' },
  TOTAL_ANTECIPACOES: { title: 'Total Antecipações', width: 130, type: 'currency', align: 'right' },
  TOTAL_PAGAMENTOS_REGULARES: { title: 'Pag. Regulares', width: 120, type: 'currency', align: 'right' },
  TOTAL_PAGO_ACUMULADO: { title: 'Total Pago', width: 110, type: 'currency', align: 'right' },
  SALDO_A_RECEBER: { title: 'Saldo', width: 110, type: 'currency', align: 'right' },
  TOTAL_COMISSAO_ANTECIPACOES: { title: 'Comis. Antecip.', width: 120, type: 'currency', align: 'right' },
  TOTAL_COMISSAO_REGULARES: { title: 'Comis. Regular', width: 120, type: 'currency', align: 'right' },
  TOTAL_COMISSAO_ACUMULADA: { title: 'Comis. Acum.', width: 110, type: 'currency', align: 'right' },
  STATUS_PROCESSO: { title: 'Status Processo', width: 130, type: 'status_processo' },
  STATUS_PAGAMENTO: { title: 'Status Pag.', width: 110, type: 'status_pagamento' },
  STATUS_CALCULO_MEDIAS: { title: 'Status Cálculo', width: 120, type: 'status_calculo' },
  MES_ANO_FATURAMENTO: { title: 'Mês/Ano Fat.', width: 100, type: 'text' },
  TCMP_JSON: { title: 'TCMP', width: 90, type: 'json', jsonType: 'tcmp' },
  FCMP_JSON: { title: 'FCMP', width: 90, type: 'json', jsonType: 'fcmp' },
  TCMP_DETALHES_JSON: { title: 'TCMP Det.', width: 100, type: 'json', jsonType: 'tcmp_detalhes' },
  FCMP_DETALHES_JSON: { title: 'FCMP Det.', width: 100, type: 'json', jsonType: 'fcmp_detalhes' },
  COLABORADORES_ENVOLVIDOS: { title: 'Colaboradores', width: 180, type: 'colaboradores' },
  DATA_PRIMEIRO_PAGAMENTO: { title: '1º Pagamento', width: 110, type: 'date' },
  DATA_ULTIMO_PAGAMENTO: { title: 'Último Pag.', width: 110, type: 'date' },
  QUANTIDADE_PAGAMENTOS: { title: 'Qtd. Pag.', width: 80, type: 'number', align: 'center' },
  ULTIMA_ATUALIZACAO: { title: 'Última Atualiz.', width: 140, type: 'datetime' },
  COMISSOES_ADIANTADAS_JSON: { title: 'Comis. Adiant.', width: 110, type: 'json', jsonType: 'comissoes_adiantadas' },
  STATUS_RECONCILIACAO: { title: 'Reconciliação', width: 110, type: 'status_reconciliacao' },
  OBSERVACOES: { title: 'Observações', width: 150, type: 'text', ellipsis: true },
};

/**
 * Cores para tags de status.
 */
const STATUS_COLORS = {
  status_processo: {
    FATURADO: 'green',
    PENDENTE: 'orange',
    ORCAMENTO: 'blue',
    CANCELADO: 'red',
  },
  status_pagamento: {
    COMPLETO: 'green',
    PARCIAL: 'blue',
    PENDENTE: 'orange',
  },
  status_calculo: {
    CALCULADO: 'green',
    PARCIAL: 'blue',
    PENDENTE: 'orange',
  },
  status_reconciliacao: {
    CONCLUIDA: 'green',
    PENDENTE: 'orange',
  },
};

/**
 * Tabela de estado raw com todas as colunas.
 * 
 * @param {Object} props
 * @param {Array} props.dados - Lista de processos
 * @param {Array} props.colunas - Lista de nomes de colunas
 * @param {boolean} props.loading - Estado de carregamento
 * @param {Function} props.onRefresh - Callback para recarregar dados
 * @param {Object} props.filters - Filtros atuais
 * @param {Function} props.onFiltersChange - Callback para mudança de filtros
 */
const TabelaEstadoRaw = ({
  dados = [],
  colunas = [],
  loading = false,
  onRefresh,
  filters = {},
  onFiltersChange,
}) => {
  const [searchText, setSearchText] = useState('');
  const [jsonModal, setJsonModal] = useState({ visible: false, title: '', tipo: '', data: null });

  // Filtrar dados localmente pelo texto de busca
  const filteredData = dados.filter((p) => {
    if (!searchText) return true;
    const search = searchText.toLowerCase();
    return (
      (p.PROCESSO && p.PROCESSO.toLowerCase().includes(search)) ||
      (p.COLABORADORES_ENVOLVIDOS && p.COLABORADORES_ENVOLVIDOS.some((c) => c.toLowerCase().includes(search)))
    );
  });

  const handleOpenJsonModal = (title, tipo, data) => {
    setJsonModal({ visible: true, title, tipo, data });
  };

  const handleCloseJsonModal = () => {
    setJsonModal({ visible: false, title: '', tipo: '', data: null });
  };

  /**
   * Verifica se um objeto JSON tem dados válidos.
   */
  const hasJsonData = (data) => {
    if (!data) return false;
    if (typeof data === 'object' && Object.keys(data).length === 0) return false;
    return true;
  };

  /**
   * Gera as colunas da tabela dinamicamente baseado nas colunas do arquivo.
   */
  const generateColumns = () => {
    // Usar ordem definida em COLUMN_CONFIG, mas apenas para colunas presentes
    const orderedColumns = Object.keys(COLUMN_CONFIG).filter((col) => colunas.includes(col));
    
    // Adicionar colunas não mapeadas ao final
    const unmappedColumns = colunas.filter((col) => !COLUMN_CONFIG[col]);
    const allColumns = [...orderedColumns, ...unmappedColumns];

    return allColumns.map((colName) => {
      const config = COLUMN_CONFIG[colName] || { title: colName, width: 120, type: 'text' };

      const baseColumn = {
        title: config.title,
        dataIndex: colName,
        key: colName,
        width: config.width,
        fixed: config.fixed,
        align: config.align,
        ellipsis: config.ellipsis,
        sorter: (a, b) => {
          const valA = a[colName];
          const valB = b[colName];
          if (typeof valA === 'number' && typeof valB === 'number') {
            return valA - valB;
          }
          return String(valA || '').localeCompare(String(valB || ''));
        },
      };

      // Renderizadores específicos por tipo
      switch (config.type) {
        case 'currency':
          return {
            ...baseColumn,
            render: (value) => (
              <Text style={{ color: value < 0 ? '#ff4d4f' : undefined }}>
                {formatCurrency(value)}
              </Text>
            ),
          };

        case 'date':
          return {
            ...baseColumn,
            render: (value) => formatDate(value),
          };

        case 'datetime':
          return {
            ...baseColumn,
            render: (value) => formatDateTime(value),
          };

        case 'number':
          return {
            ...baseColumn,
            render: (value) => (value !== null && value !== undefined ? value : '-'),
          };

        case 'status_processo':
          return {
            ...baseColumn,
            filters: [
              { text: 'Faturado', value: 'FATURADO' },
              { text: 'Pendente', value: 'PENDENTE' },
              { text: 'Orçamento', value: 'ORCAMENTO' },
            ],
            onFilter: (value, record) => record[colName] === value,
            render: (status) => (
              <Tag color={STATUS_COLORS.status_processo[status] || 'default'}>
                {status || '-'}
              </Tag>
            ),
          };

        case 'status_pagamento':
          return {
            ...baseColumn,
            filters: [
              { text: 'Completo', value: 'COMPLETO' },
              { text: 'Parcial', value: 'PARCIAL' },
              { text: 'Pendente', value: 'PENDENTE' },
            ],
            onFilter: (value, record) => record[colName] === value,
            render: (status) => (
              <Tag color={STATUS_COLORS.status_pagamento[status] || 'default'}>
                {status || '-'}
              </Tag>
            ),
          };

        case 'status_calculo':
          return {
            ...baseColumn,
            filters: [
              { text: 'Calculado', value: 'CALCULADO' },
              { text: 'Parcial', value: 'PARCIAL' },
              { text: 'Pendente', value: 'PENDENTE' },
            ],
            onFilter: (value, record) => record[colName] === value,
            render: (status) => (
              <Tag color={STATUS_COLORS.status_calculo[status] || 'default'}>
                {status || '-'}
              </Tag>
            ),
          };

        case 'status_reconciliacao':
          return {
            ...baseColumn,
            filters: [
              { text: 'Concluída', value: 'CONCLUIDA' },
              { text: 'Pendente', value: 'PENDENTE' },
            ],
            onFilter: (value, record) => record[colName] === value,
            render: (status) => (
              <Tag color={STATUS_COLORS.status_reconciliacao[status] || 'default'}>
                {status || '-'}
              </Tag>
            ),
          };

        case 'colaboradores':
          return {
            ...baseColumn,
            render: (colaboradores) => {
              if (!colaboradores || colaboradores.length === 0) {
                return <Text type="secondary">-</Text>;
              }
              const visibleCount = 2;
              const visible = colaboradores.slice(0, visibleCount);
              const remaining = colaboradores.length - visibleCount;
              
              return (
                <div>
                  {visible.map((col, idx) => (
                    <Tag key={idx} icon={<UserOutlined />} style={{ marginBottom: 2 }}>
                      {col.length > 12 ? `${col.substring(0, 12)}...` : col}
                    </Tag>
                  ))}
                  {remaining > 0 && (
                    <Tooltip title={colaboradores.slice(visibleCount).join(', ')}>
                      <Tag>+{remaining}</Tag>
                    </Tooltip>
                  )}
                </div>
              );
            },
          };

        case 'json':
          return {
            ...baseColumn,
            render: (value, record) => {
              const hasData = hasJsonData(value);
              return (
                <Tooltip title={hasData ? 'Clique para ver detalhes' : 'Sem dados'}>
                  <Button
                    type={hasData ? 'link' : 'text'}
                    size="small"
                    icon={<FileTextOutlined />}
                    disabled={!hasData}
                    onClick={() => handleOpenJsonModal(
                      `${config.title} - Processo ${record.PROCESSO}`,
                      config.jsonType,
                      value
                    )}
                  >
                    {hasData ? 'Ver' : '-'}
                  </Button>
                </Tooltip>
              );
            },
          };

        default:
          return {
            ...baseColumn,
            render: (value) => value || '-',
          };
      }
    });
  };

  const columns = generateColumns();

  // Calcular largura total para scroll horizontal
  const totalWidth = columns.reduce((sum, col) => sum + (col.width || 120), 0);

  return (
    <div>
      {/* Barra de Ferramentas */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="Buscar processo, colaborador..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 250 }}
          allowClear
        />
        
        <Select
          placeholder="Status Processo"
          style={{ width: 150 }}
          allowClear
          value={filters.statusProcesso}
          onChange={(value) => onFiltersChange?.({ ...filters, statusProcesso: value })}
        >
          <Option value="FATURADO">Faturado</Option>
          <Option value="PENDENTE">Pendente</Option>
          <Option value="ORCAMENTO">Orçamento</Option>
        </Select>

        <Select
          placeholder="Status Pagamento"
          style={{ width: 150 }}
          allowClear
          value={filters.statusPagamento}
          onChange={(value) => onFiltersChange?.({ ...filters, statusPagamento: value })}
        >
          <Option value="PENDENTE">Pendente</Option>
          <Option value="PARCIAL">Parcial</Option>
          <Option value="COMPLETO">Completo</Option>
        </Select>

        <Select
          placeholder="Status Cálculo"
          style={{ width: 150 }}
          allowClear
          value={filters.statusCalculo}
          onChange={(value) => onFiltersChange?.({ ...filters, statusCalculo: value })}
        >
          <Option value="PENDENTE">Pendente</Option>
          <Option value="PARCIAL">Parcial</Option>
          <Option value="CALCULADO">Calculado</Option>
        </Select>

        <Button
          icon={<ReloadOutlined />}
          onClick={onRefresh}
          loading={loading}
        >
          Atualizar
        </Button>
      </Space>

      {/* Tabela */}
      <Table
        columns={columns}
        dataSource={filteredData.map((p, idx) => ({ ...p, key: p.PROCESSO || idx }))}
        loading={loading}
        size="small"
        scroll={{ x: totalWidth }}
        pagination={{
          defaultPageSize: 20,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} processos`,
        }}
        bordered
      />

      {/* Modal de JSON */}
      <JsonViewerModal
        visible={jsonModal.visible}
        onClose={handleCloseJsonModal}
        title={jsonModal.title}
        tipo={jsonModal.tipo}
        data={jsonModal.data}
      />
    </div>
  );
};

export default TabelaEstadoRaw;
