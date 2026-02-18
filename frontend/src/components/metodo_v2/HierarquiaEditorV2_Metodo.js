import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { 
    Card, 
    Collapse, 
    Space, 
    Button, 
    Input, 
    message, 
    Tag, 
    Tooltip, 
    Badge,
    Empty,
    Spin,
    Typography,
    Popconfirm
} from 'antd';
import { 
    ReloadOutlined, 
    SaveOutlined, 
    PlusOutlined, 
    DeleteOutlined,
    FolderOutlined,
    FileOutlined,
    EditOutlined,
    CheckOutlined,
    CloseOutlined,
    ExpandAltOutlined,
    ShrinkOutlined,
    SearchOutlined
} from '@ant-design/icons';
import { metodoV2API } from '../../services/api';
import '../HierarquiaEditor.css';

const { Panel } = Collapse;
const { Text } = Typography;

/**
 * HierarquiaEditorV2_Metodo - Editor de hierarquia para o Método V2
 * Cópia adaptada do HierarquiaEditorV2, usando API do Método V2
 * Agrupa por: linha → grupo → subgrupo → tipo_mercadoria
 */
const HierarquiaEditorV2_Metodo = () => {
    const [rawData, setRawData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedKeys, setExpandedKeys] = useState([]);
    const [editingItem, setEditingItem] = useState(null);
    const [editValues, setEditValues] = useState({});
    const [modifiedItems, setModifiedItems] = useState(new Set());

    // Carregar dados da API V2
    const carregar = useCallback(async () => {
        setLoading(true);
        try {
            const resp = await metodoV2API.lerAba('HIERARQUIA_V2', { allPages: true });
            const arr = resp.data?.data || [];
            setRawData(arr.map((row, idx) => ({ 
                __id: `item_${idx}`, 
                ...row 
            })));
            setModifiedItems(new Set());
        } catch (e) {
            message.error(`Erro ao carregar HIERARQUIA_V2: ${e.message}`);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { 
        carregar(); 
    }, [carregar]);

    // Construir estrutura hierárquica (árvore)
    const hierarchyTree = useMemo(() => {
        const tree = {};
        const filteredData = searchTerm 
            ? rawData.filter(item => 
                Object.values(item).some(v => 
                    String(v || '').toLowerCase().includes(searchTerm.toLowerCase())
                )
              )
            : rawData;

        filteredData.forEach(item => {
            const linha = item.linha || '(Sem Linha)';
            const grupo = item.grupo || '(Sem Grupo)';
            const subgrupo = item.subgrupo || '(Sem Subgrupo)';
            const tipo = item.tipo_mercadoria || '(Sem Tipo)';

            if (!tree[linha]) {
                tree[linha] = { grupos: {}, count: 0 };
            }
            if (!tree[linha].grupos[grupo]) {
                tree[linha].grupos[grupo] = { subgrupos: {}, count: 0 };
            }
            if (!tree[linha].grupos[grupo].subgrupos[subgrupo]) {
                tree[linha].grupos[grupo].subgrupos[subgrupo] = { tipos: [], count: 0 };
            }
            
            tree[linha].grupos[grupo].subgrupos[subgrupo].tipos.push({
                ...item,
                tipo_mercadoria: tipo
            });
            tree[linha].grupos[grupo].subgrupos[subgrupo].count++;
            tree[linha].grupos[grupo].count++;
            tree[linha].count++;
        });

        return tree;
    }, [rawData, searchTerm]);

    // Gerar todas as chaves para expandir/colapsar
    const allKeys = useMemo(() => {
        const keys = [];
        Object.keys(hierarchyTree).forEach(linha => {
            keys.push(`linha_${linha}`);
            Object.keys(hierarchyTree[linha].grupos).forEach(grupo => {
                keys.push(`grupo_${linha}_${grupo}`);
                Object.keys(hierarchyTree[linha].grupos[grupo].subgrupos).forEach(subgrupo => {
                    keys.push(`subgrupo_${linha}_${grupo}_${subgrupo}`);
                });
            });
        });
        return keys;
    }, [hierarchyTree]);

    const expandAll = () => setExpandedKeys(allKeys);
    const collapseAll = () => setExpandedKeys([]);

    // Iniciar edição de um item
    const startEdit = (item) => {
        setEditingItem(item.__id);
        setEditValues({
            linha: item.linha || '',
            grupo: item.grupo || '',
            subgrupo: item.subgrupo || '',
            tipo_mercadoria: item.tipo_mercadoria || '',
            fabricante: item.fabricante || ''
        });
    };

    // Salvar edição de um item
    const saveEdit = (itemId) => {
        setRawData(prev => prev.map(item => {
            if (item.__id === itemId) {
                return { ...item, ...editValues };
            }
            return item;
        }));
        setModifiedItems(prev => new Set([...prev, itemId]));
        setEditingItem(null);
        setEditValues({});
    };

    // Cancelar edição
    const cancelEdit = () => {
        setEditingItem(null);
        setEditValues({});
    };

    // Excluir item
    const deleteItem = (itemId) => {
        setRawData(prev => prev.filter(item => item.__id !== itemId));
        setModifiedItems(prev => {
            const newSet = new Set(prev);
            newSet.delete(itemId);
            return newSet;
        });
    };

    // Adicionar novo item
    const addItem = (template = {}) => {
        const newId = `new_${Date.now()}`;
        const newItem = {
            __id: newId,
            linha: template.linha || '',
            grupo: template.grupo || '',
            subgrupo: template.subgrupo || '',
            tipo_mercadoria: '',
            fabricante: ''
        };
        setRawData(prev => [...prev, newItem]);
        setModifiedItems(prev => new Set([...prev, newId]));
        setEditingItem(newId);
        setEditValues(newItem);
    };

    // Validações
    const validateData = () => {
        const seen = new Set();
        for (const item of rawData) {
            const linha = String(item.linha || '').trim();
            const tipo = String(item.tipo_mercadoria || '').trim();
            
            if (!linha || !tipo) {
                message.error('Preencha ao menos "linha" e "tipo_mercadoria" em todos os itens.');
                return false;
            }

            const tuple = [
                item.linha,
                item.grupo,
                item.subgrupo,
                item.tipo_mercadoria,
                item.fabricante
            ].map(v => String(v || '').trim()).join('||');
            
            if (seen.has(tuple)) {
                message.error(`Duplicidade encontrada: ${tuple.replace(/\|\|/g, ' → ')}`);
                return false;
            }
            seen.add(tuple);
        }
        return true;
    };

    // Salvar todos os dados
    const salvar = async () => {
        if (!validateData()) return;
        
        setSaving(true);
        try {
            const payload = rawData.map(({ __id, ...rest }) => rest);
            await metodoV2API.salvarAba('HIERARQUIA_V2', payload, true);
            message.success('HIERARQUIA_V2 salva com sucesso!');
            setModifiedItems(new Set());
            await carregar();
        } catch (e) {
            message.error(e.message || 'Falha ao salvar HIERARQUIA_V2');
        } finally {
            setSaving(false);
        }
    };

    // Renderizar um item tipo_mercadoria (folha da árvore)
    const renderTipoItem = (item) => {
        const isEditing = editingItem === item.__id;
        const isModified = modifiedItems.has(item.__id);

        if (isEditing) {
            return (
                <div className="hierarquia-item hierarquia-item-editing">
                    <div className="hierarquia-item-fields">
                        <Input
                            size="small"
                            placeholder="Linha"
                            value={editValues.linha}
                            onChange={e => setEditValues(prev => ({ ...prev, linha: e.target.value }))}
                            style={{ width: 120 }}
                        />
                        <Input
                            size="small"
                            placeholder="Grupo"
                            value={editValues.grupo}
                            onChange={e => setEditValues(prev => ({ ...prev, grupo: e.target.value }))}
                            style={{ width: 120 }}
                        />
                        <Input
                            size="small"
                            placeholder="Subgrupo"
                            value={editValues.subgrupo}
                            onChange={e => setEditValues(prev => ({ ...prev, subgrupo: e.target.value }))}
                            style={{ width: 120 }}
                        />
                        <Input
                            size="small"
                            placeholder="Tipo Mercadoria"
                            value={editValues.tipo_mercadoria}
                            onChange={e => setEditValues(prev => ({ ...prev, tipo_mercadoria: e.target.value }))}
                            style={{ width: 130 }}
                        />
                        <Input
                            size="small"
                            placeholder="Fabricante"
                            value={editValues.fabricante}
                            onChange={e => setEditValues(prev => ({ ...prev, fabricante: e.target.value }))}
                            style={{ width: 120 }}
                        />
                    </div>
                    <Space className="hierarquia-item-actions">
                        <Button 
                            type="primary" 
                            size="small" 
                            icon={<CheckOutlined />}
                            onClick={() => saveEdit(item.__id)}
                        />
                        <Button 
                            size="small" 
                            icon={<CloseOutlined />}
                            onClick={cancelEdit}
                        />
                    </Space>
                </div>
            );
        }

        return (
            <div className={`hierarquia-item ${isModified ? 'hierarquia-item-modified' : ''}`}>
                <div className="hierarquia-item-content">
                    <FileOutlined className="hierarquia-item-icon" />
                    <Text className="hierarquia-item-text">
                        {item.tipo_mercadoria}
                        {item.fabricante && <Tag size="small" style={{ marginLeft: 8 }}>{item.fabricante}</Tag>}
                    </Text>
                    {isModified && <Tag color="orange" size="small">Modificado</Tag>}
                </div>
                <Space className="hierarquia-item-actions">
                    <Tooltip title="Editar">
                        <Button 
                            type="text" 
                            size="small" 
                            icon={<EditOutlined />}
                            onClick={() => startEdit(item)}
                        />
                    </Tooltip>
                    <Popconfirm
                        title="Excluir este item?"
                        onConfirm={() => deleteItem(item.__id)}
                        okText="Sim"
                        cancelText="Não"
                    >
                        <Tooltip title="Excluir">
                            <Button 
                                type="text" 
                                size="small" 
                                danger
                                icon={<DeleteOutlined />}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            </div>
        );
    };

    // Renderizar header do painel com contagem
    const renderPanelHeader = (label, count, level = 1) => {
        const icons = {
            1: <FolderOutlined style={{ color: '#722ed1' }} />,
            2: <FolderOutlined style={{ color: '#13c2c2' }} />,
            3: <FolderOutlined style={{ color: '#fa8c16' }} />
        };

        const colors = {
            1: '#722ed1',
            2: '#13c2c2',
            3: '#fa8c16'
        };

        return (
            <div className="hierarquia-panel-header">
                {icons[level]}
                <span className="hierarquia-panel-label">{label}</span>
                <Badge 
                    count={count} 
                    style={{ backgroundColor: colors[level] }}
                    size="small"
                />
            </div>
        );
    };

    // Estatísticas
    const stats = useMemo(() => {
        const linhas = Object.keys(hierarchyTree).length;
        let grupos = 0;
        let subgrupos = 0;
        Object.values(hierarchyTree).forEach(l => {
            grupos += Object.keys(l.grupos).length;
            Object.values(l.grupos).forEach(g => {
                subgrupos += Object.keys(g.subgrupos).length;
            });
        });
        return { linhas, grupos, subgrupos, tipos: rawData.length };
    }, [hierarchyTree, rawData]);

    return (
        <Card
            title={
                <Space>
                    <span>Hierarquia de Produtos V2</span>
                    <Tag color="purple">{stats.linhas} linhas</Tag>
                    <Tag color="cyan">{stats.grupos} grupos</Tag>
                    <Tag color="orange">{stats.subgrupos} subgrupos</Tag>
                    <Tag color="default">{stats.tipos} tipos</Tag>
                </Space>
            }
            className="hierarquia-card"
            extra={
                <Space>
                    <Input
                        placeholder="Buscar..."
                        prefix={<SearchOutlined />}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        style={{ width: 200 }}
                        allowClear
                    />
                    <Tooltip title="Expandir Tudo">
                        <Button icon={<ExpandAltOutlined />} onClick={expandAll} />
                    </Tooltip>
                    <Tooltip title="Colapsar Tudo">
                        <Button icon={<ShrinkOutlined />} onClick={collapseAll} />
                    </Tooltip>
                    <Button icon={<PlusOutlined />} onClick={() => addItem()}>
                        Novo
                    </Button>
                    <Button icon={<ReloadOutlined />} onClick={carregar} loading={loading}>
                        Recarregar
                    </Button>
                    <Button 
                        type="primary" 
                        icon={<SaveOutlined />} 
                        onClick={salvar} 
                        loading={saving}
                        disabled={modifiedItems.size === 0}
                    >
                        Salvar {modifiedItems.size > 0 && `(${modifiedItems.size})`}
                    </Button>
                </Space>
            }
        >
            <Spin spinning={loading}>
                {Object.keys(hierarchyTree).length === 0 ? (
                    <Empty description="Nenhum item encontrado. Copie os dados da aba HIERARQUIA original ou adicione novos." />
                ) : (
                    <Collapse
                        activeKey={expandedKeys}
                        onChange={setExpandedKeys}
                        className="hierarquia-collapse-linha"
                    >
                        {Object.entries(hierarchyTree)
                            .sort(([a], [b]) => a.localeCompare(b))
                            .map(([linha, linhaData]) => (
                            <Panel
                                key={`linha_${linha}`}
                                header={renderPanelHeader(linha, linhaData.count, 1)}
                                className="hierarquia-panel-linha"
                                extra={
                                    <Tooltip title={`Adicionar em ${linha}`}>
                                        <Button
                                            type="text"
                                            size="small"
                                            icon={<PlusOutlined />}
                                            onClick={e => {
                                                e.stopPropagation();
                                                addItem({ linha });
                                            }}
                                        />
                                    </Tooltip>
                                }
                            >
                                <Collapse
                                    activeKey={expandedKeys}
                                    onChange={keys => setExpandedKeys(prev => {
                                        const linhaKeys = prev.filter(k => k.startsWith('linha_'));
                                        return [...linhaKeys, ...keys];
                                    })}
                                    className="hierarquia-collapse-grupo"
                                >
                                    {Object.entries(linhaData.grupos)
                                        .sort(([a], [b]) => a.localeCompare(b))
                                        .map(([grupo, grupoData]) => (
                                        <Panel
                                            key={`grupo_${linha}_${grupo}`}
                                            header={renderPanelHeader(grupo, grupoData.count, 2)}
                                            className="hierarquia-panel-grupo"
                                            extra={
                                                <Tooltip title={`Adicionar em ${linha} → ${grupo}`}>
                                                    <Button
                                                        type="text"
                                                        size="small"
                                                        icon={<PlusOutlined />}
                                                        onClick={e => {
                                                            e.stopPropagation();
                                                            addItem({ linha, grupo });
                                                        }}
                                                    />
                                                </Tooltip>
                                            }
                                        >
                                            <Collapse
                                                activeKey={expandedKeys}
                                                onChange={keys => setExpandedKeys(prev => {
                                                    const upperKeys = prev.filter(k => 
                                                        k.startsWith('linha_') || k.startsWith('grupo_')
                                                    );
                                                    return [...upperKeys, ...keys];
                                                })}
                                                className="hierarquia-collapse-subgrupo"
                                            >
                                                {Object.entries(grupoData.subgrupos)
                                                    .sort(([a], [b]) => a.localeCompare(b))
                                                    .map(([subgrupo, subgrupoData]) => (
                                                    <Panel
                                                        key={`subgrupo_${linha}_${grupo}_${subgrupo}`}
                                                        header={renderPanelHeader(subgrupo, subgrupoData.count, 3)}
                                                        className="hierarquia-panel-subgrupo"
                                                        extra={
                                                            <Tooltip title={`Adicionar em ${linha} → ${grupo} → ${subgrupo}`}>
                                                                <Button
                                                                    type="text"
                                                                    size="small"
                                                                    icon={<PlusOutlined />}
                                                                    onClick={e => {
                                                                        e.stopPropagation();
                                                                        addItem({ linha, grupo, subgrupo });
                                                                    }}
                                                                />
                                                            </Tooltip>
                                                        }
                                                    >
                                                        <div className="hierarquia-tipos-list">
                                                            {subgrupoData.tipos
                                                                .sort((a, b) => 
                                                                    String(a.tipo_mercadoria || '').localeCompare(String(b.tipo_mercadoria || ''))
                                                                )
                                                                .map(item => (
                                                                <div key={item.__id}>
                                                                    {renderTipoItem(item)}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </Panel>
                                                ))}
                                            </Collapse>
                                        </Panel>
                                    ))}
                                </Collapse>
                            </Panel>
                        ))}
                    </Collapse>
                )}
            </Spin>
        </Card>
    );
};

export default HierarquiaEditorV2_Metodo;
