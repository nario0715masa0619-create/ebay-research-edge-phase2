import json
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from src.handoff.models import HandoffResult, HandoffAttempt, HandoffTransition, HandoffStatus, HandoffDecision, DispatchTarget
from src.db.models import ListingHandoffModel, ListingHandoffAttemptModel, ListingHandoffTransitionModel

class PersistentHandoffRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def _to_domain(self, model: ListingHandoffModel) -> HandoffResult:
        return HandoffResult(
            handoff_id=model.handoff_id,
            candidate_id=model.candidate_id,
            ranking_decision_id=model.ranking_decision_id or "",
            seller_account_id=model.seller_account_id,
            environment=model.environment,
            handoff_status=HandoffStatus(model.handoff_status),
            handoff_decision=HandoffDecision(model.handoff_decision),
            execution_allowed=model.execution_allowed,
            dispatch_target=DispatchTarget(model.dispatch_target),
            batch_id=model.batch_id,
            idempotency_key=model.idempotency_key,
            duplicate_suppressed=model.duplicate_suppressed,
            deferred=model.deferred,
            retryable=model.retryable,
            block_reasons=model.block_reasons_json,
            failure_reason=model.failure_reason or "",
            next_retry_at=model.next_retry_at,
            explanation_lines=model.explanation_lines_json,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def upsert_handoff(self, result: HandoffResult):
        stmt = select(ListingHandoffModel).where(ListingHandoffModel.handoff_id == result.handoff_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        
        if not model:
            model = ListingHandoffModel(handoff_id=result.handoff_id)
            self.session.add(model)
            
        model.candidate_id = result.candidate_id
        model.ranking_decision_id = result.ranking_decision_id
        model.seller_account_id = result.seller_account_id
        model.environment = result.environment
        model.handoff_status = result.handoff_status.value
        model.handoff_decision = result.handoff_decision.value
        model.execution_allowed = result.execution_allowed
        model.dispatch_target = result.dispatch_target.value
        model.batch_id = result.batch_id
        model.idempotency_key = result.idempotency_key
        model.duplicate_suppressed = result.duplicate_suppressed
        model.deferred = result.deferred
        model.retryable = result.retryable
        model.block_reasons_json = result.block_reasons
        model.failure_reason = result.failure_reason
        model.next_retry_at = result.next_retry_at
        model.explanation_lines_json = result.explanation_lines
        
        self.session.commit()

    def append_transitions(self, handoff_id: str, transitions: List[HandoffTransition]):
        if not transitions:
            return
            
        for t in transitions:
            model = ListingHandoffTransitionModel(
                handoff_id=handoff_id,
                from_status=t.from_status,
                to_status=t.to_status,
                transition_reason=t.transition_reason,
                actor=t.actor,
                occurred_at=t.occurred_at
            )
            self.session.add(model)
        self.session.commit()
        
    def append_attempt(self, attempt: HandoffAttempt):
        stmt = select(ListingHandoffAttemptModel).where(ListingHandoffAttemptModel.attempt_id == attempt.attempt_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        
        if not model:
            model = ListingHandoffAttemptModel(
                attempt_id=attempt.attempt_id,
                handoff_id=attempt.handoff_id,
                attempt_number=attempt.attempt_number,
                started_at=attempt.started_at
            )
            self.session.add(model)
            
        model.attempt_status = attempt.attempt_status
        model.error_code = attempt.error_code
        model.error_summary = attempt.error_summary
        model.finished_at = attempt.finished_at
        
        self.session.commit()

    def get_by_id(self, handoff_id: str) -> Optional[HandoffResult]:
        stmt = select(ListingHandoffModel).where(ListingHandoffModel.handoff_id == handoff_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def find_recent_by_candidate(self, candidate_id: str, seller_account_id: str, environment: str) -> List[HandoffResult]:
        """
        Used for duplicate suppression. Returns recent handoffs for the candidate.
        Ordered by created_at DESC.
        """
        stmt = select(ListingHandoffModel).where(
            and_(
                ListingHandoffModel.candidate_id == candidate_id,
                ListingHandoffModel.seller_account_id == seller_account_id,
                ListingHandoffModel.environment == environment
            )
        ).order_by(desc(ListingHandoffModel.created_at)).limit(10)
        
        models = self.session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]
        
    def count_recent_dispatched_by_run(self, batch_id: str) -> int:
        # Simple count for current batch/run capacity
        if not batch_id:
            return 0
        stmt = select(ListingHandoffModel).where(
            and_(
                ListingHandoffModel.batch_id == batch_id,
                ListingHandoffModel.handoff_decision == HandoffDecision.DISPATCH_NOW.value
            )
        )
        return len(self.session.execute(stmt).scalars().all())

    def get_seller_active_execution_count(self, seller_account_id: str, environment: str) -> int:
        active_states = [HandoffStatus.PENDING.value, HandoffStatus.CLAIMED.value, HandoffStatus.VALIDATED.value, HandoffStatus.DISPATCHED.value, HandoffStatus.ACCEPTED.value]
        stmt = select(ListingHandoffModel).where(
            and_(
                ListingHandoffModel.seller_account_id == seller_account_id,
                ListingHandoffModel.environment == environment,
                ListingHandoffModel.handoff_status.in_(active_states)
            )
        )
        return len(self.session.execute(stmt).scalars().all())
