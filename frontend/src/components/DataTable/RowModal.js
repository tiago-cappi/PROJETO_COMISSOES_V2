import React, { useState, useEffect, useMemo } from 'react';
import { Modal, Input, InputNumber, DatePicker, Button } from 'antd';
import {
  PlusOutlined,
  EyeOutlined,
  SaveOutlined,
  CloseOutlined,
  FileTextOutlined,
  DollarOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import './RowModal.css';

// ===================== FORMATTERS (shared with DataTable) =====================

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
  const displayValue = Math.abs(num) <= 1 && num !== 0 ? num * 100 : num;
  return `${displayValue.toFixed(2).replace('.', ',')}%`;
};

const formatDate = (value) => {
  if (!value) return null;
  let dateStr = String(value).trim();
  if (dateStr.includes(' ')) dateStr = dateStr.split(' ')[0];
  if (dateStr.includes('T')) dateStr = dateStr.split('T')[0];
  if (dateStr.includes('-') && dateStr.length >= 10) {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      const [year, month, day] = parts;
      if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
        return `${day.padStart(2, '0')}/${month.padStart(2, '0')}/${year}`;
      }
    }
  }
  if (dateStr.includes('/')) {
    const parts = dateStr.split('/');
    if (parts.length === 3 && parts[0].length <= 2) return dateStr;
  }
  return value;
};

const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return null;
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  return new Intl.NumberFormat('pt-BR').format(num);
};

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

// Column type detection
const detectColumnType = (colName) => {
  const lower = normalizeForCompare(colName);
  
  if (lower.includes('valor') || lower.includes('preco') || lower.includes('custo') || 
      lower.includes('receita') || lower.includes('venda') || lower.includes('faturamento') ||
      (lower.includes('margem') && !lower.includes('%')) || lower.includes('lucro') ||
      (lower.includes('total') && !lower.includes('%')) || lower.includes('orcado') ||
      (lower.includes('realizado') && !lower.includes('%'))) {
    return 'money';
  }
  
  if (lower.includes('perc') || lower.includes('taxa') || lower.includes('%') ||
      lower.includes('margem_%') || lower.includes('rentab') || lower.includes('comissao') ||
      lower.includes('meta_%') || lower.includes('ating')) {
    return 'percent';
  }
  
  if (lower.includes('data') || lower.includes('dt_') || lower === 'dt' ||
      lower.includes('date') || lower.includes('emissao') || lower.includes('vencimento') ||
      lower.includes('aceite')) {
    return 'date';
  }
  
  if (lower.includes('nf') || lower.includes('nota') || lower.includes('documento') ||
      lower.includes('pedido') || lower.includes('numero_nf')) {
    return 'nf';
  }
  
  if (lower.includes('qtd') || lower.includes('quantidade') || lower.includes('num') ||
      (lower.includes('id') && !lower.includes('codigo'))) {
    return 'number';
  }
  
  return 'text';
};

// Get percent class
const getPercentClass = (value) => {
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return '';
  const pct = Math.abs(num) <= 1 ? num * 100 : num;
  if (pct < 30) return 'row-modal__value--percent-low';
  if (pct < 70) return 'row-modal__value--percent-medium';
  return 'row-modal__value--percent-high';
};

// ===================== COMPONENT =====================

