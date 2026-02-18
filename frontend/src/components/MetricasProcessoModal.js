import React, { useState } from 'react';
import { Typography, Table, Divider, Button } from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import EscadaDemonstrativoModal from './EscadaDemonstrativoModal';

const { Title, Text } = Typography;

function formatPercent(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
}

const MetricasProcessoModal = ({ rowData }) => {
  const [escadaModalData, setEscadaModalData] = useState(null);

  const processo = rowData?.processo || rowData?.PROCESSO;
  const mesAno = rowData?.MES_ANO_FATURAMENTO || rowData?.mes_ano_faturamento;

  const colaboradores = Array.isArray(rowData?.__colaboradores_metricas)
    ? rowData.__colaboradores_metricas
    : [];

  return (
    <div>
      <Title level={4}>Métricas do Processo</Title>
      <p><b>Processo:</b> {processo}</p>
      {mesAno && <p><b>Mês/Ano do Faturamento:</b> {mesAno}</p>}
      <Divider />

      <Title level={5}>TCMP e FCMP por Colaborador</Title>
      <Table
        columns={[
          { title: 'Colaborador', dataIndex: 'nome_colaborador', key: 'nome_colaborador', width: 200 },
          { title: 'TCMP', dataIndex: 'tcmp', key: 'tcmp', width: 100, render: (v) => formatPercent(v) },
          { title: 'FCMP (Rampa)', dataIndex: 'fcmp', key: 'fcmp', width: 120, render: (v) => formatPercent(v) },
          { 
            title: 'FCMP (Apl)', 
            dataIndex: 'fcmp_aplicado', 
            key: 'fcmp_aplicado', 
            width: 120, 
            render: (v) => (v !== undefined ? <b>{formatPercent(v)}</b> : '-') 
          },
          { 
            title: 'Det. Escada', 
            dataIndex: 'escada_detalhes', 
            key: 'escada_detalhes', 
            width: 180,
            render: (det) => {
              if (!det || !det.modo) return '-';
              if (det.modo === 'RAMPA') return 'RAMPA';
              
              return (
                 <Button 
                   type="link" 
                   size="small" 
                   icon={<CalculatorOutlined />}
                   onClick={() => setEscadaModalData({
                      cargo: det.cargo,
                      numDegraus: det.num_degraus,
                      piso: det.piso,
                      performanceRampa: det.performance_rampa,
                      multiplicadorFinal: det.multiplicador,
                      degrauAtingido: det.degrau_indice
                   })}
                 >
                   Escada #{det.degrau_indice}
                 </Button>
              );
            }
          },
        ]}
        dataSource={colaboradores.map((c, idx) => ({
          key: c.key || idx,
          nome_colaborador: c.nome_colaborador,
          tcmp: c.tcmp,
          fcmp: c.fcmp,
          fcmp_aplicado: c.fcmp_aplicado,
          escada_detalhes: c.escada_detalhes,
          fonte: c.fonte || 'ESTADO',
        }))}
        pagination={false}
        rowKey="key"
        size="small"
        scroll={{ x: 'max-content' }}
      />
      
      <EscadaDemonstrativoModal
          visible={!!escadaModalData}
          onClose={() => setEscadaModalData(null)}
          data={escadaModalData}
      />

      <Divider />
      <div style={{ padding: '10px', background: '#f0f8ff', border: '1px solid #cce5ff', borderRadius: 4 }}>
        <Text>
          <b>TCMP</b> (Taxa de Comissão Média Ponderada) é a média ponderada pelo valor dos itens das taxas por item.
          <br />
          <b>FCMP</b> (Fator de Correção Médio Ponderado) é a média ponderada pelo valor dos itens dos FCs por item.
          <br />
          Essas métricas são calculadas no mês do faturamento e persistidas para uso em parcelas futuras.
        </Text>
      </div>
    </div>
  );
};

export default MetricasProcessoModal;


