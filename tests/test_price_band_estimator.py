import pytest
from src.market_eval.models import MarketListingSnapshot
from src.market_eval.price_band_estimator import PriceBandEstimator

def test_price_band_estimator():
    snaps = [
        MarketListingSnapshot(str(i), "Item", float(i * 10), "USD", 5.0, True)
        for i in range(1, 12) # Prices (total): 15, 25, 35, 45, 55, 65, 75, 85, 95, 105, 115
    ]
    # Total prices: 11 items.
    # Outlier trim enabled: trims top 10% (1) and bottom 10% (1) -> min 25, max 105, median 65
    
    estimator = PriceBandEstimator(trim_enabled=True)
    p_low, p_med, p_high = estimator.estimate(snaps)
    
    assert p_low == 25.0
    assert p_med == 65.0
    assert p_high == 105.0

def test_price_band_estimator_no_trim():
    snaps = [
        MarketListingSnapshot("1", "Item", 10.0, "USD", 0.0, True),
        MarketListingSnapshot("2", "Item", 20.0, "USD", 0.0, True),
        MarketListingSnapshot("3", "Item", 30.0, "USD", 0.0, True),
    ]
    
    estimator = PriceBandEstimator(trim_enabled=False)
    p_low, p_med, p_high = estimator.estimate(snaps)
    
    assert p_low == 10.0
    assert p_med == 20.0
    assert p_high == 30.0
