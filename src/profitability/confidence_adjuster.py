from src.profitability.models import ProfitabilityInput
from src.profitability.config import ProfitabilitySettings

class ConfidenceAdjuster:
    def __init__(self, settings: ProfitabilitySettings):
        self.settings = settings
        
    def calculate_multiplier(self, input_data: ProfitabilityInput) -> float:
        # 13.4 Confidence Multiplier
        # confidence_multiplier = clamp(0.35, 1.00, market_confidence * 0.55 + 
        # category_alignment_score * 0.10 + condition_alignment_score * 0.10 + 
        # attribute_alignment_score * 0.10 + comparable_count_factor * 0.10 - 
        # ambiguity_penalty_factor * 0.05 - unsafe_penalty_factor * 0.10)
        
        m_conf = input_data.market_confidence or 0.0
        c_align = input_data.category_alignment_score
        cond_align = input_data.condition_alignment_score
        attr_align = input_data.attribute_alignment_score
        
        # Comparable count factor (0 to 1)
        count_factor = min(1.0, input_data.comparable_count / 5.0) 
        
        # Ambiguity factor
        ambiguity_factor = 1.0 if input_data.review_required else (len(input_data.ambiguity_flags) * 0.5)
        ambiguity_factor = min(1.0, ambiguity_factor)
        
        # Unsafe penalty factor
        unsafe_factor = min(1.0, len(input_data.unsafe_reasons) * 0.5)
        
        raw_multiplier = (
            (m_conf * 0.55) +
            (c_align * 0.10) +
            (cond_align * 0.10) +
            (attr_align * 0.10) +
            (count_factor * 0.10) -
            (ambiguity_factor * 0.05) -
            (unsafe_factor * 0.10)
        )
        
        # Clamp between 0.35 and 1.00
        return max(0.35, min(1.00, raw_multiplier))
