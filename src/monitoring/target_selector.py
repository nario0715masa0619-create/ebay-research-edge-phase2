from dataclasses import dataclass, field
from typing import List, Tuple
from src.ebay.models import ProductCandidate

@dataclass
class SelectorResult:
    eligible_flag: bool = False
    skip_flag: bool = False
    selector_reason_codes: List[str] = field(default_factory=list)

class MonitoringTargetSelector:
    def evaluate(self, candidate: ProductCandidate) -> SelectorResult:
        reasons = []
        eligible = True
        skip = False
        
        # Section 3: 監視対象抽出処理
        if candidate.status != "listed":
            eligible = False
            reasons.append("not_listed")
            
        if candidate.pipeline_type != "auto":
            eligible = False
            reasons.append("not_auto_pipeline")
            
        if candidate.pipeline_type == "manual_preban":
            eligible = False
            reasons.append("manual_preban")
            
        # Optional: sold, invalid check
        if candidate.status in ["sold", "invalid"]:
            eligible = False
            reasons.append(f"status_{candidate.status}")

        return SelectorResult(
            eligible_flag=eligible,
            skip_flag=not eligible,
            selector_reason_codes=reasons
        )
