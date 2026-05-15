from typing import Dict, Any, Optional, List
from .models import (
    SellingFeeResult,
    SellingFeeResolutionStatus,
    SellingFeeConfidence,
    SellingFeeSourceLevel
)

def resolve_selling_fee(
    marketplace_id: str,
    category_id: str,
    item_price: float,
    charged_shipping: float = 0.0,
    collected_tax: float = 0.0,
    quantity: int = 1,
    currency: str = "USD",
    promoted_listing_flag: bool = False,
    ad_rate: float = 0.0,
    international_sale_flag: bool = False,
    seller_store_plan: str = "basic",
    seller_performance_level: str = "top_rated",
    selling_fee_rule_override: Optional[List[Dict[str, Any]]] = None,
    selling_fee_rule_master: Optional[List[Dict[str, Any]]] = None,
    fallback_rule: Optional[Dict[str, Any]] = None,
    strictness: str = "balanced"
) -> SellingFeeResult:
    # Calculate Basis
    total_sale_amount = (item_price * quantity) + charged_shipping + collected_tax
    
    result = SellingFeeResult(
        marketplace_id=marketplace_id,
        category_id=category_id,
        selling_fee_currency=currency,
        fee_basis_amount=total_sale_amount,
        fee_basis_currency=currency,
        seller_store_plan=seller_store_plan,
        seller_performance_level=seller_performance_level,
        strictness=strictness,
        selling_fee_context_used={
            "item_price": item_price,
            "charged_shipping": charged_shipping,
            "collected_tax": collected_tax,
            "quantity": quantity,
            "promoted_listing_flag": promoted_listing_flag,
            "ad_rate": ad_rate,
            "international_sale_flag": international_sale_flag
        }
    )

    # Pre-validation
    if not marketplace_id:
        result.unresolved_reason = "marketplace_id_missing"
        result.add_note("selling fee unresolved: marketplace_id missing")
        return result
    
    if total_sale_amount <= 0:
        result.unresolved_reason = "total_sale_amount_invalid"
        result.add_note("selling fee unresolved: total sale amount is zero or negative")
        return result

    # Rule Collection Phase
    all_matched_rules = []
    
    ctx = {
        "marketplace_id": marketplace_id,
        "category_id": category_id,
        "store_plan": seller_store_plan,
        "performance_level": seller_performance_level,
        "promoted_listing_flag": promoted_listing_flag,
        "international_sale_flag": international_sale_flag,
        "currency": currency,
        "price": item_price
    }

    if selling_fee_rule_override:
        for rule in selling_fee_rule_override:
            if _rule_matches(rule, ctx):
                rule["_source"] = SellingFeeSourceLevel.ACCOUNT_SPECIFIC_RULE
                all_matched_rules.append(rule)

    if selling_fee_rule_master:
        for rule in selling_fee_rule_master:
            if _rule_matches(rule, ctx):
                rule["_source"] = SellingFeeSourceLevel.MARKETPLACE_FEE_MASTER
                all_matched_rules.append(rule)

    if fallback_rule:
        rules_list = fallback_rule.get("rules", [])
        for rule in rules_list:
            if _rule_matches(rule, ctx):
                rule["_source"] = SellingFeeSourceLevel.FALLBACK_MASTER
                all_matched_rules.append(rule)

    # Category/Component-based Selection
    selected_rules_by_comp = {}
    for rule in all_matched_rules:
        comp = rule.get("fee_component", "other")
        existing = selected_rules_by_comp.get(comp)
        if not existing or _is_more_specific(rule, existing):
            selected_rules_by_comp[comp] = rule

    # Application Phase
    if selected_rules_by_comp:
        for comp, rule in selected_rules_by_comp.items():
            _apply_rule(result, rule, total_sale_amount)
        
        # Determine Status and Confidence
        sources = [r["_source"] for r in selected_rules_by_comp.values()]
        if SellingFeeSourceLevel.ACCOUNT_SPECIFIC_RULE in sources:
            result.selling_fee_source_level = SellingFeeSourceLevel.ACCOUNT_SPECIFIC_RULE
            result.selling_fee_resolution_status = SellingFeeResolutionStatus.RESOLVED_EXACT
            result.selling_fee_confidence = SellingFeeConfidence.HIGH
            result.add_note("account specific selling fee rule applied")
        elif SellingFeeSourceLevel.MARKETPLACE_FEE_MASTER in sources:
            result.selling_fee_source_level = SellingFeeSourceLevel.MARKETPLACE_FEE_MASTER
            result.selling_fee_resolution_status = SellingFeeResolutionStatus.RESOLVED_ESTIMATED
            result.selling_fee_confidence = SellingFeeConfidence.MEDIUM
            result.add_note("marketplace fee master applied")
        else:
            result.selling_fee_source_level = SellingFeeSourceLevel.FALLBACK_MASTER
            result.selling_fee_resolution_status = SellingFeeResolutionStatus.FALLBACK_DEFAULT
            result.selling_fee_confidence = SellingFeeConfidence.LOW
            result.add_note("fallback selling fee rule applied")

        if len(selected_rules_by_comp) > 1:
            result.add_note("multiple selling fee rules applied")
    
    # Internal Fallback Phase (if missing essential components)
    has_master_missing = False
    if "final_value_fee" not in result.partial_fee_components:
        has_master_missing = True
        if strictness != "strict":
            result.final_value_fee_estimated_total = total_sale_amount * 0.13 # Generic 13%
            result.partial_fee_components.append("final_value_fee")
            result.add_note("fallback selling fee rule applied (FVF 13%)")
            
    if "final_value_fee_fixed" not in result.partial_fee_components:
        if strictness != "strict":
            result.final_value_fee_fixed_estimated_total = 0.40 # Generic 0.40
            result.partial_fee_components.append("final_value_fee_fixed")
            result.add_note("fixed per order fee applied (fallback 0.40)")

    # Validation Phase for strictness
    if strictness == "strict":
        if "final_value_fee" not in result.partial_fee_components:
            result.selling_fee_resolution_status = SellingFeeResolutionStatus.UNRESOLVED
            result.unresolved_reason = "missing_fvf_rule_in_strict_mode"
            result.add_note("selling fee unresolved: FVF rule missing in strict mode")

    _finalize_result(result)
    
    # Adjust status for PARTIAL
    if result.selling_fee_resolution_status in [SellingFeeResolutionStatus.RESOLVED_ESTIMATED, SellingFeeResolutionStatus.RESOLVED_EXACT]:
        if has_master_missing and strictness == "balanced":
             result.selling_fee_resolution_status = SellingFeeResolutionStatus.RESOLVED_PARTIAL
             result.add_note("selling fee partially resolved")

    if result.selling_fee_resolution_status == SellingFeeResolutionStatus.UNRESOLVED and not result.unresolved_reason:
        result.unresolved_reason = "no_matching_rules"
        result.add_note("selling fee unresolved")

    return result

