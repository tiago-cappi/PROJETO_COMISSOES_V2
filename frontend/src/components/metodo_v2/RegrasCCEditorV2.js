import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  message,
  Spin,
  Alert,
  Empty,
  Tag,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Tooltip,
  Popconfirm,
  Row,
  Col,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  SaveOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EditOutlined,
  BankOutlined,
  UserOutlined,
  InfoCircleOutlined,
  ShopOutlined,
  PercentageOutlined,
  TeamOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { metodoV2API } from '../../services/api';

const { Title, Text } = Typography;

/**
 * Componente de linha para cada faixa de comissão.
 * Extraído para poder usar Form.useWatch corretamente.
 */
const FaixaRow = ({ n, form }) => {
  return (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name={`faixa_${n}_limite`}
          label={`Limite Inferior Faixa ${n} (R$)`}
          rules={n === 1 ? [{ required: true, message: 'Obrigatório' }] : []}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder={n === 1 ? 'R$ 0' : 'Opcional'}
            min={0}
            formatter={(value) => `R$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
            parser={(value) => value.replace(/R\$\s?|(\.)/g, '')}
          />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name={`faixa_${n}_taxa`}
          label={`Taxa Faixa ${n} (%)`}
          rules={n === 1 ? [{ required: true, message: 'Obrigatório' }] : []}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0.0"
            min={0}
            max={100}
            step={0.1}
            precision={2}
          />
        </Form.Item>
      </Col>
    </Row>
  );
};

/**
 * Editor de Regras de Comissão por Centro de Custo + Fabricante.
 * 
 * Permite configurar regras de comissão onde a chave é o Centro de Custo,
 * opcionalmente combinado com um Fabricante específico.
 * 
 * Regras de Especificidade:
 * - Regra com CC + Fabricante: especificidade = 2 (prioridade maior)
 * - Regra com CC apenas (Fabricante = "TODOS"): especificidade = 1 (fallback)
 * 
 * Split (Divisão de Comissão):
 * - Aplicável apenas a cargos "Gerente Linha" e "Coordenador"
 * - Se há múltiplos do mesmo cargo na mesma regra (CC, Fab), splits devem somar 100%
 * - Se único do cargo na regra, split é implicitamente 100%
 * 
 * Estrutura:
 * - colaborador + centro_custo + fabricante + split + faixas[1..5]
 */

// Cargos que usam split por regra (CC, Fab) - soma deve ser 100%
const CARGOS_COM_SPLIT = ['Gerente Linha', 'Coordenador'];

const RegrasCCEditorV2 = () => {
  // Estado principal
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [regrasCC, setRegrasCC] = useState([]);
  const [colaboradores, setColaboradores] = useState([]);
  
  // Estado do modal
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRegra, setEditingRegra] = useState(null);
  const [form] = Form.useForm();
  
  // Estado para CC e Fabricantes da Análise Comercial
  const [ccFabData, setCcFabData] = useState({
    centros_custo: [],
    fabricantes: [],
    mapeamento: {},  // CC -> [Fabricantes]
  });
  
  // Estado para filtros dinâmicos no formulário
  const [selectedCC, setSelectedCC] = useState(null);
  const [selectedFab, setSelectedFab] = useState(null);
  const [selectedColaborador, setSelectedColaborador] = useState(null);
  
  // Estado para controle do campo split
  const [showSplitField, setShowSplitField] = useState(false);
  const [splitRequired, setSplitRequired] = useState(false);
  const [outrosDoMesmoCargo, setOutrosDoMesmoCargo] = useState([]);
  // Estado para splits editáveis (quando criando nova regra com conflito)
  const [splitsEditaveis, setSplitsEditaveis] = useState({});  // { colaborador: split }
  
  // Centros de Custo conhecidos (com descrições)
  const centrosCustoDescricoes = {
    '2.5.030': 'Remediação',
    '2.5.031': 'Hidrologia',
    '2.5.036': 'Dep. Detecção Fixa',
    '2.5.037': 'Dep. Detecção Portátil',
    '2.5.039': 'Saneamento/Aquacultura',
    '2.5.040': 'TD-24',
    '3.7.030': 'Assistência Técnica Remediação',
    '3.7.031': 'Assistência Técnica Hidrologia',
    '3.7.032': 'Assistência Técnica SSO',
    '3.7.035': 'Locações',
  };
  
  // Lista de CCs para o dropdown (combinando conhecidos + dados da AC)
  const centrosCustoOptions = useMemo(() => {
    const ccSet = new Set([
      ...Object.keys(centrosCustoDescricoes),
      ...ccFabData.centros_custo
    ]);
    return Array.from(ccSet).sort().map(cc => ({
      codigo: cc,
      descricao: centrosCustoDescricoes[cc] || cc,
    }));
  }, [ccFabData.centros_custo]);
  
  // Fabricantes disponíveis filtrados pelo CC selecionado
  const fabricantesFiltered = useMemo(() => {
    if (!selectedCC) {
      return ccFabData.fabricantes;
    }
    return ccFabData.mapeamento[selectedCC] || [];
  }, [selectedCC, ccFabData]);
  
  // CCs disponíveis filtrados pelo Fabricante selecionado
  const ccsFilteredByFab = useMemo(() => {
    if (!selectedFab || selectedFab === '') {
      return centrosCustoOptions;
    }
    // Filtrar CCs que contêm este fabricante
    const ccsComFab = Object.entries(ccFabData.mapeamento)
      .filter(([cc, fabs]) => fabs.includes(selectedFab))
      .map(([cc]) => cc);
    
    return centrosCustoOptions.filter(cc => ccsComFab.includes(cc.codigo));
  }, [selectedFab, ccFabData.mapeamento, centrosCustoOptions]);

  // Obter cargo de um colaborador
  const getCargoColaborador = useCallback((nomeColaborador) => {
    const colab = colaboradores.find(c => c.nome_colaborador === nomeColaborador);
    return colab?.cargo || '';
  }, [colaboradores]);

  // Verificar se cargo usa split
  const cargoUsaSplit = useCallback((cargo) => {
    return CARGOS_COM_SPLIT.includes(cargo);
  }, []);

  // Verificar se há outros colaboradores do mesmo cargo na mesma regra (CC, Fab)
  const verificarConflitoCargo = useCallback((nomeColaborador, cc, fab, regraEmEdicao = null) => {
    if (!nomeColaborador || !cc) return { temConflito: false, outros: [] };
    
    const cargo = getCargoColaborador(nomeColaborador);
    if (!cargoUsaSplit(cargo)) return { temConflito: false, outros: [] };
    
    // Buscar outros do mesmo cargo na mesma regra (CC, Fab)
    const fabricanteNorm = fab || '';
    const outros = regrasCC.filter(r => {
      const fabRegra = r.fabricante || '';
      
      // Se está editando, excluir a regra em edição da contagem
      if (regraEmEdicao && 
          r.colaborador === regraEmEdicao.colaborador &&
          r.centro_custo === regraEmEdicao.centro_custo &&
          (r.fabricante || '') === (regraEmEdicao.fabricante || '')) {
        return false;
      }
      
      return r.centro_custo === cc && 
             fabRegra === fabricanteNorm && 
             r.colaborador !== nomeColaborador &&
             getCargoColaborador(r.colaborador) === cargo;
    });
    
    return { 
      temConflito: outros.length > 0, 
      outros: outros.map(r => ({
        nome: r.colaborador,
        split: r.split || 100,
      })),
      cargo 
    };
  }, [regrasCC, getCargoColaborador, cargoUsaSplit]);

  // Atualizar estado do campo split quando colaborador/CC/Fab mudam
  const atualizarEstadoSplit = useCallback((nomeColaborador, cc, fab) => {
    if (!nomeColaborador) {
      setShowSplitField(false);
      setSplitRequired(false);
      setOutrosDoMesmoCargo([]);
      return;
    }
    
    const cargo = getCargoColaborador(nomeColaborador);
    
    if (!cargoUsaSplit(cargo)) {
      setShowSplitField(false);
      setSplitRequired(false);
      setOutrosDoMesmoCargo([]);
      return;
    }
    
    // Passar a regra em edição para excluí-la da busca de conflitos
    const { temConflito, outros, cargo: cargoDetectado } = verificarConflitoCargo(nomeColaborador, cc, fab, editingRegra);
    
    if (temConflito) {
      setShowSplitField(true);
      setSplitRequired(true);
      setOutrosDoMesmoCargo(outros);
      // Inicializar splits editáveis com valores atuais (para edição inline)
      const splitsIniciais = {};
      outros.forEach(o => {
        splitsIniciais[o.nome] = o.split || 100;
      });
      setSplitsEditaveis(splitsIniciais);
    } else {
      // Se está editando uma regra existente com cargo que usa split, mostrar campo (mesmo sem conflito)
      // Isso permite ajustar o split de regras antigas
      if (editingRegra && cargoUsaSplit(cargo)) {
        setShowSplitField(true);
        setSplitRequired(false);  // Não obrigatório se for único
        setOutrosDoMesmoCargo([]);
        setSplitsEditaveis({});
      } else {
        // Único do cargo e não está editando - não precisa de split (será 100%)
        setShowSplitField(false);
        setSplitRequired(false);
        setOutrosDoMesmoCargo([]);
        setSplitsEditaveis({});
      }
    }
  }, [getCargoColaborador, cargoUsaSplit, verificarConflitoCargo, editingRegra]);

  // Carregar dados
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [regrasRes, colabsRes, ccFabRes] = await Promise.all([
        metodoV2API.lerAba('REGRAS_COMISSAO_CC_V2', { allPages: true }),
        metodoV2API.lerAba('COLABORADORES_V2', { allPages: true }),
        metodoV2API.getCCFabricantes(),
      ]);
      
      setRegrasCC(regrasRes.data?.data || []);
      setColaboradores(colabsRes.data?.data || []);
      
      // Dados de CC e Fabricantes da Análise Comercial
      if (ccFabRes.data) {
        setCcFabData({
          centros_custo: ccFabRes.data.centros_custo || [],
          fabricantes: ccFabRes.data.fabricantes || [],
          mapeamento: ccFabRes.data.mapeamento || {},
        });
      }
      
    } catch (error) {
      console.error('Erro ao carregar regras CC:', error);
      // Se a aba não existir, não é um erro crítico
      if (error.response?.status !== 404) {
        message.error('Erro ao carregar configurações: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Abrir modal para adicionar/editar
  const handleOpenModal = (regra = null) => {
    setEditingRegra(regra);
    // Reset filtros dinâmicos
    setSelectedCC(null);
    setSelectedFab(null);
    setSelectedColaborador(null);
    setShowSplitField(false);
    setSplitRequired(false);
    setOutrosDoMesmoCargo([]);
    setSplitsEditaveis({});
    
    if (regra) {
      const fabricanteValue = regra.fabricante || '';
      form.setFieldsValue({
        colaborador: regra.colaborador,
        centro_custo: regra.centro_custo,
        fabricante: fabricanteValue,  // '' = TODOS
        split: regra.split,  // Pode ser null/undefined
        faixa_1_limite: regra.faixa_1_limite || 0,
        faixa_1_taxa: regra.faixa_1_taxa,
        faixa_2_limite: regra.faixa_2_limite,
        faixa_2_taxa: regra.faixa_2_taxa,
        faixa_3_limite: regra.faixa_3_limite,
        faixa_3_taxa: regra.faixa_3_taxa,
        faixa_4_limite: regra.faixa_4_limite,
        faixa_4_taxa: regra.faixa_4_taxa,
        faixa_5_limite: regra.faixa_5_limite,
        faixa_5_taxa: regra.faixa_5_taxa,
      });
      // Definir filtros para edição
      setSelectedCC(regra.centro_custo);
      setSelectedFab(fabricanteValue);
      setSelectedColaborador(regra.colaborador);
      
      // Atualizar estado do split para edição
      atualizarEstadoSplit(regra.colaborador, regra.centro_custo, fabricanteValue);
    } else {
      form.resetFields();
      form.setFieldsValue({ faixa_1_limite: 0, fabricante: '' });
    }
    setModalVisible(true);
  };

  // Salvar regra (adicionar ou editar)
  const handleSaveRegra = async () => {
    try {
      const values = await form.validateFields();
      
      // Normalizar fabricante ('' = null/TODOS)
      const fabricante = values.fabricante || '';
      values.fabricante = fabricante;
      
      // Validar split se necessário
      const cargo = getCargoColaborador(values.colaborador);
      if (cargoUsaSplit(cargo) && splitRequired && !editingRegra) {
        // Validação de splits ao CRIAR nova regra com conflito
        const splitNovoColab = values.split;
        if (!splitNovoColab || splitNovoColab <= 0 || splitNovoColab >= 100) {
          message.error('O split deve ser um valor entre 1% e 99% quando há outros do mesmo cargo.');
          return;
        }
        
        // Verificar soma dos splits editáveis + split do novo colaborador
        const somaOutros = Object.values(splitsEditaveis).reduce((acc, s) => acc + (s || 0), 0);
        const somaTotal = somaOutros + splitNovoColab;
        
        if (Math.abs(somaTotal - 100) > 0.01) {
          const detalhesOutros = Object.entries(splitsEditaveis).map(([nome, split]) => `${nome}: ${split}%`).join(', ');
          message.error(
            `A soma dos splits deve ser 100%. Atualmente: ${somaTotal.toFixed(1)}% ` +
            `(${detalhesOutros}, ${values.colaborador}: ${splitNovoColab}%)`
          );
          return;
        }
      }
      
      let novasRegras = [...regrasCC];
      
      // Se criando nova regra com conflito, atualizar splits das regras existentes primeiro
      if (!editingRegra && Object.keys(splitsEditaveis).length > 0) {
        novasRegras = novasRegras.map(r => {
          const fabRegra = r.fabricante || '';
          // Verificar se esta regra está na lista de splits editáveis
          if (splitsEditaveis[r.colaborador] !== undefined &&
              r.centro_custo === values.centro_custo &&
              fabRegra === fabricante) {
            return { ...r, split: splitsEditaveis[r.colaborador] };
          }
          return r;
        });
      }
      
      if (editingRegra) {
        // Editar: encontrar e substituir (chave = colab + cc + fab)
        const idx = novasRegras.findIndex(
          r => r.colaborador === editingRegra.colaborador && 
               r.centro_custo === editingRegra.centro_custo &&
               (r.fabricante || '') === (editingRegra.fabricante || '')
        );
        if (idx >= 0) {
          novasRegras[idx] = values;
        }
      } else {
        // Adicionar: verificar duplicata (colab + cc + fab)
        const existe = novasRegras.some(
          r => r.colaborador === values.colaborador && 
               r.centro_custo === values.centro_custo &&
               (r.fabricante || '') === fabricante
        );
        if (existe) {
          const fabLabel = fabricante || 'TODOS';
          message.error(`Já existe uma regra para ${values.colaborador} no CC ${values.centro_custo} / Fab ${fabLabel}`);
          return;
        }
        novasRegras.push(values);
      }
      
      // Salvar no backend
      setSaving(true);
      await metodoV2API.salvarAba('REGRAS_COMISSAO_CC_V2', novasRegras, true);
      
      setRegrasCC(novasRegras);
      setModalVisible(false);
      form.resetFields();
      setSelectedCC(null);
      setSelectedFab(null);
      setSelectedColaborador(null);
      setShowSplitField(false);
      setSplitRequired(false);
      setOutrosDoMesmoCargo([]);
      setSplitsEditaveis({});
      message.success('Regra salva com sucesso!');
      
    } catch (error) {
      console.error('Erro ao salvar regra CC:', error);
      message.error('Erro ao salvar: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  // Excluir regra
  const handleDeleteRegra = async (regra) => {
    try {
      const novasRegras = regrasCC.filter(
        r => !(r.colaborador === regra.colaborador && 
               r.centro_custo === regra.centro_custo &&
               (r.fabricante || '') === (regra.fabricante || ''))
      );
      
      setSaving(true);
      await metodoV2API.salvarAba('REGRAS_COMISSAO_CC_V2', novasRegras, true);
      
      setRegrasCC(novasRegras);
      message.success('Regra excluída!');
      
    } catch (error) {
      console.error('Erro ao excluir regra CC:', error);
      message.error('Erro ao excluir: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  // Formatar moeda
  const formatCurrency = (value) => {
    if (value == null || isNaN(value)) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Obter descrição do CC
  const getCCDescricao = (codigo) => {
    return centrosCustoDescricoes[codigo] || codigo;
  };

  // Obter todas as faixas de uma regra em formato estruturado
  const getFaixasFromRecord = (record) => {
    const faixas = [];
    for (let i = 1; i <= 5; i++) {
      const limite = record[`faixa_${i}_limite`];
      const taxa = record[`faixa_${i}_taxa`];
      if (taxa != null && limite != null) {
        faixas.push({ limite, taxa });
      }
    }
    return faixas;
  };

  // Renderizar faixas com limites inferior/superior
  const renderFaixas = (record) => {
    const faixas = getFaixasFromRecord(record);
    if (faixas.length === 0) return <Text type="secondary">Sem faixas</Text>;

    return (
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        {faixas.map((faixa, idx) => {
          const limiteInferior = faixa.limite;
          // Limite superior é o limite da próxima faixa, ou infinito se for a última
          const limiteSuperior = idx < faixas.length - 1 ? faixas[idx + 1].limite : null;
          
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={{ fontSize: 12 }}>
                {formatCurrency(limiteInferior)} até {limiteSuperior ? formatCurrency(limiteSuperior) : '∞'}
              </Text>
              <Tag color="green" style={{ margin: 0 }}>{faixa.taxa}%</Tag>
            </div>
          );
        })}
      </Space>
    );
  };

  // Colunas da tabela
  const columns = [
    {
      title: 'Colaborador',
      dataIndex: 'colaborador',
      key: 'colaborador',
      width: 150,
      sorter: (a, b) => a.colaborador.localeCompare(b.colaborador),
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Centro de Custo',
      dataIndex: 'centro_custo',
      key: 'centro_custo',
      width: 140,
      sorter: (a, b) => a.centro_custo.localeCompare(b.centro_custo),
      render: (codigo) => (
        <Tooltip title={getCCDescricao(codigo)}>
          <Tag color="blue" icon={<BankOutlined />}>
            {codigo}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: 'Fabricante',
      dataIndex: 'fabricante',
      key: 'fabricante',
      width: 130,
      sorter: (a, b) => (a.fabricante || '').localeCompare(b.fabricante || ''),
      render: (fab) => (
        fab && fab.trim() ? (
          <Tag color="purple" icon={<ShopOutlined />}>
            {fab}
          </Tag>
        ) : (
          <Tag color="default">TODOS</Tag>
        )
      ),
      filters: [
        { text: 'TODOS (Genérica)', value: '' },
        ...ccFabData.fabricantes.map(f => ({ text: f, value: f })),
      ],
      onFilter: (value, record) => (record.fabricante || '') === value,
    },
    {
      title: (
        <Tooltip title="Split: divisão de comissão para Gerente Linha / Coordenador">
          <span>Split <PercentageOutlined /></span>
        </Tooltip>
      ),
      dataIndex: 'split',
      key: 'split',
      width: 80,
      align: 'center',
      render: (split, record) => {
        const cargo = getCargoColaborador(record.colaborador);
        if (!cargoUsaSplit(cargo)) {
          return <Text type="secondary">-</Text>;
        }
        if (split == null) {
          return <Tag color="green">100%</Tag>;
        }
        return <Tag color="orange" icon={<TeamOutlined />}>{split}%</Tag>;
      },
      sorter: (a, b) => (a.split || 100) - (b.split || 100),
    },
    {
      title: 'Faixas de Comissão',
      key: 'faixas',
      render: (_, record) => renderFaixas(record),
    },
    {
      title: 'Ações',
      key: 'acoes',
      align: 'center',
      render: (_, record) => (
        <Space>
          <Tooltip title="Editar">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Excluir esta regra?"
            onConfirm={() => handleDeleteRegra(record)}
            okText="Sim"
            cancelText="Não"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Cabeçalho com informações */}
      <Alert
        message="Regras de Comissão por Centro de Custo + Fabricante"
        description={
          <span>
            Configure as faixas de comissão por Centro de Custo, opcionalmente combinado com Fabricante. 
            <br />
            <strong>Especificidade:</strong> Regras com CC + Fabricante têm prioridade sobre regras genéricas (CC + "TODOS").
            <br />
            No modo Centro de Custo, a taxa é determinada pelo <strong>faturamento total mensal</strong> do 
            colaborador em cada combinação CC/Fab, e depois aplicada a cada item individualmente.
          </span>
        }
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: 16 }}
      />

      {/* Barra de ações */}
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            Adicionar Regra CC
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadData}
            loading={loading}
          >
            Recarregar
          </Button>
          <Text type="secondary">
            Total: {regrasCC.length} regra(s) configurada(s)
          </Text>
        </Space>
      </Card>

      {/* Tabela */}
      <Card>
        <Spin spinning={loading || saving}>
          {regrasCC.length === 0 ? (
            <Empty
              description="Nenhuma regra por Centro de Custo configurada"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
                Adicionar Primeira Regra
              </Button>
            </Empty>
          ) : (
            <Table
              dataSource={regrasCC}
              columns={columns}
              rowKey={(r) => `${r.colaborador}_${r.centro_custo}_${r.fabricante || 'TODOS'}`}
              pagination={{ pageSize: 10, showSizeChanger: true }}
              size="middle"
            />
          )}
        </Spin>
      </Card>

      {/* Modal de Edição */}
      <Modal
        title={
          <Space>
            <BankOutlined style={{ color: '#1890ff' }} />
            <span>{editingRegra ? 'Editar Regra CC' : 'Nova Regra por Centro de Custo'}</span>
          </Space>
        }
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setSelectedCC(null);
          setSelectedFab(null);
        }}
        onOk={handleSaveRegra}
        confirmLoading={saving}
        okText="Salvar"
        cancelText="Cancelar"
        width={750}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="colaborador"
                label="Colaborador"
                rules={[{ required: true, message: 'Selecione o colaborador' }]}
              >
                <Select
                  placeholder="Selecione..."
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    String(option?.children).toLowerCase().includes(input.toLowerCase())
                  }
                  disabled={!!editingRegra}
                  onChange={(value) => {
                    setSelectedColaborador(value);
                    atualizarEstadoSplit(value, selectedCC, selectedFab);
                  }}
                >
                  {colaboradores
                    .filter(c => c.nome_colaborador)
                    .map(c => (
                      <Select.Option key={c.nome_colaborador} value={c.nome_colaborador}>
                        {c.nome_colaborador} {c.cargo ? `(${c.cargo})` : ''}
                      </Select.Option>
                    ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="centro_custo"
                label="Centro de Custo"
                rules={[{ required: true, message: 'Selecione o Centro de Custo' }]}
              >
                <Select
                  placeholder="Selecione..."
                  showSearch
                  disabled={!!editingRegra}
                  onChange={(value) => {
                    setSelectedCC(value);
                    atualizarEstadoSplit(selectedColaborador, value, selectedFab);
                    // Se fabricante selecionado não existe no novo CC, limpar
                    if (selectedFab && ccFabData.mapeamento[value] && 
                        !ccFabData.mapeamento[value].includes(selectedFab)) {
                      form.setFieldValue('fabricante', '');
                      setSelectedFab(null);
                    }
                  }}
                >
                  {ccsFilteredByFab.map(cc => (
                    <Select.Option key={cc.codigo} value={cc.codigo}>
                      {cc.codigo} - {cc.descricao}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="fabricante"
                label={
                  <Space>
                    Fabricante
                    <Tooltip title="Deixe como 'TODOS' para criar regra genérica (fallback). Regras com fabricante específico têm prioridade.">
                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                    </Tooltip>
                  </Space>
                }
              >
                <Select
                  placeholder="TODOS (genérica)"
                  allowClear
                  showSearch
                  disabled={!!editingRegra}
                  onChange={(value) => {
                    const fabValue = value || '';
                    setSelectedFab(fabValue);
                    atualizarEstadoSplit(selectedColaborador, selectedCC, fabValue);
                  }}
                >
                  <Select.Option key="__TODOS__" value="">
                    <Tag color="default">TODOS</Tag> (regra genérica)
                  </Select.Option>
                  {fabricantesFiltered.map(fab => (
                    <Select.Option key={fab} value={fab}>
                      <Tag color="purple" icon={<ShopOutlined />}>{fab}</Tag>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {/* Campo de Split - Visível apenas para Gerente Linha / Coordenador */}
          {showSplitField && (
            <>
              {/* Se criando nova regra com conflito: edição inline de TODOS os splits */}
              {!editingRegra && outrosDoMesmoCargo.length > 0 && (
                <>
                  <Alert
                    message={
                      <Space>
                        <TeamOutlined />
                        <span>
                          <strong>Divisão de Comissão:</strong> Defina o split para cada <strong>{getCargoColaborador(selectedColaborador)}</strong> nesta regra.
                        </span>
                      </Space>
                    }
                    description={
                      <span>
                        A soma dos splits deve ser exatamente <strong>100%</strong>. 
                        Soma atual: <strong style={{ color: Math.abs((Object.values(splitsEditaveis).reduce((a, b) => a + (b || 0), 0) + (form.getFieldValue('split') || 0)) - 100) < 0.01 ? '#52c41a' : '#ff4d4f' }}>
                          {(Object.values(splitsEditaveis).reduce((a, b) => a + (b || 0), 0) + (form.getFieldValue('split') || 0)).toFixed(0)}%
                        </strong>
                      </span>
                    }
                    type="info"
                    showIcon={false}
                    style={{ marginBottom: 16 }}
                  />
                  <Row gutter={16}>
                    {/* Campos de split para colaboradores existentes */}
                    {outrosDoMesmoCargo.map((outro) => (
                      <Col span={8} key={outro.nome}>
                        <Form.Item
                          label={
                            <Space>
                              <Tag color="blue">{outro.nome}</Tag>
                              <span style={{ fontSize: '12px', color: '#888' }}>(existente)</span>
                            </Space>
                          }
                        >
                          <InputNumber
                            style={{ width: '100%' }}
                            value={splitsEditaveis[outro.nome]}
                            onChange={(value) => {
                              setSplitsEditaveis(prev => ({
                                ...prev,
                                [outro.nome]: value || 0
                              }));
                            }}
                            min={1}
                            max={99}
                            addonAfter="%"
                          />
                        </Form.Item>
                      </Col>
                    ))}
                    {/* Campo de split para o novo colaborador */}
                    <Col span={8}>
                      <Form.Item
                        name="split"
                        label={
                          <Space>
                            <Tag color="green">{selectedColaborador}</Tag>
                            <span style={{ fontSize: '12px', color: '#52c41a' }}>(novo)</span>
                          </Space>
                        }
                        rules={[
                          { required: true, message: 'Defina o split' },
                        ]}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          placeholder={`Ex: ${Math.max(1, 100 - Object.values(splitsEditaveis).reduce((a, b) => a + (b || 0), 0))}`}
                          min={1}
                          max={99}
                          addonAfter="%"
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              )}
              
              {/* Se editando regra existente OU único do cargo: campo simples */}
              {(editingRegra || outrosDoMesmoCargo.length === 0) && (
                <Row gutter={16}>
                  <Col span={8}>
                    <Form.Item
                      name="split"
                      label={
                        <Space>
                          Split (%)
                          <Tooltip title="Percentual de divisão da comissão. Soma dos splits de mesmo cargo deve ser 100%.">
                            <InfoCircleOutlined style={{ color: '#1890ff' }} />
                          </Tooltip>
                        </Space>
                      }
                      rules={[
                        { required: splitRequired, message: 'Defina o percentual de split' },
                      ]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        placeholder="Ex: 100"
                        min={1}
                        max={100}
                        addonAfter="%"
                      />
                    </Form.Item>
                  </Col>
                </Row>
              )}
            </>
          )}

          <Divider />
          
          <Title level={5}>Faixas de Comissão</Title>
          <Alert
            message="Como funcionam os limites das faixas?"
            description={
              <div>
                <p style={{ marginBottom: 8 }}>
                  <strong>Limite Inferior:</strong> Define o ponto de partida da faixa (inclusive).
                </p>
                <p style={{ marginBottom: 8 }}>
                  <strong>Limite Superior:</strong> É automaticamente determinado pelo limite inferior da próxima faixa.
                </p>
                <p style={{ marginBottom: 0 }}>
                  A <strong>última faixa configurada</strong> sempre se estende até infinito (∞).
                </p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          {[1, 2, 3, 4, 5].map((n) => (
            <FaixaRow key={n} n={n} form={form} />
          ))}
        </Form>
      </Modal>
    </div>
  );
};

export default RegrasCCEditorV2;
