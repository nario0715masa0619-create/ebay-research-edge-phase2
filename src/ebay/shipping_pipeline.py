from typing import Dict, Any, Optional
from .browse_client import EbayBrowseClient
from .snapshot_adapters import SnapshotAdapter
from src.shipping.resolver import resolve_shipping_cost
from src.shipping.models import ShippingResult, ShippingResolutionStatus

class ShippingPipeline:
    def __init__(self, client: EbayBrowseClient):
        self.client = client
        self.adapter = SnapshotAdapter()

    def should_fetch_detail(self, search_snapshot: Dict[str, Any]) -> bool:
        """
        Determine if we need more info from getItem.
        Example: search shows CALCULATED or missing options.
        For best accuracy, we usually always fetch detail if possible.
        """
        options = search_snapshot.get("shippingOptions", [])
        if not options:
            return True
        
        # If any option is CALCULATED, detail might provide more accurate info
        for opt in options:
            if opt.get("shippingCostType") == "CALCULATED":
                return True
        
        return False

    def resolve_item_shipping_via_api(
        self, 
        item_id: str, 
        marketplace_id: str, 
        country: str,
        zip_code: str = None,
        quantity: int = 1,
        search_item_summary: Optional[Any] = None,
        fallback_value: Optional[float] = None
    ) -> ShippingResult:
        """
        Main pipeline flow:
        1. Adapt search summary (if provided)
        2. Decide if detail fetch is needed
        3. Fetch detail (if needed or always)
        4. Resolve using resolver
        """
        search_snapshot = None
        if search_item_summary:
            search_snapshot = self.adapter.adapt_search_item_summary_to_snapshot(search_item_summary)

        # Always try to fetch detail for accuracy if item_id is provided
        detail_snapshot = None
        try:
            detail_data = self.client.get_item_with_context(item_id, country, zip_code, marketplace_id)
            if detail_data:
                detail_snapshot = self.adapter.adapt_detail_item_to_snapshot(detail_data)
        except Exception as e:
            # If detail fetch fails, we continue with search_snapshot only
            pass

        return resolve_shipping_cost(
            item_id=item_id,
            marketplace_id=marketplace_id,
            delivery_country=country,
            quantity=quantity,
            context={"zip_code": zip_code},
            search_snapshot=search_snapshot,
            detail_snapshot=detail_snapshot,
            fallback_shipping_value=fallback_value
        )

    def enrich_item_with_shipping(self, item_summary: Any, country: str, marketplace_id: str) -> Dict[str, Any]:
        """Convenience method to add shipping info to a search item result"""
        result = self.resolve_item_shipping_via_api(
            item_id=item_summary.item_id,
            marketplace_id=marketplace_id,
            country=country,
            search_item_summary=item_summary
        )
        
        return {
            "item_id": item_summary.item_id,
            "shipping_info": result
        }
