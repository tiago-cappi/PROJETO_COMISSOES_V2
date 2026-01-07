import React, { useEffect, useMemo, useState } from 'react';
import { Modal, Breadcrumb, Button, Card, Descriptions, Space, Table, Typography, Tag, Tooltip } from 'antd';
import { LeftOutlined, MinusCircleOutlined, PlusCircleOutlined } from '@ant-design/icons';
import DetalhesCalculoModal from '../DetalhesCalculoModal';
import { formatCurrencyBR } from './faturamentoGrouping';

const { Title, Text } = Typography;

const formatPercent = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
};

const getCrossSellingDecisionFromRow = (row) => {
  const decision = row?.cross_selling_decision || row?.CROSS_SELLING_DECISION;
  if (decision === 'A' || decision === 'B') return decision;
  return null;
};

const getCrossSellingInfo = (rows = []) => {
  const isConsultorExterno = rows.some((r) => r?.observacao === 'CROSS_SELLING');
  if (!isConsultorExterno) return { isConsultorExterno: false, decision: null };

  // Prefer an explicit decision if present in any row; fallback to A (default behavior in existing UI).
  for (const r of rows) {
    const d = getCrossSellingDecisionFromRow(r);
    if (d) return { isConsultorExterno: true, decision: d };
  }
  return { isConsultorExterno: true, decision: 'A' };
};

const extractFcFinal = (rows = []) => {
  // Cross-selling commissions do not use FC.
  const { isConsultorExterno } = getCrossSellingInfo(rows);
  if (isConsultorExterno) return null;

  const candidates = ['fator_correcao_fc', 'fator_correcao_final', 'fc_final'];
  for (const r of rows) {
    for (const key of candidates) {
      const v = r?.[key];
      const num = Number(v);
      if (!Number.isNaN(num) && v !== '' && v !== null && v !== undefined) {
        return num;
      }
    }
  }
  return null;
};

const LEVEL = {
  PROCESSO: 'processo',
  ITEM: 'item',
  COLABORADOR: 'colaborador',
};

const buildBreadcrumbLabel = (node) => {
  if (!node) return '';
  if (node.level === LEVEL.PROCESSO) return `Processo ${node.processo}`;
  if (node.level === LEVEL.ITEM) return `Item ${node.item?.cod_produto || '-'}`;
  if (node.level === LEVEL.COLABORADOR) return node.colaborador?.nome_colaborador || 'Colaborador';
  return '';
};

