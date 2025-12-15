import React, { useMemo } from 'react';
import { Table, Tag, Button, Tooltip, Space, Badge } from 'antd';
import { EyeOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';

/**
 * Tabela simples (flat) de pagamentos processados no mês.
 * Uma linha = um pagamento de colaborador.
 */
const RecebimentosTabelaSimples = ({ dados, loading, onVerDetalhes, filtros, onFiltrosChange }) => {
  // Configuração das colunas
  const columns = useMemo(() => [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 130,
      fixed: 'left',
      render: (tipo) => {
        const isAdiantamento = tipo === 'ADIANTAMENTO' || tipo === 'Antecipação';
        return (
          <Tag
            icon={isAdiantamento ? <ClockCircleOutlined /> : <CheckCircleOutlined />}
            color={isAdiantamento ? 'blue' : 'green'}
          >
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
        if (value === 'ADIANTAMENTO') {
          return tipo === 'ADIANTAMENTO' || tipo === 'Antecipação';
        }
        return tipo === 'REGULAR' || tipo === 'Pagamento';
      },
    },
    {
      title: 'Processo',
      dataIndex: 'processo',
      key: 'processo',
      width: 120,
      render: (text) => <strong style={{ color: '#1890ff' }}>{text}</strong>,
      sorter: (a, b) => (a.processo || '').localeCompare(b.processo || ''),
    },
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
      width: 160,
      ellipsis: true,
    },
    {
      title: 'Data Pagamento',
      dataIndex: 'data_pagamento',
      key: 'data_pagamento',
      width: 130,
      render: (data) => {
        if (!data) return '-';
        try {
          // Se vier no formato YYYY-MM-DD (ISO), fazer split para evitar timezone
          if (typeof data === 'string' && data.includes('-')) {
            const [ano, mes, dia] = data.split('-');
            return `${dia}/${mes}/${ano}`;
          }
          // Fallback para outros formatos
          return new Date(data).toLocaleDateString('pt-BR');
        } catch {
          return data;
        }
      },
      sorter: (a, b) => {
        const dateA = new Date(a.data_pagamento || 0);
        const dateB = new Date(b.data_pagamento || 0);
        return dateA - dateB;
      },
      defaultSortOrder: 'descend',
    },
    {
      title: 'Valor Pago',
      dataIndex: 'valor_pago',
      key: 'valor_pago',
      width: 140,
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
      sorter: (a, b) => (a.valor_pago || 0) - (b.valor_pago || 0),
    },
    {
      title: (
        <Tooltip title="Taxa de Comissão Média Ponderada">
          <span>TCMP</span>
        </Tooltip>
      ),
      dataIndex: 'tcmp',
      key: 'tcmp',
      width: 90,
      align: 'center',
      render: (tcmp) => {
        if (tcmp == null) return '-';
        return (
          <span style={{ color: '#1890ff', fontWeight: 500 }}>
            {(tcmp * 100).toFixed(2)}%
          </span>
        );
      },
    },
    {
      title: (
        <Tooltip title="Fator de Correção Médio Ponderado">
          <span>FCMP</span>
        </Tooltip>
      ),
      dataIndex: 'fcmp',
      key: 'fcmp',
      width: 90,
      align: 'center',
      render: (fcmp, record) => {
        if (fcmp == null) return '-';
        const isAdiantamento = record.tipo === 'ADIANTAMENTO' || record.tipo === 'Antecipação';
        const cor = fcmp > 1 ? '#52c41a' : fcmp < 1 ? '#ff4d4f' : '#000';
        
        return (
          <Badge
            count={isAdiantamento ? 'FC=1.0' : null}
            style={{ backgroundColor: '#1890ff' }}
          >
            <span style={{ color: cor, fontWeight: 500 }}>
              {fcmp.toFixed(4)}
            </span>
          </Badge>
        );
      },
    },
    {
      title: 'Comissão',
      dataIndex: 'comissao_calculada',
      key: 'comissao_calculada',
      width: 140,
      align: 'right',
      render: (comissao) => {
        if (comissao == null) return '-';
        return (
          <strong style={{ fontSize: 15, color: '#52c41a' }}>
            {new Intl.NumberFormat('pt-BR', {
              style: 'currency',
              currency: 'BRL',
            }).format(comissao)}
          </strong>
        );
      },
      sorter: (a, b) => (a.comissao_calculada || 0) - (b.comissao_calculada || 0),
    },
    {
      title: 'Detalhes',
      key: 'detalhes',
      width: 120,
      align: 'center',
      fixed: 'right',
      render: (_, record) => (
        <Tooltip title="Ver cálculo detalhado">
          <Button
            type="primary"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => onVerDetalhes(record)}
          >
            Ver Cálculo
          </Button>
        </Tooltip>
      ),
    },
  ], [onVerDetalhes]);

  return (
    <Table
      columns={columns}
      dataSource={dados}
      loading={loading}
      rowKey={(record, index) => `${record.processo}-${record.nome_colaborador}-${index}`}
      scroll={{ x: 1300 }}
      pagination={{
        defaultPageSize: 10,
        showSizeChanger: true,
        showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} pagamentos`,
        pageSizeOptions: ['10', '20', '50', '100'],
      }}
      bordered
      size="small"
    />
  );
};

export default RecebimentosTabelaSimples;
