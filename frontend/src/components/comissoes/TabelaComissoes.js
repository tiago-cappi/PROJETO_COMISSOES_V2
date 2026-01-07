import React, { useMemo } from 'react';
import { Table, Tag, Button, Tooltip, Typography } from 'antd';
import { EyeOutlined } from '@ant-design/icons';

const { Text } = Typography;

const formatCurrency = (value) => {
  if (value === undefined || value === null) return '-';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

const TabelaComissoes = ({ data, type, loading, onViewDetails }) => {
  const columns = useMemo(() => {
    const baseColumns = [
      {
        title: 'Processo',
        dataIndex: 'processo',
        key: 'processo',
        width: 120,
        fixed: 'left',
        render: (text) => <Text strong style={{ color: '#1890ff' }}>{text}</Text>,
        sorter: (a, b) => (a.processo || '').localeCompare(b.processo || ''),
      },
    ];

    if (type === 'faturamento') {
      return [
        ...baseColumns,
        {
          title: 'Itens',
          key: 'total_itens',
          width: 90,
          align: 'center',
          render: (_, record) => <Text strong>{record.total_itens ?? (record.items || []).length ?? '-'}</Text>,
        },
        {
          title: 'Colaboradores',
          key: 'total_colaboradores',
          width: 130,
          align: 'center',
          render: (_, record) => <Text strong>{record.total_colaboradores ?? '-'}</Text>,
        },
        {
          title: 'Total Faturado',
          dataIndex: 'total_faturado_processo',
          key: 'total_faturado_processo',
          width: 160,
          align: 'right',
          render: (val) => formatCurrency(val),
          sorter: (a, b) => (a.total_faturado_processo || 0) - (b.total_faturado_processo || 0),
        },
        {
          title: 'Comissão Total',
          dataIndex: 'comissao_total_processo',
          key: 'comissao_total_processo',
          width: 170,
          align: 'right',
          render: (val) => <Text type="success" strong>{formatCurrency(val)}</Text>,
          sorter: (a, b) => (a.comissao_total_processo || 0) - (b.comissao_total_processo || 0),
        },
        {
          title: 'Status',
          key: 'status',
          width: 110,
          align: 'center',
          render: () => <Tag color="blue">Calculado</Tag>,
        },
      ];
    } else if (type === 'recebimento') {
      return [
        ...baseColumns,
        {
          title: 'Colaborador',
          dataIndex: 'nome_colaborador',
          key: 'nome_colaborador',
          width: 200,
          ellipsis: true,
          sorter: (a, b) => (a.nome_colaborador || '').localeCompare(b.nome_colaborador || ''),
        },
        {
          title: 'Cargo',
          dataIndex: 'cargo',
          key: 'cargo',
          width: 150,
          ellipsis: true,
          filters: [...new Set(data.map((item) => item.cargo).filter(Boolean))].map((c) => ({ text: c, value: c })),
          onFilter: (value, record) => record.cargo === value,
        },
        {
          title: 'Tipo',
          dataIndex: 'tipo',
          key: 'tipo',
          width: 120,
          render: (tipo) => {
            const isAdiantamento = tipo === 'ADIANTAMENTO' || tipo === 'Antecipação';
            return (
              <Tag color={isAdiantamento ? 'orange' : 'green'}>
                {isAdiantamento ? 'Adiantamento' : 'Regular'}
              </Tag>
            );
          },
          filters: [
            { text: 'Adiantamento', value: 'ADIANTAMENTO' },
            { text: 'Regular', value: 'REGULAR' },
          ],
          onFilter: (value, record) => {
             const tipo = record.tipo || '';
             if (value === 'ADIANTAMENTO') return tipo === 'ADIANTAMENTO' || tipo === 'Antecipação';
             return tipo === 'REGULAR' || tipo === 'Regular';
          }
        },
        {
          title: 'Data Pagamento',
          dataIndex: 'data_pagamento',
          key: 'data_pagamento',
          width: 130,
          render: (val) => val ? new Date(val).toLocaleDateString('pt-BR') : '-',
          sorter: (a, b) => new Date(a.data_pagamento || 0) - new Date(b.data_pagamento || 0),
        },
        {
          title: 'Valor Pago',
          dataIndex: 'valor_pago', // Adjust based on actual data key
          key: 'valor_pago',
          width: 150,
          align: 'right',
          render: (val) => <Text strong>{formatCurrency(val)}</Text>,
          sorter: (a, b) => (a.valor_pago || 0) - (b.valor_pago || 0),
        },
        {
            title: 'Comissão',
            dataIndex: 'comissao_calculada',
            key: 'comissao',
            width: 150,
            align: 'right',
            render: (val) => <Text type="success" strong>{formatCurrency(val)}</Text>,
            sorter: (a, b) => (a.comissao_calculada || 0) - (b.comissao_calculada || 0),
        },
      ];
    }
    return baseColumns;
  }, [data, type]);

  const actionColumn = {
    title: 'Ações',
    key: 'actions',
    width: 100,
    fixed: 'right',
    align: 'center',
    render: (_, record) => (
      <Tooltip title="Ver Detalhes">
        <Button
          type="primary"
          shape="circle"
          icon={<EyeOutlined />}
          onClick={() => onViewDetails(record)}
        />
      </Tooltip>
    ),
  };

  return (
    <Table
      columns={[...columns, actionColumn]}
      dataSource={data}
      rowKey={(record) => record.id || record.key || `${record.processo || ''}-${record.cod_produto || ''}-${record.nome_colaborador || ''}-${record.tipo || ''}-${record.data_pagamento || ''}`}
      loading={loading}
      scroll={{ x: 1000 }}
      pagination={{ pageSize: 10 }}
      size="middle"
      bordered
    />
  );
};

export default TabelaComissoes;
