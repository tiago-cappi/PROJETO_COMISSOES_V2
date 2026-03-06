import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, Tabs, DatePicker, Space, Button, message, Typography, Row, Col, Alert, Input, Select, Table } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/pt-br';
import locale from 'antd/es/date-picker/locale/pt_BR';

import { ColaboradorCardList, ColaboradorDashboard } from '../components/colaborador-dashboard';
import { comissoesAPI, resultadosAPI, recebimentoAPI, historicoAPI } from '../services/api';

import TabelaSaldosNegativos from '../components/historico/TabelaSaldosNegativos';
import DetalhesSaldoNegativoModal from '../components/historico/DetalhesSaldoNegativoModal';
import TabelaResumoFinalColaborador from '../components/historico/TabelaResumoFinalColaborador';
import DetalhesResumoFinalModal from '../components/historico/DetalhesResumoFinalModal';

const { TabPane } = Tabs;
const { Title } = Typography;
const { Option } = Select;

const ComissoesPage = () => {
  const [activeTab, setActiveTab] = useState('faturamento');

  const handleTabChange = (key) => {
    setActiveTab(key);
    setSelectedColaborador(null);
    setViewLevel('list');
  };
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [loading, setLoading] = useState(false);
  const [colaboradoresFat, setColaboradoresFat] = useState([]);
  const [colaboradoresRec, setColaboradoresRec] = useState([]);
  const [selectedColaborador, setSelectedColaborador] = useState(null);
  const [viewLevel, setViewLevel] = useState('list'); // 'list' | 'dashboard'

  const [loadingHistorico, setLoadingHistorico] = useState(false);
  const [saldosNegativos, setSaldosNegativos] = useState({ resumo: [], itens: [] });
  const [resumoFinal, setResumoFinal] = useState([]);
  const [historicoMaster, setHistoricoMaster] = useState({ data: [], total: 0, page: 1, size: 50, columns: [] });

  const [historicoFilters, setHistoricoFilters] = useState({
    tipo_comissao: '',
    nome_colaborador: '',
    processo: '',
  });
  const [historicoPagination, setHistoricoPagination] = useState({ page: 1, size: 50 });

  const [saldoModalVisible, setSaldoModalVisible] = useState(false);
  const [saldoModalItem, setSaldoModalItem] = useState(null);

  const [resumoModalVisible, setResumoModalVisible] = useState(false);
  const [resumoModalNome, setResumoModalNome] = useState(null);
  const [resumoModalLinhas, setResumoModalLinhas] = useState([]);

  const [debugAuditLogText, setDebugAuditLogText] = useState('');
  const [debugDetalhesColaboradorText, setDebugDetalhesColaboradorText] = useState('');
  const [debugSaldosNegativosText, setDebugSaldosNegativosText] = useState('');

  const mesAno = useMemo(() => {
    const mes = selectedDate.month() + 1;
    const ano = selectedDate.year();
    return { mes, ano, label: selectedDate.format('MM/YYYY') };
  }, [selectedDate]);

  // Inicializar período pelo último arquivo de resultado disponível
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const resp = await historicoAPI.getUltimoPeriodoExecutado();
        const payload = resp?.data || {};
        const mes = Number(payload.mes);
        const ano = Number(payload.ano);
        if (mounted && !Number.isNaN(mes) && !Number.isNaN(ano)) {
          setSelectedDate(dayjs(`${ano}-${String(mes).padStart(2, '0')}-01`));
        }
      } catch (e) {
        // Se não houver arquivo ainda, mantém o mês atual.
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'faturamento') {
        const resp = await comissoesAPI.getColaboradoresFaturamento();
        const payload = resp?.data || {};
        setColaboradoresFat(payload.colaboradores || []);
      } else if (activeTab === 'recebimento') {
        const { mes, ano } = mesAno;
        const resp = await comissoesAPI.getColaboradoresRecebimento(mes, ano);
        const payload = resp?.data || {};
        setColaboradoresRec(payload.colaboradores || []);
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      message.error('Erro ao carregar dados de comissões.');
    } finally {
      setLoading(false);
    }
  }, [activeTab, mesAno]);

  const fetchHistoricoViews = useCallback(async () => {
    const { mes, ano } = mesAno;
    setLoadingHistorico(true);
    setDebugSaldosNegativosText('');
    
    const requestContext = {
      feature: 'saldos_negativos',
      operation: 'GET /api/historico/saldos-negativos',
      periodo: { mes, ano, label: mesAno.label },
    };
    try {
      // Saldos negativos (DEVOLUCAO agora; RECONCILIACAO futuro)
      const respSaldos = await historicoAPI.getSaldosNegativos(mes, ano, 'ALL', 3000);
      const saldosPayload = respSaldos?.data || {};
      
      // Debug: registrar quantidade de itens retornados
      const itensRetornados = saldosPayload.itens || [];
      const resumoRetornado = saldosPayload.resumo_colaboradores || [];
      console.log(`>>> DEBUG [fetchHistoricoViews] Saldos Negativos: ${itensRetornados.length} itens, ${resumoRetornado.length} colaboradores no resumo`);
      
      setSaldosNegativos({
        resumo: resumoRetornado,
        itens: itensRetornados,
      });

      // Resumo final por colaborador (inclui ADIANTAMENTO)
      const respResumo = await historicoAPI.getResumoFinalColaboradores(mes, ano);
      const resumoPayload = respResumo?.data || {};
      const colabs = resumoPayload.colaboradores || [];
      setResumoFinal(colabs);
    } catch (error) {
      setDebugSaldosNegativosText(buildAxiosDebugText(error, requestContext));
      message.error('Erro ao carregar dados do histórico (Master DB).');
    } finally {
      setLoadingHistorico(false);
    }
  }, [mesAno]);

  const fetchHistoricoMaster = useCallback(async () => {
    const { mes, ano } = mesAno;
    setLoadingHistorico(true);

    setDebugAuditLogText('');

    const requestContext = {
      feature: 'historico_master',
      operation: 'GET /api/historico/master',
      periodo: { mes, ano, label: mesAno.label },
      filters: historicoFilters,
      pagination: historicoPagination,
    };
    try {
      const resp = await historicoAPI.getMaster({
        mes,
        ano,
        tipo_comissao: historicoFilters.tipo_comissao || undefined,
        nome_colaborador: historicoFilters.nome_colaborador || undefined,
        processo: historicoFilters.processo || undefined,
        page: historicoPagination.page,
        size: historicoPagination.size,
        sort_by: 'Data_Execucao',
        sort_order: 'desc',
      });

      const payload = resp?.data || {};
      setHistoricoMaster({
        data: payload.data || [],
        total: payload.total || 0,
        page: payload.page || historicoPagination.page,
        size: payload.size || historicoPagination.size,
        columns: payload.columns || [],
      });
    } catch (error) {
      setDebugAuditLogText(buildAxiosDebugText(error, requestContext));
      message.error('Erro ao carregar audit log do Master DB.');
    } finally {
      setLoadingHistorico(false);
    }
  }, [mesAno, historicoFilters, historicoPagination]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab === 'saldos_negativos' || activeTab === 'resultado_final') {
      fetchHistoricoViews();
    }
    if (activeTab === 'historico_master') {
      fetchHistoricoMaster();
    }
  }, [activeTab, fetchHistoricoViews, fetchHistoricoMaster]);

  const handleSelectColaborador = (colab) => {
    setSelectedColaborador(colab);
    setViewLevel('dashboard');
  };

  const handleBackToList = () => {
    setSelectedColaborador(null);
    setViewLevel('list');
  };

  const handleClickSaldoNegativo = (record) => {
    setSaldoModalItem(record);
    setSaldoModalVisible(true);
  };

  const handleClickResumoFinal = async (record) => {
    const nome = record?.Nome_Colaborador;
    if (!nome) return;
    const { mes, ano } = mesAno;
    setResumoModalNome(nome);
    setResumoModalVisible(true);
    setResumoModalLinhas([]);

    setDebugDetalhesColaboradorText('');

    const requestContext = {
      feature: 'resultado_final_detalhes_colaborador',
      operation: 'GET /api/historico/resumo-final-colaborador/detalhes',
      periodo: { mes, ano, label: mesAno.label },
      nome_colaborador: nome,
    };
    try {
      const resp = await historicoAPI.getResumoFinalColaboradorDetalhes(mes, ano, nome);
      const payload = resp?.data || {};
      setResumoModalLinhas(payload.linhas || []);
    } catch (error) {
      setDebugDetalhesColaboradorText(buildAxiosDebugText(error, requestContext));
      message.error('Erro ao carregar detalhes do colaborador no histórico.');
    }
  };

  const handleDownload = async () => {
      try {
          if (activeTab === 'faturamento') {
              const response = await resultadosAPI.baixar();
              const url = window.URL.createObjectURL(new Blob([response.data]));
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', 'Resultados_Comissoes_Calculadas.xlsx');
              document.body.appendChild(link);
              link.click();
              link.remove();
          } else {
              const mes = selectedDate.month() + 1;
              const ano = selectedDate.year();
              const response = await recebimentoAPI.baixarExcel(mes, ano);
              const url = window.URL.createObjectURL(new Blob([response.data]));
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', `Comissoes_Recebimento_${mes}_${ano}.xlsx`);
              document.body.appendChild(link);
              link.click();
              link.remove();
          }
          message.success('Download iniciado!');
      } catch (error) {
          message.error('Erro ao baixar arquivo.');
      }
  };

  return (
    <div className="comissoes-page">
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Title level={3}>Comissões</Title>
          </Col>
          <Col>
            <Space>
              {(activeTab === 'recebimento' || activeTab === 'saldos_negativos' || activeTab === 'resultado_final' || activeTab === 'historico_master') && (
                <DatePicker 
                  picker="month" 
                  value={selectedDate} 
                  onChange={setSelectedDate} 
                  locale={locale}
                  format="MM/YYYY"
                  allowClear={false}
                />
              )}
              <Button 
                icon={<ReloadOutlined />} 
                onClick={() => {
                  if (activeTab === 'faturamento' || activeTab === 'recebimento') return fetchData();
                  if (activeTab === 'historico_master') return fetchHistoricoMaster();
                  return fetchHistoricoViews();
                }} 
                loading={loading || loadingHistorico}
              >
                Atualizar
              </Button>
              <Button 
                icon={<DownloadOutlined />} 
                onClick={handleDownload}
              >
                Exportar Excel
              </Button>
            </Space>
          </Col>
        </Row>

        <Tabs 
          activeKey={activeTab} 
          onChange={handleTabChange}
          type="card"
        >
          <TabPane tab="Por Faturamento" key="faturamento">
            {viewLevel === 'list' ? (
              <ColaboradorCardList
                colaboradores={colaboradoresFat}
                loading={loading}
                onSelectColaborador={handleSelectColaborador}
                tipo="faturamento"
              />
            ) : (
              <ColaboradorDashboard
                colaborador={selectedColaborador}
                tipo="faturamento"
                onBack={handleBackToList}
                periodo={mesAno.label}
              />
            )}
          </TabPane>
          <TabPane tab="Por Recebimento" key="recebimento">
            {viewLevel === 'list' ? (
              <ColaboradorCardList
                colaboradores={colaboradoresRec}
                loading={loading}
                onSelectColaborador={handleSelectColaborador}
                tipo="recebimento"
              />
            ) : (
              <ColaboradorDashboard
                colaborador={selectedColaborador}
                tipo="recebimento"
                onBack={handleBackToList}
                periodo={mesAno.label}
              />
            )}
          </TabPane>

          <TabPane tab="Saldos Negativos" key="saldos_negativos">
            <Alert
              message="Saldos Negativos do Mês"
              description={`Esta aba lista os estornos lançados no Master DB para o período ${mesAno.label}. Atualmente inclui DEVOLUÇÃO (e está pronta para integrar RECONCILIAÇÃO futuramente).`}
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <TabelaSaldosNegativos
              resumo={saldosNegativos.resumo}
              itens={saldosNegativos.itens}
              loading={loadingHistorico}
              onClickItem={handleClickSaldoNegativo}
            />

            <Card size="small" style={{ marginTop: 12 }}>
              <Typography.Text strong>Debug (Saldos Negativos)</Typography.Text>
              <Input.TextArea
                value={debugSaldosNegativosText}
                placeholder="Se ocorrer erro ao carregar saldos negativos, as informações de debug aparecerão aqui."
                autoSize={{ minRows: 6, maxRows: 14 }}
                readOnly
                style={{ marginTop: 8 }}
              />
            </Card>
          </TabPane>

          <TabPane tab="Resultado Final" key="resultado_final">
            <Alert
              message="Resultado Final por Colaborador"
              description={`Somatório das comissões do período ${mesAno.label}, incluindo ADIANTAMENTO e subtraindo automaticamente os saldos negativos (DEVOLUÇÃO/RECONCILIAÇÃO) quando existirem.`}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <TabelaResumoFinalColaborador
              data={resumoFinal}
              loading={loadingHistorico}
              onClickColaborador={handleClickResumoFinal}
            />

            <Card size="small" style={{ marginTop: 12 }}>
              <Typography.Text strong>Debug (Detalhes Colaborador)</Typography.Text>
              <Input.TextArea
                value={debugDetalhesColaboradorText}
                placeholder="Se ocorrer erro ao abrir detalhes do colaborador, cole o conteúdo deste campo aqui."
                autoSize={{ minRows: 6, maxRows: 14 }}
                readOnly
                style={{ marginTop: 8 }}
              />
            </Card>
          </TabPane>

          <TabPane tab="Histórico (Audit Log)" key="historico_master">
            <Alert
              message="Banco Histórico (Master DB)"
              description={`Audit log paginado do período ${mesAno.label}. Use filtros para localizar processos, colaboradores e tipos.`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
              <Col xs={24} md={6}>
                <Select
                  value={historicoFilters.tipo_comissao}
                  onChange={(v) => {
                    setHistoricoFilters((prev) => ({ ...prev, tipo_comissao: v }));
                    setHistoricoPagination((prev) => ({ ...prev, page: 1 }));
                  }}
                  style={{ width: '100%' }}
                  placeholder="Tipo"
                  allowClear
                >
                  <Option value="FATURAMENTO">FATURAMENTO</Option>
                  <Option value="ADIANTAMENTO">ADIANTAMENTO</Option>
                  <Option value="REGULAR">REGULAR</Option>
                  <Option value="RECONCILIACAO">RECONCILIACAO</Option>
                  <Option value="DEVOLUCAO">DEVOLUCAO</Option>
                </Select>
              </Col>
              <Col xs={24} md={9}>
                <Input
                  value={historicoFilters.nome_colaborador}
                  onChange={(e) => setHistoricoFilters((prev) => ({ ...prev, nome_colaborador: e.target.value }))}
                  placeholder="Filtrar por colaborador"
                />
              </Col>
              <Col xs={24} md={9}>
                <Input
                  value={historicoFilters.processo}
                  onChange={(e) => setHistoricoFilters((prev) => ({ ...prev, processo: e.target.value }))}
                  placeholder="Filtrar por processo"
                />
              </Col>
            </Row>

            <Card size="small">
              <TabelaHistoricoMaster
                data={historicoMaster.data}
                loading={loadingHistorico}
                total={historicoMaster.total}
                page={historicoPagination.page}
                size={historicoPagination.size}
                onChangePage={(page, size) => setHistoricoPagination({ page, size })}
              />
            </Card>

            <Card size="small" style={{ marginTop: 12 }}>
              <Typography.Text strong>Debug (Audit Log)</Typography.Text>
              <Input.TextArea
                value={debugAuditLogText}
                placeholder="Se ocorrer erro ao carregar o audit log, cole o conteúdo deste campo aqui."
                autoSize={{ minRows: 8, maxRows: 18 }}
                readOnly
                style={{ marginTop: 8 }}
              />
            </Card>
          </TabPane>
        </Tabs>
      </Card>

      <DetalhesSaldoNegativoModal
        visible={saldoModalVisible}
        onClose={() => setSaldoModalVisible(false)}
        item={saldoModalItem}
      />

      <DetalhesResumoFinalModal
        visible={resumoModalVisible}
        onClose={() => setResumoModalVisible(false)}
        colaboradorNome={resumoModalNome}
        periodo={mesAno.label}
        linhas={resumoModalLinhas}
      />
    </div>
  );
};

