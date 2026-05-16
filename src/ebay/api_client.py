from typing import Dict, Any, Optional, List
from .base_client import EbayBaseApiClient

class EbayInventoryApiClient(EbayBaseApiClient):
    """
    Client for eBay Sell Inventory API using Auth and Rate Limit Layer.
    """
    def __init__(self, auth_components: Dict[str, Any]):
        super().__init__(auth_components)

    def create_or_replace_inventory_item(self, sku: str, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.create_or_replace_inventory_item",
            http_method="PUT",
            path=f"/sell/inventory/v1/inventory_item/{sku}",
            payload=payload,
            dry_run=dry_run
        )

    def create_offer(self, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.create_offer",
            http_method="POST",
            path="/sell/inventory/v1/offer",
            payload=payload,
            dry_run=dry_run
        )

    def publish_offer(self, offer_id: str, dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.publish_offer",
            http_method="POST",
            path=f"/sell/inventory/v1/offer/{offer_id}/publish",
            dry_run=dry_run
        )

    def get_offer(self, offer_id: str) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.get_offer",
            http_method="GET",
            path=f"/sell/inventory/v1/offer/{offer_id}"
        )

    def withdraw_offer(self, offer_id: str, dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.withdraw_offer",
            http_method="POST",
            path=f"/sell/inventory/v1/offer/{offer_id}/withdraw",
            dry_run=dry_run
        )

    def bulk_update_price_quantity(self, sku: str, offer_id: str, price: Optional[float], quantity: Optional[int], dry_run: bool = False) -> Dict[str, Any]:
        # Note: In real API, this might be a bulk endpoint, but here we wrap for specific item
        payload = {
            "requests": [
                {
                    "offerId": offer_id,
                    "price": {"value": str(price), "currency": "USD"} if price else None,
                    "availableQuantity": quantity
                }
            ]
        }
        return self.execute_with_auth(
            operation_key="inventory.bulk_update_price_quantity",
            http_method="POST",
            path="/sell/inventory/v1/bulk_update_price_quantity",
            payload=payload,
            dry_run=dry_run
        )

    def get_offers(self, sku: str) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.get_offers",
            http_method="GET",
            path="/sell/inventory/v1/offer",
            params={"sku": sku}
        )

    def get_inventory_item(self, sku: str) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.get_inventory_item",
            http_method="GET",
            path=f"/sell/inventory/v1/inventory_item/{sku}"
        )

    def update_offer(self, offer_id: str, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.update_offer",
            http_method="PUT",
            path=f"/sell/inventory/v1/offer/{offer_id}",
            payload=payload,
            dry_run=dry_run
        )

    def withdraw_offer(self, offer_id: str, dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.withdraw_offer",
            http_method="POST",
            path=f"/sell/inventory/v1/offer/{offer_id}/withdraw",
            dry_run=dry_run
        )

    def bulk_update_price_quantity(self, payload: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        return self.execute_with_auth(
            operation_key="inventory.bulk_update_price_quantity",
            http_method="POST",
            path="/sell/inventory/v1/bulk_update_price_quantity",
            payload=payload,
            dry_run=dry_run
        )
