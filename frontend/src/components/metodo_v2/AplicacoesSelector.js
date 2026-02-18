import React from 'react';
import { Select, Tag, Space, Typography } from 'antd';

const { Text } = Typography;

/**
 * Componente para seleção de múltiplas aplicações.
 * Usado para vincular aplicações da coluna 'Aplicação Mat./Serv.' a um colaborador.
 */
const AplicacoesSelector = ({
  value = [],
  onChange,
  aplicacoesDisponiveis = [],
  loading = false,
  disabled = false,
  placeholder = 'Selecione as aplicações...',
}) => {
  // Cores para as tags baseadas no índice
  const tagColors = [
    'blue', 'green', 'orange', 'purple', 'cyan', 
    'magenta', 'gold', 'lime', 'geekblue', 'volcano'
  ];

  const getTagColor = (index) => tagColors[index % tagColors.length];

  const handleChange = (selectedValues) => {
    if (onChange) {
      onChange(selectedValues);
    }
  };

  // Custom tag render para melhor visualização
  const tagRender = (props) => {
    const { label, closable, onClose } = props;
    const index = value.indexOf(label);
    const color = getTagColor(index);

    return (
      <Tag
        color={color}
        closable={closable}
        onClose={onClose}
        style={{ marginRight: 3, marginBottom: 2 }}
      >
        {label}
      </Tag>
    );
  };

  return (
    <div className="aplicacoes-selector">
      <Select
        mode="multiple"
        allowClear
        style={{ width: '100%' }}
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        loading={loading}
        disabled={disabled}
        tagRender={tagRender}
        optionFilterProp="children"
        filterOption={(input, option) =>
          (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
        }
        maxTagCount="responsive"
      >
        {aplicacoesDisponiveis.map((app) => (
          <Select.Option key={app} value={app}>
            {app}
          </Select.Option>
        ))}
      </Select>
      
      {value.length > 0 && (
        <div style={{ marginTop: 4 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {value.length} aplicação(ões) selecionada(s)
          </Text>
        </div>
      )}
    </div>
  );
};

export default AplicacoesSelector;
