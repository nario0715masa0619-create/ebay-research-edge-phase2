from typing import Dict, Any
from src.ebay.api_client import EbayInventoryApiClient

class PublishExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute(self, offer_id: str) -> Dict[str, Any]:
        try:
            res = self.api_client.publish_offer(offer_id)
            return {
                "success": res.get("status_code") == 200,
                "listing_id": res.get("listingId"),
                "status": "published" if res.get("status_code") == 200 else "failed",
                "response": res
            }
        except Exception as e:
            return {
                "success": False,
                "status": "failed",
                "error": str(e)
            }
