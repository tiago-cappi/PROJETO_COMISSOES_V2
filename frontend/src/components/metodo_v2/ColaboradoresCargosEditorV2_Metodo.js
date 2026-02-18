import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  message,
  Tag,
  Modal,
  Form,
  Select,
  Tabs,
  Popconfirm,
  Typography,
  Empty,
  Alert,
  Switch,
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  SaveOutlined,
  ReloadOutlined,
  EditOutlined,
  UserOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { metodoV2API } from '../../services/api';

const { Search } = Input;
const { Text } = Typography;

/**
 * ColaboradoresCargosEditorV2_Metodo
 * Editor de colaboradores e cargos para o Método V2
 */
const ColaboradoresCargosEditorV2_Metodo = () => {
  // Estado para Colaboradores
  const [colaboradores, setColaboradores] = useState([]);
  const [colaboradoresLoading, setColaboradoresLoading] = useState(false);
  const [colaboradoresSaving, setColaboradoresSaving] = useState(false);
  const [colaboradoresModified, setColaboradoresModified] = useState(new Set());
  const [colaboradoresSearch, setColaboradoresSearch] = useState('');

  // Estado para Cargos
  const [cargos, setCargos] = useState([]);
  const [cargosLoading, setCargosLoading] = useState(false);
  const [cargosSaving, setCargosSaving] = useState(false);
  const [cargosModified, setCargosModified] = useState(new Set());

  // Modal de adição
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState('colaborador'); // 'colaborador' ou 'cargo'
  const [form] = Form.useForm();

  // Carregar colaboradores
  const carregarColaboradores = useCallback(async () => {
    setColaboradoresLoading(true);
    try {
      const resp = await metodoV2API.lerAba('COLABORADORES_V2', { allPages: true });
      const arr = resp.data?.data || [];
      setColaboradores(arr.map((row, idx) => ({
        __key: `colab_${idx}`,
        __original: { ...row },
        tipo_comissao: (row.tipo_comissao || 'faturamento').toString().toLowerCase(),
        taxa_adiantamento_pct: row.taxa_adiantamento_pct !== undefined && row.taxa_adiantamento_pct !== ''
          ? Number(row.taxa_adiantamento_pct)
          : null,
        ...row
      })));
      setColaboradoresModified(new Set());
    } catch (e) {
      message.error(`Erro ao carregar colaboradores V2: ${e.message}`);
    } finally {
      setColaboradoresLoading(false);
    }
  }, []);

  // Carregar cargos
  const carregarCargos = useCallback(async () => {
    setCargosLoading(true);
    try {
      const resp = await metodoV2API.lerAba('CARGOS_V2', { allPages: true });
      const arr = resp.data?.data || [];
      setCargos(arr.map((row, idx) => ({
        __key: `cargo_${idx}`,
        __original: { ...row },
        ...row
      })));
      setCargosModified(new Set());
    } catch (e) {
      message.error(`Erro ao carregar cargos V2: ${e.message}`);
    } finally {
      setCargosLoading(false);
    }
  }, []);

  useEffect(() => {
    carregarColaboradores();
    carregarCargos();
  }, [carregarColaboradores, carregarCargos]);

  // Salvar colaboradores
  const salvarColaboradores = async () => {
    const erros = [];
    colaboradores.forEach((row) => {
      const tipo = (row.tipo_comissao || 'faturamento').toString().toLowerCase();
      const taxa = row.taxa_adiantamento_pct;
      if (tipo === 'recebimento' && (!taxa || Number(taxa) <= 0)) {
        erros.push(`${row.nome_colaborador || 'Colaborador sem nome'}: taxa_adiantamento_pct obrigatória para recebimento`);
      }
    });
    if (erros.length > 0) {
      message.error(erros[0]);
      return;
    }
    setColaboradoresSaving(true);
    try {
      const payload = colaboradores.map(({ __key, __original, ...rest }) => rest);
      await metodoV2API.salvarAba('COLABORADORES_V2', payload, true);
      message.success('Colaboradores V2 salvos com sucesso!');
      setColaboradoresModified(new Set());
      await carregarColaboradores();
    } catch (e) {
      message.error(`Erro ao salvar: ${e.message}`);
    } finally {
      setColaboradoresSaving(false);
    }
  };

  // Salvar cargos
  const salvarCargos = async () => {
    setCargosSaving(true);
    try {
      const payload = cargos.map(({ __key, __original, ...rest }) => rest);
      await metodoV2API.salvarAba('CARGOS_V2', payload, true);
      message.success('Cargos V2 salvos com sucesso!');
      setCargosModified(new Set());
      await carregarCargos();
    } catch (e) {
      message.error(`Erro ao salvar: ${e.message}`);
    } finally {
      setCargosSaving(false);
    }
  };

  // Editar célula de colaborador
  const editColaboradorCell = (key, field, value) => {
    setColaboradores(prev => prev.map(row => {
      if (row.__key === key) {
        setColaboradoresModified(m => new Set([...m, key]));
        return { ...row, [field]: value };
      }
      return row;
    }));
  };

  // Excluir colaborador
  const deleteColaborador = (key) => {
    setColaboradores(prev => prev.filter(row => row.__key !== key));
    setColaboradoresModified(m => {
      const newSet = new Set(m);
      newSet.add('__deleted__');
      return newSet;
    });
  };

  // Editar célula de cargo
  const editCargoCell = (key, field, value) => {
    setCargos(prev => prev.map(row => {
      if (row.__key === key) {
        setCargosModified(m => new Set([...m, key]));
        return { ...row, [field]: value };
      }
      return row;
    }));
  };

  // Excluir cargo
  const deleteCargo = (key) => {
    setCargos(prev => prev.filter(row => row.__key !== key));
    setCargosModified(m => {
      const newSet = new Set(m);
      newSet.add('__deleted__');
      return newSet;
    });
  };

  // Abrir modal de adição
  const openAddModal = (type) => {
    setModalType(type);
    form.resetFields();
    setModalOpen(true);
  };

  // Confirmar adição
  const handleAddConfirm = () => {
    form.validateFields().then(values => {
      if (modalType === 'colaborador') {
        const newKey = `colab_new_${Date.now()}`;
        setColaboradores(prev => [...prev, {
          __key: newKey,
          __original: null,
          nome_colaborador: values.nome_colaborador,
          cargo: values.cargo || '',
        }]);
        setColaboradoresModified(m => new Set([...m, newKey]));
      } else {
        const newKey = `cargo_new_${Date.now()}`;
        setCargos(prev => [...prev, {
          __key: newKey,
          __original: null,
          nome_cargo: values.nome_cargo,
        }]);
        setCargosModified(m => new Set([...m, newKey]));
      }
      setModalOpen(false);
      message.success(`${modalType === 'colaborador' ? 'Colaborador' : 'Cargo'} adicionado. Salve para persistir.`);
    });
  };

  // Lista de cargos para dropdown
  const cargosOptions = useMemo(() => {
    return cargos.map(c => c.nome_cargo).filter(Boolean);
  }, [cargos]);

  // Filtrar colaboradores
  const filteredColaboradores = useMemo(() => {
    if (!colaboradoresSearch) return colaboradores;
    const search = colaboradoresSearch.toLowerCase();
    return colaboradores.filter(c =>
      (c.nome_colaborador || '').toLowerCase().includes(search) ||
      (c.cargo || '').toLowerCase().includes(search)
    );
  }, [colaboradores, colaboradoresSearch]);

  // Colunas da tabela de colaboradores
  const colaboradoresColumns = [
    {
      title: 'Nome',
      dataIndex: 'nome_colaborador',
      key: 'nome_colaborador',
      width: 250,
      render: (text, record) => (
        <Input
          value={text}
          onChange={e => editColaboradorCell(record.__key, 'nome_colaborador', e.target.value)}
          bordered={false}
          style={{ fontWeight: colaboradoresModified.has(record.__key) ? 'bold' : 'normal' }}
        />
      ),
    },
    {
      title: 'Cargo',
      dataIndex: 'cargo',
      key: 'cargo',
      width: 200,
      render: (text, record) => (
        <Select
          value={text}
          onChange={v => editColaboradorCell(record.__key, 'cargo', v)}
          style={{ width: '100%' }}
          bordered={false}
          allowClear
        >
          {cargosOptions.map(c => (
            <Select.Option key={c} value={c}>{c}</Select.Option>
          ))}
        </Select>
      ),
    },
      {
        title: 'Tipo Comissão',
        dataIndex: 'tipo_comissao',
        key: 'tipo_comissao',
        width: 200,
        render: (text, record) => (
          <Switch
            checked={String(record.tipo_comissao || 'faturamento').toLowerCase() === 'recebimento'}
            checkedChildren="Recebimento"
            unCheckedChildren="Faturamento"
            onChange={(checked) => {
              editColaboradorCell(record.__key, 'tipo_comissao', checked ? 'recebimento' : 'faturamento');
              if (!checked) {
                editColaboradorCell(record.__key, 'taxa_adiantamento_pct', null);
              }
            }}
          />
        ),
      },
      {
        title: 'Taxa Adiantamento (%)',
        dataIndex: 'taxa_adiantamento_pct',
        key: 'taxa_adiantamento_pct',
        width: 220,
        render: (text, record) => {
          const isRecebimento = String(record.tipo_comissao || 'faturamento').toLowerCase() === 'recebimento';
          if (!isRecebimento) {
            return <Tag color="default">-</Tag>;
          }
          return (
            <InputNumber
              value={record.taxa_adiantamento_pct}
              min={0.01}
              max={100}
              step={0.1}
              formatter={(value) => `${value}%`}
              parser={(value) => value.replace('%', '')}
              onChange={(val) => editColaboradorCell(record.__key, 'taxa_adiantamento_pct', val)}
              style={{ width: '100%' }}
            />
          );
        },
      },
    {
      title: 'Ações',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Popconfirm
          title="Excluir colaborador?"
          onConfirm={() => deleteColaborador(record.__key)}
          okText="Sim"
          cancelText="Não"
        >
          <Button type="text" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  // Colunas da tabela de cargos
  // NOTA: Split fixo para Gerente Linha e Coordenador (2 ocupantes com divisão de comissão)
  const cargosColumns = [
    {
      title: 'Nome do Cargo',
      dataIndex: 'nome_cargo',
      key: 'nome_cargo',
      width: 250,
      render: (text, record) => (
        <Input
          value={text}
          onChange={e => editCargoCell(record.__key, 'nome_cargo', e.target.value)}
          bordered={false}
          style={{ fontWeight: cargosModified.has(record.__key) ? 'bold' : 'normal' }}
        />
      ),
    },
    {
      title: 'Divisão de Comissão (Split)',
      key: 'split_info',
      width: 350,
      render: (_, record) => {
        const nome = record.nome_cargo || '';
        const isSplitCargo = nome === 'Gerente Linha' || nome === 'Coordenador';
        return isSplitCargo 
          ? <Tag color="green">✓ Permite 2 ocupantes com divisão de comissão</Tag>
          : <Tag color="default">Cargo individual (1 ocupante por hierarquia)</Tag>;
      },
    },
    {
      title: 'Ações',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Popconfirm
          title="Excluir cargo?"
          onConfirm={() => deleteCargo(record.__key)}
          okText="Sim"
          cancelText="Não"
        >
          <Button type="text" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  // Tab de Colaboradores
  const ColaboradoresTab = (
    <Card
      title={
        <Space>
          <UserOutlined />
          <span>Colaboradores V2</span>
          <Tag color="purple">{colaboradores.length}</Tag>
          {colaboradoresModified.size > 0 && (
            <Tag color="orange">Modificado</Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Search
            placeholder="Buscar colaborador..."
            value={colaboradoresSearch}
            onChange={e => setColaboradoresSearch(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Button
            icon={<PlusOutlined />}
            onClick={() => openAddModal('colaborador')}
          >
            Novo Colaborador
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={carregarColaboradores}
            loading={colaboradoresLoading}
          >
            Recarregar
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={salvarColaboradores}
            loading={colaboradoresSaving}
            disabled={colaboradoresModified.size === 0}
          >
            Salvar
          </Button>
        </Space>
      }
    >
      {filteredColaboradores.length === 0 ? (
        <Empty description="Nenhum colaborador cadastrado" />
      ) : (
        <Table
          dataSource={filteredColaboradores}
          columns={colaboradoresColumns}
          rowKey="__key"
          size="small"
          pagination={{ pageSize: 15, showSizeChanger: true }}
          loading={colaboradoresLoading}
        />
      )}
    </Card>
  );

  // Tab de Cargos
  const CargosTab = (
    <Card
      title={
        <Space>
          <TeamOutlined />
          <span>Cargos V2</span>
          <Tag color="purple">{cargos.length}</Tag>
          {cargosModified.size > 0 && (
            <Tag color="orange">Modificado</Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Button
            icon={<PlusOutlined />}
            onClick={() => openAddModal('cargo')}
          >
            Novo Cargo
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={carregarCargos}
            loading={cargosLoading}
          >
            Recarregar
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={salvarCargos}
            loading={cargosSaving}
            disabled={cargosModified.size === 0}
          >
            Salvar
          </Button>
        </Space>
      }
    >
      {cargos.length === 0 ? (
        <Empty description="Nenhum cargo cadastrado" />
      ) : (
        <Table
          dataSource={cargos}
          columns={cargosColumns}
          rowKey="__key"
          size="small"
          pagination={{ pageSize: 10 }}
          loading={cargosLoading}
        />
      )}
    </Card>
  );

  const tabItems = [
    { key: 'colaboradores', label: 'Colaboradores', children: ColaboradoresTab },
    { key: 'cargos', label: 'Cargos', children: CargosTab },
  ];

  return (
    <>
      <Tabs items={tabItems} />

      {/* Modal de adição */}
      <Modal
        title={modalType === 'colaborador' ? 'Novo Colaborador' : 'Novo Cargo'}
        open={modalOpen}
        onOk={handleAddConfirm}
        onCancel={() => setModalOpen(false)}
        okText="Adicionar"
        cancelText="Cancelar"
      >
        <Form form={form} layout="vertical">
          {modalType === 'colaborador' ? (
            <>
              <Form.Item
                name="nome_colaborador"
                label="Nome do Colaborador"
                rules={[{ required: true, message: 'Nome é obrigatório' }]}
              >
                <Input placeholder="Ex: João Silva" />
              </Form.Item>
              <Form.Item name="cargo" label="Cargo">
                <Select placeholder="Selecione um cargo" allowClear>
                  {cargosOptions.map(c => (
                    <Select.Option key={c} value={c}>{c}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </>
          ) : (
            <>
              <Form.Item
                name="nome_cargo"
                label="Nome do Cargo"
                rules={[{ required: true, message: 'Nome é obrigatório' }]}
              >
                <Input placeholder="Ex: Gerente Linha, Coordenador, Vendedor" />
              </Form.Item>
              <Alert
                message="Divisão de Comissão (Split)"
                description="Somente os cargos 'Gerente Linha' e 'Coordenador' permitem 2 ocupantes com divisão de comissão. Outros cargos são individuais."
                type="info"
                showIcon
                style={{ marginTop: 8 }}
              />
            </>
          )}
        </Form>
      </Modal>
    </>
  );
};

export default ColaboradoresCargosEditorV2_Metodo;
