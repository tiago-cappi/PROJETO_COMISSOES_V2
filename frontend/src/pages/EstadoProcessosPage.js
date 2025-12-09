/**
 * EstadoProcessosPage.js
 * 
 * Página de visualização do Estado dos Processos de Recebimento.
 * Utiliza pattern Master-Detail: tabela compacta + drawer lateral com detalhes.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Alert, Typography, Divider, Statistic, Row, Col } from 'antd';
import {
  DatabaseOutlined,
  SyncOutlined,
  FileExcelOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { monitorAPI } from '../services/api';
import TabelaEstadoCompacta from '../components/estado/TabelaEstadoCompacta';
import DrawerDetalhesProcesso from '../components/estado/DrawerDetalhesProcesso';

const { Title, Text } = Typography;

/**
 * Página de Estado de Processos (Pattern Master-Detail).
 */
const EstadoProcessosPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    total_processos: 0,
    colunas: [],
    dados: [],
  });
  const [filters, setFilters] = useState({
    statusProcesso: undefined,
    statusPagamento: undefined,
    statusCalculo: undefined,
  });
  
  // Estados para controle do Drawer
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [processoSelecionado, setProcessoSelecionado] = useState(null);

  /**
   * Carrega os dados de estado dos processos.
   */
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await monitorAPI.getEstadoRaw(filters);
      setData(response.data);
    } catch (err) {
      setError(err.message || 'Erro ao carregar dados de estado');
      console.error('[EstadoProcessosPage] Erro:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Carregar dados ao montar e quando os filtros mudarem
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  /**
   * Handler para mudança de filtros.
   */
  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
  };

  /**
   * Handler para abrir o drawer de detalhes de um processo.
   */
  const handleVerDetalhes = (processo) => {
    setProcessoSelecionado(processo);
    setDrawerVisible(true);
  };

  /**
   * Handler para fechar o drawer.
   */
  const handleCloseDrawer = () => {
    setDrawerVisible(false);
    setProcessoSelecionado(null);
  };

  /**
   * Calcula estatísticas resumidas dos dados.
   */
  const calcularResumo = () => {
    if (!data.dados || data.dados.length === 0) {
      return {
        totalProcessos: 0,
        faturados: 0,
        pendentes: 0,
        calculados: 0,
        parciais: 0,
      };
    }

    return {
      totalProcessos: data.dados.length,
      faturados: data.dados.filter(d => d.STATUS_PROCESSO === 'FATURADO').length,
      pendentes: data.dados.filter(d => d.STATUS_PROCESSO === 'PENDENTE').length,
      calculados: data.dados.filter(d => d.STATUS_CALCULO_MEDIAS === 'CALCULADO').length,
      parciais: data.dados.filter(d => d.STATUS_CALCULO_MEDIAS === 'PARCIAL').length,
    };
  };

  const resumo = calcularResumo();

  return (
    <div style={{ padding: '0' }}>
      {/* Cabeçalho */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ marginRight: 12 }} />
          Estado dos Processos de Recebimento
        </Title>
        <Text type="secondary">
          Visualização do arquivo <code>Estado_Processos_Recebimento</code>. 
          Clique em "Detalhes" para ver todas as informações de um processo específico.
        </Text>
      </div>

      {/* Alerta de Erro */}
      {error && (
        <Alert
          type="error"
          message="Erro ao carregar dados"
          description={error}
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Cards de Resumo */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Total de Processos"
              value={resumo.totalProcessos}
              prefix={<FileExcelOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Faturados"
              value={resumo.faturados}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Pendentes"
              value={resumo.pendentes}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Métricas Calculadas"
              value={resumo.calculados}
              suffix={`/ ${resumo.calculados + resumo.parciais}`}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Divider />

      {/* Tabela Compacta Principal */}
      <Card
        title={
          <span>
            <SyncOutlined spin={loading} style={{ marginRight: 8 }} />
            Lista de Processos
          </span>
        }
        extra={
          <Text type="secondary">
            {data.total_processos} processo(s)
          </Text>
        }
      >
        <TabelaEstadoCompacta
          dados={data.dados}
          loading={loading}
          onVerDetalhes={handleVerDetalhes}
        />
      </Card>

      {/* Drawer de Detalhes */}
      <DrawerDetalhesProcesso
        visible={drawerVisible}
        onClose={handleCloseDrawer}
        processo={processoSelecionado}
      />
    </div>
  );
};

export default EstadoProcessosPage;
