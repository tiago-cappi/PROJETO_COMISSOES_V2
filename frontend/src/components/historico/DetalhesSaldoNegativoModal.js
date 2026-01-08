import React, { useMemo } from 'react';
import { Modal, Card, Descriptions, Typography, Alert, Steps, Tag } from 'antd';
import { 
  PercentageOutlined, 
  DollarOutlined, 
  CalculatorOutlined,
  InfoCircleOutlined,
  LineChartOutlined,
  SwapOutlined
} from '@ant-design/icons';

const { Text } = Typography;

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

const formatPercent = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
};

const formatFCMP = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return num.toFixed(4);
};

const DetalhesSaldoNegativoModal = ({ visible, onClose, item }) => {
  // Detectar o tipo de saldo negativo
  const tipoComissao = item?.Tipo_Comissao || item?.tipo_comissao || 'DEVOLUCAO';
  const isReconciliacao = tipoComissao === 'RECONCILIACAO';

  const detalhes = useMemo(() => {
    if (!item) return null;

    if (isReconciliacao) {
      // Campos para RECONCILIAÇÃO
      const valorBase = Number(item.Valor_Base ?? item.valor_base); // Comissão adiantada
      const fcmp = Number(item.FC ?? item.fc ?? item.fcmp); // FCMP calculado
      const fatorDif = Number(item.Fator_Devolucao ?? item.fator_devolucao); // FCMP - 1.0
      const saldo = Number(item.Comissao_Calculada ?? item.comissao_calculada);
      const tcmp = Number(item.TCMP ?? item.tcmp);

      return {
        valorBase: Number.isNaN(valorBase) ? null : valorBase,
        fcmp: Number.isNaN(fcmp) ? null : fcmp,
        fatorDif: Number.isNaN(fatorDif) ? null : fatorDif,
        saldo: Number.isNaN(saldo) ? null : saldo,
        tcmp: Number.isNaN(tcmp) ? null : tcmp,
      };
    } else {
      // Campos para DEVOLUÇÃO (código existente)
      const valorDevolvido = Number(item.Valor_Base ?? item.valor_base);
      const fator = Number(item.Fator_Devolucao ?? item.fator_devolucao);
      const estorno = Number(item.Comissao_Calculada ?? item.comissao_calculada);
      const comissaoOriginal = Number(item.comissao_original ?? item.Comissao_Original);
      const valorRealizado = Number(item.valor_realizado ?? item.Valor_Realizado);

      return {
        valorDevolvido: Number.isNaN(valorDevolvido) ? null : valorDevolvido,
        fator: Number.isNaN(fator) ? null : fator,
        estorno: Number.isNaN(estorno) ? null : estorno,
        comissaoOriginal: Number.isNaN(comissaoOriginal) ? null : comissaoOriginal,
        valorRealizado: Number.isNaN(valorRealizado) ? null : valorRealizado,
      };
    }
  }, [item, isReconciliacao]);

  const colaborador = item?.Nome_Colaborador || item?.nome_colaborador || '-';
  const processo = item?.Processo || item?.processo || '-';
  const nf = item?.Numero_NF || item?.numero_nf || '-';
  const cargo = item?.Cargo || item?.cargo || '-';

  // Steps para RECONCILIAÇÃO
  const stepsReconciliacao = useMemo(() => {
    if (!detalhes || !isReconciliacao) return [];
    
    const saldoPositivo = (detalhes.saldo || 0) > 0;
    const saldoZero = Math.abs(detalhes.saldo || 0) < 0.01;

    return [
      {
        title: 'Comissão Adiantada',
        icon: <DollarOutlined />,
        description: (
          <Card size="small" style={{ marginTop: 8, background: '#fafafa' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              Valor da comissão antecipada ao colaborador (calculada com FC = 1.0).
            </Text>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="Comissão Adiantada">
                <Text strong style={{ fontSize: 16 }}>
                  {formatCurrencyBR(detalhes.valorBase)}
                </Text>
              </Descriptions.Item>
              {detalhes.tcmp && (
                <Descriptions.Item label="TCMP (peso proporcional)">
                  <Text>{formatPercent(detalhes.tcmp)}</Text>
                </Descriptions.Item>
              )}
            </Descriptions>
            <Alert
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
              style={{ marginTop: 8 }}
              message="Valor pago antecipadamente com base no pagamento recebido (COT/Adiantamento)."
            />
          </Card>
        ),
      },
      {
        title: 'FCMP Calculado',
        icon: <LineChartOutlined />,
        description: (
          <Card size="small" style={{ marginTop: 8, background: '#f6ffed' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              Fator de Comissão Mensal do Processo, calculado após o faturamento com base nas metas atingidas.
            </Text>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="FCMP Real">
                <Text strong type={detalhes.fcmp >= 1 ? 'success' : 'warning'} style={{ fontSize: 16 }}>
                  {formatFCMP(detalhes.fcmp)}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Diferença (FCMP - 1.0)">
                <Text strong type={detalhes.fatorDif >= 0 ? 'success' : 'danger'}>
                  {detalhes.fatorDif >= 0 ? '+' : ''}{formatFCMP(detalhes.fatorDif)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
            <Alert
              type={detalhes.fcmp >= 1 ? 'success' : 'warning'}
              showIcon
              style={{ marginTop: 8 }}
              message={
                detalhes.fcmp >= 1
                  ? 'FCMP ≥ 1.0: O colaborador atingiu ou superou as metas.'
                  : 'FCMP < 1.0: As metas não foram totalmente atingidas.'
              }
            />
          </Card>
        ),
      },
      {
        title: 'Ajuste de Reconciliação',
        icon: <SwapOutlined />,
        description: (
          <Card size="small" style={{ marginTop: 8, background: saldoPositivo ? '#f6ffed' : '#fff1f0' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              Diferença entre o que foi adiantado e o que deveria ter sido pago com base no FCMP real.
            </Text>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label={<Text code>Ajuste = Adiantado × (FCMP - 1.0)</Text>}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Text>{formatCurrencyBR(detalhes.valorBase)}</Text>
                  <Text>×</Text>
                  <Text>({formatFCMP(detalhes.fatorDif)})</Text>
                </div>
              </Descriptions.Item>
              <Descriptions.Item label="Saldo Final">
                <Text 
                  type={saldoZero ? 'secondary' : (saldoPositivo ? 'success' : 'danger')} 
                  strong 
                  style={{ fontSize: 18 }}
                >
                  {formatCurrencyBR(detalhes.saldo)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
            <Alert
              type={saldoZero ? 'info' : (saldoPositivo ? 'success' : 'warning')}
              showIcon
              style={{ marginTop: 8 }}
              message={
                saldoZero
                  ? 'Saldo quitado: Não há ajuste a fazer.'
                  : saldoPositivo
                    ? 'Saldo positivo: A empresa deve este valor ao colaborador.'
                    : 'Saldo negativo: Este valor será descontado das próximas comissões.'
              }
            />
          </Card>
        ),
      },
    ];
  }, [detalhes, isReconciliacao]);

  // Steps para DEVOLUÇÃO (código existente)
  const stepsDevolucao = useMemo(() => {
    if (!detalhes || isReconciliacao) return [];
    
    return [
      {
        title: 'Fator de Devolução',
        icon: <PercentageOutlined />,
        description: (
          <Card size="small" style={{ marginTop: 8, background: '#fafafa' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              O fator representa a proporção do valor devolvido em relação ao valor total do processo.
            </Text>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="Valor Devolvido (A)">
                <Text strong>{formatCurrencyBR(detalhes.valorDevolvido)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Valor Realizado do Processo (B)">
                <Text strong>{formatCurrencyBR(detalhes.valorRealizado)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={<Text code>Fator = A ÷ B</Text>}>
                <Text strong type="warning" style={{ fontSize: 16 }}>
                  {formatPercent(detalhes.fator)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        ),
      },
      {
        title: 'Comissão Original',
        icon: <DollarOutlined />,
        description: (
          <Card size="small" style={{ marginTop: 8, background: '#fafafa' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              Soma de todas as comissões que o colaborador recebeu neste processo (obtida do histórico).
            </Text>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="Comissão Total no Processo">
                <Text strong style={{ fontSize: 16 }}>
                  {formatCurrencyBR(detalhes.comissaoOriginal)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
            <Alert
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
              style={{ marginTop: 8 }}
              message="Este valor é a soma de todos os itens faturados do processo no histórico de comissões."
            />
          </Card>
        ),
      },
      {
        title: 'Cálculo do Estorno',
        icon: <CalculatorOutlined />,
        description: (
          <Card size="small" style={{ marginTop: 8, background: '#fff1f0' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              O estorno é proporcional à devolução. Se 10% foi devolvido, 10% da comissão é estornada.
            </Text>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label={<Text code>Estorno = Comissão × Fator × (-1)</Text>}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Text>{formatCurrencyBR(detalhes.comissaoOriginal)}</Text>
                  <Text>×</Text>
                  <Text>{formatPercent(detalhes.fator)}</Text>
                  <Text>×</Text>
                  <Text>(-1)</Text>
                </div>
              </Descriptions.Item>
              <Descriptions.Item label="Estorno Final">
                <Text type="danger" strong style={{ fontSize: 18 }}>
                  {formatCurrencyBR(detalhes.estorno)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
            <Alert
              type="warning"
              showIcon
              style={{ marginTop: 8 }}
              message="Este valor negativo será descontado nas próximas comissões do colaborador."
            />
          </Card>
        ),
      },
    ];
  }, [detalhes, isReconciliacao]);

  const stepItems = isReconciliacao ? stepsReconciliacao : stepsDevolucao;

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      onOk={onClose}
      okText="Fechar"
      cancelButtonProps={{ style: { display: 'none' } }}
      width={700}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span>Detalhes do Saldo Negativo</span>
          {isReconciliacao ? (
            <Tag color="orange">RECONCILIAÇÃO</Tag>
          ) : (
            <Tag color="red">DEVOLUÇÃO</Tag>
          )}
        </div>
      }
      destroyOnClose
    >
      {!item || !detalhes ? (
        <Text type="secondary">Nenhum item selecionado.</Text>
      ) : (
        <div>
          {/* Cabeçalho com informações gerais */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="Colaborador">
                <Text strong>{colaborador}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Cargo">
                <Text>{cargo}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Processo">
                <Text strong>{processo}</Text>
              </Descriptions.Item>
              {!isReconciliacao && (
                <Descriptions.Item label="NF Devolução">
                  <Text>{nf}</Text>
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          {/* Passo a passo educativo */}
          <Steps
            direction="vertical"
            size="small"
            current={3}
            items={stepItems}
          />

          {/* Observação se existir */}
          {(item.Observacao || item.observacao) && (
            <Alert
              type="info"
              style={{ marginTop: 16 }}
              message="Observação"
              description={item.Observacao || item.observacao}
            />
          )}
        </div>
      )}
    </Modal>
  );
};

export default DetalhesSaldoNegativoModal;
