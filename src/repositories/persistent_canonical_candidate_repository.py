from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import CanonicalProductCandidateModel
from src.discovery.models import CanonicalProductCandidate
import json

class PersistentCanonicalCandidateRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, candidate: CanonicalProductCandidate) -> None:
        with self.session_factory() as session:
            model = CanonicalProductCandidateModel(
                candidate_id=candidate.candidate_id,
                canonical_title=candidate.canonical_title,
                canonical_brand=candidate.canonical_brand,
                canonical_model=candidate.canonical_model,
                canonical_mpn=candidate.canonical_mpn,
                canonical_gtins_json=candidate.canonical_gtins,
                canonical_condition_family=candidate.canonical_condition_family,
                variation_signature=candidate.variation_signature,
                bundle_signature=candidate.bundle_signature,
                source_count=candidate.source_count,
                matched_source_item_ids_json=candidate.matched_source_item_ids,
                match_confidence=candidate.match_confidence,
                ambiguity_flags_json=candidate.ambiguity_flags,
                review_required=candidate.review_required,
                category_candidates_json=candidate.category_candidates,
                feature_payload_json=candidate.feature_payload,
                created_at=candidate.created_at,
                updated_at=candidate.updated_at
            )
            session.add(model)
            session.commit()

    def find_by_brand_mpn(self, brand: str, mpn: str) -> Optional[CanonicalProductCandidate]:
        if not brand or not mpn:
            return None
        with self.session_factory() as session:
            stmt = select(CanonicalProductCandidateModel).where(
                CanonicalProductCandidateModel.canonical_brand == brand,
                CanonicalProductCandidateModel.canonical_mpn == mpn
            )
            model = session.execute(stmt).scalars().first()
            if not model:
                return None
            return self._to_domain(model)

    def search_similar_titles(self, title: str, limit: int = 20) -> List[CanonicalProductCandidate]:
        # For Phase A, basic exact prefix or slow ILIKE search since we don't have full-text search yet.
        # This will be replaced by a proper index in Phase B.
        with self.session_factory() as session:
            stmt = select(CanonicalProductCandidateModel).where(
                CanonicalProductCandidateModel.canonical_title.ilike(f"%{title}%")
            ).limit(limit)
            models = session.execute(stmt).scalars().all()
            return [self._to_domain(m) for m in models]

    def _to_domain(self, model: CanonicalProductCandidateModel) -> CanonicalProductCandidate:
        return CanonicalProductCandidate(
            candidate_id=model.candidate_id,
            canonical_title=model.canonical_title,
            canonical_brand=model.canonical_brand,
            canonical_model=model.canonical_model,
            canonical_mpn=model.canonical_mpn,
            canonical_gtins=model.canonical_gtins_json or [],
            canonical_condition_family=model.canonical_condition_family,
            variation_signature=model.variation_signature,
            bundle_signature=model.bundle_signature,
            source_count=model.source_count,
            matched_source_item_ids=model.matched_source_item_ids_json or [],
            match_confidence=model.match_confidence,
            ambiguity_flags=model.ambiguity_flags_json or [],
            review_required=model.review_required,
            category_candidates=model.category_candidates_json or [],
            feature_payload=model.feature_payload_json or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
