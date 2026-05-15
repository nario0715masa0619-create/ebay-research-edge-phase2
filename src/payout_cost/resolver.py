from typing import Dict, Any, Optional, List, Tuple
from .models import (
    PayoutFeeResult,
    PayoutResolutionStatus,
    PayoutConfidence,
    PayoutSourceLevel
)

def resolve_payout_fee(
    gross_payout_amount: float,
    payout_currency: str,
    target_bank_currency: str,
    payout_provider: str = "Payoneer",
    source_platform: str = "eBay",
    account_country: str = "JP",
    bank_country: str = "JP",
    same_currency_withdrawal_flag: Optional[bool] = None,
    same_country_withdrawal_flag: Optional[bool] = None,
    monthly_cumulative_volume: float = 0.0,
    conversion_required_flag: Optional[bool] = None,
    payout_rule_override: Optional[List[Dict[str, Any]]] = None,
    payout_rule_master: Optional[List[Dict[str, Any]]] = None,
    fallback_rule: Optional[Dict[str, Any]] = None,
    strictness: str = "balanced",
    payout_method: str = "Bank Withdrawal"
) -> PayoutFeeResult:
    result = PayoutFeeResult(
        gross_payout_amount=gross_payout_amount,
        payout_fee_currency=payout_currency,
        net_payout_currency=target_bank_currency,
        payout_provider=payout_provider,
        source_platform=source_platform,
        payout_method=payout_method,
        conversion_required_flag=conversion_required_flag if conversion_required_flag is not None else False,
        same_currency_withdrawal_flag=same_currency_withdrawal_flag if same_currency_withdrawal_flag is not None else False,
        same_country_withdrawal_flag=same_country_withdrawal_flag if same_country_withdrawal_flag is not None else False,
        strictness=strictness,
        payout_context_used={
            "account_country": account_country,
            "bank_country": bank_country,
            "monthly_cumulative_volume": monthly_cumulative_volume
        }
    )

    # Pre-validation for UNRESOLVED
    if gross_payout_amount <= 0:
        result.unresolved_reason = "payout_amount_invalid"
        result.add_note("payout fee unresolved: amount is zero or negative")
        return result
    
    if not payout_currency or not target_bank_currency:
        result.unresolved_reason = "currency_missing"
        result.add_note("payout fee unresolved: currency missing")
        return result

    # Rule Collection Phase
    all_matched_rules = []

    # Helper for matching
    context = {
        "provider": payout_provider,
        "payout_currency": payout_currency,
        "target_bank_currency": target_bank_currency,
        "account_country": account_country,
        "bank_country": bank_country,
        "same_currency_flag": same_currency_withdrawal_flag,
        "same_country_flag": same_country_withdrawal_flag,
        "volume": monthly_cumulative_volume,
        "conv_req_flag": conversion_required_flag
    }

    # 1. Collect Override Rules
    if payout_rule_override:
        for rule in payout_rule_override:
            if _rule_matches(rule, context):
                rule["_source"] = PayoutSourceLevel.ACCOUNT_SPECIFIC_RULE
                all_matched_rules.append(rule)

    # 2. Collect Master Rules
    if payout_rule_master:
        for rule in payout_rule_master:
            if _rule_matches(rule, context):
                rule["_source"] = PayoutSourceLevel.STANDARD_PRICING_MASTER
                all_matched_rules.append(rule)

    # 3. Collect External Fallback Rules
    if fallback_rule:
        rules_list = fallback_rule.get("rules", [])
        for rule in rules_list:
            if _rule_matches(rule, context):
                rule["_source"] = PayoutSourceLevel.FALLBACK_MASTER
                all_matched_rules.append(rule)

    # Category-based Selection
    selected_rules_by_category = {}
    for rule in all_matched_rules:
        cat = rule.get("category", "other")
        existing = selected_rules_by_category.get(cat)
        if not existing or _is_more_specific(rule, existing):
            selected_rules_by_category[cat] = rule

    # Application Phase
    if selected_rules_by_category:
        for cat, rule in selected_rules_by_category.items():
            _apply_rule(result, rule, gross_payout_amount)
        
        # Determine Status and Confidence
        sources = [r["_source"] for r in selected_rules_by_category.values()]
        if PayoutSourceLevel.ACCOUNT_SPECIFIC_RULE in sources:
            result.payout_source_level = PayoutSourceLevel.ACCOUNT_SPECIFIC_RULE
            result.payout_resolution_status = PayoutResolutionStatus.RESOLVED_EXACT
            result.payout_confidence = PayoutConfidence.HIGH
            result.add_note("account specific payout rule applied")
        elif PayoutSourceLevel.STANDARD_PRICING_MASTER in sources:
            result.payout_source_level = PayoutSourceLevel.STANDARD_PRICING_MASTER
            result.payout_resolution_status = PayoutResolutionStatus.RESOLVED_ESTIMATED
            result.payout_confidence = PayoutConfidence.MEDIUM
            result.add_note("standard pricing master applied")
        else:
            result.payout_source_level = PayoutSourceLevel.FALLBACK_MASTER
            result.payout_resolution_status = PayoutResolutionStatus.FALLBACK_DEFAULT
            result.payout_confidence = PayoutConfidence.LOW
            result.add_note("fallback payout rule applied")

        if len(selected_rules_by_category) > 1:
            result.add_note("multiple payout fee rules applied")
    
    # Internal Fallback Phase (if missing components)
    has_master_unresolved_components = False
    if result.conversion_required_flag and "conversion" not in selected_rules_by_category:
        has_master_unresolved_components = True
    
    if strictness != "strict":
        _apply_internal_fallbacks(result)

    # Validation Phase for strictness
    if strictness == "strict":
        if result.conversion_required_flag and "conversion" not in selected_rules_by_category:
            result.payout_resolution_status = PayoutResolutionStatus.UNRESOLVED
            result.unresolved_reason = "missing_conversion_rule_in_strict_mode"
            result.add_note("payout fee unresolved: conversion required but no rule found in strict mode")

    _finalize_result(result)
    
    # Adjust status for PARTIAL if master was combined with internal fallback
    if result.payout_resolution_status in [PayoutResolutionStatus.RESOLVED_ESTIMATED, PayoutResolutionStatus.RESOLVED_EXACT]:
        if has_master_unresolved_components and strictness == "balanced":
             result.payout_resolution_status = PayoutResolutionStatus.RESOLVED_PARTIAL
             result.add_note("payout fee partially resolved")

    if result.payout_resolution_status == PayoutResolutionStatus.UNRESOLVED and not result.unresolved_reason:
        result.unresolved_reason = "no_matching_rules"
        result.add_note("payout fee unresolved")

    return result

