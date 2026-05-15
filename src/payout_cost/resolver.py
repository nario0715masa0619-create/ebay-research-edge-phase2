from typing import Dict, Any, Optional, List
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
    same_currency_withdrawal_flag: bool = False,
    same_country_withdrawal_flag: bool = False,
    monthly_cumulative_volume: float = 0.0,
    conversion_required_flag: bool = False,
    payout_rule_override: Optional[Dict[str, Any]] = None,
    payout_rule_master: Optional[List[Dict[str, Any]]] = None,
) -> PayoutFeeResult:
    result = PayoutFeeResult(
        gross_payout_amount=gross_payout_amount,
        payout_fee_currency=payout_currency,
        net_payout_currency=target_bank_currency,
        payout_provider=payout_provider,
        source_platform=source_platform,
        conversion_required_flag=conversion_required_flag,
        same_currency_withdrawal_flag=same_currency_withdrawal_flag,
        same_country_withdrawal_flag=same_country_withdrawal_flag,
        payout_context_used={
            "account_country": account_country,
            "bank_country": bank_country,
            "monthly_cumulative_volume": monthly_cumulative_volume
        }
    )

    # 1. Override Rule (Priority 1)
    if payout_rule_override:
        _apply_rule(result, payout_rule_override, gross_payout_amount)
        result.payout_fee_source_level = PayoutSourceLevel.ACCOUNT_SPECIFIC_RULE
        result.payout_resolution_status = PayoutResolutionStatus.RESOLVED_EXACT
        result.payout_confidence = PayoutConfidence.HIGH
        result.add_note("account specific payout rule applied")
        _finalize_result(result)
        return result

    # 2. Standard Pricing Master (Priority 2)
    if payout_rule_master:
        for rule in payout_rule_master:
            if _rule_matches(rule, payout_provider, payout_currency, target_bank_currency, 
                             same_currency_withdrawal_flag, same_country_withdrawal_flag, 
                             monthly_cumulative_volume):
                _apply_rule(result, rule, gross_payout_amount)
                result.payout_fee_source_level = PayoutSourceLevel.STANDARD_PRICING_MASTER
                result.payout_resolution_status = PayoutResolutionStatus.RESOLVED_ESTIMATED
                result.payout_confidence = PayoutConfidence.MEDIUM
                result.add_note("standard pricing master applied")
                _finalize_result(result)
                return result

    # 3. Fallback Rule (Priority 3)
    # Simple defaults
    if same_currency_withdrawal_flag and same_country_withdrawal_flag:
        # e.g. USD to USD in US, or JPY to JPY in JP
        result.withdrawal_fee_estimated_total = 1.50 # Fixed fee example
        result.add_note("same currency local withdrawal fallback applied (fixed 1.50)")
    elif conversion_required_flag:
        # e.g. USD to JPY
        result.conversion_fee_estimated_total = gross_payout_amount * 0.02 # 2% example
        result.add_note("conversion fee fallback applied (2%)")
    else:
        # Generic 1%
        result.other_payout_fee_estimated_total = gross_payout_amount * 0.01
        result.add_note("fallback payout rule applied (generic 1%)")

    result.payout_fee_source_level = PayoutSourceLevel.FALLBACK_MASTER
    result.payout_resolution_status = PayoutResolutionStatus.FALLBACK_DEFAULT
    result.payout_confidence = PayoutConfidence.LOW
    _finalize_result(result)
    return result

def _rule_matches(rule, provider, p_curr, t_curr, s_curr_flag, s_count_flag, volume) -> bool:
    if rule.get("provider") != provider: return False
    if rule.get("payout_currency") and rule.get("payout_currency") != p_curr: return False
    if rule.get("target_bank_currency") and rule.get("target_bank_currency") != t_curr: return False
    
    # Check volume threshold if present
    threshold = rule.get("monthly_volume_threshold", 0)
    if volume < threshold: return False
    
    # Optional flags
    if "same_currency_withdrawal_flag" in rule and rule["same_currency_withdrawal_flag"] != s_curr_flag: return False
    if "same_country_withdrawal_flag" in rule and rule["same_country_withdrawal_flag"] != s_count_flag: return False
    
    return True

def _apply_rule(result: PayoutFeeResult, rule: Dict[str, Any], gross: float):
    fee_type = rule.get("fee_type", "rate")
    fee_val = 0.0
    
    if fee_type == "fixed":
        fee_val = rule.get("fixed_fee", 0.0)
    elif fee_type == "rate":
        fee_val = gross * rule.get("rate_fee", 0.0)
    
    # Min/Max constraints
    if "min_fee" in rule: fee_val = max(fee_val, rule["min_fee"])
    if "max_fee" in rule: fee_val = min(fee_val, rule["max_fee"])

    # Categorize
    cat = rule.get("category", "withdrawal")
    if cat == "receiving": result.receiving_fee_estimated_total = fee_val
    elif cat == "withdrawal": result.withdrawal_fee_estimated_total = fee_val
    elif cat == "conversion": result.conversion_fee_estimated_total = fee_val
    elif cat == "cross_border": result.cross_border_fee_estimated_total = fee_val
    else: result.other_payout_fee_estimated_total = fee_val

    result.fee_rule_applied = rule.get("rule_id")
    if rule.get("volume_tier"): result.volume_tier_applied = rule["volume_tier"]

def _finalize_result(result: PayoutFeeResult):
    result.payout_fee_estimated_total = (
        result.receiving_fee_estimated_total +
        result.withdrawal_fee_estimated_total +
        result.conversion_fee_estimated_total +
        result.cross_border_fee_estimated_total +
        result.other_payout_fee_estimated_total
    )
    result.net_payout_estimated_amount = result.gross_payout_amount - result.payout_fee_estimated_total
