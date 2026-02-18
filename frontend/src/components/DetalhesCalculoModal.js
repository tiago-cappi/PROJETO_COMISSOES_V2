import React, { useMemo, useState } from 'react';
import { Card, Divider, Progress, Space, Tooltip, Typography } from 'antd';
import { InfoCircleOutlined, CalculatorOutlined } from '@ant-design/icons';
import EscadaDemonstrativoModal from './EscadaDemonstrativoModal';

const { Title, Text } = Typography;

function formatCurrencyBR(value) {
    const num = Number(value);
    if (isNaN(num)) return '-';
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatPercent(value) {
    const num = Number(value);
    if (isNaN(num)) return '-';
    return `${(num * 100).toFixed(2)}%`;
}

function formatPercentNoScale(value) {
    const num = Number(value);
    if (isNaN(num)) return '-';
    return `${num.toFixed(2)}%`;
}

function formatDecimal4(value) {
    const num = Number(value);
    if (isNaN(num)) return '-';
    return num.toFixed(4);
}

const COMPONENTES_META = [
    {
        key: 'fat_linha',
        titulo: 'Meta: Faturamento da Linha',
        emoji: '📈',
    },
    {
        key: 'conv_linha',
        titulo: 'Meta: Conversão da Linha',
        emoji: '🔁',
    },
    {
        key: 'rentab',
        titulo: 'Meta: Rentabilidade',
        emoji: '💹',
    },
    {
        key: 'fat_ind',
        titulo: 'Meta: Faturamento Individual',
        emoji: '🧾',
    },
    {
        key: 'conv_ind',
        titulo: 'Meta: Conversão Individual',
        emoji: '🔄',
    },
    {
        key: 'retencao',
        titulo: 'Meta: Retenção de Clientes',
        emoji: '🛡️',
    },
    {
        key: 'forn1',
        buildTitulo: (row) => `Meta: Fornecedor 1 (${row?.fornecedor_1_nome || '-'})`,
        emoji: '🏷️',
        extraSub: (row) => (row?.moeda_forn1 ? `Moeda: ${row.moeda_forn1} · YTD` : 'YTD'),
    },
    {
        key: 'forn2',
        buildTitulo: (row) => `Meta: Fornecedor 2 (${row?.fornecedor_2_nome || '-'})`,
        emoji: '🏷️',
        extraSub: (row) => (row?.moeda_forn2 ? `Moeda: ${row.moeda_forn2} · YTD` : 'YTD'),
    },
];

const DetalhesCalculoModal = ({ rowData, isHistorico = false }) => {
    const [isEscadaModalVisible, setIsEscadaModalVisible] = useState(false);

    const capFcMax = Number(rowData?.cap_fc_max);
    const capFcMaxPercent = isNaN(capFcMax) ? '100%' : formatPercent(capFcMax);

    const somaFCBruto = useMemo(() => {
        let soma = 0;
        COMPONENTES_META.forEach(({ key }) => {
            const peso = Number(rowData?.[`peso_${key}`]);
            const comp = Number(rowData?.[`comp_fc_${key}`]);
            if (!isNaN(peso) && peso > 0 && !isNaN(comp)) {
                soma += comp;
            }
        });
        return soma;
    }, [rowData]);

    const somaCappedMaiorQueFinal = somaFCBruto > Number(rowData?.fator_correcao_fc || 0);

    return (
        <div className="detalhes-container">
            {isHistorico && (
                <div style={{ padding: '10px', background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: '4px', marginBottom: '15px' }}>
                    <strong>⚠️ CÁLCULO DE RECONCILIAÇÃO (HISTÓRICO)</strong>
                    <p style={{ margin: 0 }}>Os "Valores Realizados" usados aqui são do período histórico do processo, e não do mês atual.</p>
                </div>
            )}

            {/* Special Cross-Selling Section */}
            {rowData?.observacao === 'CROSS_SELLING' && (
                <div style={{ padding: '12px', background: '#fff7e6', border: '2px solid #ffa940', borderRadius: '8px', marginBottom: '20px' }}>
                    <Title level={4} style={{ marginBottom: 8, color: '#d46b08' }}>🎯 COMISSÃO POR CROSS-SELLING</Title>
                    <div style={{ marginBottom: 12 }}>
                        <Text><b>Tipo:</b> Comissão Especial de Cross-Selling (Consultor Externo)</Text><br />
                        <Text type="secondary">Você recebeu comissão por vender um produto/serviço fora da sua linha de negócio atribuída.</Text>
                    </div>
                    <div className="cards-line">
                        <Card className="mini-card" style={{ background: '#fffbe6' }}>
                            <Text strong>Valor do Item</Text>
                            <div className="mini-card-value">{formatCurrencyBR(rowData?.faturamento_item)}</div>
                        </Card>
                        <Card className="mini-card" style={{ background: '#fffbe6' }}>
                            <Text strong>Taxa de Cross-Selling</Text>
                            <div className="mini-card-value">{formatPercent(Number(rowData?.taxa_rateio_aplicada || 0))}</div>
                            <Text type="secondary">Configurada para esta linha</Text>
                        </Card>
                        <Card className="mini-card" style={{ background: '#fff1b8' }}>
                            <Text strong>Comissão Calculada</Text>
                            <div className="mini-card-value" style={{ color: '#d46b08' }}>{formatCurrencyBR(rowData?.comissao_calculada)}</div>
                        </Card>
                    </div>
                    <div style={{ marginTop: 12, padding: '8px', background: '#fff', borderRadius: '4px', border: '1px solid #d9d9d9' }}>
                        <Text><b>Cálculo:</b> {formatCurrencyBR(rowData?.faturamento_item)} × {formatPercent(Number(rowData?.taxa_rateio_aplicada || 0))} = {formatCurrencyBR(rowData?.comissao_calculada)}</Text><br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                            ⚠️ Comissões de cross-selling não usam FC (Fator de Correção). O valor é fixo com base na taxa configurada.
                        </Text>
                    </div>
                </div>
            )}

            <div className="passo">
                <Title level={4} style={{ marginBottom: 8 }}>Detalhes do Cálculo da Comissão</Title>
                <div className="detalhes-contexto">
                    <Text><b>Colaborador:</b> {rowData?.nome_colaborador} ({rowData?.cargo})</Text><br />
                    <Text><b>Processo:</b> {rowData?.processo}</Text><br />
                    <Text><b>Item:</b> {rowData?.cod_produto} - {rowData?.descricao_produto}</Text>
                </div>
            </div>

            <Divider />

            <div className="passo">
                <Title level={5}>Passo 1: Cálculo da Comissão Potencial (Base)</Title>
                <Text type="secondary">
                    Este é o valor máximo que você receberia por este item, antes de aplicarmos o Fator de Correção (FC) de desempenho.
                </Text>

                <div className="cards-line">
                    <Card className="mini-card">
                        <Text strong>Valor do Item</Text>
                        <div className="mini-card-value">{formatCurrencyBR(rowData?.faturamento_item)}</div>
                        <Text type="secondary">(A)</Text>
                    </Card>
                    <Card className="mini-card">
                        <Text strong>Taxa de Rateio (da Regra)</Text>
                        <div className="mini-card-value">{formatPercent(Number(rowData?.taxa_rateio_aplicada || 0))}</div>
                        <Text type="secondary">(B)</Text>
                    </Card>
                    <Card className="mini-card">
                        <Text strong>Sua Fatia do Cargo (PE)</Text>
                        <div className="mini-card-value">{formatPercent(Number(rowData?.percentual_elegibilidade_pe || 0))}</div>
                        <Text type="secondary">(C)</Text>
                    </Card>
                </div>

                <div className="formula-bloco">
                    <Text>Fórmula: (A) × (B) × (C)</Text><br />
                    <Text>
                        Cálculo: {formatCurrencyBR(rowData?.faturamento_item)} × {formatPercent(Number(rowData?.taxa_rateio_aplicada || 0))} × {formatPercent(Number(rowData?.percentual_elegibilidade_pe || 0))}
                    </Text>
                    <div className="resultado-linha">
                        <Text strong>Comissão Potencial (Base) = {formatCurrencyBR(rowData?.comissao_potencial_maxima)}</Text>
                    </div>
                </div>
            </div>

            <Divider />

            <div className="passo">
                <Title level={5}>Passo 2: Cálculo do Fator de Correção (FC)</Title>
                <Text type="secondary">
                    Ajustamos sua comissão base usando o Fator de Correção (FC). O FC (de 0% a 100%) mede seu desempenho em relação às metas.
                </Text>

                <div className="fc-total">
                    <Card>
                        <Space direction="vertical" size={4}>
                            <Text strong>FC Total Aplicado: {formatPercent(Number(rowData?.fator_correcao_fc || 0))}</Text>
                            <Text type="secondary">Composição do Fator de Correção (FC)</Text>
                        </Space>
                    </Card>
                </div>

                <div className="fc-cards-grid">
                    {COMPONENTES_META.map((cfg) => {
                        const peso = Number(rowData?.[`peso_${cfg.key}`]);
                        if (isNaN(peso) || peso <= 0) return null;

                        const realizado = rowData?.[`realizado_${cfg.key}`];
                        const meta = rowData?.[`meta_${cfg.key}`];
                        const ating = Number(rowData?.[`ating_${cfg.key}`]);
                        const atingCap = Number(rowData?.[`ating_cap_${cfg.key}`]);
                        const comp = rowData?.[`comp_fc_${cfg.key}`];

                        const limiteAplicado = !isNaN(ating) && !isNaN(atingCap) && ating > atingCap;
                        const titulo = cfg.buildTitulo ? cfg.buildTitulo(rowData) : cfg.titulo;

                        return (
                            <Card key={cfg.key} className="fc-card" title={<span>{cfg.emoji} {titulo}</span>} extra={<span>Peso: <b>{formatPercent(peso)}</b></span>}>
                                <div className="fc-card-body">
                                    <div className="valores">
                                        <div>
                                            <Text type="secondary">Realizado</Text>
                                            <div className="valor">
                                                {cfg.key === 'rentab' ? formatPercentNoScale(realizado) : formatCurrencyBR(realizado)}
                                            </div>
                                        </div>
                                        <div>
                                            <Text type="secondary">Meta</Text>
                                            <div className="valor">
                                                {cfg.key === 'rentab' ? formatPercentNoScale(meta) : formatCurrencyBR(meta)}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="progresso">
                                        <Progress
                                            percent={isNaN(atingCap) ? 0 : (atingCap * 100)}
                                            format={() => (isNaN(ating) ? '-' : formatPercent(ating))}
                                        />
                                    </div>

                                    <div className="rodape">
                                        <div>
                                            <Text>
                                                Atingimento (Realizado / Meta): <b>{isNaN(ating) ? '-' : formatPercent(ating)}</b>
                                            </Text>
                                        </div>
                                        <div>
                                            <Text>
                                                Atingimento (c/ Teto): <b>{isNaN(atingCap) ? '-' : formatPercent(atingCap)}</b>
                                            </Text>
                                        </div>
                                        {limiteAplicado && (
                                            <div className="limit-highlight">
                                                <Tooltip title={`Seu atingimento de ${formatPercent(ating)} foi limitado pelo teto de ${formatPercent(atingCap)}.`}>
                                                    <InfoCircleOutlined />
                                                </Tooltip>
                                                <Text type="danger" style={{ marginLeft: 6 }}>Limitado pelo teto</Text>
                                            </div>
                                        )}

                                        <Divider style={{ margin: '12px 0' }} />

                                        <div className="contrib">
                                            <Text>
                                                Contribuição para o FC: <b>{formatDecimal4(comp)}</b>
                                            </Text>
                                            <Text type="secondary" style={{ display: 'block' }}>
                                                ({isNaN(atingCap) ? '-' : formatPercent(atingCap)} × {formatPercent(peso)})
                                            </Text>
                                        </div>

                                        {cfg.extraSub && (
                                            <div className="extra-sub">
                                                <Text type="secondary">{cfg.extraSub(rowData)}</Text>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
                </div>

                <Card className="fc-sumario">
                    <Space direction="vertical" size={4}>
                        <Text>Soma dos Componentes: <b>{formatDecimal4(somaFCBruto)}</b></Text>
                        <Text>FC Bruto (Soma) = <b>{formatDecimal4(somaFCBruto)}</b></Text>
                        <Text>Teto Máximo do FC: <b>{capFcMaxPercent}</b></Text>
                        
                        <Divider style={{ margin: '8px 0' }} />
                        
                        {/* Exibir lógica de Escada se disponível */}
                        {rowData?.fc_escada_modo === 'ESCADA' ? (
                            <>
                                <Text>
                                    FC Rampa (com Teto): <b>{formatDecimal4(rowData?.fator_correcao_fc_rampa || Math.min(somaFCBruto, capFcMax))}</b>
                                </Text>
                                <div 
                                    style={{ 
                                        marginTop: 8, 
                                        padding: 8, 
                                        background: '#e6f7ff', 
                                        borderRadius: 4, 
                                        border: '1px solid #91d5ff',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s'
                                    }}
                                    className="escada-block-hover"
                                    onClick={() => setIsEscadaModalVisible(true)}
                                    title="Clique para ver o cálculo detalhado"
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Text strong style={{ color: '#0050b3' }}>
                                            🪜 Regra de Escada Aplicada <CalculatorOutlined />
                                        </Text>
                                        <Text type="secondary" style={{ fontSize: 10 }}>Clique para demonstrativo</Text>
                                    </div>
                                    <div style={{ marginLeft: 8 }}>
                                        <Text>Modo: <b>ESCADA</b></Text><br/>
                                        <Text>Degraus: <b>{rowData?.fc_escada_num_degraus}</b></Text><br/>
                                        <Text>Degrau Atingido: <b>#{rowData?.fc_escada_degrau_indice}</b></Text><br/>
                                        <Text strong>FC Final Aplicado = {formatDecimal4(rowData?.fator_correcao_fc)}</Text>
                                    </div>
                                </div>

                                <EscadaDemonstrativoModal
                                    visible={isEscadaModalVisible}
                                    onClose={() => setIsEscadaModalVisible(false)}
                                    data={{
                                        cargo: rowData?.cargo,
                                        numDegraus: rowData?.fc_escada_num_degraus,
                                        piso: rowData?.fc_escada_piso,
                                        performanceRampa: rowData?.fator_correcao_fc_rampa || Math.min(somaFCBruto, capFcMax),
                                        multiplicadorFinal: rowData?.fator_correcao_fc,
                                        degrauAtingido: rowData?.fc_escada_degrau_indice
                                    }}
                                />
                            </>
                        ) : (
                           <Text>
                                FC Final Aplicado = <b>{formatDecimal4(rowData?.fator_correcao_fc)}</b>
                                {somaCappedMaiorQueFinal && rowData?.fc_escada_modo !== 'ESCADA' && (
                                    <span className="limit-highlight" style={{ marginLeft: 8 }}>
                                        <Tooltip title={`Sua soma de ${formatDecimal4(somaFCBruto)} foi limitada pelo teto do FC de ${formatPercent(Number(rowData?.cap_fc_max || 1))}.`}>
                                            <InfoCircleOutlined />
                                        </Tooltip>
                                    </span>
                                )}
                            </Text>
                        )}
                    </Space>
                </Card>
            </div>

            <Divider />

            <div className="passo">
                <Title level={5}>Passo 3: Cálculo Final da Comissão</Title>
                <Text type="secondary">
                    Finalmente, multiplicamos sua Comissão Potencial pelo Fator de Correção (FC) final.
                </Text>

                <div className="cards-line">
                    <Card className="mini-card">
                        <Text strong>Comissão Potencial (Base)</Text>
                        <div className="mini-card-value">{formatCurrencyBR(rowData?.comissao_potencial_maxima)}</div>
                        <Text type="secondary">(A)</Text>
                    </Card>
                    <Card className="mini-card">
                        <Text strong>Fator de Correção (FC)</Text>
                        <div className="mini-card-value">{formatDecimal4(rowData?.fator_correcao_fc)}</div>
                        <Text type="secondary">(B)</Text>
                    </Card>
                </div>

                <div className="formula-bloco">
                    <Text>Fórmula: (A) × (B)</Text><br />
                    <Text>
                        Cálculo: {formatCurrencyBR(rowData?.comissao_potencial_maxima)} × {formatDecimal4(rowData?.fator_correcao_fc)}
                    </Text>
                    <div className="resultado-linha">
                        <Text strong>Resultado: Comissão Calculada = {formatCurrencyBR(rowData?.comissao_calculada)}</Text>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DetalhesCalculoModal;

