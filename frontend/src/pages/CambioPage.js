import React, { useState, useEffect } from 'react';
import { Card, Table, Select, Tag, Typography, Space, Alert, Spin } from 'antd';
import { DollarOutlined, ReloadOutlined } from '@ant-design/icons';
import { cambioAPI } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const CambioPage = () => {
  const [dados, setDados] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [anoSelecionado, setAnoSelecionado] = useState(null);
  const [moedaSelecionada, setMoedaSelecionada] = useState(null);

  useEffect(() => {
    carregarTaxas();
  }, []);

  const carregarTaxas = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await cambioAPI.getTaxas();
      setDados(response.data);
      
      // Selecionar ano mais recente automaticamente
      const anos = Object.keys(response.data.taxas || {});
      if (anos.length > 0) {
        const anoRecente = Math.max(...anos.map(Number));
        setAnoSelecionado(anoRecente.toString());
      }
      
      // Selecionar primeira moeda automaticamente
      if (response.data.metadata?.moedas_disponiveis?.length > 0) {
        setMoedaSelecionada(response.data.metadata.moedas_disponiveis[0]);
      }
    } catch (err) {
      console.error('Erro ao carregar taxas:', err);
      setError(err.message || 'Erro ao carregar taxas de câmbio');
    } finally {
      setLoading(false);
    }
  };

  const prepararDadosTabela = () => {
    if (!dados || !anoSelecionado || !moedaSelecionada) {
      return [];
    }

    const taxasAno = dados.taxas[anoSelecionado];
    if (!taxasAno || !taxasAno[moedaSelecionada]) {
      return [];
    }

    const taxasMoeda = taxasAno[moedaSelecionada];
    
    return Object.entries(taxasMoeda).map(([mes, info]) => ({
      key: `${anoSelecionado}-${mes}`,
      mes: parseInt(mes),
      mesNome: new Date(2000, parseInt(mes) - 1).toLocaleString('pt-BR', { month: 'long' }),
      ano: anoSelecionado,
      moeda: moedaSelecionada,
      taxa_media: info.taxa_media,
      fonte: info.fonte,
      fallback: info.fallback,
      observacao: info.observacao,
      dias_utilizados: info.dias_utilizados,
      data_atualizacao: info.data_atualizacao ? new Date(info.data_atualizacao).toLocaleString('pt-BR') : '-',
    })).sort((a, b) => a.mes - b.mes);
  };

  const columns = [
    {
      title: 'Mês',
      dataIndex: 'mesNome',
      key: 'mesNome',
      width: 120,
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          <Text type="secondary">({record.mes}/{record.ano})</Text>
        </Space>
      ),
    },
    {
      title: 'Taxa Média',
      dataIndex: 'taxa_media',
      key: 'taxa_media',
      width: 130,
      render: (value) => (
        <Text strong style={{ color: '#1890ff', fontSize: 16 }}>
          {value ? value.toFixed(6) : '-'}
        </Text>
      ),
    },
    {
      title: 'Fonte',
      dataIndex: 'fonte',
      key: 'fonte',
      width: 150,
      render: (text, record) => (
        <Space direction="vertical" size="small">
          <Text>{text}</Text>
          {record.fallback && (
            <Tag color="warning">Fallback</Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Dias Utilizados',
      dataIndex: 'dias_utilizados',
      key: 'dias_utilizados',
      width: 120,
      align: 'center',
    },
    {
      title: 'Última Atualização',
      dataIndex: 'data_atualizacao',
      key: 'data_atualizacao',
      width: 180,
    },
    {
      title: 'Observações',
      dataIndex: 'observacao',
      key: 'observacao',
      render: (text) => text ? (
        <Text type="warning" style={{ fontSize: 12 }}>{text}</Text>
      ) : '-',
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
        <Title level={4} style={{ marginTop: 20 }}>Carregando taxas de câmbio...</Title>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Erro ao Carregar Taxas"
          description={error}
          type="error"
          showIcon
        />
      </Card>
    );
  }

  const anosDisponiveis = dados?.taxas ? Object.keys(dados.taxas).sort((a, b) => b - a) : [];
  const moedasDisponiveis = dados?.metadata?.moedas_disponiveis || [];
  const dadosTabela = prepararDadosTabela();

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <DollarOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              <Title level={2} style={{ margin: 0 }}>Taxas de Câmbio (EUR)</Title>
            </Space>
            <ReloadOutlined
              style={{ fontSize: 24, cursor: 'pointer', color: '#1890ff' }}
              onClick={carregarTaxas}
            />
          </div>

          {dados?.metadata && (
            <Alert
              message="Informações do Sistema"
              description={
                <Space direction="vertical">
                  <Text>Última atualização: {new Date(dados.metadata.ultima_atualizacao).toLocaleString('pt-BR')}</Text>
                  <Text>Ano atual: {dados.metadata.ano_atual} | Mês atual: {dados.metadata.mes_atual}</Text>
                  <Text>Moedas disponíveis: {moedasDisponiveis.join(', ')}</Text>
                </Space>
              }
              type="info"
              showIcon
            />
          )}

          <Space size="large">
            <Space direction="vertical">
              <Text strong>Ano:</Text>
              <Select
                value={anoSelecionado}
                onChange={setAnoSelecionado}
                style={{ width: 120 }}
              >
                {anosDisponiveis.map((ano) => (
                  <Option key={ano} value={ano}>{ano}</Option>
                ))}
              </Select>
            </Space>

            <Space direction="vertical">
              <Text strong>Moeda:</Text>
              <Select
                value={moedaSelecionada}
                onChange={setMoedaSelecionada}
                style={{ width: 120 }}
              >
                {moedasDisponiveis.map((moeda) => (
                  <Option key={moeda} value={moeda}>{moeda}</Option>
                ))}
              </Select>
            </Space>
          </Space>

          <Table
            columns={columns}
            dataSource={dadosTabela}
            pagination={{
              pageSize: 12,
              showSizeChanger: false,
              showTotal: (total) => `Total: ${total} mês(es)`,
            }}
            bordered
            size="middle"
          />
        </Space>
      </Card>
    </div>
  );
};

export default CambioPage;

