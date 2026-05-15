from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from src.ebay.models import ProductCandidate

@dataclass
class ContentReadinessResult:
    content_readiness_status: str = "ready"
    title_ready: bool = True
    description_ready: bool = True
    image_ready: bool = True
    content_blockers: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)

class ContentReadinessEvaluator:
    def evaluate(self, candidate: ProductCandidate, title_max_length: int = 80) -> ContentReadinessResult:
        blockers = []
        reasons = []
        title_ready = True
        desc_ready = True
        img_ready = True
        
        # Title Evaluation
        title = candidate.ebay_title_candidate or candidate.normalized_title or candidate.source_title
        if not title:
            blockers.append("title_missing")
            title_ready = False
        elif len(title) > title_max_length:
            blockers.append("title_too_long")
            title_ready = False
            
        # Description Evaluation
        # (Assuming description template logic is elsewhere, we check if we have enough info)
        if not candidate.source_url:
            blockers.append("description_source_missing")
            desc_ready = False
            
        # Image Evaluation
        if not candidate.image_urls or len(candidate.image_urls) < 1:
            blockers.append("insufficient_images")
            img_ready = False
            
        status = "ready" if not blockers else "blocked"
        
        return ContentReadinessResult(
            content_readiness_status=status,
            title_ready=title_ready,
            description_ready=desc_ready,
            image_ready=img_ready,
            content_blockers=blockers,
            reason_codes=reasons
        )
