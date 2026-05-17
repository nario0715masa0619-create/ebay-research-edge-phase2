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

    def bulk_update_price_quantity(self, *args, **kwargs) -> Dict[str, Any]:
        if args and isinstance(args[0], dict):
            payload = args[0]
            dry_run = args[1] if len(args) > 1 else kwargs.get("dry_run", False)
        elif "payload" in kwargs:
            payload = kwargs["payload"]
            dry_run = kwargs.get("dry_run", False)
        else:
            sku = args[0] if len(args) > 0 else kwargs.get("sku")
            offer_id = args[1] if len(args) > 1 else kwargs.get("offer_id")
            price = args[2] if len(args) > 2 else kwargs.get("price")
            quantity = args[3] if len(args) > 3 else kwargs.get("quantity")
            dry_run = args[4] if len(args) > 4 else kwargs.get("dry_run", False)
            
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

    # Duplicate method bulk_update_price_quantity removed; unified implementation is above.
