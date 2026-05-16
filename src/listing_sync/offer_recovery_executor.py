from typing import Dict, Any, Optional
from src.ebay.api_client import EbayInventoryApiClient

class OfferRecoveryExecutor:
    def __init__(self, api_client: EbayInventoryApiClient):
        self.api_client = api_client

    def execute_withdraw(self, offer_id: str, dry_run: bool = False) -> Dict[str, Any]:
        return self.api_client.withdraw_offer(offer_id, dry_run=dry_run)

    def execute_update_status(self, offer_id: str, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        return self.api_client.update_offer(offer_id, payload, dry_run=dry_run)
