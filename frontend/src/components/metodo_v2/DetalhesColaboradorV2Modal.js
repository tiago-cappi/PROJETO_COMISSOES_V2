import React, { useState, useMemo } from 'react';
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
  Popover,
} from 'antd';
import {
  UserOutlined,
  FolderOutlined,
  FileTextOutlined,
  DollarOutlined,
  ExpandOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  BankOutlined,
  ShopOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

/**
 * Modal de detalhes do colaborador com drill-down em 2 níveis:
 * 
 * Nível 1: Processos agrupados
 * Nível 2: Itens do processo (expandível)
 * 
 * Suporta modo Hierarquia e modo Centro de Custo.
 */
const DetalhesColaboradorV2Modal = ({ 
  visible, 
  onClose, 
  colaborador, 
  detalhes,
  modoCalculo = 'hierarquia', // 'hierarquia' ou 'centro_custo'
}) => {
  // Estado para controlar expansão dos processos
  const [expandedRowKeys, setExpandedRowKeys] = useState([]);

  // Formatar moeda
  const formatCurrency = (value) => {
    if (value == null || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  // Verificar se é modo Centro de Custo
  const isModoCC = modoCalculo === 'centro_custo';

  // ============================================================
  // AGRUPAMENTO PARA MODO CENTRO DE CUSTO (3 níveis)
  // Nível 1: Regras (CC + Fabricante)
  // Nível 2: Processos dentro de cada regra
  // Nível 3: Itens de cada processo
  // ============================================================
  const regrasCCAgrupadas = useMemo(() => {
    if (!isModoCC || !detalhes || detalhes.length === 0) return [];
    
    // Agrupar por chave de regra (CC + Fabricante)
    const porRegra = {};
    
    detalhes.forEach(item => {
      const cc = item.centro_custo || 'SEM_CC';
      const fab = item.fabricante_regra || item.fabricante || 'TODOS';
      const chaveRegra = `${cc}__${fab}`;
      
      if (!porRegra[chaveRegra]) {
        porRegra[chaveRegra] = {
          chave: chaveRegra,
          centro_custo: cc,
          fabricante: fab,
          processos: {},
          faturamento_total: 0,
          comissao_total: 0,
          qtd_itens: 0,
        };
      }
      
      const regra = porRegra[chaveRegra];
      const processo = item.processo || 'SEM_PROCESSO';
      
      if (!regra.processos[processo]) {
        regra.processos[processo] = {
          processo,
          itens: [],
          faturamento_total: 0,
          comissao_total: 0,
        };
      }
      
      // Normalizar item
      const itemNormalizado = {
        ...item,
        faturamento: item.faturamento ?? item.faturamento_item ?? 0,
        faixa_taxa_pct: item.faixa_taxa_pct ?? item.taxa_aplicada ?? 0,
      };
      
      regra.processos[processo].itens.push(itemNormalizado);
      regra.processos[processo].faturamento_total += itemNormalizado.faturamento || 0;
      regra.processos[processo].comissao_total += item.comissao || 0;
      
      regra.faturamento_total += itemNormalizado.faturamento || 0;
      regra.comissao_total += item.comissao || 0;
      regra.qtd_itens += 1;
    });
    
    // Converter processos de objeto para array
    return Object.values(porRegra).map(regra => ({
      ...regra,
      processos: Object.values(regra.processos).sort((a, b) => b.comissao_total - a.comissao_total),
    })).sort((a, b) => b.comissao_total - a.comissao_total);
  }, [detalhes, isModoCC]);

  // ============================================================
  // AGRUPAMENTO PARA MODO HIERARQUIA (2 níveis originais)
  // ============================================================
  // Agrupar detalhes por processo (modo hierarquia)
  const processos = useMemo(() => {
    if (isModoCC || !detalhes || detalhes.length === 0) return [];
    
    // Agrupar itens por processo
    const gruposPorProcesso = {};
    
    detalhes.forEach(item => {
      const processo = item.processo || 'SEM_PROCESSO';
      
      if (!gruposPorProcesso[processo]) {
        gruposPorProcesso[processo] = {
          processo,
          itens: [],
          faturamento_total: 0,
          comissao_total: 0,
        };
      }
      
      // Normalizar campos - modo CC usa nomes diferentes
      const itemNormalizado = {
        ...item,
        // Campo faturamento: pode ser 'faturamento' ou 'faturamento_item'
        faturamento: item.faturamento ?? item.faturamento_item ?? 0,
        // Campo taxa: pode ser 'faixa_taxa_pct' ou 'taxa_aplicada'
        faixa_taxa_pct: item.faixa_taxa_pct ?? item.taxa_aplicada ?? 0,
      };
      
      gruposPorProcesso[processo].itens.push(itemNormalizado);
      gruposPorProcesso[processo].faturamento_total += itemNormalizado.faturamento || 0;
      gruposPorProcesso[processo].comissao_total += item.comissao || 0;
    });
    
    // Converter para array e ordenar por comissão
    return Object.values(gruposPorProcesso)
      .sort((a, b) => b.comissao_total - a.comissao_total);
  }, [detalhes, isModoCC]);

  // Calcular totais gerais
  const totais = useMemo(() => {
    if (!detalhes || detalhes.length === 0) {
      return { faturamento: 0, comissao: 0, processos: 0, itens: 0, taxaMedia: 0, regras: 0 };
    }
    
    // Normalizar faturamento (pode ser 'faturamento' ou 'faturamento_item')
    const faturamentoTotal = detalhes.reduce((sum, d) => {
      const fat = d.faturamento ?? d.faturamento_item ?? 0;
      return sum + fat;
    }, 0);
    
    const comissaoTotal = detalhes.reduce((sum, d) => sum + (d.comissao || 0), 0);

    // Taxa média aplicada (ponderada por faturamento): soma(fat * taxa) / soma(fat)
    const somaFatTaxa = detalhes.reduce((sum, d) => {
      const fat = d.faturamento ?? d.faturamento_item ?? 0;
      const taxa = d.faixa_taxa_pct ?? d.taxa_aplicada ?? 0;
      return sum + (fat * taxa);
    }, 0);
    const taxaMedia = faturamentoTotal > 0 ? (somaFatTaxa / faturamentoTotal) : 0;
    
    // Contar processos e regras
    const processosCount = isModoCC 
      ? regrasCCAgrupadas.reduce((sum, r) => sum + r.processos.length, 0)
      : processos.length;
    
    return {
      faturamento: faturamentoTotal,
      comissao: comissaoTotal,
      processos: processosCount,
      itens: detalhes.length,
      taxaMedia,
      regras: regrasCCAgrupadas.length,
    };
  }, [detalhes, processos, regrasCCAgrupadas, isModoCC]);

  // Colunas da tabela de processos (Nível 1)
  const columnsProcessos = [
    {
      title: 'Processo',
      dataIndex: 'processo',
      key: 'processo',
      render: (text) => (
        <Space>
          <FolderOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text || '-'}</Text>
        </Space>
      ),
    },
    {
      title: 'Qtd. Itens',
      dataIndex: 'itens',
      key: 'qtd_itens',
      align: 'center',
      width: 100,
      render: (itens) => (
        <Tag color="blue">{itens?.length || 0}</Tag>
      ),
    },
    {
      title: 'Faturamento',
      dataIndex: 'faturamento_total',
      key: 'faturamento_total',
      align: 'right',
      width: 150,
      sorter: (a, b) => a.faturamento_total - b.faturamento_total,
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Comissão',
      dataIndex: 'comissao_total',
      key: 'comissao_total',
      align: 'right',
      width: 150,
      defaultSortOrder: 'descend',
      sorter: (a, b) => a.comissao_total - b.comissao_total,
      render: (value) => (
        <Text strong style={{ color: '#52c41a' }}>
          {formatCurrency(value)}
        </Text>
      ),
    },
  ];

  // Colunas da tabela de itens (Nível 2 - expansão)
  // Colunas para modo HIERARQUIA
  const columnsItensHierarquia = [
    {
      title: 'Linha',
      dataIndex: 'linha',
      key: 'linha',
      width: 100,
      render: (text) => <Tag color="purple">{text || '-'}</Tag>,
    },
    {
      title: 'Grupo',
      dataIndex: 'grupo',
      key: 'grupo',
      width: 100,
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
      width: 90,
      render: (text) => (
        <Tag color={text === 'REVENDA' ? 'cyan' : 'orange'} style={{ fontSize: 10 }}>
          {text || '-'}
        </Tag>
      ),
    },
    {
      title: 'Faturamento',
      dataIndex: 'faturamento',
      key: 'faturamento',
      align: 'right',
      width: 110,
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Taxa',
      dataIndex: 'faixa_taxa_pct',
      key: 'faixa_taxa_pct',
      align: 'center',
      width: 70,
      render: (value) => (
        <Tag color="blue">{value ? `${value}%` : '-'}</Tag>
      ),
    },
    {
      title: 'Comissão',
      dataIndex: 'comissao',
      key: 'comissao',
      align: 'right',
      width: 100,
      render: (value) => (
        <Text type="success" strong>{formatCurrency(value)}</Text>
      ),
    },
    {
      title: 'Faixa/Regra',
      key: 'detalhes_faixa',
      width: 120,
      render: (_, record) => {
        const faixaDesc = record.faixa_descricao;
        const regraLinha = record.regra_linha;
        const regraGrupo = record.regra_grupo;
        const fatorSplit = record.fator_split;
        
        const content = (
          <div style={{ maxWidth: 350 }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Regra Aplicada">
                <Text code>
                  {regraLinha || '*'} / {regraGrupo || '*'}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Faixa de Faturamento">
                <Text>{faixaDesc || 'Não definida'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Taxa Comissão">
                <Tag color="green">{record.faixa_taxa_pct || 0}%</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Fator Split">
                <Tag color="orange">{((fatorSplit || 1) * 100).toFixed(0)}%</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Cálculo">
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {formatCurrency(record.faturamento)} × {record.faixa_taxa_pct || 0}% × {((fatorSplit || 1) * 100).toFixed(0)}% = {formatCurrency(record.comissao)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
            {record.motivo && (
              <div style={{ marginTop: 8, padding: 8, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                  {record.motivo}
                </Text>
              </div>
            )}
          </div>
        );
        
        return (
          <Popover 
            content={content} 
            title="Detalhes do Cálculo"
            trigger="click"
            placement="left"
          >
            <Tooltip title="Clique para ver detalhes da faixa/regra">
              <Tag 
                color="geekblue" 
                style={{ cursor: 'pointer' }}
                icon={<InfoCircleOutlined />}
              >
                Ver
              </Tag>
            </Tooltip>
          </Popover>
        );
      },
    },
  ];

  // Colunas para modo CENTRO DE CUSTO
  const columnsItensCC = [
    {
      title: 'Descrição do Item',
      dataIndex: 'descricao_produto',
      key: 'descricao_produto',
      width: 260,
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text || '-'}>
          <Text>{text || '-'}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Faturamento Item',
      dataIndex: 'faturamento',
      key: 'faturamento',
      align: 'right',
      width: 130,
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Taxa',
      dataIndex: 'faixa_taxa_pct',
      key: 'faixa_taxa_pct',
      align: 'center',
      width: 70,
      render: (value) => (
        <Tag color="green">{value ? `${value}%` : '-'}</Tag>
      ),
    },
    {
      title: 'Comissão',
      dataIndex: 'comissao',
      key: 'comissao',
      align: 'right',
      width: 110,
      render: (value) => (
        <Text type="success" strong>{formatCurrency(value)}</Text>
      ),
    },
    {
      title: 'Detalhes',
      key: 'detalhes_cc',
      width: 100,
      render: (_, record) => {
        const faixaDesc = record.faixa_descricao;
        const fatorSplit = record.fator_split;
        const fabricanteRegra = record.fabricante_regra || record.fabricante || 'TODOS';
        
        const content = (
          <div style={{ maxWidth: 380 }}>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Fabricante da Regra">
                <Space>
                  <ShopOutlined style={{ color: '#722ed1' }} />
                  <Tag color="purple">{fabricanteRegra === 'TODOS' ? 'Todos' : fabricanteRegra}</Tag>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Faixa Aplicada">
                <Text>{faixaDesc || 'Não definida'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Taxa Comissão">
                <Tag color="green">{record.faixa_taxa_pct || 0}%</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Fator Split">
                <Tag color="orange">{((fatorSplit || 1) * 100).toFixed(0)}%</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Cálculo">
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {formatCurrency(record.faturamento)} × {record.faixa_taxa_pct || 0}% × {((fatorSplit || 1) * 100).toFixed(0)}% = {formatCurrency(record.comissao)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
            {record.motivo && (
              <div style={{ marginTop: 8, padding: 8, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                  {record.motivo}
                </Text>
              </div>
            )}
          </div>
        );
        
        return (
          <Popover 
            content={content} 
            title="Detalhes do Cálculo (Centro de Custo)"
            trigger="click"
            placement="left"
          >
            <Tooltip title="Clique para ver detalhes">
              <Tag 
                color="geekblue" 
                style={{ cursor: 'pointer' }}
                icon={<InfoCircleOutlined />}
              >
                Ver
              </Tag>
            </Tooltip>
          </Popover>
        );
      },
    },
  ];

  // Seleciona colunas de acordo com o modo
  const columnsItens = isModoCC ? columnsItensCC : columnsItensHierarquia;

  // Renderizar tabela expandida de itens
  const expandedRowRender = (record) => {
    return (
      <Table
        columns={columnsItens}
        dataSource={record.itens}
        rowKey={(item, idx) => `${record.processo}_item_${idx}`}
        pagination={false}
        size="small"
        style={{ 
          margin: '0 -8px',
          backgroundColor: '#fafafa',
        }}
      />
    );
  };

  // Handler para expansão
  const handleExpand = (expanded, record) => {
    setExpandedRowKeys(expanded ? [record.processo] : []);
  };

  return (
    <Modal
      title={
        <Space>
          <UserOutlined />
          <span>Detalhes - {colaborador?.colaborador || 'Colaborador'}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1100}
      style={{ top: 20 }}
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
          <Descriptions.Item label="Taxa Média">
            {totais.taxaMedia.toFixed(2)}%
          </Descriptions.Item>
          <Descriptions.Item label="Qtd. Itens">
            <Tag>{totais.itens || 0}</Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Cards de estatísticas */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {/* Para modo CC: mostrar Regras, para Hierarquia: mostrar Processos */}
        {isModoCC ? (
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="Regras (CC+Fab)"
                value={totais.regras}
                prefix={<ApartmentOutlined />}
              />
            </Card>
          </Col>
        ) : (
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="Processos"
                value={totais.processos}
                prefix={<FolderOutlined />}
              />
            </Card>
          </Col>
        )}
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Itens"
              value={totais.itens}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Faturamento"
              value={totais.faturamento}
              precision={2}
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
      </Row>

      {/* ============================================================ */}
      {/* MODO CENTRO DE CUSTO: 3 níveis (Regras → Processos → Itens) */}
      {/* ============================================================ */}
      {isModoCC ? (
        <>
          <Divider orientation="left">
            <Space>
              <ApartmentOutlined />
              Regras por Centro de Custo + Fabricante
            </Space>
          </Divider>

          {regrasCCAgrupadas.length > 0 ? (
            <Table
              columns={[
                {
                  title: 'Centro de Custo',
                  dataIndex: 'centro_custo',
                  key: 'centro_custo',
                  width: 150,
                  render: (cc) => (
                    <Space>
                      <BankOutlined style={{ color: '#1890ff' }} />
                      <Tag color="blue">{cc}</Tag>
                    </Space>
                  ),
                },
                {
                  title: 'Fabricante',
                  dataIndex: 'fabricante',
                  key: 'fabricante',
                  width: 150,
                  render: (fab) => (
                    <Space>
                      <ShopOutlined style={{ color: '#722ed1' }} />
                      <Tag color="purple">{fab === 'TODOS' ? 'Todos' : fab}</Tag>
                    </Space>
                  ),
                },
                {
                  title: 'Qtd. Itens',
                  dataIndex: 'qtd_itens',
                  key: 'qtd_itens',
                  width: 100,
                  align: 'center',
                  render: (qtd) => <Tag>{qtd}</Tag>,
                },
                {
                  title: 'Fat. Total CC',
                  dataIndex: 'faturamento_total',
                  key: 'faturamento_total',
                  width: 150,
                  align: 'right',
                  render: (val) => formatCurrency(val),
                },
                {
                  title: 'Comissão',
                  dataIndex: 'comissao_total',
                  key: 'comissao_total',
                  width: 150,
                  align: 'right',
                  render: (val) => (
                    <Text strong style={{ color: '#3f8600' }}>
                      {formatCurrency(val)}
                    </Text>
                  ),
                },
                {
                  title: 'Taxa Média',
                  key: 'taxa_media',
                  width: 100,
                  align: 'center',
                  render: (_, record) => {
                    const taxa = record.faturamento_total > 0 
                      ? (record.comissao_total / record.faturamento_total) * 100 
                      : 0;
                    return <Tag color="green">{taxa.toFixed(2)}%</Tag>;
                  },
                },
              ]}
              dataSource={regrasCCAgrupadas}
              rowKey="chave"
              expandable={{
                expandedRowRender: (regraRecord) => (
                  <div style={{ margin: '8px 0', padding: '0 24px' }}>
                    <Text strong style={{ marginBottom: 8, display: 'block' }}>
                      <FolderOutlined /> Processos desta Regra:
                    </Text>
                    <Table
                      columns={columnsProcessos}
                      dataSource={regraRecord.processos}
                      rowKey="processo"
                      size="small"
                      expandable={{
                        expandedRowRender,
                        rowExpandable: (record) => record.itens?.length > 0,
                      }}
                      pagination={false}
                      style={{ backgroundColor: '#fafafa' }}
                    />
                  </div>
                ),
                rowExpandable: (record) => record.processos?.length > 0,
              }}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total: ${total} regras`,
              }}
              size="middle"
            />
          ) : (
            <Empty
              description="Nenhum detalhe encontrado"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </>
      ) : (
        <>
          {/* ============================================================ */}
          {/* MODO HIERARQUIA: 2 níveis (Processos → Itens) */}
          {/* ============================================================ */}
          <Divider orientation="left">
            <Space>
              <ExpandOutlined />
              Processos (clique para expandir)
            </Space>
          </Divider>

          {processos.length > 0 ? (
            <Table
              columns={columnsProcessos}
              dataSource={processos}
              rowKey="processo"
              expandable={{
                expandedRowRender,
                expandedRowKeys,
                onExpand: handleExpand,
                rowExpandable: (record) => record.itens?.length > 0,
              }}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total: ${total} processos`,
              }}
              size="middle"
            />
          ) : (
            <Empty
              description="Nenhum detalhe encontrado"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </>
      )}
    </Modal>
  );
};

export default DetalhesColaboradorV2Modal;
