from typing import List, Dict, Any
from .models import MarketListingSnapshot

class SearchResultNormalizer:
    """
    Normalizes a provider's raw item dictionary into a common MarketListingSnapshot.
    """
    
    def normalize_items(self, raw_items: List[Dict[str, Any]]) -> List[MarketListingSnapshot]:
        snapshots = []
        for item in raw_items:
            snapshot = self.normalize_single(item)
            if snapshot:
                snapshots.append(snapshot)
        return snapshots
        
    def normalize_single(self, item: Dict[str, Any]) -> MarketListingSnapshot:
        """
        Parses fields from a generic 'findCompletedItems' shape.
        """
        try:
            item_id = item.get("itemId", [""])[0] if isinstance(item.get("itemId"), list) else item.get("itemId", "")
            title = item.get("title", [""])[0] if isinstance(item.get("title"), list) else item.get("title", "")
            
            # Extract price
            selling_status = item.get("sellingStatus", [{}])[0] if isinstance(item.get("sellingStatus"), list) else item.get("sellingStatus", {})
            current_price = selling_status.get("currentPrice", [{}])[0] if isinstance(selling_status.get("currentPrice"), list) else selling_status.get("currentPrice", {})
            
            # Sometimes rapidapi places price at the root depending on their adapter layer
            if not current_price and "price" in item:
                current_price = item["price"]

            price_val = float(current_price.get("__value__") or current_price.get("value") or 0.0)
            currency = str(current_price.get("@currencyId") or current_price.get("currency") or "USD")
            
            # Selling state
            selling_state_val = selling_status.get("sellingState", [""])[0] if isinstance(selling_status.get("sellingState"), list) else selling_status.get("sellingState", "")
            # We treat EndedWithSales or anything successfully parsed as sold (since this is completed api)
            # Actually, findCompletedItems returns both sold and unsold. We only want sold if evaluating price.
            # Usually "EndedWithSales" or "EndedWithoutSales"
            is_sold = (selling_state_val == "EndedWithSales")
            
            # If we don't have sellingStatus (e.g. from a different provider shape), assume true if price > 0
            if not selling_state_val and price_val > 0.0:
                is_sold = True

            # Extract shipping
            shipping_info = item.get("shippingInfo", [{}])[0] if isinstance(item.get("shippingInfo"), list) else item.get("shippingInfo", {})
            shipping_cost_obj = shipping_info.get("shippingServiceCost", [{}])[0] if isinstance(shipping_info.get("shippingServiceCost"), list) else shipping_info.get("shippingServiceCost", {})
            shipping_price = float(shipping_cost_obj.get("__value__") or shipping_cost_obj.get("value") or 0.0)
            
            # Condition
            raw_condition = item.get("condition", {})
            if isinstance(raw_condition, list):
                condition_info = raw_condition[0] if raw_condition else {}
            else:
                condition_info = raw_condition

            condition_display = ""
            if isinstance(condition_info, dict):
                cd = condition_info.get("conditionDisplayName", [""])
                condition_display = cd[0] if isinstance(cd, list) and cd else str(cd)
            elif isinstance(condition_info, str):
                condition_display = condition_info
            
            if not condition_display and isinstance(item.get("condition"), str):
                condition_display = item["condition"]
            
            # Categories
            primary_cat = item.get("primaryCategory", [{}])[0] if isinstance(item.get("primaryCategory"), list) else item.get("primaryCategory", {})
            cat_name = primary_cat.get("categoryName", [""])[0] if isinstance(primary_cat.get("categoryName"), list) else primary_cat.get("categoryName", "")
            # Or root categories array fallback
            if not cat_name and "categories" in item:
                cat_name = str(item["categories"])
                
            # URLs
            listing_url = item.get("viewItemURL", [""])[0] if isinstance(item.get("viewItemURL"), list) else item.get("viewItemURL", "")
            if not listing_url:
                listing_url = item.get("itemWebUrl", "")
                
            image_url = item.get("galleryURL", [""])[0] if isinstance(item.get("galleryURL"), list) else item.get("galleryURL", "")

            return MarketListingSnapshot(
                listing_id=str(item_id),
                title=str(title),
                price=price_val,
                currency=currency,
                shipping_price=shipping_price,
                is_sold=is_sold,
                condition=condition_display,
                category_path=cat_name,
                listing_url=listing_url,
                image_url=image_url,
                raw_payload=item
            )
        except Exception:
            # If parsing completely fails for a single item, skip it to avoid crashing the whole batch
            return None
