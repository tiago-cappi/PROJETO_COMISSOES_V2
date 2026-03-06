import React, { useMemo, useState } from 'react';
import { Card, Input, Select, Typography, Tag, Avatar, Empty } from 'antd';
import {
  SearchOutlined,
  UserOutlined,
  FileTextOutlined,
  AppstoreOutlined,
  DollarOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import './ColaboradorDashboard.css';

const { Text } = Typography;
const { Option } = Select;

const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const getInitials = (name) => {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

const AVATAR_COLORS = [
  '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1',
  '#13c2c2', '#eb2f96', '#fa8c16', '#2f54eb', '#a0d911',
];

const getAvatarColor = (name) => {
  if (!name) return AVATAR_COLORS[0];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
};

const SORT_OPTIONS = [
  { value: 'comissao_desc', label: 'Comissão (maior)' },
  { value: 'comissao_asc', label: 'Comissão (menor)' },
  { value: 'nome_asc', label: 'Nome (A-Z)' },
  { value: 'nome_desc', label: 'Nome (Z-A)' },
  { value: 'processos_desc', label: 'Processos (maior)' },
];

/**
 * Nível 1 — Lista de cards de colaboradores para seleção.
 *
 * @param {Object} props
 * @param {Array} props.colaboradores - Lista de colaboradores do endpoint
 * @param {boolean} props.loading - Estado de carregamento
 * @param {Function} props.onSelectColaborador - Callback ao clicar em um card
 * @param {'faturamento'|'recebimento'} props.tipo - Tipo de comissão
 */
const ColaboradorCardList = ({ colaboradores = [], loading, onSelectColaborador, tipo = 'faturamento' }) => {
  const [search, setSearch] = useState('');
  const [filterCargo, setFilterCargo] = useState(null);
  const [sortBy, setSortBy] = useState('comissao_desc');

  // Extrair cargos únicos para o filtro
  const cargosUnicos = useMemo(() => {
    const set = new Set();
    colaboradores.forEach((c) => {
      if (c.cargo) set.add(c.cargo);
    });
    return Array.from(set).sort();
  }, [colaboradores]);

  // Filtrar e ordenar
  const filtered = useMemo(() => {
    let result = [...colaboradores];

    // Busca por nome
    if (search) {
      const term = search.toLowerCase();
      result = result.filter((c) =>
        (c.nome_colaborador || '').toLowerCase().includes(term)
      );
    }

    // Filtro por cargo
    if (filterCargo) {
      result = result.filter((c) => c.cargo === filterCargo);
    }

    // Ordenação
    switch (sortBy) {
      case 'comissao_asc':
        result.sort((a, b) => (a.total_comissao || 0) - (b.total_comissao || 0));
        break;
      case 'nome_asc':
        result.sort((a, b) => (a.nome_colaborador || '').localeCompare(b.nome_colaborador || ''));
        break;
      case 'nome_desc':
        result.sort((a, b) => (b.nome_colaborador || '').localeCompare(a.nome_colaborador || ''));
        break;
      case 'processos_desc':
        result.sort((a, b) => (b.total_processos || 0) - (a.total_processos || 0));
        break;
      case 'comissao_desc':
      default:
        result.sort((a, b) => (b.total_comissao || 0) - (a.total_comissao || 0));
        break;
    }

    return result;
  }, [colaboradores, search, filterCargo, sortBy]);

  // Totais gerais
  const totalGeral = useMemo(() => {
    return colaboradores.reduce((acc, c) => acc + (c.total_comissao || 0), 0);
  }, [colaboradores]);

  if (!loading && colaboradores.length === 0) {
    return (
      <div className="colab-empty">
        <div className="colab-empty__icon"><UserOutlined /></div>
        <div className="colab-empty__text">Nenhum dado de comissão encontrado.</div>
      </div>
    );
  }

  const isRecebimento = tipo === 'recebimento';

  return (
    <div className="colab-card-list">
      {/* Toolbar */}
      <div className="colab-card-list__toolbar">
        <Input
          className="colab-card-list__search"
          placeholder="Buscar colaborador..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
        <Select
          className="colab-card-list__filter-cargo"
          placeholder="Filtrar por cargo"
          value={filterCargo}
          onChange={setFilterCargo}
          allowClear
        >
          {cargosUnicos.map((c) => (
            <Option key={c} value={c}>{c}</Option>
          ))}
        </Select>
        <Select
          className="colab-card-list__sort"
          value={sortBy}
          onChange={setSortBy}
        >
          {SORT_OPTIONS.map((opt) => (
            <Option key={opt.value} value={opt.value}>{opt.label}</Option>
          ))}
        </Select>
        <Text className="colab-card-list__count" type="secondary">
          {filtered.length} colaborador{filtered.length !== 1 ? 'es' : ''} · Total: <Text strong>{formatCurrencyBR(totalGeral)}</Text>
        </Text>
      </div>

      {/* Cards Grid */}
      {filtered.length === 0 ? (
        <Empty description="Nenhum colaborador encontrado com os filtros aplicados." />
      ) : (
        <div className="colab-card-list__grid">
          {filtered.map((colab) => (
            <Card
              key={colab.nome_colaborador}
              className="colab-card"
              hoverable
              loading={loading}
              onClick={() => onSelectColaborador(colab)}
              size="small"
              bodyStyle={{ padding: 16 }}
            >
              {/* Header: Avatar + Nome + Cargo */}
              <div className="colab-card__header">
                <Avatar
                  className="colab-card__avatar"
                  size={44}
                  style={{ backgroundColor: getAvatarColor(colab.nome_colaborador) }}
                >
                  {getInitials(colab.nome_colaborador)}
                </Avatar>
                <div className="colab-card__info">
                  <p className="colab-card__name">{colab.nome_colaborador}</p>
                  <p className="colab-card__cargo">{colab.cargo || '—'}</p>
                </div>
              </div>

              {/* Comissão Total */}
              <div className={`colab-card__comissao ${isRecebimento ? 'colab-card__comissao--recebimento' : ''}`}>
                {formatCurrencyBR(colab.total_comissao)}
              </div>

              {/* Stats */}
              <div className="colab-card__stats">
                <span className="colab-card__stat">
                  <FileTextOutlined className="colab-card__stat-icon" />
                  {colab.total_processos || 0} processo{(colab.total_processos || 0) !== 1 ? 's' : ''}
                </span>
                {isRecebimento ? (
                  <>
                    <span className="colab-card__stat">
                      <CalendarOutlined className="colab-card__stat-icon" />
                      <Tag color="blue" style={{ margin: 0 }}>{colab.total_adiantamentos || 0} adiant.</Tag>
                    </span>
                    <span className="colab-card__stat">
                      <DollarOutlined className="colab-card__stat-icon" />
                      <Tag color="green" style={{ margin: 0 }}>{colab.total_regulares || 0} regular</Tag>
                    </span>
                  </>
                ) : (
                  <span className="colab-card__stat">
                    <AppstoreOutlined className="colab-card__stat-icon" />
                    {colab.total_itens || 0} ite{(colab.total_itens || 0) !== 1 ? 'ns' : 'm'}
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ColaboradorCardList;
