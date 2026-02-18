/**
 * RegraComissaoEditor.js
 * 
 * Editor de uma única regra de comissão.
 * 
 * Estrutura da Regra:
 * - regra_id: string identificador único
 * - linha, grupo, subgrupo, tipo_mercadoria, fabricante: filtros hierárquicos (null = wildcard)
 * - faixas: array de { limite_inferior, taxa_comissao_pct } (até 5)
 * 
 * Props:
 * - regra: objeto da regra
 * - index: índice na lista (para exibição)
 * - hierarquias: { linhas, grupos, subgrupos, tipos_mercadoria, fabricantes }
 * - onUpdate: callback(regraAtualizada)
 * - onDelete: callback()
 * - onDuplicate: callback()
 */

import React from 'react';
import FaixasComissaoEditor from './FaixasComissaoEditor';
import './RegraComissaoEditor.css';

const RegraComissaoEditor = ({
  regra,
  index,
  hierarquias = {},
  onUpdate,
  onDelete,
  onDuplicate,
}) => {
  // Handler para campos hierárquicos
  const handleHierarquiaChange = (campo, valor) => {
    onUpdate({
      ...regra,
      [campo]: valor === '' ? null : valor,
    });
  };

  // Handler para faixas
  const handleFaixasChange = (novasFaixas) => {
    onUpdate({
      ...regra,
      faixas: novasFaixas,
    });
  };

  // Calcular especificidade (campos não-null)
  const calcEspecificidade = () => {
    const campos = ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria', 'fabricante'];
    return campos.filter(c => regra[c] && regra[c] !== '').length;
  };

  const especificidade = calcEspecificidade();

  // Dropdown com opção wildcard
  const HierarchySelect = ({ campo, label, options }) => (
    <div className="hierarchy-field">
      <label>{label}</label>
      <select
        value={regra[campo] || ''}
        onChange={(e) => handleHierarquiaChange(campo, e.target.value)}
        className={regra[campo] ? 'has-value' : 'wildcard'}
      >
        <option value="">* (Qualquer)</option>
        {(options || []).map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="regra-comissao-editor">
      {/* Header da Regra */}
      <div className="regra-header">
        <div className="regra-info">
          <span className="regra-index">#{index + 1}</span>
          <span className="regra-id" title={String(regra.regra_id || '')}>
            ID: {String(regra.regra_id || '').slice(-6) || '---'}
          </span>
          <span className={`especificidade-badge esp-${especificidade}`}>
            Esp: {especificidade}/5
          </span>
        </div>
        <div className="regra-actions">
          <button 
            className="btn-action btn-duplicate"
            onClick={onDuplicate}
            title="Duplicar regra"
          >
            📋
          </button>
          <button 
            className="btn-action btn-delete-regra"
            onClick={onDelete}
            title="Excluir regra"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Filtros Hierárquicos */}
      <div className="hierarchy-filters">
        <HierarchySelect
          campo="linha"
          label="Linha"
          options={hierarquias.linhas}
        />
        <HierarchySelect
          campo="grupo"
          label="Grupo"
          options={hierarquias.grupos}
        />
        <HierarchySelect
          campo="subgrupo"
          label="Subgrupo"
          options={hierarquias.subgrupos}
        />
        <HierarchySelect
          campo="tipo_mercadoria"
          label="Tipo Mercadoria"
          options={hierarquias.tipos_mercadoria}
        />
        <HierarchySelect
          campo="fabricante"
          label="Fabricante"
          options={hierarquias.fabricantes}
        />
      </div>

      {/* Editor de Faixas */}
      <div className="faixas-section">
        <div className="faixas-header">
          <span className="section-title">Faixas de Comissão</span>
          <span className="faixas-info">
            {(regra.faixas || []).length}/5 faixas
          </span>
        </div>
        <FaixasComissaoEditor
          faixas={regra.faixas || []}
          onChange={handleFaixasChange}
          maxFaixas={5}
        />
      </div>
    </div>
  );
};

export default RegraComissaoEditor;
