import pytest
import respx
import httpx
from datetime import datetime
from unittest.mock import MagicMock
from src.listing_sync.gateway import ListingSyncRecoveryGateway, ListingSyncRequest
from src.auth.bootstrap import bootstrap_auth_layer
from src.ebay.models import ProductCandidate, EbayListing

@pytest.fixture
def auth_layer():
    return bootstrap_auth_layer()

@pytest.fixture
def repos():
    return {
        "candidate": MagicMock(),
        "evidence": MagicMock(),
        "job": MagicMock(),
        "listing": MagicMock()
    }

@respx.mock
def test_listing_sync_success_no_drift(auth_layer, repos):
    # Mock OAuth
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token",
        "expires_in": 3600
    }))
    
    # Inject dummy refresh token
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", 
        source_item_id="S-1", 
        source_platform="mercari", 
        sku="SKU-1",
        source_url="http://example.com",
        source_title="Title",
        source_price_jpy=1000.0,
        decision_type="listing_ready",
        status="listed"
    )
    listing = EbayListing(
        candidate_id="C-1", 
        sku="SKU-1", 
        marketplace_id="EBAY_US",
        offer_id="OFFER-1", 
        listing_id="LIST-1", 
        listing_price_usd=100.0, 
        quantity=5
    )
    
    repos["candidate"].get_by_candidate_id.return_value = candidate
    repos["listing"].get_by_candidate_id.return_value = listing
    
    # Mock eBay API
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(200, json={
        "offerId": "OFFER-1",
        "listingId": "LIST-1",
        "status": "PUBLISHED",
        "pricingSummary": {"price": {"value": "100.0", "currency": "USD"}},
        "listingStatus": "ACTIVE"
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(200, json={
        "sku": "SKU-1",
        "availableQuantity": 5
    }))
    
    req = ListingSyncRequest(candidate_id="C-1", sku="SKU-1")
    res = gateway.sync_and_recover_listing(req)
    
    assert res.success_flag is True
    assert res.sync_status == "synced"
    assert not res.detected_drift_types

@respx.mock
def test_listing_sync_repair_missing_listing_id(auth_layer, repos):
    # Mock OAuth
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token",
        "expires_in": 3600
    }))
    
    # Inject dummy refresh token
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", 
        source_item_id="S-1", 
        source_platform="mercari", 
        sku="SKU-1",
        source_url="http://example.com",
        source_title="Title",
        source_price_jpy=1000.0,
        decision_type="listing_ready",
        status="listed"
    )
    listing = EbayListing(
        candidate_id="C-1", 
        sku="SKU-1", 
        marketplace_id="EBAY_US",
        offer_id="OFFER-1", 
        listing_id=None, 
        listing_price_usd=100.0, 
        quantity=5
    )
    
    repos["candidate"].get_by_candidate_id.return_value = candidate
    repos["listing"].get_by_candidate_id.return_value = listing
    
    # Mock eBay API
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(200, json={
        "offerId": "OFFER-1",
        "listingId": "REAL-LIST-1",
        "status": "PUBLISHED",
        "pricingSummary": {"price": {"value": "100.0", "currency": "USD"}},
        "listingStatus": "ACTIVE"
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(200, json={
        "sku": "SKU-1",
        "availableQuantity": 5
    }))
    
    req = ListingSyncRequest(candidate_id="C-1", sku="SKU-1")
    res = gateway.sync_and_recover_listing(req)
    
    assert res.sync_status == "repaired"
    assert "missing_listing_id_in_db" in res.detected_drift_types
    assert res.recovery_applied_flag is True
    
    # Verify DB update
    repos["listing"].upsert.assert_called()
    updated_listing = repos["listing"].upsert.call_args[0][0]
    assert updated_listing.listing_id == "REAL-LIST-1"