def _rule_matches(rule, ctx) -> bool:
    if rule.get("marketplace_id") and rule.get("marketplace_id") != ctx["marketplace_id"]: return False
    if rule.get("category_id") and rule.get("category_id") != ctx["category_id"]: return False
    if rule.get("store_plan") and rule.get("store_plan") != ctx["store_plan"]: return False
    if rule.get("performance_level") and rule.get("performance_level") != ctx["performance_level"]: return False
    if rule.get("currency") and rule.get("currency") != ctx["currency"]: return False
    
    # Price band
    p_min = rule.get("price_band_min", 0)
    p_max = rule.get("price_band_max", float('inf'))
    if not (p_min <= ctx["price"] <= p_max): return False
    
    # Flags
    if "promoted_listing_flag" in rule and rule["promoted_listing_flag"] != ctx["promoted_listing_flag"]: return False
    if "international_sale_flag" in rule and rule["international_sale_flag"] != ctx["international_sale_flag"]: return False
    
    if rule.get("enabled") is False: return False
    
    return True

def _is_more_specific(new_rule: Dict[str, Any], existing_rule: Dict[str, Any]) -> bool:
    source_priority = {
        SellingFeeSourceLevel.ACCOUNT_SPECIFIC_RULE: 3,
        SellingFeeSourceLevel.MARKETPLACE_FEE_MASTER: 2,
        SellingFeeSourceLevel.FALLBACK_MASTER: 1
    }
    new_p = source_priority.get(new_rule.get("_source", SellingFeeSourceLevel.NONE), 0)
    old_p = source_priority.get(existing_rule.get("_source", SellingFeeSourceLevel.NONE), 0)
    
    if new_p > old_p: return True
    if new_p < old_p: return False
    
    condition_fields = [
        "marketplace_id", "category_id", "store_plan", "performance_level",
        "price_band_min", "price_band_max", "promoted_listing_flag", 
        "international_sale_flag", "currency"
    ]
    new_count = sum(1 for f in condition_fields if f in new_rule and new_rule[f] is not None)
    old_count = sum(1 for f in condition_fields if f in existing_rule and existing_rule[f] is not None)
    
    return new_count > old_count

