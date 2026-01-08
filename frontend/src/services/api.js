import axios from 'axios';

// Usar URL relativa para que o proxy do React funcione
// O setupProxy.js redireciona as requisições para http://localhost:8000
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de requisição para logs
api.interceptors.request.use(
  (config) => {
    console.log('[API] Requisição iniciada', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout,
      timestamp: new Date().toISOString(),
    });
    return config;
  },
  (error) => {
    console.error('[API] Erro na configuração da requisição', error);
    return Promise.reject(error);
  }
);

// Interceptor de resposta para logs e tratamento de erros
api.interceptors.response.use(
  (response) => {
    console.log('[API] Resposta recebida', {
      status: response.status,
      url: response.config.url,
      elapsed: response.config.metadata?.startTime
        ? `${((Date.now() - response.config.metadata.startTime) / 1000).toFixed(1)}s`
        : 'N/A',
      dataType: typeof response.data,
      dataLength: Array.isArray(response.data) ? response.data.length : 'N/A',
    });
    return response;
  },
  (error) => {
    const elapsed = error.config?.metadata?.startTime
      ? `${((Date.now() - error.config.metadata.startTime) / 1000).toFixed(1)}s`
      : 'N/A';

    console.error('[API] Erro na resposta', {
      url: error.config?.url,
      elapsed,
      errorName: error.name,
      errorMessage: error.message,
      errorCode: error.code,
      hasResponse: !!error.response,
      hasRequest: !!error.request,
      responseStatus: error.response?.status,
      responseData: error.response?.data,
    });

    const wrapAndReject = (message) => {
      const wrapped = new Error(message);
      // Preservar contexto do Axios para debug no frontend.
      wrapped.cause = error;
      wrapped.config = error.config;
      wrapped.request = error.request;
      wrapped.response = error.response;
      wrapped.code = error.code;
      wrapped.isAxiosError = error.isAxiosError;
      return Promise.reject(wrapped);
    };

    if (error.response) {
      // Erro da API
      const message = error.response.data?.detail || error.response.data?.message || 'Erro desconhecido';
      return wrapAndReject(message);
    }
    if (error.request) {
      // Erro de rede ou timeout
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        return wrapAndReject('Timeout: A requisição demorou muito para responder. Tente novamente.');
      }
      return wrapAndReject('Erro de conexão. Verifique se o servidor está rodando.');
    }
    return Promise.reject(error);
  }
);

// Adicionar timestamp às requisições para cálculo de tempo decorrido
api.interceptors.request.use((config) => {
  config.metadata = { startTime: Date.now() };
  return config;
});

// ==================== REGRAS ====================

export const regrasAPI = {
  listarAbas: () => api.get('/regras/abas'),

  lerAba: (nomeAba, params = {}) => {
    const { page = 1, size = 20, sortBy, sortOrder, filters, allPages = false } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (sortBy) {
      queryParams.append('sort_by', sortBy);
      queryParams.append('sort_order', sortOrder || 'asc');
    }
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }
    if (allPages) {
      queryParams.append('all_pages', 'true');
    }
    return api.get(`/regras/aba/${nomeAba}?${queryParams}`);
  },

  obterValoresUnicos: (nomeAba, coluna) =>
    api.get(`/regras/aba/${nomeAba}/valores-unicos/${coluna}`),

  salvarAba: (nomeAba, data, preserveColumns = true) =>
    api.post(`/regras/aba/${nomeAba}/save`, {
      data,
      preserve_columns: preserveColumns,
    }),

  aplicarMassa: (nomeAba, request) =>
    api.post(`/regras/aba/${nomeAba}/apply-bulk`, request),

  // ===== Metas de Aplicação - Aplicação em Massa =====
  metasAplicacaoHierarchyOptions: () =>
    api.post('/api/metas-aplicacao/hierarchy-options'),

  metasAplicacaoFilteredOptions: (escopo) =>
    api.post('/api/metas-aplicacao/filtered-options', escopo),

  metasAplicacaoHierarchyCombinations: (escopo) =>
    api.post('/api/metas-aplicacao/hierarchy-combinations', escopo),

  metasAplicacaoBulkApply: (request) =>
    api.post('/api/metas-aplicacao/bulk-apply', request),

  // ===== Gerenciamento de Regras =====
  getPesosMetas: () => api.get('/api/regras/pesos-metas'),
  updatePesosMetas: (data) => api.post('/api/regras/pesos-metas', data),

  getRuleContextOptions: () => api.get('/api/regras/config-comissao/context-options'),
  getConfigComissao: (filters) => api.post('/api/regras/config-comissao/query', filters || {}),
  updateConfigComissaoInLine: (rowData) => api.put('/api/regras/config-comissao/update-line', rowData),
  dryRunConfigComissao: (batchData) => api.post('/api/regras/config-comissao/dry-run', batchData),
  applyBatchConfigComissao: (batchData) => api.post('/api/regras/config-comissao/apply-batch', batchData),
  validateConfigComissaoPE: (contexto) => api.post('/api/regras/config-comissao/validate-pe', contexto),
};

// ==================== UPLOADS ====================

