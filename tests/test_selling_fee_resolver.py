import pytest
from src.selling_fee.resolver import resolve_selling_fee
from src.selling_fee.models import (
    SellingFeeResolutionStatus,
    SellingFeeConfidence,
    SellingFeeSourceLevel
)

def test_resolve_override_rule():
    # 1. override rule が最優先適用される
    override = [{"fee_component": "final_value_fee", "fee_type": "rate", "rate_fee": 0.10, "rule_id": "vip_fvf"}]
    result = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_override=override)
    assert result.final_value_fee_estimated_total == 10.0
    assert result.selling_fee_source_level == SellingFeeSourceLevel.ACCOUNT_SPECIFIC_RULE
    assert result.fee_rule_applied == "vip_fvf"

def test_marketplace_master_fvf():
    # 2. marketplace master の final value fee rate が適用される
    master = [{"marketplace_id": "EBAY_US", "fee_component": "final_value_fee", "fee_type": "rate", "rate_fee": 0.12, "rule_id": "m1"}]
    result = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_master=master)
    assert result.final_value_fee_estimated_total == 12.0
    assert result.selling_fee_resolution_status == SellingFeeResolutionStatus.RESOLVED_ESTIMATED

def test_fixed_per_order_fee():
    # 3. fixed per order fee が加算される
    master = [
        {"marketplace_id": "EBAY_US", "fee_component": "final_value_fee", "fee_type": "rate", "rate_fee": 0.12, "rule_id": "m1"},
        {"marketplace_id": "EBAY_US", "fee_component": "final_value_fee_fixed", "fee_type": "fixed", "fixed_fee": 0.35, "rule_id": "m2"}
    ]
    result = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_master=master)
    assert result.selling_fee_estimated_total == 12.35
    assert "final_value_fee_fixed" in result.partial_fee_components

def test_promoted_listing_fee():
    # 4. promoted listing fee が加算される
    master = [
        {"marketplace_id": "EBAY_US", "fee_component": "ad_fee", "fee_type": "rate", "rate_fee": 0.05, "rule_id": "ad1", "promoted_listing_flag": True}
    ]
    # flag False -> no ad fee
    res1 = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_master=master, promoted_listing_flag=False)
    assert res1.ad_fee_estimated_total == 0.0
    
    # flag True -> ad fee
    res2 = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_master=master, promoted_listing_flag=True)
    assert res2.ad_fee_estimated_total == 5.0
    assert "ad_fee" in res2.partial_fee_components

def test_international_selling_fee():
    # 5. international fee が加算される
    master = [
        {"marketplace_id": "EBAY_US", "fee_component": "international_fee", "fee_type": "rate", "rate_fee": 0.015, "rule_id": "i1", "international_sale_flag": True}
    ]
    result = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_master=master, international_sale_flag=True)
    assert result.international_fee_estimated_total == 1.5

def test_specificity_conflict_resolution():
    # 6. 同一 component 競合で specific rule が勝つ
    master = [
        {"marketplace_id": "EBAY_US", "fee_component": "final_value_fee", "rate_fee": 0.15, "rule_id": "generic"},
        {"marketplace_id": "EBAY_US", "category_id": "999", "fee_component": "final_value_fee", "rate_fee": 0.10, "rule_id": "specific"}
    ]
    result = resolve_selling_fee("EBAY_US", "999", 100.0, selling_fee_rule_master=master)
    assert result.final_value_fee_estimated_total == 10.0
    assert result.fee_rule_applied == "specific"

def test_fallback_rule_external():
    # 7. fallback rule が使われる
    fallback = {
        "rules": [
            {"fee_component": "final_value_fee", "fee_type": "rate", "rate_fee": 0.20, "rule_id": "fb_rate"}
        ]
    }
    # Master empty, should use external fallback
    result = resolve_selling_fee("EBAY_US", "123", 100.0, fallback_rule=fallback)
    assert result.final_value_fee_estimated_total == 20.0
    assert result.selling_fee_source_level == SellingFeeSourceLevel.FALLBACK_MASTER

def test_strict_mode_unresolved():
    # 8. strict モードで unresolved になる
    # No master rules, strict mode
    result = resolve_selling_fee("EBAY_US", "123", 100.0, strictness="strict")
    assert result.selling_fee_resolution_status == SellingFeeResolutionStatus.UNRESOLVED
    assert result.unresolved_reason == "missing_fvf_rule_in_strict_mode"

def test_total_selling_fee_calculation():
    # 9. total selling fee が複数 component 合算で正しい
    master = [
        {"fee_component": "final_value_fee", "rate_fee": 0.12, "fee_type": "rate"},
        {"fee_component": "final_value_fee_fixed", "fixed_fee": 0.30, "fee_type": "fixed"},
        {"fee_component": "insertion_fee", "fixed_fee": 0.25, "fee_type": "fixed"}
    ]
    result = resolve_selling_fee("EBAY_US", "123", 100.0, selling_fee_rule_master=master)
    # 12.0 + 0.30 + 0.25 = 12.55
    assert result.selling_fee_estimated_total == 12.55

def test_metadata_consistency():
    # 10. notes / source / status / confidence が正しく入る
    result = resolve_selling_fee("EBAY_US", "123", 100.0) # Uses internal fallbacks
    assert result.selling_fee_resolution_status == SellingFeeResolutionStatus.FALLBACK_DEFAULT
    assert result.selling_fee_confidence == SellingFeeConfidence.LOW
    assert len(result.selling_fee_notes) > 0
    assert result.selling_fee_source_level == SellingFeeSourceLevel.FALLBACK_MASTER
