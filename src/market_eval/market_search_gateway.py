from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from .models import MarketSearchRequest

class GatewayResponse:
    def __init__(self, raw_items: List[Dict[str, Any]], provider_name: str, unsafe_reasons: List[str] = None):
        self.raw_items = raw_items
        self.provider_name = provider_name
        self.unsafe_reasons = unsafe_reasons or []

class MarketSearchGateway(ABC):
    """
    Abstract interface for executing a market search against a provider.
    """
    @abstractmethod
    def search_completed_items(self, request: MarketSearchRequest) -> GatewayResponse:
        """
        Executes a search for completed/sold items based on the provided request.
        
        Returns a GatewayResponse containing raw un-normalized items and any unsafe reasons (like timeouts).
        """
        pass
