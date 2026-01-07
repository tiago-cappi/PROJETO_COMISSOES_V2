import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, Spin, message, Tooltip } from 'antd';
import { 
  FileExcelOutlined, 
  FileTextOutlined, 
  FolderOpenOutlined,
  FolderOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  RightOutlined,
  LeftOutlined,
  InboxOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';
import DataTable from '../components/DataTable';
import { dadosEntradaAPI } from '../services/api';
import './DadosEntradaPage.css';

const DadosEntradaPage = () => {
  // State
  const [arquivosPrincipais, setArquivosPrincipais] = useState([]);
  const [arquivosRentabilidades, setArquivosRentabilidades] = useState([]);
  const [arquivoSelecionado, setArquivoSelecionado] = useState(null);
  const [tipoSelecionado, setTipoSelecionado] = useState(null); // 'principal' ou 'rentabilidade'
  const [loading, setLoading] = useState(false);
  const [showRentabilidades, setShowRentabilidades] = useState(false);
  const [activeTab, setActiveTab] = useState('dados');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Load file lists
  const carregarArquivos = useCallback(async () => {
    setLoading(true);
    try {
      const [respPrincipal, respRent] = await Promise.all([
        dadosEntradaAPI.listarArquivos(),
        dadosEntradaAPI.listarRentabilidades()
      ]);
      setArquivosPrincipais(respPrincipal.data.arquivos || []);
      setArquivosRentabilidades(respRent.data.arquivos || []);
    } catch (e) {
      message.error('Erro ao listar arquivos de entrada');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    carregarArquivos();
  }, [carregarArquivos]);

  // File selection handlers
  const selectPrincipal = (arquivo) => {
    setArquivoSelecionado(arquivo);
    setTipoSelecionado('principal');
  };

  const selectRentabilidade = (arquivo) => {
    setArquivoSelecionado(arquivo);
    setTipoSelecionado('rentabilidade');
  };

  // Get file extension
  const getFileExt = (filename) => {
    return filename.split('.').pop().toLowerCase();
  };

  // API adapter for DataTable
  const getApiAdapter = () => {
    if (tipoSelecionado === 'rentabilidade') {
      return {
        read: (id, params) => dadosEntradaAPI.lerRentabilidade(id, params),
        save: (id, data) => dadosEntradaAPI.salvarRentabilidade(id, data),
      };
    }
    return {
      read: (id, params) => dadosEntradaAPI.lerArquivo(id, params),
      save: (id, data) => dadosEntradaAPI.salvarArquivo(id, data),
    };
  };

  // Render file card
  const renderFileCard = (arquivo, isActive, onClick, tipo = 'principal') => {
    const ext = getFileExt(arquivo);
    const isXlsx = ext === 'xlsx' || ext === 'xls';
    
    return (
      <div 
        key={arquivo}
        className={`file-card ${isActive ? 'file-card--active' : ''}`}
        onClick={onClick}
      >
        <div className={`file-card__icon ${isXlsx ? 'file-card__icon--xlsx' : 'file-card__icon--csv'}`}>
          {isXlsx ? <FileExcelOutlined /> : <FileTextOutlined />}
        </div>
        <div className="file-card__info">
          <p className="file-card__name" title={arquivo}>{arquivo}</p>
          <span className="file-card__type">{isXlsx ? 'Excel' : 'CSV'}</span>
        </div>
        <RightOutlined className="file-card__arrow" />
      </div>
    );
  };

  // Render file list sidebar
  const renderFileList = () => (
    <div className={`file-list ${sidebarCollapsed ? 'file-list--collapsed' : ''}`}>
      <div className="file-list__header">
        <h4 className="file-list__title">
          {!sidebarCollapsed && (
            <>
              <DatabaseOutlined /> Arquivos
              <span className="file-list__count">
                {arquivosPrincipais.length + arquivosRentabilidades.length}
              </span>
            </>
          )}
        </h4>
        <Tooltip title={sidebarCollapsed ? 'Expandir lista' : 'Recolher lista'}>
          <button 
            className="file-list__toggle"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </Tooltip>
      </div>

      <div className="file-list__items">
        {loading ? (
          <div className="file-list__loading">
            {[1, 2, 3].map(i => <div key={i} className="skeleton-card" />)}
          </div>
        ) : (
          <>
            {/* Main Files */}
            {arquivosPrincipais.map((arquivo) => 
              renderFileCard(
                arquivo, 
                arquivoSelecionado === arquivo && tipoSelecionado === 'principal',
                () => selectPrincipal(arquivo)
              )
            )}

            {/* Divider */}
            {arquivosPrincipais.length > 0 && <div className="file-list__divider" />}

            {/* Rentabilidades Folder */}
            <div 
              className={`folder-card ${showRentabilidades ? 'folder-card--open' : ''}`}
              onClick={() => setShowRentabilidades(!showRentabilidades)}
            >
              <div className="folder-card__icon">
                {showRentabilidades ? <FolderOpenOutlined /> : <FolderOutlined />}
              </div>
              <div className="folder-card__info">
                <p className="folder-card__name">📊 Rentabilidades Mensais</p>
                <span className="folder-card__count">
                  {arquivosRentabilidades.length} arquivo(s)
                </span>
              </div>
              <RightOutlined className="folder-card__arrow" />
            </div>

            {/* Rentabilidades Files (Collapsible) */}
            {showRentabilidades && (
              <div className="rentabilidades-files">
                {arquivosRentabilidades.length === 0 ? (
                  <p style={{ padding: '12px 20px', color: '#94a3b8', fontSize: 13 }}>
                    Nenhum arquivo de rentabilidade encontrado
                  </p>
                ) : (
                  arquivosRentabilidades.map((arquivo) => 
                    renderFileCard(
                      arquivo, 
                      arquivoSelecionado === arquivo && tipoSelecionado === 'rentabilidade',
                      () => selectRentabilidade(arquivo),
                      'rentabilidade'
                    )
                  )
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );

  // Render content area
  const renderContent = () => {
    if (!arquivoSelecionado) {
      return (
        <div className="file-content__empty">
          <InboxOutlined className="file-content__empty-icon" />
          <h3 className="file-content__empty-title">Selecione um arquivo</h3>
          <p className="file-content__empty-text">
            Escolha um arquivo na lista ao lado para visualizar ou editar os dados
          </p>
        </div>
      );
    }

    const ext = getFileExt(arquivoSelecionado);
    const isRent = tipoSelecionado === 'rentabilidade';
    
    return (
      <DataTable
        key={`${tipoSelecionado}-${arquivoSelecionado}`}
        resourceId={arquivoSelecionado}
        apiService={getApiAdapter()}
        title={arquivoSelecionado}
        subtitle={isRent ? 'Rentabilidade Mensal' : 'Dados de Entrada'}
        icon={ext === 'csv' ? <FileTextOutlined /> : <FileExcelOutlined />}
      />
    );
  };

  // Tab items
  const tabItems = [
    {
      key: 'dados',
      label: (
        <span>
          <DatabaseOutlined className="tab-icon" />
          Dados de Entrada
        </span>
      ),
      children: (
        <div className={`file-browser ${sidebarCollapsed ? 'file-browser--collapsed' : ''}`}>
          {renderFileList()}
          <div className="file-content">
            {renderContent()}
          </div>
        </div>
      ),
    },
    {
      key: 'info',
      label: (
        <span>
          <BarChartOutlined className="tab-icon" />
          Informações
        </span>
      ),
      children: (
        <div className="file-content__empty">
          <BarChartOutlined className="file-content__empty-icon" />
          <h3 className="file-content__empty-title">Estatísticas dos Dados</h3>
          <p className="file-content__empty-text">
            Esta seção mostrará estatísticas e validações dos dados de entrada (em breve)
          </p>
        </div>
      ),
    },
  ];

  return (
    <div className="dados-entrada-page">
      {/* Header */}
      <div className="dados-entrada-page__header">
        <h1 className="dados-entrada-page__title">Dados de Entrada</h1>
        <p className="dados-entrada-page__subtitle">
          Visualize e edite os arquivos de dados utilizados no cálculo de comissões
        </p>
      </div>

      {/* Tabs */}
      <Tabs
        className="dados-entrada-page__tabs"
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
    </div>
  );
};

export default DadosEntradaPage;
