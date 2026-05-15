import pytest
from src.shipping.resolver import resolve_shipping_cost
from src.shipping.models import (
    ShippingResolutionStatus, 
    ShippingConfidence, 
    ShippingSourceLevel
)

def test_detail_priority_fixed():
    # Case: Both snapshots present, detail has FIXED
    # search is 12.0, detail is 9.0 -> detail wins
    search_snap = {
        "shippingOptions": [{"shippingCost": {"value": "12.00", "currency": "USD"}, "shippingCostType": "FIXED"}]
    }
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "9.00", "currency": "USD"}, "type": "FIXED"}],
        "taxes": [{"taxType": "VAT"}] # Add VAT context
    }
    
    result = resolve_shipping_cost(
        "item1", "EBAY_US", "JP", 
        search_snapshot=search_snap, 
        detail_snapshot=detail_snap
    )
    
    assert result.shipping_estimated_total == 9.00
    assert result.shipping_source_level == ShippingSourceLevel.DETAIL
    assert result.shipping_resolution_status == ShippingResolutionStatus.RESOLVED_EXACT
    assert result.shipping_confidence == ShippingConfidence.HIGH

def test_search_not_fallback():
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
    assert result.shipping_resolution_status == ShippingResolutionStatus.RESOLVED_EXACT # Not fallback
    assert result.shipping_confidence == ShippingConfidence.MEDIUM # Search always medium max

def test_calculated_shipping():
    # Case: Only CALCULATED shipping
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "30.00", "currency": "USD"}, "type": "CALCULATED"}],
        "taxes": [{"taxType": "VAT"}]
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
    
    assert result.shipping_estimated_total == 50.0
    assert result.shipping_resolution_status == ShippingResolutionStatus.FALLBACK_DEFAULT

def test_return_risk_seller_true():
    # Case: Seller pays for return shipping -> risk=True
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED"}],
        "returnTerms": {"returnShippingCostPayer": "SELLER"}
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.return_shipping_risk_flag is True

def test_return_risk_buyer_false():
    # Case: Buyer pays for return shipping -> risk=False
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED"}],
        "returnTerms": {"returnShippingCostPayer": "BUYER"}
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.return_shipping_risk_flag is False

def test_vat_unknown_confidence_drop():
    # Case: No taxes info in detail -> vat_included_flag=None, confidence drops
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED"}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.vat_included_flag is None
    assert result.shipping_confidence == ShippingConfidence.MEDIUM # Drops from HIGH because no VAT context

def test_import_charges_separation():
    # Case: Import charges present
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED"}],
        "estimatedImportCosts": {"amount": {"value": "5.50", "currency": "USD"}}
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_estimated_total == 10.0
    assert result.import_charges_included_flag is True
    assert result.import_charges_estimated_total == 5.5

def test_partial_vs_unresolved():
    # Case 1: Partial - has snapshot but no shipping options
    detail_snap = {"item_id": "item1"} # No shippingOptions key
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_resolution_status == ShippingResolutionStatus.UNRESOLVED
    
    # Case 2: Fallback
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap, fallback_shipping_value=10.0)
    assert result.shipping_resolution_status == ShippingResolutionStatus.FALLBACK_DEFAULT

def test_cheapest_option():
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "20.00", "currency": "USD"}, "type": "FIXED"},
            {"shippingCost": {"value": "12.00", "currency": "USD"}, "type": "FIXED"}
        ]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_estimated_total == 12.0
