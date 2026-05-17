from typing import Any, Dict

class NotificationCliMasker:
    def __init__(self):
        self.secret_keys = ["token", "secret", "password", "key", "auth", "webhook"]

    def mask_value(self, key: str, value: Any) -> Any:
        if not value:
            return value
        if any(sk in key.lower() for sk in self.secret_keys):
            return "***MASKED***"
        return value

    def mask_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        if not d:
            return d
        masked = {}
        for k, v in d.items():
            if isinstance(v, dict):
                masked[k] = self.mask_dict(v)
            else:
                masked[k] = self.mask_value(k, v)
        return masked

    def mask_text(self, text: str) -> str:
        if not text:
            return text
        # Simple string-based masking for known patterns if needed
        # For now, we assume critical secrets are in meta_json or headers
        return text
