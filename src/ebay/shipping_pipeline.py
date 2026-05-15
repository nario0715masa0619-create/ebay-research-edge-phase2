from typing import Dict, Any, Optional, List, Tuple
from .browse_client import EbayBrowseClient
from .snapshot_adapters import SnapshotAdapter
from src.shipping.resolver import resolve_shipping_cost, normalize_carrier, ALLOWED_CARRIERS, CarrierNormalized
from src.shipping.models import ShippingResult, ShippingResolutionStatus
from src.import_cost.resolver import resolve_import_charges
from src.import_cost.models import ImportChargeResult

class ShippingPipeline:
    def __init__(self, client: EbayBrowseClient):
        self.client = client
        self.adapter = SnapshotAdapter()

    def should_fetch_detail(self, search_snapshot: Optional[Dict[str, Any]], mode: str = "balanced") -> Tuple[bool, List[str]]:
        """
        Determine if we need more info from getItem based on policies and accuracy requirements.
        Returns (should_fetch: bool, reasons: list[str])
        """
        reasons = []

        if mode == "always_detail":
            return True, ["always_detail_mode"]
        
        if mode == "search_only":
            return False, []

        if not search_snapshot:
            return True, ["no_search_snapshot"]

        options = search_snapshot.get("shippingOptions", [])
        if not options:
            return True, ["no_shipping_options"]

        allowed_count = 0
        has_unknown = False
        has_calculated = False
        has_missing_service_name = False
        has_local_pickup_only = True # Assume true until we find a non-local-pickup option
        allowed_fixed_count = 0
        cheapest_is_disallowed = False
        has_free_shipping_unknown = False

        processed_options = []
        for opt in options:
            service_name = opt.get("shippingServiceCode", "")
            if not service_name:
                has_missing_service_name = True
            
            carrier = normalize_carrier(service_name)
            cost_type = opt.get("shippingCostType") or opt.get("type") or "UNKNOWN"
            cost_value = float(opt.get("shippingCost", {}).get("value", 0))
            
            is_local_pickup = "LOCALPICKUP" in service_name.upper() or "LOCAL PICKUP" in service_name.upper()
            if not is_local_pickup:
                has_local_pickup_only = False
            
            is_allowed = carrier.value in ALLOWED_CARRIERS
            if is_allowed and not is_local_pickup:
                allowed_count += 1
                if cost_type == "FIXED":
                    allowed_fixed_count += 1
            
            if carrier == CarrierNormalized.UNKNOWN:
                has_unknown = True
                if cost_value == 0:
                    has_free_shipping_unknown = True
            
            if cost_type == "CALCULATED":
                has_calculated = True

            processed_options.append({
                "carrier": carrier,
                "is_allowed": is_allowed,
                "cost_value": cost_value,
                "is_local_pickup": is_local_pickup
            })

        # Check if cheapest is disallowed
        if processed_options:
            available = [o for o in processed_options if not o["is_local_pickup"]]
            if available:
                cheapest = min(available, key=lambda x: x["cost_value"])
                if not cheapest["is_allowed"]:
                    cheapest_is_disallowed = True
            else:
                has_local_pickup_only = True

        # Evaluation
        if allowed_count == 0: reasons.append("no_allowed_carrier")
        if has_unknown: reasons.append("unknown_carrier")
        if has_missing_service_name: reasons.append("missing_service_name")
        if allowed_count > 0 and allowed_fixed_count == 0: reasons.append("calculated_shipping_only")
        if has_local_pickup_only: reasons.append("local_pickup_only")
        if has_free_shipping_unknown: reasons.append("free_shipping_unknown_carrier")
        
        # Mode specific extra checks
        if mode == "aggressive_accuracy":
            reasons.append("aggressive_accuracy_mode_check")
            reasons.append("tax_context_missing")
            reasons.append("import_charges_check_needed")

        should_fetch = len(reasons) > 0
        return should_fetch, reasons

    def resolve_item_shipping_via_api(
        self, 
        item_id: str, 
        marketplace_id: str, 
        country: str,
        zip_code: str = None,
        quantity: int = 1,
        search_item_summary: Optional[Any] = None,
        fallback_value: Optional[float] = None,
        fallback_import_rule: Optional[Dict[str, Any]] = None,
        mode: str = "balanced"
    ) -> Tuple[ShippingResult, ImportChargeResult]:
        """
        Optimized flow:
        1. Adapt search
        2. Check should_fetch_detail
        3. Fetch detail only if needed
        4. Resolve Shipping AND Import Charges
        """
        detail_fetch_attempted = False
        detail_fetch_succeeded = False
        detail_fetch_reason = []
        
        search_snapshot = None
        if search_item_summary:
            search_snapshot = self.adapter.adapt_search_item_summary_to_snapshot(search_item_summary)

        should_fetch, reasons = self.should_fetch_detail(search_snapshot, mode)
        detail_fetch_reason = reasons

        detail_snapshot = None
        if should_fetch:
            detail_fetch_attempted = True
            try:
                detail_data = self.client.get_item_with_context(item_id, country, zip_code, marketplace_id)
                if detail_data:
                    detail_fetch_succeeded = True
                    detail_snapshot = self.adapter.adapt_detail_item_to_snapshot(detail_data)
            except Exception:
                pass

        # Resolve Shipping
        shipping_result = resolve_shipping_cost(
            item_id=item_id,
            marketplace_id=marketplace_id,
            delivery_country=country,
            quantity=quantity,
            context={"zip_code": zip_code},
            search_snapshot=search_snapshot,
            detail_snapshot=detail_snapshot,
            fallback_shipping_value=fallback_value
        )
        
        # Add metadata to shipping_result
        shipping_result.detail_fetch_attempted = detail_fetch_attempted
        shipping_result.detail_fetch_succeeded = detail_fetch_succeeded
        shipping_result.detail_fetch_reason = detail_fetch_reason
        shipping_result.pipeline_mode = mode

        # Resolve Import Charges
        item_price = 0.0
        if search_item_summary and hasattr(search_item_summary, 'price'):
            item_price = float(search_item_summary.price.get("value", 0))
        elif detail_snapshot:
            item_price = float(detail_snapshot.get("price", {}).get("value", 0))

        import_result = resolve_import_charges(
            item_id=item_id,
            marketplace_id=marketplace_id,
            delivery_country=country,
            quantity=quantity,
            item_price=item_price,
            shipping_estimate=shipping_result.shipping_estimated_total,
            search_snapshot=search_snapshot,
            detail_snapshot=detail_snapshot,
            fallback_import_rule=fallback_import_rule
        )
        
        return shipping_result, import_result

    def enrich_item_with_shipping(self, item_summary: Any, country: str, marketplace_id: str, mode: str = "balanced") -> Dict[str, Any]:
        """Convenience method to add shipping info, import info and metadata to a search item result"""
        shipping_result, import_result = self.resolve_item_shipping_via_api(
            item_id=item_summary.item_id,
            marketplace_id=marketplace_id,
            country=country,
            search_item_summary=item_summary,
            mode=mode
        )
        
        return {
            "item_id": item_summary.item_id,
            "shipping_info": shipping_result,
            "import_info": import_result,
            "pipeline_meta": {
                "detail_fetch_attempted": shipping_result.detail_fetch_attempted,
                "detail_fetch_succeeded": shipping_result.detail_fetch_succeeded,
                "detail_fetch_reason": shipping_result.detail_fetch_reason,
                "mode": shipping_result.pipeline_mode
            }
        }
