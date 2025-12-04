/**
 * MonitoramentoPage.js
 * 
 * Página principal de monitoramento do ciclo de vida dos processos.
 * Exibe o estado atual de todos os processos de recebimento,
 * incluindo valores pagos, saldos, comissões e métricas históricas.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Alert, Typography, Divider } from 'antd';
import {
  DashboardOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { monitorAPI } from '../services/api';
import {
  TabelaEstadoProcessos,
  CardResumoMonitoramento,
} from '../components/monitoramento';

const { Title, Text } = Typography;

/**
 * Página de Monitoramento de Processos.
 */
const MonitoramentoPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    total_processos: 0,
    processos: [],
    resumo: {},
  });
  const [filters, setFilters] = useState({
    statusPagamento: undefined,
    statusReconciliacao: undefined,
    apenasSaldoAberto: false,
  });

  /**
   * Carrega os dados de estado dos processos.
   */
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await monitorAPI.getEstadoProcessos(filters);
      setData(response.data);
    } catch (err) {
      setError(err.message || 'Erro ao carregar dados de monitoramento');
      console.error('[MonitoramentoPage] Erro:', err);
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

  return (
    <div style={{ padding: '0' }}>
      {/* Cabeçalho */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <DashboardOutlined style={{ marginRight: 12 }} />
          Monitoramento de Processos
        </Title>
        <Text type="secondary">
          Acompanhe o ciclo de vida dos processos de recebimento, incluindo valores pagos, 
          saldos em aberto e métricas de comissão (TCMP/FCMP).
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
      <CardResumoMonitoramento
        resumo={data.resumo}
        totalProcessos={data.total_processos}
        loading={loading}
      />

      <Divider />

      {/* Tabela Principal */}
      <Card
        title={
          <span>
            <SyncOutlined spin={loading} style={{ marginRight: 8 }} />
            Estado dos Processos
          </span>
        }
        extra={
          <Text type="secondary">
            {data.total_processos} processo(s) encontrado(s)
          </Text>
        }
      >
        <TabelaEstadoProcessos
          processos={data.processos}
          loading={loading}
          onRefresh={fetchData}
          filters={filters}
          onFiltersChange={handleFiltersChange}
        />
      </Card>
    </div>
  );
};

export default MonitoramentoPage;
