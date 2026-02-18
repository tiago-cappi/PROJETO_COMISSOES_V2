/**
 * ColaboradorConfigCard.js
 * 
 * Card expansível que exibe um colaborador e suas regras de comissão.
 * Nova arquitetura: Colaborador = Nome + Cargo + Lista de Regras
 * 
 * Cada Regra tem:
 * - regra_id (único)
 * - 5 campos de filtro hierárquico (linha, grupo, subgrupo, tipo_mercadoria, fabricante)
 * - até 5 faixas de comissão (limite_inferior R$, taxa_comissao_pct %)
 * 
 * Props:
 * - colaborador: { nome, cargo, regras: [] }
 * - cargos: ['Cargo1', 'Cargo2', ...]
 * - hierarquias: { linhas, grupos, subgrupos, tipos_mercadoria, fabricantes }
 * - onUpdate: callback(colaboradorAtualizado)
 * - onDelete: callback()
 */

import React, { useState } from 'react';
import RegraComissaoEditor from './RegraComissaoEditor';
import './ColaboradorConfigCard.css';

const ColaboradorConfigCard = ({ 
  colaborador, 
  cargos = [], 
  hierarquias = {},
  onUpdate, 
  onDelete 
}) => {
  const [expanded, setExpanded] = useState(false);
  const [editingNome, setEditingNome] = useState(false);
  const [tempNome, setTempNome] = useState(colaborador.nome || '');

  // Handlers de atualização
  const handleCargoChange = (novoCargo) => {
    onUpdate({
      ...colaborador,
      cargo: novoCargo || null,
    });
  };

  const handleNomeSave = () => {
    if (tempNome.trim()) {
      onUpdate({
        ...colaborador,
        nome: tempNome.trim(),
      });
    }
    setEditingNome(false);
  };

  const handleAddRegra = () => {
    const novaRegra = {
      regra_id: `R${Date.now()}`,
      linha: null,
      grupo: null,
      subgrupo: null,
      tipo_mercadoria: null,
      fabricante: null,
      faixas: [{ limite_inferior: 0, limite_superior: null, taxa_comissao_pct: 1 }],
    };
    onUpdate({
      ...colaborador,
      regras: [...(colaborador.regras || []), novaRegra],
    });
    setExpanded(true);
  };

  const handleUpdateRegra = (index, regraAtualizada) => {
    const regras = [...(colaborador.regras || [])];
    regras[index] = regraAtualizada;
    onUpdate({ ...colaborador, regras });
  };

  const handleDeleteRegra = (index) => {
    const regras = (colaborador.regras || []).filter((_, i) => i !== index);
    onUpdate({ ...colaborador, regras });
  };

  const handleDuplicateRegra = (index) => {
    const regraOriginal = colaborador.regras[index];
    const novaRegra = {
      ...JSON.parse(JSON.stringify(regraOriginal)),
      regra_id: `R${Date.now()}`,
    };
    const regras = [...colaborador.regras];
    regras.splice(index + 1, 0, novaRegra);
    onUpdate({ ...colaborador, regras });
  };

  const regras = colaborador.regras || [];
  const qtdRegras = regras.length;
  const especificidadeMedia = qtdRegras > 0
    ? (regras.reduce((sum, r) => sum + (r.especificidade || 0), 0) / qtdRegras).toFixed(1)
    : '-';

  return (
    <div className={`colaborador-config-card ${expanded ? 'expanded' : ''}`}>
      {/* Header do Card */}
      <div className="card-header" onClick={() => setExpanded(!expanded)}>
        <div className="header-left">
          <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
          
          {editingNome ? (
            <input
              type="text"
              value={tempNome}
              onChange={(e) => setTempNome(e.target.value)}
              onBlur={handleNomeSave}
              onKeyPress={(e) => e.key === 'Enter' && handleNomeSave()}
              onClick={(e) => e.stopPropagation()}
              className="nome-input"
              autoFocus
            />
          ) : (
            <span 
              className="colaborador-nome"
              onDoubleClick={(e) => {
                e.stopPropagation();
                setEditingNome(true);
                setTempNome(colaborador.nome || '');
              }}
              title="Clique duplo para editar"
            >
              {colaborador.nome || '(sem nome)'}
            </span>
          )}

          {/* Cargo é apenas exibido (definido em Colaboradores/Cargos) */}
          {colaborador.cargo && (
            <span className="cargo-badge" title="Cargo definido na aba Colaboradores/Cargos">
              {colaborador.cargo}
            </span>
          )}

          <span
            className={`tipo-comissao-badge ${colaborador.tipo_comissao === 'recebimento' ? 'recebimento' : 'faturamento'}`}
            title="Tipo de comissão (definido em Colaboradores/Cargos)"
          >
            {colaborador.tipo_comissao === 'recebimento' ? 'Recebimento' : 'Faturamento'}
          </span>
        </div>

        <div className="header-right">
          <span className="badge regras-count" title="Quantidade de regras">
            {qtdRegras} {qtdRegras === 1 ? 'regra' : 'regras'}
          </span>
          <span className="badge especificidade" title="Especificidade média das regras">
            Esp. média: {especificidadeMedia}
          </span>
          <button
            className="btn-icon btn-add-regra"
            onClick={(e) => {
              e.stopPropagation();
              handleAddRegra();
            }}
            title="Adicionar nova regra"
          >
            + Regra
          </button>
          <button
            className="btn-icon btn-delete"
            onClick={(e) => {
              e.stopPropagation();
              if (window.confirm(`Remover colaborador "${colaborador.nome}" e todas as suas regras?`)) {
                onDelete();
              }
            }}
            title="Remover colaborador"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* Corpo expandido */}
      {expanded && (
        <div className="card-body">
          {regras.length === 0 ? (
            <div className="empty-regras">
              <p>Nenhuma regra configurada.</p>
              <button className="btn-primary" onClick={handleAddRegra}>
                + Adicionar Primeira Regra
              </button>
            </div>
          ) : (
            <div className="regras-list">
              {regras.map((regra, index) => (
                <RegraComissaoEditor
                  key={regra.regra_id}
                  regra={regra}
                  index={index}
                  hierarquias={hierarquias}
                  onUpdate={(regraAtualizada) => handleUpdateRegra(index, regraAtualizada)}
                  onDelete={() => handleDeleteRegra(index)}
                  onDuplicate={() => handleDuplicateRegra(index)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ColaboradorConfigCard;
