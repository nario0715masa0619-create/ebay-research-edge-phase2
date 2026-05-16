from typing import List, Optional, Dict, Any
from src.repositories.persistent_product_candidate_repository import PersistentProductCandidateRepository
from ..models import CliCommandResult

class CandidateOpsService:
    def __init__(self, candidate_repo: PersistentProductCandidateRepository):
        self.candidate_repo = candidate_repo

    def list_candidates(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if status:
            candidates = self.candidate_repo.list_by_status(status, limit=limit)
        else:
            candidates = self.candidate_repo.list_all(limit=limit)
        
        return [
            {
                "sku": c.sku,
                "title": c.source_title[:40] + "..." if len(c.source_title) > 40 else c.source_title,
                "status": c.status,
                "readiness": c.listing_readiness_status,
                "score": f"{c.standard_score:.2f}",
                "profit": f"{c.expected_profit_jpy:,.0f} JPY"
            }
            for c in candidates
        ]

    def get_candidate_detail(self, sku: str) -> Optional[Dict[str, Any]]:
        c = self.candidate_repo.get_by_sku(sku)
        if not c:
            return None
        
        return {
            "candidate_id": c.candidate_id,
            "sku": c.sku,
            "source_url": c.source_url,
            "status": c.status,
            "readiness": c.listing_readiness_status,
            "publish_readiness": c.publish_readiness,
            "score": c.standard_score,
            "profit": c.expected_profit_jpy,
            "profit_rate": c.expected_profit_rate,
            "blockers": ", ".join(c.listing_blockers) if c.listing_blockers else "-",
            "exclude_reason": c.exclude_reason or "-",
            "created_at": c.created_at.isoformat()
        }
