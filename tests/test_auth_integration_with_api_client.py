import pytest
import respx
import httpx
from src.auth.config import AuthConfig
from src.auth.models import TokenInfo
from src.auth.bootstrap import bootstrap_auth_layer
from src.ebay.api_client import EbayInventoryApiClient

@pytest.fixture
def auth_components():
    config = AuthConfig(
        ebay_client_id="test_client_id",
        ebay_client_secret="test_client_secret",
        ebay_refresh_token="test_refresh_token",
        auth_enable_token_cache=True
    )
    return bootstrap_auth_layer(config)

@pytest.fixture
def api_client(auth_components):
    return EbayInventoryApiClient(auth_components)

def test_api_client_dry_run(api_client):
    res = api_client.publish_offer("OFFER-123", dry_run=True)
    assert res["dry_run"] is True
    assert res["operation"] == "inventory.publish_offer"

@respx.mock
def test_api_client_full_flow(api_client):
    # 1. Mock Token Mint
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "mock_access_token",
            "expires_in": 3600
        })
    )
    
    # 2. Mock Inventory API Call
    respx.post("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-123/publish").mock(
        return_value=httpx.Response(200, json={
            "listingId": "LISTING-123"
        })
    )
    
    res = api_client.publish_offer("OFFER-123")
    assert res["listingId"] == "LISTING-123"
    
    # Verify Authorization header was sent to Inventory API
    request = respx.calls.last.request
    assert request.headers["Authorization"] == "Bearer mock_access_token"

@respx.mock
def test_api_client_retry_on_401(api_client):
    # Set up token in cache
    from datetime import datetime, timedelta
    api_client.auth_service.cache.set(TokenInfo(
        token_type="User",
        access_token="old_token",
        expires_at=datetime.now() + timedelta(hours=1),
        scopes=["https://api.ebay.com/oauth/api_scope/sell.inventory"]
    ))
    
    # 1. First call to Inventory API fails with 401
    route_api = respx.post("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-123/publish").mock(
        side_effect=[
            httpx.Response(401, json={"errors": [{"message": "Invalid token"}]}),
            httpx.Response(200, json={"listingId": "SUCCESS-RETRY"})
        ]
    )
    
    # 2. Token Refresh mock
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "new_refreshed_token", "expires_in": 3600})
    )
    
    res = api_client.publish_offer("OFFER-123")
    
    assert res["listingId"] == "SUCCESS-RETRY"
    assert route_api.called
    assert route_api.call_count == 2
    
    # Second call should have new token
    assert route_api.calls[1].request.headers["Authorization"] == "Bearer new_refreshed_token"
