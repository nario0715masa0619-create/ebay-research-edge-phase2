from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from src.db.session import SessionManager
from src.db.models import CanonicalProductCandidateModel, MatchEvidenceModel, NormalizedSourceItemModel, ReviewAuditLogModel
from src.discovery.review_models import ReviewQueueItem, CandidateCompareView, ReviewStatus, SourceCompareItem, ReviewDecisionRecord

class PersistentReviewQueueRepository:
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()

    def get_pending_queue(self, limit: int = 50, offset: int = 0, sort_by: str = "ambiguity_desc") -> List[ReviewQueueItem]:
        with self.session_manager.session() as session:
            stmt = select(CanonicalProductCandidateModel).where(
                CanonicalProductCandidateModel.review_required == True
            )
            
            if sort_by == "ambiguity_desc":
                stmt = stmt.order_by(desc(CanonicalProductCandidateModel.updated_at)) # We can sort by updated_at or ambiguity flags length
            else:
                stmt = stmt.order_by(desc(CanonicalProductCandidateModel.updated_at))
                
            stmt = stmt.limit(limit).offset(offset)
            records = session.execute(stmt).scalars().all()
            
            items = []
            for r in records:
                items.append(ReviewQueueItem(
                    candidate_id=r.candidate_id,
                    canonical_title=r.canonical_title,
                    source_count=r.source_count,
                    review_status=ReviewStatus.PENDING,
                    ambiguity_severity=len(r.ambiguity_flags_json or []),
                    updated_at=r.updated_at,
                    brand=r.canonical_brand,
                    model=r.canonical_model,
                    ambiguity_flags=r.ambiguity_flags_json or [],
                    pending_sources_count=r.source_count
                ))
            return items

    def get_candidate_compare_view(self, candidate_id: str) -> Optional[CandidateCompareView]:
        with self.session_manager.session() as session:
            cand = session.execute(
                select(CanonicalProductCandidateModel).where(CanonicalProductCandidateModel.candidate_id == candidate_id)
            ).scalar_one_or_none()
            
            if not cand:
                return None
                
            view = CandidateCompareView(
                candidate_id=cand.candidate_id,
                canonical_title=cand.canonical_title,
                review_status=ReviewStatus.PENDING if cand.review_required else ReviewStatus.APPROVED,
                canonical_brand=cand.canonical_brand,
                canonical_model=cand.canonical_model,
                canonical_mpn=cand.canonical_mpn,
                candidate_variation_signature=cand.variation_signature,
                candidate_bundle_signature=cand.bundle_signature
            )
            
            # Fetch Evidences and Sources
            evidences = session.execute(
                select(MatchEvidenceModel, NormalizedSourceItemModel)
                .join(NormalizedSourceItemModel, MatchEvidenceModel.normalized_item_id == NormalizedSourceItemModel.normalized_item_id)
                .where(MatchEvidenceModel.candidate_id == candidate_id)
            ).all()
            
            for ev, src in evidences:
                view.sources.append(SourceCompareItem(
                    source_item_id=src.source_item_id,
                    normalized_title=src.normalized_title,
                    raw_title=src.normalized_title, # For UI
                    match_confidence=cand.match_confidence,
                    variation_penalty=ev.variation_penalty,
                    bundle_penalty=ev.bundle_penalty,
                    ambiguity_flags=ev.ambiguity_flags_json or [],
                    explanation_lines=ev.explanation_lines_json or [],
                    variation_keys=src.variation_keys_json or {},
                    bundle_flags=src.bundle_flags_json or []
                ))
                
            # Fetch Audit Logs
            logs = session.execute(
                select(ReviewAuditLogModel).where(ReviewAuditLogModel.candidate_id == candidate_id).order_by(desc(ReviewAuditLogModel.created_at))
            ).scalars().all()
            
            for log in logs:
                view.audit_history.append(ReviewDecisionRecord(
                    decision_id=log.decision_id,
                    candidate_id=log.candidate_id,
                    actor=log.actor,
                    action=log.action,
                    reason=log.reason,
                    target_alias=log.target_alias,
                    timestamp=log.created_at
                ))
                
            # Check if split recommended
            if any("conflict" in str(f).lower() for src in view.sources for f in src.ambiguity_flags):
                view.split_recommended = True
                view.split_reason = "Variation or Bundle Conflict detected in sources."
                
            return view

    def update_review_status(self, candidate_id: str, status: ReviewStatus):
        # We handle PENDING status with the `review_required` boolean
        pass # Status is mostly boolean mapping currently

    def clear_review_required_flag(self, candidate_id: str):
        with self.session_manager.session() as session:
            cand = session.execute(
                select(CanonicalProductCandidateModel).where(CanonicalProductCandidateModel.candidate_id == candidate_id)
            ).scalar_one_or_none()
            if cand:
                cand.review_required = False
            session.commit()

    def set_review_required_flag(self, candidate_id: str):
        with self.session_manager.session() as session:
            cand = session.execute(
                select(CanonicalProductCandidateModel).where(CanonicalProductCandidateModel.candidate_id == candidate_id)
            ).scalar_one_or_none()
            if cand:
                cand.review_required = True
            session.commit()

class PersistentReviewAuditRepository:
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()
        
    def save_audit_record(self, record: ReviewDecisionRecord):
        with self.session_manager.session() as session:
            db_record = ReviewAuditLogModel(
                decision_id=record.decision_id,
                candidate_id=record.candidate_id,
                actor=record.actor,
                action=record.action,
                reason=record.reason,
                target_alias=record.target_alias,
                created_at=record.timestamp
            )
            session.add(db_record)
            session.commit()
