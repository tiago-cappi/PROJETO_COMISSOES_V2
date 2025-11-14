"""
Script para adicionar dados de rentabilidade fictícios para testes de reconciliação.

Este script:
1. Lê o arquivo de rentabilidade existente (se houver)
2. Adiciona linhas de rentabilidade para os produtos de teste
3. Salva o arquivo atualizado

Os valores de rentabilidade são escolhidos para testar diferentes cenários:
- Produtos com rentabilidade BAIXA (< meta) → FC < 1.0 → reconciliação negativa
- Serviços com rentabilidade ALTA (≈ meta) → FC ≈ 1.0 → sem reconciliação
- Reposição com rentabilidade MUITO BAIXA → FC muito baixo
"""

import pandas as pd
import os
from pathlib import Path

def gerar_rentabilidade_teste():
    """Gera ou atualiza arquivo de rentabilidade com dados de teste."""
    
    print("=" * 80)
    print("GERADOR DE RENTABILIDADE PARA TESTES")
    print("=" * 80)
    print()
    
    # Caminho do arquivo
    base_path = Path(__file__).parent
    rentabilidade_dir = base_path / "dados_entrada" / "rentabilidades"
    arquivo_rentabilidade = rentabilidade_dir / "rentabilidade_08_2025_agrupada.xlsx"
    
    # Criar diretório se não existir
    rentabilidade_dir.mkdir(parents=True, exist_ok=True)
    
    # Dados de rentabilidade para teste
    # Meta de rentabilidade para SSO = 33.3% (conforme CONFIG)
    dados_teste = [
        {
            "Negócio": "SSO",
            "Grupo": "Analisador Fixo",
            "Subgrupo": "Falco",
            "Tipo de Mercadoria": "Produto",
            "rentabilidade_realizada_pct": 25.5,  # Abaixo da meta → FC < 1.0
            "observacao": "TESTE: Rentabilidade baixa para gerar reconciliação negativa"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Analisador Fixo",
            "Subgrupo": "Titan",
            "Tipo de Mercadoria": "Produto",
            "rentabilidade_realizada_pct": 28.3,  # Abaixo da meta → FC < 1.0
            "observacao": "TESTE: Rentabilidade baixa para gerar reconciliação negativa"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Analisador Portátil",
            "Subgrupo": "Acessório",
            "Tipo de Mercadoria": "Produto",
            "rentabilidade_realizada_pct": 30.2,  # Abaixo da meta → FC < 1.0
            "observacao": "TESTE: Rentabilidade baixa para gerar reconciliação negativa"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Analisador Fixo",
            "Subgrupo": "Acessório",
            "Tipo de Mercadoria": "Reposição",
            "rentabilidade_realizada_pct": 18.7,  # MUITO abaixo da meta → FC muito baixo
            "observacao": "TESTE: Rentabilidade muito baixa para gerar reconciliação mais negativa"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Diversos Diversos",
            "Subgrupo": "Calibração",
            "Tipo de Mercadoria": "Serviço",
            "rentabilidade_realizada_pct": 33.5,  # Próximo da meta → FC ≈ 1.0
            "observacao": "TESTE: Rentabilidade próxima da meta para FC ≈ 1.0 (sem reconciliação)"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Analisador Portátil",
            "Subgrupo": "Filtro",
            "Tipo de Mercadoria": "Insumo",
            "rentabilidade_realizada_pct": 22.4,  # Baixo
            "observacao": "TESTE: Rentabilidade baixa"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Calibração Diversos",
            "Subgrupo": "Cilindro",
            "Tipo de Mercadoria": "Insumo",
            "rentabilidade_realizada_pct": 26.8,  # Baixo
            "observacao": "TESTE: Rentabilidade baixa"
        },
        {
            "Negócio": "SSO",
            "Grupo": "Analisador Portátil",
            "Subgrupo": "Acessório",
            "Tipo de Mercadoria": "Reposição",
            "rentabilidade_realizada_pct": 20.1,  # MUITO baixo
            "observacao": "TESTE: Rentabilidade muito baixa"
        },
    ]
    
    print("1. Verificando arquivo existente...")
    
    # Tentar ler arquivo existente
    if arquivo_rentabilidade.exists():
        print(f"   ✓ Arquivo encontrado: {arquivo_rentabilidade}")
        try:
            df_existente = pd.read_excel(arquivo_rentabilidade)
            print(f"   ✓ Arquivo carregado: {len(df_existente)} linhas existentes")
            
            # Remover coluna 'observacao' se existir no arquivo original
            if 'observacao' in df_existente.columns:
                df_existente = df_existente.drop(columns=['observacao'])
        except Exception as e:
            print(f"   ⚠ Erro ao ler arquivo existente: {e}")
            print("   → Criando arquivo novo")
            df_existente = pd.DataFrame()
    else:
        print(f"   ⚠ Arquivo não encontrado: {arquivo_rentabilidade}")
        print("   → Criando arquivo novo")
        df_existente = pd.DataFrame()
    
    print()
    print("2. Preparando dados de teste...")
    df_teste = pd.DataFrame(dados_teste)
    
    # Remover coluna 'observacao' antes de salvar
    df_teste_sem_obs = df_teste.drop(columns=['observacao'])
    
    print(f"   ✓ {len(df_teste)} linhas de teste criadas")
    print()
    print("   Detalhes dos dados de teste:")
    for i, row in df_teste.iterrows():
        print(f"   - {row['Negócio']} → {row['Grupo']} → {row['Subgrupo']} → {row['Tipo de Mercadoria']}")
        print(f"     Rentabilidade: {row['rentabilidade_realizada_pct']:.1f}%")
        print(f"     {row['observacao']}")
    
    print()
    print("3. Mesclando dados...")
    
    if not df_existente.empty:
        # Remover linhas duplicadas (caso já existam dados de teste)
        # Criar chave única para identificar duplicatas
        chave_cols = ['Negócio', 'Grupo', 'Subgrupo', 'Tipo de Mercadoria']
        
        # Marcar linhas do arquivo existente que devem ser removidas
        df_existente['_chave'] = df_existente[chave_cols].apply(
            lambda x: tuple(x), axis=1
        )
        df_teste_sem_obs['_chave'] = df_teste_sem_obs[chave_cols].apply(
            lambda x: tuple(x), axis=1
        )
        
        chaves_teste = set(df_teste_sem_obs['_chave'])
        df_existente_filtrado = df_existente[~df_existente['_chave'].isin(chaves_teste)]
        
        # Remover coluna auxiliar
        df_existente_filtrado = df_existente_filtrado.drop(columns=['_chave'])
        df_teste_sem_obs = df_teste_sem_obs.drop(columns=['_chave'])
        
        removidas = len(df_existente) - len(df_existente_filtrado)
        if removidas > 0:
            print(f"   ⚠ {removidas} linha(s) duplicada(s) removida(s)")
        
        # Concatenar
        df_final = pd.concat([df_existente_filtrado, df_teste_sem_obs], ignore_index=True)
        print(f"   ✓ Dados mesclados: {len(df_existente_filtrado)} existentes + {len(df_teste_sem_obs)} teste = {len(df_final)} total")
    else:
        df_final = df_teste_sem_obs
        print(f"   ✓ Arquivo novo criado com {len(df_final)} linhas")
    
    print()
    print("4. Salvando arquivo...")
    
    try:
        df_final.to_excel(arquivo_rentabilidade, index=False)
        print(f"   ✓ Arquivo salvo: {arquivo_rentabilidade}")
        print(f"   ✓ Total de linhas: {len(df_final)}")
        
        # Verificar se o arquivo foi criado
        if arquivo_rentabilidade.exists():
            tamanho = arquivo_rentabilidade.stat().st_size
            print(f"   ✓ Tamanho do arquivo: {tamanho:,} bytes")
        else:
            print("   ✗ ERRO: Arquivo não foi criado!")
            return False
            
    except PermissionError:
        print()
        print("   ✗ ERRO: Arquivo está aberto no Excel!")
        print("   → Feche o arquivo e execute novamente")
        return False
    except Exception as e:
        print(f"   ✗ ERRO ao salvar: {e}")
        return False
    
    print()
    print("=" * 80)
    print("✅ RENTABILIDADE DE TESTE GERADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("RESUMO:")
    print(f"  • Arquivo: {arquivo_rentabilidade.name}")
    print(f"  • Total de linhas: {len(df_final)}")
    print(f"  • Linhas de teste adicionadas: {len(df_teste)}")
    print()
    print("PRÓXIMO PASSO:")
    print("  Execute novamente: python calculo_comissoes.py --mes 8 --ano 2025")
    print()
    print("VALORES DE TESTE (Meta SSO = 33.3%):")
    print()
    for i, row in df_teste.iterrows():
        rent = row['rentabilidade_realizada_pct']
        meta = 33.3
        ating = rent / meta
        fc_comp = ating * 0.2  # Peso = 0.2 para adiantamento
        fc_total = 0.15 + fc_comp
        fc_final = min(fc_total, 0.4)
        
        print(f"  • {row['Subgrupo']} ({row['Tipo de Mercadoria']})")
        print(f"    - Rentabilidade: {rent:.1f}% (meta: {meta:.1f}%)")
        print(f"    - Atingimento: {ating:.2%}")
        print(f"    - FC esperado: {fc_final:.4f}")
        
        if fc_final < 1.0:
            print(f"    - ⚠️  RECONCILIAÇÃO NEGATIVA esperada")
        else:
            print(f"    - ✅ Sem reconciliação (FC = 1.0)")
        print()
    
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    sucesso = gerar_rentabilidade_teste()
    
    if not sucesso:
        print()
        print("❌ Falha ao gerar rentabilidade de teste")
        exit(1)

