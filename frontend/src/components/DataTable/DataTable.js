import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { 
  Table, 
  Button, 
  Input, 
  InputNumber,
  DatePicker,
  message, 
  Modal, 
  Tooltip,
  Empty
} from 'antd';
import { 
  ReloadOutlined, 
  SaveOutlined, 
  PlusOutlined, 
  CopyOutlined, 
  DeleteOutlined,
  SearchOutlined,
  EditOutlined,
  EyeOutlined,
  FileExcelOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import RowModal from './RowModal';
import './DataTable.css';

// ===================== FORMATTERS =====================

const formatMoney = (value) => {
  if (value === null || value === undefined || value === '') return null;
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(num);
};

const formatPercent = (value) => {
  if (value === null || value === undefined || value === '') return null;
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  // Assume values > 1 are already percentage, <= 1 need *100
  const displayValue = Math.abs(num) <= 1 && num !== 0 ? num * 100 : num;
  return `${displayValue.toFixed(2).replace('.', ',')}%`;
};

const formatDate = (value) => {
  if (!value) return null;
  
  let dateStr = String(value).trim();
  
  // Remove time portion if present (handles "2023-10-01 00:00:00" format)
  if (dateStr.includes(' ')) {
    dateStr = dateStr.split(' ')[0];
  }
  
  // Handle ISO format with T (2023-10-01T00:00:00)
  if (dateStr.includes('T')) {
    dateStr = dateStr.split('T')[0];
  }
  
  // Parse YYYY-MM-DD format
  if (dateStr.includes('-') && dateStr.length >= 10) {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      const [year, month, day] = parts;
      // Validate parts are numeric
      if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
        return `${day.padStart(2, '0')}/${month.padStart(2, '0')}/${year}`;
      }
    }
  }
  
  // Already in DD/MM/YYYY format
  if (dateStr.includes('/')) {
    // Check if it's a valid date format, not corrupted
    const parts = dateStr.split('/');
    if (parts.length === 3 && parts[0].length <= 2) {
      return dateStr;
    }
  }
  
  return value;
};

const formatNumber = (value, useGrouping = true) => {
  if (value === null || value === undefined || value === '') return null;
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  // If it's an integer (like NF number), don't use grouping
  if (Number.isInteger(num) && !useGrouping) {
    return String(Math.round(num));
  }
  return new Intl.NumberFormat('pt-BR').format(num);
};

