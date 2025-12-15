import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { 
    Card, 
    Tabs, 
    Space, 
    Tag, 
    Typography, 
    Statistic,
    Row,
    Col,
    message
} from 'antd';
import { 
    DollarOutlined, 
    PercentageOutlined,
    TeamOutlined,
    ShopOutlined,
    AimOutlined,
    BankOutlined
} from '@ant-design/icons';
import SmartTable from './SmartTable';
import { regrasAPI } from '../services/api';
import './MetasEditor.css';

const { Text } = Typography;

/**
 * Configuração das abas de metas com schemas inteligentes
 */
const SHEETS_CONFIG = {
    METAS_APLICACAO: {
        label: 'Metas de Aplicação',
        icon: <AimOutlined />,
        description: 'Metas de faturamento por linha e tipo de mercadoria',
        contextCols: ['linha', 'tipo_mercadoria'],
        schema: {
            linha: { label: 'Linha', type: 'text', width: 120 },
            tipo_mercadoria: { label: 'Tipo Mercadoria', type: 'text', width: 150 },
            meta_anual: { label: 'Meta Anual', type: 'money', width: 130 },
            meta_jan: { label: 'Jan', type: 'money', width: 100 },
            meta_fev: { label: 'Fev', type: 'money', width: 100 },
            meta_mar: { label: 'Mar', type: 'money', width: 100 },
            meta_abr: { label: 'Abr', type: 'money', width: 100 },
            meta_mai: { label: 'Mai', type: 'money', width: 100 },
            meta_jun: { label: 'Jun', type: 'money', width: 100 },
            meta_jul: { label: 'Jul', type: 'money', width: 100 },
            meta_ago: { label: 'Ago', type: 'money', width: 100 },
            meta_set: { label: 'Set', type: 'money', width: 100 },
            meta_out: { label: 'Out', type: 'money', width: 100 },
            meta_nov: { label: 'Nov', type: 'money', width: 100 },
            meta_dez: { label: 'Dez', type: 'money', width: 100 },
        }
    },
    METAS_INDIVIDUAIS: {
        label: 'Metas Individuais',
        icon: <TeamOutlined />,
        description: 'Metas de performance individual por colaborador',
        contextCols: ['nome_colaborador'],
        schema: {
            nome_colaborador: { label: 'Colaborador', type: 'text', width: 180 },
            meta_conversao_pct: { label: 'Meta Conversão', type: 'percent', width: 120 },
            meta_retencao_pct: { label: 'Meta Retenção', type: 'percent', width: 120 },
            meta_faturamento: { label: 'Meta Faturamento', type: 'money', width: 140 },
        }
    },
    META_RENTABILIDADE: {
        label: 'Metas de Rentabilidade',
        icon: <PercentageOutlined />,
        description: 'Metas de rentabilidade por hierarquia de produto',
        contextCols: ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria'],
        schema: {
            linha: { label: 'Linha', type: 'text', width: 100 },
            grupo: { label: 'Grupo', type: 'text', width: 120 },
            subgrupo: { label: 'Subgrupo', type: 'text', width: 120 },
            tipo_mercadoria: { label: 'Tipo Mercadoria', type: 'text', width: 140 },
            meta_rentabilidade_pct: { label: 'Meta Rent. %', type: 'percent', width: 120 },
            piso_rentabilidade_pct: { label: 'Piso Rent. %', type: 'percent', width: 120 },
            teto_rentabilidade_pct: { label: 'Teto Rent. %', type: 'percent', width: 120 },
        }
    },
    METAS_FORNECEDORES: {
        label: 'Metas de Fornecedores',
        icon: <ShopOutlined />,
        description: 'Metas de compra por fornecedor',
        contextCols: ['linha', 'fornecedor', 'moeda'],
        schema: {
            linha: { label: 'Linha', type: 'text', width: 100 },
            fornecedor: { label: 'Fornecedor', type: 'text', width: 180 },
            moeda: { label: 'Moeda', type: 'tag', width: 80 },
            meta_anual: { label: 'Meta Anual', type: 'money', width: 130 },
            meta_trimestre_1: { label: 'Q1', type: 'money', width: 110 },
            meta_trimestre_2: { label: 'Q2', type: 'money', width: 110 },
            meta_trimestre_3: { label: 'Q3', type: 'money', width: 110 },
            meta_trimestre_4: { label: 'Q4', type: 'money', width: 110 },
        }
    }
};

