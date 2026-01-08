import React, { useState, useEffect } from 'react';
import { Modal, Table, Typography, Spin, Empty, Tag } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { historicoAPI } from '../../services/api';

const { Text } = Typography;

const formatCurrencyBR = (value) => {
  if (value === null || value === undefined || value === '') return '-';
  const num = Number(String(value).replace(/[^\d.,-]/g, '').replace(',', '.'));
  if (Number.isNaN(num)) return value;
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const DetalhesProcessoItensModal = ({ visible, onClose, processo, numeroNF }) => {
  const [loading, setLoading] = useState(false);
  const [itens, setItens] = useState([]);

  useEffect(() => {
    if (visible && processo) {
      fetchItens();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, processo]);

  const fetchItens = async () => {
    setLoading(true);
    try {
      const resp = await historicoAPI.getProcessoItens(processo);
      const payload = resp?.data || {};
      setItens(payload.itens || []);
    } catch (error) {
      console.error('Erro ao carregar itens do processo:', error);
      setItens([]);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Operação',
      dataIndex: 'Operação',
      key: 'Operação',
      width: 100,
      ellipsis: true,
    },
    {
      title: 'Descrição Produto',
      dataIndex: 'Descrição Produto',
      key: 'Descrição Produto',
      width: 220,
      ellipsis: true,
      render: (v) => <Text>{v || '-'}</Text>,
    },
    {
      title: 'Negócio',
      dataIndex: 'Negócio',
      key: 'Negócio',
      width: 120,
      ellipsis: true,
    },
    {
      title: 'Grupo',
      dataIndex: 'Grupo',
      key: 'Grupo',
      width: 120,
      ellipsis: true,
    },
    {
      title: 'Subgrupo',
      dataIndex: 'Subgrupo',
      key: 'Subgrupo',
      width: 120,
      ellipsis: true,
    },
    {
      title: 'Tipo de Mercadoria',
      dataIndex: 'Tipo de Mercadoria',
      key: 'Tipo de Mercadoria',
      width: 140,
      ellipsis: true,
    },
    {
      title: 'Valor Realizado',
      dataIndex: 'Valor Realizado',
      key: 'Valor Realizado',
      width: 140,
      align: 'right',
      render: (v) => <Text strong>{formatCurrencyBR(v)}</Text>,
    },
    {
      title: 'Dt Emissão',
      dataIndex: 'Dt Emissão',
      key: 'Dt Emissão',
      width: 110,
    },
    {
      title: 'Consultor Interno',
      dataIndex: 'Consultor Interno',
      key: 'Consultor Interno',
      width: 160,
      ellipsis: true,
    },
    {
      title: 'Status Processo',
      dataIndex: 'Status Processo',
      key: 'Status Processo',
      width: 130,
      render: (v) => {
        if (!v) return '-';
        let color = 'default';
        const val = String(v).toUpperCase();
        if (val.includes('FATURADO') || val.includes('CONCLUIDO')) color = 'green';
        if (val.includes('CANCELADO')) color = 'red';
        if (val.includes('PENDENTE') || val.includes('ANDAMENTO')) color = 'orange';
        return <Tag color={color}>{v}</Tag>;
      },
    },
    {
      title: 'Processo',
      dataIndex: 'Processo',
      key: 'Processo',
      width: 120,
    },
    {
      title: 'Numero NF',
      dataIndex: 'Numero NF',
      key: 'Numero NF',
      width: 100,
    },
    {
      title: 'Status da NF',
      dataIndex: 'Status da NF',
      key: 'Status da NF',
      width: 120,
      render: (v) => {
        if (!v) return '-';
        let color = 'default';
        const val = String(v).toUpperCase();
        if (val.includes('EMITIDA') || val.includes('OK') || val.includes('AUTORIZADA')) color = 'green';
        if (val.includes('CANCELADA')) color = 'red';
        return <Tag color={color}>{v}</Tag>;
      },
    },
  ];

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      onOk={onClose}
      okText="Fechar"
      cancelButtonProps={{ style: { display: 'none' } }}
      width={1200}
      title={
        <span>
          <FileTextOutlined style={{ marginRight: 8 }} />
          Itens do Processo: {processo} {numeroNF ? `(NF: ${numeroNF})` : ''}
        </span>
      }
      destroyOnClose
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" tip="Carregando itens..." />
        </div>
      ) : itens.length === 0 ? (
        <Empty description="Nenhum item encontrado para este processo" />
      ) : (
        <Table
          size="small"
          bordered
          rowKey={(r, idx) => `${r.Processo || ''}-${r['Numero NF'] || ''}-${idx}`}
          pagination={{ pageSize: 10, showSizeChanger: true, pageSizeOptions: ['10', '20', '50'] }}
          columns={columns}
          dataSource={itens}
          scroll={{ x: 'max-content' }}
        />
      )}
    </Modal>
  );
};

export default DetalhesProcessoItensModal;
