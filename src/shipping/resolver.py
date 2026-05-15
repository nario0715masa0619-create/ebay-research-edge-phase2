from typing import Dict, Any, Optional, List, Set
from .models import (
    ShippingResult, 
    ShippingResolutionStatus, 
    ShippingConfidence, 
    ShippingSourceLevel,
    CarrierNormalized,
    CarrierFilterStatus
)

ALLOWED_CARRIERS: Set[str] = {"FEDEX", "POSTAL"}

def normalize_carrier(service_name: str) -> CarrierNormalized:
    if not service_name or service_name.strip() == "":
        return CarrierNormalized.UNKNOWN
        
    name = service_name.lower()
    
    # FEDEX
    fedex_keywords = ["fedex", "fedex express", "fedex international", "fedex priority", "fedex economy", "fedex ground"]
    if any(k in name for k in fedex_keywords):
        return CarrierNormalized.FEDEX
        
    # POSTAL
    postal_keywords = [
        "usps", "post", "postal", "parcel post", "japan post", "royal mail", "auspost", 
        "australia post", "canada post", "la poste", "deutsche post", "china post", 
        "hongkong post", "singpost", "mail service", "standard post", "economy post"
    ]
    if any(k in name for k in postal_keywords):
        return CarrierNormalized.POSTAL
        
    return CarrierNormalized.OTHER

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
        return _handle_fallback(result, fallback_shipping_value, CarrierFilterStatus.NO_ALLOWED_CARRIER_FOUND)

    result.shipping_source_level = source_level
    
    # 2. Extract Shipping Options
    shipping_options = target_snapshot.get("shippingOptions", [])
    result.raw_shipping_options_snapshot = shipping_options

    if not shipping_options:
        result.add_note("No shipping options found in snapshot.")
        return _handle_fallback(result, fallback_shipping_value, CarrierFilterStatus.NO_ALLOWED_CARRIER_FOUND)

    # 3. Process and Filter Options
    processed_options = []
    for opt in shipping_options:
        service_name = opt.get("shippingServiceCode", "")
        # In search, sometimes it's just a generic name
        carrier = normalize_carrier(service_name)
        
        is_local_pickup = False
        upper_service = service_name.upper()
        if "LOCALPICKUP" in upper_service or "LOCAL PICKUP" in upper_service:
            is_local_pickup = True
            
        processed_options.append({
            "raw": opt,
            "service_name": service_name,
            "carrier": carrier,
            "is_allowed": carrier.value in ALLOWED_CARRIERS,
            "is_local_pickup": is_local_pickup,
            "cost_type": opt.get("shippingCostType") or opt.get("type") or "UNKNOWN",
            "cost_value": float(opt.get("shippingCost", {}).get("value", 0))
        })

    # Filter out Local Pickup
    available_options = [o for o in processed_options if not o["is_local_pickup"]]
    
    if not available_options:
        result.add_note("All shipping options were filtered out (e.g., Local Pickup only).")
        return _handle_fallback(result, fallback_shipping_value, CarrierFilterStatus.NO_ALLOWED_CARRIER_FOUND)

    # Separate by Carrier Status
    allowed_options = [o for o in available_options if o["is_allowed"]]
    unknown_options = [o for o in available_options if o["carrier"] == CarrierNormalized.UNKNOWN]
    other_options = [o for o in available_options if o["carrier"] == CarrierNormalized.OTHER]

    selected_option_data = None
    
    if allowed_options:
        # Prioritize FIXED over CALCULATED
        fixed_allowed = [o for o in allowed_options if o["cost_type"] == "FIXED"]
        calc_allowed = [o for o in allowed_options if o["cost_type"] == "CALCULATED"]
        
        if fixed_allowed:
            selected_option_data = min(fixed_allowed, key=lambda x: x["cost_value"])
            result.shipping_resolution_status = ShippingResolutionStatus.RESOLVED_EXACT
            result.shipping_confidence = ShippingConfidence.HIGH
        elif calc_allowed:
            selected_option_data = min(calc_allowed, key=lambda x: x["cost_value"])
            result.shipping_resolution_status = ShippingResolutionStatus.RESOLVED_ESTIMATED
            result.shipping_confidence = ShippingConfidence.MEDIUM
        else:
            selected_option_data = min(allowed_options, key=lambda x: x["cost_value"])
            result.shipping_resolution_status = ShippingResolutionStatus.RESOLVED_PARTIAL
            result.shipping_confidence = ShippingConfidence.LOW
            
        result.carrier_filter_status = CarrierFilterStatus.ALLOWED_CARRIER_SELECTED
        result.carrier_allowed_flag = True
        
        # Check if we ignored a cheaper disallowed carrier
        if other_options:
            cheapest_other = min(other_options, key=lambda x: x["cost_value"])
            if cheapest_other["cost_value"] < selected_option_data["cost_value"]:
                result.add_note(f"Cheapest option was disallowed carrier ({cheapest_other['carrier'].value}). Selected FedEx/Postal instead.")

    elif unknown_options:
        # If we only have unknown carriers
        if source_level == ShippingSourceLevel.SEARCH:
            result.carrier_filter_status = CarrierFilterStatus.CARRIER_UNKNOWN_NEEDS_DETAIL
            result.add_note("Carrier unknown in search, detail fetch recommended.")
        else:
            result.carrier_filter_status = CarrierFilterStatus.CARRIER_UNKNOWN_AFTER_DETAIL
            result.add_note("Carrier unknown even after detail fetch.")
            
        return _handle_fallback(result, fallback_shipping_value, result.carrier_filter_status)

    else:
        # Only disallowed carriers found
        result.carrier_filter_status = CarrierFilterStatus.ONLY_DISALLOWED_CARRIERS_FOUND
        result.add_note("Only disallowed carriers found (e.g. DHL, UPS).")
        return _handle_fallback(result, fallback_shipping_value, CarrierFilterStatus.ONLY_DISALLOWED_CARRIERS_FOUND)

    # 4. Fill result from selected option
    opt = selected_option_data["raw"]
    cost_obj = opt.get("shippingCost", {})
    result.shipping_estimated_total = selected_option_data["cost_value"]
    result.shipping_currency = cost_obj.get("currency", "")
    result.shipping_cost_type = selected_option_data["cost_type"]
    result.service_name_raw = selected_option_data["service_name"]
    result.carrier_normalized = selected_option_data["carrier"]
    result.selected_option_summary = f"{result.carrier_normalized.value} ({result.shipping_cost_type}): {result.service_name_raw}"

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
            result.vat_included_flag = True
            result.add_note("Taxes/VAT info present.")
        else:
            result.vat_included_flag = None
            result.taxes_included_flag = None
            result.add_note("VAT/Tax context is missing (Unknown).")
            # Confidence drop
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

def _handle_fallback(result: ShippingResult, fallback_value: Optional[float], filter_status: CarrierFilterStatus) -> ShippingResult:
    result.carrier_filter_status = filter_status
    
    if fallback_value is not None:
        result.shipping_estimated_total = fallback_value
        result.shipping_source_level = ShippingSourceLevel.FALLBACK
        result.shipping_resolution_status = ShippingResolutionStatus.FALLBACK_DEFAULT
        result.shipping_confidence = ShippingConfidence.LOW
        result.carrier_filter_status = CarrierFilterStatus.FALLBACK_USED_DUE_TO_NO_ALLOWED_CARRIER
        result.add_note(f"Using fallback shipping value: {fallback_value} due to carrier constraints.")
        return result
    
    result.shipping_resolution_status = ShippingResolutionStatus.UNRESOLVED
    result.shipping_confidence = ShippingConfidence.NONE
    if result.carrier_filter_status == CarrierFilterStatus.NONE:
        result.carrier_filter_status = CarrierFilterStatus.UNRESOLVED_NO_ALLOWED_CARRIER
    result.add_note("No valid shipping info found matching carrier constraints.")
    return result
