from typing import Dict, Any, Optional
from src.ebay.api_client import EbayInventoryApiClient

class InventoryRecoveryExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute_price_qty_sync(self, sku: str, offer_id: str, price: Optional[float], quantity: Optional[int], dry_run: bool = False) -> Dict[str, Any]:
        payload = {
            "requests": [
                {
                    "offers": [
                        {
                            "offerId": offer_id,
                            "price": {"value": str(price), "currency": "USD"} if price is not None else None,
                            "availableQuantity": quantity if quantity is not None else None
                        }
                    ],
                    "shipToLocationAvailability": {
                        "quantity": quantity
                    } if quantity is not None else None
                }
            ]
        }
        # Filter None
        if price is None:
            del payload["requests"][0]["offers"][0]["price"]
        if quantity is None:
            del payload["requests"][0]["offers"][0]["availableQuantity"]
            del payload["requests"][0]["shipToLocationAvailability"]
            
        res = self.api_client.bulk_update_price_quantity(payload, dry_run=dry_run)
        # eBay Bulk API returns list of responses. Check if first one is 200/204
        if "responses" in res and len(res["responses"]) > 0:
            first_res = res["responses"][0]
            status = first_res.get("statusCode")
            if status in [200, 204]:
                res["success"] = True
        return res
