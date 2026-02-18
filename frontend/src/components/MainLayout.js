import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  FileTextOutlined,
  UploadOutlined,
  PlayCircleOutlined,
  BarChartOutlined,
  DollarOutlined,
  DollarCircleOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  FileExcelOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import logo from '../assets/logo.png';

const { Sider, Header } = Layout;

// Paleta de cores corporativa - Azul e Branco
const colors = {
  primary: '#1E64A5',        // Azul institucional forte
  primaryDark: '#164875',    // Azul escuro para sidebar
  primaryLight: '#2D7DD2',   // Azul vibrante
  accent: '#4A9FE3',         // Azul claro para hovers
  white: '#FFFFFF',
  grayLight: '#F8F9FA',
  grayText: '#4A5568',
};

const MainLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/regras',
      icon: <FileTextOutlined />,
      label: 'Regras',
    },
    {
      key: '/metodo-v2',
      icon: <ExperimentOutlined />,
      label: 'Metodologia V2',
    },
    {
      key: '/uploads',
      icon: <UploadOutlined />,
      label: 'Uploads',
    },
    {
      key: '/dados-entrada',
      icon: <FileExcelOutlined />,
      label: 'Dados de Entrada',
    },
    {
      key: '/executar',
      icon: <PlayCircleOutlined />,
      label: 'Executar Cálculo',
    },
    {
      key: '/comissoes',
      icon: <BarChartOutlined />,
      label: 'Comissões',
    },
    {
      key: '/estado-processos',
      icon: <DatabaseOutlined />,
      label: 'Estado Processos',
    },
    {
      key: '/cambio',
      icon: <DollarOutlined />,
      label: 'Taxas de Câmbio',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        theme="dark"
        width={250}
        style={{
          background: colors.primaryDark,
          boxShadow: '2px 0 12px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ 
          padding: '20px 16px', 
          textAlign: 'center', 
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          background: colors.primary,
        }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: '18px', 
            fontWeight: 'bold',
            color: colors.white,
            letterSpacing: '0.5px',
          }}>
            Robô de Comissões
          </h2>
        </div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ 
            borderRight: 0, 
            marginTop: '8px',
            background: 'transparent',
          }}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          background: colors.white, 
          padding: '0 24px', 
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          borderBottom: `3px solid ${colors.primary}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h1 style={{ 
            margin: 0, 
            fontSize: '20px', 
            fontWeight: '500',
            color: colors.grayText,
          }}>
            Sistema de Cálculo de Comissões
          </h1>
          <img 
            src={logo} 
            alt="Logo da Empresa" 
            style={{ 
              maxHeight: '50px', 
              height: 'auto',
              objectFit: 'contain',
            }} 
          />
        </Header>
        {children}
      </Layout>
    </Layout>
  );
};

export default MainLayout;

