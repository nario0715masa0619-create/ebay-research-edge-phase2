from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from src.ebay.models import ProductCandidate

@dataclass
class PolicyReadinessResult:
    fulfillment_policy_id: Optional[str] = None
    payment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    merchant_location_key: Optional[str] = None
    policy_ready: bool = True
    policy_blockers: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)

class PolicyReadinessEvaluator:
    def evaluate(self, candidate: ProductCandidate, allow_default: bool = True) -> PolicyReadinessResult:
        blockers = []
        
        # In real implementation, check if these IDs exist or can be defaulted
        fulfillment_id = "default_fulfillment_id" if allow_default else None
        payment_id = "default_payment_id" if allow_default else None
        return_id = "default_return_id" if allow_default else None
        location_key = "default_location" if allow_default else None
        
        if not fulfillment_id: blockers.append("fulfillment_policy_missing")
        if not payment_id: blockers.append("payment_policy_missing")
        if not return_id: blockers.append("return_policy_missing")
        if not location_key: blockers.append("location_missing")
        
        return PolicyReadinessResult(
            fulfillment_policy_id=fulfillment_id,
            payment_policy_id=payment_id,
            return_policy_id=return_id,
            merchant_location_key=location_key,
            policy_ready=len(blockers) == 0,
            policy_blockers=blockers
        )