const RowModal = ({
  visible,
  onClose,
  onSave,
  columns = [],
  rowData = null,  // null = add mode, object = view/edit mode
  rowIndex = null,
  title = '',
  allowEdit = false,
  startEditing = false,
}) => {
  const [formData, setFormData] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  
  const isAddMode = rowData === null;

  // Initialize form data
  useEffect(() => {
    if (visible) {
      if (isAddMode) {
        // Initialize empty form for add mode
        const emptyData = {};
        columns.forEach(col => {
          emptyData[col] = '';
        });
        setFormData(emptyData);
        setIsEditing(true);
      } else {
        // Copy row data for view/edit
        setFormData({ ...rowData });
        setIsEditing(Boolean(startEditing && allowEdit));
      }
    }
  }, [visible, rowData, columns, isAddMode, startEditing, allowEdit]);

  // Handle field change
  const handleChange = (col, value) => {
    setFormData(prev => ({ ...prev, [col]: value }));
  };

  // Handle save
  const handleSave = () => {
    onSave(formData, isAddMode);
    onClose();
  };

  // Categorize columns by type
  const categorizedColumns = useMemo(() => {
    const categories = {
      general: { title: 'Informações Gerais', icon: <FileTextOutlined />, fields: [] },
      financial: { title: 'Valores Financeiros', icon: <DollarOutlined />, fields: [] },
      dates: { title: 'Datas', icon: <CalendarOutlined />, fields: [] },
    };

    columns.forEach(col => {
      const type = detectColumnType(col);
      const field = { name: col, type };
      
      if (type === 'money') {
        categories.financial.fields.push(field);
      } else if (type === 'percent') {
        categories.financial.fields.push(field);
      } else if (type === 'date') {
        categories.dates.fields.push(field);
      } else {
        categories.general.fields.push(field);
      }
    });

    // Filter out empty categories
    return Object.entries(categories)
      .filter(([_, cat]) => cat.fields.length > 0)
      .map(([key, cat]) => ({ key, ...cat }));
  }, [columns]);

  // Render field value (view mode)
  const renderValue = (col, value, type) => {
    if (value === null || value === undefined || value === '') {
      return <div className="row-modal__value row-modal__value--empty">—</div>;
    }

    switch (type) {
      case 'money': {
        const num = parseFloat(String(value).replace(',', '.'));
        const isNegative = !isNaN(num) && num < 0;
        return (
          <div className={`row-modal__value row-modal__value--money ${isNegative ? 'row-modal__value--money-negative' : ''}`}>
            {formatMoney(value)}
          </div>
        );
      }
      case 'percent': {
        const colorClass = getPercentClass(value);
        return (
          <div className={`row-modal__value row-modal__value--percent ${colorClass}`}>
            {formatPercent(value)}
          </div>
        );
      }
      case 'date':
        return (
          <div className="row-modal__value row-modal__value--date">
            {formatDate(value)}
          </div>
        );
      case 'number':
        return (
          <div className="row-modal__value row-modal__value--number">
            {formatNumber(value)}
          </div>
        );
      case 'nf':
        return (
          <div className="row-modal__value row-modal__value--number">
            {String(value).replace(/\./g, '')}
          </div>
        );
      default:
        return <div className="row-modal__value">{value}</div>;
    }
  };

  // Render field input (edit mode)
  const renderInput = (col, value, type) => {
    switch (type) {
      case 'money':
      case 'number':
      case 'nf':
        return (
          <div className="row-modal__input">
            <InputNumber
              value={parseFloat(String(value).replace(',', '.')) || null}
              onChange={(v) => handleChange(col, v)}
              style={{ width: '100%' }}
              decimalSeparator=","
              precision={type === 'money' ? 2 : undefined}
              placeholder={type === 'money' ? 'R$ 0,00' : '0'}
            />
          </div>
        );
      case 'percent':
        return (
          <div className="row-modal__input">
            <InputNumber
              value={parseFloat(String(value).replace(',', '.')) || null}
              onChange={(v) => handleChange(col, v)}
              style={{ width: '100%' }}
              decimalSeparator=","
              precision={2}
              addonAfter="%"
              placeholder="0,00"
            />
          </div>
        );
      case 'date': {
        const cleaned = value
          ? String(value).trim().split(' ')[0].split('T')[0]
          : '';
        const dateValue = cleaned ? dayjs(cleaned, ['YYYY-MM-DD', 'DD/MM/YYYY']) : null;
        return (
          <div className="row-modal__input">
            <DatePicker
              value={dateValue?.isValid() ? dateValue : null}
              onChange={(date) => handleChange(col, date ? date.format('YYYY-MM-DD') : '')}
              format="DD/MM/YYYY"
              style={{ width: '100%' }}
              placeholder="DD/MM/AAAA"
            />
          </div>
        );
      }
      default:
        return (
          <div className="row-modal__input">
            <Input
              value={value || ''}
              onChange={(e) => handleChange(col, e.target.value)}
              placeholder="Digite..."
            />
          </div>
        );
    }
  };

  // Render field
  const renderField = (field) => {
    const value = formData[field.name];
    const isWideField = field.type === 'text' && field.name.toLowerCase().includes('descricao');

    return (
      <div key={field.name} className={`row-modal__field ${isWideField ? 'row-modal__field--full' : ''}`}>
        <label className="row-modal__label">{field.name}</label>
        {isEditing ? renderInput(field.name, value, field.type) : renderValue(field.name, value, field.type)}
      </div>
    );
  };

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
      className="row-modal"
      closable={false}
      destroyOnClose
    >
      {/* Header */}
      <div className={`row-modal__header ${isAddMode ? 'row-modal__header--add' : ''}`}>
        <h2 className="row-modal__title">
          <span className="row-modal__title-icon">
            {isAddMode ? <PlusOutlined /> : <EyeOutlined />}
          </span>
          {isAddMode ? 'Adicionar Nova Linha' : (title || 'Detalhes do Registro')}
          {rowIndex !== null && !isAddMode && (
            <span className="row-modal__index">Linha {rowIndex + 1}</span>
          )}
        </h2>
        <p className="row-modal__subtitle">
          {isAddMode 
            ? 'Preencha os campos abaixo para adicionar um novo registro'
            : isEditing 
              ? 'Edite os campos abaixo e salve as alterações'
              : 'Visualize os dados deste registro'
          }
        </p>
      </div>

      {/* Content */}
      <div className="row-modal__content">
        {categorizedColumns.map(category => (
          <div key={category.key} className="row-modal__section">
            <h3 className="row-modal__section-title">
              <span className="row-modal__section-icon">{category.icon}</span>
              {category.title}
            </h3>
            <div className="row-modal__fields">
              {category.fields.map(renderField)}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="row-modal__actions">
        <Button 
          className="row-modal__btn"
          icon={<CloseOutlined />}
          onClick={onClose}
        >
          {isEditing && !isAddMode ? 'Cancelar' : 'Fechar'}
        </Button>
        
        {!isAddMode && !isEditing && allowEdit && (
          <Button 
            type="primary"
            className="row-modal__btn row-modal__btn--primary"
            onClick={() => setIsEditing(true)}
          >
            Editar
          </Button>
        )}
        
        {isEditing && (
          <Button 
            type="primary"
            className={`row-modal__btn ${isAddMode ? 'row-modal__btn--add' : 'row-modal__btn--primary'}`}
            icon={isAddMode ? <PlusOutlined /> : <SaveOutlined />}
            onClick={handleSave}
          >
            {isAddMode ? 'Adicionar' : 'Salvar'}
          </Button>
        )}
      </div>
    </Modal>
  );
};

export default RowModal;
