from typing import Dict, Any, Optional
from .models import EbayApiItemSummary, EbayApiItemDetail

class SnapshotAdapter:
    @staticmethod
    def adapt_search_item_summary_to_snapshot(summary: EbayApiItemSummary) -> Dict[str, Any]:
        """
        Search API response -> Resolver snapshot format.
        Focuses on shippingOptions.
        """
        return {
            "item_id": summary.item_id,
            "title": summary.title,
            "price": summary.price,
            "shippingOptions": summary.shipping_options,
            "source": "api_search"
        }

    @staticmethod
    def adapt_detail_item_to_snapshot(detail: EbayApiItemDetail) -> Dict[str, Any]:
        """
        Detail API response -> Resolver snapshot format.
        Includes taxes, returnTerms, etc.
        """
        return {
            "item_id": detail.item_id,
            "title": detail.title,
            "price": detail.price,
            "shippingOptions": detail.shipping_options,
            "taxes": detail.taxes,
            "returnTerms": detail.return_terms,
            "estimatedImportCosts": detail.estimated_import_costs,
            "source": "api_detail"
        }

    @staticmethod
    def adapt_raw_dict_to_snapshot(raw_data: Dict[str, Any], level: str) -> Dict[str, Any]:
        """Directly adapt raw JSON if models are not used"""
        # Simply ensure keys exist or are mapped
        snapshot = raw_data.copy()
        snapshot["source"] = f"raw_{level}"
        return snapshot
