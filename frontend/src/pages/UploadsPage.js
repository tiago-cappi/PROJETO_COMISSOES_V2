import React, { useState } from 'react';
import { Card, Upload, Button, message, Space, Typography } from 'antd';
import {
  UploadOutlined,
  FileExcelOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { uploadAPI } from '../services/api';

const { Title, Text } = Typography;

const UploadsPage = () => {
  const [uploadStates, setUploadStates] = useState({
    analise: { status: 'idle', filename: null },
    analiseFinanceira: { status: 'idle', filename: null },
    devolucoes: { status: 'idle', filename: null },
  });

  const handleUpload = async (tipo, file) => {
    try {
      setUploadStates((prev) => ({
        ...prev,
        [tipo]: { status: 'uploading', filename: file.name },
      }));

      let response;
      switch (tipo) {
        case 'analise':
          response = await uploadAPI.analiseComercial(file);
          break;
        case 'analiseFinanceira':
          response = await uploadAPI.analiseFinanceira(file);
          break;
        case 'devolucoes':
          response = await uploadAPI.devolucoes(file);
          break;
        default:
          throw new Error('Tipo de upload inválido');
      }

      setUploadStates((prev) => ({
        ...prev,
        [tipo]: { status: 'success', filename: response.data.filename },
      }));

      message.success(`${file.name} enviado com sucesso!`);
    } catch (error) {
      setUploadStates((prev) => ({
        ...prev,
        [tipo]: { status: 'error', filename: file.name },
      }));
      message.error(`Erro ao enviar ${file.name}: ${error.message}`);
    }
  };

  const uploadProps = (tipo, accept, descricao) => ({
    accept,
    beforeUpload: (file) => {
      handleUpload(tipo, file);
      return false; // Prevent auto upload
    },
    showUploadList: false,
    maxCount: 1,
  });

  const cards = [
    {
      key: 'analise',
      title: 'Análise Comercial Completa',
      descricao: 'Arquivo principal do ERP (xlsx ou csv)',
      accept: '.xlsx,.csv',
      icon: <FileExcelOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
    },
    {
      key: 'analiseFinanceira',
      title: 'Análise Financeira.xlsx',
      descricao: 'Pagamentos Regulares do Mês',
      accept: '.xlsx',
      icon: <FileExcelOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
    },
    {
      key: 'devolucoes',
      title: 'Devoluções.xlsx',
      descricao: 'Devoluções do período (xlsx)',
      accept: '.xlsx',
      icon: <FileExcelOutlined style={{ fontSize: 48, color: '#fa541c' }} />,
    },
  ];

  return (
    <div>
      <Card>
        <Title level={2}>Upload de Arquivos ERP</Title>
        <Text type="secondary">
          Faça upload dos arquivos necessários para o cálculo de comissões.
          Os arquivos serão salvos na pasta raiz do robô.
        </Text>
      </Card>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '24px',
          marginTop: '24px',
        }}
      >
        {cards.map((card) => {
          const state = uploadStates[card.key];
          const isSuccess = state.status === 'success';
          const isUploading = state.status === 'uploading';

          return (
            <Card
              key={card.key}
              hoverable
              style={{
                textAlign: 'center',
                border: isSuccess ? '2px solid #52c41a' : undefined,
              }}
            >
              {card.icon}
              <Title level={4} style={{ marginTop: 16 }}>
                {card.title}
              </Title>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                {card.descricao}
              </Text>

              {isSuccess ? (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <CheckCircleOutlined
                    style={{ fontSize: 32, color: '#52c41a' }}
                  />
                  <Text strong style={{ color: '#52c41a' }}>
                    Arquivo pronto
                  </Text>
                  {state.filename && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {state.filename}
                    </Text>
                  )}
                </Space>
              ) : (
                <Upload {...uploadProps(card.key, card.accept, card.descricao)}>
                  <Button
                    icon={<UploadOutlined />}
                    loading={isUploading}
                    type={isSuccess ? 'default' : 'primary'}
                    size="large"
                    block
                  >
                    {isUploading ? 'Enviando...' : 'Selecionar Arquivo'}
                  </Button>
                </Upload>
              )}

              {state.status === 'error' && (
                <Text type="danger" style={{ display: 'block', marginTop: 8 }}>
                  Erro no upload
                </Text>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default UploadsPage;

