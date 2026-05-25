import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from src.listing_execution.models.ebay_response import EBayResponse

class RateLimitError(Exception):
    """Raised when eBay API rate limits are exceeded."""
    pass

class InvalidRequestError(Exception):
    """Raised when the request to eBay API is invalid."""
    pass

class TimeoutError(Exception):
    """Raised when eBay API request times out."""
    pass

class EBayApiGateway:
    """Mock implementation of the eBay API gateway for Wave 1."""
    
    def __init__(self, simulate_network_delay: bool = False):
        self.simulate_network_delay = simulate_network_delay
        
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validates that the provided credentials are well-formed."""
        if not credentials:
            return False
        if not credentials.get("auth_token"):
            return False
        return True
        
    def create_or_replace_inventory_item(self, sku: str, payload: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Simulates creating an inventory item."""
        if not self.validate_credentials(credentials):
            raise InvalidRequestError("Invalid credentials provided.")
            
        if self.simulate_network_delay:
            time.sleep(0.1)
            
        # Simulate errors based on SKU
        if sku.endswith("_timeout"):
            raise TimeoutError("Connection to eBay API timed out.")
        if sku.endswith("_ratelimit"):
            raise RateLimitError("eBay API rate limit exceeded.")
        if sku.endswith("_invalid"):
            raise InvalidRequestError("Invalid payload provided to eBay API.")
            
        return True
        
    def create_offer(self, sku: str, marketplace_id: str, credentials: Dict[str, Any]) -> str:
        """Simulates creating an offer and returns an offer ID."""
        if not self.validate_credentials(credentials):
            raise InvalidRequestError("Invalid credentials provided.")
            
        # Simulate errors based on SKU
        if sku.endswith("_timeout"):
            raise TimeoutError("Connection to eBay API timed out.")
            
        return f"offer_{sku}"
        
    def publish_offer(self, offer_id: str, credentials: Dict[str, Any]) -> EBayResponse:
        """Simulates publishing an offer and returns an EBayResponse."""
        if not self.validate_credentials(credentials):
            raise InvalidRequestError("Invalid credentials provided.")
            
        sku = offer_id.replace("offer_", "")
        
        # Simulate errors based on SKU
        if sku.endswith("_publish_timeout"):
            raise TimeoutError("Connection to eBay API timed out during publish.")
            
        return EBayResponse(
            listing_id=f"lst_{sku}",
            sku=sku,
            status="published",
            item_id=f"item_{sku}",
            timestamp=datetime.now(timezone.utc)
        )
