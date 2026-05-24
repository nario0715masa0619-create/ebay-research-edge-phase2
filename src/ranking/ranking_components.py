from src.ranking.models import RankingInput, RankingComponents
from src.ranking.config import RankingSettings

class RankingCalculator:
    def __init__(self, settings: RankingSettings):
        self.settings = settings
        
    def calculate_score(self, input_data: RankingInput, is_stale: bool, is_blocked: bool) -> tuple[float, RankingComponents]:
        comps = RankingComponents()
        
        # Base normalization functions (simplified for v0.1)
        # Assuming profit of 10000 is 100% score for profit component
        max_profit = 10000.0
        comps.profitability_component = min(1.0, max(0.0, input_data.confidence_adjusted_profit / max_profit))
        
        comps.margin_component = min(1.0, max(0.0, input_data.expected_margin / 0.50)) # 50% margin is perfect
        comps.roi_component = min(1.0, max(0.0, input_data.expected_roi / 0.50))       # 50% ROI is perfect
        comps.market_confidence_component = min(1.0, max(0.0, input_data.market_confidence))
        
        # Proxies
        comps.demand_component = 1.0 if input_data.demand_proxy == "high" else (0.5 if input_data.demand_proxy == "medium" else 0.2)
        comps.competition_component = 1.0 if input_data.competition_proxy == "low" else (0.5 if input_data.competition_proxy == "medium" else 0.0)
        
        # Penalties
        if input_data.review_required or input_data.ambiguity_flags:
            comps.review_penalty = 0.5
            
        if input_data.market_unsafe_reasons or input_data.profitability_unsafe_reasons:
            comps.unsafe_penalty = 0.8
            
        if is_stale:
            comps.staleness_penalty = 0.6
            
        if is_blocked and self.settings.capacity_penalty_enabled:
            comps.capacity_penalty = 0.4
            
        # Recommended Synthetic Formula (v0.1)
        raw_score = (
            (comps.profitability_component * 0.35) +
            (min(1.0, input_data.profitability_score / 100.0) * 0.20) +
            (comps.market_confidence_component * 0.10) +
            (comps.margin_component * 0.10) +
            (comps.roi_component * 0.10) +
            (comps.demand_component * 0.10) -
            (comps.review_penalty * 0.10) -
            (comps.unsafe_penalty * 0.10) -
            (comps.staleness_penalty * 0.05) -
            (comps.capacity_penalty * 0.05)
        )
        
        final_score = min(100.0, max(0.0, raw_score * 100.0))
        return final_score, comps
