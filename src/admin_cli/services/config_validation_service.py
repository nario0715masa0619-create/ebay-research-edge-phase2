import os
from typing import List, Optional, Dict, Any
from ..models import CliCommandResult

class ConfigValidationService:
    def validate(self) -> Dict[str, Any]:
        required_env = [
            "DATABASE_URL",
            "EBAY_CLIENT_ID",
            "EBAY_CLIENT_SECRET",
            "EBAY_REFRESH_TOKEN",
            "EBAY_ENVIRONMENT"
        ]
        
        checks = {}
        all_ok = True
        for env in required_env:
            val = os.environ.get(env)
            if not val:
                checks[env] = {"status": "missing", "message": "Environment variable not set."}
                all_ok = False
            else:
                checks[env] = {"status": "ok", "message": "Present (masked)." if "SECRET" in env or "TOKEN" in env else f"Value: {val}"}
                
        return {
            "status": "ok" if all_ok else "fail",
            "checks": checks
        }
