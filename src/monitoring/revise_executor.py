from typing import Dict, Any, Optional
from src.ebay.api_client import EbayInventoryApiClient

class PriceQuantityReviseExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute(self, sku: str, offer_id: str, price: Optional[float], quantity: Optional[int]) -> Dict[str, Any]:
        try:
            res = self.api_client.bulk_update_price_quantity(sku, offer_id, price, quantity)
            return {
                "revise_status": "updated" if res.get("status_code") == 200 else "failed",
                "updated_price": price,
                "updated_quantity": quantity,
                "response_payload": res,
                "success": res.get("status_code") == 200
            }
        except Exception as e:
            return {
                "revise_status": "failed",
                "error_summary": str(e),
                "success": False
            }
