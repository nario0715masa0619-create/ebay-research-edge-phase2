import pytest
from src.market_eval.config import MarketEvalSettings
from src.market_eval.market_evaluation_service import MarketEvaluationService
from src.market_eval.mock_market_search_gateway import MockMarketSearchGateway

def test_market_evaluation_service_success():
    settings = MarketEvalSettings(market_data_provider="mock", outlier_trim_enabled=False, min_comparable_count=2)
    gateway = MockMarketSearchGateway(settings)
    service = MarketEvaluationService(settings, gateway)
    
    # 疑似的な候補データ
    candidate = {
        "candidate_id": "cand_001",
        "canonical_title": "Sony PS5 Base Edition",
        "canonical_brand": "Sony",
        "canonical_model": "PS5",
        "canonical_condition_family": "used",
        "category_candidates_json": ["Test Category"]
    }
    
    result, evidence = service.evaluate_candidate(candidate)
    
    # Assertions
    assert result.candidate_id == "cand_001"
    assert result.evaluation_status == "success"
    # Mock returns 2 items that match our condition (used_excellent, used_good).
    assert result.comparable_count == 2
    assert result.price_low == 150.0
    assert result.price_high == 165.0
    assert result.market_confidence >= 0.5  # Base confidence without severe penalty
    assert result.review_required is False
    
    assert evidence.candidate_id == "cand_001"
    assert len(evidence.comparable_listing_ids) == 2
    assert "mock" in evidence.provider_name

def test_market_evaluation_service_error():
    settings = MarketEvalSettings(market_data_provider="mock")
    gateway = MockMarketSearchGateway(settings)
    service = MarketEvaluationService(settings, gateway)
    
    candidate = {
        "candidate_id": "cand_err",
        "canonical_title": "error item",  # This triggers mock provider error
        "canonical_brand": "Sony",
        "canonical_condition_family": "used",
    }
    
    result, evidence = service.evaluate_candidate(candidate)
    
    assert result.evaluation_status == "error"
    assert result.review_required is True
    assert "provider_error" in result.unsafe_reasons[0]
    assert result.comparable_count == 0
    assert result.price_median is None
