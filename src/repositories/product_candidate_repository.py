from typing import Optional, List
from src.ebay.models import ProductCandidate

class ProductCandidateRepository:
    def __init__(self):
        self._candidates = {}  # {candidate_id: ProductCandidate}
        self._source_map = {} # {(source_platform, source_item_id): candidate_id}
        self._sku_map = {}    # {sku: candidate_id}

    def get_by_candidate_id(self, candidate_id: str) -> Optional[ProductCandidate]:
        return self._candidates.get(candidate_id)

    def get_by_source_key(self, source_platform: str, source_item_id: str) -> Optional[ProductCandidate]:
        cid = self._source_map.get((source_platform, source_item_id))
        if cid:
            return self.get_by_candidate_id(cid)
        return None

    def get_by_sku(self, sku: str) -> Optional[ProductCandidate]:
        cid = self._sku_map.get(sku)
        if cid:
            return self.get_by_candidate_id(cid)
        return None

    def upsert(self, candidate: ProductCandidate):
        self._candidates[candidate.candidate_id] = candidate
        self._source_map[(candidate.source_platform, candidate.source_item_id)] = candidate.candidate_id
        self._sku_map[candidate.sku] = candidate.candidate_id

    def list_by_status(self, status: str, limit: Optional[int] = None) -> List[ProductCandidate]:
        matches = [c for c in self._candidates.values() if c.status == status]
        if limit:
            return matches[:limit]
        return matches

    def exists_duplicate_source(self, source_platform: str, source_item_id: str) -> bool:
        return (source_platform, source_item_id) in self._source_map
