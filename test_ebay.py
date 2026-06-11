import sys
sys.path.insert(0, '.')
import os

ebay_env = os.getenv("EBAY_ENVIRONMENT", "sandbox")
ebay_app_id = os.getenv("EBAY_APP_ID")
ebay_cert_id = os.getenv("EBAY_CERT_ID")
ebay_token = os.getenv("EBAY_AUTH_TOKEN")
ebay_refresh_token = os.getenv("EBAY_REFRESH_TOKEN")

print(f"eBay Environment: {ebay_env.upper()}")
if ebay_env == "sandbox":
    client_id = os.getenv("EBAY_SANDBOX_CLIENT_ID")
    client_secret = os.getenv("EBAY_SANDBOX_CLIENT_SECRET")
    print("  - Mode: SANDBOX")
else:
    client_id = os.getenv("EBAY_PROD_CLIENT_ID")
    client_secret = os.getenv("EBAY_PROD_CLIENT_SECRET")
    print("  - Mode: PRODUCTION")

print(f"  - AppID: {'✅ PRESENT' if ebay_app_id else '❌ MISSING'}")
print(f"  - CertID: {'✅ PRESENT' if ebay_cert_id else '❌ MISSING'}")
print(f"  - AuthToken: {'✅ PRESENT' if ebay_token else '❌ MISSING'}")
print(f"  - RefreshToken: {'✅ PRESENT' if ebay_refresh_token else '⚠️  MISSING'}")
print(f"  - ClientID: {'✅ PRESENT' if client_id else '❌ MISSING'}")
print(f"  - ClientSecret: {'✅ PRESENT' if client_secret else '❌ MISSING'}")

if all([ebay_app_id, ebay_cert_id, ebay_token]):
    print("eBay Auth: ✅ CREDENTIALS PRESENT")
else:
    print("eBay Auth: ❌ CRITICAL CREDENTIALS MISSING")
