/**
 * BarraProgressoFinanceiro.js
 * 
 * Componente de barra de progresso visual que mostra o percentual
 * de pagamento de um processo (Total Pago / Valor Total).
 */

import React from 'react';
import { Progress, Tooltip } from 'antd';

/**
 * Determina a cor da barra de progresso com base no percentual.
 * @param {number} percent - Percentual de progresso (0-100)
 * @returns {string} - Cor em formato hex
 */
const getProgressColor = (percent) => {
  if (percent >= 100) return '#52c41a'; // Verde (Completo)
  if (percent >= 50) return '#1890ff';  // Azul (Bom progresso)
  if (percent >= 25) return '#faad14';  // Amarelo (Atenção)
  return '#ff4d4f';                      // Vermelho (Crítico)
};

/**
 * Formata valor monetário para exibição.
 * @param {number} value - Valor numérico
 * @returns {string} - Valor formatado em BRL
 */
const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
  }).format(value);
};

/**
 * Barra de progresso financeiro para visualização de pagamentos.
 * 
 * @param {Object} props
 * @param {number} props.totalPago - Valor total pago até o momento
 * @param {number} props.valorTotal - Valor total do processo
 * @param {number} props.percentual - Percentual pago (opcional, calculado se não fornecido)
 * @param {boolean} props.showInfo - Mostrar informações detalhadas (default: true)
 * @param {string} props.size - Tamanho da barra ('small', 'default', 'large')
 */
const BarraProgressoFinanceiro = ({
  totalPago = 0,
  valorTotal = 0,
  percentual,
  showInfo = true,
  size = 'default',
}) => {
  // Calcular percentual se não fornecido
  const percent = percentual !== undefined 
    ? percentual 
    : (valorTotal > 0 ? (totalPago / valorTotal) * 100 : 0);
  
  const roundedPercent = Math.round(percent * 100) / 100;
  const color = getProgressColor(roundedPercent);
  const saldo = valorTotal - totalPago;

  const tooltipContent = (
    <div>
      <div><strong>Total Pago:</strong> {formatCurrency(totalPago)}</div>
      <div><strong>Valor Total:</strong> {formatCurrency(valorTotal)}</div>
      <div><strong>Saldo:</strong> {formatCurrency(saldo)}</div>
    </div>
  );

  const strokeWidth = size === 'small' ? 6 : size === 'large' ? 12 : 8;

  return (
    <Tooltip title={tooltipContent} placement="top">
      <Progress
        percent={roundedPercent}
        strokeColor={color}
        trailColor="#f0f0f0"
        showInfo={showInfo}
        size={size}
        strokeWidth={strokeWidth}
        format={(p) => `${p.toFixed(1)}%`}
        status={roundedPercent >= 100 ? 'success' : 'active'}
      />
    </Tooltip>
  );
};

export default BarraProgressoFinanceiro;
