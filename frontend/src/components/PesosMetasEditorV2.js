import React, { useEffect, useState } from 'react';
import { Card, Table, InputNumber, Button, Space, message, Tag, Progress, Tooltip } from 'antd';
import { SaveOutlined, ReloadOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons';
import { regrasAPI } from '../services/api';
import './PesosMetasEditor.css';

// Friendly labels for components
const COMPONENTES_CONFIG = {
  faturamento_linha: { label: 'Fat. Linha', color: '#1890ff' },
  conversao_linha: { label: 'Conv. Linha', color: '#52c41a' },
  rentabilidade: { label: 'Rentabilidade', color: '#faad14' },
  faturamento_individual: { label: 'Fat. Individual', color: '#722ed1' },
  conversao_individual: { label: 'Conv. Individual', color: '#eb2f96' },
  retencao_clientes: { label: 'Retenção', color: '#13c2c2' },
  meta_fornecedor_1: { label: 'Fornecedor 1', color: '#fa8c16' },
  meta_fornecedor_2: { label: 'Fornecedor 2', color: '#a0d911' },
};

const COMPONENTES = Object.keys(COMPONENTES_CONFIG);

// Color intensity based on percentage value
const getPercentBgColor = (value) => {
  const num = parseFloat(value) || 0;
  if (num === 0) return '#f5f5f5';
  
  // Scale from light to intense green
  const intensity = Math.min(100, Math.max(0, num));
  const hue = 142;
  const saturation = 50 + (intensity * 0.3);
  const lightness = 90 - (intensity * 0.45);
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

const PesosMetasEditor = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);

  const carregar = async () => {
    setLoading(true);
    try {
      const resp = await regrasAPI.getPesosMetas();
      const arr = Array.isArray(resp.data) ? resp.data : [];
      const norm = arr.map((row, idx) => ({
        key: idx,
        ...row,
      }));
      setData(norm);
    } catch (e) {
      message.error(`Erro ao carregar PESOS_METAS: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const handleChangeValor = (rowIndex, field, value) => {
    setData((prev) => {
      const copy = [...prev];
      copy[rowIndex] = { ...copy[rowIndex], [field]: value };
      return copy;
    });
  };

  const salvar = async () => {
    // Validate totals
    for (const row of data) {
      const soma = COMPONENTES.reduce((acc, c) => acc + (Number(row[c]) || 0), 0);
      if (Math.abs(soma - 100) > 0.5) {
        message.error(`Cargo "${row.cargo}": soma dos pesos deve ser 100% (atual: ${soma.toFixed(1)}%)`);
        return;
      }
    }
    
    setSaving(true);
    try {
      const payload = data.map(({ key, ...rest }) => rest);
      await regrasAPI.updatePesosMetas(payload);
      message.success('Pesos salvos com sucesso!');
      setEditMode(false);
      await carregar();
    } catch (e) {
      message.error(e.message || 'Falha ao salvar');
    } finally {
      setSaving(false);
    }
  };

  // Read mode: show visual progress bars
  const renderReadCell = (value, field) => {
    const num = parseFloat(value) || 0;
    const config = COMPONENTES_CONFIG[field];
    
    if (num === 0) {
      return <span className="peso-zero">-</span>;
    }
    
    return (
      <Tooltip title={`${num.toFixed(1)}%`}>
        <div 
          className="peso-cell"
          style={{ backgroundColor: getPercentBgColor(num) }}
        >
          <span className="peso-value">{num.toFixed(0)}%</span>
        </div>
      </Tooltip>
    );
  };

  // Edit mode: input with percent
  const renderEditCell = (value, rowIndex, field) => {
    return (
      <InputNumber
        min={0}
        max={100}
        step={1}
        value={value !== undefined && value !== '' ? Number(value) : 0}
        onChange={(v) => handleChangeValor(rowIndex, field, v)}
        formatter={(v) => `${v}%`}
        parser={(v) => v.replace('%', '')}
        size="small"
        style={{ width: '100%' }}
      />
    );
  };

  const columns = [
    {
      title: 'Cargo',
      dataIndex: 'cargo',
      key: 'cargo',
      width: 160,
      fixed: 'left',
      render: (text) => <strong>{text || '-'}</strong>,
    },
    ...COMPONENTES.map((field) => ({
      title: (
        <Tooltip title={field.replace(/_/g, ' ')}>
          <span style={{ fontSize: 12 }}>{COMPONENTES_CONFIG[field].label}</span>
        </Tooltip>
      ),
      dataIndex: field,
      key: field,
      width: 100,
      align: 'center',
      render: (value, record, index) => 
        editMode 
          ? renderEditCell(value, index, field)
          : renderReadCell(value, field),
    })),
    {
      title: 'Total',
      key: 'soma',
      width: 100,
      fixed: 'right',
      align: 'center',
      render: (_, record) => {
        const soma = COMPONENTES.reduce((acc, c) => acc + (Number(record[c]) || 0), 0);
        const ok = Math.abs(soma - 100) <= 0.5;
        
        if (editMode) {
          return (
            <Tag color={ok ? 'green' : 'red'} style={{ fontWeight: 600 }}>
              {soma.toFixed(0)}%
            </Tag>
          );
        }
        
        return (
          <Progress 
            type="circle" 
            percent={soma} 
            size={40}
            format={() => `${soma.toFixed(0)}%`}
            status={ok ? 'success' : 'exception'}
          />
        );
      },
    },
  ];

  return (
    <Card
      className="pesos-editor"
      title={
        <Space>
          <span>Pesos do Fator de Correção (FC)</span>
          {editMode && <Tag color="orange">Modo Edição</Tag>}
        </Space>
      }
      extra={
        <Space>
          {editMode ? (
            <>
              <Button onClick={() => { carregar(); setEditMode(false); }}>
                Cancelar
              </Button>
              <Button 
                type="primary" 
                icon={<SaveOutlined />} 
                onClick={salvar} 
                loading={saving}
              >
                Salvar
              </Button>
            </>
          ) : (
            <>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={carregar} 
                loading={loading}
              />
              <Button 
                type="primary"
                icon={<EditOutlined />} 
                onClick={() => setEditMode(true)}
              >
                Editar
              </Button>
            </>
          )}
        </Space>
      }
    >
      <div className="pesos-legend">
        {COMPONENTES.map((c) => (
          <span key={c} className="legend-item">
            <span 
              className="legend-dot" 
              style={{ backgroundColor: COMPONENTES_CONFIG[c].color }}
            />
            {COMPONENTES_CONFIG[c].label}
          </span>
        ))}
      </div>
      
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={false}
        scroll={{ x: 'max-content' }}
        size="small"
        rowKey="key"
      />
    </Card>
  );
};

export default PesosMetasEditor;
