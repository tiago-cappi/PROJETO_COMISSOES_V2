import React, { useState, useEffect } from 'react';
import { Card, Empty, message, Typography, Space } from 'antd';
import { DollarCircleOutlined } from '@ant-design/icons';
import { recebimentoAPI } from '../services/api';
import {
  RecebimentosSelectorPanel,
  RecebimentosTabelaSimples,
  ModalDetalhesCalculoRecebimento,
} from '../components/recebimentos';

const { Title } = Typography;

/**
 * Página de Recebimentos - Visualização Minimalista
 * Objetivo: Mostrar apenas os pagamentos realizados no mês/ano selecionado.
 * Não mostra histórico acumulado (isso é responsabilidade da página Estado Processos).
 */
const RecebimentosPage = () => {
  const currentDate = new Date();
  const [mes, setMes] = useState(currentDate.getMonth() + 1);
  const [ano, setAno] = useState(currentDate.getFullYear());
  const [loading, setLoading] = useState(false);
  
  // Dados dos pagamentos do mês selecionado
  const [pagamentos, setPagamentos] = useState([]);
  const [totais, setTotais] = useState({
    adiantamentos: { valor: 0, quantidade: 0 },
    regulares: { valor: 0, quantidade: 0 },
    geral: { valor: 0, quantidade: 0 },
  });
  
  // Modal de detalhes
  const [modalVisible, setModalVisible] = useState(false);
  const [pagamentoSelecionado, setPagamentoSelecionado] = useState(null);

  // Carregar dados quando mês/ano mudarem
  useEffect(() => {
    carregarPagamentos();
  }, [mes, ano]);

  const carregarPagamentos = async () => {
    try {
      setLoading(true);
      const response = await recebimentoAPI.getPagamentos(mes, ano);
      
      const dados = response.data.pagamentos || [];
      setPagamentos(dados);
      
      // Calcular totais
      const adiantamentos = dados.filter(p => p.tipo === 'ADIANTAMENTO' || p.tipo === 'Antecipação');
      const regulares = dados.filter(p => p.tipo === 'REGULAR' || p.tipo === 'Regular');
      
      setTotais({
        adiantamentos: {
          valor: adiantamentos.reduce((acc, p) => acc + (p.comissao_calculada || 0), 0),
          quantidade: adiantamentos.length,
        },
        regulares: {
          valor: regulares.reduce((acc, p) => acc + (p.comissao_calculada || 0), 0),
          quantidade: regulares.length,
        },
        geral: {
          valor: dados.reduce((acc, p) => acc + (p.comissao_calculada || 0), 0),
          quantidade: dados.length,
        },
      });
    } catch (error) {
      console.error('Erro ao carregar pagamentos:', error);
      message.error(`Erro ao carregar pagamentos de ${mes}/${ano}`);
      setPagamentos([]);
      setTotais({
        adiantamentos: { valor: 0, quantidade: 0 },
        regulares: { valor: 0, quantidade: 0 },
        geral: { valor: 0, quantidade: 0 },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBaixarExcel = async () => {
    try {
      const response = await recebimentoAPI.baixarExcel(mes, ano);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `Comissoes_Recebimento_${mes.toString().padStart(2, '0')}_${ano}.xlsx`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('Download iniciado!');
    } catch (error) {
      console.error('Erro ao baixar Excel:', error);
      message.error('Erro ao baixar arquivo Excel');
    }
  };

  const handleVerDetalhes = async (pagamento) => {
    try {
      setLoading(true);
      // Buscar detalhes completos do cálculo (TCMP breakdown, FCMP breakdown, etc.)
      const response = await recebimentoAPI.getDetalhesPagamento(pagamento.id || pagamento.key);
      setPagamentoSelecionado(response.data);
      setModalVisible(true);
    } catch (error) {
      console.error('Erro ao buscar detalhes:', error);
      message.error('Erro ao carregar detalhes do pagamento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <Space size="middle">
            <DollarCircleOutlined style={{ fontSize: 32, color: '#52c41a' }} />
            <Title level={2} style={{ margin: 0 }}>
              Pagamentos por Recebimento
            </Title>
          </Space>
        </div>

        {/* Seletor de Mês/Ano + Cards de Totais */}
        <RecebimentosSelectorPanel
          mes={mes}
          ano={ano}
          onMesChange={setMes}
          onAnoChange={setAno}
          onReload={carregarPagamentos}
          onBaixarExcel={handleBaixarExcel}
          totais={totais}
          loading={loading}
        />

        {/* Tabela de Pagamentos */}
        {pagamentos.length === 0 && !loading ? (
          <Empty
            description={`Nenhum pagamento encontrado para ${mes}/${ano}`}
            style={{ marginTop: 40 }}
          />
        ) : (
          <RecebimentosTabelaSimples
            dados={pagamentos}
            loading={loading}
            onVerDetalhes={handleVerDetalhes}
          />
        )}
      </Card>

      {/* Modal de Detalhes do Cálculo */}
      <ModalDetalhesCalculoRecebimento
        visible={modalVisible}
        onClose={() => {
          setModalVisible(false);
          setPagamentoSelecionado(null);
        }}
        pagamento={pagamentoSelecionado}
      />
    </div>
  );
};

export default RecebimentosPage;

