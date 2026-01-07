import React from 'react';
import { ModalDetalhesCalculoRecebimento } from '../recebimentos';
import DetalhesFaturamentoStackModal from './DetalhesFaturamentoStackModal';

const DetalhesComissaoModal = ({ visible, onClose, data, type }) => {
  if (!visible || !data) return null;

  if (type === 'faturamento') {
    return (
      <DetalhesFaturamentoStackModal
        visible={visible}
        onClose={onClose}
        processo={data}
      />
    );
  } else if (type === 'recebimento') {
    // ModalDetalhesCalculoRecebimento expects 'visible', 'onClose', 'pagamento'
    // And it renders a Modal itself.
    return (
      <ModalDetalhesCalculoRecebimento
        visible={visible}
        onClose={onClose}
        pagamento={data}
      />
    );
  }

  return null;
};

export default DetalhesComissaoModal;
