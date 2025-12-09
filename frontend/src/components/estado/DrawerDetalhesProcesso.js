import React, { useState } from 'react';
import {
  Drawer,
  Tabs,
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Descriptions,
  Timeline,
  Empty,
  Tooltip,
  Space,
} from 'antd';
import {
  DollarOutlined,
  CalendarOutlined,
  TeamOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import JsonViewerModal from './JsonViewerModal';

const { TabPane } = Tabs;

/**
 * Drawer lateral com detalhes completos de um processo.
 * Organiza as 25 colunas em abas lógicas para facilitar a compreensão.
 */
const DrawerDetalhesProcesso = ({ visible, onClose, processo }) => {
  const [jsonModalVisible, setJsonModalVisible] = useState(false);
  const [jsonModalData, setJsonModalData] = useState(null);
  const [jsonModalType, setJsonModalType] = useState(null);

  if (!processo) return null;

  // Handler para abrir modal JSON
  const handleVerJson = (data, type) => {
    setJsonModalData(data);
    setJsonModalType(type);
    setJsonModalVisible(true);
  };

  // ==================== ABA 1: VISÃO GERAL ====================
  const renderVisaoGeral = () => {
    const valorTotal = processo.VALOR_TOTAL_PROCESSO || 0;
    const totalPago = processo.TOTAL_PAGO_ACUMULADO || 0;
    const saldoReceber = processo.SALDO_A_RECEBER || 0;
    const percentualPago = valorTotal > 0 ? ((totalPago / valorTotal) * 100).toFixed(1) : 0;

    return (
      <div>
        {/* Cards de Resumo Financeiro */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Valor Total do Processo"
                value={valorTotal}
                precision={2}
                valueStyle={{ color: '#1890ff' }}
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Pago Acumulado"
                value={totalPago}
                precision={2}
                valueStyle={{ color: '#52c41a' }}
                suffix={`(${percentualPago}%)`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Saldo a Receber"
                value={saldoReceber}
                precision={2}
                valueStyle={{ color: saldoReceber > 0 ? '#faad14' : '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Quantidade de Pagamentos"
                value={processo.QUANTIDADE_PAGAMENTOS || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Breakdown de Pagamentos */}
        <Card title="Breakdown de Pagamentos" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Statistic
                title="Antecipações"
                value={processo.TOTAL_ANTECIPACOES || 0}
                precision={2}
                prefix="R$"
                valueStyle={{ fontSize: 18 }}
              />
            </Col>
            <Col xs={24} md={12}>
              <Statistic
                title="Pagamentos Regulares"
                value={processo.TOTAL_PAGAMENTOS_REGULARES || 0}
                precision={2}
                prefix="R$"
                valueStyle={{ fontSize: 18 }}
              />
            </Col>
          </Row>
        </Card>

        {/* Informações Gerais */}
        <Card title="Informações Gerais">
          <Descriptions bordered column={{ xs: 1, sm: 1, md: 2 }}>
            <Descriptions.Item label="Processo" span={2}>
              <strong style={{ fontSize: 16, color: '#1890ff' }}>
                {processo.PROCESSO}
              </strong>
            </Descriptions.Item>
            <Descriptions.Item label="Status do Processo">
              <Tag color={processo.STATUS_PROCESSO === 'FATURADO' ? 'green' : 'blue'}>
                {processo.STATUS_PROCESSO || '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Status de Pagamento">
              <Tag
                color={
                  processo.STATUS_PAGAMENTO === 'COMPLETO'
                    ? 'green'
                    : processo.STATUS_PAGAMENTO === 'PARCIAL'
                    ? 'gold'
                    : 'blue'
                }
              >
                {processo.STATUS_PAGAMENTO || '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Data Primeiro Pagamento">
              <CalendarOutlined /> {processo.DATA_PRIMEIRO_PAGAMENTO || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Data Último Pagamento">
              <CalendarOutlined /> {processo.DATA_ULTIMO_PAGAMENTO || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Mês Faturamento">
              {processo.MES_FATURAMENTO || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Ano Faturamento">
              {processo.ANO_FATURAMENTO || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Última Atualização" span={2}>
              <ClockCircleOutlined /> {processo.ULTIMA_ATUALIZACAO || '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    );
  };

  // ==================== ABA 2: COLABORADORES & COMISSÕES ====================
  const renderColaboradoresComissoes = () => {
    const colaboradores = processo.COLABORADORES_ENVOLVIDOS || [];
    const tcmpJson = processo.TCMP_JSON || {};
    const fcmpJson = processo.FCMP_JSON || {};

    // Construir dados da tabela
    const dadosTabela = colaboradores.map((colab) => ({
      key: colab,
      colaborador: colab,
      tcmp: tcmpJson[colab] != null ? (tcmpJson[colab] * 100).toFixed(2) + '%' : '-',
      fcmp: fcmpJson[colab] != null ? fcmpJson[colab].toFixed(4) : '-',
      comissao_antecipacoes: '-', // Pode vir do JSON de comissões adiantadas
      comissao_regulares: '-',
      total_comissao: '-',
    }));

    const columns = [
      {
        title: 'Colaborador',
        dataIndex: 'colaborador',
        key: 'colaborador',
        render: (text) => <strong>{text}</strong>,
      },
      {
        title: 'TCMP',
        dataIndex: 'tcmp',
        key: 'tcmp',
        align: 'center',
      },
      {
        title: 'FCMP',
        dataIndex: 'fcmp',
        key: 'fcmp',
        align: 'center',
      },
      {
        title: 'Comissão Antecipações',
        dataIndex: 'comissao_antecipacoes',
        key: 'comissao_antecipacoes',
        align: 'right',
      },
      {
        title: 'Comissão Regulares',
        dataIndex: 'comissao_regulares',
        key: 'comissao_regulares',
        align: 'right',
      },
      {
        title: 'Total Comissão',
        dataIndex: 'total_comissao',
        key: 'total_comissao',
        align: 'right',
      },
    ];

    return (
      <div>
        {/* Cards de Totais de Comissão */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} md={8}>
            <Card>
              <Statistic
                title="Total Comissão Antecipações"
                value={processo.TOTAL_COMISSAO_ANTECIPACOES || 0}
                precision={2}
                prefix="R$"
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic
                title="Total Comissão Regulares"
                value={processo.TOTAL_COMISSAO_REGULARES || 0}
                precision={2}
                prefix="R$"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic
                title="Total Comissão Acumulada"
                value={processo.TOTAL_COMISSAO_ACUMULADA || 0}
                precision={2}
                prefix="R$"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Tabela de Colaboradores */}
        <Card
          title={
            <Space>
              <TeamOutlined />
              <span>Colaboradores e Comissões</span>
            </Space>
          }
          extra={
            <Space>
              <Button
                size="small"
                onClick={() => handleVerJson(processo.TCMP_JSON, 'tcmp')}
              >
                Ver TCMP JSON
              </Button>
              <Button
                size="small"
                onClick={() => handleVerJson(processo.FCMP_JSON, 'fcmp')}
              >
                Ver FCMP JSON
              </Button>
            </Space>
          }
        >
          {dadosTabela.length > 0 ? (
            <Table
              columns={columns}
              dataSource={dadosTabela}
              pagination={false}
              size="small"
              bordered
            />
          ) : (
            <Empty description="Nenhum colaborador envolvido" />
          )}
        </Card>

        {/* Botão para ver Comissões Adiantadas JSON */}
        <Card title="Detalhes Adicionais" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              block
              onClick={() =>
                handleVerJson(processo.COMISSOES_ADIANTADAS_JSON, 'comissoes_adiantadas')
              }
            >
              Ver Detalhes de Comissões Adiantadas (JSON)
            </Button>
          </Space>
        </Card>
      </div>
    );
  };

  // ==================== ABA 3: MÉTRICAS & STATUS ====================
  const renderMetricasStatus = () => {
    const getStatusIcon = (status) => {
      if (status === 'CALCULADO' || status === 'COMPLETO') {
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      } else if (status === 'PARCIAL') {
        return <WarningOutlined style={{ color: '#faad14' }} />;
      } else {
        return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
      }
    };

    return (
      <div>
        {/* Cards de Status */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} md={12}>
            <Card>
              <Descriptions bordered column={1}>
                <Descriptions.Item
                  label={
                    <Tooltip title="Indica se as médias de TCMP/FCMP foram calculadas completamente ou parcialmente (quando há adiantamentos)">
                      <span>
                        Status Cálculo Médias <WarningOutlined style={{ color: '#faad14' }} />
                      </span>
                    </Tooltip>
                  }
                >
                  <Space>
                    {getStatusIcon(processo.STATUS_CALCULO_MEDIAS)}
                    <Tag
                      color={
                        processo.STATUS_CALCULO_MEDIAS === 'CALCULADO'
                          ? 'green'
                          : processo.STATUS_CALCULO_MEDIAS === 'PARCIAL'
                          ? 'gold'
                          : 'blue'
                      }
                    >
                      {processo.STATUS_CALCULO_MEDIAS || '-'}
                    </Tag>
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card>
              <Descriptions bordered column={1}>
                <Descriptions.Item
                  label={
                    <Tooltip title="Status da reconciliação entre sistema e dados de entrada">
                      <span>
                        Status Reconciliação <FileTextOutlined />
                      </span>
                    </Tooltip>
                  }
                >
                  <Space>
                    {getStatusIcon(processo.STATUS_RECONCILIACAO)}
                    <Tag color="blue">{processo.STATUS_RECONCILIACAO || '-'}</Tag>
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
        </Row>

        {/* Detalhes TCMP e FCMP */}
        <Card
          title="Detalhes de Cálculo (TCMP/FCMP)"
          extra={
            <Space>
              <Button
                size="small"
                onClick={() => handleVerJson(processo.TCMP_DETALHES_JSON, 'tcmp_detalhes')}
              >
                Ver TCMP Detalhes
              </Button>
              <Button
                size="small"
                onClick={() => handleVerJson(processo.FCMP_DETALHES_JSON, 'fcmp_detalhes')}
              >
                Ver FCMP Detalhes
              </Button>
            </Space>
          }
        >
          <Descriptions bordered column={1}>
            <Descriptions.Item label="TCMP Detalhes Disponível">
              {processo.TCMP_DETALHES_JSON &&
              Object.keys(processo.TCMP_DETALHES_JSON).length > 0 ? (
                <Tag color="green">Sim</Tag>
              ) : (
                <Tag>Não</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="FCMP Detalhes Disponível">
              {processo.FCMP_DETALHES_JSON &&
              Object.keys(processo.FCMP_DETALHES_JSON).length > 0 ? (
                <Tag color="green">Sim</Tag>
              ) : (
                <Tag>Não</Tag>
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Informações de Faturamento */}
        <Card title="Informações de Faturamento" style={{ marginTop: 16 }}>
          <Descriptions bordered column={{ xs: 1, sm: 2 }}>
            <Descriptions.Item label="Mês Faturamento">
              {processo.MES_FATURAMENTO || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Ano Faturamento">
              {processo.ANO_FATURAMENTO || '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    );
  };

  // ==================== ABA 4: RECONCILIAÇÃO ====================
  const renderReconciliacao = () => {
    const statusRecon = processo.STATUS_RECONCILIACAO;
    const reconCalculada = statusRecon === 'CALCULADO';
    
    // Se não foi calculada, mostrar indicativo visual
    if (!reconCalculada) {
      return (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical" size="large" style={{ textAlign: 'center' }}>
                <ClockCircleOutlined style={{ fontSize: 48, color: '#faad14' }} />
                <div>
                  <strong>Reconciliação Pendente</strong>
                  <p style={{ color: '#8c8c8c', marginTop: 8 }}>
                    A reconciliação deste processo ainda não foi calculada.
                    <br />
                    Status atual: <Tag color="blue">{statusRecon || 'PENDENTE'}</Tag>
                  </p>
                </div>
              </Space>
            }
          />
        </Card>
      );
    }

    // Dados da reconciliação
    const comissoesAdiantadas = processo.COMISSOES_ADIANTADAS_JSON || {};
    const tcmpJson = processo.TCMP_JSON || {};
    const fcmpJson = processo.FCMP_JSON || {};
    const totalAdiantamentos = processo.TOTAL_COMISSAO_ANTECIPACOES || 0;
    const totalComissaoRegulares = processo.TOTAL_COMISSAO_REGULARES || 0;

    // Calcular reconciliação para cada colaborador
    const reconciliacoes = Object.keys(comissoesAdiantadas).map((colaborador) => {
      const comissaoAdiantada = comissoesAdiantadas[colaborador] || 0;
      const tcmp = tcmpJson[colaborador] || 0;
      const fcmp = fcmpJson[colaborador] || 1.0;
      
      // Fórmula: Reconciliação = Comissao_Adiantada × (FCMP - 1.0)
      const diferencaFc = fcmp - 1.0;
      const ajusteReconciliacao = comissaoAdiantada * diferencaFc;
      const comissaoDeveria = comissaoAdiantada * fcmp;

      return {
        colaborador,
        comissaoAdiantada,
        tcmp,
        fcmp,
        diferencaFc,
        comissaoDeveria,
        ajusteReconciliacao,
      };
    });

    const saldoTotal = reconciliacoes.reduce((acc, r) => acc + r.ajusteReconciliacao, 0);
    
    const getSaldoStatus = (saldo) => {
      if (Math.abs(saldo) < 0.01) return { text: 'Quitado', color: 'green' };
      if (saldo > 0) return { text: 'A Pagar', color: 'gold' };
      return { text: 'A Descontar', color: 'red' };
    };

    const saldoStatus = getSaldoStatus(saldoTotal);

    // Colunas da tabela de reconciliação
    const columns = [
      {
        title: 'Colaborador',
        dataIndex: 'colaborador',
        key: 'colaborador',
        render: (text) => <strong>{text}</strong>,
      },
      {
        title: 'Comissão Adiantada (FC=1.0)',
        dataIndex: 'comissaoAdiantada',
        key: 'comissaoAdiantada',
        align: 'right',
        render: (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val),
      },
      {
        title: 'TCMP',
        dataIndex: 'tcmp',
        key: 'tcmp',
        align: 'center',
        render: (val) => (val * 100).toFixed(2) + '%',
      },
      {
        title: 'FCMP Real',
        dataIndex: 'fcmp',
        key: 'fcmp',
        align: 'center',
        render: (val) => val.toFixed(4),
      },
      {
        title: 'Diferença FC',
        dataIndex: 'diferencaFc',
        key: 'diferencaFc',
        align: 'center',
        render: (val) => (
          <span style={{ color: val > 0 ? '#52c41a' : val < 0 ? '#ff4d4f' : '#000' }}>
            {val > 0 ? '+' : ''}{val.toFixed(4)}
          </span>
        ),
      },
      {
        title: 'Comissão Deveria (FC Real)',
        dataIndex: 'comissaoDeveria',
        key: 'comissaoDeveria',
        align: 'right',
        render: (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val),
      },
      {
        title: 'Ajuste Reconciliação',
        dataIndex: 'ajusteReconciliacao',
        key: 'ajusteReconciliacao',
        align: 'right',
        render: (val) => (
          <strong style={{ color: val > 0 ? '#52c41a' : val < 0 ? '#ff4d4f' : '#000' }}>
            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)}
          </strong>
        ),
      },
    ];

    return (
      <div>
        {/* Card de Resumo da Reconciliação */}
        <Card style={{ marginBottom: 24, backgroundColor: '#f0f2f5' }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Statistic
                title="Saldo Final da Reconciliação"
                value={saldoTotal}
                precision={2}
                valueStyle={{
                  color: saldoStatus.color === 'green' ? '#52c41a' : saldoStatus.color === 'gold' ? '#faad14' : '#ff4d4f',
                  fontSize: 24,
                  fontWeight: 'bold',
                }}
                prefix={saldoTotal >= 0 ? '+' : ''}
                suffix={
                  <Tag color={saldoStatus.color} style={{ marginLeft: 12, fontSize: 14 }}>
                    {saldoStatus.text}
                  </Tag>
                }
              />
            </Col>
            <Col xs={24} md={12}>
              <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="Total Adiantamentos">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalAdiantamentos)}
                </Descriptions.Item>
                <Descriptions.Item label="Total Comissões Regulares">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalComissaoRegulares)}
                </Descriptions.Item>
              </Descriptions>
            </Col>
          </Row>
        </Card>

        {/* Explicação da Fórmula */}
        <Card
          title={
            <Space>
              <QuestionCircleOutlined style={{ color: '#1890ff' }} />
              <span>Como é Calculada a Reconciliação?</span>
            </Space>
          }
          style={{ marginBottom: 24 }}
        >
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <p style={{ margin: 0 }}>
              A reconciliação ajusta o valor das comissões adiantadas (pagas com <strong>FC = 1.0</strong>)
              para refletir o <strong>FCMP real</strong> calculado após o faturamento.
            </p>
            <Card type="inner" title="Fórmula" size="small">
              <pre style={{ backgroundColor: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                <strong>Ajuste Reconciliação = Comissão Adiantada × (FCMP - 1.0)</strong>
                {'\n\n'}
                Onde:
                {'\n'}- <strong>Comissão Adiantada</strong>: Valor pago antecipadamente (FC fixo = 1.0)
                {'\n'}- <strong>FCMP</strong>: Fator de Correção Médio Ponderado real (calculado após faturamento)
                {'\n'}- <strong>Diferença FC</strong>: (FCMP - 1.0)
              </pre>
            </Card>
            <p style={{ margin: 0, color: '#8c8c8c', fontSize: 13 }}>
              <strong>Interpretação:</strong>
              {'\n'}• Se FCMP {'>'} 1.0 → Ajuste positivo (empresa deve pagar diferença ao colaborador)
              {'\n'}• Se FCMP {'<'} 1.0 → Ajuste negativo (empresa deve descontar diferença do colaborador)
              {'\n'}• Se FCMP = 1.0 → Sem ajuste (comissão adiantada já estava correta)
            </p>
          </Space>
        </Card>

        {/* Tabela de Detalhamento por Colaborador */}
        <Card title="Detalhamento por Colaborador">
          {reconciliacoes.length > 0 ? (
            <Table
              columns={columns}
              dataSource={reconciliacoes}
              rowKey="colaborador"
              pagination={false}
              size="small"
              bordered
              summary={() => (
                <Table.Summary fixed>
                  <Table.Summary.Row style={{ backgroundColor: '#fafafa' }}>
                    <Table.Summary.Cell index={0} colSpan={6}>
                      <strong>TOTAL GERAL</strong>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={6} align="right">
                      <strong style={{
                        fontSize: 16,
                        color: saldoStatus.color === 'green' ? '#52c41a' : saldoStatus.color === 'gold' ? '#faad14' : '#ff4d4f',
                      }}>
                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(saldoTotal)}
                      </strong>
                    </Table.Summary.Cell>
                  </Table.Summary.Row>
                </Table.Summary>
              )}
            />
          ) : (
            <Empty description="Nenhum colaborador com comissão adiantada" />
          )}
        </Card>
      </div>
    );
  };

  // ==================== ABA 5: OBSERVAÇÕES ====================
  const renderObservacoes = () => {
    return (
      <Card>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Observações">
            {processo.OBSERVACOES || (
              <Empty
                description="Nenhuma observação cadastrada para este processo"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  return (
    <>
      <Drawer
        title={
          <Space>
            <FileTextOutlined />
            <span>Detalhes do Processo: {processo.PROCESSO}</span>
          </Space>
        }
        placement="right"
        onClose={onClose}
        visible={visible}
        width="80%"
        bodyStyle={{ paddingBottom: 80 }}
      >
        <Tabs defaultActiveKey="1" size="large">
          <TabPane tab="📋 Visão Geral" key="1">
            {renderVisaoGeral()}
          </TabPane>
          <TabPane tab="👥 Colaboradores & Comissões" key="2">
            {renderColaboradoresComissoes()}
          </TabPane>
          <TabPane tab="📊 Métricas & Status" key="3">
            {renderMetricasStatus()}
          </TabPane>
          <TabPane tab="🔄 Reconciliação" key="4">
            {renderReconciliacao()}
          </TabPane>
          <TabPane tab="📝 Observações" key="5">
            {renderObservacoes()}
          </TabPane>
        </Tabs>
      </Drawer>

      {/* Modal para visualizar JSONs */}
      <JsonViewerModal
        visible={jsonModalVisible}
        onClose={() => setJsonModalVisible(false)}
        data={jsonModalData}
        type={jsonModalType}
      />
    </>
  );
};

export default DrawerDetalhesProcesso;
