from typing import Dict, Any, Optional, List
from .models import (
    TotalCostResult,
    TotalCostResolutionStatus,
    TotalCostConfidence,
    TotalCostSourceLevel
)

def resolve_total_cost(
    procurement_item_cost: float,
    sale_item_price: float,
    buyer_charged_shipping: float = 0.0,
    collected_tax: float = 0.0,
    quantity: int = 1,
    currency: str = "USD",
    shipping_result: Optional[Any] = None,
    import_result: Optional[Any] = None,
    selling_fee_result: Optional[Any] = None,
    payout_fee_result: Optional[Any] = None,
    additional_fixed_cost: float = 0.0,
    additional_variable_cost: float = 0.0,
    strictness: str = "balanced"
) -> TotalCostResult:
    result = TotalCostResult(
        total_cost_currency=currency,
        additional_fixed_cost_total=additional_fixed_cost,
        additional_variable_cost_total=additional_variable_cost,
        total_cost_context_used={
            "procurement_item_cost": procurement_item_cost,
            "sale_item_price": sale_item_price,
            "buyer_charged_shipping": buyer_charged_shipping,
            "collected_tax": collected_tax,
            "quantity": quantity,
            "strictness": strictness
        }
    )

    # 1. Sales metrics
    result.gross_sale_ex_tax = (sale_item_price * quantity) + buyer_charged_shipping
    result.gross_checkout_total = result.gross_sale_ex_tax + collected_tax
    result.add_note("tax excluded from profit base")

    # 2. Procurement metrics
    result.procurement_item_cost_total = procurement_item_cost * quantity
    if procurement_item_cost <= 0:
        result.unresolved_components.append("procurement")

    # 3. Aggregate Component Costs
    # Shipping
    if shipping_result:
        result.shipping_cost_total = getattr(shipping_result, "shipping_estimated_total", 0.0)
        _propagate_quality(result, "shipping", shipping_result)
    else:
        result.unresolved_components.append("shipping")

    # Import
    if import_result:
        result.import_cost_total = getattr(import_result, "import_charges_estimated_total", 0.0)
        _propagate_quality(result, "import", import_result)
    else:
        result.unresolved_components.append("import")

    # Selling Fee
    if selling_fee_result:
        result.selling_cost_total = getattr(selling_fee_result, "selling_fee_estimated_total", 0.0)
        _propagate_quality(result, "selling_fee", selling_fee_result)
    else:
        result.unresolved_components.append("selling_fee")

    # Payout Fee
    if payout_fee_result:
        result.payout_cost_total = getattr(payout_fee_result, "payout_fee_estimated_total", 0.0)
        _propagate_quality(result, "payout_fee", payout_fee_result)
    else:
        result.partial_components.append("payout_fee")
        result.add_note("payout fee missing, profit_before_payout_fee only")

    # 4. Total Aggregation
    result.landed_procurement_cost_total = (
        result.procurement_item_cost_total + 
        result.shipping_cost_total + 
        result.import_cost_total
    )
    
    result.total_cost_estimated = (
        result.landed_procurement_cost_total +
        result.selling_cost_total +
        result.payout_cost_total +
        result.additional_fixed_cost_total +
        result.additional_variable_cost_total
    )

    # 5. Profit Metrics
    result.profit_before_payout_fee = (
        result.gross_sale_ex_tax -
        result.landed_procurement_cost_total -
        result.selling_cost_total -
        result.additional_fixed_cost_total -
        result.additional_variable_cost_total
    )
    
    result.final_profit_after_all_costs = result.gross_sale_ex_tax - result.total_cost_estimated
    result.add_note("final profit calculated after all costs")

    # Margin and ROI
    if result.gross_sale_ex_tax > 0:
        result.estimated_margin_rate = result.final_profit_after_all_costs / result.gross_sale_ex_tax
    
    if result.landed_procurement_cost_total > 0:
        result.estimated_roi = result.final_profit_after_all_costs / result.landed_procurement_cost_total

    # 6. Final Status and Confidence
    _determine_final_status(result, strictness)
    _determine_final_confidence(result)

    return result

def _propagate_quality(result: TotalCostResult, name: str, sub_result: Any):
    status = None
    if name == "shipping": status = getattr(sub_result, "shipping_resolution_status", None)
    elif name == "import": status = getattr(sub_result, "import_resolution_status", None)
    elif name == "selling_fee": status = getattr(sub_result, "selling_fee_resolution_status", None)
    elif name == "payout_fee": status = getattr(sub_result, "payout_resolution_status", None)

    if status:
        status_str = str(status).lower()
        if "fallback" in status_str:
            result.fallback_components.append(name)
        if "partial" in status_str:
            result.partial_components.append(name)
        if "unresolved" in status_str:
            result.unresolved_components.append(name)

def _determine_final_status(result: TotalCostResult, strictness: str):
    # Requirements for Exact/Estimated
    major_components = ["procurement", "shipping", "import", "selling_fee"]
    is_unresolved = any(c in result.unresolved_components for c in major_components)
    is_partial = any(c in result.partial_components for c in major_components + ["payout_fee"])
    is_fallback = any(c in result.fallback_components for c in major_components + ["payout_fee"])

    if strictness == "strict":
        if is_unresolved or is_partial or is_fallback:
            result.total_cost_resolution_status = TotalCostResolutionStatus.UNRESOLVED
            result.total_cost_source_level = TotalCostSourceLevel.UNRESOLVED
            result.add_note("total cost unresolved due to missing or uncertain component(s) in strict mode")
            return
    
    if "procurement" in result.unresolved_components or "selling_fee" in result.unresolved_components:
        result.total_cost_resolution_status = TotalCostResolutionStatus.UNRESOLVED
        result.total_cost_source_level = TotalCostSourceLevel.UNRESOLVED
        if "procurement" in result.unresolved_components:
            result.add_note("total cost unresolved due to missing procurement cost")
        else:
            result.add_note("total cost unresolved due to missing selling fee")
        return

    if is_unresolved or is_partial:
        result.total_cost_resolution_status = TotalCostResolutionStatus.RESOLVED_PARTIAL
        result.total_cost_source_level = TotalCostSourceLevel.PARTIAL_AGGREGATION
        result.add_note("partial cost aggregation")
    elif is_fallback:
        result.total_cost_resolution_status = TotalCostResolutionStatus.FALLBACK_DEFAULT
        result.total_cost_source_level = TotalCostSourceLevel.FALLBACK_HEAVY
        result.add_note("fallback components present")
    else:
        result.total_cost_resolution_status = TotalCostResolutionStatus.RESOLVED_ESTIMATED
        result.total_cost_source_level = TotalCostSourceLevel.FULL_AGGREGATION
        result.add_note("total cost aggregation completed")

def _determine_final_confidence(result: TotalCostResult):
    if result.total_cost_resolution_status == TotalCostResolutionStatus.UNRESOLVED:
        result.total_cost_confidence = TotalCostConfidence.NONE
        return

    # Confidence logic based on count of degraded components
    degraded_count = len(result.fallback_components) + len(result.partial_components) + len(result.unresolved_components)
    
    if degraded_count == 0:
        result.total_cost_confidence = TotalCostConfidence.HIGH
    elif degraded_count <= 1:
        result.total_cost_confidence = TotalCostConfidence.MEDIUM
    else:
        result.total_cost_confidence = TotalCostConfidence.LOW
