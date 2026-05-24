from typing import Tuple, List, Optional
from src.ranking.models import RankingInput, DecisionClass
from src.ranking.config import RankingSettings

class DecisionEngine:
    def __init__(self, settings: RankingSettings):
        self.settings = settings

    def determine_decision(self, input_data: RankingInput, immediate_decision: Optional[DecisionClass], block_reasons: List[str], is_blocked: bool, is_stale: bool) -> Tuple[DecisionClass, str]:
        """
        Determines the final DecisionClass (auto_launch, manual_review, watchlist, reject)
        """
        
        # 1. Respect immediate decision from Eligibility Gate
        if immediate_decision:
            return immediate_decision, " | ".join(block_reasons)
            
        reasons = []
        
        # 2. Prevent auto_launch for stale, blocked, or explicitly review-required candidates
        can_auto_launch = True
        if is_stale:
            can_auto_launch = False
            reasons.append("Stale data. Recheck required.")
        if is_blocked:
            can_auto_launch = False
            reasons.append("Execution blocked or capacity full.")
        if input_data.review_required:
            can_auto_launch = False
            reasons.append("Review explicitly required by upstream.")
        if input_data.ambiguity_flags:
            can_auto_launch = False
            reasons.append("Ambiguity flags present.")
        if input_data.market_unsafe_reasons or input_data.profitability_unsafe_reasons:
            can_auto_launch = False
            reasons.append("Unsafe reasons present in market or profitability layer.")
            
        # 3. Check Profitability Thresholds for auto_launch
        if can_auto_launch:
            meets_launch_thresholds = (
                input_data.confidence_adjusted_profit >= self.settings.auto_launch_min_profit and
                input_data.expected_margin >= self.settings.auto_launch_min_margin and
                input_data.expected_roi >= self.settings.auto_launch_min_roi and
                input_data.market_confidence >= self.settings.auto_launch_min_confidence and
                input_data.profitability_decision_status == "launch_now"
            )
            if meets_launch_thresholds:
                return DecisionClass.AUTO_LAUNCH, "Meets all auto-launch criteria."
            else:
                reasons.append("Does not meet auto-launch financial/confidence thresholds.")
                
        # 4. If not auto_launch, decide between manual_review and watchlist
        
        # High profit or explicit review necessity -> Manual Review
        needs_review = (
            input_data.confidence_adjusted_profit >= (self.settings.auto_launch_min_profit * 0.5) or
            input_data.review_required or
            input_data.ambiguity_flags or 
            input_data.market_unsafe_reasons or
            input_data.profitability_unsafe_reasons or
            is_stale # Stale items might need review to trigger re-eval
        )
        
        if needs_review:
            # But if completely blocked by capacity/policy and it has no real review reasons, put it in watchlist
            needs_real_review = input_data.review_required or input_data.ambiguity_flags or input_data.market_unsafe_reasons or input_data.profitability_unsafe_reasons
            
            if is_blocked and not needs_real_review:
                return DecisionClass.WATCHLIST, "Blocked by capacity/policy and deferred. " + " | ".join(reasons)
                
            return DecisionClass.MANUAL_REVIEW, " | ".join(reasons)
            
        # 5. Default to Watchlist for low profit but non-reject candidates
        return DecisionClass.WATCHLIST, "Low profit or deferred. " + " | ".join(reasons)
