from typing import List, Tuple, Optional
import statistics
from .models import MarketListingSnapshot

class PriceBandEstimator:
    """
    Estimates the price band (low, median, high) from a list of comparable snapshots.
    Removes outliers (top/bottom X%) to provide a robust band.
    """
    def __init__(self, trim_enabled: bool = True):
        self.trim_enabled = trim_enabled
        
    def estimate(self, comparables: List[MarketListingSnapshot]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if not comparables:
            return None, None, None
            
        # We use price + shipping_price as total
        prices = [snap.price + snap.shipping_price for snap in comparables if snap.is_sold and snap.price > 0]
        
        if not prices:
            return None, None, None
            
        prices.sort()
        
        if len(prices) < 3 or not self.trim_enabled:
            return prices[0], statistics.median(prices), prices[-1]
            
        # Remove top 10% and bottom 10% for outlier trim (if enough data)
        if len(prices) >= 5:
            trim_count = max(1, int(len(prices) * 0.1))
            trimmed_prices = prices[trim_count:-trim_count]
            if trimmed_prices:
                prices = trimmed_prices
                
        return min(prices), statistics.median(prices), max(prices)