export default ComissoesPage;

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

const safeStringify = (value) => {
  try {
    return JSON.stringify(
      value,
      (key, val) => {
        if (typeof val === 'bigint') return val.toString();
        if (val instanceof Error) {
          return {
            name: val.name,
            message: val.message,
            stack: val.stack,
          };
        }
        return val;
      },
      2
    );
  } catch (e) {
    try {
      return String(value);
    } catch (_) {
      return '[unserializable]';
    }
  }
};

const buildAxiosDebugText = (error, context) => {
  const err = error || {};
  const response = err.response || {};
  const config = err.config || {};

  const debugPayload = {
    timestamp: new Date().toISOString(),
    context: context || null,
    error: {
      name: err.name,
      message: err.message,
      code: err.code,
      isAxiosError: err.isAxiosError,
      stack: err.stack,
    },
    request: {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      params: config.params,
      data: config.data,
      timeout: config.timeout,
    },
    response: {
      status: response.status,
      statusText: response.statusText,
      data: response.data,
    },
  };

  return safeStringify(debugPayload);
};

const TabelaHistoricoMaster = ({ data, loading, total, page, size, onChangePage }) => {
  const columns = [
    { title: 'Execução', dataIndex: 'Data_Execucao', key: 'Data_Execucao', width: 170 },
    { title: 'Tipo', dataIndex: 'Tipo_Comissao', key: 'Tipo_Comissao', width: 130 },
    { title: 'Colaborador', dataIndex: 'Nome_Colaborador', key: 'Nome_Colaborador', width: 240, ellipsis: true },
    { title: 'Processo', dataIndex: 'Processo', key: 'Processo', width: 160, ellipsis: true },
    { title: 'NF', dataIndex: 'Numero_NF', key: 'Numero_NF', width: 110 },
    {
      title: 'Valor Base',
      dataIndex: 'Valor_Base',
      key: 'Valor_Base',
      width: 140,
      align: 'right',
      render: (v) => formatCurrencyBR(v),
    },
    {
      title: 'Comissão',
      dataIndex: 'Comissao_Calculada',
      key: 'Comissao_Calculada',
      width: 140,
      align: 'right',
      render: (v) => formatCurrencyBR(v),
    },
    { title: 'Origem', dataIndex: 'Origem_Correcao', key: 'Origem_Correcao', width: 140 },
    { title: 'Proc. Ref.', dataIndex: 'Processo_Referencia', key: 'Processo_Referencia', width: 160, ellipsis: true },
    { title: 'Fator Dev.', dataIndex: 'Fator_Devolucao', key: 'Fator_Devolucao', width: 110 },
    { title: 'Obs.', dataIndex: 'Observacao', key: 'Observacao', ellipsis: true },
  ];

  return (
    <Table
      size="small"
      bordered
      loading={loading}
      columns={columns}
      dataSource={Array.isArray(data) ? data.map((r, idx) => ({ ...r, key: `${r.Data_Execucao || ''}-${idx}` })) : []}
      pagination={{
        current: page,
        pageSize: size,
        total: total,
        showSizeChanger: true,
        pageSizeOptions: ['20', '50', '100', '200'],
        onChange: (p, ps) => onChangePage && onChangePage(p, ps),
      }}
      scroll={{ x: 'max-content' }}
    />
  );
};