def _rule_matches(rule, ctx) -> bool:
    if rule.get("provider") and rule.get("provider") != ctx["provider"]: return False
    if rule.get("payout_currency") and rule.get("payout_currency") != ctx["payout_currency"]: return False
    if rule.get("target_bank_currency") and rule.get("target_bank_currency") != ctx["target_bank_currency"]: return False
    if rule.get("account_country") and rule.get("account_country") != ctx["account_country"]: return False
    if rule.get("bank_country") and rule.get("bank_country") != ctx["bank_country"]: return False
    
    # Check volume range
    v_min = rule.get("monthly_volume_min", 0)
    v_max = rule.get("monthly_volume_max", float('inf'))
    if not (v_min <= ctx["volume"] <= v_max): return False
    
    # Optional flags
    if "same_currency_withdrawal_flag" in rule and ctx["same_currency_flag"] is not None:
        if rule["same_currency_withdrawal_flag"] != ctx["same_currency_flag"]: return False
    
    if "same_country_withdrawal_flag" in rule and ctx["same_country_flag"] is not None:
        if rule["same_country_withdrawal_flag"] != ctx["same_country_flag"]: return False

    if "conversion_required_flag" in rule and ctx["conv_req_flag"] is not None:
        if rule["conversion_required_flag"] != ctx["conv_req_flag"]: return False
    
    if rule.get("enabled") is False: return False
    
    return True

