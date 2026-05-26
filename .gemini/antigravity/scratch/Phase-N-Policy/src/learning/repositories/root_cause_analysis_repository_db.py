from typing import Optional, List, Tuple, Dict
from uuid import UUID
from src.learning.models.root_cause_analysis import RootCauseAnalysis

class RootCauseAnalysisRepository:
    """DB-backed RCA repository"""
    def __init__(self):
        self.rcas = {}

    def create_rca(self, rca: RootCauseAnalysis) -> RootCauseAnalysis:
        self.rcas[rca.rca_id] = rca
        return rca

    def get_rca_by_id(self, rca_id: UUID) -> Optional[RootCauseAnalysis]:
        return self.rcas.get(rca_id)

    def get_rcas_by_learning_record(self, learning_record_id: UUID) -> List[RootCauseAnalysis]:
        res = [r for r in self.rcas.values() if r.learning_record_id == learning_record_id]
        res.sort(key=lambda x: x.created_at)
        return res

    def list_all_rcas(self, limit: int = 100, offset: int = 0) -> Tuple[List[RootCauseAnalysis], int]:
        all_rcas = list(self.rcas.values())
        all_rcas.sort(key=lambda x: x.created_at, reverse=True)
        return all_rcas[offset:offset+limit], len(all_rcas)

    def count_rcas_by_learning_record(self) -> Dict[UUID, int]:
        counts = {}
        for r in self.rcas.values():
            counts[r.learning_record_id] = counts.get(r.learning_record_id, 0) + 1
        return counts
