import React from 'react';
import {
  Table,
  InputNumber,
  Select,
  Input,
  Button,
  Space,
  Tooltip,
  Tag,
  Typography,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

/**
 * Editor de degraus de comissão para um colaborador.
 * Permite adicionar, remover e reordenar degraus.
 */
const DegrausEditor = ({
  degraus = [],
  onChange,
  disabled = false,
}) => {
  // Adicionar novo degrau
  const handleAddDegrau = () => {
    const novaOrdem = degraus.length > 0 
      ? Math.max(...degraus.map(d => d.ordem_degrau)) + 1 
      : 1;
    
    // Determinar tipo baseado na quantidade de degraus existentes
    // Se já existem 3+ degraus, novos são BONUS por padrão
    const tipoDefault = degraus.filter(d => d.tipo_degrau === 'PADRAO').length >= 3 
      ? 'BONUS' 
      : 'PADRAO';
    
    const novoDegrau = {
      ordem_degrau: novaOrdem,
      taxa_comissao_pct: 0,
      tipo_degrau: tipoDefault,
      descricao: '',
    };
    
    onChange([...degraus, novoDegrau]);
  };

  // Remover degrau
  const handleRemoveDegrau = (ordemParaRemover) => {
    const novosDegraus = degraus
      .filter(d => d.ordem_degrau !== ordemParaRemover)
      .map((d, idx) => ({ ...d, ordem_degrau: idx + 1 })); // Reordenar
    onChange(novosDegraus);
  };

  // Atualizar campo de um degrau
  const handleUpdateDegrau = (ordem, campo, valor) => {
    const novosDegraus = degraus.map(d => {
      if (d.ordem_degrau === ordem) {
        return { ...d, [campo]: valor };
      }
      return d;
    });
    onChange(novosDegraus);
  };

  // Mover degrau para cima
  const handleMoveUp = (index) => {
    if (index === 0) return;
    const novosDegraus = [...degraus];
    [novosDegraus[index - 1], novosDegraus[index]] = [novosDegraus[index], novosDegraus[index - 1]];
    // Reordenar
    novosDegraus.forEach((d, idx) => { d.ordem_degrau = idx + 1; });
    onChange(novosDegraus);
  };

  // Mover degrau para baixo
  const handleMoveDown = (index) => {
    if (index === degraus.length - 1) return;
    const novosDegraus = [...degraus];
    [novosDegraus[index], novosDegraus[index + 1]] = [novosDegraus[index + 1], novosDegraus[index]];
    // Reordenar
    novosDegraus.forEach((d, idx) => { d.ordem_degrau = idx + 1; });
    onChange(novosDegraus);
  };

  // Calcular faixas de FC para exibição
  const calcularFaixaFC = (index, tipo) => {
    const degrausPadrao = degraus.filter(d => d.tipo_degrau === 'PADRAO');
    const degrausBonus = degraus.filter(d => d.tipo_degrau === 'BONUS');
    
    if (tipo === 'PADRAO') {
      const indexPadrao = degrausPadrao.findIndex(d => d.ordem_degrau === degraus[index].ordem_degrau);
      const n = degrausPadrao.length;
      if (n === 0) return '-';
      
      const fcMin = (indexPadrao / n * 100).toFixed(0);
      const fcMax = ((indexPadrao + 1) / n * 100).toFixed(0);
      
      if (indexPadrao === n - 1) {
        return `${fcMin}% - <100%`;
      }
      return `${fcMin}% - <${fcMax}%`;
    } else {
      const indexBonus = degrausBonus.findIndex(d => d.ordem_degrau === degraus[index].ordem_degrau);
      const fcMin = (100 + indexBonus * 20);
      const fcMax = fcMin + 20;
      
      if (indexBonus === degrausBonus.length - 1) {
        return `≥${fcMin}%`;
      }
      return `${fcMin}% - <${fcMax}%`;
    }
  };

  // Ordenar degraus por ordem
  const degrausOrdenados = [...degraus].sort((a, b) => a.ordem_degrau - b.ordem_degrau);

  const columns = [
    {
      title: '#',
      dataIndex: 'ordem_degrau',
      key: 'ordem',
      width: 50,
      align: 'center',
      render: (ordem) => (
        <Tag color="default">{ordem}</Tag>
      ),
    },
    {
      title: 'Faixa FC',
      key: 'faixa',
      width: 120,
      render: (_, record, index) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {calcularFaixaFC(index, record.tipo_degrau)}
        </Text>
      ),
    },
    {
      title: 'Taxa Comissão (%)',
      dataIndex: 'taxa_comissao_pct',
      key: 'taxa',
      width: 140,
      render: (taxa, record) => (
        <InputNumber
          value={taxa}
          min={0}
          max={100}
          step={0.1}
          precision={2}
          disabled={disabled}
          onChange={(val) => handleUpdateDegrau(record.ordem_degrau, 'taxa_comissao_pct', val || 0)}
          addonAfter="%"
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_degrau',
      key: 'tipo',
      width: 120,
      render: (tipo, record) => (
        <Select
          value={tipo}
          disabled={disabled}
          onChange={(val) => handleUpdateDegrau(record.ordem_degrau, 'tipo_degrau', val)}
          style={{ width: '100%' }}
        >
          <Select.Option value="PADRAO">
            <Tag color="blue">Padrão</Tag>
          </Select.Option>
          <Select.Option value="BONUS">
            <Tag color="gold">Bônus</Tag>
          </Select.Option>
        </Select>
      ),
    },
    {
      title: 'Descrição',
      dataIndex: 'descricao',
      key: 'descricao',
      render: (desc, record) => (
        <Input
          value={desc || ''}
          placeholder="Ex: Piso, Meta, Bônus..."
          disabled={disabled}
          onChange={(e) => handleUpdateDegrau(record.ordem_degrau, 'descricao', e.target.value)}
        />
      ),
    },
    {
      title: 'Ações',
      key: 'acoes',
      width: 120,
      align: 'center',
      render: (_, record, index) => (
        <Space size="small">
          <Tooltip title="Mover para cima">
            <Button
              type="text"
              size="small"
              icon={<ArrowUpOutlined />}
              disabled={disabled || index === 0}
              onClick={() => handleMoveUp(index)}
            />
          </Tooltip>
          <Tooltip title="Mover para baixo">
            <Button
              type="text"
              size="small"
              icon={<ArrowDownOutlined />}
              disabled={disabled || index === degrausOrdenados.length - 1}
              onClick={() => handleMoveDown(index)}
            />
          </Tooltip>
          <Tooltip title="Remover degrau">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={disabled || degraus.length <= 1}
              onClick={() => handleRemoveDegrau(record.ordem_degrau)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="degraus-editor">
      <Table
        dataSource={degrausOrdenados}
        columns={columns}
        rowKey="ordem_degrau"
        pagination={false}
        size="small"
        bordered
      />
      
      <Button
        type="dashed"
        onClick={handleAddDegrau}
        disabled={disabled}
        icon={<PlusOutlined />}
        style={{ width: '100%', marginTop: 8 }}
      >
        Adicionar Degrau
      </Button>
      
      <div style={{ marginTop: 8 }}>
        <Text type="secondary" style={{ fontSize: 11 }}>
          <strong>Degraus Padrão:</strong> Distribuídos proporcionalmente entre FC 0% e &lt;100%. 
          <strong> Degraus Bônus:</strong> Para FC ≥100%, cada degrau adicional requer +20% de FC.
        </Text>
      </div>
    </div>
  );
};

export default DegrausEditor;
