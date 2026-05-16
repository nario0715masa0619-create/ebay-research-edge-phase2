import base64
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .config import AuthConfig
from .models import TokenInfo
from .token_cache import InMemoryTokenCache
from .credentials import EbayOAuthCredentialProvider

class EbayTokenService:
    def __init__(
        self, 
        config: AuthConfig, 
        credential_provider: EbayOAuthCredentialProvider,
        cache: InMemoryTokenCache
    ):
        self.config = config
        self.credential_provider = credential_provider
        self.cache = cache

    def get_app_access_token(self, scopes: List[str]) -> TokenInfo:
        scope_str = " ".join(sorted(scopes))
        if self.config.auth_enable_token_cache:
            cached = self.cache.get("Application", scope_str)
            if cached and not cached.is_expired(self.config.auth_refresh_lead_seconds):
                cached.source_type = "cache"
                return cached

        # Mint new token
        token_info = self._mint_app_token(scopes)
        if self.config.auth_enable_token_cache:
            self.cache.set(token_info)
        return token_info

    def get_user_access_token(self, scopes: List[str], seller_account_id: Optional[str] = None, force: bool = False) -> TokenInfo:
        scope_str = " ".join(sorted(scopes))
        if self.config.auth_enable_token_cache and not force:
            cached = self.cache.get("User", scope_str, seller_account_id)
            if cached and not cached.is_expired(self.config.auth_refresh_lead_seconds):
                cached.source_type = "cache"
                return cached

        # Mint/Refresh user token
        token_info = self._refresh_user_token(scopes, seller_account_id)
        if self.config.auth_enable_token_cache:
            self.cache.set(token_info)
        return token_info

    def refresh_user_access_token(self, scopes: List[str], seller_account_id: Optional[str] = None, force: bool = True) -> TokenInfo:
        # Alias for get_user_access_token with force=True by default
        return self.get_user_access_token(scopes, seller_account_id, force=force)

    def _mint_app_token(self, scopes: List[str]) -> TokenInfo:
        creds = self.credential_provider.get_client_credentials()
        auth_header = self._build_basic_auth_header(creds["client_id"], creds["client_secret"])
        
        data = {
            "grant_type": "client_credentials",
            "scope": " ".join(scopes)
        }
        
        response = httpx.post(
            self.credential_provider.get_oauth_url(),
            headers={"Authorization": auth_header, "Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=self.config.auth_request_timeout_seconds
        )
        response.raise_for_status()
        res_json = response.json()
        
        return TokenInfo(
            token_type="Application",
            access_token=res_json["access_token"],
            expires_at=datetime.now() + timedelta(seconds=res_json["expires_in"]),
            scopes=scopes,
            environment=self.config.ebay_environment,
            source_type="mint"
        )

    def _refresh_user_token(self, scopes: List[str], seller_account_id: Optional[str]) -> TokenInfo:
        refresh_token = self.credential_provider.get_refresh_token()
        if not refresh_token:
            raise ValueError("No refresh token available for User token minting")

        creds = self.credential_provider.get_client_credentials()
        auth_header = self._build_basic_auth_header(creds["client_id"], creds["client_secret"])
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(scopes)
        }
        
        response = httpx.post(
            self.credential_provider.get_oauth_url(),
            headers={"Authorization": auth_header, "Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=self.config.auth_request_timeout_seconds
        )
        response.raise_for_status()
        res_json = response.json()
        
        return TokenInfo(
            token_type="User",
            access_token=res_json["access_token"],
            expires_at=datetime.now() + timedelta(seconds=res_json["expires_in"]),
            scopes=scopes,
            seller_account_id=seller_account_id,
            environment=self.config.ebay_environment,
            source_type="refresh"
        )

    def _build_basic_auth_header(self, client_id: str, client_secret: str) -> str:
        creds_str = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(creds_str.encode("ascii")).decode("ascii")
        return f"Basic {encoded}"

    def build_auth_header(self, token_info: TokenInfo) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token_info.access_token}"}
