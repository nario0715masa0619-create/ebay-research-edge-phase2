import pytest
from src.market_eval.models import MarketSearchSeed
from src.market_eval.market_search_request_builder import MarketSearchRequestBuilder

def test_builder_gtin_priority():
    seed = MarketSearchSeed(
        candidate_id="c1",
        keyword_query="Title fallback",
        brand="Sony",
        mpn="PS5",
        gtins=["1234567890123"]
    )
    builder = MarketSearchRequestBuilder()
    req, evidence = builder.build(seed)
    
    assert req.query == "1234567890123"
    assert "Seed strategy: GTIN (1234567890123)" in evidence

def test_builder_brand_mpn_fallback():
    seed = MarketSearchSeed(
        candidate_id="c2",
        keyword_query="Title fallback",
        brand="Sony",
        mpn="PS5",
        gtins=[]
    )
    builder = MarketSearchRequestBuilder()
    req, evidence = builder.build(seed)
    
    assert req.query == "Sony PS5"
    assert "Seed strategy: Brand + MPN (Sony PS5)" in evidence

def test_builder_title_fallback_with_warnings():
    seed = MarketSearchSeed(
        candidate_id="c3",
        keyword_query="Sony Console",
        risk_flags=["variation_conflict"]
    )
    builder = MarketSearchRequestBuilder()
    req, evidence = builder.build(seed)
    
    assert req.query == "Sony Console"
    assert "Seed strategy: Title Fallback (Sony Console)" in evidence
    assert any("high ambiguity risks" in e for e in evidence)

def test_builder_exclusions():
    seed = MarketSearchSeed(
        candidate_id="c4",
        keyword_query="Sony PS5",
        brand="Sony",
        model="PS5",
        excluded_keywords=["box", "only", "broken"]
    )
    builder = MarketSearchRequestBuilder()
    req, evidence = builder.build(seed)
    
    # Should be "Sony PS5 -box -only -broken"
    assert req.query == "Sony PS5 -box -only -broken"
    assert req.excluded_keywords == ["box", "only", "broken"]
