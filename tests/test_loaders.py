"""
Arquivo de testes para validar os módulos ConfigLoader e DataLoader.
Execute este arquivo para verificar se os loaders estão funcionando corretamente.
"""

import os
import sys
import pandas as pd

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io.config_loader import ConfigLoader
from src.io.data_loader import DataLoader
from src.utils.logging import ValidationLogger


def test_config_loader():
    """Testa o ConfigLoader com arquivos reais."""
    print("\n=== Testando ConfigLoader ===")
    
    logger = ValidationLogger()
    loader = ConfigLoader(validation_logger=logger)
    
    # Tentar carregar configurações
    try:
        config_path = os.path.join("config", "REGRAS_COMISSOES.xlsx")
        if not os.path.exists(config_path):
            config_path = "config/REGRAS_COMISSOES.xlsx"
        
        config_data = loader.load_configs(config_path)
        
        # Verificar se carregou pelo menos algumas abas essenciais
        abas_esperadas = ["PARAMS", "CONFIG_COMISSAO", "PESOS_METAS", "COLABORADORES"]
        abas_encontradas = [aba for aba in abas_esperadas if aba in config_data]
        
        assert len(abas_encontradas) > 0, f"Nenhuma aba esperada foi encontrada. Abas disponíveis: {list(config_data.keys())}"
        print(f"[OK] ConfigLoader carregou {len(config_data)} aba(s) de configuração")
        print(f"[OK] Abas essenciais encontradas: {abas_encontradas}")
        
        # Testar processamento de PARAMS
        if "PARAMS" in config_data and not config_data["PARAMS"].empty:
            params = loader.process_params(config_data["PARAMS"])
            assert isinstance(params, dict), "process_params deve retornar um dicionário"
            assert "cross_selling_default_option" in params, "params deve conter cross_selling_default_option"
            print("[OK] Processamento de PARAMS funcionou corretamente")
        else:
            print("[AVISO] PARAMS não encontrado ou vazio")
        
        # Testar detecção de colaboradores que recebem por recebimento
        recebe_set = loader.detect_recebimento_colaboradores(config_data)
        assert isinstance(recebe_set, set), "detect_recebimento_colaboradores deve retornar um set"
        print(f"[OK] Detecção de colaboradores que recebem por recebimento: {len(recebe_set)} colaborador(es)")
        
        # Verificar logs de validação
        logs = logger.get_logs()
        if logs:
            print(f"[INFO] {len(logs)} log(s) de validação gerado(s)")
        
        print("[OK] Todos os testes de ConfigLoader passaram!\n")
        return True
    except Exception as e:
        print(f"[ERRO] Falha no teste de ConfigLoader: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loader():
    """Testa o DataLoader com arquivos reais (se existirem)."""
    print("\n=== Testando DataLoader ===")
    
    logger = ValidationLogger()
    loader = DataLoader(validation_logger=logger)
    
    # Usar mês/ano atual como padrão
    from datetime import datetime
    mes = datetime.now().month
    ano = datetime.now().year
    
    try:
        # Tentar carregar dados de entrada
        input_data = loader.load_input_data(
            mes=mes,
            ano=ano,
            base_path=".",
        )
        
        # Verificar se retornou um dicionário
        assert isinstance(input_data, dict), "load_input_data deve retornar um dicionário"
        print(f"[OK] DataLoader retornou {len(input_data)} tipo(s) de dados")
        
        # Verificar se os DataFrames esperados estão presentes (mesmo que vazios)
        dados_esperados = [
            "FATURADOS",
            "CONVERSOES",
            "RENTABILIDADE_REALIZADA",
            "RETENCAO_CLIENTES",
            "FATURADOS_YTD",
            "RECEBIMENTOS",
            "PAGAMENTOS_REGULARES",
            "ANALISE_COMERCIAL_COMPLETA",
            "STATUS_PAGAMENTOS",
        ]
        
        dados_encontrados = [dado for dado in dados_esperados if dado in input_data]
        print(f"[OK] Dados encontrados: {dados_encontrados}")
        
        # Verificar que todos os valores são DataFrames
        for key, value in input_data.items():
            assert isinstance(value, pd.DataFrame), f"{key} deve ser um DataFrame, mas é {type(value)}"
        
        print("[OK] Todos os valores são DataFrames válidos")
        
        # Testar função de rentabilidade especificamente
        rent_df = loader.load_rentabilidade(mes, ano, ".")
        assert isinstance(rent_df, pd.DataFrame), "load_rentabilidade deve retornar um DataFrame"
        print(f"[OK] load_rentabilidade retornou DataFrame com {len(rent_df)} linha(s)")
        
        # Verificar logs de validação
        logs = logger.get_logs()
        if logs:
            print(f"[INFO] {len(logs)} log(s) de validação gerado(s)")
        
        print("[OK] Todos os testes de DataLoader passaram!\n")
        return True
    except Exception as e:
        print(f"[ERRO] Falha no teste de DataLoader: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Testa a integração dos dois loaders juntos."""
    print("\n=== Testando Integração ConfigLoader + DataLoader ===")
    
    try:
        logger = ValidationLogger()
        
        # Carregar configurações
        config_loader = ConfigLoader(validation_logger=logger)
        config_path = os.path.join("config", "REGRAS_COMISSOES.xlsx")
        if not os.path.exists(config_path):
            config_path = "config/REGRAS_COMISSOES.xlsx"
        
        config_data = config_loader.load_configs(config_path)
        
        # Processar PARAMS
        if "PARAMS" in config_data and not config_data["PARAMS"].empty:
            params = config_loader.process_params(config_data["PARAMS"])
            
            # Carregar dados de entrada usando mes/ano dos params (se disponível)
            from datetime import datetime
            mes = int(params.get("mes_apuracao", datetime.now().month)) if params.get("mes_apuracao") else datetime.now().month
            ano = int(params.get("ano_apuracao", datetime.now().year)) if params.get("ano_apuracao") else datetime.now().year
            
            data_loader = DataLoader(validation_logger=logger)
            input_data = data_loader.load_input_data(mes=mes, ano=ano, base_path=".")
            
            # Combinar dados
            all_data = {**config_data, **input_data}
            
            print(f"[OK] Integração bem-sucedida: {len(all_data)} tipo(s) de dados carregados")
            print(f"[OK] Configurações: {len(config_data)} tipo(s)")
            print(f"[OK] Dados de entrada: {len(input_data)} tipo(s)")
            
            return True
        else:
            print("[AVISO] PARAMS não encontrado, pulando teste de integração")
            return True
    except Exception as e:
        print(f"[ERRO] Falha no teste de integração: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("TESTES DE VALIDACAO DOS LOADERS (ConfigLoader e DataLoader)")
    print("=" * 60)
    
    resultados = []
    
    try:
        resultados.append(("ConfigLoader", test_config_loader()))
        resultados.append(("DataLoader", test_data_loader()))
        resultados.append(("Integração", test_integration()))
        
        print("=" * 60)
        sucessos = sum(1 for _, sucesso in resultados if sucesso)
        total = len(resultados)
        
        if sucessos == total:
            print(f"[SUCESSO] TODOS OS TESTES PASSARAM ({sucessos}/{total})!")
        else:
            print(f"[ATENCAO] {sucessos}/{total} teste(s) passaram")
            for nome, sucesso in resultados:
                status = "[OK]" if sucesso else "[FALHA]"
                print(f"  {status} {nome}")
        
        print("=" * 60)
        return 0 if sucessos == total else 1
    except Exception as e:
        print(f"\n[ERRO] ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

