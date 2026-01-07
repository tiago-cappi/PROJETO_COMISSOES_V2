import React from 'react';
import { Table, Typography } from 'antd';

const { Text } = Typography;

const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const TabelaResumoFinalColaborador = ({ data = [], loading = false, onClickColaborador }) => {
  const columns = [
    {
      title: 'Colaborador',
      dataIndex: 'Nome_Colaborador',
      key: 'Nome_Colaborador',
      width: 280,
      ellipsis: true,
      render: (v) => <Text strong>{v || '-'}</Text>,
      sorter: (a, b) => String(a.Nome_Colaborador || '').localeCompare(String(b.Nome_Colaborador || '')),
    },
    {
      title: 'Total do Mês',
      dataIndex: 'Total_Mes',
      key: 'Total_Mes',
      width: 170,
      align: 'right',
      render: (v) => {
        const num = Number(v);
        const isNeg = !Number.isNaN(num) && num < 0;
        return <Text type={isNeg ? 'danger' : 'success'} strong>{formatCurrencyBR(num)}</Text>;
      },
      sorter: (a, b) => Number(a.Total_Mes || 0) - Number(b.Total_Mes || 0),
      defaultSortOrder: 'descend',
    },
    {
      title: 'Faturamento',
      dataIndex: 'FATURAMENTO',
      key: 'FATURAMENTO',
      width: 150,
      align: 'right',
      render: (v) => <Text>{formatCurrencyBR(v)}</Text>,
    },
    {
      title: 'Adiantamento',
      dataIndex: 'ADIANTAMENTO',
      key: 'ADIANTAMENTO',
      width: 150,
      align: 'right',
      render: (v) => <Text>{formatCurrencyBR(v)}</Text>,
    },
    {
      title: 'Regular',
      dataIndex: 'REGULAR',
      key: 'REGULAR',
      width: 140,
      align: 'right',
      render: (v) => <Text>{formatCurrencyBR(v)}</Text>,
    },
    {
      title: 'Reconciliação',
      dataIndex: 'RECONCILIACAO',
      key: 'RECONCILIACAO',
      width: 160,
      align: 'right',
      render: (v) => <Text>{formatCurrencyBR(v)}</Text>,
    },
    {
      title: 'Devolução',
      dataIndex: 'DEVOLUCAO',
      key: 'DEVOLUCAO',
      width: 140,
      align: 'right',
      render: (v) => {
        const num = Number(v);
        const isNeg = !Number.isNaN(num) && num < 0;
        return <Text type={isNeg ? 'danger' : undefined}>{formatCurrencyBR(num)}</Text>;
      },
    },
  ];

  return (
    <Table
      size="middle"
      bordered
      loading={loading}
      columns={columns}
      dataSource={Array.isArray(data) ? data.map((r, idx) => ({ ...r, key: `${r.Nome_Colaborador || ''}|${idx}` })) : []}
      pagination={{ pageSize: 12 }}
      onRow={(record) => ({
        onClick: () => onClickColaborador && onClickColaborador(record),
      })}
      scroll={{ x: 'max-content' }}
    />
  );
};

export default TabelaResumoFinalColaborador;
