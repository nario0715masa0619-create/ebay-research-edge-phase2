from typing import Optional
from sqlalchemy.orm import Session
from src.db.models import MatchEvidenceModel
from src.discovery.models import MatchEvidence

class PersistentMatchEvidenceRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, evidence: MatchEvidence) -> None:
        with self.session_factory() as session:
            model = MatchEvidenceModel(
                evidence_id=evidence.evidence_id,
                normalized_item_id=evidence.normalized_item_id,
                candidate_id=evidence.candidate_id,
                identifier_hits_json=evidence.identifier_hits,
                title_similarity_score=evidence.title_similarity_score,
                brand_match_score=evidence.brand_match_score,
                model_match_score=evidence.model_match_score,
                mpn_match_score=evidence.mpn_match_score,
                variation_penalty=evidence.variation_penalty,
                bundle_penalty=evidence.bundle_penalty,
                condition_penalty=evidence.condition_penalty,
                ambiguity_flags_json=evidence.ambiguity_flags,
                explanation_lines_json=evidence.explanation_lines,
                created_at=evidence.created_at
            )
            session.add(model)
            session.commit()
