import pytest
from unittest.mock import MagicMock
from src.ebay.shipping_pipeline import ShippingPipeline
from src.ebay.browse_client import EbayBrowseClient
from src.ebay.models import EbayApiItemSummary, EbayApiItemDetail
from src.shipping.models import ShippingSourceLevel, ShippingResolutionStatus

def test_pipeline_flow_with_detail():
    # Mock Client
    mock_client = MagicMock(spec=EbayBrowseClient)
    
    # Mock Search Summary
    summary = EbayApiItemSummary(
        item_id="item123",
        title="Search Title",
        price={"value": "100.00", "currency": "USD"},
        shipping_options=[{"shippingCost": {"value": "20.00", "currency": "USD"}, "shippingCostType": "CALCULATED", "shippingServiceCode": "USPS"}]
    )
    
    # Mock Detail Data
    detail = EbayApiItemDetail(
        item_id="item123",
        title="Detail Title",
        price={"value": "100.00", "currency": "USD"},
        shipping_options=[{"shippingCost": {"value": "15.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "FedEx"}],
        taxes=[{"taxType": "VAT"}]
    )
    mock_client.get_item_with_context.return_value = detail
    
    pipeline = ShippingPipeline(mock_client)
    result = pipeline.resolve_item_shipping_via_api(
        item_id="item123",
        marketplace_id="EBAY_US",
        country="JP",
        search_item_summary=summary
    )
    
    # Verify result (Detail should be prioritized)
    assert result.shipping_estimated_total == 15.00
    assert result.shipping_source_level == ShippingSourceLevel.DETAIL
    assert result.shipping_resolution_status == ShippingResolutionStatus.RESOLVED_EXACT
    assert mock_client.get_item_with_context.called

def test_pipeline_flow_search_only_on_detail_fail():
    # Case: Detail fetch fails (returns None or raises)
    mock_client = MagicMock(spec=EbayBrowseClient)
    mock_client.get_item_with_context.return_value = None
    
    summary = EbayApiItemSummary(
        item_id="item123",
        title="Search Title",
        price={"value": "100.00", "currency": "USD"},
        shipping_options=[{"shippingCost": {"value": "20.00", "currency": "USD"}, "shippingCostType": "FIXED", "shippingServiceCode": "FedEx"}]
    )
    
    pipeline = ShippingPipeline(mock_client)
    result = pipeline.resolve_item_shipping_via_api(
        item_id="item123",
        marketplace_id="EBAY_US",
        country="JP",
        search_item_summary=summary
    )
    
    # Verify result (Should use Search info)
    assert result.shipping_estimated_total == 20.00
    assert result.shipping_source_level == ShippingSourceLevel.SEARCH
    assert result.shipping_resolution_status == ShippingResolutionStatus.RESOLVED_EXACT

def test_should_fetch_detail():
    mock_client = MagicMock(spec=EbayBrowseClient)
    pipeline = ShippingPipeline(mock_client)
    
    # Case 1: Search has CALCULATED -> Should fetch detail
    snap_calc = {"shippingOptions": [{"shippingCostType": "CALCULATED"}]}
    assert pipeline.should_fetch_detail(snap_calc) is True
    
    # Case 2: Search has FIXED -> Still returns True for accuracy/VAT context per current spec
    snap_fixed = {"shippingOptions": [{"shippingCostType": "FIXED", "shippingServiceCode": "FedEx"}]}
    assert pipeline.should_fetch_detail(snap_fixed) is True
