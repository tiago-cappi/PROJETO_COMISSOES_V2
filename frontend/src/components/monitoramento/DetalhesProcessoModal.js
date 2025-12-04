/**
 * DetalhesProcessoModal.js
 * 
 * Modal que exibe detalhes completos de um processo específico,
 * incluindo breakdown de TCMP e FCMP por item/colaborador.
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Descriptions,
  Tag,
  Spin,
  Alert,
  Tabs,
  Table,
  Collapse,
  Typography,
  Divider,
  Card,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  UserOutlined,
  CalculatorOutlined,
  PercentageOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { monitorAPI } from '../../services/api';
import BarraProgressoFinanceiro from './BarraProgressoFinanceiro';

const { Panel } = Collapse;
const { Text, Title } = Typography;
const { TabPane } = Tabs;

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
 * Formata percentual para exibição.
 */
const formatPercent = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-';
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Formata data para exibição.
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
};

/**
 * Componente para exibir detalhes de TCMP/FCMP por colaborador.
 */
const DetalhesColaborador = ({ colaborador, detalhes }) => {
  if (!detalhes || !detalhes.itens) {
    return <Text type="secondary">Sem detalhes disponíveis</Text>;
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
    },
    {
      title: 'Subgrupo',
      dataIndex: 'subgrupo',
      key: 'subgrupo',
      width: 100,
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
      width: 100,
      align: 'right',
      render: (v) => formatCurrency(v),
    },
    {
      title: 'Taxa',
      dataIndex: 'taxa',
      key: 'taxa',
      width: 80,
      align: 'right',
      render: (v) => formatPercent(v),
    },
    {
      title: 'FC',
      dataIndex: 'fc',
      key: 'fc',
      width: 80,
      align: 'right',
      render: (v) => formatPercent(v),
    },
  ];

  return (
    <div>
      <Table
        dataSource={detalhes.itens.map((item, idx) => ({ ...item, key: idx }))}
        columns={columns}
        size="small"
        pagination={false}
        bordered
        style={{ marginBottom: 16 }}
      />
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="Total Valor"
            value={detalhes.total_valor || 0}
            precision={2}
            formatter={(v) => formatCurrency(v)}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Soma Ponderada"
            value={detalhes.soma_ponderada || 0}
            precision={4}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title={detalhes.tcmp_final !== undefined ? 'TCMP Final' : 'FCMP Final'}
            value={(detalhes.tcmp_final || detalhes.fcmp_final || 0)}
            precision={4}
            formatter={(v) => formatPercent(v)}
          />
        </Col>
      </Row>
    </div>
  );
};

/**
 * Componente para exibir breakdown de metas (FC Detalhes).
 */
const BreakdownMetas = ({ fcDetalhes }) => {
  if (!fcDetalhes || !fcDetalhes.componentes) {
    return <Text type="secondary">Sem detalhes de metas</Text>;
  }

  const columns = [
    {
      title: 'Meta',
      dataIndex: 'nome_meta',
      key: 'nome_meta',
    },
    {
      title: 'Peso',
      dataIndex: 'peso',
      key: 'peso',
      width: 80,
      align: 'right',
      render: (v) => formatPercent(v),
    },
    {
      title: 'Realizado',
      dataIndex: 'realizado',
      key: 'realizado',
      width: 100,
      align: 'right',
      render: (v, record) => {
        // Se meta é percentual (< 10), formatar como %
        if (record.meta && record.meta < 10) {
          return formatPercent(v);
        }
        return formatCurrency(v);
      },
    },
    {
      title: 'Meta',
      dataIndex: 'meta',
      key: 'meta',
      width: 100,
      align: 'right',
      render: (v) => {
        if (v && v < 10) return formatPercent(v);
        return formatCurrency(v);
      },
    },
    {
      title: 'Atingimento',
      dataIndex: 'atingimento',
      key: 'atingimento',
      width: 100,
      align: 'right',
      render: (v) => formatPercent(v),
    },
    {
      title: 'Cap',
      dataIndex: 'atingimento_cap',
      key: 'atingimento_cap',
      width: 80,
      align: 'right',
      render: (v) => formatPercent(v),
    },
    {
      title: 'Comp. FC',
      dataIndex: 'componente_fc',
      key: 'componente_fc',
      width: 80,
      align: 'right',
      render: (v) => formatPercent(v),
    },
  ];

  return (
    <div>
      <Table
        dataSource={fcDetalhes.componentes.map((c, idx) => ({ ...c, key: idx }))}
        columns={columns}
        size="small"
        pagination={false}
        bordered
      />
      <div style={{ marginTop: 12, textAlign: 'right' }}>
        <Text strong>FC Total: </Text>
        <Text type="success" strong>{formatPercent(fcDetalhes.fc_total)}</Text>
      </div>
    </div>
  );
};