/**
 * Componente para exibir estatísticas resumidas de uma aba de metas
 */
const MetasStats = ({ sheetKey, config }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadStats = async () => {
            setLoading(true);
            try {
                const resp = await regrasAPI.lerAba(sheetKey, { allPages: true });
                const data = resp.data?.data || [];
                
                const result = {
                    totalRows: data.length,
                    totalMoney: 0,
                    avgPercent: 0,
                    uniqueGroups: new Set()
                };

                let percentSum = 0;
                let percentCount = 0;

                data.forEach(row => {
                    Object.entries(row).forEach(([key, value]) => {
                        if (key.includes('meta_') && !key.includes('_pct')) {
                            const num = parseFloat(value);
                            if (!isNaN(num)) {
                                result.totalMoney += num;
                            }
                        }
                        if (key.includes('_pct')) {
                            const num = parseFloat(value);
                            if (!isNaN(num)) {
                                percentSum += num;
                                percentCount++;
                            }
                        }
                    });

                    // Unique groups
                    if (row.linha) result.uniqueGroups.add(row.linha);
                    if (row.nome_colaborador) result.uniqueGroups.add(row.nome_colaborador);
                    if (row.fornecedor) result.uniqueGroups.add(row.fornecedor);
                });

                result.avgPercent = percentCount > 0 ? percentSum / percentCount : 0;
                result.uniqueGroupsCount = result.uniqueGroups.size;

                setStats(result);
            } catch (e) {
                console.error('Erro ao carregar estatísticas:', e);
            } finally {
                setLoading(false);
            }
        };
        loadStats();
    }, [sheetKey]);

    if (loading || !stats) return null;

    const formatMoney = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    };

    return (
        <Row gutter={16} className="metas-stats">
            <Col>
                <Statistic 
                    title="Registros" 
                    value={stats.totalRows} 
                    prefix={<AimOutlined />}
                />
            </Col>
            {stats.totalMoney > 0 && (
                <Col>
                    <Statistic 
                        title="Total Metas" 
                        value={formatMoney(stats.totalMoney)}
                        prefix={<DollarOutlined />}
                        valueStyle={{ color: '#1890ff' }}
                    />
                </Col>
            )}
            {stats.avgPercent > 0 && (
                <Col>
                    <Statistic 
                        title="Média %" 
                        value={stats.avgPercent}
                        precision={1}
                        suffix="%"
                        prefix={<PercentageOutlined />}
                        valueStyle={{ color: '#52c41a' }}
                    />
                </Col>
            )}
            {stats.uniqueGroupsCount > 0 && (
                <Col>
                    <Statistic 
                        title="Grupos únicos" 
                        value={stats.uniqueGroupsCount}
                        prefix={<BankOutlined />}
                    />
                </Col>
            )}
        </Row>
    );
};

/**
 * Editor genérico de aba de metas usando SmartTable
 */
const MetasSheetEditor = ({ sheetKey, config }) => {
    // API adapter para SmartTable
    const apiAdapter = useMemo(() => ({
        read: (id, params) => regrasAPI.lerAba(id, params),
        save: (id, data) => regrasAPI.salvarAba(id, data, true),
    }), []);

    return (
        <div className="metas-sheet-editor">
            <div className="metas-sheet-header">
                <div className="metas-sheet-info">
                    <Text type="secondary">{config.description}</Text>
                </div>
                <MetasStats sheetKey={sheetKey} config={config} />
            </div>
            
            <SmartTable
                resourceId={sheetKey}
                apiService={apiAdapter}
                schema={config.schema}
                title={config.label}
            />
        </div>
    );
};

/**
 * MetasEditorV2 - Editor de metas com formatação inteligente
 * 
 * Melhorias:
 * - Formatação automática de valores monetários (R$)
 * - Formatação de percentuais (%)
 * - Estatísticas resumidas por aba
 * - Modo leitura/edição
 */
const MetasEditorV2 = () => {
    const items = Object.entries(SHEETS_CONFIG).map(([key, config]) => ({
        key,
        label: (
            <Space>
                {config.icon}
                {config.label}
            </Space>
        ),
        children: <MetasSheetEditor sheetKey={key} config={config} />,
    }));

    return (
        <Card className="metas-editor-card">
            <Tabs 
                items={items} 
                type="card"
                className="metas-tabs"
            />
        </Card>
    );
};

export default MetasEditorV2;
