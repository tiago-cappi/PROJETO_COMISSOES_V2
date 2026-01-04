import React from 'react';
import { Input, InputNumber, Select, DatePicker } from 'antd';
import dayjs from 'dayjs';
import './cellRenderers.css';

/**
 * Cell Renderers - Display formatted values in read mode
 */

// Helper to determine color intensity based on percentage (RED scale)
const getPercentColor = (value) => {
  const num = parseFloat(value);
  if (isNaN(num)) return 'inherit';
  
  // Scale from light pink (0%) to deep red (100%)
  const intensity = Math.min(100, Math.max(0, num));
  const hue = 0; // Red hue
  const saturation = 70;
  const lightness = 90 - (intensity * 0.45); // 90% at 0, 45% at 100
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

// Format number as Brazilian currency
const formatMoney = (value) => {
  if (value === null || value === undefined || value === '') return '-';
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(num);
};

// Format number as percentage
const formatPercent = (value) => {
  if (value === null || value === undefined || value === '') return '-';
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  
  // If value is already in 0-1 range (like 0.05), multiply by 100
  const displayValue = num <= 1 && num > 0 ? num * 100 : num;
  return `${displayValue.toFixed(2).replace('.', ',')}%`;
};

// Format date as DD/MM/YYYY
const formatDate = (value) => {
  if (!value) return '-';
  
  // Handle various date formats
  if (typeof value === 'string') {
    // Try ISO format first
    if (value.includes('-')) {
      const [year, month, day] = value.split('T')[0].split('-');
      if (year && month && day) {
        return `${day}/${month}/${year}`;
      }
    }
    // Already in DD/MM/YYYY format
    if (value.includes('/')) {
      return value;
    }
  }
  
  return value;
};

// Format generic number
const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') return '-';
  const num = parseFloat(String(value).replace(',', '.'));
  if (isNaN(num)) return value;
  return new Intl.NumberFormat('pt-BR').format(num);
};

/**
 * Render a cell in READ mode
 */
export const renderCell = ({ value, type, isModified }) => {
  const baseClass = `cell-value ${isModified ? 'cell-value--modified' : ''}`;
  
  switch (type) {
    case 'money':
      return (
        <span className={`${baseClass} cell-value--money`}>
          {formatMoney(value)}
        </span>
      );
      
    case 'percent':
      const bgColor = getPercentColor(value);
      return (
        <span 
          className={`${baseClass} cell-value--percent`}
          style={{ backgroundColor: bgColor }}
        >
          {formatPercent(value)}
        </span>
      );
      
    case 'date':
      return (
        <span className={`${baseClass} cell-value--date`}>
          {formatDate(value)}
        </span>
      );
      
    case 'number':
      return (
        <span className={`${baseClass} cell-value--number`}>
          {formatNumber(value)}
        </span>
      );
      
    case 'tag':
      return (
        <span className={`${baseClass} cell-value--tag`}>
          {value || '-'}
        </span>
      );
      
    default:
      return (
        <span className={baseClass}>
          {value || '-'}
        </span>
      );
  }
};

/**
 * Render a cell in EDIT mode
 */
export const renderEditor = ({ value, onChange, type, options, isModified }) => {
  const wrapperClass = `cell-editor ${isModified ? 'cell-editor--modified' : ''}`;
  
  switch (type) {
    case 'money':
      return (
        <div className={wrapperClass}>
          <InputNumber
            value={parseFloat(value) || 0}
            onChange={onChange}
            formatter={(val) => `R$ ${val}`.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
            parser={(val) => val.replace(/R\$\s?|(\.)/g, '').replace(',', '.')}
            style={{ width: '100%' }}
            size="small"
          />
        </div>
      );
      
    case 'percent':
      return (
        <div className={wrapperClass}>
          <InputNumber
            value={parseFloat(value) || 0}
            onChange={onChange}
            min={0}
            max={100}
            formatter={(val) => `${val}%`}
            parser={(val) => val.replace('%', '')}
            style={{ width: '100%' }}
            size="small"
          />
        </div>
      );
      
    case 'number':
      return (
        <div className={wrapperClass}>
          <InputNumber
            value={parseFloat(value) || 0}
            onChange={onChange}
            style={{ width: '100%' }}
            size="small"
          />
        </div>
      );
      
    case 'date':
      const dateValue = value ? dayjs(value, ['YYYY-MM-DD', 'DD/MM/YYYY']) : null;
      return (
        <div className={wrapperClass}>
          <DatePicker
            value={dateValue?.isValid() ? dateValue : null}
            onChange={(date) => onChange(date ? date.format('YYYY-MM-DD') : '')}
            format="DD/MM/YYYY"
            style={{ width: '100%' }}
            size="small"
          />
        </div>
      );
      
    case 'select':
      return (
        <div className={wrapperClass}>
          <Select
            value={value || undefined}
            onChange={onChange}
            options={(options || []).map((opt) => 
              typeof opt === 'string' ? { label: opt, value: opt } : opt
            )}
            style={{ width: '100%' }}
            size="small"
            showSearch
            allowClear
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
          />
        </div>
      );
      
    default:
      return (
        <div className={wrapperClass}>
          <Input
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            size="small"
          />
        </div>
      );
  }
};
