import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Table, Space, Button, Input, message, Modal, Tooltip, Card, Empty } from 'antd';
import { 
  ReloadOutlined, 
  SaveOutlined, 
  PlusOutlined, 
  CopyOutlined, 
  DeleteOutlined,
  SearchOutlined,
  EditOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { renderCell, renderEditor } from './cellRenderers';
import './SmartTable.css';

/**
 * SmartTable - A powerful, schema-driven table component
 * 
 * @param {string} resourceId - Identifier for the data source
 * @param {object} apiService - Object with read(id, params) and save(id, data) methods
 * @param {string} title - Display title for the table
 * @param {object} schema - Column schema definitions
 * @param {boolean} readOnly - Whether editing is disabled
 * @param {object} lookups - Cross-reference data for dropdowns { columnName: [options] }
 * @param {ReactNode} extraActions - Additional action buttons to display in header
 */
const SmartTable = ({ 
  resourceId, 
  apiService, 
  title, 
  schema = {},
  readOnly = false,
  lookups = {},
  compact = false,
  extraActions = null
}) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [modifiedRows, setModifiedRows] = useState(new Set());

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await apiService.read(resourceId, { allPages: true });
      const arr = resp.data?.data || [];
      setData(arr.map((row, idx) => ({ __key: `row_${idx}`, __original: { ...row }, ...row })));
      setColumns(resp.data?.columns || Object.keys(arr[0] || {}));
      setModifiedRows(new Set());
    } catch (e) {
      message.error(`Erro ao carregar ${title || resourceId}: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [resourceId, apiService, title]);

  useEffect(() => {
    if (resourceId) {
      carregar();
    }
  }, [resourceId, carregar]);

  const setCell = (rowKey, col, value) => {
    setData((prev) => prev.map((r) => {
      if (r.__key === rowKey) {
        setModifiedRows((m) => new Set(m).add(rowKey));
        return { ...r, [col]: value };
      }
      return r;
    }));
  };

  const addRow = () => {
    const template = {};
    columns.forEach((c) => (template[c] = ''));
    const key = `new_${Date.now()}`;
    setData((prev) => [...prev, { __key: key, __original: null, __isNew: true, ...template }]);
    setModifiedRows((m) => new Set(m).add(key));
    setEditMode(true);
  };

  const duplicateRow = (row) => {
    const key = `dup_${Date.now()}`;
    const { __key, __original, __isNew, ...rest } = row;
    setData((prev) => [...prev, { __key: key, __original: null, __isNew: true, ...rest }]);
    setModifiedRows((m) => new Set(m).add(key));
  };

  const deleteRow = (row) => {
    Modal.confirm({
      title: 'Excluir linha',
      content: 'Confirma a exclusão desta linha?',
      okText: 'Excluir',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: () => {
        // Marcar linha como deletada em vez de remover imediatamente
        setData((prev) => prev.map((r) => {
          if (r.__key === row.__key) {
            setModifiedRows((m) => new Set(m).add(row.__key));
            return { ...r, __isDeleted: true };
          }
          return r;
        }));
      },
    });
  };

  const undoDeleteRow = (row) => {
    setData((prev) => prev.map((r) => {
      if (r.__key === row.__key) {
        const newRow = { ...r };
        delete newRow.__isDeleted;
        return newRow;
      }
      return r;
    }));
  };

  const validate = () => {
    // Basic validation - can be extended with schema rules
    for (const row of data) {
      // Skip validation for deleted rows
      if (row.__isDeleted) continue;
      
      for (const col of columns) {
        const colSchema = schema[col] || {};
        if (colSchema.required && !row[col]) {
          message.error(`Campo obrigatório "${col}" está vazio.`);
          return false;
        }
        if (colSchema.type === 'percent') {
          const val = parseFloat(row[col]);
          if (!isNaN(val) && (val < 0 || val > 100)) {
            message.error(`"${col}" deve estar entre 0% e 100%.`);
            return false;
          }
        }
      }
    }
    return true;
  };

  const salvar = async () => {
    if (!validate()) return;
    
    setSaving(true);
    try {
      // Filtrar linhas deletadas e remover metadados internos
      const payload = data
        .filter((row) => !row.__isDeleted) // Excluir linhas marcadas como deletadas
        .map(({ __key, __original, __isNew, __isDeleted, ...rest }) => rest);
      
      await apiService.save(resourceId, payload);
      message.success('Alterações salvas com sucesso!');
      setEditMode(false);
      await carregar();
    } catch (e) {
      message.error(e.message || 'Falha ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const cancelEdit = () => {
    Modal.confirm({
      title: 'Descartar alterações?',
      content: 'Todas as modificações não salvas serão perdidas.',
      okText: 'Descartar',
      okType: 'danger',
      cancelText: 'Continuar editando',
      onOk: () => {
        carregar();
        setEditMode(false);
      },
    });
  };

  // Filter data based on search
  const filteredData = useMemo(() => {
    let result = data;
    
    if (!searchText) return result;
    
    const lower = searchText.toLowerCase();
    return result.filter((row) =>
      // Skip search on deleted rows
      !row.__isDeleted && columns.some((col) => String(row[col] || '').toLowerCase().includes(lower))
    );
  }, [data, columns, searchText]);

  // Build table columns
  const tableCols = useMemo(() => {
    const cols = columns.map((col) => {
      const colSchema = schema[col] || {};
      const colType = colSchema.type || 'text';
      const lookupOptions = lookups[col] || colSchema.options || null;

      return {
        title: colSchema.label || col,
        dataIndex: col,
        key: col,
        width: colSchema.width || 150,
        align: ['money', 'percent', 'number'].includes(colType) ? 'right' : 'left',
        sorter: (a, b) => {
          const valA = a[col] || '';
          const valB = b[col] || '';
          if (['money', 'percent', 'number'].includes(colType)) {
            return parseFloat(valA) - parseFloat(valB);
          }
          return String(valA).localeCompare(String(valB));
        },
        render: (value, row) => {
          const isModified = modifiedRows.has(row.__key);
          
          if (editMode && !readOnly) {
            return renderEditor({
              value,
              onChange: (v) => setCell(row.__key, col, v),
              type: colType,
              options: lookupOptions,
              isModified,
            });
          }
          
          return renderCell({ value, type: colType, isModified });
        },
      };
    });

    // Add actions column if editable
    if (!readOnly) {
      cols.push({
        title: '',
        key: '__actions',
        width: 100,
        fixed: 'right',
        render: (_, row) => (
          editMode ? (
            row.__isDeleted ? (
              <Tooltip title="Desfazer exclusão">
                <Button 
                  type="text" 
                  size="small" 
                  onClick={() => undoDeleteRow(row)}
                  style={{ color: '#ef4444' }}
                >
                  Desfazer
                </Button>
              </Tooltip>
            ) : (
              <Space size="small">
                <Tooltip title="Duplicar">
                  <Button 
                    type="text" 
                    size="small" 
                    icon={<CopyOutlined />} 
                    onClick={() => duplicateRow(row)} 
                  />
                </Tooltip>
                <Tooltip title="Excluir">
                  <Button 
                    type="text" 
                    size="small" 
                    danger 
                    icon={<DeleteOutlined />} 
                    onClick={() => deleteRow(row)} 
                  />
                </Tooltip>
              </Space>
            )
          ) : null
        ),
      });
    }

    return cols;
  }, [columns, schema, lookups, editMode, readOnly, modifiedRows]);

  const hasChanges = modifiedRows.size > 0;

  return (
    <Card 
      className={`smart-table ${compact ? 'smart-table--compact' : ''}`}
      title={
        <div className="smart-table__header">
          <span className="smart-table__title">{title || resourceId}</span>
          {hasChanges && editMode && (
            <span className="smart-table__badge">{modifiedRows.size} alterações</span>
          )}
        </div>
      }
      extra={
        <Space>
          <Input
            placeholder="Buscar..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          
          {!readOnly && (
            <>
              {editMode ? (
                <>
                  <Button icon={<PlusOutlined />} onClick={addRow}>
                    Adicionar
                  </Button>
                  <Button onClick={cancelEdit}>
                    Cancelar
                  </Button>
                  <Button 
                    type="primary" 
                    icon={<SaveOutlined />} 
                    onClick={salvar} 
                    loading={saving}
                    disabled={!hasChanges}
                  >
                    Salvar
                  </Button>
                </>
              ) : (
                <Button 
                  type="primary" 
                  icon={<EditOutlined />} 
                  onClick={() => setEditMode(true)}
                >
                  Editar
                </Button>
              )}
            </>
          )}
          
          {extraActions}
          
          <Button 
            icon={<ReloadOutlined />} 
            onClick={carregar} 
            loading={loading}
          />
        </Space>
      }
    >
      {filteredData.length === 0 && !loading ? (
        <Empty description="Nenhum dado encontrado" />
      ) : (
        <Table
          columns={tableCols}
          dataSource={filteredData}
          loading={loading}
          pagination={{ 
            pageSize: 15, 
            showSizeChanger: true,
            showTotal: (total) => `${total} registros`,
          }}
          scroll={{ x: 'max-content' }}
          size="small"
          rowKey="__key"
          rowClassName={(row) => {
            if (row.__isDeleted) return 'smart-table__row--deleted';
            if (row.__isNew) return 'smart-table__row--new';
            if (modifiedRows.has(row.__key)) return 'smart-table__row--modified';
            return '';
          }}
        />
      )}
    </Card>
  );
};

export default SmartTable;
