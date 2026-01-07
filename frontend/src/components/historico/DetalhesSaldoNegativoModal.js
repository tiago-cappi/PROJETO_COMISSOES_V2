import React, { useMemo } from 'react';
import { Modal, Card, Descriptions, Typography, Alert, Steps } from 'antd';
import { 
  PercentageOutlined, 
  DollarOutlined, 
  CalculatorOutlined,
  InfoCircleOutlined
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

const DetalhesSaldoNegativoModal = ({ visible, onClose, item }) => {
  const detalhes = useMemo(() => {
    if (!item) return null;

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
  }, [item]);

  const colaborador = item?.Nome_Colaborador || item?.nome_colaborador || '-';
  const processo = item?.Processo || item?.processo || '-';
  const nf = item?.Numero_NF || item?.numero_nf || '-';
  const cargo = item?.Cargo || item?.cargo || '-';

  const stepItems = useMemo(() => {
    if (!detalhes) return [];
    
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
  }, [detalhes]);

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      onOk={onClose}
      okText="Fechar"
      cancelButtonProps={{ style: { display: 'none' } }}
      width={700}
      title="Detalhes do Saldo Negativo"
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
              <Descriptions.Item label="NF Devolução">
                <Text>{nf}</Text>
              </Descriptions.Item>
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
