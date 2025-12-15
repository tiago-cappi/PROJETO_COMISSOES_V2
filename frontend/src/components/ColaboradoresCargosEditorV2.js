import React, { useEffect, useState } from 'react';
import { Card, Tabs, message } from 'antd';
import SmartTable from './SmartTable';
import { regrasAPI } from '../services/api';

/**
 * Colaboradores e Cargos Editor - Refactored with SmartTable
 */

// API Adapter for SmartTable
const regrasApiAdapter = {
  read: (id, params) => regrasAPI.lerAba(id, params),
  save: (id, data) => regrasAPI.salvarAba(id, data, true),
};

// Schema definitions for each sheet
const schemas = {
  COLABORADORES: {
    id_colaborador: { 
      label: 'ID', 
      type: 'text', 
      width: 80,
      required: true,
    },
    nome_colaborador: { 
      label: 'Nome', 
      type: 'text', 
      width: 200,
      required: true,
    },
    cargo: { 
      label: 'Cargo', 
      type: 'select',  // Will be populated with lookups
      width: 180,
    },
  },
  CARGOS: {
    cargo: { 
      label: 'Cargo', 
      type: 'text', 
      width: 180,
      required: true,
    },
    nivel: { 
      label: 'Nível Hierárquico', 
      type: 'number', 
      width: 120,
    },
    descricao: { 
      label: 'Descrição', 
      type: 'text', 
      width: 300,
    },
  },
};

const ColaboradoresCargosEditor = () => {
  const [cargosOptions, setCargosOptions] = useState([]);
  
  // Load cargos for dropdown
  useEffect(() => {
    const loadCargos = async () => {
      try {
        const resp = await regrasAPI.lerAba('CARGOS', { allPages: true });
        const cargos = (resp.data?.data || []).map((row) => row.cargo).filter(Boolean);
        setCargosOptions(cargos);
      } catch (e) {
        message.error('Erro ao carregar lista de cargos');
      }
    };
    loadCargos();
  }, []);

  const items = [
    {
      key: 'colabs',
      label: 'Colaboradores',
      children: (
        <SmartTable
          resourceId="COLABORADORES"
          apiService={regrasApiAdapter}
          title="Colaboradores"
          schema={schemas.COLABORADORES}
          lookups={{ cargo: cargosOptions }}
        />
      ),
    },
    {
      key: 'cargos',
      label: 'Cargos',
      children: (
        <SmartTable
          resourceId="CARGOS"
          apiService={regrasApiAdapter}
          title="Cargos"
          schema={schemas.CARGOS}
        />
      ),
    },
  ];

  return (
    <Card style={{ border: 'none', boxShadow: 'none' }}>
      <Tabs items={items} />
    </Card>
  );
};

export default ColaboradoresCargosEditor;
