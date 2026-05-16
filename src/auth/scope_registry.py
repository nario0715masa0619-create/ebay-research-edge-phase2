from typing import Dict, List

class OAuthScopeRegistry:
    def __init__(self):
        # Operation Key to Scopes mapping
        self._registry: Dict[str, List[str]] = {
            # Sell Inventory API
            "inventory.create_or_replace_inventory_item": ["https://api.ebay.com/oauth/api_scope/sell.inventory"],
            "inventory.get_inventory_item": ["https://api.ebay.com/oauth/api_scope/sell.inventory.readonly"],
            "inventory.create_offer": ["https://api.ebay.com/oauth/api_scope/sell.inventory"],
            "inventory.publish_offer": ["https://api.ebay.com/oauth/api_scope/sell.inventory"],
            "inventory.withdraw_offer": ["https://api.ebay.com/oauth/api_scope/sell.inventory"],
            "inventory.get_offer": ["https://api.ebay.com/oauth/api_scope/sell.inventory.readonly"],
            "inventory.bulk_update_price_quantity": ["https://api.ebay.com/oauth/api_scope/sell.inventory"],
            
            # Sell Account API
            "account.get_policies": ["https://api.ebay.com/oauth/api_scope/sell.account.readonly"],
            
            # Commerce Taxonomy API
            "taxonomy.get_category_suggestions": ["https://api.ebay.com/oauth/api_scope/commerce.taxonomy.readonly"],
            
            # Developer Analytics API
            "analytics.get_rate_limits": ["https://api.ebay.com/oauth/api_scope/developer.analytics.readonly"],
        }

    def get_required_scopes(self, operation_key: str) -> List[str]:
        if operation_key not in self._registry:
            raise ValueError(f"Operation key '{operation_key}' is not registered in OAuthScopeRegistry")
        return self._registry.get(operation_key, [])

    def register(self, operation_key: str, scopes: List[str]):
        self._registry[operation_key] = scopes
