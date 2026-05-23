from typing import Optional
from src.discovery.review_models import ReviewStatus, ReviewDecisionRecord
import uuid

class ReviewDecisionService:
    """
    Handles state mutations for the Review Queue and ensures audit trails are created.
    """
    
    def __init__(self, review_repo, audit_repo):
        self.review_repo = review_repo
        self.audit_repo = audit_repo
        
    def _record_audit(self, candidate_id: str, actor: str, action: str, reason: Optional[str] = None):
        record = ReviewDecisionRecord(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            candidate_id=candidate_id,
            actor=actor,
            action=action,
            reason=reason
        )
        self.audit_repo.save_audit_record(record)
        return record

    def approve(self, candidate_id: str, actor: str, note: Optional[str] = None) -> ReviewDecisionRecord:
        self.review_repo.update_review_status(candidate_id, ReviewStatus.APPROVED)
        self.review_repo.clear_review_required_flag(candidate_id)
        return self._record_audit(candidate_id, actor, "approve", note)
        
    def reject(self, candidate_id: str, actor: str, note: Optional[str] = None) -> ReviewDecisionRecord:
        self.review_repo.update_review_status(candidate_id, ReviewStatus.REJECTED)
        return self._record_audit(candidate_id, actor, "reject", note)
        
    def hold(self, candidate_id: str, actor: str, note: Optional[str] = None) -> ReviewDecisionRecord:
        self.review_repo.update_review_status(candidate_id, ReviewStatus.HOLD)
        return self._record_audit(candidate_id, actor, "hold", note)
        
    def reopen(self, candidate_id: str, actor: str, note: Optional[str] = None) -> ReviewDecisionRecord:
        self.review_repo.update_review_status(candidate_id, ReviewStatus.PENDING)
        self.review_repo.set_review_required_flag(candidate_id)
        return self._record_audit(candidate_id, actor, "reopen", note)
        
    def add_note(self, candidate_id: str, actor: str, note: str) -> ReviewDecisionRecord:
        return self._record_audit(candidate_id, actor, "note", note)
