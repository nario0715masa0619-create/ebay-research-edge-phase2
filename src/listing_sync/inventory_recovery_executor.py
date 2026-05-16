from typing import Dict, Any, Optional
from src.ebay.api_client import EbayInventoryApiClient

class InventoryRecoveryExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute_price_qty_sync(self, sku: str, offer_id: str, price: Optional[float], quantity: Optional[int], dry_run: bool = False) -> Dict[str, Any]:
        return self.api_client.bulk_update_price_quantity(sku, offer_id, price, quantity, dry_run=dry_run)
