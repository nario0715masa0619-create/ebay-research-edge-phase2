from typing import Optional, Dict, Any
from .config import AuthConfig
from .credentials import EbayOAuthCredentialProvider
from .token_cache import InMemoryTokenCache
from .token_service import EbayTokenService
from .scope_registry import OAuthScopeRegistry
from .rate_limit import RateLimiter
from .retry_policy import RetryBackoffPolicy
from .error_classifier import AuthErrorClassifier

def bootstrap_auth_layer(config: Optional[AuthConfig] = None):
    cfg = config or AuthConfig()
    
    cred_provider = EbayOAuthCredentialProvider(cfg)
    token_cache = InMemoryTokenCache()
    token_service = EbayTokenService(cfg, cred_provider, token_cache)
    scope_registry = OAuthScopeRegistry()
    rate_limiter = RateLimiter(cfg)
    retry_policy = RetryBackoffPolicy(cfg)
    error_classifier = AuthErrorClassifier()
    
    from src.ebay.api_client import EbayInventoryApiClient
    
    auth_components = {
        "config": cfg,
        "token_service": token_service,
        "scope_registry": scope_registry,
        "rate_limiter": rate_limiter,
        "retry_policy": retry_policy,
        "error_classifier": error_classifier,
        "cache": token_cache
    }
    
    api_client = EbayInventoryApiClient(auth_components)
    auth_components["api_client"] = api_client
    
    return auth_components
