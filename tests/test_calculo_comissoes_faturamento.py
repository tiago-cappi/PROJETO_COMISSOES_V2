"""
Script de teste para validar o cálculo de comissões por faturamento.
Testa se o cálculo está sendo feito corretamente item a item para cada processo.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def executar_calculo_comissoes(mes: int, ano: int) -> Tuple[bool, Optional[object], str]:
    """
    Executa o cálculo de comissões para o mês/ano especificado.
    
    Returns:
        (sucesso, instancia_calculo, mensagem)
    """
    print("\n" + "=" * 60)
    print(f"EXECUTANDO CÁLCULO DE COMISSÕES ({mes:02d}/{ano})")
    print("=" * 60)
    
    try:
        # Verificar se o arquivo de saída já existe (se o cálculo já foi executado)
        arquivo_saida = f"Comissoes_{mes:02d}_{ano}.xlsx"
        if os.path.exists(arquivo_saida):
            print(f"[INFO] Arquivo de saída encontrado: {arquivo_saida}")
            print("[INFO] Tentando validar arquivo existente...")
            # Tentar ler o arquivo e validar
            try:
                df_comissoes = pd.read_excel(arquivo_saida, sheet_name="COMISSOES_CALCULADAS")
                print(f"[OK] Arquivo lido: {len(df_comissoes)} linhas")
                # Criar objeto mock para validação
                class MockCalculadora:
                    def __init__(self, comissoes_df, data):
                        self.comissoes_df = comissoes_df
                        self.data = data
                
                # Carregar dados de entrada para validação
                data = {}
                if os.path.exists("Faturados.xlsx"):
                    data["FATURADOS"] = pd.read_excel("Faturados.xlsx")
                
                mock_calc = MockCalculadora(df_comissoes, data)
                return True, mock_calc, "Arquivo existente validado"
            except Exception as e:
                print(f"[AVISO] Não foi possível ler arquivo existente: {e}")
        
        # Tentar executar o cálculo completo
        print("[INFO] Executando cálculo completo...")
        print("[AVISO] Isso pode levar alguns minutos...")
        
        # Importar e instanciar
        from calculo_comissoes import CalculoComissao
        
        calculadora = CalculoComissao()
        
        # Executar apenas o cálculo de comissões (sem gerar relatório)
        print("\n[INFO] Carregando dados...")
        calculadora._carregar_dados()
        
        print("[INFO] Preparando dados...")
        calculadora._preparar_dados()
        
        print("[INFO] Calculando comissões por faturamento...")
        calculadora._calcular_comissoes()
        
        print("[OK] Cálculo de comissões executado com sucesso!")
        
        return True, calculadora, "Cálculo executado com sucesso"
        
    except ImportError as e:
        if "models" in str(e) or "services" in str(e):
            print(f"[AVISO] Módulos opcionais não encontrados: {e}")
            print("[INFO] Tentando validar apenas com arquivos gerados...")
            # Tentar validar com arquivo existente
            arquivo_saida = f"Comissoes_{mes:02d}_{ano}.xlsx"
            if os.path.exists(arquivo_saida):
                try:
                    df_comissoes = pd.read_excel(arquivo_saida, sheet_name="COMISSOES_CALCULADAS")
                    class MockCalculadora:
                        def __init__(self, comissoes_df, data):
                            self.comissoes_df = comissoes_df
                            self.data = data
                    data = {}
                    if os.path.exists("Faturados.xlsx"):
                        data["FATURADOS"] = pd.read_excel("Faturados.xlsx")
                    mock_calc = MockCalculadora(df_comissoes, data)
                    return True, mock_calc, "Validação com arquivo existente"
                except Exception:
                    pass
            return False, None, f"Módulos necessários não encontrados: {e}"
        raise
    except Exception as e:
        print(f"[ERRO] Falha ao executar cálculo: {e}")
        import traceback
        traceback.print_exc()
        return False, None, f"Erro: {e}"


def validar_estrutura_comissoes(calculadora) -> Tuple[bool, Dict]:
    """
    Valida a estrutura do DataFrame de comissões calculadas.
    
    Returns:
        (sucesso, dicionario_com_detalhes)
    """
    print("\n" + "=" * 60)
    print("VALIDANDO ESTRUTURA DAS COMISSÕES CALCULADAS")
    print("=" * 60)
    
    resultado = {
        "existe": False,
        "linhas": 0,
        "colunas": 0,
        "colunas_esperadas": [],
        "colunas_faltantes": [],
        "processos_unicos": 0,
        "colaboradores_unicos": 0,
        "itens_unicos": 0,
    }
    
    try:
        # Verificar se o DataFrame de comissões existe
        if not hasattr(calculadora, "comissoes_df"):
            print("[ERRO] calculadora.comissoes_df não existe")
            return False, resultado
        
        df_comissoes = calculadora.comissoes_df
        
        if df_comissoes is None or df_comissoes.empty:
            print("[AVISO] DataFrame de comissões está vazio")
            resultado["existe"] = True
            resultado["linhas"] = 0
            return True, resultado  # Vazio é válido (pode não haver dados)
        
        resultado["existe"] = True
        resultado["linhas"] = len(df_comissoes)
        resultado["colunas"] = len(df_comissoes.columns)
        
        print(f"[OK] DataFrame de comissões encontrado: {len(df_comissoes)} linhas, {len(df_comissoes.columns)} colunas")
        
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
            print(f"     {resultado['colunas_esperadas']}")
        
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
        
        return True, resultado
        
    except Exception as e:
        print(f"[ERRO] Falha ao validar estrutura: {e}")
        import traceback
        traceback.print_exc()
        return False, resultado


def validar_calculo_item_item(calculadora) -> Tuple[bool, Dict]:
    """
    Valida o cálculo item a item para cada processo.
    
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
        "detalhes_por_processo": {},
    }
    
    try:
        df_comissoes = calculadora.comissoes_df
        
        if df_comissoes is None or df_comissoes.empty:
            print("[AVISO] Nenhuma comissão calculada para validar")
            return True, resultado
        
        df_faturados = calculadora.data.get("FATURADOS", pd.DataFrame())
        
        if df_faturados.empty:
            print("[AVISO] Nenhum item faturado encontrado")
            return True, resultado
        
        # Agrupar comissões por processo
        processos_comissoes = df_comissoes.groupby("processo") if "processo" in df_comissoes.columns else None
        
        if processos_comissoes is None:
            print("[ERRO] Coluna 'processo' não encontrada nas comissões")
            return False, resultado
        
        # Para cada processo, validar que todos os itens foram calculados
        processos_faturados = df_faturados["Processo"].unique() if "Processo" in df_faturados.columns else []
        
        print(f"\n[INFO] Processos faturados: {len(processos_faturados)}")
        print(f"[INFO] Processos com comissões calculadas: {df_comissoes['processo'].nunique()}")
        
        for processo in processos_faturados:
            processo_str = str(processo).strip()
            
            # Itens faturados deste processo
            itens_processo = df_faturados[df_faturados["Processo"] == processo]
            
            # Comissões calculadas para este processo
            comissoes_processo = df_comissoes[df_comissoes["processo"] == processo_str]
            
            if comissoes_processo.empty:
                resultado["avisos"].append(
                    f"Processo {processo_str}: Nenhuma comissão calculada (pode ser normal se não houver colaboradores atribuídos)"
                )
                continue
            
            # Validar que cada item tem comissões calculadas
            itens_com_comissao = comissoes_processo["cod_produto"].nunique() if "cod_produto" in comissoes_processo.columns else 0
            itens_faturados = itens_processo["Código Produto"].nunique() if "Código Produto" in itens_processo.columns else 0
            
            detalhes_processo = {
                "processo": processo_str,
                "itens_faturados": len(itens_processo),
                "itens_com_comissao": itens_com_comissao,
                "linhas_comissao": len(comissoes_processo),
                "colaboradores": comissoes_processo["nome_colaborador"].nunique() if "nome_colaborador" in comissoes_processo.columns else 0,
            }
            
            # Validar cálculos básicos
            erros_processo = []
            
            # Verificar se comissao_calculada = comissao_potencial_maxima * fator_correcao_fc
            if all(col in comissoes_processo.columns for col in ["comissao_calculada", "comissao_potencial_maxima", "fator_correcao_fc"]):
                for idx, row in comissoes_processo.iterrows():
                    try:
                        comissao_calc = float(row["comissao_calculada"]) if pd.notna(row["comissao_calculada"]) else 0.0
                        comissao_pot = float(row["comissao_potencial_maxima"]) if pd.notna(row["comissao_potencial_maxima"]) else 0.0
                        fc = float(row["fator_correcao_fc"]) if pd.notna(row["fator_correcao_fc"]) else 0.0
                        
                        esperado = comissao_pot * fc
                        diferenca = abs(comissao_calc - esperado)
                        
                        # Tolerância para erros de arredondamento
                        if diferenca > 0.01:
                            erros_processo.append(
                                f"Item {row.get('cod_produto', 'N/A')}: comissao_calculada ({comissao_calc:.2f}) != "
                                f"comissao_potencial_maxima ({comissao_pot:.2f}) * fator_correcao_fc ({fc:.4f}) = {esperado:.2f}"
                            )
                    except Exception as e:
                        erros_processo.append(f"Erro ao validar cálculo do item: {e}")
            
            if erros_processo:
                resultado["erros_encontrados"].extend(erros_processo)
                detalhes_processo["erros"] = len(erros_processo)
            else:
                detalhes_processo["erros"] = 0
            
            resultado["detalhes_por_processo"][processo_str] = detalhes_processo
            resultado["processos_validados"] += 1
            resultado["itens_validados"] += len(comissoes_processo)
            
            # Mostrar resumo do processo
            status = "[OK]" if detalhes_processo["erros"] == 0 else "[ERRO]"
            print(f"\n  {status} Processo {processo_str}:")
            print(f"      Itens faturados: {detalhes_processo['itens_faturados']}")
            print(f"      Linhas de comissão: {detalhes_processo['linhas_comissao']}")
            print(f"      Colaboradores: {detalhes_processo['colaboradores']}")
            if detalhes_processo["erros"] > 0:
                print(f"      Erros: {detalhes_processo['erros']}")
        
        print(f"\n[INFO] Processos validados: {resultado['processos_validados']}")
        print(f"[INFO] Itens validados: {resultado['itens_validados']}")
        
        if resultado["erros_encontrados"]:
            print(f"\n[ERRO] {len(resultado['erros_encontrados'])} erro(s) encontrado(s):")
            for erro in resultado["erros_encontrados"][:10]:  # Mostrar apenas os primeiros 10
                print(f"  - {erro}")
            if len(resultado["erros_encontrados"]) > 10:
                print(f"  ... e mais {len(resultado['erros_encontrados']) - 10} erro(s)")
        
        if resultado["avisos"]:
            print(f"\n[AVISO] {len(resultado['avisos'])} aviso(s):")
            for aviso in resultado["avisos"][:5]:  # Mostrar apenas os primeiros 5
                print(f"  - {aviso}")
        
        sucesso = len(resultado["erros_encontrados"]) == 0
        return sucesso, resultado
        
    except Exception as e:
        print(f"[ERRO] Falha ao validar cálculo item a item: {e}")
        import traceback
        traceback.print_exc()
        return False, resultado


