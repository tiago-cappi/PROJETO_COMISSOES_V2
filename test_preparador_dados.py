"""
Script de validação para testar se o preparador de dados está funcionando corretamente.
Valida:
1. Leitura do arquivo Analise_Comercial_Completa.xlsx
2. Geração dos arquivos de saída (Faturados, Conversões, Faturados_YTD, Retencao_Clientes)
3. Estrutura e conteúdo dos arquivos gerados
"""

import os
import sys
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional


def verificar_arquivo_entrada() -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Verifica se o arquivo Analise_Comercial_Completa existe e pode ser lido.

    Returns:
        (sucesso, mensagem_erro, dataframe)
    """
    print("\n" + "=" * 60)
    print("1. VERIFICANDO ARQUIVO DE ENTRADA")
    print("=" * 60)

    # Tentar diferentes localizações e formatos
    arquivos_tentados = [
        "Analise_Comercial_Completa.xlsx",
        "dados_entrada/Analise_Comercial_Completa.xlsx",
        "Analise_Comercial_Completa.csv",
        "dados_entrada/Analise_Comercial_Completa.csv",
    ]

    arquivo_encontrado = None
    df_analise = None

    for arquivo in arquivos_tentados:
        if os.path.exists(arquivo):
            arquivo_encontrado = arquivo
            print(f"[OK] Arquivo encontrado: {arquivo}")

            try:
                if arquivo.endswith(".xlsx"):
                    df_analise = pd.read_excel(
                        arquivo, dtype=str, nrows=1000
                    )  # Ler apenas primeiras 1000 linhas para teste
                else:
                    df_analise = pd.read_csv(
                        arquivo,
                        dtype=str,
                        nrows=1000,
                        encoding="utf-8-sig",
                        sep=None,
                        engine="python",
                    )

                print(
                    f"[OK] Arquivo lido com sucesso: {len(df_analise)} linhas (amostra)"
                )
                print(f"[OK] Colunas encontradas: {len(df_analise.columns)}")
                print(f"     Primeiras colunas: {list(df_analise.columns[:10])}")

                # Verificar colunas essenciais
                colunas_essenciais = [
                    "Processo",
                    "Dt Emissão",
                    "Valor Realizado",
                ]
                colunas_encontradas = []
                colunas_faltantes = []

                for col_essencial in colunas_essenciais:
                    # Buscar coluna (case-insensitive, com normalização)
                    encontrou = False
                    for col in df_analise.columns:
                        if col_essencial.lower().strip() in col.lower().strip():
                            colunas_encontradas.append(col)
                            encontrou = True
                            break
                    if not encontrou:
                        colunas_faltantes.append(col_essencial)

                if colunas_faltantes:
                    print(
                        f"[AVISO] Colunas essenciais não encontradas: {colunas_faltantes}"
                    )
                else:
                    print(f"[OK] Todas as colunas essenciais foram encontradas")

                return True, None, df_analise

            except Exception as e:
                print(f"[ERRO] Falha ao ler arquivo {arquivo}: {e}")
                import traceback

                traceback.print_exc()
                return False, f"Erro ao ler {arquivo}: {e}", None

    # Se chegou aqui, nenhum arquivo foi encontrado
    print(f"[ERRO] Nenhum arquivo Analise_Comercial_Completa encontrado!")
    print(f"     Arquivos tentados: {arquivos_tentados}")
    return False, "Arquivo Analise_Comercial_Completa não encontrado", None


def preparar_arquivo_entrada() -> Tuple[bool, str]:
    """
    Prepara o arquivo de entrada na raiz (onde o preparador espera).
    Copia de dados_entrada/ se necessário.

    Returns:
        (sucesso, mensagem)
    """
    print("\n  Preparando arquivo de entrada na raiz...")

    # Verificar se já existe na raiz
    if os.path.exists("Analise_Comercial_Completa.xlsx"):
        print("    [OK] Arquivo já existe na raiz")
        return True, "Arquivo já existe"

    # Tentar copiar de dados_entrada/
    origem = "dados_entrada/Analise_Comercial_Completa.xlsx"
    if os.path.exists(origem):
        try:
            import shutil

            shutil.copy2(origem, "Analise_Comercial_Completa.xlsx")
            print(f"    [OK] Arquivo copiado de {origem} para raiz")
            return True, "Arquivo copiado com sucesso"
        except Exception as e:
            print(f"    [ERRO] Falha ao copiar arquivo: {e}")
            return False, f"Erro ao copiar: {e}"

    # Tentar copiar CSV se existir
    origem_csv = "dados_entrada/Analise_Comercial_Completa.csv"
    if os.path.exists(origem_csv):
        try:
            import shutil

            shutil.copy2(origem_csv, "Analise_Comercial_Completa.csv")
            print(f"    [OK] Arquivo CSV copiado de {origem_csv} para raiz")
            return True, "Arquivo CSV copiado com sucesso"
        except Exception as e:
            print(f"    [ERRO] Falha ao copiar arquivo CSV: {e}")
            return False, f"Erro ao copiar CSV: {e}"

    print("    [ERRO] Arquivo não encontrado em dados_entrada/")
    return False, "Arquivo não encontrado"


def executar_preparador(mes: int, ano: int) -> Tuple[bool, str]:
    """
    Executa o preparador de dados.

    Returns:
        (sucesso, mensagem)
    """
    print("\n" + "=" * 60)
    print(f"2. EXECUTANDO PREPARADOR DE DADOS ({mes:02d}/{ano})")
    print("=" * 60)

    # Preparar arquivo de entrada na raiz
    sucesso_prep_arquivo, msg_prep = preparar_arquivo_entrada()
    if not sucesso_prep_arquivo:
        return False, f"Falha ao preparar arquivo de entrada: {msg_prep}"

    try:
        import preparar_dados_mensais

        sucesso = preparar_dados_mensais.run_preparador(mes, ano)

        if sucesso:
            print("[OK] Preparador executado com sucesso!")
            return True, "Preparador executado com sucesso"
        else:
            print("[ERRO] Preparador retornou False (erro crítico)")
            return False, "Preparador retornou False"

    except Exception as e:
        print(f"[ERRO] Falha ao executar preparador: {e}")
        import traceback

        traceback.print_exc()
        return False, f"Erro ao executar preparador: {e}"


def validar_arquivo_saida(
    nome_arquivo: str,
    colunas_esperadas: List[str],
    descricao: str,
    validar_nao_vazio: bool = True,
) -> Tuple[bool, Dict]:
    """
    Valida um arquivo de saída gerado.

    Args:
        nome_arquivo: Nome do arquivo a validar
        colunas_esperadas: Lista de colunas esperadas (pelo menos algumas devem existir)
        descricao: Descrição do arquivo para mensagens
        validar_nao_vazio: Se True, verifica se o arquivo não está vazio

    Returns:
        (sucesso, dicionario_com_detalhes)
    """
    resultado = {
        "arquivo": nome_arquivo,
        "existe": False,
        "pode_ler": False,
        "linhas": 0,
        "colunas": 0,
        "colunas_esperadas_encontradas": [],
        "colunas_esperadas_faltantes": [],
        "vazio": True,
        "erro": None,
    }

    print(f"\n  Validando {descricao}: {nome_arquivo}")

    # Verificar se arquivo existe
    if not os.path.exists(nome_arquivo):
        print(f"    [ERRO] Arquivo não encontrado: {nome_arquivo}")
        resultado["erro"] = "Arquivo não encontrado"
        return False, resultado

    resultado["existe"] = True
    print(f"    [OK] Arquivo existe")

    # Tentar ler o arquivo
    try:
        df = pd.read_excel(nome_arquivo)
        resultado["pode_ler"] = True
        resultado["linhas"] = len(df)
        resultado["colunas"] = len(df.columns)
        resultado["vazio"] = len(df) == 0

        print(f"    [OK] Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")

        # Verificar colunas esperadas
        colunas_df = [c.strip().lower() for c in df.columns]
        colunas_esperadas_lower = [c.strip().lower() for c in colunas_esperadas]

        for col_esperada, col_esperada_lower in zip(
            colunas_esperadas, colunas_esperadas_lower
        ):
            encontrou = False
            for col_df in colunas_df:
                if col_esperada_lower in col_df or col_df in col_esperada_lower:
                    resultado["colunas_esperadas_encontradas"].append(col_esperada)
                    encontrou = True
                    break
            if not encontrou:
                resultado["colunas_esperadas_faltantes"].append(col_esperada)

        if resultado["colunas_esperadas_encontradas"]:
            print(
                f"    [OK] Colunas encontradas: {resultado['colunas_esperadas_encontradas']}"
            )

        if resultado["colunas_esperadas_faltantes"]:
            print(
                f"    [AVISO] Colunas faltantes: {resultado['colunas_esperadas_faltantes']}"
            )

        # Validar se não está vazio (se necessário)
        if validar_nao_vazio and resultado["vazio"]:
            print(f"    [AVISO] Arquivo está vazio (sem linhas de dados)")
            return False, resultado

        if not resultado["vazio"]:
            print(f"    [OK] Arquivo contém dados ({len(df)} linhas)")

        # Mostrar amostra de dados
        if not df.empty:
            print(f"    [INFO] Amostra de dados:")
            print(f"           Primeiras colunas: {list(df.columns[:5])}")
            if "Processo" in df.columns:
                processos_unicos = df["Processo"].nunique()
                print(f"           Processos únicos: {processos_unicos}")
            if "Valor Realizado" in df.columns:
                valor_total = pd.to_numeric(
                    df["Valor Realizado"], errors="coerce"
                ).sum()
                print(f"           Valor total (aproximado): R$ {valor_total:,.2f}")

        return True, resultado

    except Exception as e:
        print(f"    [ERRO] Falha ao ler arquivo: {e}")
        resultado["erro"] = str(e)
        return False, resultado


def validar_arquivos_saida(mes: int, ano: int) -> Tuple[bool, Dict]:
    """
    Valida todos os arquivos de saída gerados.

    Returns:
        (sucesso_geral, dicionario_com_resultados)
    """
    print("\n" + "=" * 60)
    print("3. VALIDANDO ARQUIVOS DE SAÍDA GERADOS")
    print("=" * 60)

    resultados = {}
    sucesso_geral = True

    # Validar Faturados.xlsx
    sucesso_fat, detalhes_fat = validar_arquivo_saida(
        "Faturados.xlsx",
        [
            "Processo",
            "Dt Emissão",
            "Valor Realizado",
            "Código Produto",
            "Consultor Interno",
        ],
        "Faturados",
        validar_nao_vazio=False,  # Pode estar vazio se não houver dados do mês
    )
    resultados["Faturados"] = detalhes_fat
    if not sucesso_fat:
        sucesso_geral = False

    # Validar Conversões.xlsx
    sucesso_conv, detalhes_conv = validar_arquivo_saida(
        "Conversões.xlsx",
        [
            "Processo",
            "Data Aceite",
            "Valor Orçado",
            "Valor Realizado",
        ],
        "Conversões",
        validar_nao_vazio=False,
    )
    resultados["Conversões"] = detalhes_conv
    if not sucesso_conv:
        sucesso_geral = False

    # Validar Faturados_YTD.xlsx
    sucesso_ytd, detalhes_ytd = validar_arquivo_saida(
        "Faturados_YTD.xlsx",
        [
            "Processo",
            "Dt Emissão",
            "Valor Realizado",
            "Fabricante",
        ],
        "Faturados YTD",
        validar_nao_vazio=False,
    )
    resultados["Faturados_YTD"] = detalhes_ytd
    if not sucesso_ytd:
        sucesso_geral = False

    # Validar Retencao_Clientes.xlsx
    sucesso_reten, detalhes_reten = validar_arquivo_saida(
        "Retencao_Clientes.xlsx",
        [
            "linha",
            "clientes_mes_anterior",
            "clientes_mes_atual",
        ],
        "Retenção de Clientes",
        validar_nao_vazio=False,
    )
    resultados["Retencao_Clientes"] = detalhes_reten
    if not sucesso_reten:
        sucesso_geral = False

    return sucesso_geral, resultados


def gerar_relatorio(resultados: Dict) -> str:
    """
    Gera um relatório resumido dos resultados.
    """
    relatorio = "\n" + "=" * 60
    relatorio += "\nRELATÓRIO DE VALIDAÇÃO"
    relatorio += "\n" + "=" * 60

    for nome_arquivo, detalhes in resultados.items():
        relatorio += f"\n\n{nome_arquivo}:"
        relatorio += f"\n  Existe: {'Sim' if detalhes.get('existe') else 'Não'}"
        relatorio += f"\n  Pode ler: {'Sim' if detalhes.get('pode_ler') else 'Não'}"
        relatorio += f"\n  Linhas: {detalhes.get('linhas', 0)}"
        relatorio += f"\n  Colunas: {detalhes.get('colunas', 0)}"
        relatorio += f"\n  Vazio: {'Sim' if detalhes.get('vazio') else 'Não'}"

        if detalhes.get("colunas_esperadas_encontradas"):
            relatorio += f"\n  Colunas encontradas: {', '.join(detalhes['colunas_esperadas_encontradas'])}"
        if detalhes.get("colunas_esperadas_faltantes"):
            relatorio += f"\n  Colunas faltantes: {', '.join(detalhes['colunas_esperadas_faltantes'])}"
        if detalhes.get("erro"):
            relatorio += f"\n  Erro: {detalhes['erro']}"

    return relatorio


def detectar_mes_ano_dos_dados(
    df_analise: pd.DataFrame,
) -> Tuple[Optional[int], Optional[int]]:
    """
    Detecta o mês/ano mais comum nos dados do arquivo de entrada.

    Returns:
        (mes, ano) ou (None, None) se não conseguir detectar
    """
    try:
        # Tentar encontrar coluna de data
        colunas_data = ["Dt Emissão", "Dt Emissao", "Data Emissão", "Data Emissao"]
        col_data = None

        for col in df_analise.columns:
            if any(c.lower() in col.lower() for c in colunas_data):
                col_data = col
                break

        if col_data is None:
            return None, None

        # Converter para datetime
        df_analise[col_data] = pd.to_datetime(df_analise[col_data], errors="coerce")

        # Filtrar apenas datas válidas
        datas_validas = df_analise[col_data].dropna()

        if len(datas_validas) == 0:
            return None, None

        # Encontrar mês/ano mais comum
        datas_validas = pd.to_datetime(datas_validas)
        mes_ano_counts = datas_validas.groupby(
            [datas_validas.dt.year, datas_validas.dt.month]
        ).size()

        if len(mes_ano_counts) == 0:
            return None, None

        # Pegar o mês/ano mais frequente
        (ano_detectado, mes_detectado), _ = (
            mes_ano_counts.idxmax(),
            mes_ano_counts.max(),
        )

        return int(mes_detectado), int(ano_detectado)

    except Exception as e:
        print(f"    [AVISO] Não foi possível detectar mês/ano dos dados: {e}")
        return None, None


def main():
    """Função principal."""
    print("=" * 60)
    print("VALIDAÇÃO DO PREPARADOR DE DADOS")
    print("=" * 60)

    # 1. Verificar arquivo de entrada primeiro para detectar mês/ano
    sucesso_entrada, erro_entrada, df_entrada = verificar_arquivo_entrada()
    if not sucesso_entrada:
        print(
            f"\n[ERRO CRÍTICO] Falha na verificação do arquivo de entrada: {erro_entrada}"
        )
        return 1

    # 2. Detectar mês/ano dos dados ou usar padrão
    mes_detectado, ano_detectado = None, None
    if df_entrada is not None and not df_entrada.empty:
        print("\n  Detectando mês/ano dos dados no arquivo...")
        mes_detectado, ano_detectado = detectar_mes_ano_dos_dados(df_entrada.copy())
        if mes_detectado and ano_detectado:
            print(f"    [OK] Mês/ano detectado: {mes_detectado:02d}/{ano_detectado}")
        else:
            print("    [AVISO] Não foi possível detectar mês/ano dos dados")

    # Obter mês/ano (prioridade: argumentos > detectado > atual)
    from datetime import datetime

    mes = datetime.now().month
    ano = datetime.now().year

    # Permitir override via argumentos
    if len(sys.argv) >= 3:
        try:
            mes = int(sys.argv[1])
            ano = int(sys.argv[2])
            print(f"\n[INFO] Usando mês/ano dos argumentos: {mes:02d}/{ano}")
        except ValueError:
            print(f"[AVISO] Argumentos inválidos. Usando mês/ano detectado ou atual.")
    elif mes_detectado and ano_detectado:
        # Usar mês/ano detectado automaticamente
        mes = mes_detectado
        ano = ano_detectado
        print(f"\n[INFO] Usando mês/ano detectado dos dados: {mes:02d}/{ano}")
    else:
        print(f"\n[AVISO] Usando mês/ano atual (pode não haver dados): {mes:02d}/{ano}")

    # 3. Executar preparador
    sucesso_prep, msg_prep = executar_preparador(mes, ano)
    if not sucesso_prep:
        print(f"\n[ERRO CRÍTICO] Falha ao executar preparador: {msg_prep}")
        return 1

    # 4. Validar arquivos de saída
    sucesso_saida, resultados = validar_arquivos_saida(mes, ano)

    # 5. Gerar relatório
    relatorio = gerar_relatorio(resultados)
    print(relatorio)

    # 6. Resumo final
    print("\n" + "=" * 60)
    if sucesso_entrada and sucesso_prep and sucesso_saida:
        print("[SUCESSO] TODAS AS VALIDAÇÕES PASSARAM!")
        print("=" * 60)
        return 0
    else:
        print("[ATENÇÃO] ALGUMAS VALIDAÇÕES FALHARAM")
        print("=" * 60)
        if not sucesso_entrada:
            print(f"  - Arquivo de entrada: FALHOU ({erro_entrada})")
        if not sucesso_prep:
            print(f"  - Preparador: FALHOU ({msg_prep})")
        if not sucesso_saida:
            print("  - Arquivos de saída: ALGUMAS VALIDAÇÕES FALHARAM")
        return 1


if __name__ == "__main__":
    sys.exit(main())
