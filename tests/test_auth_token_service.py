import pytest
import respx
import httpx
from datetime import datetime, timedelta
from src.auth.config import AuthConfig
from src.auth.models import TokenInfo
from src.auth.token_service import EbayTokenService
from src.auth.token_cache import InMemoryTokenCache
from src.auth.credentials import EbayOAuthCredentialProvider

@pytest.fixture
def auth_config():
    return AuthConfig(
        ebay_client_id="test_id",
        ebay_client_secret="test_secret",
        ebay_refresh_token="test_refresh_token"
    )

@pytest.fixture
def token_service(auth_config):
    cred_provider = EbayOAuthCredentialProvider(auth_config)
    cache = InMemoryTokenCache()
    return EbayTokenService(auth_config, cred_provider, cache)

@respx.mock
def test_get_app_access_token_mint(token_service):
    # Mock OAuth response
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "app_token_123",
            "expires_in": 7200,
            "token_type": "User Access Token"
        })
    )
    
    token = token_service.get_app_access_token(["https://api.ebay.com/oauth/api_scope/commerce.taxonomy.readonly"])
    assert token.access_token == "app_token_123"
    assert token.token_type == "Application"
    
    # Check cache
    cached = token_service.cache.get("Application", "https://api.ebay.com/oauth/api_scope/commerce.taxonomy.readonly")
    assert cached.access_token == "app_token_123"

@respx.mock
def test_get_user_access_token_refresh(token_service):
    # Mock OAuth response
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "user_token_456",
            "expires_in": 7200
        })
    )
    
    token = token_service.get_user_access_token(["https://api.ebay.com/oauth/api_scope/sell.inventory"])
    assert token.access_token == "user_token_456"
    assert token.token_type == "User"

def test_token_cache_reuse(token_service):
    # Manually set a token in cache
    future = datetime.now() + timedelta(hours=1)
    token_service.cache.set(TokenInfo(
        token_type="Application",
        access_token="cached_token",
        expires_at=future,
        scopes=["scope1"]
    ))
    
    token = token_service.get_app_access_token(["scope1"])
    assert token.access_token == "cached_token"

def test_token_cache_expiry(token_service):
    # Manually set an expired token
    past = datetime.now() - timedelta(minutes=10)
    token_service.cache.set(TokenInfo(
        token_type="Application",
        access_token="expired_token",
        expires_at=past,
        scopes=["scope1"]
    ))
    
    # This should trigger a mint (which we mock here manually)
    with respx.mock:
        respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
            return_value=httpx.Response(200, json={"access_token": "new_token", "expires_in": 3600})
        )
        token = token_service.get_app_access_token(["scope1"])
        assert token.access_token == "new_token"
