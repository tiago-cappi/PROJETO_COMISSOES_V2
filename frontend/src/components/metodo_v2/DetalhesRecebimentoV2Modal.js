import React, { useMemo } from 'react';
import {
  Modal,
  Table,
  Typography,
  Tag,
  Space,
  Card,
  Statistic,
  Row,
  Col,
  Descriptions,
  Divider,
  Empty,
  Tooltip,
} from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  DollarOutlined,
  BankOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

/**
 * Modal de detalhes de recebimento por colaborador.
 *
 * Exibe a lista de documentos (adiantamentos/pagamentos regulares) de um
 * colaborador, diferenciando o tipo de comissão com Tags coloridas.
 *
 * Props:
 * - visible: boolean — controla visibilidade do modal
 * - onClose: () => void — callback para fechar
 * - colaborador: object — linha agregada do resumoRecebimentoAgregado
 *   (contém .documentos[], .colaborador, .cargo, .valor_base_total,
 *    .comissao_total, .taxa_media_pct, .qtd_docs)
 */
const DetalhesRecebimentoV2Modal = ({ visible, onClose, colaborador }) => {
  // Formatar moeda
  const formatCurrency = (value) => {
    if (value == null || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  // Mapear tipo de cálculo para label/cor amigável
  const tipoTag = (tipo) => {
    if (!tipo) return <Tag>-</Tag>;
    const upper = tipo.toUpperCase();
    if (upper.includes('ADIANTAMENTO')) {
      return <Tag color="orange">Adiantamento</Tag>;
    }
    if (upper.includes('RECEBIMENTO') || upper.includes('REGULAR')) {
      return <Tag color="green">Pagamento Regular</Tag>;
    }
    return <Tag>{tipo}</Tag>;
  };

  // Documentos do colaborador selecionado
  const documentos = useMemo(() => {
    if (!colaborador?.documentos) return [];
    return colaborador.documentos.map((d, idx) => ({ ...d, _idx: idx }));
  }, [colaborador]);

  // Totais para stat cards
  const totais = useMemo(() => {
    if (!colaborador) {
      return { valorBase: 0, comissao: 0, taxaMedia: 0, qtd: 0 };
    }
    return {
      valorBase: colaborador.valor_base_total || 0,
      comissao: colaborador.comissao_total || 0,
      taxaMedia: colaborador.taxa_media_pct || 0,
      qtd: colaborador.qtd_docs || 0,
    };
  }, [colaborador]);

  // Contagem por tipo
  const contagemPorTipo = useMemo(() => {
    const counts = { adiantamento: 0, regular: 0 };
    (colaborador?.documentos || []).forEach((d) => {
      const tipo = (d['Tipo Cálculo'] || '').toUpperCase();
      if (tipo.includes('ADIANTAMENTO')) {
        counts.adiantamento += 1;
      } else {
        counts.regular += 1;
      }
    });
    return counts;
  }, [colaborador]);

  // Colunas da tabela de documentos
  const columns = useMemo(
    () => [
      {
        title: 'Documento',
        dataIndex: 'Documento',
        key: 'documento',
        width: 140,
        render: (text) => <Text strong>{text || '-'}</Text>,
      },
      {
        title: 'Doc. Normalizado',
        dataIndex: 'Documento Normalizado',
        key: 'doc_norm',
        width: 160,
        ellipsis: true,
      },
      {
        title: 'Valor Base',
        dataIndex: 'Valor Base',
        key: 'valor_base',
        align: 'right',
        width: 130,
        sorter: (a, b) => (Number(a['Valor Base']) || 0) - (Number(b['Valor Base']) || 0),
        render: (v) => formatCurrency(v || 0),
      },
      {
        title: 'Taxa (%)',
        key: 'taxa',
        align: 'center',
        width: 80,
        render: (_, record) => {
          const taxa = record['Taxa (%)'] ?? record['Percentual Aplicado'] ?? 0;
          return <Tag color="blue">{Number(taxa).toFixed(2)}%</Tag>;
        },
      },
      {
        title: 'Comissão',
        key: 'comissao',
        align: 'right',
        width: 130,
        defaultSortOrder: 'descend',
        sorter: (a, b) => {
          const ca = Number(a['Comissão'] || a['Comissão Calculada'] || 0);
          const cb = Number(b['Comissão'] || b['Comissão Calculada'] || 0);
          return ca - cb;
        },
        render: (_, record) => {
          const val = Number(record['Comissão'] || record['Comissão Calculada'] || 0);
          return (
            <Text strong style={{ color: '#52c41a' }}>
              {formatCurrency(val)}
            </Text>
          );
        },
      },
      {
        title: 'Tipo',
        dataIndex: 'Tipo Cálculo',
        key: 'tipo',
        width: 160,
        filters: [
          { text: 'Adiantamento', value: 'ADIANTAMENTO' },
          { text: 'Pagamento Regular', value: 'REGULAR' },
        ],
        onFilter: (value, record) => {
          const tipo = (record['Tipo Cálculo'] || '').toUpperCase();
          if (value === 'ADIANTAMENTO') return tipo.includes('ADIANTAMENTO');
          return tipo.includes('RECEBIMENTO') || tipo.includes('REGULAR');
        },
        render: (tipo) => tipoTag(tipo),
      },
      {
        title: 'Regra',
        dataIndex: 'Regra Utilizada',
        key: 'regra',
        width: 130,
        ellipsis: true,
        render: (text) =>
          text ? (
            <Tooltip title={text}>
              <Tag color="geekblue" icon={<InfoCircleOutlined />}>
                {text}
              </Tag>
            </Tooltip>
          ) : (
            <Text type="secondary">-</Text>
          ),
      },
    ],
    []
  );

  return (
    <Modal
      title={
        <Space>
          <UserOutlined />
          <span>Detalhes Recebimento - {colaborador?.colaborador || 'Colaborador'}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1100}
      style={{ top: 20 }}
      destroyOnClose
    >
      {/* Cabeçalho com informações do colaborador */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 4 }} size="small">
          <Descriptions.Item label="Colaborador">
            <Text strong>{colaborador?.colaborador}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Cargo">
            <Tag color="blue">{colaborador?.cargo || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Adiantamentos">
            <Tag color="orange">{contagemPorTipo.adiantamento}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Pagamentos Regulares">
            <Tag color="green">{contagemPorTipo.regular}</Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Cards de estatísticas */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Documentos"
              value={totais.qtd}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Valor Base Total"
              value={totais.valorBase}
              precision={2}
              prefix={<BankOutlined />}
              formatter={(value) => formatCurrency(value)}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Comissão Total"
              value={totais.comissao}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
              prefix={<DollarOutlined />}
              formatter={(value) => formatCurrency(value)}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Taxa Média"
              value={`${totais.taxaMedia.toFixed(2)}%`}
            />
          </Card>
        </Col>
      </Row>

      {/* Tabela de documentos */}
      <Divider orientation="left">
        <Space>
          <FileTextOutlined />
          Documentos de Recebimento
        </Space>
      </Divider>

      {documentos.length > 0 ? (
        <Table
          columns={columns}
          dataSource={documentos}
          rowKey={(record) => `doc_${record._idx}`}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total: ${total} documentos`,
          }}
          size="small"
          summary={(pageData) => {
            const totalVB = pageData.reduce(
              (sum, r) => sum + (Number(r['Valor Base']) || 0),
              0
            );
            const totalComissao = pageData.reduce(
              (sum, r) => sum + (Number(r['Comissão'] || r['Comissão Calculada'] || 0) || 0),
              0
            );
            return (
              <Table.Summary fixed>
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={2}>
                    <Text strong>Total da Página</Text>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={2} align="right">
                    <Text strong>{formatCurrency(totalVB)}</Text>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={3} />
                  <Table.Summary.Cell index={4} align="right">
                    <Text strong style={{ color: '#52c41a' }}>
                      {formatCurrency(totalComissao)}
                    </Text>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={5} colSpan={2} />
                </Table.Summary.Row>
              </Table.Summary>
            );
          }}
        />
      ) : (
        <Empty
          description="Nenhum documento encontrado"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}
    </Modal>
  );
};

export default DetalhesRecebimentoV2Modal;
