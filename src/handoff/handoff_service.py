import uuid
from datetime import datetime
from typing import List, Any, Optional

from src.handoff.config import HandoffSettings
from src.handoff.models import (
    HandoffInput, HandoffResult, HandoffStatus, HandoffDecision, 
    DispatchTarget, HandoffAttempt, HandoffTransition, FailureClassification
)
from src.handoff.eligibility_validator import EligibilityValidator
from src.handoff.duplicate_guard import DuplicateGuard
from src.handoff.capacity_controller import CapacityController
from src.handoff.cooldown_policy import CooldownPolicy
from src.handoff.retry_policy import RetryPolicy
from src.handoff.state_machine import StateMachine
from src.handoff.execution_dispatch_gateway import ExecutionDispatchGateway
from src.handoff.mock_execution_dispatch_gateway import MockExecutionDispatchGateway

class HandoffService:
    def __init__(self, settings: HandoffSettings, gateway: Optional[ExecutionDispatchGateway] = None):
        self.settings = settings
        self.validator = EligibilityValidator(settings)
        self.duplicate_guard = DuplicateGuard(settings)
        self.capacity_controller = CapacityController(settings)
        self.cooldown_policy = CooldownPolicy(settings)
        self.retry_policy = RetryPolicy(settings)
        self.state_machine = StateMachine()
        self.gateway = gateway or (MockExecutionDispatchGateway() if settings.use_mock_gateway else None)
        
    def process_handoff(
        self, 
        input_data: HandoffInput, 
        existing_handoffs: List[Any], 
        run_handoff_count: int, 
        seller_active_execution_count: int,
        last_seller_execution_at: Optional[datetime] = None,
        now: datetime = None,
        existing_handoff_id: Optional[str] = None, # Used for retries
        current_attempt_count: int = 0
    ) -> HandoffResult:
        if now is None:
            now = datetime.utcnow()
            
        handoff_id = existing_handoff_id or f"hoff_{uuid.uuid4().hex[:12]}"
        attempt_id = f"att_{uuid.uuid4().hex[:8]}"
        explanation_lines: List[str] = []
        
        result = HandoffResult(
            handoff_id=handoff_id,
            candidate_id=input_data.candidate_id,
            ranking_decision_id=input_data.ranking_decision_id,
            seller_account_id=input_data.seller_account_id,
            environment=input_data.environment,
            handoff_status=HandoffStatus.PENDING,
            handoff_decision=HandoffDecision.DEFER, # Default safe state
            dispatch_target=DispatchTarget.MOCK if self.settings.use_mock_gateway else DispatchTarget.LIVE_READINESS,
            created_at=now,
            updated_at=now
        )
        
        # Track transitions locally for the service run
        transitions: List[HandoffTransition] = []
        
        def _transition(to_status: HandoffStatus, reason: str):
            _, result.handoff_status, t = self.state_machine.transition(result.handoff_status, to_status, reason)
            transitions.append(t)
            explanation_lines.append(f"State transition: -> {to_status.value} ({reason})")

        _transition(HandoffStatus.CLAIMED, "Handoff process started")
        
        # 1. Eligibility Validation
        val_res = self.validator.validate(input_data)
        if not val_res.is_valid:
            result.block_reasons.extend(val_res.block_reasons)
            _transition(HandoffStatus.REJECTED, "Failed eligibility validation")
            result.handoff_decision = HandoffDecision.REJECT_HANDOFF
            result.explanation_lines = explanation_lines
            return result
            
        # 2. Duplicate Guard
        # Only check duplicate if it's a new handoff (not a retry attempt)
        if not existing_handoff_id:
            dup_res = self.duplicate_guard.check_duplicates(input_data, existing_handoffs, now)
            if dup_res.duplicate_suppressed:
                result.duplicate_suppressed = True
                result.block_reasons.append(dup_res.duplicate_reason)
                _transition(HandoffStatus.REJECTED, "Duplicate suppressed")
                result.handoff_decision = HandoffDecision.REJECT_HANDOFF
                result.explanation_lines = explanation_lines
                return result
                
        # 3. Cooldown Check
        in_cooldown, next_cooldown_retry, cd_reason = self.cooldown_policy.check_cooldown(last_seller_execution_at, now)
        if in_cooldown:
            result.deferred = True
            result.next_retry_at = next_cooldown_retry
            result.block_reasons.append(cd_reason)
            _transition(HandoffStatus.DEFERRED, "Seller in cooldown")
            result.handoff_decision = HandoffDecision.DEFER
            result.explanation_lines = explanation_lines
            return result
            
        # 4. Capacity Check
        cap_allowed, should_defer, cap_reason = self.capacity_controller.check_capacity(run_handoff_count, seller_active_execution_count)
        if not cap_allowed:
            result.block_reasons.append(cap_reason)
            if should_defer:
                result.deferred = True
                _transition(HandoffStatus.DEFERRED, "Capacity full")
                result.handoff_decision = HandoffDecision.DEFER
            else:
                _transition(HandoffStatus.REJECTED, "Capacity full and defer disabled")
                result.handoff_decision = HandoffDecision.REJECT_HANDOFF
            result.explanation_lines = explanation_lines
            return result
            
        _transition(HandoffStatus.VALIDATED, "All guards passed")
        
        # 5. Dispatch
        if not self.gateway:
            raise RuntimeError("Execution Dispatch Gateway is not configured.")
            
        _transition(HandoffStatus.DISPATCHED, "Dispatching to execution layer")
        
        dispatch_success, error_code, error_summary = self.gateway.dispatch(handoff_id, input_data)
        
        if dispatch_success:
            _transition(HandoffStatus.ACCEPTED, "Accepted by execution layer")
            # Usually downstream layer moves it to completed, but we mock it here.
            _transition(HandoffStatus.COMPLETED, "Handoff successful")
            result.execution_allowed = True
            result.handoff_decision = HandoffDecision.DISPATCH_NOW
            result.explanation_lines = explanation_lines
            return result
            
        # 6. Failure & Retry Handling
        _transition(HandoffStatus.FAILED, f"Dispatch failed: {error_code} - {error_summary}")
        result.failure_reason = f"[{error_code}] {error_summary}"
        
        retryable, exhausted, next_retry_at, failure_class = self.retry_policy.evaluate_failure(error_code, current_attempt_count + 1, now)
        result.retryable = retryable and not exhausted
        
        if result.retryable:
            result.next_retry_at = next_retry_at
            result.deferred = True
            _transition(HandoffStatus.DEFERRED, "Retryable failure. Deferred for next attempt.")
            result.handoff_decision = HandoffDecision.RETRY_LATER
        else:
            reason = "Retry attempts exhausted." if exhausted else "Non-retryable failure."
            _transition(HandoffStatus.REJECTED, f"{reason} Rejecting handoff.")
            result.handoff_decision = HandoffDecision.REJECT_HANDOFF
            
        result.explanation_lines = explanation_lines
        return result
