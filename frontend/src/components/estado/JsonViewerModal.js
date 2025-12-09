/**
 * JsonViewerModal.js
 * 
 * Modal reutilizável para exibição de dados JSON de forma limpa e formatada.
 * Suporta visualização de TCMP, FCMP, detalhes de cálculo e comissões adiantadas.
 */

import React from 'react';
import {
  Modal,
  Collapse,
  Descriptions,
  Table,
  Typography,
  Tag,
  Empty,
  Divider,
} from 'antd';
import {
  UserOutlined,
  CalculatorOutlined,
} from '@ant-design/icons';

const { Panel } = Collapse;
const { Text, Title } = Typography;

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
 * Formata percentual para exibição.
 */
const formatPercent = (value, decimals = 4) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Renderiza dados simples de TCMP/FCMP (colaborador -> valor).
 */
const RenderSimpleJson = ({ data, label, formatter }) => {
  if (!data || Object.keys(data).length === 0) {
    return <Empty description="Sem dados" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  return (
    <Descriptions column={1} bordered size="small">
      {Object.entries(data).map(([colaborador, valor]) => (
        <Descriptions.Item 
          key={colaborador} 
          label={
            <span>
              <UserOutlined style={{ marginRight: 8 }} />
              {colaborador}
            </span>
          }
        >
          <Text strong style={{ color: '#1890ff' }}>
            {formatter ? formatter(valor) : valor}
          </Text>
        </Descriptions.Item>
      ))}
    </Descriptions>
  );
};

/**
 * Renderiza detalhes de TCMP/FCMP com breakdown por item.
 */
const RenderDetalhesJson = ({ data, tipo }) => {
  if (!data || Object.keys(data).length === 0) {
    return <Empty description="Sem detalhes disponíveis" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  const columns = [
    {
      title: 'Negócio',
      dataIndex: 'negocio',
      key: 'negocio',
      width: 80,
    },
    {
      title: 'Grupo',
      dataIndex: 'grupo',
      key: 'grupo',
      width: 120,
      ellipsis: true,
    },
    {
      title: 'Subgrupo',
      dataIndex: 'subgrupo',
      key: 'subgrupo',
      width: 100,
      ellipsis: true,
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_mercadoria',
      key: 'tipo_mercadoria',
      width: 80,
    },
    {
      title: 'Valor',
      dataIndex: 'valor',
      key: 'valor',
      width: 110,
      align: 'right',
      render: (v) => formatCurrency(v),
    },
    {
      title: 'Taxa',
      dataIndex: 'taxa',
      key: 'taxa',
      width: 80,
      align: 'right',
      render: (v) => formatPercent(v, 2),
    },
    {
      title: 'FC',
      dataIndex: 'fc',
      key: 'fc',
      width: 70,
      align: 'right',
      render: (v) => formatPercent(v, 2),
    },
  ];

  return (
    <Collapse defaultActiveKey={Object.keys(data).slice(0, 1)}>
      {Object.entries(data).map(([colaborador, detalhes]) => (
        <Panel
          key={colaborador}
          header={
            <span>
              <UserOutlined style={{ marginRight: 8 }} />
              <Text strong>{colaborador}</Text>
              {detalhes && (
                <Tag color="blue" style={{ marginLeft: 12 }}>
                  {tipo === 'tcmp' ? 'TCMP' : 'FCMP'}: {formatPercent(detalhes.tcmp_final || detalhes.fcmp_final, 4)}
                </Tag>
              )}
            </span>
          }
        >
          {detalhes && detalhes.itens && detalhes.itens.length > 0 ? (
            <>
              <Table
                dataSource={detalhes.itens.map((item, idx) => ({ ...item, key: idx }))}
                columns={columns}
                size="small"
                pagination={false}
                bordered
                scroll={{ x: 600 }}
              />
              <Divider style={{ margin: '12px 0' }} />
              <Descriptions column={3} size="small">
                <Descriptions.Item label="Total Valor">
                  <Text strong>{formatCurrency(detalhes.total_valor)}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Soma Ponderada">
                  <Text>{(detalhes.soma_ponderada || 0).toFixed(4)}</Text>
                </Descriptions.Item>
                <Descriptions.Item label={tipo === 'tcmp' ? 'TCMP Final' : 'FCMP Final'}>
                  <Text strong style={{ color: '#52c41a' }}>
                    {formatPercent(detalhes.tcmp_final || detalhes.fcmp_final, 4)}
                  </Text>
                </Descriptions.Item>
              </Descriptions>
            </>
          ) : (
            <Empty description="Sem itens detalhados" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </Panel>
      ))}
    </Collapse>
  );
};

/**
 * Renderiza comissões adiantadas por colaborador.
 */
const RenderComissoesAdiantadas = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return <Empty description="Sem comissões adiantadas" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  return (
    <Descriptions column={1} bordered size="small">
      {Object.entries(data).map(([colaborador, valor]) => (
        <Descriptions.Item 
          key={colaborador} 
          label={
            <span>
              <UserOutlined style={{ marginRight: 8 }} />
              {colaborador}
            </span>
          }
        >
          <Text strong style={{ color: '#722ed1' }}>
            {formatCurrency(valor)}
          </Text>
        </Descriptions.Item>
      ))}
    </Descriptions>
  );
};

/**
 * Modal para visualização de dados JSON.
 * 
 * @param {Object} props
 * @param {boolean} props.visible - Se o modal está visível
 * @param {Function} props.onClose - Callback para fechar o modal
 * @param {string} props.title - Título do modal
 * @param {string} props.tipo - Tipo de dados: 'tcmp', 'fcmp', 'tcmp_detalhes', 'fcmp_detalhes', 'comissoes_adiantadas'
 * @param {Object} props.data - Dados JSON a serem exibidos
 */
const JsonViewerModal = ({ visible, onClose, title, tipo, data }) => {
  const renderContent = () => {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
      return <Empty description="Sem dados disponíveis" />;
    }

    switch (tipo) {
      case 'tcmp':
        return (
          <div>
            <Title level={5}>
              <CalculatorOutlined style={{ marginRight: 8 }} />
              Taxa de Comissão Média Ponderada por Colaborador
            </Title>
            <RenderSimpleJson data={data} formatter={formatPercent} />
          </div>
        );

      case 'fcmp':
        return (
          <div>
            <Title level={5}>
              <CalculatorOutlined style={{ marginRight: 8 }} />
              Fator de Correção Médio Ponderado por Colaborador
            </Title>
            <RenderSimpleJson data={data} formatter={formatPercent} />
          </div>
        );

      case 'tcmp_detalhes':
        return (
          <div>
            <Title level={5}>
              <CalculatorOutlined style={{ marginRight: 8 }} />
              Detalhes do Cálculo de TCMP
            </Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              Breakdown da taxa de comissão por item do processo
            </Text>
            <RenderDetalhesJson data={data} tipo="tcmp" />
          </div>
        );

      case 'fcmp_detalhes':
        return (
          <div>
            <Title level={5}>
              <CalculatorOutlined style={{ marginRight: 8 }} />
              Detalhes do Cálculo de FCMP
            </Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              Breakdown do fator de correção por item do processo
            </Text>
            <RenderDetalhesJson data={data} tipo="fcmp" />
          </div>
        );

      case 'comissoes_adiantadas':
        return (
          <div>
            <Title level={5}>
              <CalculatorOutlined style={{ marginRight: 8 }} />
              Comissões Adiantadas por Colaborador
            </Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              Valores de comissão já pagos como adiantamento
            </Text>
            <RenderComissoesAdiantadas data={data} />
          </div>
        );

      default:
        // Renderizar como JSON formatado genérico
        return (
          <pre style={{ 
            background: '#f5f5f5', 
            padding: 16, 
            borderRadius: 8,
            maxHeight: 400,
            overflow: 'auto',
            fontSize: 12,
          }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        );
    }
  };

  return (
    <Modal
      title={title || 'Visualizar Dados'}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      styles={{ body: { maxHeight: '70vh', overflow: 'auto' } }}
    >
      {renderContent()}
    </Modal>
  );
};

export default JsonViewerModal;
