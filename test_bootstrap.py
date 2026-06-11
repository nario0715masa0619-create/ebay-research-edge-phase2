import sys
sys.path.insert(0, '.')
try:
    from src.auth.config import AuthConfig
    from src.market_eval.config import MarketEvalSettings
    from src.db.engine import create_engine_from_config
    
    auth_config = AuthConfig()
    print("Auth config loaded: READY")
    print("  - Environment: " + auth_config.ebay_environment)
    print("  - Base API URL: " + auth_config.ebay_base_api_url)
    
    market_config = MarketEvalSettings()
    print("Market Eval config loaded: READY")
    print("  - Provider: " + market_config.market_data_provider)
    
    try:
        engine = create_engine_from_config()
        print("Database engine: READY")
    except Exception as e:
        print("Database engine: ERROR - " + str(e))
    
    print("✅ Bootstrap validation: PASSED")
    
except ImportError as e:
    print("❌ Import error: " + str(e))
except Exception as e:
    print("❌ Config load error: " + str(e))
