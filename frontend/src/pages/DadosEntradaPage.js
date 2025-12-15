import React, { useState, useEffect } from 'react';
import { Card, Select, Empty, message } from 'antd';
import { FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import GenericSheetEditor from '../components/GenericSheetEditor';
import { dadosEntradaAPI } from '../services/api';

const { Option } = Select;

const DadosEntradaPage = () => {
  const [arquivos, setArquivos] = useState([]);
  const [arquivoSelecionado, setArquivoSelecionado] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    carregarArquivos();
  }, []);

  const carregarArquivos = async () => {
    setLoading(true);
    try {
      const resp = await dadosEntradaAPI.listarArquivos();
      setArquivos(resp.data.arquivos || []);
    } catch (e) {
      message.error('Erro ao listar arquivos de entrada');
    } finally {
      setLoading(false);
    }
  };

  // Adaptador para o GenericSheetEditor usar a API de dados de entrada
  const apiAdapter = {
    read: (id, params) => dadosEntradaAPI.lerArquivo(id, params),
    save: (id, data) => dadosEntradaAPI.salvarArquivo(id, data),
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title="Dados de Entrada" style={{ marginBottom: 24 }}>
        <Select
          style={{ width: 400 }}
          placeholder="Selecione um arquivo para editar"
          onChange={setArquivoSelecionado}
          value={arquivoSelecionado}
          loading={loading}
        >
          {arquivos.map((arq) => (
            <Option key={arq} value={arq}>
              {arq.endsWith('.csv') ? <FileTextOutlined /> : <FileExcelOutlined />} {arq}
            </Option>
          ))}
        </Select>
      </Card>

      {arquivoSelecionado ? (
        <GenericSheetEditor
          key={arquivoSelecionado} // Forçar remontagem ao trocar arquivo
          resourceId={arquivoSelecionado}
          apiService={apiAdapter}
          title={`Editando: ${arquivoSelecionado}`}
        />
      ) : (
        <Empty description="Selecione um arquivo para visualizar ou editar" />
      )}
    </div>
  );
};

export default DadosEntradaPage;
