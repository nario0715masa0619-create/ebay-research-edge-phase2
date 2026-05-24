from typing import List, Tuple, Optional
from .models import ComparableEvaluation

class MarketConfidenceCalculator:
    """
    Calculates the final market confidence score and competition/demand proxies.
    """
    
    def calculate(self, 
                  evaluations: List[ComparableEvaluation], 
                  unsafe_reasons: List[str], 
                  raw_count: int,
                  min_comparable_count: int = 3) -> Tuple[float, Optional[str], Optional[str], List[str]]:
        
        confidence = 1.0
        new_unsafe = list(unsafe_reasons)
        
        included_evals = [e for e in evaluations if e.included]
        comparable_count = len(included_evals)
        
        # Base penalty for too few items
        if comparable_count < min_comparable_count:
            confidence *= 0.5
            new_unsafe.append("too_few_comparables")
        
        # Penalize if the overall quality is low
        if comparable_count > 0:
            avg_cat = sum(e.category_alignment_score for e in included_evals) / comparable_count
            avg_cond = sum(e.condition_alignment_score for e in included_evals) / comparable_count
            avg_attr = sum(e.attribute_alignment_score for e in included_evals) / comparable_count
            
            if avg_cat < 0.7:
                confidence *= 0.8
            if avg_cond < 0.7:
                confidence *= 0.8
            if avg_attr < 0.7:
                confidence *= 0.6
                
        # Proxies
        competition_proxy = "low"
        demand_proxy = "low"
        
        if comparable_count >= 10:
            demand_proxy = "high"
            competition_proxy = "high"
        elif comparable_count >= 5:
            demand_proxy = "medium"
            competition_proxy = "medium"
            
        # Severe penalty if any hard unsafe reasons exist from provider
        if any("provider_" in u for u in new_unsafe) or any("parse_failure" in u for u in new_unsafe):
            confidence = 0.0
            
        return max(0.0, min(1.0, confidence)), competition_proxy, demand_proxy, new_unsafe

