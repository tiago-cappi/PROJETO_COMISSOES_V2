import React, { useEffect, useState, useMemo } from 'react';
import { Card, Tabs, message, Button } from 'antd';
import PesosMetasEditor from '../components/PesosMetasEditorV2';
import ConfigComissaoEditor from '../components/ConfigComissaoEditorV2';
import MetasEditor from '../components/MetasEditorV2';
import ColaboradoresCargosEditor from '../components/ColaboradoresCargosEditorV2';
import HierarquiaEditor from '../components/HierarquiaEditorV2';
import SmartTable from '../components/SmartTable';
import { regrasAPI } from '../services/api';

const RegrasPage = () => {
  const [colaboradoresOptions, setColaboradoresOptions] = useState([]);
  const [colsAtribuicoes, setColsAtribuicoes] = useState({});
  const [linhasOptions, setLinhasOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roleColumnsList, setRoleColumnsList] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  
  // Load lookup data on mount
  useEffect(() => {
    const loadLookups = async () => {
      try {
        setLoading(true);
        const [colabResp, cargosResp, hierResp] = await Promise.all([
          regrasAPI.lerAba('COLABORADORES', { allPages: true }),
          regrasAPI.lerAba('CARGOS', { allPages: true }),
          regrasAPI.lerAba('HIERARQUIA', { allPages: true }),
        ]);
        
        const colabRespData = colabResp.data?.data || [];
        const colabs = colabRespData.map((r) => ({
          nome: r.nome_colaborador,
          cargo: r.cargo
        })).filter(c => c.nome);
        
        setColaboradoresOptions(colabs);
        
        const cargos = (cargosResp.data?.data || []).map((r) => r.nome_cargo).filter(Boolean);
        
        setLinhasOptions(
          [...new Set((hierResp.data?.data || []).map((r) => r.linha).filter(Boolean))].sort()
        );

        // Build Dynamic Schema for Atribuicoes
        const baseSchema = {
          linha: { label: 'Linha', type: 'select', width: 150 },
          grupo: { label: 'Grupo', type: 'text', width: 150 },
          subgrupo: { label: 'Subgrupo', type: 'text', width: 150 },
          tipo_mercadoria: { label: 'Tipo Mercadoria', type: 'text', width: 130 },
        };

        const roleColumns = {};
        
        // Define special handling for split roles
        const splitRoles = ['Gerente Linha', 'Coordenador'];
        
        // Populate schema based on valid CARGOS
        cargos.forEach(cargo => {
           if (cargo === 'Gerente Linha') {
             roleColumns['Gerente Linha 1'] = { label: 'Gerente Linha 1', type: 'select', width: 180 };
             roleColumns['Gerente Linha 2'] = { label: 'Gerente Linha 2', type: 'select', width: 180 };
           } else if (cargo === 'Coordenador') {
             roleColumns['Coordenador 1'] = { label: 'Coordenador 1', type: 'select', width: 180 };
             roleColumns['Coordenador 2'] = { label: 'Coordenador 2', type: 'select', width: 180 };
           } else {
             // For other roles, just one column with the exact name
             roleColumns[cargo] = { label: cargo, type: 'select', width: 180 };
           }
        });

        // Fallback: Ensure specific split roles exist even if not in CARGOS (defensive)
        if (!roleColumns['Gerente Linha 1'] && !roleColumns['Gerente Linha']) {
            roleColumns['Gerente Linha 1'] = { label: 'Gerente Linha 1', type: 'select', width: 180 };
            roleColumns['Gerente Linha 2'] = { label: 'Gerente Linha 2', type: 'select', width: 180 };
        }
        if (!roleColumns['Coordenador 1'] && !roleColumns['Coordenador']) {
             roleColumns['Coordenador 1'] = { label: 'Coordenador 1', type: 'select', width: 180 };
             roleColumns['Coordenador 2'] = { label: 'Coordenador 2', type: 'select', width: 180 };
        }

        // Colunas de fator_split para Gerente e Coordenador
        const splitFactorColumns = {
          fator_split_gerente: { label: 'Split Gerente (%)', type: 'number', width: 130 },
          fator_split_coordenador: { label: 'Split Coordenador (%)', type: 'number', width: 150 },
        };

        setColsAtribuicoes({ ...baseSchema, ...roleColumns, ...splitFactorColumns });
        
        // Guardar lista de colunas de cargo para o modal
        setRoleColumnsList(Object.keys(roleColumns));

      } catch (e) {
        message.error('Erro ao carregar dados de referência');
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadLookups();
  }, []);

  // Adapter for SmartTable
  const regrasApiAdapter = {
    read: (id, params) => regrasAPI.lerAba(id, params),
    save: (id, data) => regrasAPI.salvarAba(id, data, true),
  };

  const dynamicLookups = useMemo(() => {
     const lookups = {
        linha: linhasOptions,
     };
     
     const colabNames = ['Nenhum', ...colaboradoresOptions.map(c => c.nome).sort()];

     // Colunas que não são de seleção de colaborador
     const nonSelectCols = ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria', 'fator_split_gerente', 'fator_split_coordenador'];

     // Assign collaborator list to all role columns
     Object.keys(colsAtribuicoes).forEach(k => {
        if (!nonSelectCols.includes(k)) {
            lookups[k] = colabNames;
        }
     });
     return lookups;
  }, [colsAtribuicoes, linhasOptions, colaboradoresOptions]);

  const items = [
    { key: 'pesos', label: 'Pesos do FC', children: <PesosMetasEditor /> },
    { key: 'hierarquia', label: 'Hierarquia de Produtos', children: <HierarquiaEditor /> },
    { key: 'config', label: 'Taxas e Fatias de Comissão', children: <ConfigComissaoEditor /> },
    { key: 'metas', label: 'Gerenciar Metas', children: <MetasEditor /> },
    { key: 'colabs', label: 'Colaboradores e Cargos', children: <ColaboradoresCargosEditor /> },
    { 
      key: 'atribuicoes', 
      label: 'Atribuições', 
      children: !loading ? (
        <>
          <SmartTable 
            key={refreshKey}
            resourceId="ATRIBUICOES" 
            apiService={regrasApiAdapter} 
            title="Atribuições de Carteira (Tabela Larga)"
            schema={colsAtribuicoes}
            lookups={dynamicLookups}
          />
        </>
      ) : <Card loading /> 
    },
  ];

  return (
    <Card title="Gerenciamento de Regras de Negócio">
      <Tabs items={items} />
      </Card>
  );
};

export default RegrasPage;

