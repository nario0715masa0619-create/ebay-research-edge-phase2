from typing import List, Dict, Any, Tuple
from .category_resolver import CategoryResolutionResult
from .aspects_resolver import AspectsResolutionResult
from .condition_resolver import ConditionResolutionResult
from .content_evaluator import ContentReadinessResult
from .policy_evaluator import PolicyReadinessResult

class BlockerEngine:
    def evaluate(
        self,
        category_res: CategoryResolutionResult,
        aspects_res: AspectsResolutionResult,
        condition_res: ConditionResolutionResult,
        content_res: ContentReadinessResult,
        policy_res: PolicyReadinessResult,
        strictness: str = "balanced"
    ) -> Tuple[str, bool, List[str], List[str]]:
        """
        Returns: (listing_readiness_status, publish_readiness, listing_blockers, reason_codes)
        """
        blockers = []
        reason_codes = []
        
        # 1. Category Blockers
        if not category_res.ebay_category_id:
            blockers.append("category_unresolved")
        if category_res.review_required:
            reason_codes.append("category_review_required")
            
        # 2. Aspect Blockers
        if aspects_res.missing_required_aspects:
            blockers.append("required_aspects_missing")
            reason_codes.extend([f"missing_req_{a}" for a in aspects_res.missing_required_aspects])
            
        # 3. Condition Blockers
        if not condition_res.ebay_condition:
            blockers.append("condition_unresolved")
            
        # 4. Content Blockers
        blockers.extend(content_res.content_blockers)
        
        # 5. Policy Blockers
        blockers.extend(policy_res.policy_blockers)
        
        # Decide Status
        publish_readiness = (len(blockers) == 0)
        
        if len(blockers) > 0:
            status = "blocked"
        elif category_res.confidence < 0.5 or aspects_res.confidence < 0.5 or condition_res.confidence < 0.5:
            status = "review_required"
        elif aspects_res.missing_recommended_aspects:
            status = "review_required"
            reason_codes.append("recommended_aspects_missing")
        else:
            status = "ready"
            
        # If strictness is high, even low confidence is a blocker
        if strictness == "strict" and status == "review_required":
            status = "blocked"
            blockers.append("low_confidence_strict")
            
        return status, publish_readiness, blockers, reason_codes
