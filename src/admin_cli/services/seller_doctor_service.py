import os
from typing import List, Dict, Any
from src.seller_env.config_resolver import SellerConfigResolver
from src.seller_env.environment_guard import EnvironmentGuard

class SellerDoctorService:
    def __init__(self, resolver: SellerConfigResolver, guard: EnvironmentGuard):
        self.resolver = resolver
        self.guard = guard

    def diagnose_seller(self, seller_account_id: str) -> Dict[str, Any]:
        report = {
            "seller_account_id": seller_account_id,
            "status": "ok",
            "checks": []
        }
        
        try:
            # 1. Resolve context
            ctx = self.resolver.resolve_context(seller_account_id)
            report["checks"].append({"name": "context_resolution", "status": "pass"})
            
            # 2. Check credentials
            binding = self.resolver._find_binding_by_type(seller_account_id, ctx.environment_type)
            if not binding or not binding.refresh_token_ref:
                report["checks"].append({"name": "refresh_token_config", "status": "fail", "message": "Missing refresh token reference."})
            else:
                token = os.environ.get(binding.refresh_token_ref)
                if not token:
                    report["checks"].append({"name": "refresh_token_presence", "status": "fail", "message": f"Environment variable {binding.refresh_token_ref} is empty."})
                else:
                    report["checks"].append({"name": "refresh_token_presence", "status": "pass"})

            # 3. Check environment URLs
            api_url = "https://api.sandbox.ebay.com" if ctx.environment_type == "sandbox" else "https://api.ebay.com"
            try:
                self.guard.check_auth_integration(ctx, api_url)
                report["checks"].append({"name": "environment_guard", "status": "pass"})
            except Exception as e:
                report["checks"].append({"name": "environment_guard", "status": "fail", "message": str(e)})

        except Exception as e:
            report["status"] = "error"
            report["error"] = str(e)
            
        if any(c["status"] == "fail" for c in report["checks"]):
            report["status"] = "fail"
            
        return report
