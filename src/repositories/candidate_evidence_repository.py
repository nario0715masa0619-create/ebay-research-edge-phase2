from typing import List
from src.ebay.models import CandidateEvidence

class CandidateEvidenceRepository:
    def __init__(self):
        self._evidence = {}  # {evidence_id: CandidateEvidence}
        self._candidate_map = {} # {candidate_id: [evidence_id]}

    def save(self, evidence: CandidateEvidence):
        self._evidence[evidence.evidence_id] = evidence
        if evidence.candidate_id not in self._candidate_map:
            self._candidate_map[evidence.candidate_id] = []
        self._candidate_map[evidence.candidate_id].append(evidence.evidence_id)

    def save_many(self, evidence_list: List[CandidateEvidence]):
        for e in evidence_list:
            self.save(e)

    def list_by_candidate_id(self, candidate_id: str) -> List[CandidateEvidence]:
        eids = self._candidate_map.get(candidate_id, [])
        return [self._evidence[eid] for eid in eids]
