from typing import Dict, Any
from src.ebay.api_client import EbayInventoryApiClient

class InventoryItemExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute(self, sku: str, draft: Dict[str, Any]) -> Dict[str, Any]:
        try:
            res = self.api_client.create_or_replace_inventory_item(sku, draft)
            return {
                "success": res.get("status_code") in [201, 204],
                "status": "created" if res.get("status_code") == 201 else "updated",
                "response": res
            }
        except Exception as e:
            return {
                "success": False,
                "status": "failed",
                "error": str(e)
            }
