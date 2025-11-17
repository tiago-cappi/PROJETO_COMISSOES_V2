import React, { useEffect, useState } from 'react';
import { Modal, Spin, Alert, Typography, Divider, Table, Card, Collapse } from 'antd';
import { recebimentoAPI } from '../services/api';

const { Panel } = Collapse;

const { Title, Text } = Typography;

function formatCurrency(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatPercent(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
}

function formatDecimal(value, decimals = 2) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return num.toFixed(decimals);
}

const DetalhesRecebimentoModal = ({ 
  visible, 
  onClose, 
  processo, 
  colaborador, 
  mes, 
  ano,
  tipoAba  // 'REGULARES', 'ADIANTAMENTOS' ou 'RECONCILIACOES'
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detalhes, setDetalhes] = useState(null);

  useEffect(() => {
    if (visible && processo && colaborador) {
      carregarDetalhes();
    }
  }, [visible, processo, colaborador, mes, ano]);

  const carregarDetalhes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await recebimentoAPI.obterDetalhes(processo, colaborador, mes, ano);
      setDetalhes(response.data);
    } catch (err) {
      console.error('Erro ao carregar detalhes:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar detalhes do cálculo');
    } finally {
      setLoading(false);
    }
  };

  const renderTabelaItens = (itens, metrica) => {
    const colunas = [
      {
        title: 'Negócio',
        dataIndex: 'negocio',
        key: 'negocio',
        width: 120,
      },
      {
        title: 'Grupo',
        dataIndex: 'grupo',
        key: 'grupo',
        width: 120,
      },
      {
        title: 'Subgrupo',
        dataIndex: 'subgrupo',
        key: 'subgrupo',
        width: 120,
      },
      {
        title: 'Tipo',
        dataIndex: 'tipo_mercadoria',
        key: 'tipo_mercadoria',
        width: 100,
      },
      {
        title: 'Valor Item',
        dataIndex: 'valor',
        key: 'valor',
        width: 130,
        align: 'right',
        render: (val) => formatCurrency(val),
      },
    ];

    if (metrica === 'TCMP') {
      colunas.push(
        {
          title: 'Taxa Rateio',
          dataIndex: 'taxa_rateio',
          key: 'taxa_rateio',
          width: 110,
          align: 'right',
          render: (val) => formatPercent(val),
        },
        {
          title: 'Fatia Cargo',
          dataIndex: 'fatia_cargo',
          key: 'fatia_cargo',
          width: 110,
          align: 'right',
          render: (val) => formatPercent(val),
        },
        {
          title: 'Taxa Final',
          dataIndex: 'taxa',
          key: 'taxa',
          width: 110,
          align: 'right',
          render: (val) => formatPercent(val),
        },
        {
          title: 'Taxa × Valor',
          key: 'taxa_ponderada',
          width: 130,
          align: 'right',
          render: (_, record) => formatCurrency(record.taxa * record.valor),
        }
      );
    } else {
      colunas.push(
        {
          title: 'FC',
          dataIndex: 'fc',
          key: 'fc',
          width: 100,
          align: 'right',
          render: (val) => formatDecimal(val, 4),
        },
        {
          title: 'FC × Valor',
          key: 'fc_ponderado',
          width: 130,
          align: 'right',
          render: (_, record) => formatCurrency(record.fc * record.valor),
        }
      );
    }

    return (
      <Table
        dataSource={itens || []}
        columns={colunas}
        rowKey={(record, index) => `item-${index}`}
        pagination={false}
        size="small"
        scroll={{ x: 'max-content' }}
        bordered
      />
    );
  };

  const renderCalculoTCMP = () => {
    if (!detalhes?.tcmp_detalhes || Object.keys(detalhes.tcmp_detalhes).length === 0) {
      return (
        <Alert 
          message="Detalhes de TCMP não disponíveis" 
          description="Os detalhes do cálculo de TCMP não estão disponíveis para este registro."
          type="info" 
        />
      );
    }

    const tcmp = detalhes.tcmp_detalhes;
    const itens = tcmp.itens || [];
    const totalValor = tcmp.total_valor || 0;
    const somaPonderada = tcmp.soma_ponderada || 0;
    const tcmpFinal = tcmp.tcmp_final || 0;

    return (
      <Card title="📊 TCMP - Taxa de Comissão Média Ponderada" size="small" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 15 }}>
          <Text strong>Fórmula:</Text>
          <div style={{ 
            padding: '10px', 
            background: '#f5f5f5', 
            borderRadius: '4px', 
            marginTop: '5px',
            fontFamily: 'monospace'
          }}>
            TCMP = Σ(Taxa × Valor do Item) / Σ(Valor do Item)
          </div>
        </div>

        <Divider>Itens do Processo</Divider>

        {renderTabelaItens(itens, 'TCMP')}

        <Divider>Passo a Passo do Cálculo</Divider>

        <div style={{ background: '#fafafa', padding: '15px', borderRadius: '4px' }}>
          {/* Passo 1: Multiplicações individuais */}
          <div style={{ marginBottom: 15 }}>
            <Text strong style={{ fontSize: '14px', color: '#1890ff' }}>
              📝 Passo 1: Calcular Taxa × Valor para cada item
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20 }}>
              {itens.map((item, index) => {
                const taxaPonderada = item.taxa * item.valor;
                return (
                  <div key={index} style={{ marginBottom: 8 }}>
                    <div style={{ marginBottom: 4, fontFamily: 'monospace', fontSize: '12px' }}>
                      <Text>
                        Item {index + 1}: {formatPercent(item.taxa)} × {formatCurrency(item.valor)} = {formatCurrency(taxaPonderada)}
                      </Text>
                    </div>
                    
                    {/* Seção expansível para mostrar cálculo da Taxa Final */}
                    <Collapse 
                      ghost 
                      size="small" 
                      style={{ marginLeft: 20, background: '#fff', borderRadius: '4px' }}
                    >
                      <Panel 
                        header={
                          <Text style={{ fontSize: '11px', color: '#1890ff' }}>
                            🔍 Como foi calculada a Taxa Final de {formatPercent(item.taxa)}?
                          </Text>
                        } 
                        key="taxa"
                      >
                        <div style={{ padding: '8px', background: '#f0f5ff', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace' }}>
                          <div style={{ marginBottom: 4 }}>
                            <Text strong>Fórmula:</Text> Taxa Final = Taxa Rateio × Fatia Cargo
                          </div>
                          <div style={{ marginBottom: 4 }}>
                            <Text>Taxa Rateio = {formatPercent(item.taxa_rateio)}</Text>
                          </div>
                          <div style={{ marginBottom: 4 }}>
                            <Text>Fatia Cargo = {formatPercent(item.fatia_cargo)}</Text>
                          </div>
                          <Divider style={{ margin: '8px 0' }} />
                          <div>
                            <Text strong style={{ color: '#1890ff' }}>
                              Taxa Final = {formatPercent(item.taxa_rateio)} × {formatPercent(item.fatia_cargo)} = {formatPercent(item.taxa)}
                            </Text>
                          </div>
                        </div>
                      </Panel>
                    </Collapse>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Passo 2: Soma dos valores ponderados */}
          <div style={{ marginBottom: 15 }}>
            <Text strong style={{ fontSize: '14px', color: '#52c41a' }}>
              ➕ Passo 2: Somar todos os valores ponderados
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20, fontFamily: 'monospace', fontSize: '12px' }}>
              <Text>
                Σ(Taxa × Valor) = {itens.map((item, idx) => 
                  formatCurrency(item.taxa * item.valor)
                ).join(' + ')}
              </Text>
              <div style={{ marginTop: 4 }}>
                <Text strong>Σ(Taxa × Valor) = {formatCurrency(somaPonderada)}</Text>
              </div>
            </div>
          </div>

          {/* Passo 3: Soma dos valores */}
          <div style={{ marginBottom: 15 }}>
            <Text strong style={{ fontSize: '14px', color: '#fa8c16' }}>
              ➕ Passo 3: Somar todos os valores dos itens
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20, fontFamily: 'monospace', fontSize: '12px' }}>
              <Text>
                Σ(Valor) = {itens.map(item => formatCurrency(item.valor)).join(' + ')}
              </Text>
              <div style={{ marginTop: 4 }}>
                <Text strong>Σ(Valor) = {formatCurrency(totalValor)}</Text>
              </div>
            </div>
          </div>

          {/* Passo 4: Divisão final */}
          <div style={{ marginBottom: 0, padding: '12px', background: '#e6f7ff', borderRadius: '4px', border: '1px solid #91d5ff' }}>
            <Text strong style={{ fontSize: '14px', color: '#0050b3' }}>
              ➗ Passo 4: Calcular TCMP (dividir soma ponderada pela soma dos valores)
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20, fontFamily: 'monospace' }}>
              <div style={{ marginBottom: 4 }}>
                <Text>TCMP = Σ(Taxa × Valor) / Σ(Valor)</Text>
              </div>
              <div style={{ marginBottom: 4 }}>
                <Text>TCMP = {formatCurrency(somaPonderada)} / {formatCurrency(totalValor)}</Text>
              </div>
              <div>
                <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                  TCMP = {formatPercent(tcmpFinal)}
                </Text>
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderCalculoFCMP = () => {
    if (!detalhes?.fcmp_detalhes || Object.keys(detalhes.fcmp_detalhes).length === 0) {
      return (
        <Alert 
          message="Detalhes de FCMP não disponíveis" 
          description="Os detalhes do cálculo de FCMP não estão disponíveis para este registro. Isso pode ocorrer em reconciliações onde o FCMP é reutilizado do faturamento."
          type="info" 
        />
      );
    }

    const fcmp = detalhes.fcmp_detalhes;
    const itens = fcmp.itens || [];
    const totalValor = fcmp.total_valor || 0;
    const somaPonderada = fcmp.soma_ponderada || 0;
    const fcmpFinal = fcmp.fcmp_final || 0;

    return (
      <Card title="📉 FCMP - Fator de Correção Médio Ponderado" size="small">
        <div style={{ marginBottom: 15 }}>
          <Text strong>Fórmula:</Text>
          <div style={{ 
            padding: '10px', 
            background: '#f5f5f5', 
            borderRadius: '4px', 
            marginTop: '5px',
            fontFamily: 'monospace'
          }}>
            FCMP = Σ(FC × Valor do Item) / Σ(Valor do Item)
          </div>
        </div>

        <Divider>Itens do Processo</Divider>

        {renderTabelaItens(itens, 'FCMP')}

        <Divider>Passo a Passo do Cálculo</Divider>

        <div style={{ background: '#fafafa', padding: '15px', borderRadius: '4px' }}>
          {/* Passo 1: Multiplicações individuais */}
          <div style={{ marginBottom: 15 }}>
            <Text strong style={{ fontSize: '14px', color: '#1890ff' }}>
              📝 Passo 1: Calcular FC × Valor para cada item
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20 }}>
              {itens.map((item, index) => {
                const fcPonderado = item.fc * item.valor;
                return (
                  <div key={index} style={{ marginBottom: 8 }}>
                    <div style={{ marginBottom: 4, fontFamily: 'monospace', fontSize: '12px' }}>
                      <Text>
                        Item {index + 1}: {formatDecimal(item.fc, 4)} × {formatCurrency(item.valor)} = {formatCurrency(fcPonderado)}
                      </Text>
                    </div>
                    
                    {/* Seção expansível para mostrar cálculo do FC */}
                    <Collapse 
                      ghost 
                      size="small" 
                      style={{ marginLeft: 20, background: '#fff', borderRadius: '4px' }}
                    >
                      <Panel 
                        header={
                          <Text style={{ fontSize: '11px', color: '#52c41a' }}>
                            🔍 Como foi calculado o FC de {formatDecimal(item.fc, 4)}?
                          </Text>
                        } 
                        key="fc"
                      >
                        <div style={{ padding: '8px', background: '#f6ffed', borderRadius: '4px', fontSize: '11px' }}>
                          {item.fc_detalhes ? (
                            <div style={{ fontFamily: 'monospace' }}>
                              <div style={{ marginBottom: 8 }}>
                                <Text strong>Fórmula:</Text> FC = Σ(Peso × Componente de Meta)
                              </div>
                              <Divider style={{ margin: '8px 0' }} />
                              {item.fc_detalhes.componentes && item.fc_detalhes.componentes.map((comp, idx) => (
                                <div key={idx} style={{ marginBottom: 6, paddingLeft: 8 }}>
                                  <div style={{ marginBottom: 2 }}>
                                    <Text strong>{comp.nome_meta}:</Text>
                                  </div>
                                  <div style={{ paddingLeft: 12, fontSize: '10px' }}>
                                    <div>Realizado: {comp.realizado}</div>
                                    <div>Meta: {comp.meta}</div>
                                    <div>Atingimento: {formatPercent(comp.atingimento)}</div>
                                    <div>Peso: {formatPercent(comp.peso)}</div>
                                    <div style={{ color: '#52c41a' }}>
                                      <strong>Componente FC: {formatDecimal(comp.componente_fc, 4)}</strong>
                                    </div>
                                  </div>
                                </div>
                              ))}
                              <Divider style={{ margin: '8px 0' }} />
                              <div>
                                <Text strong style={{ color: '#52c41a' }}>
                                  FC Total = {formatDecimal(item.fc, 4)}
                                </Text>
                              </div>
                            </div>
                          ) : (
                            <Alert
                              message="Detalhes do cálculo de FC"
                              description="O FC é calculado com base no atingimento de várias metas (rentabilidade, faturamento, conversão, etc.). Os detalhes completos do cálculo requerem informações adicionais do backend."
                              type="info"
                              showIcon
                              style={{ fontSize: '10px' }}
                            />
                          )}
                        </div>
                      </Panel>
                    </Collapse>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Passo 2: Soma dos valores ponderados */}
          <div style={{ marginBottom: 15 }}>
            <Text strong style={{ fontSize: '14px', color: '#52c41a' }}>
              ➕ Passo 2: Somar todos os valores ponderados
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20, fontFamily: 'monospace', fontSize: '12px' }}>
              <Text>
                Σ(FC × Valor) = {itens.map((item, idx) => 
                  formatCurrency(item.fc * item.valor)
                ).join(' + ')}
              </Text>
              <div style={{ marginTop: 4 }}>
                <Text strong>Σ(FC × Valor) = {formatCurrency(somaPonderada)}</Text>
              </div>
            </div>
          </div>

          {/* Passo 3: Soma dos valores */}
          <div style={{ marginBottom: 15 }}>
            <Text strong style={{ fontSize: '14px', color: '#fa8c16' }}>
              ➕ Passo 3: Somar todos os valores dos itens
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20, fontFamily: 'monospace', fontSize: '12px' }}>
              <Text>
                Σ(Valor) = {itens.map(item => formatCurrency(item.valor)).join(' + ')}
              </Text>
              <div style={{ marginTop: 4 }}>
                <Text strong>Σ(Valor) = {formatCurrency(totalValor)}</Text>
              </div>
            </div>
          </div>

          {/* Passo 4: Divisão final */}
          <div style={{ marginBottom: 0, padding: '12px', background: '#f6ffed', borderRadius: '4px', border: '1px solid #b7eb8f' }}>
            <Text strong style={{ fontSize: '14px', color: '#389e0d' }}>
              ➗ Passo 4: Calcular FCMP (dividir soma ponderada pela soma dos valores)
            </Text>
            <div style={{ marginTop: 8, marginLeft: 20, fontFamily: 'monospace' }}>
              <div style={{ marginBottom: 4 }}>
                <Text>FCMP = Σ(FC × Valor) / Σ(Valor)</Text>
              </div>
              <div style={{ marginBottom: 4 }}>
                <Text>FCMP = {formatCurrency(somaPonderada)} / {formatCurrency(totalValor)}</Text>
              </div>
              <div>
                <Text strong style={{ fontSize: '16px', color: '#52c41a' }}>
                  FCMP = {formatDecimal(fcmpFinal, 4)}
                </Text>
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const getTituloModal = () => {
    const tipoTexto = tipoAba === 'ADIANTAMENTOS' 
      ? 'Adiantamento' 
      : tipoAba === 'RECONCILIACOES' 
        ? 'Reconciliação' 
        : 'Pagamento Regular';
    return `Detalhes do Cálculo - ${tipoTexto}`;
  };

  return (
    <Modal
      title={getTituloModal()}
      visible={visible}
      onCancel={onClose}
      width={1200}
      footer={null}
      bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
    >
      {loading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" tip="Carregando detalhes..." />
        </div>
      )}

      {error && <Alert message="Erro" description={error} type="error" showIcon />}

      {!loading && !error && detalhes && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <Text strong>Processo: </Text>
            <Text>{processo}</Text>
            <Divider type="vertical" />
            <Text strong>Colaborador: </Text>
            <Text>{colaborador}</Text>
          </div>

          {renderCalculoTCMP()}
          {renderCalculoFCMP()}

          <Alert
            message="Informação"
            description="Os valores de TCMP e FCMP são calculados como médias ponderadas pelo valor de cada item do processo."
            type="info"
            showIcon
            style={{ marginTop: 20 }}
          />
        </div>
      )}
    </Modal>
  );
};

export default DetalhesRecebimentoModal;

