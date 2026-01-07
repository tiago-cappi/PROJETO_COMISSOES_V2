import React, { useEffect, useMemo, useState, useRef } from 'react';
import {
  Modal,
  Collapse,
  Descriptions,
  Table,
  Alert,
  Tag,
  Space,
  Typography,
  Divider,
  Spin,
  Segmented,
  Drawer,
  Button,
  Card,
  Progress,
} from 'antd';
import {
  InfoCircleOutlined,
  CalculatorOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DollarOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';

import { recebimentoAPI } from '../../services/api';

const { Panel } = Collapse;
const { Text, Title } = Typography;

const VIEW_MODE = {
  BASICO: 'BASICO',
  AUDITORIA: 'AUDITORIA',
};

const formatCurrencyBR = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
const formatPercent = (value) => `${((value || 0) * 100).toFixed(2)}%`;

/**
 * Formata valor de meta de acordo com o tipo.
 * Metas de rentabilidade são exibidas como % (já vêm em decimal).
 * Metas de faturamento são exibidas como R$.
 * Metas de conversão/retenção são exibidas como %.
 */
const formatMetaValue = (value, metaNome) => {
  if (value === null || value === undefined) return '-';
  const nome = (metaNome || '').toLowerCase();
  // Metas que são valores monetários
  if (nome.includes('faturamento')) {
    return formatCurrencyBR(value);
  }
  // Metas que são percentuais (rentabilidade, conversão, retenção)
  if (nome.includes('rentabilidade') || nome.includes('conversão') || nome.includes('conversao') || nome.includes('retenção') || nome.includes('retencao')) {
    // Se valor > 1, assumir que já está em % (ex: 15 = 15%)
    // Se valor <= 1, assumir que está em decimal (ex: 0.15 = 15%)
    const pct = value > 1 ? value : value * 100;
    return `${pct.toFixed(2)}%`;
  }
  // Fallback: exibir número formatado
  return typeof value === 'number' ? value.toLocaleString('pt-BR', { maximumFractionDigits: 4 }) : String(value);
};

/**
 * Modal para exibir detalhes completos do cálculo de um pagamento.
 * 4 Seções: Informações Gerais, TCMP, FCMP, Cálculo Final.
 */
const ModalDetalhesCalculoRecebimento = ({ visible, onClose, pagamento }) => {
  const [pagamentoDetalhado, setPagamentoDetalhado] = useState(null);
  const [loadingDetalhes, setLoadingDetalhes] = useState(false);
  const [erroDetalhes, setErroDetalhes] = useState(null);
  const [viewMode, setViewMode] = useState(VIEW_MODE.BASICO);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTitle, setDrawerTitle] = useState('');
  const [drawerContent, setDrawerContent] = useState(null);

  const [auditoriaData, setAuditoriaData] = useState(null);
  const [loadingAuditoria, setLoadingAuditoria] = useState(false);
  const [erroAuditoria, setErroAuditoria] = useState(null);
  const [expandedTcmpKeys, setExpandedTcmpKeys] = useState([]);
  // Stack para navegação aninhada no drawer (permite voltar ao nível anterior)
  const [drawerStack, setDrawerStack] = useState([]);
  // Ref para manter valor atual do stack (evita problemas de closure)
  const drawerStackRef = useRef([]);
  const drawerTitleRef = useRef('');
  const drawerContentRef = useRef(null);
  const [expandedFcmpKeys, setExpandedFcmpKeys] = useState([]);

  const pagamentoView = pagamentoDetalhado || pagamento;

  const deveBuscarDetalhes = useMemo(() => {
    if (!visible) return false;
    if (!pagamento?.id) return false;

    const hasTcmp = Object.prototype.hasOwnProperty.call(pagamento, 'tcmp_detalhes');
    const hasFcmp = Object.prototype.hasOwnProperty.call(pagamento, 'fcmp_detalhes');
    return !(hasTcmp && hasFcmp);
  }, [visible, pagamento]);

  useEffect(() => {
    if (!visible) return;
    if (!pagamento) return;
    setErroDetalhes(null);
    setPagamentoDetalhado(null);
    setViewMode(VIEW_MODE.BASICO);
    setDrawerOpen(false);
    setDrawerTitle('');
    setDrawerContent(null);
    setDrawerStack([]);
    setAuditoriaData(null);
    setErroAuditoria(null);
    setExpandedTcmpKeys([]);
    setExpandedFcmpKeys([]);

    if (!deveBuscarDetalhes) return;

    let cancelled = false;
    (async () => {
      try {
        setLoadingDetalhes(true);
        const resp = await recebimentoAPI.getDetalhesPagamento(pagamento.id);
        if (cancelled) return;
        setPagamentoDetalhado(resp?.data || null);
      } catch (e) {
        if (cancelled) return;
        setErroDetalhes(e?.message || 'Falha ao carregar detalhes do pagamento');
      } finally {
        if (!cancelled) setLoadingDetalhes(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [visible, pagamento?.id, deveBuscarDetalhes]);

  useEffect(() => {
    if (!visible) return;
    if (viewMode !== VIEW_MODE.AUDITORIA) return;
    const processo = (pagamentoDetalhado || pagamento)?.processo;
    if (!processo) return;

    let cancelled = false;
    (async () => {
      try {
        setLoadingAuditoria(true);
        setErroAuditoria(null);
        const resp = await recebimentoAPI.getAuditoriaProcesso(processo);
        if (cancelled) return;
        setAuditoriaData(resp?.data || null);
      } catch (e) {
        if (cancelled) return;
        setErroAuditoria(e?.message || 'Falha ao carregar auditoria do processo');
      } finally {
        if (!cancelled) setLoadingAuditoria(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [visible, viewMode, pagamentoDetalhado, pagamento]);

  if (!pagamento) return null;

  const isAdiantamento = pagamentoView.tipo === 'ADIANTAMENTO' || pagamentoView.tipo === 'Antecipação';
  const tcmpDetalhes = pagamentoView.tcmp_detalhes || [];
  const fcmpDetalhes = pagamentoView.fcmp_detalhes || [];

  const openDrawer = (title, content) => {
    drawerTitleRef.current = title;
    drawerContentRef.current = content;
    drawerStackRef.current = [];
    setDrawerTitle(title);
    setDrawerContent(content);
    setDrawerStack([]);
    setDrawerOpen(true);
  };

  // Navegar para um novo nível no drawer (push na pilha)
  const pushDrawer = (title, content) => {
    // Salvar estado atual na pilha usando refs (evita problemas de closure)
    const newStack = [...drawerStackRef.current, { title: drawerTitleRef.current, content: drawerContentRef.current }];
    drawerStackRef.current = newStack;
    drawerTitleRef.current = title;
    drawerContentRef.current = content;
    setDrawerStack(newStack);
    setDrawerTitle(title);
    setDrawerContent(content);
  };

  // Voltar ao nível anterior no drawer (pop da pilha)
  const popDrawer = () => {
    if (drawerStackRef.current.length === 0) return;
    const prev = drawerStackRef.current[drawerStackRef.current.length - 1];
    const newStack = drawerStackRef.current.slice(0, -1);
    drawerStackRef.current = newStack;
    drawerTitleRef.current = prev.title;
    drawerContentRef.current = prev.content;
    setDrawerStack(newStack);
    setDrawerTitle(prev.title);
    setDrawerContent(prev.content);
  };

  const buildCardEquation = (label, equation, substitution, result) => (
    <Card size="small" title={label}>
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        <Text><strong>Equação:</strong> <span style={{ fontFamily: 'monospace' }}>{equation}</span></Text>
        {substitution ? <Text type="secondary"><strong>Substituindo:</strong> <span style={{ fontFamily: 'monospace' }}>{substitution}</span></Text> : null}
        {result ? <Alert type="success" showIcon message={result} /> : null}
      </Space>
    </Card>
  );

  const openDrawerTcmpItem = ({ itemNome, colaborador, record, totalValorColab }) => {
    const valor = record?.valor || 0;
    const peso = record?.peso || (totalValorColab > 0 ? (valor / totalValorColab) : 0);
    const taxa = record?.taxa || 0;
    const taxaRateio = record?.taxa_rateio;
    const fatiaCargo = record?.fatia_cargo;
    const taxaTemDecomposicao = taxaRateio !== undefined && fatiaCargo !== undefined;
    const taxaCalc = taxaTemDecomposicao ? (taxaRateio * fatiaCargo) : null;
    const parcial = taxa * peso;

    openDrawer(
      `TCMP · ${itemNome} · ${colaborador}`,
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small" title="📌 Visão geral">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="Colaborador"><strong>{colaborador}</strong></Descriptions.Item>
            <Descriptions.Item label="Item"><strong>{itemNome}</strong></Descriptions.Item>
            <Descriptions.Item label="Valor do item"><strong>{formatCurrencyBR(valor)}</strong></Descriptions.Item>
            <Descriptions.Item label="Taxa do item"><strong>{formatPercent(taxa)}</strong></Descriptions.Item>
            <Descriptions.Item label="Peso"><strong>{formatPercent(peso)}</strong></Descriptions.Item>
            <Descriptions.Item label="Contribuição (Taxa × Peso)"><strong>{formatPercent(parcial)}</strong></Descriptions.Item>
          </Descriptions>
        </Card>

        {taxaTemDecomposicao ? (
          <Card size="small" title="🧮 Como foi calculada a Taxa do item">
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Space wrap>
                <Tag color="blue">Taxa Rateio: {formatPercent(taxaRateio)}</Tag>
                <Tag color="cyan">Fatia Cargo: {formatPercent(fatiaCargo)}</Tag>
                <Tag color="green">Taxa Efetiva: {formatPercent(taxaCalc)}</Tag>
              </Space>
              {buildCardEquation(
                'Equação',
                'Taxa_Item = Taxa_Rateio × Fatia_Cargo',
                `Taxa_Item = ${formatPercent(taxaRateio)} × ${formatPercent(fatiaCargo)} = ${formatPercent(taxaCalc)}`,
                `Taxa do item = ${formatPercent(taxaCalc)}`
              )}
            </Space>
          </Card>
        ) : (
          <Alert
            type="info"
            showIcon
            message="Detalhe da taxa"
            description="Este item não possui taxa_rateio/fatia_cargo no estado. Exibindo a taxa final disponível."
          />
        )}

        {buildCardEquation(
          '⚖️ Como foi calculado o Peso',
          'Peso = Valor_Item / Σ(Valor_Item)',
          `Peso = ${formatCurrencyBR(valor)} / ${formatCurrencyBR(totalValorColab)} = ${formatPercent(peso)}`,
          `Peso = ${formatPercent(peso)}`
        )}

        {buildCardEquation(
          '✅ Contribuição no TCMP',
          'TCMP_Parcial = Taxa_Item × Peso',
          `TCMP_Parcial = ${formatPercent(taxa)} × ${formatPercent(peso)} = ${formatPercent(parcial)}`,
          `TCMP Parcial = ${formatPercent(parcial)}`
        )}
      </Space>
    );
  };

  const openDrawerFcmpItem = ({ itemNome, colaborador, record, totalValorColab }) => {
    const valor = record?.valor || 0;
    const peso = record?.peso || (totalValorColab > 0 ? (valor / totalValorColab) : 0);
    const fc = record?.fc ?? 1;
    const metas = Array.isArray(record?.metas) ? record.metas : [];
    const somaComponentes = metas.reduce((acc, m) => acc + (m.peso || 0) * (m.componente_fc || 0), 0);
    const contrib = fc * peso;

    openDrawer(
      `FCMP · ${itemNome} · ${colaborador}`,
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small" title="📌 Visão geral">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="Colaborador"><strong>{colaborador}</strong></Descriptions.Item>
            <Descriptions.Item label="Item"><strong>{itemNome}</strong></Descriptions.Item>
            <Descriptions.Item label="Valor realizado do item"><strong>{formatCurrencyBR(valor)}</strong></Descriptions.Item>
            <Descriptions.Item label="FC do item"><strong>{fc.toFixed(4)}</strong></Descriptions.Item>
            <Descriptions.Item label="Peso"><strong>{formatPercent(peso)}</strong></Descriptions.Item>
            <Descriptions.Item label="Contribuição (FC × Peso)"><strong>{contrib.toFixed(4)}</strong></Descriptions.Item>
          </Descriptions>
        </Card>

        <Card size="small" title="🎯 Metas consideradas (peso > 0)" extra={<Text type="secondary" style={{ fontSize: 11 }}>Clique em uma meta para ver detalhes</Text>}>
          {metas.length === 0 ? (
            <Alert
              type="info"
              showIcon
              message="Sem detalhamento de metas"
              description="O estado não retornou a composição das metas (fc_detalhes.componentes) para este item/colaborador."
            />
          ) : (
            <Table
              size="small"
              bordered
              pagination={false}
              dataSource={metas.map((m, idx) => ({ ...m, key: idx }))}
              columns={[
                { title: 'Meta', dataIndex: 'nome_meta', key: 'nome_meta', ellipsis: true },
                {
                  title: 'Peso',
                  dataIndex: 'peso',
                  key: 'peso',
                  width: 90,
                  align: 'center',
                  render: (v) => formatPercent(v),
                },
                {
                  title: '% Cumprimento',
                  dataIndex: 'atingimento',
                  key: 'atingimento',
                  width: 160,
                  render: (v) => (
                    <Space direction="vertical" size={0} style={{ width: '100%' }}>
                      <Text style={{ fontSize: 12 }}>{formatPercent(v)}</Text>
                      <Progress percent={Math.max(0, Math.min(200, (v || 0) * 100))} showInfo={false} />
                    </Space>
                  ),
                },
                {
                  title: 'FC da meta',
                  dataIndex: 'componente_fc',
                  key: 'componente_fc',
                  width: 110,
                  align: 'center',
                  render: (v) => <strong>{(v || 0).toFixed(4)}</strong>,
                },
              ]}
              onRow={(record) => ({
                onClick: () => openDrawerMetaDetalhe({ metaData: record, itemNome, colaborador }),
                style: { cursor: 'pointer' },
              })}
              rowClassName={() => 'clickable-row'}
            />
          )}
        </Card>

        {metas.length > 0 ? buildCardEquation(
          '🧮 Como foi calculado o FC do item',
          'FC_Item = Σ (Peso_Meta × FC_Meta)',
          `FC_Item = ${metas.map((m) => `(${formatPercent(m.peso)}×${(m.componente_fc || 0).toFixed(4)})`).join(' + ')} = ${somaComponentes.toFixed(4)}`,
          `FC do item = ${fc.toFixed(4)}`
        ) : null}

        {buildCardEquation(
          '⚖️ Como foi calculado o Peso',
          'Peso = Valor_Item / Σ(Valor_Item)',
          `Peso = ${formatCurrencyBR(valor)} / ${formatCurrencyBR(totalValorColab)} = ${formatPercent(peso)}`,
          `Peso = ${formatPercent(peso)}`
        )}

        {buildCardEquation(
          '✅ Contribuição no FCMP',
          'Parcela = FC_Item × Peso',
          `Parcela = ${fc.toFixed(4)} × ${formatPercent(peso)} = ${contrib.toFixed(4)}`,
          `Parcela = ${contrib.toFixed(4)}`
        )}
      </Space>
    );
  };

  /**
   * Abre detalhe de uma meta específica (terceira camada de auditoria).
   * Mostra o passo a passo do cálculo do atingimento da meta.
   */
  const openDrawerMetaDetalhe = ({ metaData, itemNome, colaborador }) => {
    const nomeMeta = metaData?.nome_meta || 'Meta';
    const peso = metaData?.peso || 0;
    const realizado = metaData?.realizado;
    const meta = metaData?.meta;
    const atingimento = metaData?.atingimento || 0;
    const atingimentoCap = metaData?.atingimento_cap;
    const componenteFc = metaData?.componente_fc || 0;

    // Verificar se há cap aplicado (atingimento_cap diferente de atingimento)
    const temCap = atingimentoCap !== undefined && atingimentoCap !== null && Math.abs(atingimentoCap - atingimento) > 0.0001;
    const capUsado = temCap ? atingimentoCap : atingimento;

    // Verificar se temos dados suficientes para mostrar o cálculo
    const temDadosCalculo = realizado !== undefined && realizado !== null && meta !== undefined && meta !== null;

    pushDrawer(
      `📊 ${nomeMeta}`,
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={popDrawer} style={{ marginBottom: 8 }}>
          Voltar para FC do Item
        </Button>

        <Card size="small" title="📌 Visão Geral">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="Meta"><strong>{nomeMeta}</strong></Descriptions.Item>
            <Descriptions.Item label="Colaborador"><strong>{colaborador}</strong></Descriptions.Item>
            <Descriptions.Item label="Item"><strong>{itemNome}</strong></Descriptions.Item>
            <Descriptions.Item label="Peso da Meta"><strong>{formatPercent(peso)}</strong></Descriptions.Item>
          </Descriptions>
        </Card>

        <Card size="small" title="📊 Dados Utilizados">
          {temDadosCalculo ? (
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="Valor Realizado">
                <strong style={{ color: '#1890ff', fontSize: 16 }}>
                  {formatMetaValue(realizado, nomeMeta)}
                </strong>
              </Descriptions.Item>
              <Descriptions.Item label="Meta Estabelecida">
                <strong style={{ fontSize: 16 }}>
                  {formatMetaValue(meta, nomeMeta)}
                </strong>
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <Alert
              type="warning"
              showIcon
              message="Dados não disponíveis"
              description="O estado não retornou os valores de 'realizado' e 'meta' para este componente. Apenas o atingimento final está disponível."
            />
          )}
        </Card>

        <Card size="small" title="🧮 Cálculo do Atingimento">
          <Space direction="vertical" size={8} style={{ width: '100%' }}>
            <Text><strong>Fórmula:</strong> <span style={{ fontFamily: 'monospace' }}>Atingimento = Realizado / Meta</span></Text>
            {temDadosCalculo ? (
              <>
                <Text type="secondary">
                  <strong>Substituindo:</strong>{' '}
                  <span style={{ fontFamily: 'monospace' }}>
                    Atingimento = {formatMetaValue(realizado, nomeMeta)} / {formatMetaValue(meta, nomeMeta)}
                  </span>
                </Text>
                <Alert
                  type="success"
                  showIcon
                  message={
                    <span>
                      <strong>Atingimento = {formatPercent(atingimento)}</strong>
                      {atingimento >= 1 ? ' ✅ Meta atingida!' : ' ⚠️ Meta não atingida'}
                    </span>
                  }
                />
              </>
            ) : (
              <Alert type="info" showIcon message={`Atingimento = ${formatPercent(atingimento)}`} />
            )}
          </Space>
        </Card>

        {temCap && (
          <Card size="small" title="⚠️ Aplicação do Cap (Limite Máximo)">
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Alert
                type="warning"
                showIcon
                icon={<WarningOutlined />}
                message="O atingimento foi limitado pelo cap máximo configurado"
              />
              <Text>
                <strong>Fórmula:</strong>{' '}
                <span style={{ fontFamily: 'monospace' }}>Atingimento_Cap = min(Atingimento, Cap_Máximo)</span>
              </Text>
              <Text type="secondary">
                <strong>Aplicando:</strong>{' '}
                <span style={{ fontFamily: 'monospace' }}>
                  Atingimento_Cap = min({formatPercent(atingimento)}, {formatPercent(atingimentoCap / atingimento * atingimentoCap)}) = {formatPercent(atingimentoCap)}
                </span>
              </Text>
              <Space wrap>
                <Tag color="orange">Atingimento Original: {formatPercent(atingimento)}</Tag>
                <Tag color="green">Atingimento Aplicado: {formatPercent(atingimentoCap)}</Tag>
              </Space>
            </Space>
          </Card>
        )}

        <Card size="small" title="✅ Contribuição no FC do Item">
          <Space direction="vertical" size={8} style={{ width: '100%' }}>
            <Text>
              <strong>Fórmula:</strong>{' '}
              <span style={{ fontFamily: 'monospace' }}>Componente_FC = Peso × Atingimento{temCap ? '_Cap' : ''}</span>
            </Text>
            <Text type="secondary">
              <strong>Substituindo:</strong>{' '}
              <span style={{ fontFamily: 'monospace' }}>
                Componente_FC = {formatPercent(peso)} × {formatPercent(capUsado)} = {componenteFc.toFixed(4)}
              </span>
            </Text>
            <Alert
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
              message={
                <span style={{ fontSize: 16 }}>
                  <strong>Contribuição desta meta no FC = {componenteFc.toFixed(4)}</strong>
                </span>
              }
            />
          </Space>
        </Card>

        <Card size="small" title="📋 Resumo do Cálculo">
          <div style={{ backgroundColor: '#f5f5f5', padding: 12, borderRadius: 4, fontFamily: 'monospace', fontSize: 12 }}>
            <div>1. Atingimento = Realizado / Meta = {formatPercent(atingimento)}</div>
            {temCap && <div>2. Atingimento_Cap = min({formatPercent(atingimento)}, Cap) = {formatPercent(atingimentoCap)}</div>}
            <div>{temCap ? '3' : '2'}. Componente_FC = Peso × Atingimento{temCap ? '_Cap' : ''}</div>
            <div style={{ marginTop: 8, fontWeight: 'bold', color: '#52c41a' }}>
              → Componente_FC = {formatPercent(peso)} × {formatPercent(capUsado)} = {componenteFc.toFixed(4)}
            </div>
          </div>
        </Card>
      </Space>
    );
  };

  const openDrawerTotalSelector = ({ tipo, titulo, totaisPorColab, parcelasPorColab }) => {
    const colaboradores = Object.keys(totaisPorColab || {});
    openDrawer(
      titulo,
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Alert
          type="info"
          showIcon
          message="Selecione um colaborador para auditar o TOTAL"
          description="O TCMP/FCMP final é calculado individualmente por colaborador."
        />

        <Table
          size="small"
          bordered
          pagination={false}
          dataSource={colaboradores.map((c) => ({ key: c, colaborador: c, ...(totaisPorColab[c] || {}) }))}
          columns={[
            { title: 'Colaborador', dataIndex: 'colaborador', key: 'colaborador', ellipsis: true },
            {
              title: tipo === 'TCMP' ? 'TCMP Final' : 'FCMP Final',
              dataIndex: tipo === 'TCMP' ? 'tcmp_final' : 'fcmp_final',
              key: 'final',
              width: 120,
              align: 'center',
              render: (v) => <strong>{tipo === 'TCMP' ? formatPercent(v) : (v ?? 1).toFixed(4)}</strong>,
            },
          ]}
          onRow={(record) => ({
            onClick: () => {
              const colab = record.colaborador;
              const tot = totaisPorColab?.[colab] || {};
              const parcelas = parcelasPorColab?.[colab] || [];

              const denominador = tot.denominador || tot.total_valor || 0;
              const numerador = tot.numerador || parcelas.reduce((acc, p) => acc + (p.produto || 0), 0);
              const finalVal = tipo === 'TCMP' ? (tot.tcmp_final || 0) : (tot.fcmp_final ?? 1);

              openDrawer(
                `${tipo} TOTAL · ${colab}`,
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Card size="small" title="📌 Fórmula completa">
                    <Text>
                      <strong>{tipo}</strong> = Σ({tipo === 'TCMP' ? 'Taxa_Item × Valor_Item' : 'FC_Item × Valor_Item'}) / Σ(Valor_Item)
                    </Text>
                  </Card>

                  <Card size="small" title="🧾 Parcelas (por item)">
                    <Table
                      size="small"
                      bordered
                      pagination={false}
                      dataSource={parcelas.map((p, idx) => ({ ...p, key: idx }))}
                      columns={[
                        { title: 'Item', dataIndex: 'item', key: 'item', ellipsis: true },
                        {
                          title: tipo === 'TCMP' ? 'Taxa' : 'FC',
                          dataIndex: tipo === 'TCMP' ? 'taxa' : 'fc',
                          key: 'coef',
                          width: 90,
                          align: 'center',
                          render: (v) => (tipo === 'TCMP' ? formatPercent(v) : (v ?? 1).toFixed(4)),
                        },
                        {
                          title: 'Valor',
                          dataIndex: 'valor',
                          key: 'valor',
                          width: 120,
                          align: 'right',
                          render: (v) => formatCurrencyBR(v),
                        },
                        {
                          title: 'Produto',
                          dataIndex: 'produto',
                          key: 'produto',
                          width: 120,
                          align: 'right',
                          render: (v) => formatCurrencyBR(v),
                        },
                      ]}
                      summary={() => (
                        <Table.Summary fixed>
                          <Table.Summary.Row>
                            <Table.Summary.Cell index={0}><strong>TOTAL</strong></Table.Summary.Cell>
                            <Table.Summary.Cell index={1} align="center">-</Table.Summary.Cell>
                            <Table.Summary.Cell index={2} align="right"><strong>{formatCurrencyBR(denominador)}</strong></Table.Summary.Cell>
                            <Table.Summary.Cell index={3} align="right"><strong>{formatCurrencyBR(numerador)}</strong></Table.Summary.Cell>
                          </Table.Summary.Row>
                        </Table.Summary>
                      )}
                    />
                  </Card>

                  {buildCardEquation(
                    '✅ Resultado',
                    `${tipo} = Numerador / Denominador`,
                    `${tipo} = ${formatCurrencyBR(numerador)} / ${formatCurrencyBR(denominador)}`,
                    tipo === 'TCMP' ? `${tipo} Final = ${formatPercent(finalVal)}` : `${tipo} Final = ${(finalVal ?? 1).toFixed(4)}`
                  )}
                </Space>
              );
            },
            style: { cursor: 'pointer' },
          })}
        />
      </Space>
    );
  };

  // ==================== SEÇÃO A: INFORMAÇÕES GERAIS ====================
  const renderInformacoesGerais = () => (
    <Descriptions bordered column={1} size="small">
      <Descriptions.Item label="Tipo">
        <Tag color={isAdiantamento ? 'blue' : 'green'} icon={isAdiantamento ? <CheckCircleOutlined /> : <CheckCircleOutlined />}>
          {isAdiantamento ? '🔵 Adiantamento' : '🟢 Regular'}
        </Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Processo">
        <strong style={{ fontSize: 16, color: '#1890ff' }}>{pagamentoView.processo}</strong>
      </Descriptions.Item>
      <Descriptions.Item label="Colaborador">
        <strong>{pagamentoView.nome_colaborador}</strong>
      </Descriptions.Item>
      <Descriptions.Item label="Cargo">{pagamentoView.cargo || '-'}</Descriptions.Item>
      <Descriptions.Item label="Data Pagamento">
        {pagamentoView.data_pagamento ? new Date(pagamentoView.data_pagamento).toLocaleDateString('pt-BR') : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="Valor Base">
        <strong style={{ fontSize: 16 }}>
          {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(pagamentoView.valor_pago || 0)}
        </strong>
      </Descriptions.Item>
    </Descriptions>
  );

  // ==================== SEÇÃO B: TCMP ====================
  const renderTCMP = () => {
    if (erroDetalhes) {
      return (
        <Alert
          message="Não foi possível carregar os detalhes do TCMP"
          description={erroDetalhes}
          type="warning"
          showIcon
        />
      );
    }
    if (loadingDetalhes && (!tcmpDetalhes || tcmpDetalhes.length === 0)) {
      return (
        <div style={{ padding: 12, textAlign: 'center' }}>
          <Spin tip="Carregando detalhes do TCMP..." />
        </div>
      );
    }
    if (!tcmpDetalhes || tcmpDetalhes.length === 0) {
      return (
        <Alert
          message="Detalhes de TCMP não disponíveis"
          type="info"
          showIcon
        />
      );
    }

    const colunasTCMP = [
      {
        title: 'Item',
        dataIndex: 'item',
        key: 'item',
        width: 200,
        ellipsis: true,
      },
      {
        title: 'Valor Item',
        dataIndex: 'valor',
        key: 'valor',
        align: 'right',
        render: (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0),
      },
      {
        title: 'Taxa Item',
        dataIndex: 'taxa',
        key: 'taxa',
        align: 'center',
        render: (val) => `${(val * 100).toFixed(2)}%`,
      },
      {
        title: 'Peso',
        dataIndex: 'peso',
        key: 'peso',
        align: 'center',
        render: (val) => `${(val * 100).toFixed(1)}%`,
      },
      {
        title: 'TCMP Parcial',
        dataIndex: 'tcmp_parcial',
        key: 'tcmp_parcial',
        align: 'center',
        render: (val) => <strong>{(val * 100).toFixed(2)}%</strong>,
      },
    ];

    const totalValor = tcmpDetalhes.reduce((acc, d) => acc + (d.valor || 0), 0);
    const tcmpFinal = tcmpDetalhes.reduce((acc, d) => acc + (d.tcmp_parcial || 0), 0);

    if (viewMode === VIEW_MODE.BASICO) {
      return (
        <div>
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="Itens no cálculo">{tcmpDetalhes.length}</Descriptions.Item>
            <Descriptions.Item label="Valor Total">
              <strong>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalValor)}
              </strong>
            </Descriptions.Item>
            <Descriptions.Item label="TCMP Final" span={2}>
              <strong style={{ fontSize: 16, color: '#1890ff' }}>{(tcmpFinal * 100).toFixed(2)}%</strong>
            </Descriptions.Item>
          </Descriptions>
          <Alert
            style={{ marginTop: 12 }}
            type="info"
            showIcon
            message="Modo Básico"
            description="Troque para 'Auditoria' para ver o passo a passo (itens, pesos e somatório)."
          />
        </div>
      );
    }

    // Auditoria (processo inteiro, por item -> colaboradores)
    if (loadingAuditoria) {
      return (
        <div style={{ padding: 12, textAlign: 'center' }}>
          <Spin tip="Carregando auditoria do processo..." />
        </div>
      );
    }
    if (erroAuditoria) {
      return <Alert type="warning" showIcon message="Falha ao carregar auditoria" description={erroAuditoria} />;
    }
    if (!auditoriaData?.tcmp?.itens) {
      return <Alert type="info" showIcon message="Auditoria não disponível" />;
    }

    const itens = auditoriaData.tcmp.itens || [];
    const itemRows = [...itens].map((it) => ({
      key: it.item,
      item: it.item,
      valor: it.valor,
      taxa: it.taxa,
      peso: it.peso,
      tcmp_parcial: (it.taxa || 0) * (it.peso || 0),
      colaboradores: it.colaboradores || [],
    }));

    const totalValorItens = itemRows.reduce((acc, r) => acc + (r.valor || 0), 0);
    const numeradorItens = itemRows.reduce((acc, r) => acc + (r.taxa || 0) * (r.valor || 0), 0);
    const taxaTotal = totalValorItens > 0 ? (numeradorItens / totalValorItens) : 0;

    itemRows.push({
      key: '__TOTAL__',
      item: 'TOTAL',
      __isTotal: true,
      valor: totalValorItens,
      taxa: taxaTotal,
      peso: 1,
      tcmp_parcial: taxaTotal,
    });

    const columnsItem = [
      { title: 'Item', dataIndex: 'item', key: 'item', ellipsis: true },
      { title: 'Valor Item', dataIndex: 'valor', key: 'valor', align: 'right', render: (v) => formatCurrencyBR(v) },
      { title: 'Taxa Item', dataIndex: 'taxa', key: 'taxa', align: 'center', render: (v) => formatPercent(v) },
      { title: 'Peso', dataIndex: 'peso', key: 'peso', align: 'center', render: (v) => formatPercent(v) },
      { title: 'Contribuição (TCMP Parcial)', dataIndex: 'tcmp_parcial', key: 'tcmp_parcial', align: 'center', render: (v) => <strong>{formatPercent(v)}</strong> },
    ];

    const renderColaboradoresTable = (row) => {
      const colaboradores = row.colaboradores || [];
      return (
        <Table
          size="small"
          bordered
          pagination={false}
          dataSource={colaboradores.map((c, idx) => ({ ...c, key: `${row.item}-${c.colaborador}-${idx}` }))}
          columns={[
            { title: 'Colaborador', dataIndex: 'colaborador', key: 'colaborador', ellipsis: true },
            { title: 'Valor', dataIndex: 'valor', key: 'valor', align: 'right', render: (v) => formatCurrencyBR(v) },
            { title: 'Taxa', dataIndex: 'taxa', key: 'taxa', align: 'center', render: (v) => formatPercent(v) },
            { title: 'Peso', dataIndex: 'peso', key: 'peso', align: 'center', render: (v) => formatPercent(v) },
            {
              title: 'TCMP Parcial',
              dataIndex: 'tcmp_parcial',
              key: 'tcmp_parcial',
              align: 'center',
              render: (v, r) => <strong>{formatPercent((v ?? ((r.taxa || 0) * (r.peso || 0))))}</strong>,
            },
          ]}
          onRow={(record) => ({
            onClick: () => {
              const totalValorColab = auditoriaData?.tcmp?.totais_por_colaborador?.[record.colaborador]?.total_valor || 0;
              openDrawerTcmpItem({ itemNome: row.item, colaborador: record.colaborador, record, totalValorColab });
            },
            style: { cursor: 'pointer' },
          })}
        />
      );
    };

    return (
      <div>
        <Alert
          message={<div><strong>Fórmula:</strong> <code>{auditoriaData.tcmp.formula}</code></div>}
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
        />

        <Table
          columns={columnsItem}
          dataSource={itemRows}
          pagination={false}
          size="small"
          bordered
          expandable={{
            expandedRowKeys: expandedTcmpKeys,
            onExpandedRowsChange: (keys) => setExpandedTcmpKeys(keys),
            rowExpandable: (record) => !record.__isTotal,
            expandedRowRender: (record) => renderColaboradoresTable(record),
          }}
          onRow={(record) => ({
            onClick: () => {
              if (record.__isTotal) {
                openDrawerTotalSelector({
                  tipo: 'TCMP',
                  titulo: 'TCMP TOTAL (por colaborador)',
                  totaisPorColab: auditoriaData?.tcmp?.totais_por_colaborador,
                  parcelasPorColab: auditoriaData?.tcmp?.parcelas_por_colaborador,
                });
                return;
              }
              setExpandedTcmpKeys((prev) => (prev.includes(record.key) ? prev.filter((k) => k !== record.key) : [...prev, record.key]));
            },
            style: { cursor: 'pointer' },
          })}
        />
      </div>
    );
  };

  // ==================== SEÇÃO C: FCMP ====================
  const renderFCMP = () => {
    if (erroDetalhes) {
      return (
        <Alert
          message="Não foi possível carregar os detalhes do FCMP"
          description={erroDetalhes}
          type="warning"
          showIcon
        />
      );
    }
    if (loadingDetalhes && (!fcmpDetalhes || fcmpDetalhes.length === 0)) {
      return (
        <div style={{ padding: 12, textAlign: 'center' }}>
          <Spin tip="Carregando detalhes do FCMP..." />
        </div>
      );
    }
    if (isAdiantamento) {
      return (
        <Alert
          message="FCMP para Adiantamentos"
          description={
            <div>
              <p>⚠️ <strong>Adiantamentos sempre usam FC fixo = 1.0</strong></p>
              <Divider />
              <p><strong>Motivo:</strong></p>
              <ul>
                <li>Pago <strong>ANTES</strong> do faturamento</li>
                <li>Metas ainda não foram realizadas</li>
                <li>FC real será calculado após fechamento</li>
                <li>Ajuste será feito na <strong>Reconciliação</strong></li>
              </ul>
              <Divider />
              <p style={{ marginBottom: 0 }}>
                ✅ <strong>FCMP Aplicado: 1.0000</strong>
              </p>
            </div>
          }
          type="warning"
          showIcon
          icon={<WarningOutlined />}
        />
      );
    }

    // Para pagamentos regulares
    if (!fcmpDetalhes || fcmpDetalhes.length === 0) {
      return (
        <Alert
          message="Detalhes de FCMP não disponíveis"
          type="info"
          showIcon
        />
      );
    }

    const colunasFCMP = [
      {
        title: 'Item',
        dataIndex: 'item',
        key: 'item',
        width: 180,
        ellipsis: true,
      },
      {
        title: 'Comissão Item',
        dataIndex: 'comissao',
        key: 'comissao',
        align: 'right',
        render: (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0),
      },
      {
        title: 'FC Real',
        dataIndex: 'fc',
        key: 'fc',
        align: 'center',
        render: (val) => {
          const cor = val > 1 ? '#52c41a' : val < 1 ? '#ff4d4f' : '#000';
          return <strong style={{ color: cor }}>{val?.toFixed(4)}</strong>;
        },
      },
      {
        title: 'Peso',
        dataIndex: 'peso',
        key: 'peso',
        align: 'center',
        render: (val) => `${(val * 100).toFixed(1)}%`,
      },
      {
        title: 'FCMP Parcial',
        dataIndex: 'fcmp_parcial',
        key: 'fcmp_parcial',
        align: 'center',
        render: (val) => <strong>{val?.toFixed(4)}</strong>,
      },
    ];

    const totalComissao = fcmpDetalhes.reduce((acc, d) => acc + (d.comissao || 0), 0);
    const fcmpFinal = fcmpDetalhes.reduce((acc, d) => acc + (d.fcmp_parcial || 0), 0);

    if (viewMode === VIEW_MODE.BASICO) {
      return (
        <div>
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="Itens no cálculo">{fcmpDetalhes.length}</Descriptions.Item>
            <Descriptions.Item label="FCMP Final">
              <strong style={{ color: fcmpFinal > 1 ? '#52c41a' : fcmpFinal < 1 ? '#ff4d4f' : '#000' }}>
                {fcmpFinal.toFixed(4)}
              </strong>
            </Descriptions.Item>
          </Descriptions>
          <Alert
            style={{ marginTop: 12 }}
            type="info"
            showIcon
            message="Modo Básico"
            description="Troque para 'Auditoria' para ver o passo a passo e clicar em um item para ver o FC detalhado por meta."
          />
        </div>
      );
    }

    // Auditoria (processo inteiro, por item -> colaboradores)
    if (loadingAuditoria) {
      return (
        <div style={{ padding: 12, textAlign: 'center' }}>
          <Spin tip="Carregando auditoria do processo..." />
        </div>
      );
    }
    if (erroAuditoria) {
      return <Alert type="warning" showIcon message="Falha ao carregar auditoria" description={erroAuditoria} />;
    }
    if (!auditoriaData?.fcmp) {
      return <Alert type="info" showIcon message="Auditoria não disponível" />;
    }

    if (auditoriaData.fcmp.calculado === false) {
      return (
        <Alert
          message="FCMP ainda não calculado (Processo não faturado)"
          description="Enquanto o processo não estiver FATURADO, o FCMP permanece 1.0000. A auditoria detalhada de metas será disponível após o faturamento."
          type="warning"
          showIcon
          icon={<WarningOutlined />}
        />
      );
    }

    const itens = auditoriaData.fcmp.itens || [];
    const itemRows = [...itens].map((it) => ({
      key: it.item,
      item: it.item,
      valor: it.valor,
      fc: it.fc,
      peso: it.peso,
      fcmp_parcial: (it.fc ?? 1) * (it.peso || 0),
      colaboradores: it.colaboradores || [],
    }));

    const totalValorItens = itemRows.reduce((acc, r) => acc + (r.valor || 0), 0);
    const numeradorItens = itemRows.reduce((acc, r) => acc + ((r.fc ?? 1) * (r.valor || 0)), 0);
    const fcTotal = totalValorItens > 0 ? (numeradorItens / totalValorItens) : 1;

    itemRows.push({
      key: '__TOTAL__',
      item: 'TOTAL',
      __isTotal: true,
      valor: totalValorItens,
      fc: fcTotal,
      peso: 1,
      fcmp_parcial: fcTotal,
    });

    const columnsItem = [
      { title: 'Item', dataIndex: 'item', key: 'item', ellipsis: true },
      { title: 'FC do item', dataIndex: 'fc', key: 'fc', align: 'center', render: (v) => (v ?? 1).toFixed(4) },
      { title: 'Peso', dataIndex: 'peso', key: 'peso', align: 'center', render: (v) => formatPercent(v) },
      { title: 'Contribuição (FCMP Parcial)', dataIndex: 'fcmp_parcial', key: 'fcmp_parcial', align: 'center', render: (v) => <strong>{(v ?? 0).toFixed(4)}</strong> },
    ];

    const renderColaboradoresTable = (row) => {
      const colaboradores = row.colaboradores || [];
      return (
        <Table
          size="small"
          bordered
          pagination={false}
          dataSource={colaboradores.map((c, idx) => ({ ...c, key: `${row.item}-${c.colaborador}-${idx}` }))}
          columns={[
            { title: 'Colaborador', dataIndex: 'colaborador', key: 'colaborador', ellipsis: true },
            { title: 'FC', dataIndex: 'fc', key: 'fc', align: 'center', render: (v) => (v ?? 1).toFixed(4) },
            { title: 'Peso', dataIndex: 'peso', key: 'peso', align: 'center', render: (v) => formatPercent(v) },
            {
              title: 'FCMP Parcial',
              dataIndex: 'fcmp_parcial',
              key: 'fcmp_parcial',
              align: 'center',
              render: (v, r) => <strong>{((v ?? ((r.fc ?? 1) * (r.peso || 0))) || 0).toFixed(4)}</strong>,
            },
          ]}
          onRow={(record) => ({
            onClick: () => {
              const totalValorColab = auditoriaData?.fcmp?.totais_por_colaborador?.[record.colaborador]?.total_valor || 0;
              openDrawerFcmpItem({ itemNome: row.item, colaborador: record.colaborador, record, totalValorColab });
            },
            style: { cursor: 'pointer' },
          })}
        />
      );
    };

    return (
      <div>
        <Alert
          message={<div><strong>Fórmula:</strong> <code>{auditoriaData.fcmp.formula}</code></div>}
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
        />

        <Table
          columns={columnsItem}
          dataSource={itemRows}
          pagination={false}
          size="small"
          bordered
          expandable={{
            expandedRowKeys: expandedFcmpKeys,
            onExpandedRowsChange: (keys) => setExpandedFcmpKeys(keys),
            rowExpandable: (record) => !record.__isTotal,
            expandedRowRender: (record) => renderColaboradoresTable(record),
          }}
          onRow={(record) => ({
            onClick: () => {
              if (record.__isTotal) {
                openDrawerTotalSelector({
                  tipo: 'FCMP',
                  titulo: 'FCMP TOTAL (por colaborador)',
                  totaisPorColab: auditoriaData?.fcmp?.totais_por_colaborador,
                  parcelasPorColab: auditoriaData?.fcmp?.parcelas_por_colaborador,
                });
                return;
              }
              setExpandedFcmpKeys((prev) => (prev.includes(record.key) ? prev.filter((k) => k !== record.key) : [...prev, record.key]));
            },
            style: { cursor: 'pointer' },
          })}
        />
      </div>
    );
  };

  // ==================== SEÇÃO D: CÁLCULO FINAL ====================
  const renderCalculoFinal = () => {
    const valorPago = pagamentoView.valor_pago || 0;
    const tcmp = pagamentoView.tcmp || 0;
    const fcmp = pagamentoView.fcmp || 1.0;
    const comissaoFinal = pagamentoView.comissao_calculada || 0;

    return (
      <div style={{ padding: 16, backgroundColor: '#f0f2f5', borderRadius: 4 }}>
        <Title level={5} style={{ marginBottom: 16 }}>
          <CalculatorOutlined /> Fórmula
        </Title>
        <div style={{ backgroundColor: '#fff', padding: 16, borderRadius: 4, marginBottom: 16 }}>
          <pre style={{ margin: 0, fontSize: 14 }}>
            <strong>Comissão = Valor_Pago × TCMP × FCMP</strong>
          </pre>
        </div>

        <Title level={5} style={{ marginBottom: 16 }}>Aplicando os valores:</Title>
        <div style={{ backgroundColor: '#fff', padding: 16, borderRadius: 4, marginBottom: 16 }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text>
              Comissão = {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorPago)}{' '}
              × {(tcmp * 100).toFixed(2)}% × {fcmp.toFixed(4)}
            </Text>
            <Text>
              Comissão = {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorPago)}{' '}
              × {tcmp.toFixed(4)} × {fcmp.toFixed(4)}
            </Text>
            <Text>
              Comissão = <strong style={{ fontSize: 16 }}>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(comissaoFinal)}
              </strong>
            </Text>
          </Space>
        </div>

        <Alert
          message={
            <span>
              <CheckCircleOutlined /> <strong>Comissão Final: </strong>
              <span style={{ fontSize: 18, color: '#52c41a', fontWeight: 'bold' }}>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(comissaoFinal)}
              </span>
            </span>
          }
          type="success"
          showIcon={false}
        />
      </div>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <DollarOutlined />
          <span>Detalhes do Cálculo - {pagamentoView.processo}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={900}
      destroyOnClose
    >
      <div style={{ marginBottom: 12 }}>
        <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
          <Segmented
            value={viewMode}
            onChange={(v) => setViewMode(v)}
            options={[
              { label: 'Básico', value: VIEW_MODE.BASICO },
              { label: 'Auditoria', value: VIEW_MODE.AUDITORIA },
            ]}
          />
          {drawerOpen && (
            <Button icon={<ArrowLeftOutlined />} onClick={() => setDrawerOpen(false)}>
              Fechar Detalhe do Item
            </Button>
          )}
        </Space>
      </div>

      <Collapse defaultActiveKey={['1', '2', '3', '4']} accordion={false}>
        <Panel
          header={
            <Space>
              <InfoCircleOutlined />
              <strong>📊 Informações Gerais</strong>
            </Space>
          }
          key="1"
        >
          {renderInformacoesGerais()}
        </Panel>

        <Panel
          header={
            <Space>
              <CalculatorOutlined />
              <strong>📈 TCMP (Taxa de Comissão Média Ponderada)</strong>
            </Space>
          }
          key="2"
        >
          {renderTCMP()}
        </Panel>

        <Panel
          header={
            <Space>
              {isAdiantamento ? <WarningOutlined /> : <CheckCircleOutlined />}
              <strong>{isAdiantamento ? '🔵 FCMP (Adiantamento)' : '🟢 FCMP (Pagamento Regular)'}</strong>
            </Space>
          }
          key="3"
        >
          {renderFCMP()}
        </Panel>

        <Panel
          header={
            <Space>
              <DollarOutlined />
              <strong>💰 Cálculo Final</strong>
            </Space>
          }
          key="4"
        >
          {renderCalculoFinal()}
        </Panel>
      </Collapse>

      <Drawer
        title={drawerTitle}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={520}
        destroyOnClose
      >
        {drawerContent || <Alert type="info" showIcon message="Nenhum detalhe disponível." />}
      </Drawer>
    </Modal>
  );
};

export default ModalDetalhesCalculoRecebimento;
