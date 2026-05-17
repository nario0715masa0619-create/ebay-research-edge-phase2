import os
from typing import Dict, List, Optional
from .config import AuthConfig
from src.seller_env.config_resolver import SellerConfigResolver

class EbayOAuthCredentialProvider:
    def __init__(self, config: AuthConfig, seller_resolver: Optional[SellerConfigResolver] = None):
        self.config = config
        self.seller_resolver = seller_resolver

    def get_client_credentials(self, seller_account_id: str = None, environment_type: str = None) -> Dict[str, str]:
        if self.seller_resolver and (seller_account_id or environment_type):
            ctx = self.seller_resolver.resolve_context(seller_account_id, environment_type)
            # In a real system, we'd look up keyset by ctx.auth_profile_ref
            # For v0.1, if it's sandbox, we return sandbox keys from config
            if ctx.environment_type == "sandbox":
                return {
                    "client_id": os.environ.get("EBAY_SANDBOX_CLIENT_ID", self.config.ebay_client_id),
                    "client_secret": os.environ.get("EBAY_SANDBOX_CLIENT_SECRET", self.config.ebay_client_secret)
                }
            else:
                return {
                    "client_id": os.environ.get("EBAY_PROD_CLIENT_ID", self.config.ebay_client_id),
                    "client_secret": os.environ.get("EBAY_PROD_CLIENT_SECRET", self.config.ebay_client_secret)
                }
        
        return {
            "client_id": self.config.ebay_client_id,
            "client_secret": self.config.ebay_client_secret
        }

    def get_refresh_token(self, seller_account_id: str = None, environment_type: str = None) -> Optional[str]:
        if self.seller_resolver and (seller_account_id or environment_type):
            ctx = self.seller_resolver.resolve_context(seller_account_id, environment_type)
            # Find binding to get refresh_token_ref
            binding = self.seller_resolver._find_binding_by_type(ctx.seller_account_id, ctx.environment_type)
            if binding and binding.refresh_token_ref:
                return os.environ.get(binding.refresh_token_ref)
        
        return self.config.ebay_refresh_token

    def get_oauth_url(self, seller_account_id: str = None, environment_type: str = None) -> str:
        if self.seller_resolver and (seller_account_id or environment_type):
            ctx = self.seller_resolver.resolve_context(seller_account_id, environment_type)
            if ctx.environment_type == "sandbox":
                return "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            else:
                return "https://api.ebay.com/identity/v1/oauth2/token"
        return self.config.ebay_oauth_url
