"""
Script de diagnóstico para verificar o cálculo do Fator de Correção (FC) de rentabilidade.

Este script verifica:
1. Se o arquivo de rentabilidade realizada foi carregado corretamente
2. Se as chaves (linha, grupo, subgrupo, tipo_mercadoria) correspondem entre dados e metas
3. Se as metas de rentabilidade estão configuradas corretamente
4. Se há problemas de normalização ou correspondência de valores
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Adicionar raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.io.config_loader import ConfigLoader
from src.io.data_loader import DataLoader
from src.utils.logging import ValidationLogger


def _normalize_text(s):
    """Normaliza texto para comparação."""
    if pd.isna(s):
        return ""
    s = str(s).strip().upper()
    return " ".join(s.split())


def verificar_arquivo_rentabilidade(mes: int, ano: int, base_path: str = ".") -> Tuple[bool, pd.DataFrame, str]:
    """
    Verifica se o arquivo de rentabilidade existe e pode ser carregado.
    
    Returns:
        (sucesso, dataframe, mensagem)
    """
    data_loader = DataLoader()
    
    # Tentar carregar rentabilidade
    df_rent = data_loader.load_rentabilidade(mes, ano, base_path)
    
    if df_rent.empty:
        return False, pd.DataFrame(), "Arquivo de rentabilidade não encontrado ou vazio"
    
    # Verificar colunas esperadas
    colunas_esperadas = ["Negócio", "Grupo", "Subgrupo", "Tipo de Mercadoria", "rentabilidade_realizada_pct"]
    colunas_faltantes = [c for c in colunas_esperadas if c not in df_rent.columns]
    
    if colunas_faltantes:
        return False, df_rent, f"Colunas faltantes no arquivo de rentabilidade: {colunas_faltantes}"
    
    return True, df_rent, "Arquivo de rentabilidade carregado com sucesso"


def verificar_meta_rentabilidade(base_path: str = ".") -> Tuple[bool, pd.DataFrame, str]:
    """
    Verifica se o arquivo de meta de rentabilidade existe e pode ser carregado.
    
    Returns:
        (sucesso, dataframe, mensagem)
    """
    config_loader = ConfigLoader()
    config_path = os.path.join("config", "Regras_Comissoes.xlsx")
    if not os.path.exists(config_path):
        config_path = "Regras_Comissoes.xlsx"
    
    configs = config_loader.load_configs(config_path)
    
    if "META_RENTABILIDADE" not in configs:
        return False, pd.DataFrame(), "META_RENTABILIDADE não encontrada nas configurações"
    
    df_meta = configs["META_RENTABILIDADE"]
    
    if df_meta.empty:
        return False, df_meta, "META_RENTABILIDADE está vazia"
    
    # Verificar colunas esperadas
    colunas_esperadas = ["linha", "grupo", "subgrupo", "tipo_mercadoria", "meta_rentabilidade_alvo_pct"]
    colunas_faltantes = [c for c in colunas_esperadas if c not in df_meta.columns]
    
    if colunas_faltantes:
        return False, df_meta, f"Colunas faltantes em META_RENTABILIDADE: {colunas_faltantes}"
    
    return True, df_meta, "META_RENTABILIDADE carregada com sucesso"


def verificar_correspondencia_chaves(
    df_rent: pd.DataFrame, df_meta: pd.DataFrame
) -> Dict[str, any]:
    """
    Verifica se as chaves (linha, grupo, subgrupo, tipo_mercadoria) correspondem
    entre rentabilidade realizada e metas.
    
    Returns:
        Dicionário com estatísticas de correspondência
    """
    resultado = {
        "total_rentabilidade": len(df_rent),
        "total_metas": len(df_meta),
        "chaves_rentabilidade": set(),
        "chaves_metas": set(),
        "chaves_em_ambos": set(),
        "chaves_apenas_rentabilidade": set(),
        "chaves_apenas_metas": set(),
        "exemplos_sem_correspondencia": [],
    }
    
    # Normalizar e criar chaves de rentabilidade
    if not df_rent.empty:
        df_rent_norm = df_rent.copy()
        df_rent_norm["linha"] = df_rent_norm["Negócio"].apply(_normalize_text)
        df_rent_norm["grupo_norm"] = df_rent_norm["Grupo"].apply(_normalize_text)
        df_rent_norm["subgrupo_norm"] = df_rent_norm["Subgrupo"].apply(_normalize_text)
        df_rent_norm["tipo_norm"] = df_rent_norm["Tipo de Mercadoria"].apply(_normalize_text)
        
        for _, row in df_rent_norm.iterrows():
            chave = (
                row["linha"],
                row["grupo_norm"],
                row["subgrupo_norm"],
                row["tipo_norm"],
            )
            resultado["chaves_rentabilidade"].add(chave)
    
    # Normalizar e criar chaves de metas
    if not df_meta.empty:
        df_meta_norm = df_meta.copy()
        df_meta_norm["linha_norm"] = df_meta_norm["linha"].apply(_normalize_text)
        df_meta_norm["grupo_norm"] = df_meta_norm["grupo"].apply(_normalize_text)
        df_meta_norm["subgrupo_norm"] = df_meta_norm["subgrupo"].apply(_normalize_text)
        df_meta_norm["tipo_norm"] = df_meta_norm["tipo_mercadoria"].apply(_normalize_text)
        
        for _, row in df_meta_norm.iterrows():
            chave = (
                row["linha_norm"],
                row["grupo_norm"],
                row["subgrupo_norm"],
                row["tipo_norm"],
            )
            resultado["chaves_metas"].add(chave)
    
    # Comparar chaves
    resultado["chaves_em_ambos"] = resultado["chaves_rentabilidade"] & resultado["chaves_metas"]
    resultado["chaves_apenas_rentabilidade"] = resultado["chaves_rentabilidade"] - resultado["chaves_metas"]
    resultado["chaves_apenas_metas"] = resultado["chaves_metas"] - resultado["chaves_rentabilidade"]
    
    # Coletar exemplos de chaves sem correspondência (até 10)
    for chave in list(resultado["chaves_apenas_rentabilidade"])[:10]:
        # Encontrar linha original
        linha_orig = next(
            (
                (row["Negócio"], row["Grupo"], row["Subgrupo"], row["Tipo de Mercadoria"])
                for _, row in df_rent_norm.iterrows()
                if (
                    _normalize_text(row["Negócio"]),
                    _normalize_text(row["Grupo"]),
                    _normalize_text(row["Subgrupo"]),
                    _normalize_text(row["Tipo de Mercadoria"]),
                )
                == chave
            ),
            None,
        )
        if linha_orig:
            resultado["exemplos_sem_correspondencia"].append(
                {
                    "chave_normalizada": chave,
                    "valores_originais": linha_orig,
                    "tipo": "apenas_rentabilidade",
                }
            )
    
    return resultado


def verificar_processamento_realizado(df_rent: pd.DataFrame) -> Dict[str, any]:
    """
    Verifica como o DataFrame de rentabilidade seria processado em _calcular_realizado.
    
    Returns:
        Dicionário com informações sobre o processamento
    """
    resultado = {
        "sucesso": False,
        "erro": None,
        "total_linhas": len(df_rent),
        "series_criada": False,
        "total_indices": 0,
        "exemplos_indices": [],
        "valores_nulos": 0,
        "valores_invalidos": 0,
    }
    
    try:
        # Simular processamento como em _calcular_realizado
        rent_realizada = df_rent.rename(columns={"Negócio": "linha"})
        
        # Verificar se todas as colunas necessárias existem
        colunas_indice = ["linha", "Grupo", "Subgrupo", "Tipo de Mercadoria"]
        if not all(c in rent_realizada.columns for c in colunas_indice):
            resultado["erro"] = f"Colunas faltantes para índice: {colunas_indice}"
            return resultado
        
        # Verificar se há valores nulos nas colunas de índice
        nulos_por_coluna = rent_realizada[colunas_indice].isnull().sum()
        if nulos_por_coluna.any():
            resultado["erro"] = f"Valores nulos nas colunas de índice: {nulos_por_coluna.to_dict()}"
            return resultado
        
        # Criar índice
        series_rent = rent_realizada.set_index(colunas_indice)["rentabilidade_realizada_pct"]
        resultado["series_criada"] = True
        resultado["total_indices"] = len(series_rent)
        
        # Coletar exemplos de índices (até 10)
        for idx in list(series_rent.index)[:10]:
            resultado["exemplos_indices"].append(
                {
                    "indice": idx,
                    "valor": series_rent[idx],
                    "tipo_valor": type(series_rent[idx]).__name__,
                }
            )
        
        # Verificar valores nulos ou inválidos
        resultado["valores_nulos"] = series_rent.isnull().sum()
        resultado["valores_invalidos"] = (
            pd.to_numeric(series_rent, errors="coerce").isnull().sum()
            - resultado["valores_nulos"]
        )
        
        resultado["sucesso"] = True
        
    except Exception as e:
        resultado["erro"] = str(e)
    
    return resultado


def verificar_busca_meta(chave: Tuple, df_meta: pd.DataFrame) -> Dict[str, any]:
    """
    Simula a busca de meta como em _get_meta para uma chave específica.
    
    Args:
        chave: Tupla (linha, grupo, subgrupo, tipo_mercadoria)
        df_meta: DataFrame de META_RENTABILIDADE
    
    Returns:
        Dicionário com resultado da busca
    """
    resultado = {
        "encontrada": False,
        "valor": None,
        "erro": None,
        "linhas_candidatas": 0,
    }
    
    try:
        linha, grupo, subgrupo, tipo_mercadoria = chave
        
        # Buscar como em _get_meta
        filtro = (
            (df_meta["linha"] == linha)
            & (df_meta["grupo"] == grupo)
            & (df_meta["subgrupo"] == subgrupo)
            & (df_meta["tipo_mercadoria"] == tipo_mercadoria)
        )
        
        candidatos = df_meta[filtro]
        resultado["linhas_candidatas"] = len(candidatos)
        
        if len(candidatos) > 0:
            resultado["encontrada"] = True
            resultado["valor"] = candidatos["meta_rentabilidade_alvo_pct"].iloc[0]
        else:
            resultado["erro"] = "Nenhuma meta encontrada para esta chave"
            
            # Tentar encontrar com normalização
            df_meta_norm = df_meta.copy()
            df_meta_norm["linha_norm"] = df_meta_norm["linha"].apply(_normalize_text)
            df_meta_norm["grupo_norm"] = df_meta_norm["grupo"].apply(_normalize_text)
            df_meta_norm["subgrupo_norm"] = df_meta_norm["subgrupo"].apply(_normalize_text)
            df_meta_norm["tipo_norm"] = df_meta_norm["tipo_mercadoria"].apply(_normalize_text)
            
            filtro_norm = (
                (df_meta_norm["linha_norm"] == _normalize_text(linha))
                & (df_meta_norm["grupo_norm"] == _normalize_text(grupo))
                & (df_meta_norm["subgrupo_norm"] == _normalize_text(subgrupo))
                & (df_meta_norm["tipo_norm"] == _normalize_text(tipo_mercadoria))
            )
            
            candidatos_norm = df_meta_norm[filtro_norm]
            if len(candidatos_norm) > 0:
                resultado["erro"] = "Meta encontrada apenas com normalização (problema de correspondência exata)"
                resultado["valor"] = candidatos_norm["meta_rentabilidade_alvo_pct"].iloc[0]
                resultado["encontrada"] = True
                
    except Exception as e:
        resultado["erro"] = f"Erro ao buscar meta: {e}"
    
    return resultado


def verificar_exemplo_item(
    linha: str, grupo: str, subgrupo: str, tipo_mercadoria: str,
    df_rent: pd.DataFrame, df_meta: pd.DataFrame
) -> Dict[str, any]:
    """
    Verifica um exemplo específico de item para diagnosticar problemas.
    
    Returns:
        Dicionário com diagnóstico completo do item
    """
    resultado = {
        "item": {
            "linha": linha,
            "grupo": grupo,
            "subgrupo": subgrupo,
            "tipo_mercadoria": tipo_mercadoria,
        },
        "rentabilidade_encontrada": False,
        "rentabilidade_valor": None,
        "meta_encontrada": False,
        "meta_valor": None,
        "problemas": [],
    }
    
    # Buscar rentabilidade realizada
    try:
        rent_realizada = df_rent.rename(columns={"Negócio": "linha"})
        series_rent = rent_realizada.set_index(
            ["linha", "Grupo", "Subgrupo", "Tipo de Mercadoria"]
        )["rentabilidade_realizada_pct"]
        
        chave_rent = (linha, grupo, subgrupo, tipo_mercadoria)
        if chave_rent in series_rent.index:
            resultado["rentabilidade_encontrada"] = True
            resultado["rentabilidade_valor"] = series_rent[chave_rent]
        else:
            resultado["problemas"].append(
                f"Rentabilidade não encontrada para chave: {chave_rent}"
            )
            
            # Tentar com normalização
            chave_norm = (
                _normalize_text(linha),
                _normalize_text(grupo),
                _normalize_text(subgrupo),
                _normalize_text(tipo_mercadoria),
            )
            indices_norm = [
                (
                    _normalize_text(str(idx[0])),
                    _normalize_text(str(idx[1])),
                    _normalize_text(str(idx[2])),
                    _normalize_text(str(idx[3])),
                )
                for idx in series_rent.index
            ]
            if chave_norm in indices_norm:
                idx_pos = indices_norm.index(chave_norm)
                resultado["rentabilidade_encontrada"] = True
                resultado["rentabilidade_valor"] = series_rent.iloc[idx_pos]
                resultado["problemas"].append(
                    "Rentabilidade encontrada apenas com normalização (problema de correspondência)"
                )
    except Exception as e:
        resultado["problemas"].append(f"Erro ao buscar rentabilidade: {e}")
    
    # Buscar meta
    resultado_meta = verificar_busca_meta((linha, grupo, subgrupo, tipo_mercadoria), df_meta)
    resultado["meta_encontrada"] = resultado_meta["encontrada"]
    resultado["meta_valor"] = resultado_meta["valor"]
    if resultado_meta["erro"]:
        resultado["problemas"].append(f"Meta: {resultado_meta['erro']}")
    
    return resultado


def gerar_relatorio_completo(mes: int, ano: int, base_path: str = ".") -> str:
    """
    Gera relatório completo de diagnóstico.
    
    Returns:
        String com relatório formatado
    """
    relatorio = []
    relatorio.append("=" * 80)
    relatorio.append("DIAGNÓSTICO DE RENTABILIDADE PARA CÁLCULO DE FC")
    relatorio.append("=" * 80)
    relatorio.append(f"Mês/Ano: {mes:02d}/{ano}")
    relatorio.append("")
    
    # 1. Verificar arquivo de rentabilidade
    relatorio.append("1. VERIFICAÇÃO DO ARQUIVO DE RENTABILIDADE REALIZADA")
    relatorio.append("-" * 80)
    sucesso_rent, df_rent, msg_rent = verificar_arquivo_rentabilidade(mes, ano, base_path)
    if sucesso_rent:
        relatorio.append(f"[OK] {msg_rent}")
        relatorio.append(f"     Total de linhas: {len(df_rent)}")
        relatorio.append(f"     Colunas: {list(df_rent.columns)}")
        if not df_rent.empty:
            relatorio.append(f"     Primeiras linhas:")
            for idx, row in df_rent.head(3).iterrows():
                relatorio.append(
                    f"       - {row.get('Negócio', 'N/A')} | {row.get('Grupo', 'N/A')} | "
                    f"{row.get('Subgrupo', 'N/A')} | {row.get('Tipo de Mercadoria', 'N/A')} | "
                    f"Rent: {row.get('rentabilidade_realizada_pct', 'N/A')}"
                )
    else:
        relatorio.append(f"[ERRO] {msg_rent}")
    relatorio.append("")
    
    # 2. Verificar meta de rentabilidade
    relatorio.append("2. VERIFICAÇÃO DA META DE RENTABILIDADE")
    relatorio.append("-" * 80)
    sucesso_meta, df_meta, msg_meta = verificar_meta_rentabilidade(base_path)
    if sucesso_meta:
        relatorio.append(f"[OK] {msg_meta}")
        relatorio.append(f"     Total de linhas: {len(df_meta)}")
        relatorio.append(f"     Colunas: {list(df_meta.columns)}")
        if not df_meta.empty:
            relatorio.append(f"     Primeiras linhas:")
            for idx, row in df_meta.head(3).iterrows():
                relatorio.append(
                    f"       - {row.get('linha', 'N/A')} | {row.get('grupo', 'N/A')} | "
                    f"{row.get('subgrupo', 'N/A')} | {row.get('tipo_mercadoria', 'N/A')} | "
                    f"Meta: {row.get('meta_rentabilidade_alvo_pct', 'N/A')}"
                )
    else:
        relatorio.append(f"[ERRO] {msg_meta}")
    relatorio.append("")
    
    # 3. Verificar processamento de realizado
    if sucesso_rent:
        relatorio.append("3. VERIFICAÇÃO DO PROCESSAMENTO DE RENTABILIDADE REALIZADA")
        relatorio.append("-" * 80)
        proc_rent = verificar_processamento_realizado(df_rent)
        if proc_rent["sucesso"]:
            relatorio.append("[OK] Processamento bem-sucedido")
            relatorio.append(f"     Total de índices criados: {proc_rent['total_indices']}")
            relatorio.append(f"     Valores nulos: {proc_rent['valores_nulos']}")
            relatorio.append(f"     Valores inválidos: {proc_rent['valores_invalidos']}")
            if proc_rent["exemplos_indices"]:
                relatorio.append("     Exemplos de índices:")
                for ex in proc_rent["exemplos_indices"][:5]:
                    relatorio.append(f"       - {ex['indice']} -> {ex['valor']} ({ex['tipo_valor']})")
        else:
            relatorio.append(f"[ERRO] {proc_rent['erro']}")
        relatorio.append("")
    
    # 4. Verificar correspondência de chaves
    if sucesso_rent and sucesso_meta:
        relatorio.append("4. VERIFICAÇÃO DE CORRESPONDÊNCIA DE CHAVES")
        relatorio.append("-" * 80)
        corresp = verificar_correspondencia_chaves(df_rent, df_meta)
        relatorio.append(f"Total de chaves em rentabilidade: {len(corresp['chaves_rentabilidade'])}")
        relatorio.append(f"Total de chaves em metas: {len(corresp['chaves_metas'])}")
        relatorio.append(f"Chaves presentes em ambos: {len(corresp['chaves_em_ambos'])}")
        relatorio.append(f"Chaves apenas em rentabilidade: {len(corresp['chaves_apenas_rentabilidade'])}")
        relatorio.append(f"Chaves apenas em metas: {len(corresp['chaves_apenas_metas'])}")
        
        if corresp["chaves_apenas_rentabilidade"]:
            relatorio.append("")
            relatorio.append("[AVISO] Chaves em rentabilidade sem meta correspondente:")
            for ex in corresp["exemplos_sem_correspondencia"][:5]:
                relatorio.append(
                    f"       - {ex['valores_originais']} (normalizada: {ex['chave_normalizada']})"
                )
        
        relatorio.append("")
    
    # 5. Verificar exemplo específico (se houver dados)
    if sucesso_rent and not df_rent.empty:
        relatorio.append("5. EXEMPLO DE DIAGNÓSTICO PARA ITEM ESPECÍFICO")
        relatorio.append("-" * 80)
        primeira_linha = df_rent.iloc[0]
        exemplo = verificar_exemplo_item(
            primeira_linha.get("Negócio", ""),
            primeira_linha.get("Grupo", ""),
            primeira_linha.get("Subgrupo", ""),
            primeira_linha.get("Tipo de Mercadoria", ""),
            df_rent,
            df_meta if sucesso_meta else pd.DataFrame(),
        )
        relatorio.append(f"Item: {exemplo['item']}")
        relatorio.append(f"Rentabilidade encontrada: {exemplo['rentabilidade_encontrada']}")
        if exemplo["rentabilidade_encontrada"]:
            relatorio.append(f"  Valor: {exemplo['rentabilidade_valor']}")
        relatorio.append(f"Meta encontrada: {exemplo['meta_encontrada']}")
        if exemplo["meta_encontrada"]:
            relatorio.append(f"  Valor: {exemplo['meta_valor']}")
        if exemplo["problemas"]:
            relatorio.append("Problemas detectados:")
            for prob in exemplo["problemas"]:
                relatorio.append(f"  - {prob}")
        relatorio.append("")
    
    # Resumo final
    relatorio.append("=" * 80)
    relatorio.append("RESUMO")
    relatorio.append("=" * 80)
    if sucesso_rent and sucesso_meta:
        relatorio.append("[OK] Arquivos carregados com sucesso")
        if sucesso_rent and sucesso_meta:
            corresp = verificar_correspondencia_chaves(df_rent, df_meta)
            pct_corresp = (
                (len(corresp["chaves_em_ambos"]) / len(corresp["chaves_rentabilidade"]) * 100)
                if corresp["chaves_rentabilidade"]
                else 0
            )
            relatorio.append(
                f"     Correspondência: {len(corresp['chaves_em_ambos'])}/{len(corresp['chaves_rentabilidade'])} "
                f"({pct_corresp:.1f}%)"
            )
            if pct_corresp < 100:
                relatorio.append(
                    f"[AVISO] {len(corresp['chaves_apenas_rentabilidade'])} chaves sem meta correspondente"
                )
    else:
        relatorio.append("[ERRO] Problemas detectados - verifique os detalhes acima")
    
    return "\n".join(relatorio)


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Diagnóstico de rentabilidade para cálculo de FC"
    )
    parser.add_argument("--mes", type=int, help="Mês de apuração (1-12)")
    parser.add_argument("--ano", type=int, help="Ano de apuração")
    parser.add_argument("--base-path", type=str, default=".", help="Caminho base do projeto")
    parser.add_argument("--output", type=str, help="Arquivo de saída para o relatório")
    
    args = parser.parse_args()
    
    # Obter mês/ano
    mes = args.mes
    ano = args.ano
    
    if not mes or not ano:
        from datetime import datetime
        mes = mes or datetime.now().month
        ano = ano or datetime.now().year
        print(f"[INFO] Usando mês/ano padrão: {mes:02d}/{ano}")
    
    # Gerar relatório
    relatorio = gerar_relatorio_completo(mes, ano, args.base_path)
    
    # Exibir
    print(relatorio)
    
    # Salvar se solicitado
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print(f"\n[OK] Relatório salvo em: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

