from typing import Tuple, List, Optional
from src.ranking.models import RankingInput, DecisionClass
from src.ranking.config import RankingSettings
from src.ranking.staleness_policy import StalenessPolicy
from datetime import datetime

class EligibilityGate:
    def __init__(self, settings: RankingSettings, staleness_policy: Optional[StalenessPolicy] = None):
        self.settings = settings
        self.staleness_policy = staleness_policy or StalenessPolicy(settings)

    def evaluate_gates(self, input_data: RankingInput, now: datetime = None) -> Tuple[Optional[DecisionClass], List[str], bool, bool]:
        """
        Evaluate gates sequentially.
        Returns:
            Tuple[Optional[DecisionClass], List[str], bool, bool]: 
            (immediate_decision, block_reasons, is_blocked, is_stale)
        """
        block_reasons = []
        is_stale = False
        
        # 1. Reject Gate (Severe issues)
        if input_data.profitability_scoring_status in ["invalid_input", "input_incomplete"]:
            block_reasons.append(f"Profitability input incomplete: {input_data.profitability_scoring_status}")
            return DecisionClass.REJECT, block_reasons, True, is_stale
            
        if input_data.market_evaluation_status != "success":
            block_reasons.append("Market evaluation failed.")
            return DecisionClass.REJECT, block_reasons, True, is_stale
            
        if input_data.expected_net_profit <= 0 or input_data.confidence_adjusted_profit <= 0:
            block_reasons.append("Expected profit is negative or zero.")
            return DecisionClass.REJECT, block_reasons, True, is_stale
            
        if input_data.market_confidence < self.settings.reject_market_confidence_threshold:
            block_reasons.append(f"Market confidence ({input_data.market_confidence:.2f}) is below reject threshold.")
            return DecisionClass.REJECT, block_reasons, True, is_stale
            
        if input_data.blacklisted:
            block_reasons.append("Seller policy strictly blocks this candidate.")
            return DecisionClass.REJECT, block_reasons, True, is_stale
            
        # 2. Block/Capacity Gate
        is_blocked = False
        if input_data.execution_blocked_by_seller:
            block_reasons.append("Execution blocked by seller level restrictions.")
            is_blocked = True
            
        if input_data.seller_capacity_full and self.settings.defer_when_capacity_full:
            block_reasons.append("Seller capacity is full. Deferred.")
            is_blocked = True
            
        # 3. Staleness Gate
        if self.staleness_policy.evaluate_staleness(input_data, now):
            block_reasons.append("Market or Profitability data is stale. Recheck required.")
            is_stale = True
            
        # If any block reasons exist (stale or capacity), we definitely cannot auto-launch.
        # But we don't immediately reject; we might pass it to Manual Review or Watchlist later in Decision Engine.
        # So we return None for immediate_decision, allowing DecisionEngine to handle it based on block_reasons.
        
        return None, block_reasons, is_blocked, is_stale