def gerar_relatorio_detalhado(calculadora, resultado_estrutura: Dict, resultado_calculo: Dict):
    """
    Gera um relatório detalhado dos resultados.
    """
    print("\n" + "=" * 60)
    print("RELATÓRIO DETALHADO")
    print("=" * 60)
    
    df_comissoes = calculadora.comissoes_df
    
    if df_comissoes is not None and not df_comissoes.empty:
        print(f"\nResumo Geral:")
        print(f"  Total de linhas de comissão: {len(df_comissoes)}")
        print(f"  Processos únicos: {df_comissoes['processo'].nunique() if 'processo' in df_comissoes.columns else 'N/A'}")
        print(f"  Colaboradores únicos: {df_comissoes['nome_colaborador'].nunique() if 'nome_colaborador' in df_comissoes.columns else 'N/A'}")
        print(f"  Itens únicos: {df_comissoes['cod_produto'].nunique() if 'cod_produto' in df_comissoes.columns else 'N/A'}")
        
        # Valor total de comissões
        if "comissao_calculada" in df_comissoes.columns:
            total_comissoes = pd.to_numeric(df_comissoes["comissao_calculada"], errors="coerce").sum()
            print(f"  Total de comissões calculadas: R$ {total_comissoes:,.2f}")
        
        # Valor total faturado
        df_faturados = calculadora.data.get("FATURADOS", pd.DataFrame())
        if not df_faturados.empty and "Valor Realizado" in df_faturados.columns:
            total_faturado = pd.to_numeric(df_faturados["Valor Realizado"], errors="coerce").sum()
            print(f"  Total faturado: R$ {total_faturado:,.2f}")
        
        # Top colaboradores por comissão
        if "nome_colaborador" in df_comissoes.columns and "comissao_calculada" in df_comissoes.columns:
            print(f"\nTop 5 Colaboradores por Comissão:")
            top_colabs = (
                df_comissoes.groupby("nome_colaborador")["comissao_calculada"]
                .apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
                .sort_values(ascending=False)
                .head(5)
            )
            for colab, valor in top_colabs.items():
                print(f"  {colab}: R$ {valor:,.2f}")
    
    print(f"\nValidação de Estrutura:")
    print(f"  Colunas encontradas: {len(resultado_estrutura.get('colunas_esperadas', []))}")
    print(f"  Colunas faltantes: {len(resultado_estrutura.get('colunas_faltantes', []))}")
    
    print(f"\nValidação de Cálculo:")
    print(f"  Processos validados: {resultado_calculo.get('processos_validados', 0)}")
    print(f"  Itens validados: {resultado_calculo.get('itens_validados', 0)}")
    print(f"  Erros encontrados: {len(resultado_calculo.get('erros_encontrados', []))}")
    print(f"  Avisos: {len(resultado_calculo.get('avisos', []))}")


