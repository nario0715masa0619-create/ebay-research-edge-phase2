import pytest
from src.payout_cost.resolver import resolve_payout_fee
from src.payout_cost.models import (
    PayoutResolutionStatus,
    PayoutConfidence,
    PayoutSourceLevel
)

def test_resolve_override_rule():
    # Case 1: account specific rule があれば最優先適用
    override = {"fee_type": "rate", "rate_fee": 0.012, "rule_id": "vip_account"}
    result = resolve_payout_fee(1000.0, "USD", "JPY", payout_rule_override=override)
    assert result.payout_fee_estimated_total == 12.0
    assert result.payout_fee_source_level == PayoutSourceLevel.ACCOUNT_SPECIFIC_RULE
    assert result.payout_confidence == PayoutConfidence.HIGH
    assert result.fee_rule_applied == "vip_account"

def test_resolve_standard_fixed_fee():
    # Case 2: standard pricing master の fixed fee を適用
    master = [{"provider": "Payoneer", "payout_currency": "USD", "fee_type": "fixed", "fixed_fee": 1.5, "rule_id": "std_usd_fixed"}]
    result = resolve_payout_fee(100.0, "USD", "USD", payout_rule_master=master, same_currency_withdrawal_flag=True)
    assert result.payout_fee_estimated_total == 1.5
    assert result.payout_fee_source_level == PayoutSourceLevel.STANDARD_PRICING_MASTER
    assert result.fee_rule_applied == "std_usd_fixed"

def test_resolve_standard_rate_fee():
    # Case 3: standard pricing master の rate fee を適用
    master = [{"provider": "Payoneer", "payout_currency": "USD", "fee_type": "rate", "rate_fee": 0.02, "rule_id": "std_usd_rate"}]
    result = resolve_payout_fee(500.0, "USD", "JPY", payout_rule_master=master, conversion_required_flag=True)
    assert result.payout_fee_estimated_total == 10.0
    assert result.payout_resolution_status == PayoutResolutionStatus.RESOLVED_ESTIMATED

def test_volume_tier_switching():
    # Case 4: monthly threshold 超過で fee 体系が切り替わる
    master = [
        {"provider": "Payoneer", "monthly_volume_threshold": 10000, "rate_fee": 0.01, "rule_id": "tier2"},
        {"provider": "Payoneer", "monthly_volume_threshold": 0, "rate_fee": 0.02, "rule_id": "tier1"}
    ]
    # Under threshold
    res1 = resolve_payout_fee(1000.0, "USD", "JPY", monthly_cumulative_volume=5000, payout_rule_master=master)
    assert res1.fee_rule_applied == "tier1"
    assert res1.payout_fee_estimated_total == 20.0
    
    # Over threshold (tier2 should match first if ordered correctly or we iterate correctly)
    # Our resolver matches the first matching rule.
    res2 = resolve_payout_fee(1000.0, "USD", "JPY", monthly_cumulative_volume=15000, payout_rule_master=master)
    assert res2.fee_rule_applied == "tier2"
    assert res2.payout_fee_estimated_total == 10.0

def test_conversion_fee_fallback():
    # Case 5: conversion required のとき conversion fee が乗る (fallback)
    result = resolve_payout_fee(100.0, "USD", "JPY", conversion_required_flag=True)
    assert result.conversion_fee_estimated_total == 2.0
    assert result.payout_resolution_status == PayoutResolutionStatus.FALLBACK_DEFAULT

def test_same_currency_fallback():
    # Case 6: same currency local withdrawal
    result = resolve_payout_fee(100.0, "USD", "USD", same_currency_withdrawal_flag=True, same_country_withdrawal_flag=True)
    assert result.withdrawal_fee_estimated_total == 1.50
    assert "same currency local withdrawal" in result.payout_notes[0]

def test_fallback_generic():
    # Case 7: fallback rule が使われる (generic 1%)
    result = resolve_payout_fee(100.0, "USD", "EUR") # No flags set
    assert result.other_payout_fee_estimated_total == 1.0

def test_net_payout_calculation():
    # Case 9: net payout が正しく計算される
    override = {"fee_type": "rate", "rate_fee": 0.02, "category": "conversion"}
    result = resolve_payout_fee(1000.0, "USD", "JPY", payout_rule_override=override)
    assert result.payout_fee_estimated_total == 20.0
    assert result.net_payout_estimated_amount == 980.0
    assert result.net_payout_currency == "JPY"

def test_metadata_completeness():
    # Case 10: notes / source / status / confidence が正しく入る
    result = resolve_payout_fee(100.0, "USD", "JPY")
    assert result.payout_fee_source_level != PayoutSourceLevel.NONE
    assert len(result.payout_notes) > 0
    assert result.payout_resolution_status != PayoutResolutionStatus.UNRESOLVED

def test_min_max_constraints():
    # Extra: min/max fee
    master = [{"provider": "Payoneer", "fee_type": "rate", "rate_fee": 0.02, "min_fee": 5.0, "max_fee": 15.0}]
    # 100 * 0.02 = 2, min 5 -> 5
    res1 = resolve_payout_fee(100.0, "USD", "JPY", payout_rule_master=master)
    assert res1.payout_fee_estimated_total == 5.0
    # 1000 * 0.02 = 20, max 15 -> 15
    res2 = resolve_payout_fee(1000.0, "USD", "JPY", payout_rule_master=master)
    assert res2.payout_fee_estimated_total == 15.0
