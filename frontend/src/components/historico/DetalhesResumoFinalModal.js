import React, { useMemo } from 'react';
import { Modal, Card, Descriptions, Table, Typography, Divider } from 'antd';

const { Title, Text } = Typography;

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

const DetalhesResumoFinalModal = ({ visible, onClose, colaboradorNome, periodo, linhas = [] }) => {
  const resumo = useMemo(() => {
    const totals = new Map();
    let totalMes = 0;

    for (const row of linhas) {
      const tipo = row.Tipo_Comissao || row.tipo_comissao || '—';
      const valor = Number(row.Comissao_Calculada ?? row.comissao_calculada ?? 0);
      totalMes += Number.isNaN(valor) ? 0 : valor;
      totals.set(tipo, (totals.get(tipo) || 0) + (Number.isNaN(valor) ? 0 : valor));
    }

    const breakdown = Array.from(totals.entries()).map(([tipo, valor]) => ({
      key: tipo,
      tipo,
      valor,
    }));

    breakdown.sort((a, b) => Math.abs(b.valor) - Math.abs(a.valor));

    return { totalMes, breakdown };
  }, [linhas]);

  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 160,
      render: (v) => <Text strong>{v}</Text>,
    },
    {
      title: 'Valor',
      dataIndex: 'valor',
      key: 'valor',
      align: 'right',
      render: (v) => {
        const num = Number(v);
        const isNeg = !Number.isNaN(num) && num < 0;
        return <Text type={isNeg ? 'danger' : 'success'} strong>{formatCurrencyBR(num)}</Text>;
      },
    },
  ];

  const colunasLinhas = [
    { title: 'Tipo', dataIndex: 'Tipo_Comissao', key: 'Tipo_Comissao', width: 140 },
    { title: 'Processo', dataIndex: 'Processo', key: 'Processo', width: 160, ellipsis: true },
    { title: 'NF', dataIndex: 'Numero_NF', key: 'Numero_NF', width: 120 },
    {
      title: 'Valor Base',
      dataIndex: 'Valor_Base',
      key: 'Valor_Base',
      width: 140,
      align: 'right',
      render: (v) => formatCurrencyBR(v),
    },
    {
      title: 'Comissão',
      dataIndex: 'Comissao_Calculada',
      key: 'Comissao_Calculada',
      width: 140,
      align: 'right',
      render: (v) => {
        const num = Number(v);
        const isNeg = !Number.isNaN(num) && num < 0;
        return <Text type={isNeg ? 'danger' : 'success'} strong>{formatCurrencyBR(num)}</Text>;
      },
    },
    { title: 'Obs.', dataIndex: 'Observacao', key: 'Observacao', ellipsis: true },
  ];

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      onOk={onClose}
      okText="Fechar"
      cancelButtonProps={{ style: { display: 'none' } }}
      width={980}
      title="Detalhes do Resultado Final"
      destroyOnClose
    >
      <SpaceBlock>
        <Card size="small">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="Colaborador">
              <Text strong>{colaboradorNome || '-'}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Período">
              <Text>{periodo || '-'}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Total do Mês" span={2}>
              <Text strong style={{ fontSize: '16px' }}>{formatCurrencyBR(resumo.totalMes)}</Text>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Divider />

        <Title level={5} style={{ marginTop: 0 }}>Breakdown por Tipo</Title>
        <Table
          size="small"
          bordered
          pagination={false}
          columns={columns}
          dataSource={resumo.breakdown}
        />

        <Divider />

        <Title level={5} style={{ marginTop: 0 }}>Linhas do Banco Histórico (mês)</Title>
        <Table
          size="small"
          bordered
          rowKey={(r, idx) => `${r.Data_Execucao || ''}-${r.Tipo_Comissao || ''}-${idx}`}
          pagination={{ pageSize: 8 }}
          columns={colunasLinhas}
          dataSource={Array.isArray(linhas) ? linhas : []}
          scroll={{ x: 'max-content' }}
        />
      </SpaceBlock>
    </Modal>
  );
};

const SpaceBlock = ({ children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>{children}</div>
);

export default DetalhesResumoFinalModal;
