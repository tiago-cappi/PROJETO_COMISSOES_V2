/**
 * FaixasComissaoEditor.js
 * 
 * Editor de faixas de comissão simplificado com validação de gaps.
 * 
 * Estrutura de faixa:
 * {
 *   limite_inferior: number,    // De (R$)
 *   limite_superior: number|null, // Até (R$) - null = sem limite (∞)
 *   taxa_comissao_pct: number   // Taxa %
 * }
 * 
 * Validações:
 * - Gaps: Faixa N.limite_superior + 0.01 === Faixa N+1.limite_inferior
 * - Overlap: Faixa N.limite_superior >= Faixa N+1.limite_inferior
 * - Ordem: limite_inferior < limite_superior
 * 
 * Props:
 * - faixas: array de faixas
 * - onChange: callback(novasFaixas)
 * - maxFaixas: número máximo de faixas (default 5)
 */

import React, { useMemo } from 'react';
import './FaixasComissaoEditor.css';

const FaixasComissaoEditor = ({ faixas = [], onChange, maxFaixas = 5 }) => {
  
  // ==================== FORMATAÇÃO ====================
  
  // Formatar valor para exibição em R$
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '∞';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Formatar input para display (sem símbolo R$)
  const formatInputDisplay = (value) => {
    if (value === null || value === undefined || value === '') return '';
    const num = parseFloat(value);
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  // Parse de string formatada para número
  const parseFormattedValue = (str) => {
    if (!str || str === '') return 0;
    // Remove pontos de milhar e troca vírgula por ponto
    const cleaned = str.replace(/\./g, '').replace(',', '.');
    const num = parseFloat(cleaned);
    return isNaN(num) ? 0 : num;
  };

  // ==================== VALIDAÇÃO ====================
  
  // Validar todas as faixas e retornar erros
  const validationErrors = useMemo(() => {
    const errors = [];
    
    for (let i = 0; i < faixas.length; i++) {
      const faixa = faixas[i];
      const faixaErrors = [];
      const isLast = i === faixas.length - 1;
      
      // Validar ordem dentro da faixa (limite_inferior < limite_superior)
      if (faixa.limite_superior !== null && faixa.limite_inferior >= faixa.limite_superior) {
        faixaErrors.push('O valor "De" deve ser menor que "Até"');
      }
      
      // Faixas intermediárias DEVEM ter limite_superior definido
      if (!isLast && faixa.limite_superior === null) {
        faixaErrors.push('Faixas intermediárias devem ter limite superior definido. Clique em "Definir".');
      }
      
      // Validar gap/overlap com a próxima faixa
      if (i < faixas.length - 1) {
        const proximaFaixa = faixas[i + 1];
        const fimAtual = faixa.limite_superior;
        const inicioProxima = proximaFaixa.limite_inferior;
        
        if (fimAtual !== null) {
          const esperado = fimAtual + 0.01;
          const diff = Math.abs(esperado - inicioProxima);
          
          if (diff > 0.02) { // Tolerância para arredondamento
            if (inicioProxima > esperado) {
              // GAP detectado
              const gapInicio = fimAtual + 0.01;
              const gapFim = inicioProxima - 0.01;
              faixaErrors.push(
                `Gap detectado: ${formatCurrency(gapInicio)} até ${formatCurrency(gapFim)} não está coberto`
              );
            } else {
              // OVERLAP detectado
              faixaErrors.push(
                `Sobreposição: Faixa ${i + 2} começa antes do fim desta faixa`
              );
            }
          }
        }
      }
      
      // Validar taxa
      if (faixa.taxa_comissao_pct < 0 || faixa.taxa_comissao_pct > 100) {
        faixaErrors.push('Taxa deve estar entre 0% e 100%');
      }
      
      errors.push(faixaErrors);
    }
    
    return errors;
  }, [faixas]);

  // Verificar se há algum erro
  const hasErrors = validationErrors.some(e => e.length > 0);

  // ==================== HANDLERS ====================
  
  // Atualizar campo de uma faixa
  const handleFaixaChange = (index, campo, valorString) => {
    const novasFaixas = [...faixas];
    
    if (campo === 'taxa_comissao_pct') {
      // Taxa aceita decimais
      const valor = parseFloat(valorString) || 0;
      novasFaixas[index] = { ...novasFaixas[index], [campo]: valor };
    } else {
      // Limites monetários
      const valor = parseFormattedValue(valorString);
      novasFaixas[index] = { ...novasFaixas[index], [campo]: valor };
    }
    
    onChange(novasFaixas);
  };

  // Definir limite superior como infinito (null)
  const handleSetInfinito = (index) => {
    const novasFaixas = [...faixas];
    novasFaixas[index] = { ...novasFaixas[index], limite_superior: null };
    onChange(novasFaixas);
  };

  // Adicionar nova faixa
  const handleAddFaixa = () => {
    if (faixas.length >= maxFaixas) return;
    
    // Calcular início da nova faixa baseado no fim da última
    let novoInicio = 0;
    if (faixas.length > 0) {
      const ultimaFaixa = faixas[faixas.length - 1];
      if (ultimaFaixa.limite_superior !== null) {
        novoInicio = ultimaFaixa.limite_superior + 0.01;
      } else {
        // Se última faixa é infinita, definir um limite e criar nova
        novoInicio = ultimaFaixa.limite_inferior + 50000;
      }
    }
    
    const novaFaixa = {
      limite_inferior: novoInicio,
      limite_superior: null, // Última faixa sempre infinita por padrão
      taxa_comissao_pct: faixas.length > 0 ? faixas[faixas.length - 1].taxa_comissao_pct + 0.5 : 1,
    };
    
    // Se já existia uma faixa infinita, dar um limite a ela
    const novasFaixas = [...faixas];
    if (novasFaixas.length > 0 && novasFaixas[novasFaixas.length - 1].limite_superior === null) {
      novasFaixas[novasFaixas.length - 1] = {
        ...novasFaixas[novasFaixas.length - 1],
        limite_superior: novoInicio - 0.01,
      };
    }
    
    novasFaixas.push(novaFaixa);
    onChange(novasFaixas);
  };

  // Remover faixa
  const handleRemoveFaixa = (index) => {
    if (faixas.length <= 1) return;
    
    const novasFaixas = faixas.filter((_, i) => i !== index);
    
    // Se removeu a última e a nova última tem limite, torná-la infinita
    if (index === faixas.length - 1 && novasFaixas.length > 0) {
      novasFaixas[novasFaixas.length - 1] = {
        ...novasFaixas[novasFaixas.length - 1],
        limite_superior: null,
      };
    }
    
    onChange(novasFaixas);
  };

  // Auto-ajustar gaps (conectar faixas automaticamente)
  const handleAutoAjustar = () => {
    if (faixas.length < 2) return;
    
    const novasFaixas = faixas.map((faixa, index) => {
      if (index < faixas.length - 1) {
        // Todas exceto a última: limite_superior = próxima.limite_inferior - 0.01
        return {
          ...faixa,
          limite_superior: faixas[index + 1].limite_inferior - 0.01,
        };
      }
      // Última faixa: manter infinita
      return { ...faixa, limite_superior: null };
    });
    
    onChange(novasFaixas);
  };

  // ==================== RENDER ====================

  return (
    <div className="faixas-comissao-editor">
      {/* Validação Global */}
      {hasErrors && (
        <div className="faixas-validation-warning">
          <span className="warning-icon">⚠️</span>
          <span>Existem problemas nas faixas. Verifique os campos destacados.</span>
          <button 
            type="button" 
            className="btn-auto-ajustar"
            onClick={handleAutoAjustar}
          >
            Auto-ajustar
          </button>
        </div>
      )}

      {!hasErrors && faixas.length > 1 && (
        <div className="faixas-validation-success">
          <span className="success-icon">✓</span>
          <span>Faixas contíguas - sem gaps ou sobreposições</span>
        </div>
      )}

      {/* Tabela de Faixas */}
      <div className="faixas-table">
        {/* Header */}
        <div className="faixas-row faixas-header">
          <div className="faixa-col col-numero">#</div>
          <div className="faixa-col col-de">De (R$)</div>
          <div className="faixa-col col-ate">Até (R$)</div>
          <div className="faixa-col col-taxa">Taxa (%)</div>
          <div className="faixa-col col-actions"></div>
        </div>

        {/* Faixas */}
        {faixas.map((faixa, index) => {
          const faixaErrors = validationErrors[index] || [];
          const hasError = faixaErrors.length > 0;
          const isLast = index === faixas.length - 1;
          
          return (
            <div key={index} className={`faixas-row ${hasError ? 'row-error' : ''}`}>
              {/* Número */}
              <div className="faixa-col col-numero">
                <span className="faixa-numero">{index + 1}</span>
              </div>
              
              {/* De (R$) */}
              <div className="faixa-col col-de">
                <div className="input-wrapper">
                  <span className="input-prefix">R$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={faixa.limite_inferior || 0}
                    onChange={(e) => {
                      const valor = parseFloat(e.target.value) || 0;
                      const novasFaixas = [...faixas];
                      novasFaixas[index] = { ...novasFaixas[index], limite_inferior: valor };
                      onChange(novasFaixas);
                    }}
                    className={`limite-input ${hasError ? 'input-error' : ''}`}
                    placeholder="0,00"
                  />
                </div>
              </div>
              
              {/* Até (R$) */}
              <div className="faixa-col col-ate">
                {faixa.limite_superior === null ? (
                  <div className="infinito-display">
                    <span className="infinito-symbol">∞</span>
                    <span className="infinito-label">Sem limite</span>
                    {!isLast && (
                      <button
                        type="button"
                        className="btn-definir-limite"
                        onClick={() => {
                          const novoLimite = faixa.limite_inferior + 50000;
                          handleFaixaChange(index, 'limite_superior', novoLimite.toString());
                        }}
                      >
                        Definir
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="input-wrapper">
                    <span className="input-prefix">R$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={faixa.limite_superior || 0}
                      onChange={(e) => {
                        const valor = parseFloat(e.target.value) || 0;
                        const novasFaixas = [...faixas];
                        novasFaixas[index] = { ...novasFaixas[index], limite_superior: valor };
                        onChange(novasFaixas);
                      }}
                      className={`limite-input ${hasError ? 'input-error' : ''}`}
                      placeholder="0,00"
                    />
                    {isLast && (
                      <button
                        type="button"
                        className="btn-infinito"
                        onClick={() => handleSetInfinito(index)}
                        title="Definir como sem limite"
                      >
                        ∞
                      </button>
                    )}
                  </div>
                )}
              </div>
              
              {/* Taxa (%) */}
              <div className="faixa-col col-taxa">
                <input
                  type="number"
                  value={faixa.taxa_comissao_pct}
                  onChange={(e) => handleFaixaChange(index, 'taxa_comissao_pct', e.target.value)}
                  min="0"
                  max="100"
                  step="0.1"
                  className="taxa-input"
                />
                <span className="taxa-suffix">%</span>
              </div>
              
              {/* Ações */}
              <div className="faixa-col col-actions">
                {faixas.length > 1 && (
                  <button
                    type="button"
                    className="btn-remove-faixa"
                    onClick={() => handleRemoveFaixa(index)}
                    title="Remover faixa"
                  >
                    ✕
                  </button>
                )}
              </div>
              
              {/* Preview da faixa */}
              <div className="faixa-preview-row">
                <span className="preview-text">
                  {formatCurrency(faixa.limite_inferior)} até {formatCurrency(faixa.limite_superior)} → {faixa.taxa_comissao_pct}%
                </span>
              </div>
              
              {/* Erros da faixa */}
              {hasError && (
                <div className="faixa-errors">
                  {faixaErrors.map((err, errIdx) => (
                    <div key={errIdx} className="error-message">
                      <span className="error-icon">!</span>
                      {err}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Botão adicionar */}
      {faixas.length < maxFaixas && (
        <button
          type="button"
          className="btn-add-faixa"
          onClick={handleAddFaixa}
        >
          + Adicionar Faixa ({faixas.length}/{maxFaixas})
        </button>
      )}

      {/* Aviso de limite máximo */}
      {faixas.length >= maxFaixas && (
        <div className="faixas-max-warning">
          Limite máximo de {maxFaixas} faixas atingido
        </div>
      )}
    </div>
  );
};

export default FaixasComissaoEditor;