// Detect column type based on name
const normalizeForCompare = (text) => {
  try {
    return String(text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  } catch {
    return String(text || '').toLowerCase();
  }
};

const detectColumnType = (colName) => {
  const lower = normalizeForCompare(colName);
  
  // Money detection
  if (lower.includes('valor') || lower.includes('preco') || lower.includes('custo') || 
      lower.includes('receita') || lower.includes('venda') || lower.includes('faturamento') ||
      (lower.includes('margem') && !lower.includes('%')) || lower.includes('lucro') ||
      (lower.includes('total') && !lower.includes('%')) || lower.includes('orcado') ||
      (lower.includes('realizado') && !lower.includes('%'))) {
    return 'money';
  }
  
  // Percent detection
  if (lower.includes('perc') || lower.includes('taxa') || lower.includes('%') ||
      lower.includes('margem_%') || lower.includes('rentab') || lower.includes('comissao') ||
      lower.includes('meta_%') || lower.includes('ating')) {
    return 'percent';
  }
  
  // Date detection
  if (lower.includes('data') || lower.includes('dt_') || lower === 'dt' ||
      lower.includes('date') || lower.includes('emissao') || lower.includes('vencimento')) {
    return 'date';
  }
  
  // NF/Document number detection (no thousand separator)
  if (lower.includes('nf') || lower.includes('nota') || lower.includes('documento') ||
      lower.includes('pedido') || lower.includes('numero_nf')) {
    return 'nf';
  }
  
  // Number detection
  if (lower.includes('qtd') || lower.includes('quantidade') || lower.includes('num') ||
      (lower.includes('id') && !lower.includes('codigo'))) {
    return 'number';
  }
  
  return 'text';
};

// Get percent color class
const getPercentClass = (value) => {
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return '';
  const pct = Math.abs(num) <= 1 ? num * 100 : num;
  if (pct < 30) return 'dt-cell--percent-low';
  if (pct < 70) return 'dt-cell--percent-medium';
  return 'dt-cell--percent-high';
};

// ===================== COMPONENT =====================

const DataTable = ({ 
  resourceId, 
  apiService, 
  title,
  icon,
  subtitle,
  readOnly = false,
}) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [modifiedRows, setModifiedRows] = useState(new Set());
  
  // Modal states
  const [modalVisible, setModalVisible] = useState(false);
  const [modalRow, setModalRow] = useState(null);
  const [modalRowIndex, setModalRowIndex] = useState(null);

  // Load data
  const carregar = useCallback(async () => {
    if (!resourceId || !apiService) return;
    
    setLoading(true);
    try {
      const resp = await apiService.read(resourceId, { allPages: true });
      const arr = resp.data?.data || [];
      setData(arr.map((row, idx) => ({ 
        __key: `row_${idx}`, 
        __original: { ...row }, 
        __isNew: false,
        ...row 
      })));
      setColumns(resp.data?.columns || Object.keys(arr[0] || {}));
      setModifiedRows(new Set());
    } catch (e) {
      message.error(`Erro ao carregar: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [resourceId, apiService]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // Cell update
  const setCell = (rowKey, col, value) => {
    setData((prev) => prev.map((r) => {
      if (r.__key === rowKey) {
        setModifiedRows((m) => new Set(m).add(rowKey));
        return { ...r, [col]: value };
      }
      return r;
    }));
  };

  // Open modal to add new row
  const openAddModal = () => {
    setModalRow(null);
    setModalRowIndex(null);
    setModalVisible(true);
  };

  // Open modal to view/edit existing row
  const openRowModal = (row, index) => {
    // Extract only the data columns (exclude internal keys)
    const { __key, __original, __isNew, ...rowData } = row;
    setModalRow(rowData);
    setModalRowIndex(index);
    setModalVisible(true);
  };

  // Handle modal save
  const handleModalSave = (formData, isAddMode) => {
    if (isAddMode) {
      // Add new row
      const key = `new_${Date.now()}`;
      setData((prev) => [...prev, { __key: key, __original: null, __isNew: true, ...formData }]);
      setModifiedRows((m) => new Set(m).add(key));
      message.success('Nova linha adicionada');
    } else {
      // Update existing row
      const targetKey = data[modalRowIndex]?.__key;
      if (targetKey) {
        setData((prev) => prev.map((r) => {
          if (r.__key === targetKey) {
            setModifiedRows((m) => new Set(m).add(targetKey));
            return { ...r, ...formData };
          }
          return r;
        }));
        message.success('Linha atualizada');
      }
    }
  };

  // Duplicate row
  const duplicateRow = (row) => {
    const key = `dup_${Date.now()}`;
    const { __key, __original, __isNew, ...rest } = row;
    setData((prev) => [...prev, { __key: key, __original: null, __isNew: true, ...rest }]);
    setModifiedRows((m) => new Set(m).add(key));
  };

  // Delete row
  const deleteRow = (row) => {
    Modal.confirm({
      title: 'Excluir linha',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta ação não pode ser desfeita.',
      okText: 'Excluir',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: () => {
        setData((prev) => prev.filter((r) => r.__key !== row.__key));
        setModifiedRows((m) => {
          const newSet = new Set(m);
          newSet.delete(row.__key);
          return newSet;
        });
      },
    });
  };

  // Save
  const salvar = async () => {
    setSaving(true);
    try {
      const payload = data.map(({ __key, __original, __isNew, ...rest }) => rest);
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

  // Cancel edit
  const cancelEdit = () => {
    if (modifiedRows.size > 0) {
      Modal.confirm({
        title: 'Descartar alterações?',
        icon: <ExclamationCircleOutlined />,
        content: `Você tem ${modifiedRows.size} alteração(ões) não salva(s).`,
        okText: 'Descartar',
        okType: 'danger',
        cancelText: 'Continuar editando',
        onOk: () => {
          carregar();
          setEditMode(false);
        },
      });
    } else {
      setEditMode(false);
    }
  };

  // Filter data
  const filteredData = useMemo(() => {
    if (!searchText) return data;
    const lower = searchText.toLowerCase();
    return data.filter((row) =>
      columns.some((col) => String(row[col] || '').toLowerCase().includes(lower))
    );
  }, [data, columns, searchText]);

  // Render cell (view mode)
  const renderViewCell = (value, type) => {
    if (value === null || value === undefined || value === '') {
      return <span className="dt-cell dt-cell--empty">—</span>;
    }

    switch (type) {
      case 'money': {
        const formatted = formatMoney(value);
        const num = parseFloat(String(value).replace(',', '.'));
        const isNegative = !isNaN(num) && num < 0;
        return (
          <span className={`dt-cell dt-cell--money ${isNegative ? 'dt-cell--money-negative' : ''}`}>
            {formatted}
          </span>
        );
      }
      case 'percent': {
        const formatted = formatPercent(value);
        const colorClass = getPercentClass(value);
        return (
          <span className={`dt-cell dt-cell--percent ${colorClass}`}>
            {formatted}
          </span>
        );
      }
      case 'date':
        return <span className="dt-cell dt-cell--date">{formatDate(value)}</span>;
      case 'nf':
        return <span className="dt-cell dt-cell--number">{formatNumber(value, false)}</span>;
      case 'number':
        return <span className="dt-cell dt-cell--number">{formatNumber(value)}</span>;
      default:
        return <span className="dt-cell dt-cell--text">{value}</span>;
    }
  };

  // Render cell (edit mode)
  const renderEditCell = (value, type, rowKey, col, isModified) => {
    const wrapperClass = `dt-editor ${isModified ? 'dt-editor--modified' : ''}`;

    switch (type) {
      case 'money':
      case 'number':
      case 'nf':
        return (
          <div className={wrapperClass}>
            <InputNumber
              value={parseFloat(String(value).replace(',', '.')) || null}
              onChange={(v) => setCell(rowKey, col, v)}
              style={{ width: '100%' }}
              size="small"
              decimalSeparator=","
              precision={type === 'money' ? 2 : undefined}
            />
          </div>
        );
      case 'percent':
        return (
          <div className={wrapperClass}>
            <InputNumber
              value={parseFloat(String(value).replace(',', '.')) || null}
              onChange={(v) => setCell(rowKey, col, v)}
              style={{ width: '100%' }}
              size="small"
              decimalSeparator=","
              precision={2}
              addonAfter="%"
            />
          </div>
        );
      case 'date': {
        const dateValue = value ? dayjs(value, ['YYYY-MM-DD', 'DD/MM/YYYY']) : null;
        return (
          <div className={wrapperClass}>
            <DatePicker
              value={dateValue?.isValid() ? dateValue : null}
              onChange={(date) => setCell(rowKey, col, date ? date.format('YYYY-MM-DD') : '')}
              format="DD/MM/YYYY"
              style={{ width: '100%' }}
              size="small"
            />
          </div>
        );
      }
      default:
        return (
          <div className={wrapperClass}>
            <Input
              value={value || ''}
              onChange={(e) => setCell(rowKey, col, e.target.value)}
              size="small"
            />
          </div>
        );
    }
  };

  // Build columns
  const tableCols = useMemo(() => {
    const cols = columns.map((col) => {
      const type = detectColumnType(col);
      const isNumeric = ['money', 'percent', 'number', 'nf'].includes(type);
      
      return {
        title: col,
        dataIndex: col,
        key: col,
        width: type === 'money' ? 140 : type === 'date' ? 120 : type === 'percent' ? 110 : type === 'nf' ? 100 : 160,
        align: isNumeric ? 'right' : 'left',
        sorter: (a, b) => {
          const valA = a[col] || '';
          const valB = b[col] || '';
          if (isNumeric) {
            return parseFloat(String(valA).replace(',', '.')) - parseFloat(String(valB).replace(',', '.'));
          }
          return String(valA).localeCompare(String(valB));
        },
        render: (value, row) => {
          const isModified = modifiedRows.has(row.__key);
          
          if (editMode && !readOnly) {
            return renderEditCell(value, type, row.__key, col, isModified);
          }
          
          return renderViewCell(value, type);
        },
      };
    });

    // Actions column (only in edit mode)
    if (editMode && !readOnly) {
      cols.push({
        title: '',
        key: '__actions',
        width: 80,
        fixed: 'right',
        render: (_, row) => (
          <div className="dt-row-actions">
            <Tooltip title="Duplicar linha">
              <Button 
                type="text" 
                size="small" 
                icon={<CopyOutlined />} 
                onClick={() => duplicateRow(row)} 
              />
            </Tooltip>
            <Tooltip title="Excluir linha">
              <Button 
                type="text" 
                size="small" 
                danger 
                icon={<DeleteOutlined />} 
                onClick={() => deleteRow(row)} 
              />
            </Tooltip>
          </div>
        ),
      });
    }

    return cols;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns, editMode, readOnly, modifiedRows, data]);

  const hasChanges = modifiedRows.size > 0;

  return (
    <div className={`data-table ${loading ? 'data-table--loading' : ''}`}>
      {/* Header */}
      <div className="data-table__header">
        <div className="data-table__title-area">
          <div className="data-table__icon">
            {icon || <FileExcelOutlined />}
          </div>
          <div>
            <h3 className="data-table__title">
              {title || resourceId}
              {hasChanges && editMode && (
                <span className="data-table__badge">
                  {modifiedRows.size} alteração(ões)
                </span>
              )}
            </h3>
            {subtitle && <div className="data-table__subtitle">{subtitle}</div>}
          </div>
        </div>

        <div className="data-table__toolbar">
          {/* Search */}
          <div className="data-table__search">
            <Input
              placeholder="Buscar..."
              prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </div>

          {/* Mode Toggle */}
          {!readOnly && (
            <Button
              type={editMode ? 'primary' : 'default'}
              className={`data-table__mode-toggle ${editMode ? 'data-table__mode-toggle--edit' : 'data-table__mode-toggle--view'}`}
              icon={editMode ? <EditOutlined /> : <EyeOutlined />}
              onClick={() => editMode ? cancelEdit() : setEditMode(true)}
            >
              {editMode ? 'Modo Edição' : 'Editar Dados'}
            </Button>
          )}

          {/* Actions */}
          <div className="data-table__actions">
            {!readOnly && (
              <Button 
                type="primary"
                icon={<PlusOutlined />} 
                onClick={openAddModal}
                className="data-table__btn data-table__btn--add"
              >
                Adicionar
              </Button>
            )}
            {editMode && !readOnly && (
              <Button 
                className="data-table__btn data-table__btn--primary"
                icon={<SaveOutlined />} 
                onClick={salvar} 
                loading={saving}
                disabled={!hasChanges}
              >
                Salvar
              </Button>
            )}
            <Tooltip title="Recarregar dados">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={carregar} 
                loading={loading}
              />
            </Tooltip>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="data-table__content">
        {filteredData.length === 0 && !loading ? (
          <div className="data-table__empty">
            <Empty 
              description="Nenhum dado encontrado" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </div>
        ) : (
          <Table
            columns={tableCols}
            dataSource={filteredData}
            loading={loading}
            pagination={{ 
              pageSize: 20, 
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50', '100'],
              showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} registros`,
            }}
            scroll={{ x: 'max-content' }}
            size="small"
            rowKey="__key"
            rowClassName={(row) => {
              let classes = 'data-table__row--clickable';
              if (row.__isNew) classes += ' data-table__row--new';
              else if (modifiedRows.has(row.__key)) classes += ' data-table__row--modified';
              return classes;
            }}
            onRow={(record, index) => ({
              onClick: (e) => {
                // Don't open modal if clicking on action buttons
                if (e.target.closest('.dt-row-actions') || e.target.closest('.ant-btn')) return;
                openRowModal(record, index);
              },
            })}
          />
        )}
      </div>

      {/* Footer Stats */}
      <div className="data-table__footer">
        <div className="data-table__stats">
          <div className="data-table__stat">
            <span>Total:</span>
            <span className="data-table__stat-value">{data.length} linhas</span>
          </div>
          <div className="data-table__stat">
            <span>Colunas:</span>
            <span className="data-table__stat-value">{columns.length}</span>
          </div>
        </div>
        {editMode && (
          <div className="data-table__stats">
            <div className="data-table__stat">
              <span>Modo:</span>
              <span className="data-table__stat-value" style={{ color: '#f59e0b' }}>
                Edição
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Row Modal (Add/View/Edit) */}
      <RowModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onSave={handleModalSave}
        columns={columns}
        rowData={modalRow}
        rowIndex={modalRowIndex}
        title={title}
        allowEdit={editMode && !readOnly}
        startEditing={editMode && !readOnly}
      />
    </div>
  );
};

export default DataTable;
