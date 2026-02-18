import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Card,
  Table,
  DatePicker,
  Button,
  Space,
  Typography,
  Statistic,
  Row,
  Col,
  Tag,
  Tooltip,
  Empty,
  Spin,
  message,
  Alert,
  Divider,
  Radio,
  Modal,
  Popconfirm,
} from 'antd';
import {
  ReloadOutlined,
  EyeOutlined,
  DollarOutlined,
  TeamOutlined,
  FileTextOutlined,
  DownloadOutlined,
  CalculatorOutlined,
  ApartmentOutlined,
  BankOutlined,
  DeleteOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { metodoV2API } from '../../services/api';
import DetalhesColaboradorV2Modal from './DetalhesColaboradorV2Modal';

const { Title, Text } = Typography;

/**
 * Tab de Resultados do cálculo V2.
 * 
 * Exibe:
 * - DatePicker para selecionar mês/ano
 * - Cards com estatísticas (total colaboradores, total comissão)
 * - Tabela resumo por colaborador
 * - Modal de drill-down: Colaborador → Processos → Itens
 */
const ResultadosV2Tab = () => {
  // Estado do período selecionado
  const [mesAno, setMesAno] = useState(dayjs());
  
  // Estado do modo de cálculo
  const [modoCalculo, setModoCalculo] = useState('hierarquia');
  
  // Estado dos dados
  const [loading, setLoading] = useState(false);
  const [calculando, setCalculando] = useState(false);
  const [resultados, setResultados] = useState(null);
  const [erro, setErro] = useState(null);

  // Estado dos resultados de recebimento V2
  const [recebimentoLoading, setRecebimentoLoading] = useState(false);
  const [recebimentoCalculando, setRecebimentoCalculando] = useState(false);
  const [recebimentoResultados, setRecebimentoResultados] = useState(null);
  const [recebimentoErro, setRecebimentoErro] = useState(null);
  
  // Estado do modal de detalhes
  const [modalVisible, setModalVisible] = useState(false);
  const [colaboradorSelecionado, setColaboradorSelecionado] = useState(null);
  const [detalhesColaborador, setDetalhesColaborador] = useState([]);

  // Estado do modal de períodos disponíveis
  const [periodoModalVisible, setPeriodoModalVisible] = useState(false);
  const [periodosDisponiveis, setPeriodosDisponiveis] = useState([]);
  const [periodosLoading, setPeriodosLoading] = useState(false);

  // Controle de concorrência para evitar respostas fora de ordem
  const latestRequestRef = useRef(0);

  // Carregar resultados
  const carregarResultados = useCallback(async () => {
    if (!mesAno) return;

    const requestId = ++latestRequestRef.current;

    setLoading(true);
    setErro(null);
    
    try {
      const mes = mesAno.month() + 1;
      const ano = mesAno.year();
      
      const response = await metodoV2API.getResultados(mes, ano, modoCalculo);

      if (requestId !== latestRequestRef.current) return;
      
      if (response.data) {
        setResultados(response.data);
      }
    } catch (error) {
      if (requestId !== latestRequestRef.current) return;
      console.error('Erro ao carregar resultados V2:', error);
      if (error.response?.status === 404) {
        const modoLabel = modoCalculo === 'centro_custo' ? 'Centro de Custo' : 'Hierarquia';
        setErro(`Nenhum resultado encontrado para ${mesAno.format('MM/YYYY')} (modo: ${modoLabel}). Execute o cálculo V2 primeiro.`);
      } else {
        setErro(error.response?.data?.detail || 'Erro ao carregar resultados');
      }
      setResultados(null);
    } finally {
      if (requestId === latestRequestRef.current) {
        setLoading(false);
      }
    }
  }, [mesAno, modoCalculo]);

  const carregarRecebimentoResultados = useCallback(async () => {
    if (!mesAno) return;

    setRecebimentoLoading(true);
    setRecebimentoErro(null);

    try {
      const mes = mesAno.month() + 1;
      const ano = mesAno.year();
      const response = await metodoV2API.getResultadosRecebimento(mes, ano, modoCalculo);
      if (response.data) {
        setRecebimentoResultados(response.data);
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setRecebimentoErro('Sem resultados de recebimento para o período selecionado.');
      } else {
        setRecebimentoErro(error.response?.data?.detail || 'Erro ao carregar recebimento V2');
      }
      setRecebimentoResultados(null);
    } finally {
      setRecebimentoLoading(false);
    }
  }, [mesAno, modoCalculo]);

  const carregarPeriodosDisponiveis = useCallback(async () => {
    setPeriodosLoading(true);
    try {
      const response = await metodoV2API.listarResultadosDisponiveis();
      setPeriodosDisponiveis(response.data?.periodos || []);
    } catch (error) {
      console.error('Erro ao carregar períodos disponíveis:', error);
      message.error('Erro ao carregar períodos disponíveis');
      setPeriodosDisponiveis([]);
    } finally {
      setPeriodosLoading(false);
    }
  }, []);

  // Calcular comissões
  const calcularComissoes = async () => {
    if (!mesAno) return;
    
    setCalculando(true);
    setErro(null);
    
    try {
      const mes = mesAno.month() + 1;
      const ano = mesAno.year();
      
      const modoLabel = modoCalculo === 'centro_custo' ? 'Centro de Custo' : 'Hierarquia';
      message.loading({ content: `Calculando comissões V2 (${modoLabel})...`, key: 'calcV2', duration: 0 });
      
      const response = await metodoV2API.executar(mes, ano, modoCalculo);
      
      if (response.data?.status === 'ok') {
        message.success({ 
          content: `Cálculo V2 (${modoLabel}) concluído! ${response.data.total_colaboradores} colaborador(es) processado(s).`, 
          key: 'calcV2' 
        });
        // Recarregar resultados após cálculo
        await carregarResultados();
        await carregarPeriodosDisponiveis();
      } else {
        throw new Error(response.data?.erro || 'Erro desconhecido');
      }
    } catch (error) {
      console.error('Erro ao calcular V2:', error);
      message.error({ 
        content: `Erro no cálculo: ${error.response?.data?.detail || error.message}`, 
        key: 'calcV2' 
      });
    } finally {
      setCalculando(false);
    }
  };

  const calcularRecebimento = async () => {
    if (!mesAno) return;

    setRecebimentoCalculando(true);
    setRecebimentoErro(null);

    try {
      const mes = mesAno.month() + 1;
      const ano = mesAno.year();

      const modoLabel = modoCalculo === 'centro_custo' ? 'Centro de Custo' : 'Hierarquia';
      message.loading({ content: `Calculando recebimento V2 (${modoLabel})...`, key: 'calcRecV2', duration: 0 });

      const response = await metodoV2API.executarRecebimento(mes, ano, modoCalculo);

      if (response.data?.status === 'ok') {
        message.success({
          content: `Recebimento V2 (${modoLabel}) concluído!`,
          key: 'calcRecV2',
        });
        await carregarRecebimentoResultados();
      } else {
        throw new Error(response.data?.erro || 'Erro desconhecido');
      }
    } catch (error) {
      message.error({
        content: `Erro no recebimento: ${error.response?.data?.detail || error.message}`,
        key: 'calcRecV2',
      });
    } finally {
      setRecebimentoCalculando(false);
    }
  };

  const baixarRecebimento = async () => {
    if (!mesAno) return;

    try {
      const mes = mesAno.month() + 1;
      const ano = mesAno.year();
      const response = await metodoV2API.baixarRecebimento(mes, ano, modoCalculo);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Comissoes_Recebimento_V2_${String(mes).padStart(2, '0')}_${ano}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('Download iniciado!');
    } catch (error) {
      message.error('Erro ao baixar recebimento V2.');
    }
  };

  // Carregar ao montar ou mudar período
  useEffect(() => {
    carregarResultados();
    carregarRecebimentoResultados();
  }, [carregarResultados, carregarRecebimentoResultados]);

  useEffect(() => {
    carregarPeriodosDisponiveis();
  }, [carregarPeriodosDisponiveis]);

  useEffect(() => {
    setResultados(null);
    setErro(null);
    setRecebimentoResultados(null);
    setRecebimentoErro(null);
    setModalVisible(false);
    setColaboradorSelecionado(null);
    setDetalhesColaborador([]);
  }, [modoCalculo]);

  useEffect(() => {
    setModalVisible(false);
    setColaboradorSelecionado(null);
    setDetalhesColaborador([]);
  }, [resultados]);

  const taxaMediaPorColaborador = useMemo(() => {
    if (!resultados?.detalhes || resultados.detalhes.length === 0) return {};

    const acc = {};
    resultados.detalhes.forEach((item) => {
      const nome = item.colaborador;
      if (!nome) return;

      const faturamento = item.faturamento ?? item.faturamento_item ?? 0;
      const taxa = item.faixa_taxa_pct ?? item.taxa_aplicada ?? 0;

      if (!acc[nome]) {
        acc[nome] = { faturamento: 0, somaFatTaxa: 0 };
      }

      acc[nome].faturamento += faturamento;
      acc[nome].somaFatTaxa += faturamento * taxa;
    });

    const map = {};
    Object.entries(acc).forEach(([nome, info]) => {
      map[nome] = info.faturamento > 0 ? (info.somaFatTaxa / info.faturamento) : 0;
    });

    return map;
  }, [resultados?.detalhes]);

  // Agregar resumo por colaborador (para modo CC com múltiplas regras)
  const resumoAgregado = useMemo(() => {
    if (!resultados?.resumo || modoCalculo !== 'centro_custo') {
      return (resultados?.resumo || []).map((row) => ({
        ...row,
        taxa_media_pct: taxaMediaPorColaborador[row.colaborador] ?? row.taxa_media_pct ?? 0,
      }));
    }
    
    // Agrupar por colaborador
    const porColaborador = {};
    
    resultados.resumo.forEach(row => {
      const nome = row.colaborador;
      
      if (!porColaborador[nome]) {
        porColaborador[nome] = {
          colaborador: nome,
          cargo: row.cargo,
          faturamento_total: 0,
          comissao_total: 0,
          qtd_itens: 0,
          centros_custo: new Set(),
          fabricantes: new Set(),
          regras: [],  // Lista de regras originais para drill-down
        };
      }
      
      const agg = porColaborador[nome];
      agg.faturamento_total += row.faturamento_total || 0;
      agg.comissao_total += row.comissao_total || 0;
      agg.qtd_itens += row.qtd_itens || 0;
      agg.centros_custo.add(row.centro_custo);
      agg.fabricantes.add(row.fabricante || 'TODOS');
      agg.regras.push(row);  // Guardar regra original
    });
    
    // Converter para array e calcular taxa média
    return Object.values(porColaborador).map(agg => ({
      ...agg,
      centros_custo: Array.from(agg.centros_custo).sort(),
      fabricantes: Array.from(agg.fabricantes).sort(),
      taxa_media_pct: taxaMediaPorColaborador[agg.colaborador] ?? (
        agg.faturamento_total > 0 
          ? (agg.comissao_total / agg.faturamento_total * 100) 
          : 0
      ),
    }));
  }, [resultados?.resumo, modoCalculo, taxaMediaPorColaborador]);

  // Abrir modal de detalhes do colaborador
  const handleVerDetalhes = (colaborador) => {
    setColaboradorSelecionado(colaborador);
    
    // Filtrar detalhes do colaborador
    if (resultados?.detalhes) {
      const detalhes = resultados.detalhes.filter(
        d => d.colaborador === colaborador.colaborador
      );
      setDetalhesColaborador(detalhes);
    }
    
    setModalVisible(true);
  };

  // Fechar modal
  const handleFecharModal = () => {
    setModalVisible(false);
    setColaboradorSelecionado(null);
    setDetalhesColaborador([]);
  };

  // Formatar moeda
  const formatCurrency = (value) => {
    if (value == null || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  // Colunas da tabela principal (por colaborador)
  const baseColumns = [
    {
      title: 'Colaborador',
      dataIndex: 'colaborador',
      key: 'colaborador',
      sorter: (a, b) => a.colaborador.localeCompare(b.colaborador),
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Cargo',
      dataIndex: 'cargo',
      key: 'cargo',
      render: (cargo) => (
        <Tag color={cargo?.includes('Gerente') ? 'blue' : 'green'}>
          {cargo || '-'}
        </Tag>
      ),
    },
    {
      title: 'Faturamento Total',
      dataIndex: 'faturamento_total',
      key: 'faturamento_total',
      align: 'right',
      sorter: (a, b) => a.faturamento_total - b.faturamento_total,
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Comissão Total',
      dataIndex: 'comissao_total',
      key: 'comissao_total',
      align: 'right',
      sorter: (a, b) => a.comissao_total - b.comissao_total,
      defaultSortOrder: 'descend',
      render: (value) => (
        <Text strong style={{ color: '#52c41a' }}>
          {formatCurrency(value)}
        </Text>
      ),
    },
    {
      title: 'Taxa Média',
      dataIndex: 'taxa_media_pct',
      key: 'taxa_media_pct',
      align: 'right',
      render: (value) => `${(value || 0).toFixed(2)}%`,
    },
    {
      title: 'Qtd. Itens',
      dataIndex: 'qtd_itens',
      key: 'qtd_itens',
      align: 'center',
      sorter: (a, b) => a.qtd_itens - b.qtd_itens,
      render: (value) => (
        <Tag color="blue">{value}</Tag>
      ),
    },
    {
      title: 'Ações',
      key: 'acoes',
      align: 'center',
      render: (_, record) => (
        <Tooltip title="Ver detalhes por processo">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleVerDetalhes(record)}
          >
            Detalhes
          </Button>
        </Tooltip>
      ),
    },
  ];

  // Coluna de Centro de Custo (só para modo CC - mostra lista)
  const colunaCentroCusto = {
    title: 'Centro de Custo',
    dataIndex: 'centros_custo',
    key: 'centros_custo',
    width: 150,
    render: (ccs) => {
      if (!ccs || ccs.length === 0) return '-';
      // Se é array (agregado), mostrar lista
      if (Array.isArray(ccs)) {
        return (
          <Space size={[0, 4]} wrap>
            {ccs.map(cc => (
              <Tag key={cc} color="blue" icon={<BankOutlined />}>{cc}</Tag>
            ))}
          </Space>
        );
      }
      // Se é string (não agregado), mostrar único
      return <Tag color="blue" icon={<BankOutlined />}>{ccs}</Tag>;
    },
  };

  // Coluna de Fabricante (só para modo CC - mostra lista)
  const colunaFabricante = {
    title: 'Fabricante',
    dataIndex: 'fabricantes',
    key: 'fabricantes',
    width: 150,
    render: (fabs) => {
      if (!fabs || fabs.length === 0) return '-';
      // Se é array (agregado), mostrar lista
      if (Array.isArray(fabs)) {
        return (
          <Space size={[0, 4]} wrap>
            {fabs.map(fab => (
              fab && fab !== 'TODOS' ? (
                <Tag key={fab} color="purple">{fab}</Tag>
              ) : (
                <Tag key="TODOS" color="default">TODOS</Tag>
              )
            ))}
          </Space>
        );
      }
      // Se é string (não agregado)
      return fabs !== 'TODOS' ? <Tag color="purple">{fabs}</Tag> : <Tag color="default">TODOS</Tag>;
    },
  };

  // Colunas finais baseadas no modo de cálculo
  const columns = useMemo(() => {
    if (modoCalculo === 'centro_custo') {
      // Inserir CC e Fabricante após Cargo (posição 2)
      const cols = [...baseColumns];
      cols.splice(2, 0, colunaCentroCusto, colunaFabricante);
      return cols;
    }
    return baseColumns;
  }, [modoCalculo, baseColumns]);

  const adiantamentosColumns = useMemo(() => ([
    { title: 'Colaborador', dataIndex: 'Colaborador', key: 'colaborador', width: 200 },
    { title: 'Documento', dataIndex: 'Documento', key: 'documento', width: 140 },
    { title: 'Documento Normalizado', dataIndex: 'Documento Normalizado', key: 'doc_norm', width: 180 },
    { title: 'Valor Base', dataIndex: 'Valor Base', key: 'valor_base', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Taxa (%)', dataIndex: 'Taxa (%)', key: 'taxa', align: 'right' },
    { title: 'Comissão', dataIndex: 'Comissão', key: 'comissao', align: 'right', render: (v) => formatCurrency(v || 0) },
  ]), []);

  const reconciliacoesColumns = useMemo(() => ([
    { title: 'Colaborador', dataIndex: 'Colaborador', key: 'colaborador', width: 200 },
    { title: 'Documento', dataIndex: 'Documento', key: 'documento', width: 140 },
    { title: 'Valor Adiantado', dataIndex: 'Valor Adiantado', key: 'valor_adiantado', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Comissão Adiantada', dataIndex: 'Comissão Adiantada', key: 'comissao_adiantada', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Valor Faturado', dataIndex: 'Valor Faturado', key: 'valor_faturado', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Comissão Real', dataIndex: 'Comissão Real', key: 'comissao_real', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Ajuste', dataIndex: 'Ajuste', key: 'ajuste', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Tipo Ajuste', dataIndex: 'Tipo Ajuste', key: 'tipo_ajuste', width: 140 },
  ]), []);

  const pendentesColumns = useMemo(() => ([
    { title: 'Documento', dataIndex: 'Documento', key: 'documento', width: 140 },
    { title: 'Colaborador', dataIndex: 'Colaborador ID', key: 'colaborador_id', width: 200 },
    { title: 'Estado', dataIndex: 'Estado', key: 'estado', width: 120 },
    { title: 'Valor Adiantado', dataIndex: 'Valor Adiantado', key: 'valor_adiantado', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Comissão Adiantada', dataIndex: 'Comissão Adiantada', key: 'comissao_adiantada', align: 'right', render: (v) => formatCurrency(v || 0) },
    { title: 'Data Adiantamento', dataIndex: 'Data Adiantamento', key: 'data_adiantamento' },
  ]), []);

  const periodosModo = useMemo(() => (
    periodosDisponiveis.filter((p) => p.modo_calculo === modoCalculo)
  ), [periodosDisponiveis, modoCalculo]);

  const isPeriodoDisponivel = useCallback((value) => {
    if (!value) return false;
    const mes = value.month() + 1;
    const ano = value.year();
    return periodosModo.some((p) => p.mes === mes && p.ano === ano);
  }, [periodosModo]);

  const monthCellRender = useCallback((current, info) => {
    if (info.type !== 'month') return info.originNode;
    if (!isPeriodoDisponivel(current)) return info.originNode;
    return (
      <div
        className="ant-picker-cell-inner"
        style={{
          border: '1px solid #52c41a',
          borderRadius: 4,
          padding: 2,
        }}
      >
        {current.format('MMM')}
      </div>
    );
  }, [isPeriodoDisponivel]);

  const totalFaturamento = useMemo(() => {
    if (!resultados) return 0;

    if (modoCalculo === 'centro_custo') {
      const detalhes = resultados.detalhes || [];
      if (!detalhes.length) {
        return resultados.resumo?.reduce(
          (sum, r) => sum + (r.faturamento_total || 0), 0
        ) || 0;
      }

      const itensUnicos = new Map();
      detalhes.forEach((d) => {
        const faturamento = d.faturamento_item ?? d.faturamento ?? 0;
        const chave = [
          d.processo || '',
          d.centro_custo || '',
          d.fabricante_item || '',
          faturamento,
        ].join('||');
        if (!itensUnicos.has(chave)) {
          itensUnicos.set(chave, faturamento);
        }
      });
      return Array.from(itensUnicos.values()).reduce((sum, v) => sum + (v || 0), 0);
    }

    return resultados.resumo?.reduce(
      (sum, r) => sum + (r.faturamento_total || 0), 0
    ) || 0;
  }, [resultados, modoCalculo]);

  const recebimentoListas = useMemo(() => {
    const adiantamentos = recebimentoResultados?.adiantamentos || recebimentoResultados?.adiantamentos_detalhes || [];
    const reconciliacoes = recebimentoResultados?.reconciliacoes || recebimentoResultados?.reconciliacoes_detalhes || [];
    const pendentes = recebimentoResultados?.pendentes || recebimentoResultados?.historico_pendente || [];
    return { adiantamentos, reconciliacoes, pendentes };
  }, [recebimentoResultados]);

  const recebimentoTotais = useMemo(() => {
    const totalAdiantamentos = recebimentoListas.adiantamentos.reduce(
      (sum, r) => sum + (Number(r['Comissão'] || r['Comissão Calculada'] || 0) || 0),
      0
    );
    const totalAjustes = recebimentoListas.reconciliacoes.reduce(
      (sum, r) => sum + (Number(r['Ajuste'] || 0) || 0),
      0
    );
    return {
      totalAdiantamentos,
      totalAjustes,
      qtdAdiantamentos: recebimentoListas.adiantamentos.length,
      qtdReconciliacoes: recebimentoListas.reconciliacoes.length,
      qtdPendentes: recebimentoListas.pendentes.length,
    };
  }, [recebimentoListas]);

  // Renderizar cards de estatísticas
  const renderEstatisticas = () => {
    if (!resultados) return null;
    
    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total de Colaboradores"
              value={resultados.total_colaboradores || resultados.resumo?.length || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Faturamento"
              value={totalFaturamento}
              precision={2}
              prefix={<FileTextOutlined />}
              formatter={(value) => formatCurrency(value)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Comissões"
              value={resultados.total_comissao || 0}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
              formatter={(value) => formatCurrency(value)}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  return (
    <div>
      {/* Cabeçalho com DatePicker e Modo de Cálculo */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="large" wrap>
          <div>
            <Text type="secondary" style={{ marginRight: 8 }}>Período:</Text>
            <DatePicker
              picker="month"
              value={mesAno}
              onChange={setMesAno}
              format="MM/YYYY"
              allowClear={false}
              style={{ width: 150 }}
              cellRender={monthCellRender}
              renderExtraFooter={() => (
                <Space size={[4, 4]} wrap>
                  <Text type="secondary">Disponíveis:</Text>
                  {periodosModo.length > 0 ? (
                    periodosModo.map((p) => (
                      <Tag key={`${p.ano}-${p.mes}-${p.modo_calculo}`} color="green">
                        {String(p.mes).padStart(2, '0')}/{p.ano}
                      </Tag>
                    ))
                  ) : (
                    <Text type="secondary">Nenhum</Text>
                  )}
                  <Button size="small" type="link" onClick={() => setPeriodoModalVisible(true)}>
                    Gerenciar
                  </Button>
                </Space>
              )}
            />
            <Button
              icon={<DownloadOutlined />}
              onClick={baixarRecebimento}
              style={{ marginLeft: 8 }}
              disabled={!recebimentoResultados}
            >
              Baixar Recebimento
            </Button>
          </div>
          
          <div>
            <Text type="secondary" style={{ marginRight: 8 }}>Modo:</Text>
            <Radio.Group 
              value={modoCalculo} 
              onChange={(e) => setModoCalculo(e.target.value)}
              buttonStyle="solid"
            >
              <Tooltip title="Regras por Linha/Grupo/Subgrupo/Tipo/Fabricante">
                <Radio.Button value="hierarquia">
                  <ApartmentOutlined /> Hierarquia
                </Radio.Button>
              </Tooltip>
              <Tooltip title="Regras por Centro de Custo (coluna 'Centro Custo-pedido')">
                <Radio.Button value="centro_custo">
                  <BankOutlined /> Centro de Custo
                </Radio.Button>
              </Tooltip>
            </Radio.Group>
          </div>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={carregarResultados}
            loading={loading}
          >
            Atualizar
          </Button>
          
          <Button
            type="primary"
            icon={<CalculatorOutlined />}
            onClick={calcularComissoes}
            loading={calculando}
          >
            Calcular Comissões
          </Button>

          <Button
            icon={<CalculatorOutlined />}
            onClick={calcularRecebimento}
            loading={recebimentoCalculando}
          >
            Calcular Recebimento
          </Button>

          <Button
            icon={<CalendarOutlined />}
            onClick={() => setPeriodoModalVisible(true)}
          >
            Gerenciar Períodos
          </Button>
          
          {resultados && (
            <Text type="secondary">
              Referência: {resultados.mes_ano} | Modo: {resultados.modo_calculo === 'centro_custo' ? 'Centro de Custo' : 'Hierarquia'}
            </Text>
          )}
        </Space>
      </Card>

      {/* Área de conteúdo */}
      <Spin spinning={loading || recebimentoLoading}>
        {erro ? (
          <Alert
            type="warning"
            message="Resultados não disponíveis"
            description={erro}
            showIcon
            style={{ marginBottom: 16 }}
          />
        ) : resultados ? (
          <>
            {/* Cards de estatísticas */}
            {renderEstatisticas()}
            
            {/* Tabela principal */}
            <Card
              title={
                <Space>
                  <TeamOutlined />
                  <span>Comissões por Colaborador</span>
                </Space>
              }
            >
              <Table
                dataSource={resumoAgregado}
                columns={columns}
                rowKey={(record) => `${modoCalculo}_${record.colaborador}`}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `Total: ${total} colaboradores`,
                }}
                size="middle"
              />
            </Card>

            <Divider orientation="left" style={{ marginTop: 24 }}>
              <Space>
                <BankOutlined />
                <span>Recebimento V2</span>
              </Space>
            </Divider>

            {recebimentoErro && (
              <Alert
                type="warning"
                message="Recebimento V2"
                description={recebimentoErro}
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {recebimentoResultados ? (
              <>
                <Row gutter={16} style={{ marginBottom: 16 }}>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic
                        title="Adiantamentos"
                        value={recebimentoTotais.qtdAdiantamentos}
                        prefix={<DollarOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic
                        title="Total Adiantamentos"
                        value={recebimentoTotais.totalAdiantamentos}
                        precision={2}
                        prefix={<DollarOutlined />}
                        formatter={(value) => formatCurrency(value)}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic
                        title="Total Ajustes"
                        value={recebimentoTotais.totalAjustes}
                        precision={2}
                        prefix={<DollarOutlined />}
                        formatter={(value) => formatCurrency(value)}
                      />
                    </Card>
                  </Col>
                </Row>

                <Card title="Adiantamentos" style={{ marginBottom: 16 }}>
                  <Table
                    dataSource={recebimentoListas.adiantamentos}
                    columns={adiantamentosColumns}
                    rowKey={(record, idx) => `adiant_${idx}`}
                    pagination={{ pageSize: 8, showSizeChanger: true }}
                    size="small"
                  />
                </Card>

                <Card title="Reconciliações" style={{ marginBottom: 16 }}>
                  <Table
                    dataSource={recebimentoListas.reconciliacoes}
                    columns={reconciliacoesColumns}
                    rowKey={(record, idx) => `reconc_${idx}`}
                    pagination={{ pageSize: 8, showSizeChanger: true }}
                    size="small"
                  />
                </Card>

                <Card title="Pendências">
                  <Table
                    dataSource={recebimentoListas.pendentes}
                    columns={pendentesColumns}
                    rowKey={(record, idx) => `pend_${idx}`}
                    pagination={{ pageSize: 8, showSizeChanger: true }}
                    size="small"
                  />
                </Card>
              </>
            ) : !recebimentoLoading && (
              <Empty
                description="Nenhum resultado de recebimento para o período"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </>
        ) : !loading && (
          <Empty
            description="Selecione um período e clique em Atualizar"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Spin>

      {/* Modal de detalhes */}
      <DetalhesColaboradorV2Modal
        visible={modalVisible}
        onClose={handleFecharModal}
        colaborador={colaboradorSelecionado}
        detalhes={detalhesColaborador}
        modoCalculo={modoCalculo}
      />

      {/* Modal de períodos disponíveis */}
      <Modal
        title="Períodos com cálculo V2"
        open={periodoModalVisible}
        onCancel={() => setPeriodoModalVisible(false)}
        footer={null}
        width={700}
      >
        <Table
          dataSource={periodosDisponiveis}
          loading={periodosLoading}
          rowKey={(record) => `${record.ano}-${record.mes}-${record.modo_calculo}`}
          pagination={false}
          columns={[
            {
              title: 'Período',
              key: 'periodo',
              render: (_, record) => (
                <Tag color="blue">{String(record.mes).padStart(2, '0')}/{record.ano}</Tag>
              ),
            },
            {
              title: 'Modo',
              dataIndex: 'modo_calculo',
              key: 'modo_calculo',
              render: (modo) => (
                <Tag color={modo === 'centro_custo' ? 'purple' : 'geekblue'}>
                  {modo === 'centro_custo' ? 'Centro de Custo' : 'Hierarquia'}
                </Tag>
              ),
            },
            {
              title: 'Arquivo',
              dataIndex: 'arquivo',
              key: 'arquivo',
              ellipsis: true,
            },
            {
              title: 'Ações',
              key: 'acoes',
              align: 'center',
              render: (_, record) => (
                <Popconfirm
                  title="Excluir resultado"
                  description={`Tem certeza que deseja excluir o resultado de ${String(record.mes).padStart(2, '0')}/${record.ano}?`}
                  okText="Excluir"
                  cancelText="Cancelar"
                  onConfirm={async () => {
                    try {
                      await metodoV2API.excluirResultados(record.mes, record.ano, record.modo_calculo);
                      message.success('Resultado excluído com sucesso');
                      await carregarPeriodosDisponiveis();
                      const mesAtual = mesAno?.month() + 1;
                      const anoAtual = mesAno?.year();
                      if (record.mes === mesAtual && record.ano === anoAtual && record.modo_calculo === modoCalculo) {
                        setResultados(null);
                        setErro('Resultados removidos. Selecione o período e execute o cálculo novamente.');
                      }
                    } catch (error) {
                      console.error('Erro ao excluir resultado:', error);
                      message.error(error.response?.data?.detail || 'Erro ao excluir resultado');
                    }
                  }}
                >
                  <Button danger size="small" icon={<DeleteOutlined />}>
                    Excluir
                  </Button>
                </Popconfirm>
              ),
            },
          ]}
        />
      </Modal>
    </div>
  );
};

export default ResultadosV2Tab;
