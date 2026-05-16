from typing import Optional, List
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

class AuthConfig(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # eBay Credentials
    ebay_environment: str = Field("sandbox", env="EBAY_ENVIRONMENT")
    ebay_client_id: str = Field("DUMMY_ID", env="EBAY_CLIENT_ID")
    ebay_client_secret: str = Field("DUMMY_SECRET", env="EBAY_CLIENT_SECRET")
    ebay_redirect_uri: str = Field("https://localhost", env="EBAY_REDIRECT_URI")
    ebay_refresh_token: Optional[str] = Field(None, env="EBAY_REFRESH_TOKEN")
    
    # eBay API URLs
    ebay_base_api_url: str = Field("https://api.sandbox.ebay.com", env="EBAY_BASE_API_URL")
    ebay_oauth_url: str = Field("https://api.sandbox.ebay.com/identity/v1/oauth2/token", env="EBAY_OAUTH_URL")
    
    # Auth behavior
    auth_refresh_lead_seconds: int = Field(300, env="AUTH_REFRESH_LEAD_SECONDS")
    auth_request_timeout_seconds: int = Field(30, env="AUTH_REQUEST_TIMEOUT_SECONDS")
    auth_enable_token_cache: bool = Field(True, env="AUTH_ENABLE_TOKEN_CACHE")
    auth_token_cache_backend: str = Field("memory", env="AUTH_TOKEN_CACHE_BACKEND")
    
    # Resilience & Rate Limit
    auth_enable_rate_limit: bool = Field(True, env="AUTH_ENABLE_RATE_LIMIT")
    auth_default_max_retry: int = Field(3, env="AUTH_DEFAULT_MAX_RETRY")
    auth_default_backoff_seconds: float = Field(1.0, env="AUTH_DEFAULT_BACKOFF_SECONDS")
    auth_max_backoff_seconds: float = Field(30.0, env="AUTH_MAX_BACKOFF_SECONDS")
    
    rate_limit_default_rps: float = Field(5.0, env="RATE_LIMIT_DEFAULT_RPS")
    rate_limit_default_burst: int = Field(10, env="RATE_LIMIT_DEFAULT_BURST")
    rate_limit_429_cooldown_seconds: int = Field(60, env="RATE_LIMIT_429_COOLDOWN_SECONDS")
