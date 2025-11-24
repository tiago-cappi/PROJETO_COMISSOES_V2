import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from src.io.config_loader import ConfigLoader

def test_config_loading():
    print("Testing ConfigLoader...")
    loader = ConfigLoader()
    
    try:
        data = loader.load_configs("config/REGRAS_COMISSOES.xlsx")
        print("Successfully loaded configuration!")
        print(f"Keys found: {list(data.keys())}")
        
        required_keys = ["PARAMS", "CONFIG_COMISSAO", "COLABORADORES", "ALIASES"]
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f"ERROR: Missing required keys: {missing}")
            sys.exit(1)
            
        print("All required keys present.")
        
        # Check row counts for sample
        print(f"ALIASES rows: {len(data.get('ALIASES', []))}")
        print(f"COLABORADORES rows: {len(data.get('COLABORADORES', []))}")
        
    except Exception as e:
        print(f"FAILED to load config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_config_loading()
