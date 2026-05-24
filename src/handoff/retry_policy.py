from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from src.handoff.config import HandoffSettings
from src.handoff.models import FailureClassification

class RetryPolicy:
    def __init__(self, settings: HandoffSettings):
        self.settings = settings

    def evaluate_failure(self, error_code: str, attempt_count: int, now: datetime = None) -> Tuple[bool, bool, Optional[datetime], FailureClassification]:
        """
        Returns:
            Tuple[retryable, retry_exhausted, next_retry_at, failure_classification]
        """
        if now is None:
            now = datetime.utcnow()
            
        now_aware = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
        
        # 1. Classify Failure
        classification = self._classify_error(error_code)
        
        if classification == FailureClassification.NON_RETRYABLE:
            return False, False, None, classification
            
        # 2. Check Attempt Limit
        if attempt_count >= self.settings.retry_max_attempts:
            return True, True, None, classification
            
        # 3. Calculate Backoff
        # Simple exponential backoff: base * (2 ^ attempt_count)
        backoff_seconds = self.settings.retry_backoff_seconds * (2 ** attempt_count)
        
        # Rate limits might have a specific fixed wait, but for now we use exponential backoff
        if classification == FailureClassification.RATE_LIMIT:
            # We could parse headers here, but simple fallback is fine
            backoff_seconds = max(backoff_seconds, 300) # Ensure at least 5 mins
            
        next_retry_at = now_aware + timedelta(seconds=backoff_seconds)
        
        return True, False, next_retry_at, classification

    def _classify_error(self, error_code: str) -> FailureClassification:
        error_code_lower = error_code.lower()
        
        if "rate_limit" in error_code_lower or "429" in error_code_lower:
            return FailureClassification.RATE_LIMIT
            
        if "timeout" in error_code_lower or "502" in error_code_lower or "503" in error_code_lower or "transient" in error_code_lower:
            return FailureClassification.TRANSIENT
            
        if "invalid_payload" in error_code_lower or "policy_block" in error_code_lower or "400" in error_code_lower or "auth_failure" in error_code_lower:
            return FailureClassification.NON_RETRYABLE
            
        # Default to transient for unknown errors to be safe
        return FailureClassification.TRANSIENT
