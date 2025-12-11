import React from 'react';
import {
  Modal,
  Collapse,
  Descriptions,
  Table,
  Alert,
  Tag,
  Space,
  Typography,
  Divider,
  Tree,
} from 'antd';
import {
  InfoCircleOutlined,
  CalculatorOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DollarOutlined,
} from '@ant-design/icons';

const { Panel } = Collapse;
const { Text, Title } = Typography;

/**
 * Modal para exibir detalhes completos do cálculo de um pagamento.
 * 4 Seções: Informações Gerais, TCMP, FCMP, Cálculo Final.
 */
const ModalDetalhesCalculoRecebimento = ({ visible, onClose, pagamento }) => {
  if (!pagamento) return null;

  const isAdiantamento = pagamento.tipo === 'ADIANTAMENTO' || pagamento.tipo === 'Antecipação';
  const tcmpDetalhes = pagamento.tcmp_detalhes || [];
  const fcmpDetalhes = pagamento.fcmp_detalhes || [];

  // ==================== SEÇÃO A: INFORMAÇÕES GERAIS ====================
  const renderInformacoesGerais = () => (
    <Descriptions bordered column={1} size="small">
      <Descriptions.Item label="Tipo">
        <Tag color={isAdiantamento ? 'blue' : 'green'} icon={isAdiantamento ? <CheckCircleOutlined /> : <CheckCircleOutlined />}>
          {isAdiantamento ? '🔵 Adiantamento' : '🟢 Regular'}
        </Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Processo">
        <strong style={{ fontSize: 16, color: '#1890ff' }}>{pagamento.processo}</strong>
      </Descriptions.Item>
      <Descriptions.Item label="Colaborador">
        <strong>{pagamento.nome_colaborador}</strong>
      </Descriptions.Item>
      <Descriptions.Item label="Cargo">{pagamento.cargo || '-'}</Descriptions.Item>
      <Descriptions.Item label="Data Pagamento">
        {pagamento.data_pagamento ? new Date(pagamento.data_pagamento).toLocaleDateString('pt-BR') : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="Valor Base">
        <strong style={{ fontSize: 16 }}>
          {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(pagamento.valor_pago || 0)}
        </strong>
      </Descriptions.Item>
    </Descriptions>
  );

  // ==================== SEÇÃO B: TCMP ====================
  const renderTCMP = () => {
    if (!tcmpDetalhes || tcmpDetalhes.length === 0) {
      return (
        <Alert
          message="Detalhes de TCMP não disponíveis"
          type="info"
          showIcon
        />
      );
    }

    const colunasTCMP = [
      {
        title: 'Item',
        dataIndex: 'item',
        key: 'item',
        width: 200,
        ellipsis: true,
      },
      {
        title: 'Valor Item',
        dataIndex: 'valor',
        key: 'valor',
        align: 'right',
        render: (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0),
      },
      {
        title: 'Taxa Item',
        dataIndex: 'taxa',
        key: 'taxa',
        align: 'center',
        render: (val) => `${(val * 100).toFixed(2)}%`,
      },
      {
        title: 'Peso',
        dataIndex: 'peso',
        key: 'peso',
        align: 'center',
        render: (val) => `${(val * 100).toFixed(1)}%`,
      },
      {
        title: 'TCMP Parcial',
        dataIndex: 'tcmp_parcial',
        key: 'tcmp_parcial',
        align: 'center',
        render: (val) => <strong>{(val * 100).toFixed(2)}%</strong>,
      },
    ];

    const totalValor = tcmpDetalhes.reduce((acc, d) => acc + (d.valor || 0), 0);
    const tcmpFinal = tcmpDetalhes.reduce((acc, d) => acc + (d.tcmp_parcial || 0), 0);

    return (
      <div>
        <Alert
          message={
            <div>
              <strong>Como foi calculado:</strong>
              <br />
              <code>TCMP = Σ (Taxa_Item × Valor_Item) / Valor_Total</code>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Table
          columns={colunasTCMP}
          dataSource={tcmpDetalhes.map((d, idx) => ({ ...d, key: idx }))}
          pagination={false}
          size="small"
          bordered
          summary={() => (
            <Table.Summary fixed>
              <Table.Summary.Row style={{ backgroundColor: '#fafafa' }}>
                <Table.Summary.Cell index={0}>
                  <strong>TOTAL</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={1} align="right">
                  <strong>
                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalValor)}
                  </strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2} align="center">-</Table.Summary.Cell>
                <Table.Summary.Cell index={3} align="center">
                  <strong>100%</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4} align="center">
                  <strong style={{ fontSize: 16, color: '#1890ff' }}>
                    {(tcmpFinal * 100).toFixed(2)}%
                  </strong>
                </Table.Summary.Cell>
              </Table.Summary.Row>
            </Table.Summary>
          )}
        />
      </div>
    );
  };

  // ==================== SEÇÃO C: FCMP ====================
  const renderFCMP = () => {
    if (isAdiantamento) {
      return (
        <Alert
          message="FCMP para Adiantamentos"
          description={
            <div>
              <p>⚠️ <strong>Adiantamentos sempre usam FC fixo = 1.0</strong></p>
              <Divider />
              <p><strong>Motivo:</strong></p>
              <ul>
                <li>Pago <strong>ANTES</strong> do faturamento</li>
                <li>Metas ainda não foram realizadas</li>
                <li>FC real será calculado após fechamento</li>
                <li>Ajuste será feito na <strong>Reconciliação</strong></li>
              </ul>
              <Divider />
              <p style={{ marginBottom: 0 }}>
                ✅ <strong>FCMP Aplicado: 1.0000</strong>
              </p>
            </div>
          }
          type="warning"
          showIcon
          icon={<WarningOutlined />}
        />
      );
    }

    // Para pagamentos regulares
    if (!fcmpDetalhes || fcmpDetalhes.length === 0) {
      return (
        <Alert
          message="Detalhes de FCMP não disponíveis"
          type="info"
          showIcon
        />
      );
    }

    const colunasFCMP = [
      {
        title: 'Item',
        dataIndex: 'item',
        key: 'item',
        width: 180,
        ellipsis: true,
      },
      {
        title: 'Comissão Item',
        dataIndex: 'comissao',
        key: 'comissao',
        align: 'right',
        render: (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0),
      },
      {
        title: 'FC Real',
        dataIndex: 'fc',
        key: 'fc',
        align: 'center',
        render: (val) => {
          const cor = val > 1 ? '#52c41a' : val < 1 ? '#ff4d4f' : '#000';
          return <strong style={{ color: cor }}>{val?.toFixed(4)}</strong>;
        },
      },
      {
        title: 'Peso',
        dataIndex: 'peso',
        key: 'peso',
        align: 'center',
        render: (val) => `${(val * 100).toFixed(1)}%`,
      },
      {
        title: 'FCMP Parcial',
        dataIndex: 'fcmp_parcial',
        key: 'fcmp_parcial',
        align: 'center',
        render: (val) => <strong>{val?.toFixed(4)}</strong>,
      },
    ];

    const totalComissao = fcmpDetalhes.reduce((acc, d) => acc + (d.comissao || 0), 0);
    const fcmpFinal = fcmpDetalhes.reduce((acc, d) => acc + (d.fcmp_parcial || 0), 0);

    return (
      <div>
        <Alert
          message={
            <div>
              <strong>Como foi calculado:</strong>
              <br />
              <code>FCMP = Σ (FC_Item × Comissão_Item) / Comissão_Total</code>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Table
          columns={colunasFCMP}
          dataSource={fcmpDetalhes.map((d, idx) => ({ ...d, key: idx }))}
          pagination={false}
          size="small"
          bordered
          summary={() => (
            <Table.Summary fixed>
              <Table.Summary.Row style={{ backgroundColor: '#fafafa' }}>
                <Table.Summary.Cell index={0}>
                  <strong>TOTAL</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={1} align="right">
                  <strong>
                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalComissao)}
                  </strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2} align="center">-</Table.Summary.Cell>
                <Table.Summary.Cell index={3} align="center">
                  <strong>100%</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4} align="center">
                  <strong style={{ fontSize: 16, color: fcmpFinal > 1 ? '#52c41a' : fcmpFinal < 1 ? '#ff4d4f' : '#000' }}>
                    {fcmpFinal.toFixed(4)}
                  </strong>
                </Table.Summary.Cell>
              </Table.Summary.Row>
            </Table.Summary>
          )}
        />
      </div>
    );
  };

  // ==================== SEÇÃO D: CÁLCULO FINAL ====================
  const renderCalculoFinal = () => {
    const valorPago = pagamento.valor_pago || 0;
    const tcmp = pagamento.tcmp || 0;
    const fcmp = pagamento.fcmp || 1.0;
    const comissaoFinal = pagamento.comissao_calculada || 0;

    return (
      <div style={{ padding: 16, backgroundColor: '#f0f2f5', borderRadius: 4 }}>
        <Title level={5} style={{ marginBottom: 16 }}>
          <CalculatorOutlined /> Fórmula
        </Title>
        <div style={{ backgroundColor: '#fff', padding: 16, borderRadius: 4, marginBottom: 16 }}>
          <pre style={{ margin: 0, fontSize: 14 }}>
            <strong>Comissão = Valor_Pago × TCMP × FCMP</strong>
          </pre>
        </div>

        <Title level={5} style={{ marginBottom: 16 }}>Aplicando os valores:</Title>
        <div style={{ backgroundColor: '#fff', padding: 16, borderRadius: 4, marginBottom: 16 }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text>
              Comissão = {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorPago)}{' '}
              × {(tcmp * 100).toFixed(2)}% × {fcmp.toFixed(4)}
            </Text>
            <Text>
              Comissão = {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorPago)}{' '}
              × {tcmp.toFixed(4)} × {fcmp.toFixed(4)}
            </Text>
            <Text>
              Comissão = <strong style={{ fontSize: 16 }}>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(comissaoFinal)}
              </strong>
            </Text>
          </Space>
        </div>

        <Alert
          message={
            <span>
              <CheckCircleOutlined /> <strong>Comissão Final: </strong>
              <span style={{ fontSize: 18, color: '#52c41a', fontWeight: 'bold' }}>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(comissaoFinal)}
              </span>
            </span>
          }
          type="success"
          showIcon={false}
        />
      </div>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <DollarOutlined />
          <span>Detalhes do Cálculo - {pagamento.processo}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={900}
      destroyOnClose
    >
      <Collapse defaultActiveKey={['1', '2', '3', '4']} accordion={false}>
        <Panel
          header={
            <Space>
              <InfoCircleOutlined />
              <strong>📊 Informações Gerais</strong>
            </Space>
          }
          key="1"
        >
          {renderInformacoesGerais()}
        </Panel>

        <Panel
          header={
            <Space>
              <CalculatorOutlined />
              <strong>📈 TCMP (Taxa de Comissão Média Ponderada)</strong>
            </Space>
          }
          key="2"
        >
          {renderTCMP()}
        </Panel>

        <Panel
          header={
            <Space>
              {isAdiantamento ? <WarningOutlined /> : <CheckCircleOutlined />}
              <strong>{isAdiantamento ? '🔵 FCMP (Adiantamento)' : '🟢 FCMP (Pagamento Regular)'}</strong>
            </Space>
          }
          key="3"
        >
          {renderFCMP()}
        </Panel>

        <Panel
          header={
            <Space>
              <DollarOutlined />
              <strong>💰 Cálculo Final</strong>
            </Space>
          }
          key="4"
        >
          {renderCalculoFinal()}
        </Panel>
      </Collapse>
    </Modal>
  );
};

export default ModalDetalhesCalculoRecebimento;
