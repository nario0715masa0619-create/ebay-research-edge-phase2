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
        cache: InMemoryTokenCache,
        notification_dispatcher: Any = None
    ):
        self.config = config
        self.credential_provider = credential_provider
        self.cache = cache
        self.notification_dispatcher = notification_dispatcher

    def get_app_access_token(self, scopes: List[str], seller_account_id: Optional[str] = None, environment_type: Optional[str] = None) -> TokenInfo:
        scope_str = " ".join(sorted(scopes))
        if self.config.auth_enable_token_cache:
            cached = self.cache.get("Application", scope_str, seller_account_id)
            if cached and not cached.is_expired(self.config.auth_refresh_lead_seconds):
                cached.source_type = "cache"
                return cached

        # Mint new token
        token_info = self._mint_app_token(scopes, seller_account_id, environment_type)
        if self.config.auth_enable_token_cache:
            self.cache.set(token_info)
        return token_info

    def get_user_access_token(self, scopes: List[str], seller_account_id: Optional[str] = None, environment_type: Optional[str] = None, force: bool = False) -> TokenInfo:
        scope_str = " ".join(sorted(scopes))
        if self.config.auth_enable_token_cache and not force:
            cached = self.cache.get("User", scope_str, seller_account_id)
            if cached and not cached.is_expired(self.config.auth_refresh_lead_seconds):
                cached.source_type = "cache"
                return cached

        # Mint/Refresh user token
        token_info = self._refresh_user_token(scopes, seller_account_id, environment_type)
        if self.config.auth_enable_token_cache:
            self.cache.set(token_info)
        return token_info

    def refresh_user_access_token(self, scopes: List[str], seller_account_id: Optional[str] = None, environment_type: Optional[str] = None, force: bool = True) -> TokenInfo:
        # Alias for get_user_access_token with force=True by default
        return self.get_user_access_token(scopes, seller_account_id, environment_type, force=force)

    def _mint_app_token(self, scopes: List[str], seller_account_id: Optional[str] = None, environment_type: Optional[str] = None) -> TokenInfo:
        creds = self.credential_provider.get_client_credentials(seller_account_id, environment_type)
        auth_header = self._build_basic_auth_header(creds["client_id"], creds["client_secret"])
        
        data = {
            "grant_type": "client_credentials",
            "scope": " ".join(scopes)
        }
        
        response = httpx.post(
            self.credential_provider.get_oauth_url(seller_account_id, environment_type),
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
            seller_account_id=seller_account_id,
            environment=environment_type or self.config.ebay_environment,
            source_type="mint"
        )

    def _refresh_user_token(self, scopes: List[str], seller_account_id: Optional[str], environment_type: Optional[str] = None) -> TokenInfo:
        refresh_token = self.credential_provider.get_refresh_token(seller_account_id, environment_type)
        if not refresh_token:
            raise ValueError(f"No refresh token available for Seller {seller_account_id} in {environment_type}")

        creds = self.credential_provider.get_client_credentials(seller_account_id, environment_type)
        auth_header = self._build_basic_auth_header(creds["client_id"], creds["client_secret"])
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(scopes)
        }
        
        response = httpx.post(
            self.credential_provider.get_oauth_url(seller_account_id, environment_type),
            headers={"Authorization": auth_header, "Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=self.config.auth_request_timeout_seconds
        )
        try:
            response.raise_for_status()
        except Exception as e:
            self._notify_auth_failure("auth_refresh_failed", str(e), seller_account_id)
            raise
        res_json = response.json()
        
        return TokenInfo(
            token_type="User",
            access_token=res_json["access_token"],
            expires_at=datetime.now() + timedelta(seconds=res_json["expires_in"]),
            scopes=scopes,
            seller_account_id=seller_account_id,
            environment=environment_type or self.config.ebay_environment,
            source_type="refresh"
        )

    def _build_basic_auth_header(self, client_id: str, client_secret: str) -> str:
        creds_str = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(creds_str.encode("ascii")).decode("ascii")
        return f"Basic {encoded}"

    def build_auth_header(self, token_info: TokenInfo) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token_info.access_token}"}

    def _notify_auth_failure(self, event_type: str, message: str, seller_account_id: Optional[str] = None):
        if not self.notification_dispatcher:
            return
            
        from src.notification.models import NotificationEvent
        event = NotificationEvent(
            event_type=event_type,
            source_layer="auth",
            source_component="EbayTokenService",
            title="Ebay Auth Failure",
            summary=message,
            severity="critical",
            priority="urgent",
            seller_account_id=seller_account_id
        )
        self.notification_dispatcher.notify(event)
