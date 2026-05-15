import pytest
from unittest.mock import MagicMock
from src.ebay.shipping_pipeline import ShippingPipeline
from src.ebay.browse_client import EbayBrowseClient
from src.ebay.models import EbayApiItemSummary, EbayApiItemDetail
from src.shipping.models import ShippingSourceLevel, ShippingResolutionStatus, CarrierNormalized

def setup_pipeline():
    mock_client = MagicMock(spec=EbayBrowseClient)
    pipeline = ShippingPipeline(mock_client)
    return pipeline, mock_client

def test_balanced_no_detail_fetch_fedex_fixed():
    # Case 1: balanced mode, FedEx FIXED in search -> Should NOT fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode":"FedEx"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    
    assert result.detail_fetch_attempted is False
    assert result.shipping_source_level == ShippingSourceLevel.SEARCH
    assert mock_client.get_item_with_context.called is False
    assert result.detail_fetch_reason == []

def test_balanced_no_detail_fetch_usps_fixed():
    # Case 2: balanced mode, USPS FIXED in search -> Should NOT fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode":"USPS"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    
    assert result.detail_fetch_attempted is False
    assert mock_client.get_item_with_context.called is False

def test_fetch_detail_if_no_allowed_carrier():
    # Case 3: search has no allowed carrier -> Should fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode":"DHL"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    assert "no_allowed_carrier" in result.detail_fetch_reason
    assert mock_client.get_item_with_context.called is True

def test_fetch_detail_if_unknown_carrier():
    # Case 4: search has UNKNOWN carrier -> Should fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode": ""}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    assert "unknown_carrier" in result.detail_fetch_reason
    assert mock_client.get_item_with_context.called is True

def test_fetch_detail_if_calculated_only():
    # Case 5: search has only CALCULATED -> Should fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"CALCULATED", "shippingServiceCode": "FedEx"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    assert "calculated_shipping_only" in result.detail_fetch_reason
    assert mock_client.get_item_with_context.called is True

def test_continue_with_search_on_detail_fail():
    # Case 6: detail fetch fails but search exists -> continue with search
    pipeline, mock_client = setup_pipeline()
    mock_client.get_item_with_context.side_effect = Exception("API Down")
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"CALCULATED", "shippingServiceCode": "FedEx"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    assert result.detail_fetch_attempted is True
    assert result.detail_fetch_succeeded is False
    assert result.shipping_source_level == ShippingSourceLevel.SEARCH

def test_search_only_mode():
    # Case 7: search_only mode -> NEVER fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"CALCULATED", "shippingServiceCode": "FedEx"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="search_only")
    assert result.detail_fetch_attempted is False
    assert mock_client.get_item_with_context.called is False

def test_always_detail_mode():
    # Case 8: always_detail mode -> ALWAYS fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode": "FedEx"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="always_detail")
    assert mock_client.get_item_with_context.called is True
    assert "always_detail_mode" in result.detail_fetch_reason

def test_fetch_detail_on_local_pickup_only():
    # Case 9: Local Pickup only -> Should fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"0","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode": "Local Pickup"}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    assert mock_client.get_item_with_context.called is True
    assert "local_pickup_only" in result.detail_fetch_reason

def test_fetch_detail_on_free_shipping_unknown_carrier():
    # Case 10: free shipping + UNKNOWN carrier -> Should fetch detail
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"0","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode": ""}]
    )
    result, _ = pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    assert mock_client.get_item_with_context.called is True
    assert "free_shipping_unknown_carrier" in result.detail_fetch_reason

def test_detail_not_called_on_optimized_case():
    # Case 11: detail not called on optimized case
    pipeline, mock_client = setup_pipeline()
    summary = EbayApiItemSummary(
        item_id="item1", title="T1", price={"value":"10","currency":"USD"},
        shipping_options=[{"shippingCost":{"value":"5","currency":"USD"}, "shippingCostType":"FIXED", "shippingServiceCode": "FedEx"}]
    )
    pipeline.resolve_item_shipping_via_api("item1", "EBAY_US", "JP", search_item_summary=summary, mode="balanced")
    mock_client.get_item_with_context.assert_not_called()
