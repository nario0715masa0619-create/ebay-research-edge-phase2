from typing import Dict, Any, Optional
from src.ebay.api_client import EbayInventoryApiClient

class EbayStateFetcher:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def fetch_remote_state(self, sku: str, offer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches eBay state using offer_id or sku.
        """
        results = {
            "offer": None,
            "inventory_item": None,
            "all_offers": [],
            "errors": []
        }

        # 1. Try getOffer if offer_id is provided
        if offer_id:
            try:
                offer_res = self.api_client.get_offer(offer_id)
                if "error" not in offer_res:
                    results["offer"] = offer_res
                else:
                    results["errors"].append(f"get_offer failed: {offer_res.get('message')}")
            except Exception as e:
                results["errors"].append(f"get_offer exception: {str(e)}")

        # 2. Try getOffers(sku) to find offers or orphaned offers
        try:
            offers_res = self.api_client.get_offers(sku)
            if "error" not in offers_res:
                results["all_offers"] = offers_res.get("offers", [])
                # If we don't have an offer yet, pick the first one matching sku
                if not results["offer"] and results["all_offers"]:
                    results["offer"] = results["all_offers"][0]
            else:
                results["errors"].append(f"get_offers failed: {offers_res.get('message')}")
        except Exception as e:
            results["errors"].append(f"get_offers exception: {str(e)}")

        # 3. Try getInventoryItem(sku)
        try:
            inv_res = self.api_client.get_inventory_item(sku)
            if "error" not in inv_res:
                results["inventory_item"] = inv_res
            else:
                results["errors"].append(f"get_inventory_item failed: {inv_res.get('message')}")
        except Exception as e:
            results["errors"].append(f"get_inventory_item exception: {str(e)}")

        return results
