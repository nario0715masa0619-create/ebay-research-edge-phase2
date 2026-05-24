import pytest
from src.profitability.config import ProfitabilitySettings
from src.profitability.models import ProfitabilityInput, DecisionStatus, ScoringStatus, SellerPolicyContext
from src.profitability.scoring_service import ProfitabilityScoringService

def test_profitability_launch_now():
    settings = ProfitabilitySettings(profitability_enabled=True)
    service = ProfitabilityScoringService(settings)
    
    # 高利益で比較件数も多く、リスク要因がない理想的なケース
    input_data = ProfitabilityInput(
        candidate_id="cand_1",
        seller_account_id="seller_1",
        environment="test",
        source_price=5000.0,
        source_shipping_cost=500.0,
        expected_sale_price_base=15000.0,
        market_confidence=0.85,
        comparable_count=10,
        competition_proxy="low",
        seller_policy_context=SellerPolicyContext(
            marketplace_fee_rate=0.10,
            fixed_marketplace_fee=0.0,
            payment_fee_rate=0.04,
            fixed_payment_fee=0.0,
            estimated_outbound_shipping=1000.0,
            packaging_cost_estimate=200.0,
            handling_cost_estimate=300.0
        )
    )
    
    result = service.evaluate_profitability(input_data)
    
    assert result.scoring_status == ScoringStatus.SUCCESS
    assert result.decision_status == DecisionStatus.LAUNCH_NOW
    assert result.expected_net_profit > 3000.0
    assert result.confidence_adjusted_profit > 3000.0
    assert result.expected_margin >= 0.18

def test_profitability_input_incomplete():
    settings = ProfitabilitySettings(profitability_enabled=True)
    service = ProfitabilityScoringService(settings)
    
    # 必須入力 (expected_sale_price_base) が欠損しているケース
    input_data = ProfitabilityInput(
        candidate_id="cand_2",
        seller_account_id="seller_1",
        environment="test",
        source_price=5000.0,
        expected_sale_price_base=None
    )
    
    result = service.evaluate_profitability(input_data)
    
    assert result.scoring_status == ScoringStatus.INPUT_INCOMPLETE
    assert result.decision_status == DecisionStatus.REJECT
    assert "input_validation_failed" in result.unsafe_reasons

def test_profitability_review_required_due_to_ambiguity():
    settings = ProfitabilitySettings(profitability_enabled=True)
    service = ProfitabilityScoringService(settings)
    
    input_data = ProfitabilityInput(
        candidate_id="cand_3",
        seller_account_id="seller_1",
        environment="test",
        source_price=5000.0,
        source_shipping_cost=0.0,
        expected_sale_price_base=15000.0,
        market_confidence=0.85,
        comparable_count=10,
        ambiguity_flags=["suspicious_image"], # Ambiguity
        review_required=True # Forced review
    )
    
    result = service.evaluate_profitability(input_data)
    
    assert result.scoring_status == ScoringStatus.SUCCESS
    assert result.decision_status == DecisionStatus.REVIEW_REQUIRED
    assert result.review_required is True

def test_profitability_reject_due_to_low_confidence():
    settings = ProfitabilitySettings(profitability_enabled=True)
    service = ProfitabilityScoringService(settings)
    
    input_data = ProfitabilityInput(
        candidate_id="cand_4",
        seller_account_id="seller_1",
        environment="test",
        source_price=5000.0,
        expected_sale_price_base=20000.0, # High profit visually
        market_confidence=0.30, # Too low confidence
        comparable_count=1
    )
    
    result = service.evaluate_profitability(input_data)
    
    assert result.scoring_status == ScoringStatus.SUCCESS
    assert result.decision_status == DecisionStatus.REJECT
