import React, { useState, useEffect, useCallback } from 'react';
import {
    Modal,
    Form,
    Steps,
    Select,
    InputNumber,
    Button,
    Table,
    Space,
    message,
    Alert,
    Typography,
    Statistic,
    Row,
    Col,
    Divider,
    Tag,
} from 'antd';
import {
    AimOutlined,
    ThunderboltOutlined,
    EyeOutlined,
    CheckCircleOutlined,
} from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const { Step } = Steps;
const { Option } = Select;
const { Text } = Typography;

/**
 * Modal especializado para aplicar metas de faturamento/conversão em massa
 * usando a hierarquia de produtos como fonte de combinações válidas.
 */
const MetasAplicacaoBulkModal = ({ open, onCancel, onSuccess }) => {
    const [form] = Form.useForm();
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);

    // Opções dos dropdowns
    const [allOptions, setAllOptions] = useState({
        linhas: [],
        grupos: [],
        subgrupos: [],
        tipos_mercadoria: [],
    });
    const [filteredOptions, setFilteredOptions] = useState({
        linhas: [],
        grupos: [],
        subgrupos: [],
        tipos_mercadoria: [],
    });

    // Estado do escopo selecionado
    const [escopo, setEscopo] = useState({
        linha: null,
        grupo: null,
        subgrupo: null,
        tipo_mercadoria: null,
    });

    // Combinações encontradas e preview
    const [combinacoes, setCombinacoes] = useState([]);
    const [previewData, setPreviewData] = useState([]);

    const resetState = useCallback(() => {
        setCurrentStep(0);
        setEscopo({ linha: null, grupo: null, subgrupo: null, tipo_mercadoria: null });
        setCombinacoes([]);
        setPreviewData([]);
        form.resetFields();
    }, [form]);

    // Carregar opções iniciais ao abrir o modal
    useEffect(() => {
        if (open) {
            loadInitialOptions();
            resetState();
        }
    }, [open, resetState]);

    const loadInitialOptions = async () => {
        try {
            setLoading(true);
            const response = await regrasAPI.metasAplicacaoHierarchyOptions();
            const options = response.data;
            setAllOptions(options);
            setFilteredOptions(options);
        } catch (error) {
            message.error('Erro ao carregar opções da hierarquia');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    // Atualizar opções filtradas quando o escopo muda (cascata)
    const updateFilteredOptions = useCallback(async (newEscopo) => {
        try {
            const response = await regrasAPI.metasAplicacaoFilteredOptions(newEscopo);
            setFilteredOptions(response.data);
        } catch (error) {
            console.error('Erro ao filtrar opções:', error);
        }
    }, []);

    // Handler para mudança de seleção
    const handleEscopoChange = async (field, value) => {
        const newEscopo = { ...escopo };

        // Limpar campos dependentes
        if (field === 'linha') {
            newEscopo.linha = value;
            newEscopo.grupo = null;
            newEscopo.subgrupo = null;
            newEscopo.tipo_mercadoria = null;
        } else if (field === 'grupo') {
            newEscopo.grupo = value;
            newEscopo.subgrupo = null;
            newEscopo.tipo_mercadoria = null;
        } else if (field === 'subgrupo') {
            newEscopo.subgrupo = value;
            newEscopo.tipo_mercadoria = null;
        } else {
            newEscopo.tipo_mercadoria = value;
        }

        setEscopo(newEscopo);
        await updateFilteredOptions(newEscopo);
        await loadCombinacoes(newEscopo);
    };

    // Carregar combinações baseadas no escopo
    const loadCombinacoes = async (currentEscopo) => {
        if (!currentEscopo.linha) {
            setCombinacoes([]);
            return;
        }

        try {
            const response = await regrasAPI.metasAplicacaoHierarchyCombinations(currentEscopo);
            setCombinacoes(response.data.combinacoes || []);
        } catch (error) {
            console.error('Erro ao carregar combinações:', error);
            setCombinacoes([]);
        }
    };

    // Gerar preview
    const handleGeneratePreview = async () => {
        try {
            await form.validateFields(['tipo_meta', 'valor_meta']);
            const values = form.getFieldsValue();

            const preview = combinacoes.map((comb, idx) => ({
                key: idx,
                ...comb,
                tipo_meta: values.tipo_meta,
                valor_meta: values.valor_meta,
            }));

            setPreviewData(preview);
            setCurrentStep(2);
        } catch (error) {
            message.error('Preencha todos os campos obrigatórios');
        }
    };

    // Aplicar metas
    const handleApply = async () => {
        try {
            setLoading(true);
            const values = form.getFieldsValue();

            const response = await regrasAPI.metasAplicacaoBulkApply({
                combinacoes: combinacoes,
                tipo_meta: values.tipo_meta,
                valor_meta: values.valor_meta,
            });

            const result = response.data;
            message.success(
                `Metas aplicadas com sucesso! Criados: ${result.criados}, Atualizados: ${result.atualizados}`
            );
            onSuccess?.();
        } catch (error) {
            message.error(`Erro ao aplicar metas: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Colunas da tabela de preview
    const previewColumns = [
        { title: 'Linha', dataIndex: 'linha', key: 'linha', width: 120 },
        { title: 'Grupo', dataIndex: 'grupo', key: 'grupo', width: 150 },
        { title: 'Subgrupo', dataIndex: 'subgrupo', key: 'subgrupo', width: 150 },
        { title: 'Tipo Mercadoria', dataIndex: 'tipo_mercadoria', key: 'tipo_mercadoria', width: 130 },
        {
            title: 'Tipo Meta',
            dataIndex: 'tipo_meta',
            key: 'tipo_meta',
            width: 100,
            render: (val) => (
                <Tag color={val === 'faturamento' ? 'blue' : 'green'}>
                    {val === 'faturamento' ? 'Faturamento' : 'Conversão'}
                </Tag>
            ),
        },
        {
            title: 'Valor Meta',
            dataIndex: 'valor_meta',
            key: 'valor_meta',
            width: 120,
            render: (val) =>
                new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: 'BRL',
                }).format(val),
        },
    ];

    // Renderizar step atual
    const renderStepContent = () => {
        switch (currentStep) {
            case 0:
                return renderEscopoStep();
            case 1:
                return renderMetaStep();
            case 2:
                return renderPreviewStep();
            default:
                return null;
        }
    };

    // Step 1: Escopo Hierárquico
    const renderEscopoStep = () => (
        <div className="bulk-step-content">
            <Alert
                message="Selecione o escopo hierárquico"
                description="Escolha a linha (obrigatório) e opcionalmente refine por grupo, subgrupo e tipo de mercadoria. Quanto mais específico, menos combinações serão afetadas."
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
            />

            <Row gutter={16}>
                <Col span={12}>
                    <Form.Item label="Linha *" required>
                        <Select
                            placeholder="Selecione a linha"
                            value={escopo.linha}
                            onChange={(val) => handleEscopoChange('linha', val)}
                            showSearch
                            allowClear
                            filterOption={(input, option) =>
                                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {allOptions.linhas.map((linha) => (
                                <Option key={linha} value={linha}>
                                    {linha}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Col>
                <Col span={12}>
                    <Form.Item label="Grupo">
                        <Select
                            placeholder="Todos os grupos"
                            value={escopo.grupo}
                            onChange={(val) => handleEscopoChange('grupo', val)}
                            showSearch
                            allowClear
                            disabled={!escopo.linha}
                            filterOption={(input, option) =>
                                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {filteredOptions.grupos.map((grupo) => (
                                <Option key={grupo} value={grupo}>
                                    {grupo}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Col>
            </Row>

            <Row gutter={16}>
                <Col span={12}>
                    <Form.Item label="Subgrupo">
                        <Select
                            placeholder="Todos os subgrupos"
                            value={escopo.subgrupo}
                            onChange={(val) => handleEscopoChange('subgrupo', val)}
                            showSearch
                            allowClear
                            disabled={!escopo.grupo}
                            filterOption={(input, option) =>
                                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {filteredOptions.subgrupos.map((subgrupo) => (
                                <Option key={subgrupo} value={subgrupo}>
                                    {subgrupo}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Col>
                <Col span={12}>
                    <Form.Item label="Tipo de Mercadoria">
                        <Select
                            placeholder="Todos os tipos"
                            value={escopo.tipo_mercadoria}
                            onChange={(val) => handleEscopoChange('tipo_mercadoria', val)}
                            showSearch
                            allowClear
                            disabled={!escopo.linha}
                            filterOption={(input, option) =>
                                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {filteredOptions.tipos_mercadoria.map((tipo) => (
                                <Option key={tipo} value={tipo}>
                                    {tipo}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Col>
            </Row>

            <Divider />

            <Row justify="center">
                <Col>
                    <Statistic
                        title="Combinações encontradas na Hierarquia"
                        value={combinacoes.length}
                        prefix={<AimOutlined />}
                        valueStyle={{
                            color: combinacoes.length > 0 ? '#1890ff' : '#999',
                            fontSize: 32,
                        }}
                    />
                </Col>
            </Row>

            {combinacoes.length > 0 && combinacoes.length <= 10 && (
                <div style={{ marginTop: 16 }}>
                    <Text type="secondary">Combinações:</Text>
                    <div style={{ maxHeight: 150, overflowY: 'auto', marginTop: 8 }}>
                        {combinacoes.map((c, idx) => (
                            <Tag key={idx} style={{ marginBottom: 4 }}>
                                {c.linha} → {c.grupo} → {c.subgrupo} → {c.tipo_mercadoria}
                            </Tag>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    // Step 2: Definir Meta
    const renderMetaStep = () => (
        <div className="bulk-step-content">
            <Alert
                message={`Definir meta para ${combinacoes.length} combinações`}
                description="Escolha o tipo de meta e o valor que será aplicado a todas as combinações selecionadas."
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
            />

            <Row gutter={24}>
                <Col span={12}>
                    <Form.Item
                        name="tipo_meta"
                        label="Tipo de Meta"
                        rules={[{ required: true, message: 'Selecione o tipo de meta' }]}
                    >
                        <Select placeholder="Selecione o tipo">
                            <Option value="faturamento">
                                <Space>
                                    <Tag color="blue">$</Tag>
                                    Faturamento
                                </Space>
                            </Option>
                            <Option value="conversao">
                                <Space>
                                    <Tag color="green">%</Tag>
                                    Conversão
                                </Space>
                            </Option>
                        </Select>
                    </Form.Item>
                </Col>
                <Col span={12}>
                    <Form.Item
                        name="valor_meta"
                        label="Valor da Meta (R$)"
                        rules={[
                            { required: true, message: 'Informe o valor da meta' },
                            { type: 'number', min: 0, message: 'Valor deve ser positivo' },
                        ]}
                    >
                        <InputNumber
                            style={{ width: '100%' }}
                            placeholder="Ex: 500000"
                            formatter={(value) =>
                                `R$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
                            }
                            parser={(value) => value.replace(/R\$\s?|(\.)/g, '').replace(',', '.')}
                            min={0}
                            step={1000}
                        />
                    </Form.Item>
                </Col>
            </Row>

            <Divider />

            <Row justify="center" gutter={24}>
                <Col>
                    <Statistic
                        title="Combinações"
                        value={combinacoes.length}
                        prefix={<AimOutlined />}
                    />
                </Col>
            </Row>
        </div>
    );

    // Step 3: Preview
    const renderPreviewStep = () => (
        <div className="bulk-step-content">
            <Alert
                message="Confirme as alterações"
                description={`${previewData.length} registros serão criados ou atualizados na aba METAS_APLICACAO.`}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
            />

            <Table
                dataSource={previewData}
                columns={previewColumns}
                pagination={{ pageSize: 10, showSizeChanger: true }}
                size="small"
                scroll={{ y: 300 }}
            />

            <Divider />

            <Row justify="center" gutter={24}>
                <Col>
                    <Statistic
                        title="Total de Registros"
                        value={previewData.length}
                        prefix={<CheckCircleOutlined />}
                        valueStyle={{ color: '#52c41a' }}
                    />
                </Col>
            </Row>
        </div>
    );

    // Navegação entre steps
    const canGoNext = () => {
        if (currentStep === 0) return escopo.linha && combinacoes.length > 0;
        if (currentStep === 1) return true;
        return false;
    };

    return (
        <Modal
            title={
                <Space>
                    <ThunderboltOutlined />
                    Aplicar Metas de Aplicação em Massa
                </Space>
            }
            open={open}
            onCancel={onCancel}
            width={900}
            footer={null}
            destroyOnClose
        >
            <Form form={form} layout="vertical">
                <Steps current={currentStep} style={{ marginBottom: 24 }}>
                    <Step title="Escopo" description="Hierarquia" icon={<AimOutlined />} />
                    <Step title="Meta" description="Tipo e valor" icon={<ThunderboltOutlined />} />
                    <Step title="Preview" description="Confirmar" icon={<EyeOutlined />} />
                </Steps>

                {renderStepContent()}

                <Divider />

                <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                    {currentStep > 0 && (
                        <Button onClick={() => setCurrentStep(currentStep - 1)}>
                            Anterior
                        </Button>
                    )}
                    {currentStep === 0 && (
                        <Button
                            type="primary"
                            onClick={() => setCurrentStep(1)}
                            disabled={!canGoNext()}
                        >
                            Próximo
                        </Button>
                    )}
                    {currentStep === 1 && (
                        <Button
                            type="primary"
                            onClick={handleGeneratePreview}
                            icon={<EyeOutlined />}
                        >
                            Gerar Preview
                        </Button>
                    )}
                    {currentStep === 2 && (
                        <Button
                            type="primary"
                            onClick={handleApply}
                            loading={loading}
                            icon={<CheckCircleOutlined />}
                        >
                            Confirmar e Aplicar
                        </Button>
                    )}
                </Space>
            </Form>
        </Modal>
    );
};

export default MetasAplicacaoBulkModal;
