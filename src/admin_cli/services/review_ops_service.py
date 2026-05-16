from typing import List, Optional, Dict, Any
from src.repositories.persistent_product_candidate_repository import PersistentProductCandidateRepository
from ..models import CliCommandResult

class ReviewOpsService:
    def __init__(self, candidate_repo: PersistentProductCandidateRepository):
        self.candidate_repo = candidate_repo

    def list_review_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        # This is a bit simplified; real review queue might involve more complex filters
        candidates = self.candidate_repo.list_by_status("review_required", limit=limit)
        return [
            {
                "sku": c.sku,
                "reason": c.review_reason or c.exclude_reason or "unknown",
                "score": f"{c.standard_score:.2f}",
                "readiness": c.listing_readiness_status,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for c in candidates
        ]
