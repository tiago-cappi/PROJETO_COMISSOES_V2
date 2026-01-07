const normalize = (v) => String(v ?? '').trim();

const toNumber = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

/**
 * Agrupa linhas de COMISSOES_CALCULADAS no formato:
 * Processo -> Itens (por cod_produto) -> Colaboradores (linhas originais).
 *
 * Importante: cod_produto é o identificador do Item (conforme regra do negócio).
 *
 * @param {Array<object>} rawRows
 * @returns {Array<object>} processos
 */
export const groupFaturamentoByProcessoItemColaborador = (rawRows = []) => {
  const processMap = new Map();

  for (const row of rawRows) {
    const processo = normalize(row.processo);
    if (!processo) continue;

    if (!processMap.has(processo)) {
      processMap.set(processo, {
        key: processo,
        processo,
        items: [],
        total_faturado_processo: 0,
        comissao_total_processo: 0,
        total_itens: 0,
        total_colaboradores: 0,
      });
    }

    const processoEntry = processMap.get(processo);

    const codProduto = normalize(row.cod_produto);
    // Fallback caso o arquivo venha sem cod_produto (não esperado, mas evita quebra)
    const fallbackKey = `${normalize(row.descricao_produto)}|${normalize(row.subgrupo)}|${normalize(row.grupo)}|${toNumber(row.faturamento_item)}`;
    const itemKey = codProduto || fallbackKey;

    if (!processoEntry.__itemMap) {
      processoEntry.__itemMap = new Map();
      processoEntry.__colabSet = new Set();
    }

    if (!processoEntry.__itemMap.has(itemKey)) {
      processoEntry.__itemMap.set(itemKey, {
        key: `${processo}-${itemKey}`,
        processo,
        cod_produto: codProduto || null,
        descricao_produto: row.descricao_produto,
        linha: row.linha,
        grupo: row.grupo,
        subgrupo: row.subgrupo,
        tipo_mercadoria: row.tipo_mercadoria,
        faturamento_item: toNumber(row.faturamento_item),
        comissao_total_item: 0,
        colaboradores: [],
      });
    }

    const itemEntry = processoEntry.__itemMap.get(itemKey);
    itemEntry.colaboradores.push({ ...row });

    const nomeColab = normalize(row.nome_colaborador || row.id_colaborador);
    if (nomeColab) {
      processoEntry.__colabSet.add(nomeColab);
    }
  }

  const processos = [];

  for (const processoEntry of processMap.values()) {
    const items = Array.from(processoEntry.__itemMap.values());

    for (const item of items) {
      item.comissao_total_item = item.colaboradores.reduce(
        (acc, r) => acc + toNumber(r.comissao_calculada),
        0
      );

      // Alguns arquivos podem repetir faturamento_item por colaborador.
      // Mantemos o valor do item como o maior não-zero visto.
      const maxFat = item.colaboradores.reduce(
        (acc, r) => Math.max(acc, toNumber(r.faturamento_item)),
        item.faturamento_item
      );
      item.faturamento_item = maxFat;
    }

    processoEntry.items = items;
    processoEntry.total_itens = items.length;
    processoEntry.total_colaboradores = processoEntry.__colabSet.size;

    processoEntry.total_faturado_processo = items.reduce(
      (acc, it) => acc + toNumber(it.faturamento_item),
      0
    );

    processoEntry.comissao_total_processo = items.reduce(
      (acc, it) => acc + toNumber(it.comissao_total_item),
      0
    );

    delete processoEntry.__itemMap;
    delete processoEntry.__colabSet;

    processos.push(processoEntry);
  }

  return processos;
};

export const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};
