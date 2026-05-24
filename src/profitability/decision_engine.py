from typing import Tuple, List
from src.profitability.models import ProfitabilityInput, ProfitabilityComponentBreakdown, DecisionStatus
from src.profitability.config import ProfitabilitySettings

class DecisionEngine:
    def __init__(self, settings: ProfitabilitySettings):
        self.settings = settings
        
    def determine_status(
        self, 
        input_data: ProfitabilityInput, 
        net_profit: float, 
        margin: float, 
        roi: float, 
        confidence_adjusted_profit: float,
        breakdown: ProfitabilityComponentBreakdown
    ) -> Tuple[DecisionStatus, str]:
        
        reasons = []
        
        # Check basic valid inputs
        if input_data.expected_sale_price_base is None or input_data.source_price is None:
            return DecisionStatus.REJECT, "Missing required base price or source price."
            
        m_conf = input_data.market_confidence or 0.0
        
        # Rule: severe unsafe reasons or low confidence -> Reject
        if m_conf < self.settings.reject_confidence_threshold:
            return DecisionStatus.REJECT, f"Market confidence ({m_conf:.2f}) below reject threshold."
            
        if net_profit <= 0 or confidence_adjusted_profit <= 0:
            return DecisionStatus.REJECT, "Expected net profit or adjusted profit is zero or negative."
            
        # Check if review is forced by input or unsafe
        if input_data.review_required:
            reasons.append("Input flagged as review_required.")
            
        if input_data.unsafe_reasons:
            reasons.append(f"Contains unsafe reasons: {', '.join(input_data.unsafe_reasons)}")
            
        if breakdown.risk_penalty_total > (input_data.expected_sale_price_base * 0.15):
             reasons.append("Risk penalties are too high.")
             
        # Launch Now thresholds
        can_launch = (
            confidence_adjusted_profit >= self.settings.min_launch_profit and
            margin >= self.settings.min_launch_margin and
            roi >= self.settings.min_launch_roi and
            m_conf >= 0.75 and
            not input_data.review_required and
            not input_data.unsafe_reasons and
            len(reasons) == 0
        )
        
        if can_launch:
            return DecisionStatus.LAUNCH_NOW, "Meets all launch criteria."
            
        # Review Required thresholds
        needs_review = (
            confidence_adjusted_profit >= self.settings.min_review_profit or
            len(reasons) > 0
        )
        
        if needs_review:
            return DecisionStatus.REVIEW_REQUIRED, " | ".join(reasons) if reasons else "Meets review criteria, but not launch criteria."
            
        # Default to Watch if positive profit but doesn't meet review threshold
        return DecisionStatus.WATCH, "Low profit opportunity. Needs monitoring."
