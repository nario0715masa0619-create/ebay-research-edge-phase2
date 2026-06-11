import sys
sys.path.insert(0, '.')
import os

print("E2E Execution Path: STARTING")
try:
    from src.auth.config import AuthConfig
    from src.market_eval.config import MarketEvalSettings
    print("✅ Step 1: Config Loaded")
    
    try:
        from src.auth.ebay_auth import EbayAuth
        auth = EbayAuth()
        print("✅ Step 2: Auth Initialized")
    except Exception as auth_err:
        print(f"❌ Step 2 Auth Error: {str(auth_err)}")
        raise auth_err
        
except Exception as e:
    print(f"❌ E2E Failed at: {str(e)[:150]}")
    print("Safe E2E Execution: ❌ BLOCKED")
