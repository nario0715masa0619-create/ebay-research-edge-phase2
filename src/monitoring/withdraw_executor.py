from typing import Dict, Any
from src.ebay.api_client import EbayInventoryApiClient

class WithdrawExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute(self, offer_id: str) -> Dict[str, Any]:
        try:
            res = self.api_client.withdraw_offer(offer_id)
            return {
                "withdraw_status": "withdrawn" if res.get("status_code") == 200 else "failed",
                "withdrawn_listing_id": res.get("listingId"),
                "response_payload": res,
                "success": res.get("status_code") == 200
            }
        except Exception as e:
            return {
                "withdraw_status": "failed",
                "error_summary": str(e),
                "success": False
            }
