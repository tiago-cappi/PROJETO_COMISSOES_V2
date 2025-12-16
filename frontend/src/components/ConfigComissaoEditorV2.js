import React, { useEffect, useMemo, useState } from 'react';
import { 
    Card, 
    Table, 
    Space, 
    Button, 
    Select, 
    Modal, 
    Form, 
    InputNumber, 
    message, 
    Typography, 
    Divider,
    Tag,
    Tooltip,
    Alert,
    Progress,
    Row,
    Col,
    Statistic,
    Steps,
    Badge
} from 'antd';
import { 
    FilterOutlined, 
    PlusOutlined, 
    SearchOutlined, 
    CheckCircleOutlined,
    PercentageOutlined,
    TeamOutlined,
    InfoCircleOutlined,
    ThunderboltOutlined,
    EyeOutlined,
    CloseOutlined,
    CheckOutlined
} from '@ant-design/icons';
import { regrasAPI } from '../services/api';
import './ConfigComissaoEditor.css';

const { Option } = Select;
const { Text, Title } = Typography;

const CONTEXT_FIELDS = ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria', 'cargo'];

/**
 * Componente de filtros com visual melhorado
 */
const FilterSection = ({ options, filters, setFilters, loading }) => (
    <div className="config-filter-section">
        <div className="config-filter-title">
            <FilterOutlined /> Filtros de Busca
        </div>
        <div className="config-filter-grid">
            {CONTEXT_FIELDS.map((field) => (
                <div key={field} className="config-filter-item">
                    <label className="config-filter-label">{field}</label>
                    <Select
                        placeholder={`Selecione ${field}`}
                        style={{ width: '100%' }}
                        allowClear
                        value={filters[field]}
                        onChange={(v) => setFilters((prev) => ({ ...prev, [field]: v }))}
                        showSearch
                        filterOption={(input, option) => 
                            String(option?.children || '').toLowerCase().includes((input || '').toLowerCase())
                        }
                    >
                        {(options[field] || []).map((opt) => (
                            <Option key={opt} value={opt}>{opt}</Option>
                        ))}
                    </Select>
                </div>
            ))}
        </div>
        <div className="config-filter-actions">
            <Button 
                icon={<CloseOutlined />} 
                onClick={() => setFilters({})}
            >
                Limpar Filtros
            </Button>
        </div>
    </div>
);

/**
 * Célula de percentual com cor visual
 */
const PercentCell = ({ value, onChange, readOnly = false }) => {
    const numValue = value !== undefined && value !== '' ? Number(value) : 0;
    
    // Determinar cor baseada no valor
    const getColor = (val) => {
        if (val === 0) return '#8c8c8c';
        if (val < 25) return '#faad14';
        if (val < 50) return '#1890ff';
        if (val < 75) return '#52c41a';
        return '#389e0d';
    };

    if (readOnly) {
        return (
            <div className="percent-cell" style={{ color: getColor(numValue) }}>
                {numValue.toFixed(1)}%
            </div>
        );
    }

    return (
        <InputNumber
            min={0}
            max={100}
            step={0.1}
            value={numValue}
            onChange={onChange}
            className="percent-input"
            formatter={(val) => `${val}%`}
            parser={(val) => val.replace('%', '')}
        />
    );
};

/**
 * Componente principal ConfigComissaoEditorV2
 */
