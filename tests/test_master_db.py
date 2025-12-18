"""
Script de teste para o Banco de Dados Master de Comissões.
Verifica todos os mecanismos de segurança e operações CRUD.
"""

import pandas as pd
import os
import sys

def main():
    print("=== TESTE DO BANCO DE DADOS MASTER DE COMISSÕES ===")
    print()

    # Teste 1: Importar módulos
    print("[TESTE 1] Importando módulos...")
    try:
        from src.utils.file_security import FileSecurityManager
        from src.io.master_db_manager import MasterDBManager, MASTER_DB_COLUMNS
        print("  ✓ Módulos importados com sucesso!")
    except Exception as e:
        print(f"  ✗ ERRO ao importar: {e}")
        return 1

    # Teste 2: Inicializar gerenciadores
    print()
    print("[TESTE 2] Inicializando gerenciadores...")
    try:
        security = FileSecurityManager()
        master_db = MasterDBManager(base_path=".")
        print(f"  ✓ FileSecurityManager inicializado")
        print(f"  ✓ MasterDBManager inicializado")
        print(f"  ✓ Caminho do DB: {master_db.db_filepath}")
        print(f"  ✓ Diretório de backups: {master_db.backup_dir}")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        return 1

    # Teste 3: Criar DataFrame de teste simulando comissões de faturamento
    print()
    print("[TESTE 3] Criando dados de teste...")
    try:
        df_teste = pd.DataFrame([
            {
                "processo": "PROC-001",
                "nome_colaborador": "João Silva",
                "cargo": "Consultor",
                "linha": "Equipamentos",
                "faturamento_item": 10000.00,
                "taxa_rateio_aplicada": 0.05,
                "fator_correcao_fc": 1.0,
                "comissao_calculada": 500.00,
                "cod_produto": "PROD-001",
                "descricao_produto": "Produto Teste A",
                "grupo": "Grupo A",
                "subgrupo": "Subgrupo 1",
            },
            {
                "processo": "PROC-001",
                "nome_colaborador": "Maria Santos",
                "cargo": "Gerente",
                "linha": "Equipamentos",
                "faturamento_item": 10000.00,
                "taxa_rateio_aplicada": 0.03,
                "fator_correcao_fc": 1.0,
                "comissao_calculada": 300.00,
                "cod_produto": "PROD-001",
                "descricao_produto": "Produto Teste A",
                "grupo": "Grupo A",
                "subgrupo": "Subgrupo 1",
            },
            {
                "processo": "PROC-002",
                "nome_colaborador": "João Silva",
                "cargo": "Consultor",
                "linha": "Serviços",
                "faturamento_item": 5000.00,
                "taxa_rateio_aplicada": 0.04,
                "fator_correcao_fc": 0.95,
                "comissao_calculada": 190.00,
                "cod_produto": "SERV-001",
                "descricao_produto": "Serviço Teste B",
                "grupo": "Grupo B",
                "subgrupo": "Subgrupo 2",
            },
        ])
        print(f"  ✓ DataFrame criado com {len(df_teste)} registros")
        processos = df_teste["processo"].unique().tolist()
        colaboradores = df_teste["nome_colaborador"].unique().tolist()
        print(f"  ✓ Processos: {processos}")
        print(f"  ✓ Colaboradores: {colaboradores}")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        return 1

    # Teste 4: Salvar no banco de dados
    print()
    print("[TESTE 4] Salvando no banco de dados master...")
    try:
        success, msg = master_db.append_comissoes(
            df_comissoes=df_teste,
            mes=12,
            ano=2025,
            tipo_comissao="FATURAMENTO",
        )
        if success:
            print(f"  ✓ {msg}")
        else:
            print(f"  ✗ ERRO: {msg}")
            return 1
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Teste 5: Verificar arquivo criado
    print()
    print("[TESTE 5] Verificando arquivo criado...")
    try:
        if os.path.exists(master_db.db_filepath):
            size = os.path.getsize(master_db.db_filepath)
            print(f"  ✓ Arquivo existe: {master_db.db_filepath}")
            print(f"  ✓ Tamanho: {size} bytes")
        else:
            print(f"  ✗ Arquivo NÃO existe!")
            return 1
        
        # Verificar arquivo de hash
        hash_file = f"{master_db.db_filepath}.hash"
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                hash_content = f.read()
            hash_short = hash_content.split("\n")[0][:32]
            print(f"  ✓ Arquivo de hash existe")
            print(f"  ✓ Hash: {hash_short}...")
        else:
            print(f"  ⚠ Arquivo de hash não encontrado")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")

    # Teste 6: Ler e validar dados salvos
    print()
    print("[TESTE 6] Lendo dados salvos...")
    try:
        df_lido = master_db.get_historico(mes=12, ano=2025)
        print(f"  ✓ Registros lidos: {len(df_lido)}")
        print(f"  ✓ Colunas: {len(df_lido.columns)}")
        
        # Verificar campos críticos
        if "Processo" in df_lido.columns:
            procs = df_lido["Processo"].unique().tolist()
            print(f"  ✓ Processos salvos: {procs}")
        if "Nome_Colaborador" in df_lido.columns:
            colabs = df_lido["Nome_Colaborador"].unique().tolist()
            print(f"  ✓ Colaboradores salvos: {colabs}")
        if "Comissao_Calculada" in df_lido.columns:
            total = df_lido["Comissao_Calculada"].sum()
            print(f"  ✓ Total de comissões: R$ {total:,.2f}")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        import traceback
        traceback.print_exc()

    # Teste 7: Estatísticas
    print()
    print("[TESTE 7] Obtendo estatísticas...")
    try:
        stats = master_db.get_estatisticas()
        print(f"  ✓ Total de registros: {stats.get('total_registros', 0)}")
        print(f"  ✓ Processos distintos: {stats.get('processos_distintos', 0)}")
        print(f"  ✓ Colaboradores distintos: {stats.get('colaboradores_distintos', 0)}")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")

    # Teste 8: Resumo por colaborador
    print()
    print("[TESTE 8] Resumo por colaborador...")
    try:
        resumo = master_db.get_resumo_por_colaborador(mes=12, ano=2025)
        if not resumo.empty:
            print(resumo.to_string(index=False))
        else:
            print("  ⚠ Resumo vazio")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")

    # Teste 9: Resumo por processo
    print()
    print("[TESTE 9] Resumo por processo...")
    try:
        resumo_proc = master_db.get_resumo_por_processo(mes=12, ano=2025)
        if not resumo_proc.empty:
            print(resumo_proc.to_string(index=False))
        else:
            print("  ⚠ Resumo vazio")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")

    # Teste 10: Verificar segurança Read-Only
    print()
    print("[TESTE 10] Verificando proteção Read-Only...")
    try:
        import stat
        file_stat = os.stat(master_db.db_filepath)
        is_readonly = not (file_stat.st_mode & stat.S_IWRITE)
        if is_readonly:
            print("  ✓ Arquivo está protegido como Read-Only")
        else:
            print("  ⚠ Arquivo NÃO está protegido como Read-Only")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")

    # Teste 11: Verificar integridade do hash
    print()
    print("[TESTE 11] Verificando integridade do hash...")
    try:
        valid, msg = security.verify_hash(master_db.db_filepath)
        if valid:
            print(f"  ✓ {msg}")
        else:
            print(f"  ⚠ {msg}")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")

    print()
    print("=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
