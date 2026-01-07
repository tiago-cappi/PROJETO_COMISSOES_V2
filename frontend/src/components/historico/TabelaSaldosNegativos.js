import React, { useMemo } from 'react';
import { Table, Typography, Tag } from 'antd';

const { Text } = Typography;

const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const buildRowKey = (row, idx) => {
  const base = [row?.Nome_Colaborador, row?.Processo, row?.Tipo_Comissao, row?.Numero_NF, row?.Data_Execucao].filter(Boolean).join('|');
  return base ? `${base}|${idx}` : String(idx);
};

const TabelaSaldosNegativos = ({ resumo = [], itens = [], loading = false, onClickItem }) => {
  const dataSource = useMemo(() => {
    const itensArray = Array.isArray(itens) ? itens : [];
    const byColab = new Map();

    for (const it of itensArray) {
      const nome = it.Nome_Colaborador || it.nome_colaborador || '—';
      if (!byColab.has(nome)) byColab.set(nome, []);
      byColab.get(nome).push(it);
    }

    const resumoArray = Array.isArray(resumo) ? resumo : [];

    return resumoArray.map((r, idx) => {
      const nome = r.Nome_Colaborador || r.nome_colaborador || '—';
      const childrenRaw = byColab.get(nome) || [];
      const children = childrenRaw.map((c, childIdx) => ({
        ...c,
        key: buildRowKey(c, childIdx),
      }));

      return {
        ...r,
        key: `${nome}|${idx}`,
        Nome_Colaborador: nome,
        children,
      };
    });
  }, [resumo, itens]);

  const columns = [
    {
      title: 'Colaborador',
      dataIndex: 'Nome_Colaborador',
      key: 'Nome_Colaborador',
      width: 260,
      ellipsis: true,
      render: (v, record) => {
        if (record?.children) return <Text strong>{v}</Text>;
        return <Text>{v}</Text>;
      },
    },
    {
      title: 'Total (a descontar)',
      dataIndex: 'Total_Absoluto',
      key: 'Total_Absoluto',
      width: 170,
      align: 'right',
      render: (v, record) => {
        if (record?.children) {
          return <Text type="danger" strong>{formatCurrencyBR(v)}</Text>;
        }
        // child row
        const num = Number(record?.Comissao_Calculada ?? 0);
        return <Text type="danger" strong>{formatCurrencyBR(Math.abs(num))}</Text>;
      },
    },
    {
      title: 'Origem',
      key: 'origem',
      width: 140,
      render: (_, record) => {
        if (record?.children) return <Text type="secondary">—</Text>;
        const tipo = record?.Tipo_Comissao || record?.tipo_comissao;
        if (tipo === 'DEVOLUCAO') return <Tag color="red">DEVOLUÇÃO</Tag>;
        if (tipo === 'RECONCILIACAO') return <Tag color="orange">RECONCILIAÇÃO</Tag>;
        return <Tag>{String(tipo || '—')}</Tag>;
      },
    },
    {
      title: 'Processo',
      dataIndex: 'Processo',
      key: 'Processo',
      width: 160,
      ellipsis: true,
      render: (v, record) => (record?.children ? <Text type="secondary">—</Text> : <Text>{v || '-'}</Text>),
    },
    {
      title: 'NF',
      dataIndex: 'Numero_NF',
      key: 'Numero_NF',
      width: 120,
      render: (v, record) => (record?.children ? <Text type="secondary">—</Text> : <Text>{v || '-'}</Text>),
    },
    {
      title: 'Qtd.',
      dataIndex: 'Quantidade',
      key: 'Quantidade',
      width: 90,
      align: 'center',
      render: (v, record) => (record?.children ? <Text>{v ?? 0}</Text> : <Text type="secondary">—</Text>),
    },
  ];

  return (
    <Table
      size="middle"
      bordered
      loading={loading}
      columns={columns}
      dataSource={dataSource}
      pagination={{ pageSize: 12 }}
      expandable={{
        expandRowByClick: true,
        rowExpandable: (record) => Array.isArray(record.children) && record.children.length > 0,
      }}
      onRow={(record) => {
        if (record?.children) return {};
        return {
          onClick: () => onClickItem && onClickItem(record),
        };
      }}
      scroll={{ x: 'max-content' }}
    />
  );
};

export default TabelaSaldosNegativos;
