import pytest
from src.shipping.resolver import resolve_shipping_cost
from src.shipping.models import (
    ShippingResolutionStatus, 
    ShippingConfidence, 
    ShippingSourceLevel,
    CarrierNormalized,
    CarrierFilterStatus
)

def test_carrier_selection_fedex_over_dhl():
    # Case: DHL is cheaper (10.0), FedEx is more expensive (15.0)
    # Goal: FedEx should be selected
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "DHL Express"},
            {"shippingCost": {"value": "15.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "FedEx Priority"}
        ],
        "taxes": [{"taxType": "VAT"}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_estimated_total == 15.00
    assert result.carrier_normalized == CarrierNormalized.FEDEX
    assert result.carrier_allowed_flag is True
    assert result.carrier_filter_status == CarrierFilterStatus.ALLOWED_CARRIER_SELECTED
    assert any("Cheapest option was disallowed carrier" in note for note in result.notes)

def test_carrier_selection_postal_over_ups():
    # Case: UPS (12.0) vs USPS (18.0)
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "12.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "UPS Ground"},
            {"shippingCost": {"value": "18.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "USPS First Class"}
        ],
        "taxes": [{"taxType": "VAT"}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_estimated_total == 18.00
    assert result.carrier_normalized == CarrierNormalized.POSTAL

def test_search_unknown_to_detail_fedex():
    # Case: Search has unknown carrier, Detail resolves to FedEx
    search_snap = {
        "shippingOptions": [{"shippingCost": {"value": "20.00", "currency": "USD"}, "shippingCostType": "FIXED", "shippingServiceCode": ""}]
    }
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "20.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "FedEx"}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", search_snapshot=search_snap, detail_snapshot=detail_snap)
    assert result.carrier_normalized == CarrierNormalized.FEDEX
    assert result.shipping_source_level == ShippingSourceLevel.DETAIL

def test_both_unknown_unresolved():
    # Case: Carrier is unknown (empty string) in detail
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": ""}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_resolution_status == ShippingResolutionStatus.UNRESOLVED
    assert result.carrier_filter_status == CarrierFilterStatus.CARRIER_UNKNOWN_AFTER_DETAIL

def test_local_pickup_with_postal():
    # Case: Local Pickup (0.0) vs Postal (10.0)
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "0.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "Local Pickup"},
            {"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "Standard Post"}
        ]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_estimated_total == 10.0
    assert result.carrier_normalized == CarrierNormalized.POSTAL

def test_free_shipping_unknown_not_auto_selected():
    # Case: Free shipping but carrier is unknown
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "0.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": ""}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_resolution_status == ShippingResolutionStatus.UNRESOLVED

def test_no_allowed_with_fallback():
    # Case: Only UPS found, but fallback value provided
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "UPS"}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap, fallback_shipping_value=30.0)
    assert result.shipping_estimated_total == 30.0
    assert result.shipping_resolution_status == ShippingResolutionStatus.FALLBACK_DEFAULT
    assert result.carrier_filter_status == CarrierFilterStatus.FALLBACK_USED_DUE_TO_NO_ALLOWED_CARRIER

def test_no_allowed_no_fallback_unresolved():
    # Case: Only UPS found, no fallback
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "UPS"}]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_resolution_status == ShippingResolutionStatus.UNRESOLVED
    assert result.carrier_filter_status == CarrierFilterStatus.ONLY_DISALLOWED_CARRIERS_FOUND

def test_fixed_fedex_vs_calculated_postal():
    # Case: FIXED FedEx (20.0) vs CALCULATED Postal (15.0)
    # Goal: FIXED should be prioritized even if slightly more expensive
    detail_snap = {
        "shippingOptions": [
            {"shippingCost": {"value": "20.00", "currency": "USD"}, "type": "FIXED", "shippingServiceCode": "FedEx"},
            {"shippingCost": {"value": "15.00", "currency": "USD"}, "type": "CALCULATED", "shippingServiceCode": "USPS"}
        ]
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.shipping_estimated_total == 20.0
    assert result.carrier_normalized == CarrierNormalized.FEDEX
    assert result.shipping_cost_type == "FIXED"

def test_missing_service_name_in_detail():
    detail_snap = {
        "shippingOptions": [{"shippingCost": {"value": "10.00", "currency": "USD"}, "type": "FIXED"}] # No service name
    }
    result = resolve_shipping_cost("item1", "EBAY_US", "JP", detail_snapshot=detail_snap)
    assert result.carrier_normalized == CarrierNormalized.UNKNOWN
    assert result.shipping_resolution_status == ShippingResolutionStatus.UNRESOLVED
