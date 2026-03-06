import React from 'react';
import DetalhesCalculoModal from '../DetalhesCalculoModal';
import './ColaboradorDashboard.css';

/**
 * Renderiza o detalhamento inline (expandido) de um item de faturamento.
 *
 * Reutiliza o componente DetalhesCalculoModal existente, que já renderiza
 * os 3 passos do cálculo (Base → FC → Final) como um <div> (sem Modal).
 *
 * @param {Object} props
 * @param {Object} props.rowData - Linha completa do item (todos os campos de COMISSOES_CALCULADAS)
 */
const FaturamentoItemDetail = ({ rowData }) => {
  if (!rowData) {
    return <div className="colab-item-detail">Nenhum dado disponível.</div>;
  }

  return (
    <div className="colab-item-detail">
      <DetalhesCalculoModal rowData={rowData} />
    </div>
  );
};

export default FaturamentoItemDetail;