export const uploadAPI = {
  analiseComercial: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/analise', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  analiseFinanceira: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/analise_financeira', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  devolucoes: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/devolucoes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // DESABILITADO - Não mais necessário no novo robô
  // finAdcli: (file) => {
  //   const formData = new FormData();
  //   formData.append('file', file);
  //   return api.post('/upload/fin_adcli', formData, {
  //     headers: { 'Content-Type': 'multipart/form-data' },
  //   });
  // },
  //
  // finConci: (file) => {
  //   const formData = new FormData();
  //   formData.append('file', file);
  //   return api.post('/upload/fin_conci', formData, {
  //     headers: { 'Content-Type': 'multipart/form-data' },
  //   });
  // },
};

// ==================== EXECUÇÃO ====================

export const execucaoAPI = {
  iniciar: (mes, ano) => api.post(`/calcular?mes=${mes}&ano=${ano}`),

  consultarProgresso: (jobId) => api.get(`/progresso/${jobId}`),
};

// ==================== EXECUÇÃO (Pré-Scan + Execução com Decisões) ====================

export const execucaoAPI2 = {
  executarPreScanCrossSelling: (mes, ano) =>
    api.post('/api/executar-prescan', { mes, ano }, {
      timeout: 600000, // 10 minutos de timeout para pré-scan (dados volumosos)
    }),
  executarCalculo: (mes, ano, decisoes, opcoes = {}) =>
    api.post('/api/executar-calculo', {
      mes,
      ano,
      decisoes_cross_selling: decisoes || [],
      limpar_historico_master: !!opcoes.limparHistoricoMaster,
      limpar_estado_processos_recebimento: !!opcoes.limparEstadoProcessosRecebimento,
    }, {
      timeout: 600000, // 10 minutos de timeout para cálculo completo
    }),
};

// ==================== RESULTADOS ====================

export const resultadosAPI = {
  listarAbas: () => api.get('/resultado/abas'),

  lerAba: (nomeAba, params = {}) => {
    const { page = 1, size = 20, sortBy, sortOrder, filters } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (sortBy) {
      queryParams.append('sort_by', sortBy);
      queryParams.append('sort_order', sortOrder || 'asc');
    }
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }
    return api.get(`/resultado/aba/${nomeAba}?${queryParams}`);
  },

  obterValoresUnicos: (nomeAba, coluna) =>
    api.get(`/resultado/aba/${nomeAba}/valores-unicos/${coluna}`),

  baixar: () => api.get('/baixar/resultado', { responseType: 'blob' }),
};

// ==================== HEALTH ====================

export const healthAPI = {
  check: () => api.get('/health'),
};

// ==================== DEBUG ====================

export const debugAPI = {
  getLogs: (lines = 400) => api.get(`/debug/logs?lines=${lines}`, { responseType: 'text' }),
};

// ==================== TAXAS DE CÂMBIO ====================

export const cambioAPI = {
  getTaxas: () => api.get('/api/taxas-cambio'),
};

// ==================== RECEBIMENTO ====================

export const recebimentoAPI = {
  // ==================== MÉTODOS NOVOS (Minimalista) ====================
  /**
   * Obtém lista de pagamentos do mês/ano (snapshot do mês selecionado).
   * Retorna adiantamentos + regulares em uma lista flat.
   */
  getPagamentos: (mes, ano, filtros = {}) => {
    const params = new URLSearchParams({ mes, ano, ...filtros });
    return api.get(`/resultado/recebimento/pagamentos?${params.toString()}`);
  },
  
  /**
   * Obtém detalhes completos do cálculo de um pagamento específico.
   * Inclui breakdown de TCMP (por item) e FCMP (por item, com metas).
   */
  getDetalhesPagamento: (id) => 
    api.get(`/resultado/recebimento/pagamento/${id}/detalhes`),

  /**
   * Obtém auditoria completa do processo (todos os colaboradores), agrupada por item.
   */
  getAuditoriaProcesso: (processo) =>
    api.get(`/resultado/recebimento/processo/${encodeURIComponent(processo)}/auditoria`),
  
  /**
   * Download do Excel de recebimentos do mês/ano.
   */
  baixarExcel: (mes, ano) => 
    api.get(`/baixar/recebimento?mes=${mes}&ano=${ano}`, { responseType: 'blob' }),
  
  // ==================== MÉTODOS ANTIGOS (Legacy - manter compatibilidade) ====================
  listarAbas: (mes, ano) => api.get(`/resultado/recebimento/abas?mes=${mes}&ano=${ano}`),
  
  lerAba: (nomeAba, mes, ano, params = {}) => {
    const { page = 1, size = 20 } = params;
    return api.get(`/resultado/recebimento/aba/${nomeAba}?mes=${mes}&ano=${ano}&page=${page}&size=${size}`);
  },
  
  obterDetalhes: (processo, colaborador, mes, ano) => 
    api.get(`/resultado/recebimento/detalhes?processo=${processo}&colaborador=${colaborador}&mes=${mes}&ano=${ano}`),
  
  baixar: (mes, ano) => api.get(`/baixar/recebimento?mes=${mes}&ano=${ano}`, { responseType: 'blob' }),
};

