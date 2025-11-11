"""
Script para validar o cálculo de comissões por faturamento após a execução.
Este script valida os arquivos gerados pelo cálculo de comissões.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Tuple

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def validar_arquivo_comissoes(mes: int, ano: int) -> Tuple[bool, Dict]:
    """
    Valida o arquivo de comissões gerado.
    
    Returns:
        (sucesso, dicionario_com_detalhes)
    """
    print("\n" + "=" * 60)
    print("VALIDANDO ARQUIVO DE COMISSÕES GERADO")
    print("=" * 60)
    
    resultado = {
        "arquivo_existe": False,
        "aba_encontrada": False,
        "linhas": 0,
        "colunas": 0,
        "colunas_esperadas": [],
        "colunas_faltantes": [],
        "processos_unicos": 0,
        "colaboradores_unicos": 0,
        "itens_unicos": 0,
        "total_comissoes": 0.0,
    }
    
    # Tentar diferentes nomes de arquivo
    arquivos_tentados = [
        f"Comissoes_{mes:02d}_{ano}.xlsx",
        f"Comissoes_{mes}_{ano}.xlsx",
        "Comissoes.xlsx",
    ]
    
    arquivo_encontrado = None
    for arquivo in arquivos_tentados:
        if os.path.exists(arquivo):
            arquivo_encontrado = arquivo
            break
    
    if arquivo_encontrado is None:
        print(f"[ERRO] Arquivo de comissões não encontrado!")
        print(f"     Arquivos tentados: {arquivos_tentados}")
        print(f"\n[INFO] Para gerar o arquivo, execute:")
        print(f"     python calculo_comissoes.py")
        return False, resultado
    
    resultado["arquivo_existe"] = True
    print(f"[OK] Arquivo encontrado: {arquivo_encontrado}")
    
    try:
        # Tentar ler a aba COMISSOES_CALCULADAS
        try:
            df_comissoes = pd.read_excel(arquivo_encontrado, sheet_name="COMISSOES_CALCULADAS")
            resultado["aba_encontrada"] = True
        except Exception:
            # Tentar ler a primeira aba
            try:
                df_comissoes = pd.read_excel(arquivo_encontrado, sheet_name=0)
                print("[AVISO] Aba 'COMISSOES_CALCULADAS' não encontrada, usando primeira aba")
                resultado["aba_encontrada"] = True
            except Exception as e:
                print(f"[ERRO] Falha ao ler arquivo: {e}")
                return False, resultado
        
        if df_comissoes.empty:
            print("[AVISO] DataFrame de comissões está vazio")
            return True, resultado  # Vazio é válido (pode não haver dados)
        
        resultado["linhas"] = len(df_comissoes)
        resultado["colunas"] = len(df_comissoes.columns)
        
        print(f"[OK] Arquivo lido: {len(df_comissoes)} linhas, {len(df_comissoes.columns)} colunas")
        
        # Colunas essenciais esperadas
        colunas_esperadas = [
            "processo",
            "cod_produto",
            "nome_colaborador",
            "cargo",
            "faturamento_item",
            "taxa_rateio_aplicada",
            "percentual_elegibilidade_pe",
            "fator_correcao_fc",
            "comissao_potencial_maxima",
            "comissao_calculada",
        ]
        
        colunas_df = [c.lower().strip() for c in df_comissoes.columns]
        
        for col_esperada in colunas_esperadas:
            encontrou = False
            for col_df in colunas_df:
                if col_esperada.lower() in col_df or col_df in col_esperada.lower():
                    resultado["colunas_esperadas"].append(col_esperada)
                    encontrou = True
                    break
            if not encontrou:
                resultado["colunas_faltantes"].append(col_esperada)
        
        if resultado["colunas_esperadas"]:
            print(f"[OK] Colunas encontradas: {len(resultado['colunas_esperadas'])}/{len(colunas_esperadas)}")
        
        if resultado["colunas_faltantes"]:
            print(f"[AVISO] Colunas faltantes: {resultado['colunas_faltantes']}")
        
        # Estatísticas
        if "processo" in df_comissoes.columns:
            resultado["processos_unicos"] = df_comissoes["processo"].nunique()
            print(f"[INFO] Processos únicos: {resultado['processos_unicos']}")
        
        if "nome_colaborador" in df_comissoes.columns:
            resultado["colaboradores_unicos"] = df_comissoes["nome_colaborador"].nunique()
            print(f"[INFO] Colaboradores únicos: {resultado['colaboradores_unicos']}")
        
        if "cod_produto" in df_comissoes.columns:
            resultado["itens_unicos"] = df_comissoes["cod_produto"].nunique()
            print(f"[INFO] Itens únicos: {resultado['itens_unicos']}")
        
        # Valor total de comissões
        if "comissao_calculada" in df_comissoes.columns:
            total = pd.to_numeric(df_comissoes["comissao_calculada"], errors="coerce").sum()
            resultado["total_comissoes"] = float(total)
            print(f"[INFO] Total de comissões calculadas: R$ {total:,.2f}")
        
        return True, resultado
        
    except Exception as e:
        print(f"[ERRO] Falha ao validar arquivo: {e}")
        import traceback
        traceback.print_exc()
        return False, resultado


def validar_calculo_item_item(mes: int, ano: int) -> Tuple[bool, Dict]:
    """
    Valida o cálculo item a item comparando Faturados com Comissões.
    
    Returns:
        (sucesso, dicionario_com_detalhes)
    """
    print("\n" + "=" * 60)
    print("VALIDANDO CÁLCULO ITEM A ITEM POR PROCESSO")
    print("=" * 60)
    
    resultado = {
        "processos_validados": 0,
        "itens_validados": 0,
        "erros_encontrados": [],
        "avisos": [],
    }
    
    try:
        # Carregar Faturados
        if not os.path.exists("Faturados.xlsx"):
            print("[ERRO] Arquivo Faturados.xlsx não encontrado")
            return False, resultado
        
        df_faturados = pd.read_excel("Faturados.xlsx")
        
        if df_faturados.empty:
            print("[AVISO] Nenhum item faturado encontrado")
            return True, resultado
        
        # Carregar Comissões
        arquivos_tentados = [
            f"Comissoes_{mes:02d}_{ano}.xlsx",
            f"Comissoes_{mes}_{ano}.xlsx",
            "Comissoes.xlsx",
        ]
        
        arquivo_comissoes = None
        for arquivo in arquivos_tentados:
            if os.path.exists(arquivo):
                arquivo_comissoes = arquivo
                break
        
        if arquivo_comissoes is None:
            print("[ERRO] Arquivo de comissões não encontrado")
            return False, resultado
        
        try:
            df_comissoes = pd.read_excel(arquivo_comissoes, sheet_name="COMISSOES_CALCULADAS")
        except Exception:
            df_comissoes = pd.read_excel(arquivo_comissoes, sheet_name=0)
        
        if df_comissoes.empty:
            print("[AVISO] Nenhuma comissão calculada encontrada")
            return True, resultado
        
        # Validar que cada processo tem comissões calculadas
        processos_faturados = df_faturados["Processo"].unique() if "Processo" in df_faturados.columns else []
        
        print(f"\n[INFO] Processos faturados: {len(processos_faturados)}")
        print(f"[INFO] Processos com comissões: {df_comissoes['processo'].nunique() if 'processo' in df_comissoes.columns else 0}")
        
        # Validar fórmula: comissao_calculada = comissao_potencial_maxima * fator_correcao_fc
        if all(col in df_comissoes.columns for col in ["comissao_calculada", "comissao_potencial_maxima", "fator_correcao_fc"]):
            erros_formula = 0
            for idx, row in df_comissoes.iterrows():
                try:
                    comissao_calc = pd.to_numeric(row["comissao_calculada"], errors="coerce")
                    comissao_pot = pd.to_numeric(row["comissao_potencial_maxima"], errors="coerce")
                    fc = pd.to_numeric(row["fator_correcao_fc"], errors="coerce")
                    
                    if pd.notna(comissao_calc) and pd.notna(comissao_pot) and pd.notna(fc):
                        esperado = comissao_pot * fc
                        diferenca = abs(comissao_calc - esperado)
                        
                        # Tolerância para erros de arredondamento
                        if diferenca > 0.01:
                            erros_formula += 1
                            if erros_formula <= 5:  # Mostrar apenas os primeiros 5
                                resultado["erros_encontrados"].append(
                                    f"Linha {idx}: comissao_calculada ({comissao_calc:.2f}) != "
                                    f"comissao_potencial_maxima ({comissao_pot:.2f}) * fator_correcao_fc ({fc:.4f}) = {esperado:.2f}"
                                )
                except Exception:
                    pass
            
            if erros_formula == 0:
                print("[OK] Fórmula de cálculo validada: comissao_calculada = comissao_potencial_maxima * fator_correcao_fc")
            else:
                print(f"[ERRO] {erros_formula} erro(s) na fórmula de cálculo encontrado(s)")
        
        # Validar por processo
        for processo in processos_faturados[:10]:  # Validar apenas os primeiros 10 processos
            processo_str = str(processo).strip()
            
            itens_processo = df_faturados[df_faturados["Processo"] == processo]
            comissoes_processo = df_comissoes[df_comissoes["processo"] == processo_str] if "processo" in df_comissoes.columns else pd.DataFrame()
            
            if comissoes_processo.empty:
                resultado["avisos"].append(f"Processo {processo_str}: Nenhuma comissão calculada")
                continue
            
            resultado["processos_validados"] += 1
            resultado["itens_validados"] += len(comissoes_processo)
            
            print(f"\n  [OK] Processo {processo_str}:")
            print(f"      Itens faturados: {len(itens_processo)}")
            print(f"      Linhas de comissão: {len(comissoes_processo)}")
            if "nome_colaborador" in comissoes_processo.columns:
                print(f"      Colaboradores: {comissoes_processo['nome_colaborador'].nunique()}")
        
        print(f"\n[INFO] Processos validados: {resultado['processos_validados']}")
        print(f"[INFO] Itens validados: {resultado['itens_validados']}")
        
        if resultado["erros_encontrados"]:
            print(f"\n[ERRO] {len(resultado['erros_encontrados'])} erro(s) encontrado(s)")
        
        sucesso = len(resultado["erros_encontrados"]) == 0
        return sucesso, resultado
        
    except Exception as e:
        print(f"[ERRO] Falha ao validar cálculo item a item: {e}")
        import traceback
        traceback.print_exc()
        return False, resultado


def main():
    """Função principal."""
    print("=" * 60)
    print("VALIDAÇÃO DE CÁLCULO DE COMISSÕES POR FATURAMENTO")
    print("=" * 60)
    
    # Mês/ano para teste
    mes = 9
    ano = 2025
    
    # Permitir override via argumentos
    if len(sys.argv) >= 3:
        try:
            mes = int(sys.argv[1])
            ano = int(sys.argv[2])
        except ValueError:
            print(f"[AVISO] Argumentos inválidos. Usando mês/ano padrão: {mes:02d}/{ano}")
    
    print(f"\nMês/Ano de apuração: {mes:02d}/{ano}")
    print("\n[INFO] Este script valida os arquivos gerados pelo cálculo de comissões.")
    print("[INFO] Se os arquivos não existirem, execute primeiro:")
    print("       python calculo_comissoes.py")
    
    # 1. Validar arquivo de comissões
    sucesso_arquivo, resultado_arquivo = validar_arquivo_comissoes(mes, ano)
    if not sucesso_arquivo:
        print(f"\n[ERRO] Falha na validação do arquivo")
        return 1
    
    # 2. Validar cálculo item a item
    sucesso_calculo, resultado_calculo = validar_calculo_item_item(mes, ano)
    
    # 3. Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    if resultado_arquivo["arquivo_existe"]:
        print(f"\nArquivo de Comissões:")
        print(f"  Linhas: {resultado_arquivo['linhas']}")
        print(f"  Processos únicos: {resultado_arquivo['processos_unicos']}")
        print(f"  Colaboradores únicos: {resultado_arquivo['colaboradores_unicos']}")
        print(f"  Itens únicos: {resultado_arquivo['itens_unicos']}")
        print(f"  Total de comissões: R$ {resultado_arquivo['total_comissoes']:,.2f}")
    
    print(f"\nValidação de Cálculo:")
    print(f"  Processos validados: {resultado_calculo.get('processos_validados', 0)}")
    print(f"  Itens validados: {resultado_calculo.get('itens_validados', 0)}")
    print(f"  Erros encontrados: {len(resultado_calculo.get('erros_encontrados', []))}")
    
    print("\n" + "=" * 60)
    if sucesso_arquivo and sucesso_calculo:
        print("[SUCESSO] TODAS AS VALIDAÇÕES PASSARAM!")
        print("=" * 60)
        return 0
    else:
        print("[ATENÇÃO] ALGUMAS VALIDAÇÕES FALHARAM")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

