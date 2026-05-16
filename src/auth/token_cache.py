from typing import Dict, Optional
from .models import TokenInfo

class InMemoryTokenCache:
    def __init__(self):
        # Key: fingerprint (token_type + scopes + seller_id)
        self._cache: Dict[str, TokenInfo] = {}

    def get(self, token_type: str, scopes: str, seller_id: Optional[str] = None) -> Optional[TokenInfo]:
        key = self._build_key(token_type, scopes, seller_id)
        return self._cache.get(key)

    def set(self, token_info: TokenInfo):
        key = self._build_key(token_info.token_type, " ".join(sorted(token_info.scopes)), token_info.seller_account_id)
        self._cache[key] = token_info

    def invalidate(self, token_type: str, scopes: str, seller_id: Optional[str] = None):
        key = self._build_key(token_type, scopes, seller_id)
        if key in self._cache:
            del self._cache[key]

    def _build_key(self, token_type: str, scopes: str, seller_id: Optional[str]) -> str:
        return f"{token_type}:{scopes}:{seller_id or 'GLOBAL'}"
