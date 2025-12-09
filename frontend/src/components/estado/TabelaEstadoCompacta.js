import React, { useMemo } from 'react';
import { Table, Tag, Progress, Avatar, Tooltip, Button, Space } from 'antd';
import { EyeOutlined, UserOutlined } from '@ant-design/icons';

/**
 * Tabela compacta do Estado dos Processos.
 * Exibe apenas as colunas essenciais para facilitar a navegação.
 */
const TabelaEstadoCompacta = ({ dados, loading, onVerDetalhes }) => {
  // Configuração das colunas principais
  const columns = useMemo(() => [
    {
      title: 'Processo',
      dataIndex: 'PROCESSO',
      key: 'processo',
      width: 150,
      fixed: 'left',
      render: (text) => (
        <span style={{ fontWeight: 600, color: '#1890ff' }}>{text}</span>
      ),
      sorter: (a, b) => a.PROCESSO.localeCompare(b.PROCESSO),
    },
    {
      title: 'Valor Total',
      dataIndex: 'VALOR_TOTAL_PROCESSO',
      key: 'valor_total',
      width: 150,
      align: 'right',
      render: (valor) => {
        if (valor == null) return '-';
        return (
          <span style={{ fontWeight: 500 }}>
            {new Intl.NumberFormat('pt-BR', {
              style: 'currency',
              currency: 'BRL',
            }).format(valor)}
          </span>
        );
      },
      sorter: (a, b) => (a.VALOR_TOTAL_PROCESSO || 0) - (b.VALOR_TOTAL_PROCESSO || 0),
    },
    {
      title: 'Progresso Pagamento',
      key: 'progresso',
      width: 200,
      render: (_, record) => {
        const total = record.VALOR_TOTAL_PROCESSO || 0;
        const pago = record.TOTAL_PAGO_ACUMULADO || 0;
        const percentual = total > 0 ? Math.round((pago / total) * 100) : 0;
        
        let status = 'active';
        let strokeColor = '#1890ff';
        
        if (percentual === 100) {
          status = 'success';
          strokeColor = '#52c41a';
        } else if (percentual > 0) {
          status = 'active';
          strokeColor = '#faad14';
        }
        
        return (
          <div>
            <Progress
              percent={percentual}
              status={status}
              strokeColor={strokeColor}
              size="small"
            />
            <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2 }}>
              {new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL',
              }).format(pago)} de {new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL',
              }).format(total)}
            </div>
          </div>
        );
      },
      sorter: (a, b) => {
        const percA = (a.TOTAL_PAGO_ACUMULADO || 0) / (a.VALOR_TOTAL_PROCESSO || 1);
        const percB = (b.TOTAL_PAGO_ACUMULADO || 0) / (b.VALOR_TOTAL_PROCESSO || 1);
        return percA - percB;
      },
    },
    {
      title: 'Status Processo',
      dataIndex: 'STATUS_PROCESSO',
      key: 'status_processo',
      width: 140,
      align: 'center',
      render: (status) => {
        if (!status) return '-';
        
        let color = 'default';
        if (status === 'FATURADO') color = 'green';
        else if (status === 'PENDENTE') color = 'blue';
        else if (status === 'CANCELADO') color = 'red';
        
        return <Tag color={color}>{status}</Tag>;
      },
      filters: [
        { text: 'FATURADO', value: 'FATURADO' },
        { text: 'PENDENTE', value: 'PENDENTE' },
        { text: 'CANCELADO', value: 'CANCELADO' },
      ],
      onFilter: (value, record) => record.STATUS_PROCESSO === value,
    },
    {
      title: 'Status Pagamento',
      dataIndex: 'STATUS_PAGAMENTO',
      key: 'status_pagamento',
      width: 140,
      align: 'center',
      render: (status) => {
        if (!status) return '-';
        
        let color = 'default';
        if (status === 'COMPLETO') color = 'green';
        else if (status === 'PARCIAL') color = 'gold';
        else if (status === 'PENDENTE') color = 'blue';
        
        return <Tag color={color}>{status}</Tag>;
      },
      filters: [
        { text: 'COMPLETO', value: 'COMPLETO' },
        { text: 'PARCIAL', value: 'PARCIAL' },
        { text: 'PENDENTE', value: 'PENDENTE' },
      ],
      onFilter: (value, record) => record.STATUS_PAGAMENTO === value,
    },
    {
      title: 'Colaboradores',
      dataIndex: 'COLABORADORES_ENVOLVIDOS',
      key: 'colaboradores',
      width: 200,
      render: (colaboradores) => {
        if (!colaboradores || colaboradores.length === 0) return '-';
        
        const maxVisivel = 3;
        const visiveis = colaboradores.slice(0, maxVisivel);
        const restantes = colaboradores.length - maxVisivel;
        
        return (
          <Avatar.Group maxCount={3} size="small">
            {visiveis.map((colab, idx) => (
              <Tooltip title={colab} key={idx}>
                <Avatar
                  style={{ backgroundColor: '#1890ff' }}
                  icon={<UserOutlined />}
                >
                  {colab.substring(0, 2).toUpperCase()}
                </Avatar>
              </Tooltip>
            ))}
            {restantes > 0 && (
              <Tooltip title={colaboradores.slice(maxVisivel).join(', ')}>
                <Avatar style={{ backgroundColor: '#f56a00' }}>
                  +{restantes}
                </Avatar>
              </Tooltip>
            )}
          </Avatar.Group>
        );
      },
    },
    {
      title: 'Ações',
      key: 'acoes',
      width: 120,
      align: 'center',
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="Ver detalhes completos">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onVerDetalhes(record)}
            >
              Detalhes
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ], [onVerDetalhes]);

  return (
    <Table
      columns={columns}
      dataSource={dados}
      loading={loading}
      rowKey="PROCESSO"
      scroll={{ x: 1200 }}
      pagination={{
        defaultPageSize: 20,
        showSizeChanger: true,
        showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} processos`,
        pageSizeOptions: ['10', '20', '50', '100'],
      }}
      bordered
      size="middle"
    />
  );
};

export default TabelaEstadoCompacta;