def _is_more_specific(new_rule: Dict[str, Any], existing_rule: Dict[str, Any]) -> bool:
    source_priority = {
        PayoutSourceLevel.ACCOUNT_SPECIFIC_RULE: 3,
        PayoutSourceLevel.STANDARD_PRICING_MASTER: 2,
        PayoutSourceLevel.FALLBACK_MASTER: 1
    }
    new_p = source_priority.get(new_rule.get("_source", PayoutSourceLevel.NONE), 0)
    old_p = source_priority.get(existing_rule.get("_source", PayoutSourceLevel.NONE), 0)
    
    if new_p > old_p: return True
    if new_p < old_p: return False
    
    condition_fields = [
        "payout_currency", "target_bank_currency", "account_country", "bank_country",
        "monthly_volume_min", "monthly_volume_max", "same_currency_withdrawal_flag", 
        "same_country_withdrawal_flag", "conversion_required_flag"
    ]
    new_count = sum(1 for f in condition_fields if f in new_rule and new_rule[f] is not None)
    old_count = sum(1 for f in condition_fields if f in existing_rule and existing_rule[f] is not None)
    
    return new_count > old_count

def _apply_rule(result: PayoutFeeResult, rule: Dict[str, Any], gross: float):
    fee_type = rule.get("fee_type", "rate")
    fee_val = 0.0
    
    if fee_type == "fixed":
        fee_val = rule.get("fixed_fee", 0.0)
    elif fee_type == "rate":
        fee_val = gross * rule.get("rate_fee", 0.0)
    
    if "min_fee" in rule: fee_val = max(fee_val, rule["min_fee"])
    if "max_fee" in rule: fee_val = min(fee_val, rule["max_fee"])

    cat = rule.get("category", "other")
    if cat == "receiving": 
        result.receiving_fee_estimated_total = fee_val
    elif cat == "withdrawal": 
        result.withdrawal_fee_estimated_total = fee_val
        result.add_note("withdrawal rule applied")
    elif cat == "conversion": 
        result.conversion_fee_estimated_total = fee_val
        result.add_note("conversion rule applied")
    elif cat == "cross_border": 
        result.cross_border_fee_estimated_total = fee_val
        result.add_note("cross-border rule applied")
    else: 
        result.other_payout_fee_estimated_total = fee_val

    if rule.get("rule_id"):
        result.applied_rule_ids.append(rule["rule_id"])
        result.applied_rule_count += 1
        result.fee_rule_applied = rule["rule_id"]
    
    result.partial_fee_components.append(cat)

def _apply_internal_fallbacks(result: PayoutFeeResult):
    if "withdrawal" not in result.partial_fee_components:
        if result.same_currency_withdrawal_flag and result.same_country_withdrawal_flag:
            result.withdrawal_fee_estimated_total = 1.50
            result.add_note("internal fallback: same currency local withdrawal (fixed 1.50)")
            result.partial_fee_components.append("withdrawal")
    
    if "conversion" not in result.partial_fee_components:
        if result.conversion_required_flag:
            result.conversion_fee_estimated_total = result.gross_payout_amount * 0.02
            result.add_note("internal fallback: conversion fee (2%)")
            result.partial_fee_components.append("conversion")
            
    if not result.partial_fee_components and result.payout_resolution_status == PayoutResolutionStatus.UNRESOLVED:
        result.other_payout_fee_estimated_total = result.gross_payout_amount * 0.01
        result.add_note("internal fallback: generic payout fee (1%)")
        result.partial_fee_components.append("other")
        result.payout_source_level = PayoutSourceLevel.FALLBACK_MASTER
        result.payout_resolution_status = PayoutResolutionStatus.FALLBACK_DEFAULT
        result.payout_confidence = PayoutConfidence.LOW

def _finalize_result(result: PayoutFeeResult):
    result.payout_fee_estimated_total = (
        result.receiving_fee_estimated_total +
        result.withdrawal_fee_estimated_total +
        result.conversion_fee_estimated_total +
        result.cross_border_fee_estimated_total +
        result.other_payout_fee_estimated_total
    )
    result.net_payout_estimated_amount = result.gross_payout_amount - result.payout_fee_estimated_total
    
    if result.payout_resolution_status == PayoutResolutionStatus.UNRESOLVED and result.partial_fee_components:
         if not result.applied_rule_ids:
             result.payout_resolution_status = PayoutResolutionStatus.FALLBACK_DEFAULT
             result.payout_confidence = PayoutConfidence.LOW
         else:
             result.payout_resolution_status = PayoutResolutionStatus.RESOLVED_PARTIAL
             result.payout_confidence = PayoutConfidence.LOW
