import React, { useEffect, useState } from 'react';
import { Card, Tabs, message } from 'antd';
import PesosMetasEditor from '../components/PesosMetasEditorV2';
import ConfigComissaoEditor from '../components/ConfigComissaoEditorV2';
import MetasEditor from '../components/MetasEditorV2';
import ColaboradoresCargosEditor from '../components/ColaboradoresCargosEditorV2';
import HierarquiaEditor from '../components/HierarquiaEditorV2';
import SmartTable from '../components/SmartTable';
import { regrasAPI } from '../services/api';

const RegrasPage = () => {
  const [colaboradoresOptions, setColaboradoresOptions] = useState([]);
  const [cargosOptions, setCargosOptions] = useState([]);
  const [linhasOptions, setLinhasOptions] = useState([]);
  
  // Load lookup data on mount
  useEffect(() => {
    const loadLookups = async () => {
      try {
        const [colabResp, cargosResp, hierResp] = await Promise.all([
          regrasAPI.lerAba('COLABORADORES', { allPages: true }),
          regrasAPI.lerAba('CARGOS', { allPages: true }),
          regrasAPI.lerAba('HIERARQUIA', { allPages: true }),
        ]);
        
        setColaboradoresOptions(
          (colabResp.data?.data || []).map((r) => r.nome_colaborador).filter(Boolean)
        );
        setCargosOptions(
          (cargosResp.data?.data || []).map((r) => r.cargo).filter(Boolean)
        );
        setLinhasOptions(
          [...new Set((hierResp.data?.data || []).map((r) => r.linha).filter(Boolean))]
        );
      } catch (e) {
        message.error('Erro ao carregar dados de referência');
      }
    };
    loadLookups();
  }, []);

  // Adapter for SmartTable
  const regrasApiAdapter = {
    read: (id, params) => regrasAPI.lerAba(id, params),
    save: (id, data) => regrasAPI.salvarAba(id, data, true),
  };

  // Schema for ATRIBUICOES
  const atribuicoesSchema = {
    linha: { label: 'Linha', type: 'select', width: 150 },
    grupo: { label: 'Grupo', type: 'text', width: 180 },
    subgrupo: { label: 'Subgrupo', type: 'text', width: 180 },
    tipo_mercadoria: { label: 'Tipo Mercadoria', type: 'text', width: 140 },
    colaborador: { label: 'Colaborador', type: 'select', width: 200 },
    cargo: { label: 'Cargo', type: 'select', width: 150 },
  };

  const items = [
    { key: 'pesos', label: 'Pesos do FC', children: <PesosMetasEditor /> },
    { key: 'hierarquia', label: 'Hierarquia de Produtos', children: <HierarquiaEditor /> },
    { key: 'config', label: 'Taxas e Fatias de Comissão', children: <ConfigComissaoEditor /> },
    { key: 'metas', label: 'Gerenciar Metas', children: <MetasEditor /> },
    { key: 'colabs', label: 'Colaboradores e Cargos', children: <ColaboradoresCargosEditor /> },
    { 
      key: 'atribuicoes', 
      label: 'Atribuições', 
      children: (
        <SmartTable 
          resourceId="ATRIBUICOES" 
          apiService={regrasApiAdapter} 
          title="Atribuições de Carteira"
          schema={atribuicoesSchema}
          lookups={{
            linha: linhasOptions,
            colaborador: colaboradoresOptions,
            cargo: cargosOptions,
          }}
        />
      ) 
    },
  ];

  return (
    <Card title="Gerenciamento de Regras de Negócio">
      <Tabs items={items} />
      </Card>
  );
};

export default RegrasPage;

