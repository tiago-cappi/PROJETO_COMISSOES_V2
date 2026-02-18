import React, { useState } from 'react';
import {
  Card,
  Input,
  InputNumber,
  Button,
  Space,
  Typography,
  Collapse,
  Popconfirm,
  Tag,
  Divider,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  DeleteOutlined,
  UserOutlined,
  DollarOutlined,
  PercentageOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons';
import AplicacoesSelector from './AplicacoesSelector';
import DegrausEditor from './DegrausEditor';

const { Text, Title } = Typography;
const { Panel } = Collapse;

/**
 * Card de configuração de um colaborador individual.
 * Inclui nome, aplicações vinculadas, meta e degraus de comissão.
 */
const ColaboradorMetaCard = ({
  colaborador,
  index,
  onChange,
  onRemove,
  aplicacoesDisponiveis = [],
  disabled = false,
}) => {
  const [expanded, setExpanded] = useState(true);

  // Atualizar campo do colaborador
  const handleFieldChange = (campo, valor) => {
    onChange(index, { ...colaborador, [campo]: valor });
  };

  // Atualizar degraus
  const handleDegrausChange = (novosDegraus) => {
    onChange(index, { ...colaborador, degraus: novosDegraus });
  };

  // Estatísticas rápidas
  const totalDegraus = colaborador.degraus?.length || 0;
  const degrausPadrao = colaborador.degraus?.filter(d => d.tipo_degrau === 'PADRAO').length || 0;
  const degrausBonus = colaborador.degraus?.filter(d => d.tipo_degrau === 'BONUS').length || 0;
  const taxaMaxima = colaborador.degraus?.length > 0 
    ? Math.max(...colaborador.degraus.map(d => d.taxa_comissao_pct || 0))
    : 0;

  const cardTitle = (
    <Space>
      <UserOutlined />
      <Text strong style={{ fontSize: 16 }}>
        {colaborador.nome_colaborador || 'Novo Colaborador'}
      </Text>
      {colaborador.aplicacoes_vinculadas?.length > 0 && (
        <Tag color="blue">{colaborador.aplicacoes_vinculadas.length} aplicação(ões)</Tag>
      )}
      {totalDegraus > 0 && (
        <Tag color="green">{totalDegraus} degrau(s)</Tag>
      )}
    </Space>
  );

  const cardExtra = (
    <Space>
      <Button
        type="text"
        icon={expanded ? <UpOutlined /> : <DownOutlined />}
        onClick={(e) => {
          e.stopPropagation();
          setExpanded(!expanded);
        }}
      />
      <Popconfirm
        title="Remover colaborador?"
        description="Esta ação não pode ser desfeita."
        onConfirm={() => onRemove(index)}
        okText="Sim"
        cancelText="Não"
      >
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          disabled={disabled}
          onClick={(e) => e.stopPropagation()}
        />
      </Popconfirm>
    </Space>
  );

  return (
    <Card
      title={cardTitle}
      extra={cardExtra}
      style={{ marginBottom: 16 }}
      bodyStyle={{ display: expanded ? 'block' : 'none' }}
      hoverable
    >
      <Row gutter={[16, 16]}>
        {/* Nome do Colaborador */}
        <Col xs={24} md={12}>
          <div style={{ marginBottom: 8 }}>
            <Text strong>Nome do Colaborador</Text>
          </div>
          <Input
            value={colaborador.nome_colaborador || ''}
            onChange={(e) => handleFieldChange('nome_colaborador', e.target.value)}
            placeholder="Nome completo do colaborador"
            prefix={<UserOutlined />}
            disabled={disabled}
          />
        </Col>

        {/* Meta de Faturamento */}
        <Col xs={24} md={12}>
          <div style={{ marginBottom: 8 }}>
            <Text strong>Meta de Faturamento Mensal</Text>
          </div>
          <InputNumber
            value={colaborador.meta_faturamento || 0}
            onChange={(val) => handleFieldChange('meta_faturamento', val || 0)}
            formatter={(value) => `R$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
            parser={(value) => value.replace(/R\$\s?|(\.)/g, '').replace(',', '.')}
            min={0}
            step={1000}
            style={{ width: '100%' }}
            prefix={<DollarOutlined />}
            disabled={disabled}
          />
        </Col>

        {/* Aplicações Vinculadas */}
        <Col xs={24}>
          <div style={{ marginBottom: 8 }}>
            <Text strong>Aplicações Vinculadas</Text>
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
              (Coluna "Aplicação Mat./Serv." da Análise Comercial)
            </Text>
          </div>
          <AplicacoesSelector
            value={colaborador.aplicacoes_vinculadas || []}
            onChange={(apps) => handleFieldChange('aplicacoes_vinculadas', apps)}
            aplicacoesDisponiveis={aplicacoesDisponiveis}
            disabled={disabled}
          />
        </Col>
      </Row>

      <Divider orientation="left" style={{ marginTop: 24 }}>
        <Space>
          <PercentageOutlined />
          <span>Degraus de Comissão</span>
        </Space>
      </Divider>

      {/* Estatísticas dos Degraus */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic
            title="Total Degraus"
            value={totalDegraus}
            valueStyle={{ color: '#1890ff', fontSize: 20 }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Degraus Padrão"
            value={degrausPadrao}
            valueStyle={{ color: '#52c41a', fontSize: 20 }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Degraus Bônus"
            value={degrausBonus}
            valueStyle={{ color: '#faad14', fontSize: 20 }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Taxa Máxima"
            value={taxaMaxima}
            suffix="%"
            precision={2}
            valueStyle={{ color: '#722ed1', fontSize: 20 }}
          />
        </Col>
      </Row>

      {/* Editor de Degraus */}
      <DegrausEditor
        degraus={colaborador.degraus || []}
        onChange={handleDegrausChange}
        disabled={disabled}
      />
    </Card>
  );
};

export default ColaboradorMetaCard;
