from typing import Dict, Any
from src.ebay.api_client import EbayInventoryApiClient

class OfferExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        try:
            res = self.api_client.create_offer(draft)
            return {
                "success": res.get("status_code") == 201,
                "offer_id": res.get("offerId"),
                "status": "created" if res.get("status_code") == 201 else "failed",
                "response": res
            }
        except Exception as e:
            return {
                "success": False,
                "status": "failed",
                "error": str(e)
            }
