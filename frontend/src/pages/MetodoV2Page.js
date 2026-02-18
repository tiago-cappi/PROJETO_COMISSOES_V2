import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  message,
  Spin,
  Alert,
  Empty,
  Divider,
  Row,
  Col,
  Statistic,
  Tag,
  Tabs,
  Modal,
  Select,
} from 'antd';
import {
  PlusOutlined,
  SaveOutlined,
  ReloadOutlined,
  UserOutlined,
  DollarOutlined,
  PercentageOutlined,
  InfoCircleOutlined,
  ApartmentOutlined,
  TeamOutlined,
  SettingOutlined,
  FileTextOutlined,
  UserAddOutlined,
  BarChartOutlined,
  BankOutlined,
} from '@ant-design/icons';
import { 
  ColaboradorConfigCard,
  HierarquiaEditorV2_Metodo, 
  ColaboradoresCargosEditorV2_Metodo,
  ResultadosV2Tab,
  RegrasCCEditorV2,
} from '../components/metodo_v2';
import { metodoV2API } from '../services/api';

const { Title, Text, Paragraph } = Typography;

/**
 * Página de configuração da Metodologia V2 de Comissões.
 * 
 * Nova Arquitetura:
 * - Colaborador = Nome + Cargo + Lista de Regras
 * - Cada Regra = Filtros Hierárquicos (até 5) + Faixas de Comissão (até 5)
 * - Prioridade: regra mais específica vence
 * - Comissão baseada em faturamento absoluto (R$), não FC%
 */
