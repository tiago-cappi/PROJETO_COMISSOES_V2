import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Table,
  Space,
  Button,
  InputNumber,
  message,
  Typography,
  Tag,
} from 'antd';
import {
  DownloadOutlined,
  ReloadOutlined,
  DollarCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { recebimentoAPI } from '../services/api';
import DetalhesRecebimentoModal from '../components/DetalhesRecebimentoModal';

const { TabPane } = Tabs;
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

const RecebimentosPage = () => {
  const [mesAno, setMesAno] = useState({ mes: new Date().getMonth() || 1, ano: new Date().getFullYear() });
  const [abas, setAbas] = useState([]);
  const [abaAtual, setAbaAtual] = useState(null);
  const [dadosAba, setDadosAba] = useState([]);
  const [colunas, setColunas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  
  // Estado para o modal de detalhes
  const [modalVisible, setModalVisible] = useState(false);
  const [detalhesRecord, setDetalhesRecord] = useState(null);

  useEffect(() => {
    carregarAbas();
  }, [mesAno]);

  useEffect(() => {
    if (abaAtual) {
      carregarDadosAba();
    }
  }, [abaAtual, pagination.current, pagination.pageSize]);

  const carregarAbas = async () => {
    try {
      setLoading(true);
      const response = await recebimentoAPI.listarAbas(mesAno.mes, mesAno.ano);
      setAbas(response.data.abas || []);
      
      if (response.data.abas && response.data.abas.length > 0) {
        setAbaAtual(response.data.abas[0]);
      } else {
        setAbaAtual(null);
        message.warning(`Nenhum arquivo de recebimento encontrado para ${mesAno.mes}/${mesAno.ano}`);
      }
    } catch (error) {
      console.error('Erro ao carregar abas:', error);
      message.error('Erro ao carregar abas de recebimento');
      setAbas([]);
      setAbaAtual(null);
    } finally {
      setLoading(false);
    }
  };

  const carregarDadosAba = async () => {
    if (!abaAtual) return;

    try {
      setLoading(true);
      const response = await recebimentoAPI.lerAba(abaAtual, mesAno.mes, mesAno.ano, {
        page: pagination.current,
        size: pagination.pageSize,
      });

      setDadosAba(response.data.data || []);
      setColunas(response.data.columns || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
      }));
    } catch (error) {
      console.error('Erro ao carregar dados da aba:', error);
      message.error('Erro ao carregar dados');
      setDadosAba([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await recebimentoAPI.baixar(mesAno.mes, mesAno.ano);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Comissoes_Recebimento_${mesAno.mes.toString().padStart(2, '0')}_${mesAno.ano}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('Download iniciado!');
    } catch (error) {
      message.error('Erro ao baixar arquivo');
    }
  };

  const criarColunas = () => {
    if (colunas.length === 0) return [];

    // Mapear colunas dinamicamente
    const colunasBase = colunas.map(col => {
      const isMonetary = ['comissao_calculada', 'valor_pago', 'comissao_adiantada', 'saldo'].includes(col);
      const isPercentage = ['tcmp', 'fcmp', 'fc'].includes(col);
      const isDecimal = ['fcmp'].includes(col) && !isPercentage;

      return {
        title: col.replace(/_/g, ' ').toUpperCase(),
        dataIndex: col,
        key: col,
        width: isMonetary || isPercentage ? 150 : col.length > 20 ? 200 : 150,
        render: (value) => {
          if (value === null || value === undefined || value === '') return '-';
          if (isMonetary) return formatCurrencyBR(value);
          if (isPercentage) return `${(Number(value) * 100).toFixed(2)}%`;
          if (isDecimal) return Number(value).toFixed(2);
          return value;
        },
      };
    });

    // Adicionar coluna de ação "Ver Detalhes" apenas para REGULARES e RECONCILIACOES
    if (abaAtual === 'COMISSOES_REGULARES' || abaAtual === 'RECONCILIACOES') {
      colunasBase.push({
        title: 'Ações',
        key: 'acoes',
        width: 120,
        fixed: 'right',
        render: (_, record) => (
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              setDetalhesRecord(record);
              setModalVisible(true);
            }}
          >
            Ver Detalhes
          </Button>
        ),
      });
    }

    return colunasBase;
  };

  const handleTableChange = (pag) => {
    setPagination({
      ...pagination,
      current: pag.current,
      pageSize: pag.pageSize,
    });
  };

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <DollarCircleOutlined style={{ fontSize: 32, color: '#52c41a' }} />
              <Title level={2} style={{ margin: 0 }}>Comissões por Recebimento</Title>
            </Space>
            <Space>
              <Text>Mês:</Text>
              <InputNumber
                min={1}
                max={12}
                value={mesAno.mes}
                onChange={(val) => setMesAno({ ...mesAno, mes: val || 1 })}
                style={{ width: 80 }}
              />
              <Text>Ano:</Text>
              <InputNumber
                min={2020}
                max={2099}
                value={mesAno.ano}
                onChange={(val) => setMesAno({ ...mesAno, ano: val || new Date().getFullYear() })}
                style={{ width: 100 }}
              />
              <Button icon={<ReloadOutlined />} onClick={carregarAbas}>
                Atualizar
              </Button>
              {abas.length > 0 && (
                <Button icon={<DownloadOutlined />} type="primary" onClick={handleDownload}>
                  Baixar Excel
                </Button>
              )}
            </Space>
          </div>

          {abas.length === 0 ? (
            <Card style={{ textAlign: 'center', padding: 40 }}>
              <Text type="secondary" style={{ fontSize: 16 }}>
                Nenhum arquivo de recebimento encontrado para {mesAno.mes}/{mesAno.ano}
              </Text>
            </Card>
          ) : (
            <Tabs activeKey={abaAtual} onChange={setAbaAtual} type="card">
              {abas.map((aba) => (
                <TabPane
                  tab={aba.replace('COMISSOES_', '').replace(/_/g, ' ')}
                  key={aba}
                >
                  <Table
                    columns={criarColunas()}
                    dataSource={dadosAba}
                    loading={loading}
                    pagination={{
                      current: pagination.current,
                      pageSize: pagination.pageSize,
                      total: pagination.total,
                      showSizeChanger: true,
                      showTotal: (total) => `Total: ${total} registros`,
                      pageSizeOptions: ['10', '20', '50', '100'],
                    }}
                    onChange={handleTableChange}
                    bordered
                    size="small"
                    scroll={{ x: 'max-content' }}
                    rowKey={(record, index) => `${abaAtual}-${index}`}
                  />
                </TabPane>
              ))}
            </Tabs>
          )}
        </Space>
      </Card>

      {/* Modal de Detalhes do Cálculo */}
      {detalhesRecord && (
        <DetalhesRecebimentoModal
          visible={modalVisible}
          onClose={() => {
            setModalVisible(false);
            setDetalhesRecord(null);
          }}
          processo={detalhesRecord.processo}
          colaborador={detalhesRecord.nome_colaborador || detalhesRecord.colaborador}
          mes={mesAno.mes}
          ano={mesAno.ano}
          tipoAba={abaAtual}
        />
      )}
    </div>
  );
};

export default RecebimentosPage;

