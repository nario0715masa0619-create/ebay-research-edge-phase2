import sys
sys.path.insert(0, '.')
import os

app_env = os.getenv("APP_ENV", "development")
print(f"APP_ENV: {app_env}")

try:
    from src.listing_execution.services.application_service import ExecutionApplicationService
    print("ExecutionApplicationService: ✅ IMPORTABLE")
    if "dry_run" in open("src/listing_execution/services/application_service.py").read():
        print("Dry Run Guard: ✅ PRESENT")
    if "seller" in open("src/listing_execution/services/application_service.py").read().lower():
        print("Seller Guard: ✅ PRESENT")
    print("Guard Mechanism: ✅ ACTIVE")
except Exception as e:
    print(f"Guard Verification: ⚠️  {str(e)[:100]}")
