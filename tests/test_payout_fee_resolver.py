import pytest
from src.payout_cost.resolver import resolve_payout_fee
from src.payout_cost.models import (
    PayoutResolutionStatus,
    PayoutConfidence,
    PayoutSourceLevel
)

def test_multiple_components_simultaneous():
    # 1. withdrawal + conversion が同時に加算される
    master = [
        {"category": "withdrawal", "fee_type": "fixed", "fixed_fee": 1.5, "rule_id": "std_withdrawal"},
        {"category": "conversion", "fee_type": "rate", "rate_fee": 0.02, "rule_id": "std_conversion"}
    ]
    result = resolve_payout_fee(100.0, "USD", "JPY", payout_rule_master=master, conversion_required_flag=True)
    # 1.5 (fixed) + 2.0 (2%) = 3.5
    assert result.payout_fee_estimated_total == 3.5
    assert "withdrawal" in result.partial_fee_components
    assert "conversion" in result.partial_fee_components
    assert len(result.applied_rule_ids) == 2

def test_withdrawal_plus_cross_border():
    # 2. withdrawal + cross_border が同時に加算される
    master = [
        {"category": "withdrawal", "fee_type": "rate", "rate_fee": 0.01, "rule_id": "w1"},
        {"category": "cross_border", "fee_type": "fixed", "fixed_fee": 5.0, "rule_id": "cb1"}
    ]
    result = resolve_payout_fee(1000.0, "USD", "EUR", payout_rule_master=master)
    # 10.0 (1%) + 5.0 = 15.0
    assert result.payout_fee_estimated_total == 15.0
    assert "cross_border" in result.partial_fee_components

def test_specificity_conflict_resolution():
    # 3. 同一 category の競合で specificity の高い rule が勝つ
    master = [
        {"category": "withdrawal", "fee_type": "rate", "rate_fee": 0.02, "rule_id": "generic_usd", "payout_currency": "USD"},
        {"category": "withdrawal", "fee_type": "rate", "rate_fee": 0.01, "rule_id": "specific_usd_jp", "payout_currency": "USD", "account_country": "JP"}
    ]
    result = resolve_payout_fee(1000.0, "USD", "USD", payout_rule_master=master, account_country="JP")
    # specific_usd_jp (1%) should win over generic_usd (2%)
    assert result.payout_fee_estimated_total == 10.0
    assert result.fee_rule_applied == "specific_usd_jp" # This reflects the last rule applied or we can check applied_rule_ids
    assert "specific_usd_jp" in result.applied_rule_ids
    assert "generic_usd" not in result.applied_rule_ids

def test_external_fallback_rule():
    # 4. fallback_rule 引数が適用される
    fallback = {
        "rule_id": "ext_fb_v1",
        "rules": [
            {"category": "withdrawal", "fee_type": "rate", "rate_fee": 0.005, "rule_id": "fb_w"},
            {"category": "conversion", "fee_type": "rate", "rate_fee": 0.03, "rule_id": "fb_c"}
        ]
    }
    result = resolve_payout_fee(1000.0, "USD", "JPY", fallback_rule=fallback, conversion_required_flag=True)
    # 5.0 (0.5%) + 30.0 (3%) = 35.0
    assert result.payout_fee_estimated_total == 35.0
    assert result.payout_source_level == PayoutSourceLevel.FALLBACK_MASTER
    assert "fb_w" in result.applied_rule_ids

def test_strict_mode_unresolved():
    # 5. strict モードで unresolved になる
    # No rules, conversion required
    result = resolve_payout_fee(100.0, "USD", "JPY", conversion_required_flag=True, strictness="strict")
    assert result.payout_resolution_status == PayoutResolutionStatus.UNRESOLVED
    assert result.unresolved_reason == "missing_conversion_rule_in_strict_mode"

def test_balanced_mode_partial():
    # 6. balanced モードで partial になる
    # Withdrawal is resolved by master, but conversion is resolved by internal fallback
    master = [{"category": "withdrawal", "fee_type": "fixed", "fixed_fee": 1.0, "rule_id": "w_m"}]
    result = resolve_payout_fee(100.0, "USD", "JPY", payout_rule_master=master, conversion_required_flag=True, strictness="balanced")
    # 1.0 (master) + 2.0 (internal fallback 2%) = 3.0
    assert result.payout_fee_estimated_total == 3.0
    assert result.payout_resolution_status == PayoutResolutionStatus.RESOLVED_PARTIAL
    assert "withdrawal" in result.partial_fee_components
    assert "conversion" in result.partial_fee_components

def test_internal_fallback_only_if_no_external():
    # 7. internal fallback は外部 fallback_rule 不在時のみ使う
    fallback = {"rules": [{"category": "withdrawal", "fee_type": "fixed", "fixed_fee": 10.0, "rule_id": "ext"}]}
    result = resolve_payout_fee(100.0, "USD", "USD", same_currency_withdrawal_flag=True, same_country_withdrawal_flag=True, fallback_rule=fallback)
    # Should use 10.0 (ext) instead of 1.50 (internal)
    assert result.payout_fee_estimated_total == 10.0
    assert "ext" in result.applied_rule_ids

def test_multiple_rule_ids_tracking():
    # 8. applied_rule_ids が複数保持される
    master = [
        {"category": "receiving", "fee_type": "fixed", "fixed_fee": 0.5, "rule_id": "r1"},
        {"category": "withdrawal", "fee_type": "fixed", "fixed_fee": 1.5, "rule_id": "w1"}
    ]
    result = resolve_payout_fee(100.0, "USD", "USD", payout_rule_master=master)
    assert "r1" in result.applied_rule_ids
    assert "w1" in result.applied_rule_ids
    assert result.applied_rule_count == 2

def test_unresolved_reason_on_no_rules():
    # 9. unresolved_reason が入る
    result = resolve_payout_fee(100.0, "USD", "JPY", strictness="strict")
    assert result.payout_resolution_status == PayoutResolutionStatus.UNRESOLVED
    assert result.unresolved_reason == "no_matching_rules"

def test_notes_status_confidence_consistency():
    # 10. notes / status / confidence が整合する
    override = [{"category": "withdrawal", "fee_type": "rate", "rate_fee": 0.01, "rule_id": "o1"}]
    result = resolve_payout_fee(1000.0, "USD", "USD", payout_rule_override=override)
    assert result.payout_resolution_status == PayoutResolutionStatus.RESOLVED_EXACT
    assert result.payout_confidence == PayoutConfidence.HIGH
    assert any("account specific" in n for n in result.payout_notes)
