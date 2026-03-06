import React, { useState } from 'react';
import { Button, Card, Descriptions, Divider, Space, Tag, Typography } from 'antd';
import { AuditOutlined } from '@ant-design/icons';
import { ModalDetalhesCalculoRecebimento } from '../recebimentos';
import './ColaboradorDashboard.css';

const { Text, Title } = Typography;

const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const formatPercent = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
};

/**
 * Renderiza o detalhamento inline (expandido) de um pagamento de recebimento.
 *
 * Mostra cálculo simplificado inline + botão "Auditoria Completa" que abre
 * o ModalDetalhesCalculoRecebimento existente (1291 linhas de UI sofisticada).
 *
 * @param {Object} props
 * @param {Object} props.pagamento - Objeto do pagamento (id, tipo, processo, valor_pago, tcmp, fcmp, comissao_calculada)
 */
const RecebimentoItemDetail = ({ pagamento }) => {
  const [auditoriaVisible, setAuditoriaVisible] = useState(false);

  if (!pagamento) {
    return <div className="colab-item-detail">Nenhum dado disponível.</div>;
  }

  const isAdiantamento = pagamento.tipo === 'ADIANTAMENTO' || pagamento.tipo === 'Antecipação';
  const valorPago = pagamento.valor_pago || 0;
  const tcmp = pagamento.tcmp || 0;
  const fcmp = isAdiantamento ? 1.0 : (pagamento.fcmp || 1.0);
  const comissao = pagamento.comissao_calculada || 0;

  return (
    <div className="colab-item-detail">
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* Tipo badge */}
        <div>
          <Tag color={isAdiantamento ? 'blue' : 'green'} style={{ fontSize: 13 }}>
            {isAdiantamento ? '🔵 Adiantamento' : '🟢 Pagamento Regular'}
          </Tag>
        </div>

        {/* Informações gerais */}
        <Card size="small">
          <Descriptions bordered size="small" column={{ xs: 1, sm: 2 }}>
            <Descriptions.Item label="Processo">
              <Text strong>{pagamento.processo || '-'}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Data Pagamento">
              {pagamento.data_pagamento
                ? new Date(pagamento.data_pagamento).toLocaleDateString('pt-BR')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Valor Pago">
              <Text strong style={{ fontSize: 16 }}>{formatCurrencyBR(valorPago)}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="TCMP">
              <Text strong>{formatPercent(tcmp)}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="FCMP">
              <Text strong>{isAdiantamento ? '1.0000 (fixo)' : fcmp.toFixed(4)}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Comissão Final">
              <Text strong type="success" style={{ fontSize: 16 }}>{formatCurrencyBR(comissao)}</Text>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Fórmula do cálculo */}
        <Card size="small" title={<Title level={5} style={{ margin: 0 }}>Cálculo</Title>}>
          <div style={{ fontFamily: 'monospace', fontSize: 13, lineHeight: 2 }}>
            <div><strong>Fórmula:</strong> Comissão = Valor_Pago × TCMP × FCMP</div>
            <div>
              <strong>Substituindo:</strong>{' '}
              {formatCurrencyBR(valorPago)} × {formatPercent(tcmp)} × {fcmp.toFixed(4)}
            </div>
            <Divider style={{ margin: '8px 0' }} />
            <div>
              <strong>Resultado:</strong>{' '}
              <Text type="success" strong style={{ fontSize: 16 }}>{formatCurrencyBR(comissao)}</Text>
            </div>
          </div>
        </Card>

        {/* Nota para adiantamentos */}
        {isAdiantamento && (
          <Card size="small" style={{ background: '#f0f8ff', border: '1px solid #cce5ff' }}>
            <Text><strong>ⓘ Adiantamento:</strong> O FC (Fator de Correção) baseado em metas não é aplicado (FCMP = 1.0). O ajuste será feito na Reconciliação após o faturamento.</Text>
          </Card>
        )}

        {/* Botão de auditoria completa */}
        <Button
          type="default"
          icon={<AuditOutlined />}
          onClick={() => setAuditoriaVisible(true)}
          style={{ alignSelf: 'flex-start' }}
        >
          Auditoria Completa (TCMP/FCMP detalhado)
        </Button>
      </Space>

      {/* Modal de auditoria completa (reutiliza componente existente) */}
      <ModalDetalhesCalculoRecebimento
        visible={auditoriaVisible}
        onClose={() => setAuditoriaVisible(false)}
        pagamento={pagamento}
      />
    </div>
  );
};

export default RecebimentoItemDetail;
