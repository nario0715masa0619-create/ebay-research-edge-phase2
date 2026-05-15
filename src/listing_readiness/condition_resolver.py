from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from src.ebay.models import ProductCandidate

@dataclass
class ConditionResolutionResult:
    ebay_condition: str = "USED_GOOD" # Default
    condition_descriptor_json: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reason_codes: List[str] = field(default_factory=list)

class ConditionResolver:
    def resolve(self, candidate: ProductCandidate, category_id: Optional[str] = None) -> ConditionResolutionResult:
        # Simple mapping for mock
        source_cond = (candidate.condition_source or "new").lower()
        
        if source_cond == "new":
            return ConditionResolutionResult(
                ebay_condition="NEW",
                confidence=1.0,
                reason_codes=["direct_mapping_new"]
            )
        
        # Default used
        return ConditionResolutionResult(
            ebay_condition="USED_GOOD",
            confidence=0.7,
            reason_codes=["default_used_mapping"]
        )
