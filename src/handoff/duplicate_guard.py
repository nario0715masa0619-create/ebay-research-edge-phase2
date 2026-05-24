from datetime import datetime, timezone
from typing import List, Any
from src.handoff.models import DuplicateCheckResult, HandoffInput, HandoffStatus
from src.handoff.config import HandoffSettings

class DuplicateGuard:
    def __init__(self, settings: HandoffSettings):
        self.settings = settings
        
    def check_duplicates(self, input_data: HandoffInput, existing_handoffs: List[Any], now: datetime = None) -> DuplicateCheckResult:
        """
        Check against existing handoffs for the same candidate + seller + environment.
        existing_handoffs should be ordered by created_at DESC.
        """
        if now is None:
            now = datetime.utcnow()
            
        result = DuplicateCheckResult()
        
        if not existing_handoffs:
            return result
            
        for h in existing_handoffs:
            # 1. State-based Hard Block
            active_states = [
                HandoffStatus.PENDING.value,
                HandoffStatus.CLAIMED.value,
                HandoffStatus.VALIDATED.value,
                HandoffStatus.DISPATCHED.value,
                HandoffStatus.ACCEPTED.value,
                HandoffStatus.DEFERRED.value
            ]
            if h.handoff_status in active_states:
                result.is_duplicate = True
                result.duplicate_suppressed = True
                result.duplicate_reason = f"Active handoff already exists in state '{h.handoff_status}'."
                result.existing_handoff_ref = h.handoff_id
                return result
                
            # 2. Time-window Suppression
            # If there's a recent handoff, block it (unless it was cancelled or failed and we are retrying as attempt)
            # Wait, if we are here, it means we are creating a *new* handoff request for the same candidate.
            # Retry logic handles appending attempts to the *same* handoff.
            # So a *new* handoff within the suppression window is suppressed.
            
            created_at = h.created_at.replace(tzinfo=timezone.utc) if h.created_at.tzinfo is None else h.created_at
            now_aware = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
            
            elapsed_seconds = (now_aware - created_at).total_seconds()
            if elapsed_seconds < self.settings.duplicate_suppression_window_seconds:
                # If it's a completely terminal status like COMPLETED, it's still suppressed to prevent double-listing
                if h.handoff_status == HandoffStatus.COMPLETED.value:
                    result.is_duplicate = True
                    result.duplicate_suppressed = True
                    result.duplicate_reason = f"Already completed handoff within suppression window ({int(elapsed_seconds)}s ago)."
                    result.existing_handoff_ref = h.handoff_id
                    return result
                    
                # If it's FAILED or REJECTED, do we allow a new handoff? 
                # Policy says "time-window suppression", so we generally suppress it to prevent thrashing.
                # Manual force override would bypass this guard entirely at the service level.
                result.is_duplicate = True
                result.duplicate_suppressed = True
                result.duplicate_reason = f"Recent handoff ({h.handoff_status}) exists within suppression window."
                result.existing_handoff_ref = h.handoff_id
                return result

        return result
