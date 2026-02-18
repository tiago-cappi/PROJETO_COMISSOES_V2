import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  Table,
  Select,
  Button,
  Space,
  message,
  Alert,
  Tag,
  Typography,
  Spin,
} from 'antd';
import { 
  ExclamationCircleOutlined, 
  TeamOutlined,
  CheckCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const { Option } = Select;
const { Text } = Typography;

/**
 * Modal para preenchimento de atribuições obrigatórias pendentes.
 * 
 * Exibe hierarquias com cargos obrigatórios faltantes e permite preenchimento
 * rápido antes de re-executar o cálculo.
 * 
 * Props:
 * - open: boolean - controla visibilidade
 * - onCancel: function - callback ao fechar
 * - onSaved: function - callback após salvar com sucesso (para re-executar cálculo)
 * - missingData: array - lista de hierarquias com atribuições pendentes
 */
const MissingAssignmentsModal = ({ 
  open, 
  onCancel, 
  onSaved,
  missingData = [] 
}) => {
  const [colaboradoresOptions, setColaboradoresOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [assignments, setAssignments] = useState({});

  // Carregar colaboradores ao abrir o modal
  useEffect(() => {
    if (open) {
      loadColaboradores();
      // Inicializar assignments vazio
      setAssignments({});
    }
  }, [open]);

  const loadColaboradores = async () => {
    setLoading(true);
    try {
      const response = await regrasAPI.lerAba('COLABORADORES', { allPages: true });
      const colabData = response.data?.data || [];
      const colabs = colabData.map((r) => ({
        nome: r.nome_colaborador,
        cargo: r.cargo
      })).filter(c => c.nome);
      setColaboradoresOptions(colabs);
    } catch (error) {
      console.error('Erro ao carregar colaboradores:', error);
      message.error('Erro ao carregar lista de colaboradores');
    } finally {
      setLoading(false);
    }
  };

  // Cargos obrigatórios (os que bloqueiam o cálculo)
  const MANDATORY_SLOTS = [
    'Gerente Linha 1',
    'Gerente Linha 2',
    'Coordenador 1',
    'Coordenador 2'
  ];

  // Mapeamento de slot para cargo real
  const SLOT_TO_CARGO = {
    'Gerente Linha 1': 'Gerente de Linha',
    'Gerente Linha 2': 'Gerente de Linha',
    'Coordenador 1': 'Coordenador',
    'Coordenador 2': 'Coordenador',
  };

  // Processar dados para a tabela
  const tableData = useMemo(() => {
    return missingData.map((item, index) => ({
      key: index,
      linha: item.linha,
      grupo: item.grupo,
      subgrupo: item.subgrupo,
      tipo_mercadoria: item.tipo_mercadoria,
      motivo: item.motivo,
      missing_slots: item.missing_slots || [],
    }));
  }, [missingData]);

  // Contar quantos slots faltam no total
  const totalMissingSlots = useMemo(() => {
    return tableData.reduce((acc, row) => {
      const mandatoryMissing = row.missing_slots.filter(slot => 
        MANDATORY_SLOTS.includes(slot)
      );
      return acc + mandatoryMissing.length;
    }, 0);
  }, [tableData]);

  // Verificar se todos os slots obrigatórios foram preenchidos
  const allFilled = useMemo(() => {
    for (const row of tableData) {
      const mandatoryMissing = row.missing_slots.filter(slot => 
        MANDATORY_SLOTS.includes(slot)
      );
      for (const slot of mandatoryMissing) {
        const key = `${row.key}_${slot}`;
        if (!assignments[key]) {
          return false;
        }
      }
    }
    return tableData.length > 0;
  }, [tableData, assignments]);

  // Handler para mudança de select
  const handleAssignmentChange = (rowKey, slot, value) => {
    setAssignments(prev => ({
      ...prev,
      [`${rowKey}_${slot}`]: value
    }));
  };

  // Filtrar colaboradores por cargo
  const getFilteredColaboradores = (slot) => {
    const targetCargo = SLOT_TO_CARGO[slot];
    if (!targetCargo) return colaboradoresOptions;
    return colaboradoresOptions.filter(c => c.cargo === targetCargo);
  };

  // Salvar as atribuições
  const handleSave = async () => {
    setSaving(true);
    try {
      // 1. Carregar dados atuais de ATRIBUICOES
      const currentResp = await regrasAPI.lerAba('ATRIBUICOES', { allPages: true });
      const currentData = currentResp.data?.data || [];
      
      // 2. Criar mapa para atualização
      const updatedData = [...currentData];
      
      // 3. Processar cada hierarquia com atribuições pendentes
      for (const row of tableData) {
        // Encontrar ou criar registro na tabela de atribuições
        let existingIndex = updatedData.findIndex(r => 
          r.linha === row.linha &&
          r.grupo === row.grupo &&
          r.subgrupo === row.subgrupo &&
          r.tipo_mercadoria === row.tipo_mercadoria
        );
        
        let record;
        if (existingIndex >= 0) {
          record = { ...updatedData[existingIndex] };
        } else {
          // Criar novo registro
          record = {
            linha: row.linha,
            grupo: row.grupo,
            subgrupo: row.subgrupo,
            tipo_mercadoria: row.tipo_mercadoria,
            fator_split_gerente: 50,
            fator_split_coordenador: 50,
          };
          existingIndex = updatedData.length;
          updatedData.push(record);
        }
        
        // 4. Preencher os slots com as atribuições selecionadas
        for (const slot of row.missing_slots) {
          if (!MANDATORY_SLOTS.includes(slot)) continue;
          
          const key = `${row.key}_${slot}`;
          const selectedColab = assignments[key];
          
          if (selectedColab) {
            record[slot] = selectedColab;
          }
        }
        
        // Atualizar o registro
        if (existingIndex < currentData.length) {
          updatedData[existingIndex] = record;
        }
      }
      
      // 5. Salvar via API
      await regrasAPI.salvarAba('ATRIBUICOES', updatedData, true);
      
      message.success('Atribuições salvas com sucesso!');
      
      // 6. Chamar callback para re-executar cálculo
      if (onSaved) {
        onSaved();
      }
      
    } catch (error) {
      console.error('Erro ao salvar atribuições:', error);
      message.error('Erro ao salvar atribuições: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  // Colunas da tabela
  const columns = [
    {
      title: 'Linha',
      dataIndex: 'linha',
      key: 'linha',
      width: 120,
    },
    {
      title: 'Grupo',
      dataIndex: 'grupo',
      key: 'grupo',
      width: 120,
    },
    {
      title: 'Subgrupo',
      dataIndex: 'subgrupo',
      key: 'subgrupo',
      width: 120,
    },
    {
      title: 'Tipo Mercadoria',
      dataIndex: 'tipo_mercadoria',
      key: 'tipo_mercadoria',
      width: 130,
    },
    {
      title: 'Cargos Pendentes',
      key: 'assignments',
      width: 500,
      render: (_, record) => {
        const mandatoryMissing = record.missing_slots.filter(slot => 
          MANDATORY_SLOTS.includes(slot)
        );
        
        if (mandatoryMissing.length === 0) {
          return <Tag color="green">✓ Completo</Tag>;
        }
        
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            {mandatoryMissing.map(slot => {
              const key = `${record.key}_${slot}`;
              const options = getFilteredColaboradores(slot);
              const isFilled = !!assignments[key];
              
              return (
                <Space key={slot} align="center">
                  <Text type="secondary" style={{ width: 120, display: 'inline-block' }}>
                    {slot}:
                  </Text>
                  <Select
                    style={{ width: 250 }}
                    placeholder={`Selecione ${slot}`}
                    value={assignments[key] || undefined}
                    onChange={(value) => handleAssignmentChange(record.key, slot, value)}
                    showSearch
                    optionFilterProp="children"
                    status={isFilled ? '' : 'warning'}
                  >
                    {options.map(c => (
                      <Option key={c.nome} value={c.nome}>
                        {c.nome}
                      </Option>
                    ))}
                  </Select>
                  {isFilled && (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  )}
                </Space>
              );
            })}
          </Space>
        );
      },
    },
  ];

  return (
    <Modal
      title={
        <Space>
          <ExclamationCircleOutlined style={{ color: '#faad14' }} />
          <span>Atribuições Pendentes</span>
          <Tag color="orange">{missingData.length} hierarquias</Tag>
        </Space>
      }
      open={open}
      onCancel={onCancel}
      width={1100}
      footer={
        <Space>
          <Button onClick={onCancel}>
            Cancelar
          </Button>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleSave}
            loading={saving}
            disabled={!allFilled || loading}
          >
            Salvar e Re-executar Cálculo
          </Button>
        </Space>
      }
      destroyOnClose
    >
      <Alert
        message="Hierarquias com cargos obrigatórios não preenchidos"
        description={
          <span>
            O cálculo de comissões não pode prosseguir pois existem <strong>{totalMissingSlots}</strong> cargos 
            obrigatórios não preenchidos em <strong>{missingData.length}</strong> hierarquias. 
            Preencha os campos abaixo para continuar.
          </span>
        }
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" tip="Carregando colaboradores..." />
        </div>
      ) : (
        <Table
          columns={columns}
          dataSource={tableData}
          pagination={false}
          scroll={{ y: 400, x: 'max-content' }}
          size="small"
          bordered
        />
      )}
    </Modal>
  );
};

export default MissingAssignmentsModal;
