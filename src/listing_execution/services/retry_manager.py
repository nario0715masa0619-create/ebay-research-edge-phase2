from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone

class FailureBoundary(str, Enum):
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN = "UNKNOWN"
    SELLER_LIMIT = "SELLER_LIMIT"
    STATE_CONFLICT = "STATE_CONFLICT"

class RetryAction(str, Enum):
    RETRY_LATER = "RETRY_LATER"
    DEFER = "DEFER"
    CANCEL = "CANCEL"

@dataclass
class RetryDecision:
    action: RetryAction
    reason: str
    next_retry_at: Optional[datetime] = None
    next_attempt_number: Optional[int] = None

class ExecutionRetryManager:
    """
    Manages failure classification, backoff calculation, and retry scheduling 
    for the execution layer.
    """
    MAX_ATTEMPTS = 3
    BASE_BACKOFF_SECONDS = 1.0

    def classify_failure(self, error_message: str) -> FailureBoundary:
        error_lower = error_message.lower()
        if "timeout" in error_lower:
            return FailureBoundary.TIMEOUT
        if "network" in error_lower or "connection" in error_lower:
            return FailureBoundary.NETWORK_ERROR
        if "limit" in error_lower or "capacity" in error_lower:
            return FailureBoundary.SELLER_LIMIT
        if "duplicate" in error_lower or "conflict" in error_lower or "invalid state" in error_lower:
            return FailureBoundary.STATE_CONFLICT
        return FailureBoundary.UNKNOWN

    def evaluate_failure(self, error_message: str, attempt_number: int) -> RetryDecision:
        boundary = self.classify_failure(error_message)

        if boundary in (FailureBoundary.SELLER_LIMIT,):
            return RetryDecision(
                action=RetryAction.DEFER,
                reason="Seller limit reached or capacity full. Deferring execution."
            )

        if boundary in (FailureBoundary.STATE_CONFLICT,):
            return RetryDecision(
                action=RetryAction.CANCEL,
                reason="State conflict or non-retryable error. Cancelling execution."
            )

        # Retryable cases (TIMEOUT, NETWORK_ERROR, UNKNOWN)
        if attempt_number >= self.MAX_ATTEMPTS:
            return RetryDecision(
                action=RetryAction.CANCEL,
                reason=f"Retry limit exhausted after {attempt_number} attempts."
            )

        # Calculate backoff
        # next_retry_at = now + base * (2 ^ (attempt_number - 1))
        backoff_seconds = self.BASE_BACKOFF_SECONDS * (2 ** (attempt_number - 1))
        next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
        
        return RetryDecision(
            action=RetryAction.RETRY_LATER,
            reason=f"Transient error ({boundary.value}). Scheduling retry.",
            next_retry_at=next_retry_at,
            next_attempt_number=attempt_number + 1
        )

    def prepare_next_attempt(self, listing_id: str, current_attempt_id: str, next_attempt_number: int) -> str:
        """
        Creates a completely new attempt_id to enforce idempotency strictly per-attempt,
        meaning state is not reverted but rather the flow proceeds forward with a new attempt.
        """
        # A simple deterministic or random generation. Here we use deterministic string concat for simplicity.
        return f"{listing_id}_att_{next_attempt_number}"

    def safely_rollback_execution_scope(self, state_machine, attempt_id: str, reason: str):
        """
        Executes a safe rollback that is strictly bounded to the execution scope.
        It does NOT revert ranking, profitability, or the listing itself.
        It simply transitions the ExecutionStateMachine to rolled_back.
        """
        # Call the rollback method of the ExecutionStateMachine which audits the transition
        state_machine.rollback(reason=f"[Attempt: {attempt_id}] {reason}")
