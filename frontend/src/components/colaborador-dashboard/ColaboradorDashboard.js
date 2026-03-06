import React, { useMemo, useRef } from 'react';
import { Avatar, Button, Card, Space, Table, Tag, Tooltip, Typography } from 'antd';
import {
  ArrowLeftOutlined,
  PrinterOutlined,
  FileTextOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import FaturamentoItemDetail from './FaturamentoItemDetail';
import RecebimentoItemDetail from './RecebimentoItemDetail';
import './ColaboradorDashboard.css';

const { Text, Title } = Typography;

const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const formatPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
};

const getInitials = (name) => {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

const AVATAR_COLORS = [
  '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1',
  '#13c2c2', '#eb2f96', '#fa8c16', '#2f54eb', '#a0d911',
];

const getAvatarColor = (name) => {
  if (!name) return AVATAR_COLORS[0];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
};

/**
 * Nível 2 — Dashboard individual de um colaborador.
 *
 * Exibe header com resumo, tabela de itens/pagamentos agrupados por processo
 * e detalhamento expandível inline para cada linha.
 *
 * @param {Object} props
 * @param {Object} props.colaborador - Dados do colaborador (do endpoint)
 * @param {'faturamento'|'recebimento'} props.tipo - Tipo de comissão
 * @param {Function} props.onBack - Callback para voltar à lista
 * @param {string} [props.periodo] - Label do período ex: "01/2026"
 */
const ColaboradorDashboard = ({ colaborador, tipo = 'faturamento', onBack, periodo }) => {
  const printRef = useRef(null);

  const isFaturamento = tipo === 'faturamento';
  const nome = colaborador?.nome_colaborador || '';
  const cargo = colaborador?.cargo || '—';

  // Dados da tabela
  const dataSource = useMemo(() => {
    if (isFaturamento) {
      return (colaborador?.itens || []).map((item, idx) => ({
        ...item,
        key: `${item.processo || ''}-${item.cod_produto || ''}-${idx}`,
      }));
    }
    return (colaborador?.pagamentos || []).map((pag, idx) => ({
      ...pag,
      key: pag.id || `${pag.processo || ''}-${pag.tipo || ''}-${idx}`,
    }));
  }, [colaborador, isFaturamento]);

  // Agrupar por processo para facilitar auditoria visual
  const processosUnicos = useMemo(() => {
    const set = new Set();
    dataSource.forEach((row) => {
      if (row.processo) set.add(row.processo);
    });
    return Array.from(set).sort();
  }, [dataSource]);

  const processoFilters = useMemo(() => {
    return processosUnicos.map((p) => ({ text: p, value: p }));
  }, [processosUnicos]);

  // Colunas — Faturamento
  const faturamentoColumns = useMemo(() => [
    {
      title: 'Processo',
      dataIndex: 'processo',
      key: 'processo',
      width: 130,
      fixed: 'left',
      filters: processoFilters,
      onFilter: (value, record) => record.processo === value,
      render: (v) => <Text strong style={{ color: '#1890ff' }}>{v || '-'}</Text>,
      sorter: (a, b) => (a.processo || '').localeCompare(b.processo || ''),
    },
    {
      title: 'Item',
      dataIndex: 'cod_produto',
      key: 'cod_produto',
      width: 130,
      render: (v) => <Text>{v || '-'}</Text>,
    },
    {
      title: 'Descrição',
      dataIndex: 'descricao_produto',
      key: 'descricao_produto',
      ellipsis: true,
      width: 200,
    },
    {
      title: 'Valor Item',
      dataIndex: 'faturamento_item',
      key: 'faturamento_item',
      width: 140,
      align: 'right',
      render: (v) => formatCurrencyBR(v),
      sorter: (a, b) => Number(a.faturamento_item || 0) - Number(b.faturamento_item || 0),
    },
    {
      title: 'Taxa Rateio',
      dataIndex: 'taxa_rateio_aplicada',
      key: 'taxa_rateio_aplicada',
      width: 110,
      align: 'center',
      render: (v) => formatPercent(v),
    },
    {
      title: 'Fatia Cargo',
      dataIndex: 'percentual_elegibilidade_pe',
      key: 'percentual_elegibilidade_pe',
      width: 110,
      align: 'center',
      render: (v) => formatPercent(v),
    },
    {
      title: 'FC',
      dataIndex: 'fator_correcao_fc',
      key: 'fator_correcao_fc',
      width: 90,
      align: 'center',
      render: (v) => {
        const num = Number(v);
        if (!Number.isFinite(num)) return '-';
        const color = num >= 1 ? '#52c41a' : num >= 0.7 ? '#faad14' : '#f5222d';
        return <Text strong style={{ color }}>{(num * 100).toFixed(1)}%</Text>;
      },
      sorter: (a, b) => Number(a.fator_correcao_fc || 0) - Number(b.fator_correcao_fc || 0),
    },
    {
      title: 'Comissão',
      dataIndex: 'comissao_calculada',
      key: 'comissao_calculada',
      width: 150,
      align: 'right',
      fixed: 'right',
      render: (v) => <Text type="success" strong>{formatCurrencyBR(v)}</Text>,
      sorter: (a, b) => Number(a.comissao_calculada || 0) - Number(b.comissao_calculada || 0),
    },
  ], [processoFilters]);

  // Colunas — Recebimento
  const recebimentoColumns = useMemo(() => [
    {
      title: 'Processo',
      dataIndex: 'processo',
      key: 'processo',
      width: 130,
      fixed: 'left',
      filters: processoFilters,
      onFilter: (value, record) => record.processo === value,
      render: (v) => <Text strong style={{ color: '#1890ff' }}>{v || '-'}</Text>,
      sorter: (a, b) => (a.processo || '').localeCompare(b.processo || ''),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 130,
      align: 'center',
      filters: [
        { text: 'Adiantamento', value: 'ADIANTAMENTO' },
        { text: 'Regular', value: 'REGULAR' },
      ],
      onFilter: (value, record) => record.tipo === value,
      render: (v) => {
        const isAdiant = v === 'ADIANTAMENTO' || v === 'Antecipação';
        return <Tag color={isAdiant ? 'blue' : 'green'}>{isAdiant ? 'Adiantamento' : 'Regular'}</Tag>;
      },
    },
    {
      title: 'Data Pgto',
      dataIndex: 'data_pagamento',
      key: 'data_pagamento',
      width: 120,
      render: (v) => v ? new Date(v).toLocaleDateString('pt-BR') : '-',
      sorter: (a, b) => new Date(a.data_pagamento || 0) - new Date(b.data_pagamento || 0),
    },
    {
      title: 'Valor Pago',
      dataIndex: 'valor_pago',
      key: 'valor_pago',
      width: 140,
      align: 'right',
      render: (v) => formatCurrencyBR(v),
      sorter: (a, b) => Number(a.valor_pago || 0) - Number(b.valor_pago || 0),
    },
    {
      title: 'TCMP',
      dataIndex: 'tcmp',
      key: 'tcmp',
      width: 100,
      align: 'center',
      render: (v) => formatPercent(v),
    },
    {
      title: 'FCMP',
      dataIndex: 'fcmp',
      key: 'fcmp',
      width: 90,
      align: 'center',
      render: (v, record) => {
        const isAdiant = record.tipo === 'ADIANTAMENTO';
        const num = Number(v);
        if (isAdiant) return <Tooltip title="Adiantamento: FC fixo = 1.0"><Text type="secondary">1.0000</Text></Tooltip>;
        if (!Number.isFinite(num)) return '-';
        return <Text strong>{num.toFixed(4)}</Text>;
      },
    },
    {
      title: 'Comissão',
      dataIndex: 'comissao_calculada',
      key: 'comissao_calculada',
      width: 150,
      align: 'right',
      fixed: 'right',
      render: (v) => <Text type="success" strong>{formatCurrencyBR(v)}</Text>,
      sorter: (a, b) => Number(a.comissao_calculada || 0) - Number(b.comissao_calculada || 0),
    },
  ], [processoFilters]);

  const columns = isFaturamento ? faturamentoColumns : recebimentoColumns;

  // Summary row que mostra o total
  const summaryRow = () => {
    const totalComissao = dataSource.reduce(
      (acc, row) => acc + Number(row.comissao_calculada || 0),
      0
    );
    const colSpan = columns.length - 1;

    return (
      <Table.Summary fixed>
        <Table.Summary.Row>
          <Table.Summary.Cell index={0} colSpan={colSpan} align="right">
            <Text strong>Total da Comissão</Text>
          </Table.Summary.Cell>
          <Table.Summary.Cell index={colSpan} align="right">
            <Text type="success" strong style={{ fontSize: 16 }}>
              {formatCurrencyBR(totalComissao)}
            </Text>
          </Table.Summary.Cell>
        </Table.Summary.Row>
      </Table.Summary>
    );
  };

  // Print (comprovante)
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="colab-dashboard" ref={printRef}>
      {/* Back button */}
      <div className="colab-dashboard__back-row">
        <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
          Voltar para lista
        </Button>
        <Text type="secondary">
          Dashboard do Colaborador · {isFaturamento ? 'Faturamento' : 'Recebimento'}
          {periodo ? ` · ${periodo}` : ''}
        </Text>
      </div>

      {/* Header Card */}
      <Card className="colab-dashboard__header-card" size="small">
        <div className="colab-dashboard__header-content">
          <Avatar
            className="colab-dashboard__header-avatar"
            size={64}
            style={{ backgroundColor: getAvatarColor(nome), fontSize: 22 }}
          >
            {getInitials(nome)}
          </Avatar>

          <div className="colab-dashboard__header-info">
            <h2 className="colab-dashboard__header-name">{nome}</h2>
            <p className="colab-dashboard__header-cargo">{cargo}</p>
          </div>

          <div className="colab-dashboard__header-stats">
            <div className="colab-dashboard__header-stat">
              <span className="colab-dashboard__header-stat-value colab-dashboard__header-stat-value--comissao">
                {formatCurrencyBR(colaborador?.total_comissao)}
              </span>
              <span className="colab-dashboard__header-stat-label">Comissão Total</span>
            </div>

            <div className="colab-dashboard__header-stat">
              <span className="colab-dashboard__header-stat-value">
                <FileTextOutlined style={{ marginRight: 4 }} />
                {colaborador?.total_processos || 0}
              </span>
              <span className="colab-dashboard__header-stat-label">Processos</span>
            </div>

            <div className="colab-dashboard__header-stat">
              <span className="colab-dashboard__header-stat-value">
                <AppstoreOutlined style={{ marginRight: 4 }} />
                {isFaturamento
                  ? (colaborador?.total_itens || 0)
                  : (colaborador?.total_pagamentos || 0)}
              </span>
              <span className="colab-dashboard__header-stat-label">
                {isFaturamento ? 'Itens' : 'Pagamentos'}
              </span>
            </div>

            {!isFaturamento && (
              <>
                <div className="colab-dashboard__header-stat">
                  <span className="colab-dashboard__header-stat-value" style={{ color: '#1890ff' }}>
                    {colaborador?.total_adiantamentos || 0}
                  </span>
                  <span className="colab-dashboard__header-stat-label">Adiantamentos</span>
                </div>
                <div className="colab-dashboard__header-stat">
                  <span className="colab-dashboard__header-stat-value" style={{ color: '#52c41a' }}>
                    {colaborador?.total_regulares || 0}
                  </span>
                  <span className="colab-dashboard__header-stat-label">Regulares</span>
                </div>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="colab-dashboard__actions">
        <Button icon={<PrinterOutlined />} onClick={handlePrint}>
          Gerar Comprovante (Imprimir)
        </Button>
      </div>

      {/* Main Table */}
      <Card size="small">
        <Title level={5} style={{ marginBottom: 12 }}>
          {isFaturamento ? 'Itens (por Processo)' : 'Pagamentos (por Processo)'}
          <Text type="secondary" style={{ fontSize: 12, fontWeight: 400, marginLeft: 8 }}>
            Clique na linha para expandir o cálculo detalhado
          </Text>
        </Title>
        <Table
          columns={columns}
          dataSource={dataSource}
          size="middle"
          bordered
          scroll={{ x: 'max-content' }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
            showTotal: (total) => `${total} registro${total !== 1 ? 's' : ''}`,
          }}
          expandable={{
            expandedRowRender: (record) =>
              isFaturamento ? (
                <FaturamentoItemDetail rowData={record} />
              ) : (
                <RecebimentoItemDetail pagamento={record} />
              ),
            rowExpandable: () => true,
          }}
          rowClassName={(record, index) => (index % 2 === 0 ? '' : 'ant-table-row-striped')}
          summary={summaryRow}
        />
      </Card>
    </div>
  );
};

export default ColaboradorDashboard;