const DetalhesFaturamentoStackModal = ({ visible, onClose, processo }) => {
  const [stack, setStack] = useState([]);
  const [selectedRow, setSelectedRow] = useState(null);

  useEffect(() => {
    if (!visible || !processo) return;

    setStack([
      {
        level: LEVEL.PROCESSO,
        processo: processo.processo,
        processoData: processo,
      },
    ]);
    setSelectedRow(null);
  }, [visible, processo]);

  const current = stack[stack.length - 1];

  const goBack = () => {
    setStack((prev) => (prev.length > 1 ? prev.slice(0, -1) : prev));
    setSelectedRow(null);
  };

  const jumpTo = (index) => {
    setStack((prev) => prev.slice(0, index + 1));
    setSelectedRow(null);
  };

  const pushItem = (item) => {
    setStack((prev) => [
      ...prev,
      {
        level: LEVEL.ITEM,
        processo: current.processo,
        processoData: current.processoData,
        item,
      },
    ]);
    setSelectedRow(null);
  };

  const pushColaborador = (colaborador, rows) => {
    setStack((prev) => [
      ...prev,
      {
        level: LEVEL.COLABORADOR,
        processo: current.processo,
        processoData: current.processoData,
        item: current.item,
        colaborador,
        rows,
      },
    ]);

    if (Array.isArray(rows) && rows.length === 1) {
      setSelectedRow(rows[0]);
    } else {
      setSelectedRow(null);
    }
  };

  const breadcrumbItems = useMemo(() => {
    return stack.map((node, idx) => ({
      title: (
        <Button type="link" size="small" onClick={() => jumpTo(idx)} style={{ padding: 0 }}>
          {buildBreadcrumbLabel(node)}
        </Button>
      ),
    }));
  }, [stack]);

  const renderProcessoPage = () => {
    const p = current.processoData;
    const items = p.items || [];

    const columns = [
      {
        title: 'Cod. Produto',
        dataIndex: 'cod_produto',
        key: 'cod_produto',
        width: 140,
        render: (v) => <Text strong>{v || '-'}</Text>,
        sorter: (a, b) => String(a.cod_produto || '').localeCompare(String(b.cod_produto || '')),
      },
      {
        title: 'Descrição',
        dataIndex: 'descricao_produto',
        key: 'descricao_produto',
        ellipsis: true,
      },
      {
        title: 'Valor do Item',
        dataIndex: 'faturamento_item',
        key: 'faturamento_item',
        width: 160,
        align: 'right',
        render: (v) => formatCurrencyBR(v),
        sorter: (a, b) => (a.faturamento_item || 0) - (b.faturamento_item || 0),
      },
      {
        title: 'Comissão (Total Item)',
        dataIndex: 'comissao_total_item',
        key: 'comissao_total_item',
        width: 180,
        align: 'right',
        render: (v) => <Text type="success" strong>{formatCurrencyBR(v)}</Text>,
        sorter: (a, b) => (a.comissao_total_item || 0) - (b.comissao_total_item || 0),
      },
    ];

    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small">
          <Title level={5} style={{ margin: 0 }}>Resumo do Processo</Title>
          <Descriptions bordered size="small" column={2} style={{ marginTop: 12 }}>
            <Descriptions.Item label="Processo"><Text strong>{p.processo}</Text></Descriptions.Item>
            <Descriptions.Item label="Itens"><Text strong>{p.total_itens ?? (p.items || []).length}</Text></Descriptions.Item>
            <Descriptions.Item label="Colaboradores"><Text strong>{p.total_colaboradores ?? '-'}</Text></Descriptions.Item>
            <Descriptions.Item label="Total Faturado"><Text strong>{formatCurrencyBR(p.total_faturado_processo)}</Text></Descriptions.Item>
            <Descriptions.Item label="Comissão Total" span={2}><Text type="success" strong>{formatCurrencyBR(p.comissao_total_processo)}</Text></Descriptions.Item>
          </Descriptions>
        </Card>

        <Card size="small" title="Itens (clique para ver detalhes)">
          <Table
            size="middle"
            bordered
            columns={columns}
            dataSource={items.map((it) => ({ ...it, key: it.key || `${p.processo}-${it.cod_produto}` }))}
            pagination={{ pageSize: 8 }}
            onRow={(record) => ({
              onClick: () => pushItem(record),
            })}
          />
        </Card>
      </Space>
    );
  };

  const renderItemPage = () => {
    const item = current.item;
    const colaboradores = (item?.colaboradores || []).slice();

    const colabsGrouped = new Map();
    for (const row of colaboradores) {
      const nome = row.nome_colaborador || row.id_colaborador || '—';
      if (!colabsGrouped.has(nome)) {
        colabsGrouped.set(nome, { nome_colaborador: nome, cargo: row.cargo, rows: [] });
      }
      colabsGrouped.get(nome).rows.push(row);
    }

    const colabs = Array.from(colabsGrouped.values()).map((c) => ({
      ...c,
      comissao_total_colaborador_item: c.rows.reduce((acc, r) => acc + Number(r.comissao_calculada || 0), 0),
      fc_final: extractFcFinal(c.rows),
      crossSellingInfo: getCrossSellingInfo(c.rows),
      key: `${current.processo}-${item.cod_produto || 'item'}-${c.nome_colaborador}`,
    }));

    const columns = [
      {
        title: 'Colaborador',
        dataIndex: 'nome_colaborador',
        key: 'nome_colaborador',
        width: 240,
        ellipsis: true,
        render: (value, record) => {
          const info = record?.crossSellingInfo || { isConsultorExterno: false, decision: null };
          if (!info.isConsultorExterno) return value;

          const decision = info.decision || 'A';
          const isA = decision === 'A';
          const tooltip = isA
            ? 'Cross-Selling (Opção A): taxa do consultor externo SUBTRAÍDA da taxa dos demais.'
            : 'Cross-Selling (Opção B): comissão do consultor externo ADICIONAL.';

          return (
            <Space size={8}>
              <span>{value}</span>
              <Tooltip title={tooltip}>
                <Tag
                  color={isA ? 'orange' : 'blue'}
                  icon={isA ? <MinusCircleOutlined /> : <PlusCircleOutlined />}
                  style={{ marginInlineEnd: 0 }}
                >
                  CS-{decision}
                </Tag>
              </Tooltip>
            </Space>
          );
        },
        sorter: (a, b) => String(a.nome_colaborador || '').localeCompare(String(b.nome_colaborador || '')),
      },
      {
        title: 'Cargo',
        dataIndex: 'cargo',
        key: 'cargo',
        width: 200,
        ellipsis: true,
      },
      {
        title: 'FC Final',
        dataIndex: 'fc_final',
        key: 'fc_final',
        width: 120,
        align: 'center',
        render: (v, record) => {
          const info = record?.crossSellingInfo || { isConsultorExterno: false };
          if (info.isConsultorExterno) {
            return (
              <Tooltip title="Comissões de cross-selling não usam FC.">
                <Text type="secondary">—</Text>
              </Tooltip>
            );
          }
          if (v === null || v === undefined || Number.isNaN(Number(v))) return <Text type="secondary">-</Text>;
          return <Text strong>{formatPercent(v)}</Text>;
        },
        sorter: (a, b) => (Number(a.fc_final || 0) - Number(b.fc_final || 0)),
      },
      {
        title: 'Comissão (Item)',
        dataIndex: 'comissao_total_colaborador_item',
        key: 'comissao_total_colaborador_item',
        width: 170,
        align: 'right',
        render: (v) => <Text type="success" strong>{formatCurrencyBR(v)}</Text>,
        sorter: (a, b) => (a.comissao_total_colaborador_item || 0) - (b.comissao_total_colaborador_item || 0),
      },
    ];

    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small">
          <Title level={5} style={{ margin: 0 }}>Resumo do Item</Title>
          <Descriptions bordered size="small" column={2} style={{ marginTop: 12 }}>
            <Descriptions.Item label="Cod. Produto"><Text strong>{item?.cod_produto || '-'}</Text></Descriptions.Item>
            <Descriptions.Item label="Valor do Item"><Text strong>{formatCurrencyBR(item?.faturamento_item)}</Text></Descriptions.Item>
            <Descriptions.Item label="Descrição" span={2}>{item?.descricao_produto || '-'}</Descriptions.Item>
            <Descriptions.Item label="Comissão (Total Item)" span={2}><Text type="success" strong>{formatCurrencyBR(item?.comissao_total_item)}</Text></Descriptions.Item>
          </Descriptions>
        </Card>

        <Card size="small" title="Colaboradores (clique para ver cálculo do item)">
          <Table
            size="middle"
            bordered
            columns={columns}
            dataSource={colabs}
            pagination={{ pageSize: 8 }}
            onRow={(record) => ({
              onClick: () => pushColaborador(record, record.rows),
            })}
          />
        </Card>
      </Space>
    );
  };

  const renderColaboradorPage = () => {
    const rows = current.rows || [];

    const selectColumns = [
      {
        title: 'Processo',
        dataIndex: 'processo',
        key: 'processo',
        width: 120,
      },
      {
        title: 'Cod. Produto',
        dataIndex: 'cod_produto',
        key: 'cod_produto',
        width: 140,
      },
      {
        title: 'Descrição',
        dataIndex: 'descricao_produto',
        key: 'descricao_produto',
        ellipsis: true,
      },
      {
        title: 'Valor Item',
        dataIndex: 'faturamento_item',
        key: 'faturamento_item',
        width: 140,
        align: 'right',
        render: (v) => formatCurrencyBR(v),
      },
      {
        title: 'Comissão',
        dataIndex: 'comissao_calculada',
        key: 'comissao_calculada',
        width: 140,
        align: 'right',
        render: (v) => <Text type="success" strong>{formatCurrencyBR(v)}</Text>,
      },
    ];

    const dataSource = rows.map((r, idx) => ({
      ...r,
      key: r.key || `${current.processo}-${current.item?.cod_produto || 'item'}-${current.colaborador?.nome_colaborador || 'colab'}-${idx}`,
    }));

    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small">
          <Title level={5} style={{ margin: 0 }}>Cálculo do Colaborador (no Item)</Title>
          <Descriptions bordered size="small" column={2} style={{ marginTop: 12 }}>
            <Descriptions.Item label="Processo"><Text strong>{current.processo}</Text></Descriptions.Item>
            <Descriptions.Item label="Cod. Produto"><Text strong>{current.item?.cod_produto || '-'}</Text></Descriptions.Item>
            <Descriptions.Item label="Colaborador" span={2}><Text strong>{current.colaborador?.nome_colaborador || '-'}</Text></Descriptions.Item>
          </Descriptions>
        </Card>

        {rows.length > 1 && (
          <Card size="small" title="Selecione uma linha (quando houver múltiplas)">
            <Table
              size="small"
              bordered
              columns={selectColumns}
              dataSource={dataSource}
              pagination={false}
              rowClassName={(record) => (record === selectedRow ? 'row-selected' : '')}
              onRow={(record) => ({
                onClick: () => setSelectedRow(record),
              })}
            />
          </Card>
        )}

        <Card size="small" title="Detalhamento do Cálculo">
          {selectedRow ? (
            <DetalhesCalculoModal rowData={selectedRow} />
          ) : (
            <Text type="secondary">
              {rows.length === 0
                ? 'Nenhuma linha encontrada para este colaborador/item.'
                : 'Selecione uma linha acima para ver o cálculo detalhado.'}
            </Text>
          )}
        </Card>
      </Space>
    );
  };

  const renderBody = () => {
    if (!current) return null;
    if (current.level === LEVEL.PROCESSO) return renderProcessoPage();
    if (current.level === LEVEL.ITEM) return renderItemPage();
    if (current.level === LEVEL.COLABORADOR) return renderColaboradorPage();
    return null;
  };

  return (
    <Modal
      title={
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space align="center">
              <Button onClick={goBack} disabled={stack.length <= 1} icon={<LeftOutlined />}>
                Voltar
              </Button>
              <Text type="secondary">Navegue pelos níveis para ver o cálculo</Text>
            </Space>
          </Space>
          <Breadcrumb items={breadcrumbItems} />
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={980}
      destroyOnClose
    >
      {renderBody()}
    </Modal>
  );
};

export default DetalhesFaturamentoStackModal;
