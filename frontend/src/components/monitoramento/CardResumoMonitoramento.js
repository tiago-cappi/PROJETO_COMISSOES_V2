/**
 * CardResumoMonitoramento.js
 * 
 * Componente que exibe cards de resumo com métricas agregadas
 * sobre os processos de recebimento.
 */

import React from 'react';
import { Card, Row, Col, Statistic, Tag } from 'antd';
import {
  DollarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons';

/**
 * Formata valor monetário para exibição.
 */
const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
  }).format(value);
};

/**
 * Cards de resumo para o monitoramento de processos.
 * 
 * @param {Object} props
 * @param {Object} props.resumo - Dados de resumo da API
 * @param {number} props.totalProcessos - Total de processos
 * @param {boolean} props.loading - Estado de carregamento
 */
const CardResumoMonitoramento = ({ resumo = {}, totalProcessos = 0, loading = false }) => {
  const {
    total_valor_processos = 0,
    total_pago = 0,
    total_saldo_aberto = 0,
    total_comissoes = 0,
    por_status_pagamento = {},
    por_status_reconciliacao = {},
  } = resumo;

  const statusPagColors = {
    COMPLETO: 'green',
    PARCIAL: 'blue',
    PENDENTE: 'orange',
  };

  const statusReconColors = {
    CONCLUIDA: 'green',
    PENDENTE: 'orange',
  };

  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      {/* Total de Processos */}
      <Col xs={24} sm={12} md={6}>
        <Card size="small" loading={loading}>
          <Statistic
            title="Total de Processos"
            value={totalProcessos}
            prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
          />
        </Card>
      </Col>

      {/* Valor Total dos Processos */}
      <Col xs={24} sm={12} md={6}>
        <Card size="small" loading={loading}>
          <Statistic
            title="Valor Total"
            value={total_valor_processos}
            precision={2}
            prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
            formatter={(value) => formatCurrency(value)}
          />
        </Card>
      </Col>

      {/* Total Pago */}
      <Col xs={24} sm={12} md={6}>
        <Card size="small" loading={loading}>
          <Statistic
            title="Total Pago"
            value={total_pago}
            precision={2}
            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            formatter={(value) => formatCurrency(value)}
          />
        </Card>
      </Col>

      {/* Saldo em Aberto */}
      <Col xs={24} sm={12} md={6}>
        <Card size="small" loading={loading}>
          <Statistic
            title="Saldo em Aberto"
            value={total_saldo_aberto}
            precision={2}
            prefix={<ClockCircleOutlined style={{ color: total_saldo_aberto > 0 ? '#faad14' : '#52c41a' }} />}
            formatter={(value) => formatCurrency(value)}
            valueStyle={{ color: total_saldo_aberto > 0 ? '#faad14' : '#52c41a' }}
          />
        </Card>
      </Col>

      {/* Comissões Acumuladas */}
      <Col xs={24} sm={12} md={6}>
        <Card size="small" loading={loading}>
          <Statistic
            title="Comissões Acumuladas"
            value={total_comissoes}
            precision={4}
            prefix={<DollarOutlined style={{ color: '#722ed1' }} />}
            formatter={(value) => formatCurrency(value)}
          />
        </Card>
      </Col>

      {/* Status de Pagamento */}
      <Col xs={24} sm={12} md={9}>
        <Card size="small" title="Por Status de Pagamento" loading={loading}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(por_status_pagamento).map(([status, count]) => (
              <Tag
                key={status}
                color={statusPagColors[status] || 'default'}
                style={{ fontSize: 13 }}
              >
                {status}: {count}
              </Tag>
            ))}
            {Object.keys(por_status_pagamento).length === 0 && (
              <span style={{ color: '#999' }}>Nenhum dado</span>
            )}
          </div>
        </Card>
      </Col>

      {/* Status de Reconciliação */}
      <Col xs={24} sm={12} md={9}>
        <Card size="small" title="Por Status de Reconciliação" loading={loading}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(por_status_reconciliacao).map(([status, count]) => (
              <Tag
                key={status}
                color={statusReconColors[status] || 'default'}
                style={{ fontSize: 13 }}
              >
                {status}: {count}
              </Tag>
            ))}
            {Object.keys(por_status_reconciliacao).length === 0 && (
              <span style={{ color: '#999' }}>Nenhum dado</span>
            )}
          </div>
        </Card>
      </Col>
    </Row>
  );
};

export default CardResumoMonitoramento;