/**
 * Modal de detalhes completos de um processo.
 */
const DetalhesProcessoModal = ({ visible, processoId, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detalhes, setDetalhes] = useState(null);

  useEffect(() => {
    if (visible && processoId) {
      fetchDetalhes();
    }
  }, [visible, processoId]);

  const fetchDetalhes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await monitorAPI.getProcessoDetalhes(processoId);
      setDetalhes(response.data);
    } catch (err) {
      setError(err.message || 'Erro ao carregar detalhes do processo');
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status, type = 'pagamento') => {
    const colors = {
      pagamento: {
        COMPLETO: 'green',
        PARCIAL: 'blue',
        PENDENTE: 'orange',
      },
      reconciliacao: {
        CONCLUIDA: 'green',
        PENDENTE: 'orange',
      },
    };
    return (
      <Tag color={colors[type]?.[status] || 'default'}>
        {status}
      </Tag>
    );
  };

  return (
    <Modal
      title={
        <span>
          <InfoCircleOutlined style={{ marginRight: 8 }} />
          Detalhes do Processo {processoId}
        </span>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1000}
      destroyOnClose
    >
      {loading && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" tip="Carregando detalhes..." />
        </div>
      )}

      {error && (
        <Alert
          type="error"
          message="Erro ao carregar dados"
          description={error}
          showIcon
        />
      )}

      {!loading && !error && detalhes && (
        <Tabs defaultActiveKey="geral">
          {/* Tab: Informações Gerais */}
          <TabPane tab="Informações Gerais" key="geral">
            <Card size="small" style={{ marginBottom: 16 }}>
              <Title level={5}>Progresso Financeiro</Title>
              <BarraProgressoFinanceiro
                totalPago={detalhes.total_pago_acumulado}
                valorTotal={detalhes.valor_total_processo}
                size="large"
              />
            </Card>

            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Processo">
                <Text strong>{detalhes.processo}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Mês/Ano Faturamento">
                {detalhes.mes_ano_faturamento || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Valor Total">
                {formatCurrency(detalhes.valor_total_processo)}
              </Descriptions.Item>
              <Descriptions.Item label="Total Pago">
                <Text type="success">{formatCurrency(detalhes.total_pago_acumulado)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Saldo a Receber">
                <Text type={detalhes.saldo_a_receber > 0 ? 'warning' : 'success'}>
                  {formatCurrency(detalhes.saldo_a_receber)}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Qtd. Pagamentos">
                {detalhes.quantidade_pagamentos}
              </Descriptions.Item>
              <Descriptions.Item label="Total Antecipações">
                {formatCurrency(detalhes.total_antecipacoes)}
              </Descriptions.Item>
              <Descriptions.Item label="Total Regulares">
                {formatCurrency(detalhes.total_pagamentos_regulares)}
              </Descriptions.Item>
              <Descriptions.Item label="Status Pagamento">
                {getStatusTag(detalhes.status_pagamento, 'pagamento')}
              </Descriptions.Item>
              <Descriptions.Item label="Status Reconciliação">
                {getStatusTag(detalhes.status_reconciliacao, 'reconciliacao')}
              </Descriptions.Item>
              <Descriptions.Item label="Primeiro Pagamento">
                {formatDate(detalhes.data_primeiro_pagamento)}
              </Descriptions.Item>
              <Descriptions.Item label="Último Pagamento">
                {formatDate(detalhes.data_ultimo_pagamento)}
              </Descriptions.Item>
              <Descriptions.Item label="Última Atualização" span={2}>
                {formatDate(detalhes.ultima_atualizacao)}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Title level={5}>
              <UserOutlined style={{ marginRight: 8 }} />
              Colaboradores Envolvidos
            </Title>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {detalhes.colaboradores_envolvidos?.map((col) => (
                <Tag key={col} color="blue">{col}</Tag>
              ))}
              {(!detalhes.colaboradores_envolvidos || detalhes.colaboradores_envolvidos.length === 0) && (
                <Text type="secondary">Nenhum colaborador registrado</Text>
              )}
            </div>
          </TabPane>

          {/* Tab: Comissões */}
          <TabPane tab="Comissões" key="comissoes">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Comissão Antecipações"
                    value={detalhes.total_comissao_antecipacoes}
                    precision={4}
                    formatter={(v) => formatCurrency(v)}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Comissão Regulares"
                    value={detalhes.total_comissao_regulares}
                    precision={4}
                    formatter={(v) => formatCurrency(v)}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Comissão Total"
                    value={detalhes.total_comissao_acumulada}
                    precision={4}
                    formatter={(v) => formatCurrency(v)}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Card>
              </Col>
            </Row>

            <Title level={5}>
              <CalculatorOutlined style={{ marginRight: 8 }} />
              TCMP por Colaborador
            </Title>
            <Table
              dataSource={Object.entries(detalhes.tcmp_json || {}).map(([col, val]) => ({
                key: col,
                colaborador: col,
                tcmp: val,
              }))}
              columns={[
                { title: 'Colaborador', dataIndex: 'colaborador', key: 'colaborador' },
                {
                  title: 'TCMP',
                  dataIndex: 'tcmp',
                  key: 'tcmp',
                  align: 'right',
                  render: (v) => formatPercent(v, 4),
                },
              ]}
              size="small"
              pagination={false}
              bordered
              style={{ marginBottom: 24 }}
            />

            <Title level={5}>
              <PercentageOutlined style={{ marginRight: 8 }} />
              FCMP por Colaborador
            </Title>
            <Table
              dataSource={Object.entries(detalhes.fcmp_json || {}).map(([col, val]) => ({
                key: col,
                colaborador: col,
                fcmp: val,
              }))}
              columns={[
                { title: 'Colaborador', dataIndex: 'colaborador', key: 'colaborador' },
                {
                  title: 'FCMP',
                  dataIndex: 'fcmp',
                  key: 'fcmp',
                  align: 'right',
                  render: (v) => formatPercent(v, 4),
                },
              ]}
              size="small"
              pagination={false}
              bordered
            />
          </TabPane>

          {/* Tab: Detalhes TCMP */}
          <TabPane tab="Detalhes TCMP" key="tcmp_detalhes">
            {detalhes.tcmp_detalhes && Object.keys(detalhes.tcmp_detalhes).length > 0 ? (
              <Collapse defaultActiveKey={Object.keys(detalhes.tcmp_detalhes)}>
                {Object.entries(detalhes.tcmp_detalhes).map(([colaborador, det]) => (
                  <Panel
                    header={
                      <span>
                        <UserOutlined style={{ marginRight: 8 }} />
                        {colaborador}
                      </span>
                    }
                    key={colaborador}
                  >
                    <DetalhesColaborador colaborador={colaborador} detalhes={det} />
                  </Panel>
                ))}
              </Collapse>
            ) : (
              <Alert
                type="info"
                message="Sem detalhes de TCMP disponíveis"
                description="Os detalhes de cálculo de TCMP não estão disponíveis para este processo."
              />
            )}
          </TabPane>

          {/* Tab: Detalhes FCMP */}
          <TabPane tab="Detalhes FCMP" key="fcmp_detalhes">
            {detalhes.fcmp_detalhes && Object.keys(detalhes.fcmp_detalhes).length > 0 ? (
              <Collapse defaultActiveKey={Object.keys(detalhes.fcmp_detalhes)}>
                {Object.entries(detalhes.fcmp_detalhes).map(([colaborador, det]) => (
                  <Panel
                    header={
                      <span>
                        <UserOutlined style={{ marginRight: 8 }} />
                        {colaborador}
                      </span>
                    }
                    key={colaborador}
                  >
                    <DetalhesColaborador colaborador={colaborador} detalhes={det} />
                  </Panel>
                ))}
              </Collapse>
            ) : (
              <Alert
                type="info"
                message="Sem detalhes de FCMP disponíveis"
                description="Os detalhes de cálculo de FCMP não estão disponíveis para este processo."
              />
            )}
          </TabPane>

          {/* Tab: Observações */}
          {detalhes.observacoes && (
            <TabPane tab="Observações" key="observacoes">
              <Card>
                <Text>{detalhes.observacoes}</Text>
              </Card>
            </TabPane>
          )}
        </Tabs>
      )}
    </Modal>
  );
};

export default DetalhesProcessoModal;
