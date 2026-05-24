from typing import List, Dict, Any
from .market_search_gateway import MarketSearchGateway, GatewayResponse
from .models import MarketSearchRequest
from .config import MarketEvalSettings

class MockMarketSearchGateway(MarketSearchGateway):
    """
    Mock gateway for CI, local development, and tests.
    Uses hardcoded fixtures to simulate RapidAPI findCompletedItems response without network calls.
    """
    def __init__(self, settings: MarketEvalSettings):
        self.settings = settings
        
    def search_completed_items(self, request: MarketSearchRequest) -> GatewayResponse:
        # Simple fixture matching based on query keywords
        query = request.query.lower()
        
        unsafe_reasons = []
        raw_items = []
        
        if "error" in query:
            unsafe_reasons.append("provider_error: Mocked provider error")
        elif "timeout" in query:
            unsafe_reasons.append("provider_timeout: Mocked timeout")
        elif "empty" in query:
            # Returns empty raw_items
            pass
        else:
            # Default success mock
            # In a real fixture setup, you might read JSON files. Here we provide a minimal standard response.
            raw_items = [
                {
                    "itemId": "1001",
                    "title": f"Sold {request.query} Example",
                    "price": {"value": "150.0", "currency": "USD"},
                    "shippingOptions": [{"shippingCost": {"value": "10.0", "currency": "USD"}}],
                    "buyingOptions": ["FIXED_PRICE"],
                    "condition": "USED_EXCELLENT",
                    "categories": [{"categoryId": "123", "categoryName": "Test Category"}],
                    "itemWebUrl": "https://ebay.com/itm/1001"
                },
                {
                    "itemId": "1002",
                    "title": f"Sold {request.query} with box",
                    "price": {"value": "165.0", "currency": "USD"},
                    "shippingOptions": [],
                    "condition": "USED_GOOD",
                    "categories": [{"categoryId": "123", "categoryName": "Test Category"}],
                    "itemWebUrl": "https://ebay.com/itm/1002"
                }
            ]
            
        return GatewayResponse(raw_items=raw_items, provider_name="mock", unsafe_reasons=unsafe_reasons)