def _apply_rule(result: SellingFeeResult, rule: Dict[str, Any], total_basis: float):
    fee_type = rule.get("fee_type", "rate")
    fee_val = 0.0
    
    if fee_type == "fixed":
        fee_val = rule.get("fixed_fee", 0.0)
    elif fee_type == "rate":
        fee_val = total_basis * rule.get("rate_fee", 0.0)
    
    if "min_fee" in rule: fee_val = max(fee_val, rule["min_fee"])
    if "max_fee" in rule: fee_val = min(fee_val, rule["max_fee"])

    comp = rule.get("fee_component", "other")
    if comp == "final_value_fee": 
        result.final_value_fee_estimated_total = fee_val
        result.add_note("final value fee rule applied")
    elif comp == "final_value_fee_fixed": 
        result.final_value_fee_fixed_estimated_total = fee_val
        result.add_note("fixed per order fee applied")
    elif comp == "insertion_fee": result.insertion_fee_estimated_total = fee_val
    elif comp == "ad_fee": 
        result.ad_fee_estimated_total = fee_val
        result.add_note("promoted listing fee applied")
    elif comp == "international_fee": 
        result.international_fee_estimated_total = fee_val
        result.add_note("international selling fee applied")
    elif comp == "regulatory_fee": result.regulatory_fee_estimated_total = fee_val
    elif comp == "payment_processing_fee": result.payment_processing_fee_estimated_total = fee_val
    else: result.other_selling_fee_estimated_total = fee_val

    if rule.get("rule_id"):
        result.applied_rule_ids.append(rule["rule_id"])
        result.applied_rule_count += 1
        result.fee_rule_applied = rule["rule_id"]
    
    result.partial_fee_components.append(comp)

def _finalize_result(result: SellingFeeResult):
    result.selling_fee_estimated_total = (
        result.final_value_fee_estimated_total +
        result.final_value_fee_fixed_estimated_total +
        result.insertion_fee_estimated_total +
        result.ad_fee_estimated_total +
        result.international_fee_estimated_total +
        result.regulatory_fee_estimated_total +
        result.payment_processing_fee_estimated_total +
        result.other_selling_fee_estimated_total
    )
    
    if result.selling_fee_resolution_status == SellingFeeResolutionStatus.UNRESOLVED and result.partial_fee_components:
         if not result.applied_rule_ids:
             result.selling_fee_resolution_status = SellingFeeResolutionStatus.FALLBACK_DEFAULT
             result.selling_fee_confidence = SellingFeeConfidence.LOW
             result.selling_fee_source_level = SellingFeeSourceLevel.FALLBACK_MASTER
         else:
             result.selling_fee_resolution_status = SellingFeeResolutionStatus.RESOLVED_PARTIAL
             result.selling_fee_confidence = SellingFeeConfidence.LOW
             # If some rules were applied, source level might already be set or should be set to master if those were master
             if not result.selling_fee_source_level or result.selling_fee_source_level == SellingFeeSourceLevel.NONE:
                 result.selling_fee_source_level = SellingFeeSourceLevel.FALLBACK_MASTER
