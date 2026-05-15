import pytest
from src.shipping.resolver import resolve_shipping_cost
from src.shipping.models import (
    ShippingResolutionStatus, 
    ShippingConfidence, 
    ShippingSourceLevel
)

def test_detail_priority_fixed():
    # Case: Both snapshots present, detail has FIXED
    search_snap = {
        "shippingOptions": [{"shippingCost": {"value": "20.00", "currency": "USD"}, "shippingCostType": "FIXED"}]
    }
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "15.00", "currency": "USD"}, "type": "FIXED"}]
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        search_snapshot=search_snap, 
        detail_snapshot=detail_snap
    )
    
    assert result.shipping_estimated_total == 15.00
    assert result.shipping_source_level == ShippingSourceLevel.DETAIL
    assert result.shipping_resolution_status == ShippingResolutionStatus.RESOLVED_EXACT
    assert result.shipping_confidence == ShippingConfidence.HIGH

def test_search_fallback():
    # Case: Only search snapshot present
    search_snap = {
        "shippingOptions": [{"shippingCost": {"value": "25.00", "currency": "USD"}, "shippingCostType": "FIXED"}]
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        search_snapshot=search_snap
    )
    
    assert result.shipping_estimated_total == 25.00
    assert result.shipping_source_level == ShippingSourceLevel.SEARCH
    assert result.shipping_confidence == ShippingConfidence.MEDIUM # Confidence drops for search

def test_calculated_shipping():
    # Case: Only CALCULATED shipping
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "30.00", "currency": "USD"}, "type": "CALCULATED"}]
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        detail_snapshot=detail_snap
    )
    
    assert result.shipping_estimated_total == 30.00
    assert result.shipping_resolution_status == ShippingResolutionStatus.RESOLVED_ESTIMATED
    assert result.shipping_confidence == ShippingConfidence.MEDIUM

def test_local_pickup_exclusion():
    # Case: Only Local Pickup option
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "0.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "LocalPickup"}
        ]
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        detail_snapshot=detail_snap,
        fallback_shipping_value=50.0
    )
    
    assert result.shipping_estimated_total == 50.0 # Uses fallback
    assert result.shipping_resolution_status == ShippingResolutionStatus.FALLBACK_DEFAULT

def test_import_charges_and_returns():
    # Case: Detail snap with import charges and seller return risk
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED"}],
        "estimatedImportCosts": {"amount": {"value": "5.50", "currency": "USD"}},
        "returnTerms": {"returnShippingCostPayer": "BUYER"}
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        detail_snapshot=detail_snap
    )
    
    assert result.shipping_estimated_total == 10.0
    assert result.import_charges_included_flag is True
    assert result.import_charges_estimated_total == 5.5
    assert result.return_shipping_risk_flag is True # Buyer pays = risk for buyer

def test_unresolved():
    # Case: No snapshots, no fallback
    result = resolve_shipping_cost("item1", "EBAY_US", "JP")
    
    assert result.shipping_resolution_status == ShippingResolutionStatus.UNRESOLVED
    assert result.shipping_confidence == ShippingConfidence.NONE

def test_cheapest_option():
    # Case: Multiple fixed options
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "20.00", "currency": "USD"}, "type": "FIXED"},
            {"shippingCost": {"value": "12.00", "currency": "USD"}, "type": "FIXED"},
            {"shippingCost": {"value": "30.00", "currency": "USD"}, "type": "FIXED"}
        ]
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        detail_snapshot=detail_snap
    )
    
    assert result.shipping_estimated_total == 12.0
