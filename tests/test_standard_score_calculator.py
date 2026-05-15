import pytest
from dataclasses import dataclass, field
from typing import List
from src.score.calculator import calculate_standard_score
from src.score.models import (
    StandardScoreResolutionStatus,
    StandardScoreConfidence,
    StandardScoreProfile
)

@dataclass
class MockTotalCostResult:
    final_profit_after_all_costs: float = 0.0
    estimated_margin_rate: float = 0.0
    estimated_roi: float = 0.0
    total_cost_resolution_status: str = "resolved_estimated"
    total_cost_confidence: str = "medium"
    unresolved_components: List[str] = field(default_factory=list)
    fallback_components: List[str] = field(default_factory=list)
    partial_components: List[str] = field(default_factory=list)

def test_high_profit_high_confidence():
    # 1. 全 resolver が高信頼・高利益 -> Grade A
    res = MockTotalCostResult(
        final_profit_after_all_costs=60.0,
        estimated_margin_rate=0.35,
        estimated_roi=1.2,
        total_cost_resolution_status="resolved_exact",
        total_cost_confidence="high"
    )
    score_res = calculate_standard_score(res)
    assert score_res.standard_score >= 85.0
    assert score_res.score_grade == "A"
    assert "positive_profit" in score_res.reason_codes

def test_high_profit_with_fallbacks():
    # 2. 利益は高いが fallback 多数 -> stability が下がる
    res = MockTotalCostResult(
        final_profit_after_all_costs=60.0,
        estimated_margin_rate=0.35,
        estimated_roi=1.2,
        total_cost_resolution_status="fallback_default",
        total_cost_confidence="low",
        fallback_components=["shipping", "import", "selling"]
    )
    score_res = calculate_standard_score(res)
    # Stability: 100 - 3*10 = 70. Quality: 30. Confidence: 40.
    # Base score will be lower than A.
    assert score_res.standard_score < 85.0
    assert score_res.stability_score < 100.0

def test_medium_profit_high_confidence():
    # 3. 利益中程度・confidence 高い
    res = MockTotalCostResult(
        final_profit_after_all_costs=20.0,
        estimated_margin_rate=0.15,
        estimated_roi=0.4,
        total_cost_resolution_status="resolved_exact",
        total_cost_confidence="high"
    )
    score_res = calculate_standard_score(res)
    assert score_res.standard_score > 50.0
    assert score_res.score_grade in ["B", "C"]

def test_high_profit_with_unresolved():
    # 4. 利益は高いが unresolved component あり -> penalty
    res = MockTotalCostResult(
        final_profit_after_all_costs=60.0,
        unresolved_components=["payout_fee"]
    )
    score_res = calculate_standard_score(res)
    assert "contains_unresolved_components" in score_res.reason_codes
    assert score_res.risk_penalty >= 20.0

def test_negative_profit():
    # 5. 最終利益がマイナス -> score が大きく下がる
    res = MockTotalCostResult(final_profit_after_all_costs=-10.0)
    score_res = calculate_standard_score(res)
    assert score_res.standard_score < 30.0
    assert "negative_profit" in score_res.reason_codes

def test_strict_mode_unresolved():
    # 6. strict モードで unresolved total cost
    res = MockTotalCostResult(
        final_profit_after_all_costs=0.0,
        total_cost_resolution_status="unresolved"
    )
    score_res = calculate_standard_score(res, strictness="strict")
    assert score_res.standard_score == 0.0
    assert "strict_mode_blocked_scoring" in score_res.reason_codes

def test_profit_first_profile():
    # 7. profit_first profile -> 利益額の影響が強くなる
    res = MockTotalCostResult(final_profit_after_all_costs=100.0, total_cost_confidence="low")
    score_balanced = calculate_standard_score(res, scoring_profile="balanced")
    score_profit = calculate_standard_score(res, scoring_profile="profit_first")
    # In profit_first, profit weight is 0.4 vs 0.3. So score should be higher if profit is high but quality is low.
    assert score_profit.standard_score > score_balanced.standard_score

def test_safety_first_profile():
    # 8. safety_first profile -> confidence / stability の影響が強くなる
    res = MockTotalCostResult(final_profit_after_all_costs=10.0, total_cost_confidence="high")
    score_balanced = calculate_standard_score(res, scoring_profile="balanced")
    score_safety = calculate_standard_score(res, scoring_profile="safety_first")
    # In safety_first, quality weights are higher.
    assert score_safety.standard_score > score_balanced.standard_score

def test_weight_override():
    # 9. weight_override 適用
    res = MockTotalCostResult(final_profit_after_all_costs=10.0)
    # Set profit weight to 1.0 (rest 0)
    override = {
        "profit_score": 1.0, "margin_score": 0, "roi_score": 0,
        "confidence_score": 0, "stability_score": 0, "resolution_quality_score": 0
    }
    score_res = calculate_standard_score(res, weight_override=override)
    # profit=10 -> profit_score = (10/50)*100 = 20. Total score should be approx 20 (minus risk).
    assert 15.0 <= score_res.standard_score <= 25.0

def test_metadata_consistency():
    # 10. metadata consistency
    res = MockTotalCostResult(
        final_profit_after_all_costs=60.0,
        estimated_margin_rate=0.35,
        total_cost_resolution_status="resolved_exact"
    )
    score_res = calculate_standard_score(res)
    assert score_res.score_grade != ""
    assert len(score_res.reason_codes) > 0
    assert "profit_score" in score_res.applied_weight_map
