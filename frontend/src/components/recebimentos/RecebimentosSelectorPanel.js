import React from 'react';
import { Card, Row, Col, Select, Button, Statistic, Space } from 'antd';
import { ReloadOutlined, DollarOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Option } = Select;

/**
 * Painel de seleção de mês/ano e cards de resumo dos pagamentos.
 */
const RecebimentosSelectorPanel = ({
  mes,
  ano,
  onMesChange,
  onAnoChange,
  onCarregar,
  totais,
  loading,
}) => {
  // Opções de meses
  const meses = [
    { value: 1, label: 'Janeiro' },
    { value: 2, label: 'Fevereiro' },
    { value: 3, label: 'Março' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Maio' },
    { value: 6, label: 'Junho' },
    { value: 7, label: 'Julho' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Setembro' },
    { value: 10, label: 'Outubro' },
    { value: 11, label: 'Novembro' },
    { value: 12, label: 'Dezembro' },
  ];

  // Opções de anos (últimos 5 anos + próximo ano)
  const anoAtual = new Date().getFullYear();
  const anos = Array.from({ length: 6 }, (_, i) => anoAtual - 4 + i);

  return (
    <Card style={{ marginBottom: 24 }}>
      {/* Seletores de Mês/Ano */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <span style={{ fontWeight: 500 }}>Selecione o período:</span>
            <Select
              value={mes}
              onChange={onMesChange}
              style={{ width: 140 }}
              disabled={loading}
            >
              {meses.map((m) => (
                <Option key={m.value} value={m.value}>
                  {m.label}
                </Option>
              ))}
            </Select>
            <Select
              value={ano}
              onChange={onAnoChange}
              style={{ width: 100 }}
              disabled={loading}
            >
              {anos.map((a) => (
                <Option key={a} value={a}>
                  {a}
                </Option>
              ))}
            </Select>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={onCarregar}
              loading={loading}
            >
              Carregar Dados
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Cards de Resumo */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <Card style={{ backgroundColor: '#e6f7ff', border: '1px solid #91d5ff' }}>
            <Statistic
              title={
                <span>
                  <ClockCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  Adiantamentos
                </span>
              }
              value={totais?.adiantamentos?.valor || 0}
              precision={2}
              valueStyle={{ color: '#1890ff', fontSize: 24 }}
              prefix="R$"
              suffix={
                <div style={{ fontSize: 14, color: '#8c8c8c', marginTop: 4 }}>
                  {totais?.adiantamentos?.quantidade || 0} pagamento(s)
                </div>
              }
              loading={loading}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
            <Statistic
              title={
                <span>
                  <CheckCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                  Regulares
                </span>
              }
              value={totais?.regulares?.valor || 0}
              precision={2}
              valueStyle={{ color: '#52c41a', fontSize: 24 }}
              prefix="R$"
              suffix={
                <div style={{ fontSize: 14, color: '#8c8c8c', marginTop: 4 }}>
                  {totais?.regulares?.quantidade || 0} pagamento(s)
                </div>
              }
              loading={loading}
            />
          </Card>
        </Col>

        <Col xs={24} sm={24} md={8}>
          <Card style={{ backgroundColor: '#f9f0ff', border: '1px solid #d3adf7' }}>
            <Statistic
              title={
                <span>
                  <DollarOutlined style={{ marginRight: 8, color: '#722ed1' }} />
                  Total Geral
                </span>
              }
              value={totais?.geral?.valor || 0}
              precision={2}
              valueStyle={{ color: '#722ed1', fontSize: 24, fontWeight: 'bold' }}
              prefix="R$"
              suffix={
                <div style={{ fontSize: 14, color: '#8c8c8c', marginTop: 4 }}>
                  {totais?.geral?.quantidade || 0} pagamento(s)
                </div>
              }
              loading={loading}
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default RecebimentosSelectorPanel;
