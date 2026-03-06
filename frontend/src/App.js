import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import MainLayout from './components/MainLayout';

import 'antd/dist/reset.css';
import './App.css';

const { Content } = Layout;

const RegrasPage = lazy(() => import('./pages/RegrasPage'));
const UploadsPage = lazy(() => import('./pages/UploadsPage'));
const ExecutarPage = lazy(() => import('./pages/ExecutarPage'));
const ComissoesPage = lazy(() => import('./pages/ComissoesPage'));
const CambioPage = lazy(() => import('./pages/CambioPage'));
const EstadoProcessosPage = lazy(() => import('./pages/EstadoProcessosPage'));
const DadosEntradaPage = lazy(() => import('./pages/DadosEntradaPage'));
const MetodoV2Page = lazy(() => import('./pages/MetodoV2Page'));

function App() {
  return (
    <Router>
      <MainLayout>
        <Content style={{ padding: '24px', minHeight: '100vh' }}>
          <Suspense fallback={<div>Carregando módulo...</div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/regras" replace />} />
              <Route path="/regras" element={<RegrasPage />} />
              <Route path="/uploads" element={<UploadsPage />} />
              <Route path="/dados-entrada" element={<DadosEntradaPage />} />
              <Route path="/executar" element={<ExecutarPage />} />
              <Route path="/comissoes" element={<ComissoesPage />} />
              <Route path="/estado-processos" element={<EstadoProcessosPage />} />
              <Route path="/cambio" element={<CambioPage />} />
              <Route path="/metodo-v2" element={<MetodoV2Page />} />
            </Routes>
          </Suspense>
        </Content>
      </MainLayout>
    </Router>
  );
}

export default App;