const ConfigComissaoEditorV2 = () => {
    const [options, setOptions] = useState({});
    const [dynOptions, setDynOptions] = useState({});
    const [filters, setFilters] = useState({});
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState({ total: 0, avgTaxa: 0, validFatias: 0 });

    // Wizard state
    const [wizardOpen, setWizardOpen] = useState(false);
    const [wizardStep, setWizardStep] = useState(0);
    const [wizardMode, setWizardMode] = useState('taxa'); // 'taxa' ou 'fatias'
    const [wizardScope, setWizardScope] = useState({});
    const [wizardValue, setWizardValue] = useState(0);
    const [wizardFatias, setWizardFatias] = useState({});
    const [previewCount, setPreviewCount] = useState(null);

    // Validação modal
    const [validarOpen, setValidarOpen] = useState(false);
    const [validarContext, setValidarContext] = useState({});
    const [validarResult, setValidarResult] = useState(null);

    // Carregar opções iniciais
    useEffect(() => {
        const loadOptions = async () => {
            try {
                const resp = await regrasAPI.getRuleContextOptions();
                const base = resp.data || {};
                
                // Normalize options to remove duplicates and fix encoding issues
                const normalizedBase = {};
                Object.keys(base).forEach(key => {
                    if (Array.isArray(base[key])) {
                        const uniqueValues = new Set();
                        base[key].forEach(val => {
                            if (!val) return;
                            // Fix specific encoding issue for "Remediação"
                            let cleanVal = val;
                            if (typeof val === 'string') {
                                if (val.includes('Remediaç') && val.includes('o')) {
                                    cleanVal = 'Remediação';
                                }
                            }
                            uniqueValues.add(cleanVal);
                        });
                        normalizedBase[key] = Array.from(uniqueValues).sort();
                    } else {
                        normalizedBase[key] = base[key];
                    }
                });

                setOptions(normalizedBase);
                setDynOptions(normalizedBase);
            } catch (e) {
                message.error(`Erro ao carregar opções: ${e.message}`);
            }
        };
        loadOptions();
    }, []);

    // Atualizar opções dinâmicas com base nos filtros e buscar dados automaticamente
    useEffect(() => {
        const updateDynOptionsAndSearch = async () => {
            const partial = ['linha', 'tipo_mercadoria', 'grupo', 'subgrupo']
                .reduce((acc, k) => (filters[k] ? { ...acc, [k]: filters[k] } : acc), {});
            
            // Trigger search automatically
            buscar(partial);

            if (Object.keys(partial).length === 0) {
                setDynOptions(options);
                return;
            }

            try {
                const resp = await regrasAPI.getConfigComissao(partial);
                const arr = Array.isArray(resp.data) ? resp.data : [];
                const byCol = {};
                ['linha', 'tipo_mercadoria', 'grupo', 'subgrupo'].forEach((k) => {
                    const uniqueValues = new Set();
                    arr.forEach(r => {
                        const val = r[k];
                        if (!val) return;
                        let cleanVal = val;
                        if (typeof val === 'string') {
                            if (val.includes('Remediaç') && val.includes('o')) {
                                cleanVal = 'Remediação';
                            }
                        }
                        uniqueValues.add(cleanVal);
                    });
                    byCol[k] = Array.from(uniqueValues).sort();
                });
                byCol['cargo'] = options['cargo'] || [];
                setDynOptions(byCol);
            } catch {
                setDynOptions(options);
            }
        };
        updateDynOptionsAndSearch();
    }, [filters.linha, filters.tipo_mercadoria, filters.grupo, filters.subgrupo, options]);

    // Buscar dados
    const buscar = async (currentFilters = filters) => {
        setLoading(true);
        try {
            const resp = await regrasAPI.getConfigComissao(currentFilters);
            const arr = Array.isArray(resp.data) ? resp.data : [];
            setData(arr.map((row, idx) => ({ key: idx, ...row })));
            
            // Calcular estatísticas
            const totalTaxa = arr.reduce((sum, r) => sum + (Number(r.taxa_rateio_maximo_pct) || 0), 0);
            setStats({
                total: arr.length,
                avgTaxa: arr.length > 0 ? totalTaxa / arr.length : 0,
                validFatias: arr.filter(r => Number(r.fatia_cargo_pct) > 0).length
            });
        } catch (e) {
            message.error(`Erro ao buscar regras: ${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Atualizar célula inline
    const updateInline = async (row, field, value) => {
        try {
            const payload = { 
                ...CONTEXT_FIELDS.reduce((acc, k) => ({ ...acc, [k]: row[k] }), {}), 
                [field]: value 
            };
            await regrasAPI.updateConfigComissaoInLine(payload);
            message.success('Regra atualizada');
            setData((prev) => prev.map((r) => (r.key === row.key ? { ...r, [field]: value } : r)));
        } catch (e) {
            message.error(e.message || 'Falha ao atualizar');
        }
    };

    // Colunas da tabela
    const columns = useMemo(() => [
        { 
            title: 'Linha', 
            dataIndex: 'linha', 
            key: 'linha', 
            width: 120, 
            fixed: 'left',
            render: (val) => <Tag color="blue">{val}</Tag>
        },
        { title: 'Grupo', dataIndex: 'grupo', key: 'grupo', width: 140 },
        { title: 'Subgrupo', dataIndex: 'subgrupo', key: 'subgrupo', width: 140 },
        { title: 'Tipo Mercadoria', dataIndex: 'tipo_mercadoria', key: 'tipo_mercadoria', width: 150 },
        { 
            title: 'Cargo', 
            dataIndex: 'cargo', 
            key: 'cargo', 
            width: 120,
            render: (val) => <Tag color="purple">{val}</Tag>
        },
        {
            title: (
                <Tooltip title="Taxa máxima de rateio da comissão">
                    <Space>
                        Taxa Rateio Máx.
                        <InfoCircleOutlined />
                    </Space>
                </Tooltip>
            ),
            dataIndex: 'taxa_rateio_maximo_pct',
            key: 'taxa_rateio_maximo_pct',
            width: 160,
            align: 'right',
            render: (val, row) => (
                <PercentCell 
                    value={val} 
                    onChange={(v) => updateInline(row, 'taxa_rateio_maximo_pct', v)}
                />
            ),
        },
        {
            title: (
                <Tooltip title="Percentual da fatia de comissão para este cargo">
                    <Space>
                        Fatia Cargo
                        <InfoCircleOutlined />
                    </Space>
                </Tooltip>
            ),
            dataIndex: 'fatia_cargo_pct',
            key: 'fatia_cargo_pct',
            width: 140,
            align: 'right',
            render: (val, row) => (
                <PercentCell 
                    value={val} 
                    onChange={(v) => updateInline(row, 'fatia_cargo_pct', v)}
                />
            ),
        },
    ], []);

    // ==================== WIZARD LOGIC ====================
    const openWizard = (mode) => {
        setWizardMode(mode);
        setWizardOpen(true);
        setWizardStep(0);
        setWizardScope({});
        setWizardValue(0);
        setWizardFatias({});
        setPreviewCount(null);
    };

    const calcFatiasSum = () => {
        const cargos = options['cargo'] || [];
        return cargos.reduce((sum, c) => {
            const val = Number(wizardFatias[c]) || 0;
            return sum + val;
        }, 0);
    };

    const doPreview = async () => {
        try {
            if (wizardMode === 'taxa') {
                const batch = {
                    escopo: wizardScope,
                    acao: { taxa_rateio_maximo_pct: { valor: wizardValue } },
                };
                const resp = await regrasAPI.dryRunConfigComissao(batch);
                setPreviewCount(resp.data?.linhas_afetadas || 0);
            } else {
                // Fatias - contar linhas por cargo
                const cargosComValor = (options['cargo'] || []).filter(c => Number(wizardFatias[c]) > 0);
                let total = 0;
                for (const cargo of cargosComValor) {
                    const resp = await regrasAPI.getConfigComissao({ ...wizardScope, cargo });
                    total += Array.isArray(resp.data) ? resp.data.length : 0;
                }
                setPreviewCount(total);
            }
            setWizardStep(2);
        } catch (e) {
            message.error(e.message || 'Erro ao pré-visualizar');
        }
    };

    const applyWizard = async () => {
        try {
            if (wizardMode === 'taxa') {
                const batch = {
                    escopo: wizardScope,
                    acao: { taxa_rateio_maximo_pct: { valor: wizardValue } },
                };
                await regrasAPI.applyBatchConfigComissao(batch);
                message.success('Taxa de rateio aplicada com sucesso!');
            } else {
                const cargosComValor = (options['cargo'] || []).filter(c => Number(wizardFatias[c]) > 0);
                for (const cargo of cargosComValor) {
                    await regrasAPI.updateConfigComissaoInLine({ 
                        ...wizardScope, 
                        cargo, 
                        fatia_cargo_pct: wizardFatias[cargo] 
                    });
                }
                message.success('Fatias por cargo aplicadas com sucesso!');
            }
            setWizardOpen(false);
            buscar();
        } catch (e) {
            message.error(e.message || 'Falha ao aplicar alterações');
        }
    };

    // ==================== VALIDAÇÃO ====================
    const executarValidacao = async () => {
        try {
            const resp = await regrasAPI.validateConfigComissaoPE(validarContext);
            setValidarResult(resp.data);
        } catch (e) {
            message.error(e.message || 'Falha na validação');
        }
    };

    return (
        <div className="config-comissao-editor">
            {/* Header com estatísticas */}
            <Card className="config-stats-card">
                <Row gutter={24}>
                    <Col span={6}>
                        <Statistic 
                            title="Total de Regras"
                            value={stats.total}
                            prefix={<FilterOutlined />}
                        />
                    </Col>
                    <Col span={6}>
                        <Statistic 
                            title="Taxa Média"
                            value={stats.avgTaxa}
                            precision={1}
                            suffix="%"
                            prefix={<PercentageOutlined />}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Col>
                    <Col span={6}>
                        <Statistic 
                            title="Fatias Definidas"
                            value={stats.validFatias}
                            prefix={<TeamOutlined />}
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Col>
                    <Col span={6}>
                        <Space direction="vertical">
                            <Button 
                                type="primary" 
                                icon={<ThunderboltOutlined />}
                                onClick={() => openWizard('taxa')}
                            >
                                Aplicar Taxa em Lote
                            </Button>
                            <Button 
                                icon={<TeamOutlined />}
                                onClick={() => openWizard('fatias')}
                            >
                                Configurar Fatias PE
                            </Button>
                        </Space>
                    </Col>
                </Row>
            </Card>

            {/* Filtros */}
            <Card className="config-filter-card">
                <FilterSection 
                    options={Object.keys(dynOptions).length ? dynOptions : options}
                    filters={filters}
                    setFilters={setFilters}
                    loading={loading}
                />
            </Card>

            {/* Tabela de dados */}
            <Card 
                className="config-table-card"
                title={
                    <Space>
                        <span>Regras de Comissão</span>
                        {data.length > 0 && <Badge count={data.length} style={{ backgroundColor: '#1890ff' }} />}
                    </Space>
                }
                extra={
                    <Button 
                        icon={<CheckCircleOutlined />} 
                        onClick={() => setValidarOpen(true)}
                    >
                        Validar Soma (PE)
                    </Button>
                }
            >
                <Table
                    columns={columns}
                    dataSource={data}
                    loading={loading}
                    pagination={{ 
                        pageSize: 15,
                        showSizeChanger: true,
                        showTotal: (total) => `${total} regras`
                    }}
                    scroll={{ x: 'max-content' }}
                    size="small"
                    rowClassName={(row) => {
                        const fatia = Number(row.fatia_cargo_pct) || 0;
                        if (fatia === 0) return 'row-warning';
                        return '';
                    }}
                />
            </Card>

            {/* ==================== WIZARD MODAL ==================== */}
            <Modal
                title={
                    <Space>
                        {wizardMode === 'taxa' ? <PercentageOutlined /> : <TeamOutlined />}
                        {wizardMode === 'taxa' ? 'Aplicar Taxa de Rateio em Lote' : 'Configurar Fatias por Cargo (PE)'}
                    </Space>
                }
                open={wizardOpen}
                onCancel={() => setWizardOpen(false)}
                footer={null}
                width={700}
                destroyOnClose
            >
                <Steps 
                    current={wizardStep} 
                    className="wizard-steps"
                    items={[
                        { title: 'Escopo' },
                        { title: 'Valores' },
                        { title: 'Confirmar' }
                    ]}
                />

                <div className="wizard-content">
                    {/* Step 0: Escopo */}
                    {wizardStep === 0 && (
                        <div className="wizard-step">
                            <Title level={5}>Selecione o escopo de aplicação:</Title>
                            <div className="wizard-scope-grid">
                                {['linha', 'tipo_mercadoria', 'grupo', 'subgrupo'].map((field) => (
                                    <div key={field} className="wizard-scope-item">
                                        <label>{field}</label>
                                        <Select
                                            style={{ width: '100%' }}
                                            allowClear
                                            value={wizardScope[field]}
                                            onChange={(v) => setWizardScope(prev => ({ ...prev, [field]: v }))}
                                        >
                                            {(dynOptions[field] || options[field] || []).map((opt) => (
                                                <Option key={opt} value={opt}>{opt}</Option>
                                            ))}
                                        </Select>
                                    </div>
                                ))}
                            </div>
                            <Alert 
                                message="Deixe campos vazios para aplicar a todas as regras correspondentes" 
                                type="info" 
                                showIcon 
                                style={{ marginTop: 16 }}
                            />
                            <div className="wizard-actions">
                                <Button onClick={() => setWizardOpen(false)}>Cancelar</Button>
                                <Button type="primary" onClick={() => setWizardStep(1)}>Próximo</Button>
                            </div>
                        </div>
                    )}

                    {/* Step 1: Valores */}
                    {wizardStep === 1 && (
                        <div className="wizard-step">
                            {wizardMode === 'taxa' ? (
                                <>
                                    <Title level={5}>Defina a taxa de rateio máximo:</Title>
                                    <div className="wizard-value-input">
                                        <InputNumber
                                            min={0}
                                            max={100}
                                            step={0.1}
                                            value={wizardValue}
                                            onChange={(v) => setWizardValue(v || 0)}
                                            addonAfter="%"
                                            size="large"
                                            style={{ width: 200 }}
                                        />
                                    </div>
                                    <Progress 
                                        percent={wizardValue} 
                                        status="active"
                                        style={{ marginTop: 16 }}
                                    />
                                </>
                            ) : (
                                <>
                                    <Title level={5}>Defina as fatias por cargo:</Title>
                                    <Alert 
                                        message="A soma das fatias deve ser exatamente 100%" 
                                        type="warning" 
                                        showIcon 
                                        style={{ marginBottom: 16 }}
                                    />
                                    <div className="wizard-fatias-grid">
                                        {(options['cargo'] || []).map((cargo) => (
                                            <div key={cargo} className="wizard-fatia-item">
                                                <span className="wizard-fatia-label">{cargo}</span>
                                                <InputNumber
                                                    min={0}
                                                    max={100}
                                                    step={0.1}
                                                    value={wizardFatias[cargo] || 0}
                                                    onChange={(v) => setWizardFatias(prev => ({ ...prev, [cargo]: v || 0 }))}
                                                    addonAfter="%"
                                                />
                                            </div>
                                        ))}
                                    </div>
                                    <Divider />
                                    <div className="wizard-fatias-total">
                                        <Text>Soma das fatias: </Text>
                                        <Text 
                                            strong 
                                            style={{ 
                                                color: calcFatiasSum().toFixed(2) === '100.00' ? '#52c41a' : '#ff4d4f',
                                                fontSize: 18
                                            }}
                                        >
                                            {calcFatiasSum().toFixed(2)}%
                                        </Text>
                                        {calcFatiasSum().toFixed(2) === '100.00' && (
                                            <CheckCircleOutlined style={{ color: '#52c41a', marginLeft: 8 }} />
                                        )}
                                    </div>
                                </>
                            )}
                            <div className="wizard-actions">
                                <Button onClick={() => setWizardStep(0)}>Voltar</Button>
                                <Button 
                                    type="primary" 
                                    onClick={doPreview}
                                    disabled={wizardMode === 'fatias' && calcFatiasSum().toFixed(2) !== '100.00'}
                                >
                                    <EyeOutlined /> Pré-visualizar
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Confirmar */}
                    {wizardStep === 2 && (
                        <div className="wizard-step">
                            <Title level={5}>Confirme a aplicação:</Title>
                            <Alert
                                message={`${previewCount} regra(s) serão afetadas`}
                                type={previewCount > 0 ? 'success' : 'warning'}
                                showIcon
                                style={{ marginBottom: 16 }}
                            />
                            <div className="wizard-summary">
                                <div className="wizard-summary-item">
                                    <Text type="secondary">Escopo:</Text>
                                    <div>
                                        {Object.entries(wizardScope)
                                            .filter(([_, v]) => v)
                                            .map(([k, v]) => (
                                                <Tag key={k}>{k}: {v}</Tag>
                                            ))
                                        }
                                        {Object.keys(wizardScope).filter(k => wizardScope[k]).length === 0 && (
                                            <Tag>Todas as regras</Tag>
                                        )}
                                    </div>
                                </div>
                                <div className="wizard-summary-item">
                                    <Text type="secondary">
                                        {wizardMode === 'taxa' ? 'Taxa:' : 'Fatias:'}
                                    </Text>
                                    <div>
                                        {wizardMode === 'taxa' ? (
                                            <Tag color="blue">{wizardValue}%</Tag>
                                        ) : (
                                            Object.entries(wizardFatias)
                                                .filter(([_, v]) => v > 0)
                                                .map(([cargo, val]) => (
                                                    <Tag key={cargo} color="purple">{cargo}: {val}%</Tag>
                                                ))
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="wizard-actions">
                                <Button onClick={() => setWizardStep(1)}>Voltar</Button>
                                <Button 
                                    type="primary" 
                                    onClick={applyWizard}
                                    disabled={previewCount === 0}
                                >
                                    <CheckOutlined /> Aplicar Alterações
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </Modal>

            {/* ==================== VALIDAÇÃO MODAL ==================== */}
            <Modal
                title={<Space><CheckCircleOutlined /> Validar Soma das Fatias (PE)</Space>}
                open={validarOpen}
                onCancel={() => { setValidarOpen(false); setValidarResult(null); }}
                onOk={executarValidacao}
                okText="Validar"
            >
                <div className="validar-content">
                    <Text type="secondary">Selecione o contexto para validação:</Text>
                    <div className="validar-filters">
                        {['linha', 'grupo', 'subgrupo', 'tipo_mercadoria'].map((field) => (
                            <div key={field} className="validar-filter-item">
                                <label>{field}</label>
                                <Select
                                    style={{ width: '100%' }}
                                    allowClear
                                    value={validarContext[field]}
                                    onChange={(v) => setValidarContext(prev => ({ ...prev, [field]: v }))}
                                >
                                    {(options[field] || []).map((opt) => (
                                        <Option key={opt} value={opt}>{opt}</Option>
                                    ))}
                                </Select>
                            </div>
                        ))}
                    </div>
                    {validarResult && (
                        <Alert
                            message={validarResult.message}
                            type={validarResult.valid ? 'success' : 'error'}
                            showIcon
                            style={{ marginTop: 16 }}
                        />
                    )}
                </div>
            </Modal>
        </div>
    );
};

export default ConfigComissaoEditorV2;
