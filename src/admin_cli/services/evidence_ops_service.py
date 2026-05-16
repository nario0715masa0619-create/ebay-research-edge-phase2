from typing import List, Optional, Dict, Any
from src.repositories.persistent_candidate_evidence_repository import PersistentCandidateEvidenceRepository
from ..models import CliCommandResult

class EvidenceOpsService:
    def __init__(self, evidence_repo: PersistentCandidateEvidenceRepository):
        self.evidence_repo = evidence_repo

    def list_by_candidate(self, candidate_id: str) -> List[Dict[str, Any]]:
        evidences = self.evidence_repo.get_by_candidate_id(candidate_id)
        return [
            {
                "evidence_id": e.evidence_id[:8] + "...",
                "type": e.evidence_type,
                "version": e.rule_version,
                "created": e.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for e in evidences
        ]

    def get_detail(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        e = self.evidence_repo.get_by_evidence_id(evidence_id)
        if not e:
            return None
        return {
            "evidence_id": e.evidence_id,
            "candidate_id": e.candidate_id,
            "type": e.evidence_type,
            "payload": e.evidence_payload,
            "version": e.rule_version,
            "created_at": e.created_at.isoformat()
        }