const MetodoV2Page = () => {
  // Estado principal
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [colaboradores, setColaboradores] = useState([]);
  const [configExiste, setConfigExiste] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Estado para modal de adição de colaborador
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [selectedColabToAdd, setSelectedColabToAdd] = useState(null);
  const [colaboradoresDisponiveis, setColaboradoresDisponiveis] = useState([]);
  
  // Lookups (dados de referência)
  const [lookups, setLookups] = useState({
    cargos: [],
    hierarquias: {
      linhas: [],
      grupos: [],
      subgrupos: [],
      tipos_mercadoria: [],
      fabricantes: [],
    },
  });

  // Carregar configuração atual
  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const [configRes, lookupsRes, colaboradoresV2Res] = await Promise.all([
        metodoV2API.getConfig(),
        metodoV2API.getLookups(),
        metodoV2API.lerAba('COLABORADORES_V2', { allPages: true }),
      ]);

      const colaboradoresConfig = configRes.data.colaboradores || [];
      const colaboradoresSheet = colaboradoresV2Res.data?.data || [];
      const sheetMap = new Map(
        colaboradoresSheet
          .filter((c) => c.nome_colaborador)
          .map((c) => [
            c.nome_colaborador,
            {
              tipo_comissao: (c.tipo_comissao || 'faturamento').toString().toLowerCase(),
              taxa_adiantamento_pct: c.taxa_adiantamento_pct !== undefined && c.taxa_adiantamento_pct !== ''
                ? Number(c.taxa_adiantamento_pct)
                : null,
            },
          ])
      );
      const colaboradoresMerged = colaboradoresConfig.map((c) => {
        const meta = sheetMap.get(c.nome);
        return {
          ...c,
          tipo_comissao: meta?.tipo_comissao || 'faturamento',
          taxa_adiantamento_pct: meta?.taxa_adiantamento_pct ?? null,
        };
      });

      setColaboradores(colaboradoresMerged);
      setConfigExiste(configRes.data.existe || false);
      setLookups({
        cargos: lookupsRes.data.cargos || [],
        hierarquias: lookupsRes.data.hierarquias || {},
      });
      
      // Guardar colaboradores disponíveis para dropdown
      setColaboradoresDisponiveis(colaboradoresV2Res.data?.data || []);
      
      setHasChanges(false);

    } catch (error) {
      console.error('Erro ao carregar configuração V2:', error);
      message.error('Erro ao carregar configuração: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  }, []);

  // Carregar ao montar
  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // Salvar configuração
  const handleSave = async () => {
    // Validar antes de salvar
    const erros = [];
    colaboradores.forEach((c, idx) => {
      if (!c.nome?.trim()) {
        erros.push(`Colaborador #${idx + 1}: Nome é obrigatório`);
      }
      if (!c.regras?.length) {
        erros.push(`${c.nome || `Colaborador #${idx + 1}`}: Adicione pelo menos uma regra de comissão`);
      }
      // Validar faixas em cada regra
      (c.regras || []).forEach((regra, rIdx) => {
        if (!regra.faixas?.length) {
          erros.push(`${c.nome} → Regra #${rIdx + 1}: Adicione pelo menos uma faixa de comissão`);
        }
      });
    });

    if (erros.length > 0) {
      message.error(
        <div>
          <strong>Erros de validação:</strong>
          <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
            {erros.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
            {erros.length > 5 && <li>... e mais {erros.length - 5} erro(s)</li>}
          </ul>
        </div>
      );
      return;
    }

    setSaving(true);
    try {
      // Converter formato para API (nome -> nome_colaborador se necessário)
      const payload = {
        colaboradores: colaboradores.map(c => ({
          nome: c.nome,
          cargo: c.cargo || null,
          regras: (c.regras || []).map(r => ({
            regra_id: r.regra_id,
            linha: r.linha || null,
            grupo: r.grupo || null,
            subgrupo: r.subgrupo || null,
            tipo_mercadoria: r.tipo_mercadoria || null,
            fabricante: r.fabricante || null,
            faixas: r.faixas || [],
          })),
        })),
      };
      
      await metodoV2API.saveConfig(payload);
      message.success('Configuração salva com sucesso!');
      setHasChanges(false);
      setConfigExiste(true);
      // Recarregar do backend
      await loadConfig();
    } catch (error) {
      console.error('Erro ao salvar configuração V2:', error);
      const errorDetail = error.response?.data?.detail;
      const errorMsg = typeof errorDetail === 'object' 
        ? JSON.stringify(errorDetail) 
        : (errorDetail || error.message || 'Erro desconhecido');
      message.error('Erro ao salvar: ' + errorMsg);
    } finally {
      setSaving(false);
    }
  };

  // Adicionar novo colaborador - abre modal de seleção
  const handleAddColaborador = () => {
    setSelectedColabToAdd(null);
    setAddModalVisible(true);
  };

  // Confirmar adição de colaborador do dropdown
  const handleConfirmAddColaborador = () => {
    if (!selectedColabToAdd) {
      message.warning('Selecione um colaborador');
      return;
    }

    // Verificar se já está na lista
    const jaExiste = colaboradores.some(c => c.nome === selectedColabToAdd.nome);
    if (jaExiste) {
      message.warning(`${selectedColabToAdd.nome} já está configurado(a)`);
      return;
    }

    const novoColaborador = {
      nome: selectedColabToAdd.nome,
      cargo: selectedColabToAdd.cargo || null,
      regras: [
        {
          regra_id: `R${Date.now()}`,
          linha: null,
          grupo: null,
          subgrupo: null,
          tipo_mercadoria: null,
          fabricante: null,
          faixas: [
            { limite_inferior: 0, limite_superior: 49999.99, taxa_comissao_pct: 1.0 },
            { limite_inferior: 50000, limite_superior: 99999.99, taxa_comissao_pct: 1.5 },
            { limite_inferior: 100000, limite_superior: null, taxa_comissao_pct: 2.0 },
          ],
        },
      ],
    };
    
    setColaboradores([...colaboradores, novoColaborador]);
    setHasChanges(true);
    setAddModalVisible(false);
    setSelectedColabToAdd(null);
    message.success(`${novoColaborador.nome} adicionado(a) com sucesso!`);
  };

  // Colaboradores disponíveis para adicionar (excluindo já configurados)
  const colaboradoresParaAdicionar = useMemo(() => {
    const jaConfigurados = new Set(colaboradores.map(c => c.nome));
    // COLABORADORES_V2 usa 'nome_colaborador', não 'nome'
    return colaboradoresDisponiveis
      .filter(c => c.nome_colaborador && !jaConfigurados.has(c.nome_colaborador))
      .map(c => ({ nome: c.nome_colaborador, cargo: c.cargo }));
  }, [colaboradoresDisponiveis, colaboradores]);

  // Atualizar colaborador
  const handleUpdateColaborador = (index, colaboradorAtualizado) => {
    const novosColaboradores = [...colaboradores];
    novosColaboradores[index] = colaboradorAtualizado;
    setColaboradores(novosColaboradores);
    setHasChanges(true);
  };

  // Remover colaborador
  const handleRemoveColaborador = (index) => {
    const novosColaboradores = colaboradores.filter((_, i) => i !== index);
    setColaboradores(novosColaboradores);
    setHasChanges(true);
    message.info('Colaborador removido. Salve para confirmar.');
  };

  // Estatísticas gerais
  const totalColaboradores = colaboradores.length;
  const totalRegras = colaboradores.reduce((acc, c) => acc + (c.regras?.length || 0), 0);
  const totalFaixas = colaboradores.reduce(
    (acc, c) => acc + (c.regras || []).reduce((a2, r) => a2 + (r.faixas?.length || 0), 0),
    0
  );

  // ==================== TAB: CONFIGURAÇÃO DE REGRAS ====================
  const ConfiguracaoRegrasTab = (
    <>
      {/* Alerta de mudanças não salvas */}
      {hasChanges && (
        <Alert
          message="Você tem alterações não salvas"
          description="Clique em 'Salvar Configurações' para persistir as mudanças."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Card de Estatísticas */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={24}>
          <Col xs={24} sm={8}>
            <Statistic
              title="Total de Colaboradores"
              value={totalColaboradores}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Statistic
              title="Total de Regras"
              value={totalRegras}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Statistic
              title="Total de Faixas"
              value={totalFaixas}
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Barra de Ações */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
            disabled={!hasChanges}
          >
            Salvar Configurações
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={handleAddColaborador}
          >
            Adicionar Colaborador
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadConfig}
            loading={loading}
          >
            Recarregar
          </Button>
          {!configExiste && (
            <Tag color="orange" icon={<InfoCircleOutlined />}>
              Nenhuma configuração salva ainda
            </Tag>
          )}
        </Space>
      </Card>

      {/* Lista de Colaboradores */}
      <Spin spinning={loading}>
        {colaboradores.length === 0 ? (
          <Empty
            description={
              <span>
                Nenhum colaborador configurado.
                <br />
                Clique em "Adicionar Colaborador" para começar.
              </span>
            }
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddColaborador}>
              Adicionar Primeiro Colaborador
            </Button>
          </Empty>
        ) : (
          <div>
            {colaboradores.map((colaborador, index) => (
              <ColaboradorConfigCard
                key={colaborador.nome || index}
                colaborador={colaborador}
                cargos={lookups.cargos}
                hierarquias={lookups.hierarquias}
                onUpdate={(colabAtualizado) => handleUpdateColaborador(index, colabAtualizado)}
                onDelete={() => handleRemoveColaborador(index)}
              />
            ))}
          </div>
        )}
      </Spin>

      {/* Informações sobre a metodologia */}
      <Divider />
      <Card title="ℹ️ Sobre a Nova Metodologia V2" size="small">
        <Row gutter={16}>
          <Col xs={24} md={8}>
            <Title level={5}>Regras por Hierarquia</Title>
            <Text type="secondary">
              Cada colaborador pode ter múltiplas regras de comissão.
              <br />
              Cada regra filtra por: Linha, Grupo, Subgrupo, Tipo, Fabricante.
            </Text>
          </Col>
          <Col xs={24} md={8}>
            <Title level={5}>Prioridade por Especificidade</Title>
            <Text type="secondary">
              Regra mais específica vence (mais campos preenchidos).
              <br />
              Campos vazios = wildcard (vale para qualquer valor).
            </Text>
          </Col>
          <Col xs={24} md={8}>
            <Title level={5}>Faixas de Faturamento</Title>
            <Text type="secondary">
              Comissão baseada em faturamento absoluto (R$).
              <br />
              Ex: R$ 0-50k = 1%, R$ 50k-100k = 1.5%, ≥R$ 100k = 2%
            </Text>
          </Col>
        </Row>
        <Divider style={{ margin: '12px 0' }} />
        <Text strong style={{ color: '#1890ff' }}>
          💡 As atribuições de carteira (Aba "Atribuições") definem quais hierarquias 
          cada colaborador atende. As regras aqui definem a taxa de comissão para cada faixa de faturamento.
        </Text>
      </Card>

      {/* Modal de Adição de Colaborador */}
      <Modal
        title={
          <Space>
            <UserAddOutlined style={{ color: '#1890ff' }} />
            <span>Adicionar Colaborador</span>
          </Space>
        }
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          setSelectedColabToAdd(null);
        }}
        onOk={handleConfirmAddColaborador}
        okText="Adicionar"
        cancelText="Cancelar"
        width={500}
      >
        <Alert
          message="Selecione um colaborador cadastrado"
          description="Escolha um colaborador da lista de COLABORADORES_V2 para configurar suas regras de comissão."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Select
          style={{ width: '100%' }}
          placeholder="Selecione um colaborador..."
          showSearch
          allowClear
          value={selectedColabToAdd?.nome || undefined}
          onChange={(value) => {
            const colab = colaboradoresParaAdicionar.find(c => c.nome === value);
            setSelectedColabToAdd(colab || null);
          }}
          filterOption={(input, option) =>
            String(option?.children).toLowerCase().includes(input.toLowerCase())
          }
          optionLabelProp="label"
        >
          {colaboradoresParaAdicionar.map(colab => (
            <Select.Option 
              key={colab.nome} 
              value={colab.nome}
              label={colab.nome}
            >
              <Space>
                <UserOutlined />
                <span>{colab.nome}</span>
                {colab.cargo && <Tag color="blue">{colab.cargo}</Tag>}
              </Space>
            </Select.Option>
          ))}
        </Select>
        
        {selectedColabToAdd && (
          <Card size="small" style={{ marginTop: 16 }}>
            <Space direction="vertical">
              <Text strong>Colaborador selecionado:</Text>
              <Text>{selectedColabToAdd.nome}</Text>
              {selectedColabToAdd.cargo && (
                <Text type="secondary">Cargo: {selectedColabToAdd.cargo}</Text>
              )}
            </Space>
          </Card>
        )}
        
        {colaboradoresParaAdicionar.length === 0 && (
          <Alert
            message="Nenhum colaborador disponível"
            description="Todos os colaboradores cadastrados já estão configurados, ou não há colaboradores em COLABORADORES_V2."
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Modal>
    </>
  );

  // ==================== TAB ITEMS ====================
  const tabItems = [
    {
      key: 'resultados',
      label: (
        <span>
          <BarChartOutlined />
          Resultados
        </span>
      ),
      children: <ResultadosV2Tab />,
    },
    {
      key: 'hierarquia',
      label: (
        <span>
          <ApartmentOutlined />
          Hierarquia
        </span>
      ),
      children: <HierarquiaEditorV2_Metodo />,
    },
    {
      key: 'colaboradores',
      label: (
        <span>
          <UserOutlined />
          Colaboradores/Cargos
        </span>
      ),
      children: <ColaboradoresCargosEditorV2_Metodo />,
    },
    {
      key: 'regras',
      label: (
        <span>
          <SettingOutlined />
          Configuração de Regras
        </span>
      ),
      children: (
        <Tabs
          defaultActiveKey="hierarquia"
          type="card"
          items={[
            {
              key: 'hierarquia',
              label: (
                <span>
                  <ApartmentOutlined />
                  Por Hierarquia
                </span>
              ),
              children: ConfiguracaoRegrasTab,
            },
            {
              key: 'centro_custo',
              label: (
                <span>
                  <BankOutlined />
                  Por Centro de Custo
                </span>
              ),
              children: <RegrasCCEditorV2 />,
            },
          ]}
        />
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* Cabeçalho */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <PercentageOutlined style={{ marginRight: 12 }} />
          Metodologia V2 - Configuração de Comissões
        </Title>
        <Paragraph type="secondary">
          Configure hierarquia, atribuições, colaboradores e regras de comissão por faixa de faturamento.
          Esta metodologia é completamente separada e independente do cálculo principal.
        </Paragraph>
      </div>

      <Tabs items={tabItems} defaultActiveKey="resultados" size="large" />
    </div>
  );
};

export default MetodoV2Page;
