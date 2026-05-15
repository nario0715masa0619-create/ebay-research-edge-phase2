from typing import Dict, Any, Optional, List
from .models import (
    ShippingResult, 
    ShippingResolutionStatus, 
    ShippingConfidence, 
    ShippingSourceLevel
)

def resolve_shipping_cost(
    item_id: str,
    marketplace_id: str,
    delivery_country: str,
    quantity: int = 1,
    context: Optional[Dict[str, Any]] = None,
    search_snapshot: Optional[Dict[str, Any]] = None,
    detail_snapshot: Optional[Dict[str, Any]] = None,
    fallback_shipping_value: Optional[float] = None
) -> ShippingResult:
    result = ShippingResult(
        quantity_basis=quantity,
        delivery_context_used={
            "item_id": item_id,
            "marketplace_id": marketplace_id,
            "delivery_country": delivery_country,
            "context": context or {}
        }
    )

    # 1. Determine which snapshot to use (Detail > Search)
    target_snapshot = None
    source_level = ShippingSourceLevel.NONE

    if detail_snapshot:
        target_snapshot = detail_snapshot
        source_level = ShippingSourceLevel.DETAIL
    elif search_snapshot:
        target_snapshot = search_snapshot
        source_level = ShippingSourceLevel.SEARCH

    if not target_snapshot:
        return _handle_fallback(result, fallback_shipping_value)

    result.shipping_source_level = source_level
    
    # 2. Extract Shipping Options
    shipping_options = target_snapshot.get("shippingOptions", [])
    result.raw_shipping_options_snapshot = shipping_options

    if not shipping_options:
        result.add_note("No shipping options found in snapshot.")
        return _handle_fallback(result, fallback_shipping_value)

    # 3. Filter and Select Best Option
    # Exclude "LOCAL_PICKUP"
    valid_options = []
    for opt in shipping_options:
        # eBay API field names vary slightly between search and detail
        # In search: shippingCostType
        # In detail: type (sometimes) or shippingCostType
        cost_type = opt.get("shippingCostType") or opt.get("type")
        
        # Check for local pickup (usually in service name or description, but sometimes in type)
        service_name = opt.get("shippingServiceCode", "").upper()
        if "LOCALPICKUP" in service_name or "LOCAL PICKUP" in service_name:
            continue
            
        valid_options.append(opt)

    if not valid_options:
        result.add_note("All shipping options were filtered out (e.g., Local Pickup only).")
        return _handle_fallback(result, fallback_shipping_value)

    # Prioritize FIXED over CALCULATED, then cheapest
    fixed_options = [o for o in valid_options if (o.get("shippingCostType") or o.get("type")) == "FIXED"]
    calculated_options = [o for o in valid_options if (o.get("shippingCostType") or o.get("type")) == "CALCULATED"]

    selected_option = None
    if fixed_options:
        # Sort by cost value
        selected_option = min(fixed_options, key=lambda x: float(x.get("shippingCost", {}).get("value", 0)))
        result.shipping_cost_type = "FIXED"
        result.shipping_resolution_status = ShippingResolutionStatus.RESOLVED_EXACT
        result.shipping_confidence = ShippingConfidence.HIGH
    elif calculated_options:
        selected_option = min(calculated_options, key=lambda x: float(x.get("shippingCost", {}).get("value", 0)))
        result.shipping_cost_type = "CALCULATED"
        result.shipping_resolution_status = ShippingResolutionStatus.RESOLVED_ESTIMATED
        result.shipping_confidence = ShippingConfidence.MEDIUM
    else:
        # Other types? fallback
        selected_option = min(valid_options, key=lambda x: float(x.get("shippingCost", {}).get("value", 0)))
        result.shipping_cost_type = selected_option.get("shippingCostType") or selected_option.get("type") or "UNKNOWN"
        result.shipping_resolution_status = ShippingResolutionStatus.RESOLVED_PARTIAL
        result.shipping_confidence = ShippingConfidence.LOW

    # 4. Fill result from selected option
    cost_obj = selected_option.get("shippingCost", {})
    result.shipping_estimated_total = float(cost_obj.get("value", 0))
    result.shipping_currency = cost_obj.get("currency", "")
    result.selected_option_summary = f"{result.shipping_cost_type}: {selected_option.get('shippingServiceCode', 'Standard')}"

    # 5. Handle Import Charges, Taxes, and Return Risk (Only in detail)
    if source_level == ShippingSourceLevel.DETAIL:
        # Import Charges
        import_charges = target_snapshot.get("estimatedImportCosts", {})
        if import_charges:
            result.import_charges_included_flag = True
            result.import_charges_estimated_total = float(import_charges.get("amount", {}).get("value", 0))
            result.add_note(f"Import charges found: {result.import_charges_estimated_total}")

        # Taxes / VAT context
        taxes = target_snapshot.get("taxes", [])
        if taxes:
            result.taxes_included_flag = True
            result.vat_included_flag = True # eBay taxes field often implies VAT/SalesTax
            result.add_note("Taxes/VAT info present.")
        else:
            result.vat_included_flag = None # Unknown
            result.taxes_included_flag = None # Unknown
            result.add_note("VAT/Tax context is missing (Unknown).")
            # Confidence drop if context is missing
            if result.shipping_confidence == ShippingConfidence.HIGH:
                result.shipping_confidence = ShippingConfidence.MEDIUM
            elif result.shipping_confidence == ShippingConfidence.MEDIUM:
                result.shipping_confidence = ShippingConfidence.LOW

        # Return Risk
        return_terms = target_snapshot.get("returnTerms", {})
        payer = return_terms.get("returnShippingCostPayer", "")
        if payer == "SELLER":
            result.return_shipping_risk_flag = True
            result.add_note("Seller pays for return shipping (Risk flag set per spec).")
        elif payer == "BUYER":
            result.return_shipping_risk_flag = False
            result.add_note("Buyer pays for return shipping.")
        else:
            result.return_shipping_risk_flag = False
            result.add_note("Return shipping payer unknown.")

    # 6. Adjust Confidence if Search Snapshot used
    if source_level == ShippingSourceLevel.SEARCH:
        if result.shipping_confidence == ShippingConfidence.HIGH:
            result.shipping_confidence = ShippingConfidence.MEDIUM
        result.add_note("Used search snapshot (lower confidence).")

    return result

def _handle_fallback(result: ShippingResult, fallback_value: Optional[float]) -> ShippingResult:
    if fallback_value is not None:
        result.shipping_estimated_total = fallback_value
        result.shipping_source_level = ShippingSourceLevel.FALLBACK
        result.shipping_resolution_status = ShippingResolutionStatus.FALLBACK_DEFAULT
        result.shipping_confidence = ShippingConfidence.LOW
        result.add_note(f"Using fallback shipping value: {fallback_value}")
        return result
    
    result.shipping_resolution_status = ShippingResolutionStatus.UNRESOLVED
    result.shipping_confidence = ShippingConfidence.NONE
    result.add_note("No valid shipping info found and no fallback provided.")
    return result
