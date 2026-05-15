from typing import Dict, Any, Optional, List
from .models import (
    StandardScoreResult,
    StandardScoreResolutionStatus,
    StandardScoreConfidence,
    StandardScoreProfile
)

# Default Weights
WEIGHTS = {
    "balanced": {
        "profit_score": 0.30,
        "margin_score": 0.20,
        "roi_score": 0.15,
        "confidence_score": 0.15,
        "stability_score": 0.10,
        "resolution_quality_score": 0.10
    },
    "profit_first": {
        "profit_score": 0.40,
        "margin_score": 0.20,
        "roi_score": 0.15,
        "confidence_score": 0.10,
        "stability_score": 0.08,
        "resolution_quality_score": 0.07
    },
    "safety_first": {
        "profit_score": 0.20,
        "margin_score": 0.15,
        "roi_score": 0.10,
        "confidence_score": 0.20,
        "stability_score": 0.20,
        "resolution_quality_score": 0.15
    },
    "velocity_first": {
        "profit_score": 0.20,
        "margin_score": 0.25,
        "roi_score": 0.25,
        "confidence_score": 0.10,
        "stability_score": 0.10,
        "resolution_quality_score": 0.10
    }
}

def calculate_standard_score(
    total_cost_result,
    shipping_result=None,
    import_result=None,
    selling_fee_result=None,
    payout_fee_result=None,
    scoring_profile: str = "balanced",
    weight_override: Optional[Dict[str, float]] = None,
    negative_profit_floor: float = 0.0,
    strictness: str = "balanced"
) -> StandardScoreResult:
    result = StandardScoreResult(
        scoring_profile=scoring_profile,
        strictness=strictness,
        final_profit_after_all_costs=getattr(total_cost_result, "final_profit_after_all_costs", 0.0),
        estimated_margin_rate=getattr(total_cost_result, "estimated_margin_rate", 0.0),
        estimated_roi=getattr(total_cost_result, "estimated_roi", 0.0),
        unresolved_components=getattr(total_cost_result, "unresolved_components", []),
        fallback_components=getattr(total_cost_result, "fallback_components", []),
        partial_components=getattr(total_cost_result, "partial_components", [])
    )

    # 1. Weights determination
    weights = WEIGHTS.get(scoring_profile, WEIGHTS["balanced"]).copy()
    if weight_override:
        weights.update(weight_override)
    result.applied_weight_map = weights

    # 2. Pre-scoring validation
    total_status = getattr(total_cost_result, "total_cost_resolution_status", None)
    if strictness == "strict":
        if str(total_status).lower() == "unresolved" or not result.final_profit_after_all_costs:
            result.reason_codes.append("strict_mode_blocked_scoring")
            result.add_note("strict mode forced unresolved scoring result")
            return result

    # 3. Financial Sub-scores
    # Profit Score (0-50 USD -> 0-100 score)
    profit = result.final_profit_after_all_costs or 0.0
    if profit <= negative_profit_floor:
        result.profit_score = 0.0
        result.negative_profit_penalty = 100.0
        result.reason_codes.append("negative_profit")
    else:
        result.profit_score = min(100.0, (profit / 50.0) * 100.0)
        result.reason_codes.append("positive_profit")
        if profit >= 10.0: result.positive_factors.append("high profit amount contributes positively")

    # Margin Score (0-30% -> 0-100 score)
    margin = result.estimated_margin_rate or 0.0
    if margin <= 0:
        result.margin_score = 0.0
    else:
        result.margin_score = min(100.0, (margin / 0.30) * 100.0)
        if margin >= 0.15: 
            result.reason_codes.append("strong_margin")
            result.positive_factors.append("healthy margin rate contributes positively")

    # ROI Score (0-1.0 -> 0-100 score)
    roi = result.estimated_roi or 0.0
    if roi <= 0:
        result.roi_score = 0.0
    else:
        result.roi_score = min(100.0, (roi / 1.0) * 100.0)
        if roi >= 0.3: 
            result.reason_codes.append("strong_roi")
            result.positive_factors.append("roi is above target threshold")

    # 4. Quality Sub-scores
    # Confidence Score
    conf = getattr(total_cost_result, "total_cost_confidence", None)
    conf_str = str(conf).lower()
    if "high" in conf_str: 
        result.confidence_score = 100.0
        result.confidence = StandardScoreConfidence.HIGH
        result.reason_codes.append("high_confidence_total_cost")
    elif "medium" in conf_str: 
        result.confidence_score = 70.0
        result.confidence = StandardScoreConfidence.MEDIUM
    elif "low" in conf_str: 
        result.confidence_score = 40.0
        result.confidence = StandardScoreConfidence.LOW
    else: 
        result.confidence_score = 0.0
        result.confidence = StandardScoreConfidence.NONE

    # Stability Score (100 - unresolved*35 - partial*15 - fallback*10)
    stability = 100.0
    stability -= len(result.unresolved_components) * 35.0
    stability -= len(result.partial_components) * 15.0
    stability -= len(result.fallback_components) * 10.0
    result.stability_score = max(0.0, stability)
    if stability < 100:
        result.negative_factors.append("fallback/partial components reduced stability score")
        if result.unresolved_components:
            result.reason_codes.append("contains_unresolved_components")
            result.negative_factors.append("unresolved components strongly reduced score")
        if result.fallback_components:
            result.reason_codes.append("contains_fallback_components")
        if result.partial_components:
            result.reason_codes.append("contains_partial_components")

    # Resolution Quality Score
    status_str = str(total_status).lower()
    if "resolved_exact" in status_str: 
        result.resolution_quality_score = 100.0
        result.reason_codes.append("all_major_components_resolved")
    elif "resolved_estimated" in status_str: result.resolution_quality_score = 80.0
    elif "resolved_partial" in status_str: result.resolution_quality_score = 50.0
    elif "fallback" in status_str: result.resolution_quality_score = 30.0
    else: result.resolution_quality_score = 0.0

    # 5. Penalties and Base Score
    base_score = (
        result.profit_score * weights["profit_score"] +
        result.margin_score * weights["margin_score"] +
        result.roi_score * weights["roi_score"] +
        result.confidence_score * weights["confidence_score"] +
        result.stability_score * weights["stability_score"] +
        result.resolution_quality_score * weights["resolution_quality_score"]
    )

    # Risk Penalty
    risk = 0.0
    if len(result.unresolved_components) > 0: risk += 20.0
    if len(result.fallback_components) > 1: risk += 10.0
    if profit < 0: risk += 50.0
    result.risk_penalty = risk

    final_score = base_score - result.risk_penalty
    result.standard_score = max(0.0, min(100.0, final_score))

    # 6. Finalization
    result.score_grade = _determine_grade(result.standard_score)
    result.resolution_status = _determine_status(result)
    
    return result

def _determine_grade(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "E"

def _determine_status(result: StandardScoreResult) -> StandardScoreResolutionStatus:
    if result.unresolved_components: return StandardScoreResolutionStatus.UNRESOLVED
    if result.partial_components or result.fallback_components: return StandardScoreResolutionStatus.PARTIAL
    return StandardScoreResolutionStatus.RESOLVED
