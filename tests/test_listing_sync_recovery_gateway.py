import pytest
import respx
import httpx
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
from src.listing_sync.gateway import ListingSyncRecoveryGateway, ListingSyncRequest
from src.auth.bootstrap import bootstrap_auth_layer
from src.ebay.models import ProductCandidate, EbayListing, CandidateEvidence, MonitoringEvent

@pytest.fixture
def auth_layer():
    return bootstrap_auth_layer()

@pytest.fixture
def repos():
    return {
        "candidate": MagicMock(),
        "evidence": MagicMock(),
        "job": MagicMock(),
        "listing": MagicMock(),
        "event": MagicMock()
    }

def setup_mocks(repos, candidate, listing=None):
    repos["candidate"].get_by_candidate_id.return_value = candidate
    repos["listing"].get_by_candidate_id.return_value = listing
    repos["job"].start_run.return_value = MagicMock(run_id="JOB-1")

@respx.mock
def test_sync_no_drift(auth_layer, repos):
    # Mock OAuth
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token", "expires_in": 3600
    }))
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        event_repo=repos["event"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", sku="SKU-1", status="listed", decision_type="listing_ready",
        source_item_id="S-1", source_platform="mercari", source_url="http://ex.com", source_title="T", source_price_jpy=1000
    )
    listing = EbayListing(
        candidate_id="C-1", sku="SKU-1", marketplace_id="EBAY_US",
        offer_id="OFFER-1", listing_id="LIST-1", listing_price_usd=100.0, quantity=5,
        offer_status="PUBLISHED", listing_status="ACTIVE"
    )
    setup_mocks(repos, candidate, listing)
    
    # Mock eBay
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(200, json={
        "offerId": "OFFER-1", "listingId": "LIST-1", "status": "PUBLISHED", "listingStatus": "ACTIVE",
        "pricingSummary": {"price": {"value": "100.0", "currency": "USD"}}
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(200, json={
        "sku": "SKU-1", "availableQuantity": 5
    }))
    
    res = gateway.sync_and_recover_listing(ListingSyncRequest(candidate_id="C-1", sku="SKU-1"))
    assert res.success_flag is True
    assert res.sync_status == "synced"
    assert not res.detected_drift_types

@respx.mock
def test_sync_repair_listing_id(auth_layer, repos):
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token", "expires_in": 3600
    }))
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        event_repo=repos["event"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", sku="SKU-1", status="listed", decision_type="listing_ready",
        source_item_id="S-1", source_platform="mercari", source_url="http://ex.com", source_title="T", source_price_jpy=1000
    )
    listing = EbayListing(
        candidate_id="C-1", sku="SKU-1", marketplace_id="EBAY_US",
        offer_id="OFFER-1", listing_id=None, listing_price_usd=100.0, quantity=5
    )
    setup_mocks(repos, candidate, listing)
    
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(200, json={
        "offerId": "OFFER-1", "listingId": "REAL-LIST-1", "status": "PUBLISHED", "listingStatus": "ACTIVE",
        "pricingSummary": {"price": {"value": "100.0", "currency": "USD"}}
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(200, json={
        "sku": "SKU-1", "availableQuantity": 5
    }))
    
    res = gateway.sync_and_recover_listing(ListingSyncRequest(candidate_id="C-1", sku="SKU-1"))
    assert res.sync_status == "repaired"
    assert "missing_listing_id_in_db" in res.detected_drift_types
    repos["listing"].upsert.assert_called()
    assert repos["listing"].upsert.call_args[0][0].listing_id == "REAL-LIST-1"

@respx.mock
def test_sync_reconcile_price(auth_layer, repos):
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token", "expires_in": 3600
    }))
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        event_repo=repos["event"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", sku="SKU-1", status="listed", decision_type="listing_ready",
        source_item_id="S-1", source_platform="mercari", source_url="http://ex.com", source_title="T", source_price_jpy=1000
    )
    listing = EbayListing(
        candidate_id="C-1", sku="SKU-1", marketplace_id="EBAY_US",
        offer_id="OFFER-1", listing_id="LIST-1", listing_price_usd=100.0, quantity=5,
        offer_status="PUBLISHED", listing_status="ACTIVE"
    )
    setup_mocks(repos, candidate, listing)
    
    # Remote has price 120.0
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(200, json={
        "offerId": "OFFER-1", "listingId": "LIST-1", "status": "PUBLISHED", "listingStatus": "ACTIVE",
        "pricingSummary": {"price": {"value": "120.0", "currency": "USD"}}
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(200, json={
        "sku": "SKU-1", "availableQuantity": 5
    }))
    
    # Mock Bulk Update
    respx.post("https://api.sandbox.ebay.com/sell/inventory/v1/bulk_update_price_quantity").mock(return_value=httpx.Response(200, json={
        "responses": [{"statusCode": 200}]
    }))
    
    req = ListingSyncRequest(candidate_id="C-1", sku="SKU-1", allow_recover_inventory=True)
    res = gateway.sync_and_recover_listing(req)
    
    assert res.sync_status == "repaired"
    assert "price_drift" in res.detected_drift_types
    # Verify bulk update was called
    assert any("bulk_update_price_quantity" in str(call.request.url) for call in respx.calls)

@respx.mock
def test_sync_review_required_offer_not_found(auth_layer, repos):
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token", "expires_in": 3600
    }))
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        event_repo=repos["event"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", sku="SKU-1", status="listed", decision_type="listing_ready",
        source_item_id="S-1", source_platform="mercari", source_url="http://ex.com", source_title="T", source_price_jpy=1000
    )
    listing = EbayListing(
        candidate_id="C-1", sku="SKU-1", marketplace_id="EBAY_US",
        offer_id="OFFER-1", listing_id="LIST-1", listing_price_usd=100.0, quantity=5
    )
    setup_mocks(repos, candidate, listing)
    
    # Mock 404 for offer
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(404, json={
        "errors": [{"message": "Offer not found"}]
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(404))
    
    res = gateway.sync_and_recover_listing(ListingSyncRequest(candidate_id="C-1", sku="SKU-1"))
    
    assert res.review_required_flag is True
    assert "offer_missing_remote" in res.detected_drift_types
    repos["candidate"].upsert.assert_called()
    assert repos["candidate"].upsert.call_args[0][0].status == "review_required"

@respx.mock
def test_sync_dry_run_no_updates(auth_layer, repos):
    respx.post("https://api.sandbox.ebay.com/identity/v1/oauth2/token").mock(return_value=httpx.Response(200, json={
        "access_token": "mock_token", "expires_in": 3600
    }))
    auth_layer["config"].ebay_refresh_token = "mock_refresh_token"
    
    gateway = ListingSyncRecoveryGateway(
        repos["candidate"], repos["evidence"], repos["job"], repos["listing"],
        event_repo=repos["event"],
        api_client=auth_layer["api_client"]
    )
    
    candidate = ProductCandidate(
        candidate_id="C-1", sku="SKU-1", status="listed", decision_type="listing_ready",
        source_item_id="S-1", source_platform="mercari", source_url="http://ex.com", source_title="T", source_price_jpy=1000
    )
    listing = EbayListing(
        candidate_id="C-1", sku="SKU-1", marketplace_id="EBAY_US",
        offer_id="OFFER-1", listing_id=None, listing_price_usd=100.0, quantity=5
    )
    setup_mocks(repos, candidate, listing)
    
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer/OFFER-1").mock(return_value=httpx.Response(200, json={
        "offerId": "OFFER-1", "listingId": "REAL-LIST-1", "status": "PUBLISHED", "listingStatus": "ACTIVE",
        "pricingSummary": {"price": {"value": "100.0", "currency": "USD"}}
    }))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/offer?sku=SKU-1").mock(return_value=httpx.Response(200, json={"offers": []}))
    respx.get("https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/SKU-1").mock(return_value=httpx.Response(200, json={
        "sku": "SKU-1", "availableQuantity": 5
    }))
    
    res = gateway.sync_and_recover_listing(ListingSyncRequest(candidate_id="C-1", sku="SKU-1", dry_run=True))
    
    assert res.sync_status == "drift_detected" # Logic says drift detected in dry run
    repos["listing"].upsert.assert_not_called()
