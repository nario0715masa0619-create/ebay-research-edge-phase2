from typing import List, Tuple
from .models import MarketSearchSeed, MarketListingSnapshot, ComparableEvaluation
from .alignment_evaluator import AlignmentEvaluator

class ComparableFilter:
    """
    Filters normalized snapshots to retain only those that are safe and comparable.
    Uses AlignmentEvaluator to score categories, conditions, and attributes.
    """
    
    def __init__(self, evaluator: AlignmentEvaluator = None):
        self.evaluator = evaluator or AlignmentEvaluator()
        
    def filter_comparables(self, seed: MarketSearchSeed, snapshots: List[MarketListingSnapshot]) -> List[ComparableEvaluation]:
        evaluations = []
        
        for snap in snapshots:
            # 1. Category
            cat_score = self.evaluator.evaluate_category(seed, snap)
            # 2. Condition
            cond_score = self.evaluator.evaluate_condition(seed, snap)
            # 3. Attributes
            attr_score, v_flags, b_flags = self.evaluator.evaluate_attributes(seed, snap)
            
            # Combine scores (simple weighted minimums or thresholds)
            comp_score = cat_score * cond_score * attr_score
            
            included = True
            exclusion_reason = None
            
            if cat_score < 0.4:
                included = False
                exclusion_reason = "category_mismatch"
            elif cond_score < 0.4:
                included = False
                exclusion_reason = "condition_mismatch"
            elif v_flags:
                included = False
                exclusion_reason = f"variation_conflict: {v_flags[0]}"
            elif b_flags:
                included = False
                exclusion_reason = f"bundle_conflict: {b_flags[0]}"
            elif attr_score < 0.4:
                included = False
                exclusion_reason = "attribute_mismatch"
                
            evaluation = ComparableEvaluation(
                listing_id=snap.listing_id,
                included=included,
                comparable_score=comp_score,
                category_alignment_score=cat_score,
                condition_alignment_score=cond_score,
                attribute_alignment_score=attr_score,
                variation_conflict_flags=v_flags,
                bundle_conflict_flags=b_flags,
                exclusion_reason=exclusion_reason
            )
            evaluations.append(evaluation)
            
        return evaluations