// ==================== MONITORAMENTO (Estado de Processos) ====================

export const monitorAPI = {
  /**
   * Retorna o estado raw (todas as colunas) de todos os processos.
   * Ideal para visualização completa do arquivo Estado_Processos_Recebimento.
   * @param {Object} params - Parâmetros de filtro
   * @param {string} params.busca - Busca por texto em processo ou colaborador
   * @param {string} params.statusProcesso - Filtrar por status do processo
   * @param {string} params.statusPagamento - Filtrar por status de pagamento
   * @param {string} params.statusCalculo - Filtrar por status de cálculo de médias
   */
  getEstadoRaw: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.busca) {
      queryParams.append('busca', params.busca);
    }
    if (params.statusProcesso) {
      queryParams.append('status_processo', params.statusProcesso);
    }
    if (params.statusPagamento) {
      queryParams.append('status_pagamento', params.statusPagamento);
    }
    if (params.statusCalculo) {
      queryParams.append('status_calculo', params.statusCalculo);
    }
    const queryString = queryParams.toString();
    return api.get(`/api/monitor/estado-raw${queryString ? `?${queryString}` : ''}`);
  },
};

// ==================== HISTÓRICO (MASTER DB) ====================

export const historicoAPI = {
  getUltimoPeriodoExecutado: () => api.get('/api/execucao/ultimo-periodo'),

  getMaster: (params = {}) => {
    const {
      mes,
      ano,
      tipo_comissao,
      nome_colaborador,
      processo,
      page = 1,
      size = 50,
      sort_by,
      sort_order,
    } = params;

    const queryParams = new URLSearchParams();
    if (mes) queryParams.append('mes', String(mes));
    if (ano) queryParams.append('ano', String(ano));
    if (tipo_comissao) queryParams.append('tipo_comissao', tipo_comissao);
    if (nome_colaborador) queryParams.append('nome_colaborador', nome_colaborador);
    if (processo) queryParams.append('processo', processo);
    queryParams.append('page', String(page));
    queryParams.append('size', String(size));
    if (sort_by) queryParams.append('sort_by', sort_by);
    if (sort_order) queryParams.append('sort_order', sort_order);

    return api.get(`/api/historico/master?${queryParams.toString()}`);
  },

  getSaldosNegativos: (mes, ano, origem = 'ALL', size_itens = 2000) => {
    const queryParams = new URLSearchParams({
      mes: String(mes),
      ano: String(ano),
      origem: String(origem),
      size_itens: String(size_itens),
    });
    return api.get(`/api/historico/saldos-negativos?${queryParams.toString()}`);
  },

  getResumoFinalColaboradores: (mes, ano) => {
    const queryParams = new URLSearchParams({ mes: String(mes), ano: String(ano) });
    return api.get(`/api/historico/resumo-final-colaboradores?${queryParams.toString()}`);
  },

  getResumoFinalColaboradorDetalhes: (mes, ano, nome_colaborador) => {
    const queryParams = new URLSearchParams({
      mes: String(mes),
      ano: String(ano),
      nome_colaborador: String(nome_colaborador),
    });
    return api.get(`/api/historico/resumo-final-colaborador/detalhes?${queryParams.toString()}`);
  },

  getProcessoItens: (processo) => {
    const queryParams = new URLSearchParams({ processo: String(processo) });
    return api.get(`/api/historico/processo-itens?${queryParams.toString()}`);
  },
};

export default api;



// ==================== DADOS DE ENTRADA ====================

export const dadosEntradaAPI = {
  listarArquivos: () => api.get('/dados-entrada/arquivos'),
  
  lerArquivo: (nomeArquivo, params = {}) => {
    const { page = 1, size = 20, sortBy, sortOrder, filters, allPages = false } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (sortBy) {
      queryParams.append('sort_by', sortBy);
      queryParams.append('sort_order', sortOrder || 'asc');
    }
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }
    if (allPages) {
      queryParams.append('all_pages', 'true');
    }
    return api.get(`/dados-entrada/arquivo/${nomeArquivo}?${queryParams.toString()}`);
  },
  
  salvarArquivo: (nomeArquivo, dados) => api.post(`/dados-entrada/arquivo/${nomeArquivo}`, { dados }),
  
  // Rentabilidades (subpasta)
  listarRentabilidades: () => api.get('/dados-entrada/rentabilidades'),
  
  lerRentabilidade: (nomeArquivo, params = {}) => {
    const { page = 1, size = 20, sortBy, sortOrder, filters, allPages = false } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (sortBy) {
      queryParams.append('sort_by', sortBy);
      queryParams.append('sort_order', sortOrder || 'asc');
    }
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }
    if (allPages) {
      queryParams.append('all_pages', 'true');
    }
    return api.get(`/dados-entrada/rentabilidades/${nomeArquivo}?${queryParams.toString()}`);
  },
  
  salvarRentabilidade: (nomeArquivo, dados) => 
    api.post(`/dados-entrada/rentabilidades/${nomeArquivo}`, { dados }),
};
