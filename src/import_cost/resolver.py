from typing import Dict, Any, Optional, List
from .models import (
    ImportChargeResult,
    ImportResolutionStatus,
    ImportConfidence,
    ImportSourceLevel
)

def resolve_import_charges(
    item_id: str,
    marketplace_id: str,
    delivery_country: str,
    quantity: int = 1,
    item_price: float = 0.0,
    shipping_estimate: float = 0.0,
    search_snapshot: Optional[Dict[str, Any]] = None,
    detail_snapshot: Optional[Dict[str, Any]] = None,
    fallback_import_rule: Optional[Dict[str, Any]] = None,
) -> ImportChargeResult:
    result = ImportChargeResult(
        quantity_basis=quantity,
        delivery_context_used={
            "item_id": item_id,
            "marketplace_id": marketplace_id,
            "delivery_country": delivery_country,
            "item_price": item_price,
            "shipping_estimate": shipping_estimate
        }
    )

    # 1. Check Detail Snapshot (Priority 1)
    if detail_snapshot:
        result.raw_import_snapshot = detail_snapshot
        
        # A. Check shippingOptions for importCharges
        # Note: In getItem, shippingOptions is a list. We usually look at the selected/relevant option.
        # For simplicity, we look for any option that has importCharges.
        shipping_options = detail_snapshot.get("shippingOptions", [])
        import_charges_found = False
        
        for opt in shipping_options:
            ic = opt.get("importCharges")
            if ic:
                result.import_charges_estimated_total = float(ic.get("amount", {}).get("value", 0))
                result.import_charges_currency = ic.get("amount", {}).get("currency", "")
                result.import_charges_included_flag = True
                # eBay usually implies these are payable at checkout if listed here
                result.payable_at_checkout_flag = True 
                
                result.import_cost_source_level = ImportSourceLevel.DETAIL_IMPORT_CHARGES
                result.import_resolution_status = ImportResolutionStatus.RESOLVED_EXACT
                result.import_confidence = ImportConfidence.HIGH
                result.add_note("import charges found from detail (shippingOptions.importCharges)")
                import_charges_found = True
                break
        
        if import_charges_found:
            # Still process taxes if present to enrich metadata
            _enrich_from_taxes(result, detail_snapshot)
            return result

        # B. Check taxes container
        if _enrich_from_taxes(result, detail_snapshot):
            # If taxes exist but no total importCharges, we might have partial info
            result.import_cost_source_level = ImportSourceLevel.DETAIL_TAXES
            result.import_resolution_status = ImportResolutionStatus.RESOLVED_PARTIAL
            result.import_confidence = ImportConfidence.MEDIUM
            result.add_note("tax information found from detail, but total import charges missing")
            return result

    # 2. Fallback Rule (Priority 2)
    if fallback_import_rule:
        # Example rule: {"rate": 0.1, "rule_id": "standard_vat"}
        rate = fallback_import_rule.get("rate", 0)
        result.import_tax_estimated_total = item_price * rate * quantity
        result.import_charges_estimated_total = result.import_tax_estimated_total
        result.import_cost_source_level = ImportSourceLevel.FALLBACK_MASTER
        result.import_resolution_status = ImportResolutionStatus.FALLBACK_DEFAULT
        result.import_confidence = ImportConfidence.LOW
        result.fallback_rule_used = fallback_import_rule.get("rule_id", "default")
        result.add_note(f"fallback import rule applied: {result.fallback_rule_used}")
        return result

    # 3. Unresolved
    result.import_resolution_status = ImportResolutionStatus.UNRESOLVED
    result.import_confidence = ImportConfidence.NONE
    result.add_note("import charges unavailable, unresolved")
    return result

def _enrich_from_taxes(result: ImportChargeResult, snapshot: Dict[str, Any]) -> bool:
    """Extract tax info from taxes container"""
    taxes = snapshot.get("taxes", [])
    if not taxes:
        return False
    
    result.tax_present_flag = True
    # We take info from the first tax record for simplicity
    tax = taxes[0]
    
    result.tax_percentage = float(tax.get("taxPercentage", 0))
    result.tax_included_in_price_flag = tax.get("includedInPrice", False)
    result.shipping_taxed_flag = tax.get("shippingAndHandlingTaxed", False)
    
    # If there is a Collect and Remit tax amount
    tax_amount = tax.get("ebayCollectAndRemitTax", False)
    # The actual amount might be in a different field or nested
    # Some responses have 'amount' inside the tax object
    amount_obj = tax.get("amount")
    if amount_obj:
        val = float(amount_obj.get("value", 0))
        result.import_tax_estimated_total = val
        result.import_charges_currency = amount_obj.get("currency", "")
        # If it's collect and remit, it's payable at checkout
        if tax_collect := tax.get("ebayCollectAndRemitTax"):
            result.payable_at_checkout_flag = True
            
    return True
