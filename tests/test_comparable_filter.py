import pytest
from src.market_eval.models import MarketSearchSeed, MarketListingSnapshot
from src.market_eval.comparable_filter import ComparableFilter

def test_comparable_filter_excludes_mismatches():
    seed = MarketSearchSeed(
        candidate_id="c1",
        keyword_query="Sony PS5",
        brand="Sony",
        model="PS5",
        condition_family="new",
        category_candidates=["Video Game Consoles"]
    )
    
    # 1. Good Match
    snap1 = MarketListingSnapshot("1", "Sony PS5 New in box", 500, "USD", 0, True, "New", "Video Game Consoles")
    # 2. Condition Mismatch (Used in New search)
    snap2 = MarketListingSnapshot("2", "Sony PS5 Used broken", 100, "USD", 0, True, "For parts or not working", "Video Game Consoles")
    # 3. Category Mismatch
    snap3 = MarketListingSnapshot("3", "Sony PS5 empty box only", 20, "USD", 0, True, "New", "Video Game Boxes")
    # 4. Capacity Mismatch (Variation proxy)
    snap4 = MarketListingSnapshot("4", "Sony PS5 1TB", 550, "USD", 0, True, "New", "Video Game Consoles")
    seed_cap = MarketSearchSeed(
        candidate_id="c1",
        keyword_query="Sony PS5 256GB",
        brand="Sony",
        condition_family="new"
    )
    
    filter = ComparableFilter()
    evals = filter.filter_comparables(seed, [snap1, snap2, snap3])
    
    assert evals[0].included is True
    assert evals[1].included is False
    assert evals[1].exclusion_reason == "condition_mismatch"
    assert evals[2].included is False
    assert "bundle_conflict" in evals[2].exclusion_reason
    
    # Check capacity mismatch
    evals2 = filter.filter_comparables(seed_cap, [snap4])
    assert evals2[0].included is False
    assert "variation_conflict" in evals2[0].exclusion_reason