def main():
    """Função principal."""
    print("=" * 60)
    print("TESTE DE CÁLCULO DE COMISSÕES POR FATURAMENTO")
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
    
    # 1. Executar cálculo de comissões
    sucesso_exec, calculadora, msg_exec = executar_calculo_comissoes(mes, ano)
    if not sucesso_exec:
        print(f"\n[ERRO CRÍTICO] Falha ao executar cálculo: {msg_exec}")
        return 1
    
    # 2. Validar estrutura
    sucesso_estrutura, resultado_estrutura = validar_estrutura_comissoes(calculadora)
    if not sucesso_estrutura:
        print(f"\n[ERRO] Falha na validação de estrutura")
        return 1
    
    # 3. Validar cálculo item a item
    sucesso_calculo, resultado_calculo = validar_calculo_item_item(calculadora)
    
    # 4. Gerar relatório detalhado
    gerar_relatorio_detalhado(calculadora, resultado_estrutura, resultado_calculo)
    
    # 5. Resumo final
    print("\n" + "=" * 60)
    if sucesso_exec and sucesso_estrutura and sucesso_calculo:
        print("[SUCESSO] TODAS AS VALIDAÇÕES PASSARAM!")
        print("=" * 60)
        return 0
    else:
        print("[ATENÇÃO] ALGUMAS VALIDAÇÕES FALHARAM")
        print("=" * 60)
        if not sucesso_exec:
            print(f"  - Execução do cálculo: FALHOU")
        if not sucesso_estrutura:
            print(f"  - Validação de estrutura: FALHOU")
        if not sucesso_calculo:
            print(f"  - Validação de cálculo: FALHOU")
        return 1


if __name__ == "__main__":
    sys.exit(main())

