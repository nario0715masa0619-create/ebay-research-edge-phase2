from typing import Dict, Any, Optional

class EbayInventoryApiClient:
    """
    Mock client for eBay Sell Inventory API.
    """
    def __init__(self, credentials: Dict[str, str] = None):
        self.credentials = credentials or {}

    def create_or_replace_inventory_item(self, sku: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Mock successful response
        return {
            "status_code": 204,
            "sku": sku
        }

    def create_offer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Mock successful response
        return {
            "status_code": 201,
            "offerId": f"OFFER-{payload.get('sku', 'UNKNOWN')}"
        }

    def publish_offer(self, offer_id: str) -> Dict[str, Any]:
        # Mock successful response
        return {
            "status_code": 200,
            "listingId": f"LISTING-{offer_id}"
        }

    def get_offer(self, offer_id: str) -> Dict[str, Any]:
        return {
            "status_code": 200,
            "offerId": offer_id,
            "status": "PUBLISHED"
        }

    def withdraw_offer(self, offer_id: str) -> Dict[str, Any]:
        return {
            "status_code": 200,
            "listingId": f"WITHDRAWN-{offer_id}"
        }
