import React from 'react';
import { Modal, Typography, Divider, Row, Col, Card, Steps, Alert, Tag } from 'antd';
import { CalculatorOutlined, ArrowRightOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

function formatPercent(value) {
    const num = Number(value);
    if (isNaN(num)) return '-';
    // Mostra até 4 casas decimais para didática no cálculo, mas 2 no geral
    return `${(num * 100).toFixed(2)}%`;
}

function formatDecimal(value) {
    const num = Number(value);
    if (isNaN(num)) return '-';
    return num.toFixed(4);
}

const EscadaDemonstrativoModal = ({ visible, onClose, data }) => {
    if (!data) return null;

    // Normalização dos dados recebidos
    const {
        cargo,
        numDegraus, // N
        piso,       // P
        performanceRampa, // FC_rampa
        multiplicadorFinal, // M
        degrauAtingido // i
    } = data;

    // Cálculos Intermediários para Didática
    const N = Number(numDegraus);
    const P = Number(piso);
    const Rampa = Number(performanceRampa);
    const Topo = 1.0;
    
    // Passo 1: Tamanho do Intervalo
    // Fórmula: (1.0 - P) / (N - 1)
    const numIntervalos = N - 1;
    const tamanhoIntervalo = (Topo - P) / numIntervalos;

    // Passo 2: Onde cai a performance (sem arredondamento)
    // Valor "bruto" do índice: Rampa / (1 / (N-1)) ?? Não. 
    // A fórmula inversa é: O degrau sobe a cada X de performance.
    // Intervalo de performance por degrau = 1.0 / (N - 1)
    // Ex: N=5 (4 intervalos). Perf 0..0.25 -> Degrau 0. 0.25..0.50 -> Degrau 1.
    const tamanhoFaixaPerformance = 1.0 / numIntervalos;
    
    // Cálculo do 'i' teórico
    const indiceTeorico = Rampa * numIntervalos; // Ex: 0.74 * 4 = 2.96

    return (
        <Modal
            title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <CalculatorOutlined style={{ color: '#1890ff' }} />
                    <span>Demonstrativo de Cálculo: Regra de Escada</span>
                </div>
            }
            open={visible}
            onCancel={onClose}
            footer={null}
            width={800}
            destroyOnClose
        >
            <Alert 
                message="Transparência Total" 
                description="Este painel demonstra exatamente como sua performance foi convertida em fator de comissão segundo a regra do seu cargo." 
                type="info" 
                showIcon 
                style={{ marginBottom: 24 }}
            />

            {/* SEÇÃO 1: FONTES DE DADOS */}
            <Title level={5}>1. Dados de Entrada</Title>
            <Row gutter={[16, 16]}>
                <Col span={12}>
                    <Card size="small" title={<Text strong style={{ color: '#722ed1' }}>🟣 Configuração (Cargo: {cargo})</Text>} bordered={false} style={{ background: '#f9f0ff' }}>
                        <p><b>Modo:</b> ESCADA</p>
                        <p><b>Número de Degraus (N):</b> {N}</p>
                        <p><b>Piso (P):</b> {formatDecimal(P)} ({formatPercent(P)})</p>
                        <p><small>Origem: Tabela de Regras (Excel)</small></p>
                    </Card>
                </Col>
                <Col span={12}>
                    <Card size="small" title={<Text strong style={{ color: '#096dd9' }}>🔵 Sua Performance</Text>} bordered={false} style={{ background: '#e6f7ff' }}>
                        <p><b>Performance Real (Rampa):</b> {formatDecimal(Rampa)}</p>
                        <p><b>Atingimento:</b> {formatPercent(Rampa)}</p>
                        <p><small>Origem: Cálculo de Metas/Métricas</small></p>
                    </Card>
                </Col>
            </Row>

            <Divider />

            {/* SEÇÃO 2: CÁLCULO PASSO A PASSO */}
            <Title level={5}>2. O Cálculo Passo a Passo</Title>
            
            <div style={{ padding: 16, border: '1px solid #d9d9d9', borderRadius: 8, background: '#fafafa' }}>
                <Steps direction="vertical" current={-1}>
                    
                    {/* PASSO A */}
                    <Step 
                        title="Definição das Faixas" 
                        status="process"
                        description={
                            <div>
                                <Paragraph>
                                    O sistema divide a performance (0% a 100%) em <b>{numIntervalos}</b> intervalos iguais (pois são {N} degraus).
                                </Paragraph>
                                <div style={{ fontFamily: 'monospace', background: '#fff', padding: 8, borderRadius: 4, border: '1px dashed #ccc' }}>
                                    Tamanho da Faixa = 100% ÷ {numIntervalos} = <b>{formatPercent(tamanhoFaixaPerformance)}</b>
                                </div>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    Isso significa que a cada {formatPercent(tamanhoFaixaPerformance)} de meta batida, você sobe um degrau.
                                </Text>
                            </div>
                        } 
                    />

                    {/* PASSO B */}
                    <Step 
                        title="Cálculo do Degrau Atingido (Sem Tolerância)" 
                        status="process"
                        description={
                            <div>
                                <Paragraph>
                                    Verificamos quantas faixas completas sua performance de <Text strong style={{ color: '#096dd9' }}>{formatDecimal(Rampa)}</Text> preencheu.
                                </Paragraph>
                                <div style={{ fontFamily: 'monospace', background: '#fff', padding: 8, borderRadius: 4, border: '1px dashed #ccc' }}>
                                    Índice = floor(Performance × Intervalos) <br/>
                                    Índice = floor(<span style={{ color: '#096dd9' }}>{formatDecimal(Rampa)}</span> × {numIntervalos}) <br/>
                                    Índice = floor({formatDecimal(indiceTeorico)}) = <b>{degrauAtingido}</b>
                                </div>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    {indiceTeorico < degrauAtingido + 1 && indiceTeorico > degrauAtingido ? 
                                        `Note: Você tinha ${formatDecimal(indiceTeorico)}, mas como a regra é sem tolerância, arredondamos para baixo (${degrauAtingido}).` : 
                                        'O índice define em qual degrau da escada você parou.'}
                                </Text>
                            </div>
                        } 
                    />

                    {/* PASSO C */}
                    <Step 
                        title="Determinação do Multiplicador Final" 
                        status="finish"
                        description={
                            <div>
                                <Paragraph>
                                    Calculamos o valor do degrau <b>#{degrauAtingido}</b> interpolando entre o Piso (<span style={{ color: '#722ed1' }}>{P}</span>) e o Teto (1.0).
                                </Paragraph>
                                <div style={{ fontFamily: 'monospace', background: '#fff', padding: 8, borderRadius: 4, border: '1px dashed #ccc' }}>
                                    Multiplicador = Piso + (Índice × Incremento) <br/>
                                    Incremento = (1.0 - <span style={{ color: '#722ed1' }}>{P}</span>) ÷ {numIntervalos} = {formatDecimal(tamanhoIntervalo)} <br/>
                                    <br/>
                                    M = <span style={{ color: '#722ed1' }}>{P}</span> + (<b>{degrauAtingido}</b> × {formatDecimal(tamanhoIntervalo)}) <br/>
                                    M = <span style={{ color: '#722ed1' }}>{P}</span> + {formatDecimal(degrauAtingido * tamanhoIntervalo)} <br/>
                                    M = <Text strong style={{ color: '#389e0d', fontSize: 16 }}>{formatDecimal(multiplicadorFinal)}</Text>
                                </div>
                            </div>
                        } 
                    />
                </Steps>
            </div>

            <Divider />

            {/* SEÇÃO 3: VISUALIZAÇÃO GRÁFICA */}
            <Title level={5}>3. Visualização</Title>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <Text>Piso ({formatPercent(P)})</Text>
                <Text>Topo (100%)</Text>
            </div>
            <div style={{ display: 'flex', width: '100%', height: 40, border: '1px solid #d9d9d9', borderRadius: 4, overflow: 'hidden' }}>
                {Array.from({ length: N }).map((_, idx) => {
                    const isActive = idx === degrauAtingido;
                    const isPassed = idx < degrauAtingido;
                    
                    // Cálculo do valor deste degrau para label
                    const valorDegrau = P + (idx * tamanhoIntervalo);
                    
                    let bg = '#f5f5f5'; // Futuro
                    if (isPassed) bg = '#d9f7be'; // Passado
                    if (isActive) bg = '#1890ff'; // Atual

                    return (
                        <div 
                            key={idx}
                            style={{ 
                                flex: 1, 
                                background: bg, 
                                borderRight: idx < N-1 ? '1px solid #fff' : 'none',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: isActive ? '#fff' : '#595959',
                                fontWeight: isActive ? 'bold' : 'normal',
                                fontSize: 10,
                                position: 'relative',
                                cursor: 'help'
                            }}
                            title={`Degrau ${idx}: Multiplicador ${formatPercent(valorDegrau)}`}
                        >
                            {formatPercent(valorDegrau)}
                        </div>
                    );
                })}
            </div>
            <div style={{ textAlign: 'center', marginTop: 8 }}>
                <Tag color="blue">Você está aqui: Degrau {degrauAtingido}</Tag>
            </div>

        </Modal>
    );
};

export default EscadaDemonstrativoModal;
