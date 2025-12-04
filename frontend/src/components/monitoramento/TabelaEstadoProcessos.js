/**
 * TabelaEstadoProcessos.js
 * 
 * Componente principal de tabela para exibição do estado dos processos.
 * Inclui filtros, busca, ordenação e ações para cada processo.
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
  EyeOutlined,
  FilterOutlined,
  ReloadOutlined,
  UserOutlined,
} from '@ant-design/icons';
import BarraProgressoFinanceiro from './BarraProgressoFinanceiro';
import DetalhesProcessoModal from './DetalhesProcessoModal';

const { Text } = Typography;
const { Option } = Select;

/**
 * Formata valor monetário para exibição.
 */
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
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
 * Tabela de estado de processos com recursos avançados.
 * 
 * @param {Object} props
 * @param {Array} props.processos - Lista de processos
 * @param {boolean} props.loading - Estado de carregamento
 * @param {Function} props.onRefresh - Callback para recarregar dados
 * @param {Object} props.filters - Filtros atuais
 * @param {Function} props.onFiltersChange - Callback para mudança de filtros
 */
const TabelaEstadoProcessos = ({
  processos = [],
  loading = false,
  onRefresh,
  filters = {},
  onFiltersChange,
}) => {
  const [searchText, setSearchText] = useState('');
  const [selectedProcesso, setSelectedProcesso] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  // Filtrar dados localmente pelo texto de busca
  const filteredData = processos.filter((p) => {
    if (!searchText) return true;
    const search = searchText.toLowerCase();
    return (
      p.processo?.toLowerCase().includes(search) ||
      p.colaboradores_envolvidos?.some((c) => c.toLowerCase().includes(search)) ||
      p.mes_ano_faturamento?.toLowerCase().includes(search)
    );
  });

  const handleViewDetails = (processo) => {
    setSelectedProcesso(processo.processo);
    setModalVisible(true);
  };

  const handleCloseModal = () => {
    setModalVisible(false);
    setSelectedProcesso(null);
  };

  const columns = [
    {
      title: 'Processo',
      dataIndex: 'processo',
      key: 'processo',
      fixed: 'left',
      width: 120,
      sorter: (a, b) => a.processo.localeCompare(b.processo),
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Progresso',
      key: 'progresso',
      width: 180,
      sorter: (a, b) => a.percentual_pago - b.percentual_pago,
      render: (_, record) => (
        <BarraProgressoFinanceiro
          totalPago={record.total_pago_acumulado}
          valorTotal={record.valor_total_processo}
          percentual={record.percentual_pago}
          size="small"
        />
      ),
    },
    {
      title: 'Status Pag.',
      dataIndex: 'status_pagamento',
      key: 'status_pagamento',
      width: 110,
      filters: [
        { text: 'Completo', value: 'COMPLETO' },
        { text: 'Parcial', value: 'PARCIAL' },
        { text: 'Pendente', value: 'PENDENTE' },
      ],
      onFilter: (value, record) => record.status_pagamento === value,
      render: (status) => {
        const colors = {
          COMPLETO: 'green',
          PARCIAL: 'blue',
          PENDENTE: 'orange',
        };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: 'Status Recon.',
      dataIndex: 'status_reconciliacao',
      key: 'status_reconciliacao',
      width: 110,
      filters: [
        { text: 'Concluída', value: 'CONCLUIDA' },
        { text: 'Pendente', value: 'PENDENTE' },
      ],
      onFilter: (value, record) => record.status_reconciliacao === value,
      render: (status) => {
        const colors = {
          CONCLUIDA: 'green',
          PENDENTE: 'orange',
        };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: 'Valor Total',
      dataIndex: 'valor_total_processo',
      key: 'valor_total_processo',
      width: 130,
      align: 'right',
      sorter: (a, b) => a.valor_total_processo - b.valor_total_processo,
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Saldo',
      dataIndex: 'saldo_a_receber',
      key: 'saldo_a_receber',
      width: 130,
      align: 'right',
      sorter: (a, b) => a.saldo_a_receber - b.saldo_a_receber,
      render: (value) => (
        <Text type={value > 0 ? 'warning' : 'success'} strong={value > 0}>
          {formatCurrency(value)}
        </Text>
      ),
    },
    {
      title: 'Comissão Acum.',
      dataIndex: 'total_comissao_acumulada',
      key: 'total_comissao_acumulada',
      width: 130,
      align: 'right',
      sorter: (a, b) => a.total_comissao_acumulada - b.total_comissao_acumulada,
      render: (value) => (
        <Text style={{ color: '#722ed1' }}>{formatCurrency(value)}</Text>
      ),
    },
    {
      title: 'Colaboradores',
      dataIndex: 'colaboradores_envolvidos',
      key: 'colaboradores_envolvidos',
      width: 200,
      render: (colaboradores) => {
        if (!colaboradores || colaboradores.length === 0) {
          return <Text type="secondary">-</Text>;
        }
        // Mostrar apenas os 2 primeiros e indicar quantos mais
        const visibleCount = 2;
        const visible = colaboradores.slice(0, visibleCount);
        const remaining = colaboradores.length - visibleCount;
        
        return (
          <div>
            {visible.map((col, idx) => (
              <Tag key={idx} icon={<UserOutlined />} style={{ marginBottom: 2 }}>
                {col.length > 15 ? `${col.substring(0, 15)}...` : col}
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
    },
    {
      title: 'Mês/Ano',
      dataIndex: 'mes_ano_faturamento',
      key: 'mes_ano_faturamento',
      width: 100,
      sorter: (a, b) => {
        const parseDate = (d) => {
          if (!d) return 0;
          const [m, y] = d.split('/');
          return parseInt(y) * 100 + parseInt(m);
        };
        return parseDate(a.mes_ano_faturamento) - parseDate(b.mes_ano_faturamento);
      },
      render: (value) => value || '-',
    },
    {
      title: 'Qtd. Pag.',
      dataIndex: 'quantidade_pagamentos',
      key: 'quantidade_pagamentos',
      width: 90,
      align: 'center',
      sorter: (a, b) => a.quantidade_pagamentos - b.quantidade_pagamentos,
    },
    {
      title: 'Última Atualização',
      dataIndex: 'ultima_atualizacao',
      key: 'ultima_atualizacao',
      width: 130,
      sorter: (a, b) => {
        const dateA = a.ultima_atualizacao ? new Date(a.ultima_atualizacao) : new Date(0);
        const dateB = b.ultima_atualizacao ? new Date(b.ultima_atualizacao) : new Date(0);
        return dateA - dateB;
      },
      render: (value) => formatDate(value),
    },
    {
      title: 'Ações',
      key: 'acoes',
      fixed: 'right',
      width: 80,
      align: 'center',
      render: (_, record) => (
        <Tooltip title="Ver Detalhes">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record)}
          />
        </Tooltip>
      ),
    },
  ];

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
          placeholder="Status Pagamento"
          style={{ width: 160 }}
          allowClear
          value={filters.statusPagamento}
          onChange={(value) => onFiltersChange?.({ ...filters, statusPagamento: value })}
        >
          <Option value="PENDENTE">Pendente</Option>
          <Option value="PARCIAL">Parcial</Option>
          <Option value="COMPLETO">Completo</Option>
        </Select>

        <Select
          placeholder="Status Reconciliação"
          style={{ width: 170 }}
          allowClear
          value={filters.statusReconciliacao}
          onChange={(value) => onFiltersChange?.({ ...filters, statusReconciliacao: value })}
        >
          <Option value="PENDENTE">Pendente</Option>
          <Option value="CONCLUIDA">Concluída</Option>
        </Select>

        <Button
          type={filters.apenasSaldoAberto ? 'primary' : 'default'}
          icon={<FilterOutlined />}
          onClick={() => onFiltersChange?.({ ...filters, apenasSaldoAberto: !filters.apenasSaldoAberto })}
        >
          Saldo Aberto
        </Button>

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
        dataSource={filteredData.map((p, idx) => ({ ...p, key: p.processo || idx }))}
        loading={loading}
        size="small"
        scroll={{ x: 1600 }}
        pagination={{
          defaultPageSize: 20,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} processos`,
        }}
        bordered
      />

      {/* Modal de Detalhes */}
      <DetalhesProcessoModal
        visible={modalVisible}
        processoId={selectedProcesso}
        onClose={handleCloseModal}
      />
    </div>
  );
};

export default TabelaEstadoProcessos;
