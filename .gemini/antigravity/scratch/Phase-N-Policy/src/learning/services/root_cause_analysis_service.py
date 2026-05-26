from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from src.learning.models.root_cause_analysis import RootCauseAnalysis

class RootCauseAnalysisService:
    """RCA 管理"""

    def __init__(self):
        self.rcas: Dict[UUID, RootCauseAnalysis] = {}

    def create_rca(
        self, 
        learning_record_id: UUID, 
        problem: str, 
        symptoms: str, 
        cause: str, 
        factors: str, 
        mitigation: str, 
        resolution: str, 
        prevention: str, 
        created_by: str, 
        evidence: Optional[Dict[str, Any]] = None
    ) -> RootCauseAnalysis:
        """RCA 作成。Returns: RootCauseAnalysis"""
        rca = RootCauseAnalysis(
            rca_id=uuid4(),
            learning_record_id=learning_record_id,
            problem_statement=problem,
            observed_symptoms=symptoms,
            primary_cause=cause,
            contributing_factors=factors,
            detection_gap=None,
            mitigation_taken=mitigation,
            resolution_summary=resolution,
            prevention_proposal=prevention,
            evidence_snapshot=evidence or {},
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        self.rcas[rca.rca_id] = rca
        return rca

    def get_rca_by_id(self, rca_id: UUID) -> Optional[RootCauseAnalysis]:
        """ID で取得。Returns: RootCauseAnalysis or None"""
        return self.rcas.get(rca_id)

    def get_rcas_by_learning_record(self, learning_record_id: UUID) -> List[RootCauseAnalysis]:
        """learning_record でフィルタ。Returns: [RootCauseAnalysis]"""
        filtered = [r for r in self.rcas.values() if r.learning_record_id == learning_record_id]
        filtered.sort(key=lambda x: x.created_at)
        return filtered

    def update_rca(
        self, 
        rca_id: UUID, 
        problem: Optional[str] = None, 
        cause: Optional[str] = None, 
        resolution: Optional[str] = None
    ) -> RootCauseAnalysis:
        """更新。Returns: 更新済み RCA"""
        rca = self.rcas.get(rca_id)
        if not rca:
            raise ValueError(f"RCA {rca_id} not found")
            
        if problem is not None:
            rca.problem_statement = problem
        if cause is not None:
            rca.primary_cause = cause
        if resolution is not None:
            rca.resolution_summary = resolution
            
        return rca

    def add_detection_gap_analysis(self, rca_id: UUID, gap_description: str) -> RootCauseAnalysis:
        """detection_gap 追加。Returns: 更新済み RCA"""
        rca = self.rcas.get(rca_id)
        if not rca:
            raise ValueError(f"RCA {rca_id} not found")
            
        rca.detection_gap = gap_description
        return rca

    def extract_prevention_proposal(self, rca_id: UUID) -> str:
        """prevention_proposal を抽出・フォーマット。Returns: proposal text"""
        rca = self.rcas.get(rca_id)
        if not rca:
            raise ValueError(f"RCA {rca_id} not found")
            
        return f"Prevention Proposal for RCA {rca_id}:\n{rca.prevention_proposal}"
