from src.profitability.models import ProfitabilityInput, ProfitabilityComponentBreakdown
from src.profitability.config import ProfitabilitySettings

class RiskPenaltyEngine:
    def __init__(self, settings: ProfitabilitySettings):
        self.settings = settings
        
    def calculate_penalties(self, input_data: ProfitabilityInput, breakdown: ProfitabilityComponentBreakdown) -> None:
        base_price = input_data.expected_sale_price_base or 0.0
        
        # 1. Low Comparable Penalty
        if input_data.comparable_count < 3:
            breakdown.low_comparable_penalty = base_price * self.settings.default_low_comparable_penalty_rate
            
        # 2. Unsafe Reasons Penalities
        for unsafe in input_data.unsafe_reasons:
            if "condition_mismatch" in unsafe:
                breakdown.condition_mismatch_penalty += base_price * 0.05
            if "category_mismatch" in unsafe:
                # Strong penalty
                breakdown.restriction_risk_penalty += base_price * 0.10
        
        # 3. Special Restrictions
        for flag in input_data.special_restriction_flags:
            if flag in ["fragile", "bulky"]:
                breakdown.damage_risk_penalty += base_price * 0.05
            if flag == "authenticity_concern":
                breakdown.authenticity_risk_penalty += base_price * 0.15
                
        # 4. Competition Proxy
        comp = input_data.competition_proxy or "low"
        if comp == "high":
            breakdown.competition_penalty = base_price * 0.08
        elif comp == "medium":
            breakdown.competition_penalty = base_price * 0.03
            
        # 5. Ambiguity
        if input_data.review_required:
            breakdown.ambiguity_penalty += base_price * 0.12
        elif input_data.ambiguity_flags:
            # simple count based penalty for flags
            count = len(input_data.ambiguity_flags)
            rate = min(0.12, count * self.settings.default_ambiguity_penalty_rate)
            breakdown.ambiguity_penalty += base_price * rate
