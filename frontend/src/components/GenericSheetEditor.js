import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table, Space, Button, Input, message, Modal, Tooltip } from 'antd';
import { ReloadOutlined, SaveOutlined, PlusOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons';

const GenericSheetEditor = ({ 
  resourceId, 
  apiService, 
  title, 
  readOnly = false 
}) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const carregar = async () => {
    setLoading(true);
    try {
      // apiService deve ter métodos read e save
      const resp = await apiService.read(resourceId, { allPages: true });
      const arr = resp.data?.data || [];
      setData(arr.map((row, idx) => ({ key: idx, __key: idx, ...row })));
      setColumns(resp.data?.columns || Object.keys(arr[0] || {}));
    } catch (e) {
      message.error(`Erro ao carregar ${title || resourceId}: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resourceId) {
      carregar();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resourceId]);

  const setCell = (rowKey, col, value) => {
    setData((prev) => prev.map((r) => (r.key === rowKey ? { ...r, [col]: value } : r)));
  };

  const addRow = () => {
    const template = {};
    columns.forEach((c) => (template[c] = ''));
    const key = `new_${Date.now()}`;
    setData((prev) => [...prev, { key, __key: key, ...template }]);
  };

  const duplicateRow = (row) => {
    const key = `dup_${Date.now()}`;
    const { key: _k, __key: _r, ...rest } = row;
    setData((prev) => [...prev, { key, __key: key, ...rest }]);
  };

  const deleteRow = (row) => {
    Modal.confirm({
      title: 'Excluir linha',
      content: 'Confirma a exclusão desta linha?',
      onOk: () => setData((prev) => prev.filter((r) => r.key !== row.key)),
    });
  };

  const salvar = async () => {
    setSaving(true);
    try {
      const payload = data.map(({ key, __key, ...rest }) => rest);
      await apiService.save(resourceId, payload);
      message.success('Alterações salvas');
      await carregar();
    } catch (e) {
      message.error(e.message || 'Falha ao salvar');
    } finally {
      setSaving(false);
    }
  };

  // Lógica de Formatação Inteligente
  const getColumnConfig = (col) => {
    const lowerCol = col.toLowerCase();
    let width = 180;
    let align = 'left';
    let placeholder = '';

    if (lowerCol.includes('data') || lowerCol.includes('dt_') || lowerCol === 'dt') {
      width = 140;
      placeholder = 'DD/MM/AAAA';
    } else if (lowerCol.includes('valor') || lowerCol.includes('preco') || lowerCol.includes('custo') || lowerCol.includes('orcado') || lowerCol.includes('realizado')) {
      width = 140;
      align = 'right';
      placeholder = '0.00';
    } else if (lowerCol.includes('perc') || lowerCol.includes('taxa')) {
      width = 120;
      align = 'right';
      placeholder = '%';
    } else if (lowerCol.includes('id') || lowerCol.includes('cod')) {
      width = 100;
    } else if (lowerCol.includes('descricao') || lowerCol.includes('nome')) {
      width = 250;
    }

    return { width, align, placeholder };
  };

  const tableCols = useMemo(() => (
    (columns || []).map((c) => {
      const config = getColumnConfig(c);
      return {
        title: c,
        dataIndex: c,
        key: c,
        width: config.width,
        align: config.align,
        render: (val, row) => (
          <Input 
            value={val} 
            onChange={(e) => setCell(row.key, c, e.target.value)} 
            placeholder={config.placeholder}
            style={{ textAlign: config.align === 'right' ? 'right' : 'left' }}
            readOnly={readOnly}
          />
        ),
      };
    }).concat(readOnly ? [] : [
      {
        title: 'Ações',
        key: 'acoes',
        width: 100,
        fixed: 'right',
        render: (_, row) => (
          <Space>
            <Tooltip title="Duplicar">
              <Button icon={<CopyOutlined />} size="small" onClick={() => duplicateRow(row)} />
            </Tooltip>
            <Tooltip title="Excluir">
              <Button danger icon={<DeleteOutlined />} size="small" onClick={() => deleteRow(row)} />
            </Tooltip>
          </Space>
        ),
      },
    ])
  ), [columns, data, readOnly]);

  return (
    <Card
      title={title || resourceId}
      extra={
        !readOnly && (
          <Space>
            <Button icon={<PlusOutlined />} onClick={addRow}>Adicionar</Button>
            <Button icon={<ReloadOutlined />} onClick={carregar} loading={loading}>Recarregar</Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={salvar} loading={saving}>Salvar</Button>
          </Space>
        )
      }
    >
      <Table
        columns={tableCols}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 'max-content' }}
        size="small"
        rowKey="key"
      />
    </Card>
  );
};

export default GenericSheetEditor;
