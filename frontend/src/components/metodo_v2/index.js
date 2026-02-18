// Componentes da Metodologia V2

// =====================================================
// NOVA ARQUITETURA V2: Colaboradores + Regras + Faixas
// =====================================================

// Card principal de colaborador (exibe nome, cargo, lista de regras)
export { default as ColaboradorConfigCard } from './ColaboradorConfigCard';

// Editor de uma regra de comissão (filtros hierárquicos + faixas)
export { default as RegraComissaoEditor } from './RegraComissaoEditor';

// Editor de faixas de comissão (limite_inferior + taxa%)
export { default as FaixasComissaoEditor } from './FaixasComissaoEditor';

// =====================================================
// Componentes de estrutura organizacional V2
// =====================================================
export { default as HierarquiaEditorV2_Metodo } from './HierarquiaEditorV2_Metodo';
export { default as ColaboradoresCargosEditorV2_Metodo } from './ColaboradoresCargosEditorV2_Metodo';

// =====================================================
// Componentes de RESULTADOS V2
// =====================================================
export { default as ResultadosV2Tab } from './ResultadosV2Tab';
export { default as DetalhesColaboradorV2Modal } from './DetalhesColaboradorV2Modal';

// =====================================================
// Componentes de CENTRO DE CUSTO V2
// =====================================================
export { default as RegrasCCEditorV2 } from './RegrasCCEditorV2';

// =====================================================
// COMPONENTES OBSOLETOS (manter temporariamente para compatibilidade)
// =====================================================
export { default as AplicacoesSelector } from './AplicacoesSelector';
export { default as DegrausEditor } from './DegrausEditor';
export { default as ColaboradorMetaCard } from './ColaboradorMetaCard';
