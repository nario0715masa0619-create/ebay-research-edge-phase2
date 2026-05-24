import uuid
from typing import List

from src.profitability.models import (
    ProfitabilityInput, ProfitabilityResult, ProfitabilityComponentBreakdown, 
    ScoringStatus, DecisionStatus
)
from src.profitability.config import ProfitabilitySettings
from src.profitability.cost_estimator import CostEstimator
from src.profitability.risk_penalty import RiskPenaltyEngine
from src.profitability.confidence_adjuster import ConfidenceAdjuster
from src.profitability.decision_engine import DecisionEngine

class ProfitabilityScoringService:
    def __init__(
        self,
        settings: ProfitabilitySettings,
        cost_estimator: CostEstimator = None,
        risk_engine: RiskPenaltyEngine = None,
        confidence_adjuster: ConfidenceAdjuster = None,
        decision_engine: DecisionEngine = None
    ):
        self.settings = settings
        self.cost_estimator = cost_estimator or CostEstimator(settings)
        self.risk_engine = risk_engine or RiskPenaltyEngine(settings)
        self.confidence_adjuster = confidence_adjuster or ConfidenceAdjuster(settings)
        self.decision_engine = decision_engine or DecisionEngine(settings)
        
    def _validate_input(self, input_data: ProfitabilityInput) -> ScoringStatus:
        if input_data.source_price is None or input_data.expected_sale_price_base is None:
            return ScoringStatus.INPUT_INCOMPLETE
        if input_data.source_price <= 0 or input_data.expected_sale_price_base <= 0:
            return ScoringStatus.INVALID_INPUT
        return ScoringStatus.SUCCESS

    def evaluate_profitability(self, input_data: ProfitabilityInput) -> ProfitabilityResult:
        score_id = f"pscore_{uuid.uuid4().hex[:12]}"
        explanation_lines: List[str] = []
        
        status = self._validate_input(input_data)
        if status != ScoringStatus.SUCCESS:
            explanation_lines.append(f"Validation failed: {status.value}")
            return ProfitabilityResult(
                profitability_score_id=score_id,
                candidate_id=input_data.candidate_id,
                market_evaluation_id=input_data.market_evaluation_id,
                scoring_status=status,
                expected_sale_price_low=input_data.expected_sale_price_low,
                expected_sale_price_base=input_data.expected_sale_price_base,
                expected_sale_price_high=input_data.expected_sale_price_high,
                components=ProfitabilityComponentBreakdown(),
                expected_net_profit=0.0,
                expected_margin=0.0,
                expected_roi=0.0,
                confidence_multiplier=0.0,
                confidence_adjusted_profit=0.0,
                profitability_score=0.0,
                decision_status=DecisionStatus.REJECT,
                decision_reason=f"Failed due to {status.value}",
                review_required=True,
                unsafe_reasons=input_data.unsafe_reasons + ["input_validation_failed"],
                explanation_lines=explanation_lines
            )
            
        # 1. Cost Estimation
        breakdown = self.cost_estimator.estimate_costs(input_data)
        explanation_lines.append(f"Estimated base costs. Effective Source Cost: {breakdown.effective_source_cost}")
        
        # 2. Risk Penalties
        self.risk_engine.calculate_penalties(input_data, breakdown)
        if breakdown.risk_penalty_total > 0:
            explanation_lines.append(f"Applied risk penalties total: {breakdown.risk_penalty_total}")
            
        # 3. Calculate Raw Profit
        base_price = input_data.expected_sale_price_base
        net_profit = base_price - breakdown.total_cost_and_penalty
        margin = net_profit / base_price if base_price > 0 else 0.0
        roi = net_profit / breakdown.effective_source_cost if breakdown.effective_source_cost > 0 else 0.0
        
        explanation_lines.append(f"Raw expected net profit: {net_profit:.2f} (Margin: {margin:.2%}, ROI: {roi:.2%})")
        
        # 4. Confidence Adjuster
        multiplier = self.confidence_adjuster.calculate_multiplier(input_data)
        adjusted_profit = net_profit * multiplier
        explanation_lines.append(f"Confidence Multiplier: {multiplier:.2f} -> Adjusted Profit: {adjusted_profit:.2f}")
        
        # Optional: Synthetic Score (normalized 0-100 placeholder)
        profitability_score = max(0.0, min(100.0, (adjusted_profit / 10000.0) * 100.0))
        
        # 5. Decision Engine
        decision, reason = self.decision_engine.determine_status(
            input_data, net_profit, margin, roi, adjusted_profit, breakdown
        )
        explanation_lines.append(f"Decision: {decision.value}. Reason: {reason}")
        
        return ProfitabilityResult(
            profitability_score_id=score_id,
            candidate_id=input_data.candidate_id,
            market_evaluation_id=input_data.market_evaluation_id,
            scoring_status=ScoringStatus.SUCCESS,
            expected_sale_price_low=input_data.expected_sale_price_low,
            expected_sale_price_base=input_data.expected_sale_price_base,
            expected_sale_price_high=input_data.expected_sale_price_high,
            components=breakdown,
            expected_net_profit=net_profit,
            expected_margin=margin,
            expected_roi=roi,
            confidence_multiplier=multiplier,
            confidence_adjusted_profit=adjusted_profit,
            profitability_score=profitability_score,
            decision_status=decision,
            decision_reason=reason,
            review_required=(decision == DecisionStatus.REVIEW_REQUIRED or input_data.review_required),
            unsafe_reasons=input_data.unsafe_reasons,
            explanation_lines=explanation_lines
        )
