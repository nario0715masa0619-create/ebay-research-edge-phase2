from typing import List, Tuple
from src.handoff.models import HandoffStatus, HandoffTransition

class StateMachine:
    def __init__(self):
        # Define allowed transitions
        # format: from_state -> list[to_state]
        self._transitions = {
            HandoffStatus.PENDING: [HandoffStatus.CLAIMED, HandoffStatus.CANCELLED],
            HandoffStatus.CLAIMED: [HandoffStatus.VALIDATED, HandoffStatus.REJECTED, HandoffStatus.DEFERRED, HandoffStatus.CANCELLED],
            HandoffStatus.VALIDATED: [HandoffStatus.DISPATCHED, HandoffStatus.CANCELLED, HandoffStatus.DEFERRED], # Can be deferred due to capacity
            HandoffStatus.DISPATCHED: [HandoffStatus.ACCEPTED, HandoffStatus.FAILED],
            HandoffStatus.FAILED: [HandoffStatus.DEFERRED, HandoffStatus.REJECTED], # Deferred if retryable
            HandoffStatus.DEFERRED: [HandoffStatus.PENDING, HandoffStatus.CANCELLED], # Wake up to pending
            HandoffStatus.ACCEPTED: [HandoffStatus.COMPLETED],
            
            # Terminal states
            HandoffStatus.COMPLETED: [],
            HandoffStatus.REJECTED: [],
            HandoffStatus.CANCELLED: []
        }
        
    def can_transition(self, current_status: HandoffStatus, new_status: HandoffStatus) -> bool:
        if current_status == new_status:
            return True # Trivial transition
        allowed_next_states = self._transitions.get(current_status, [])
        return new_status in allowed_next_states
        
    def transition(self, current_status: HandoffStatus, new_status: HandoffStatus, reason: str, actor: str = "system") -> Tuple[bool, HandoffStatus, HandoffTransition]:
        """
        Returns (success, final_status, transition_record)
        """
        if current_status == new_status:
            # Create a self-transition record just for audit, but it's optional
            transition = HandoffTransition(
                from_status=current_status.value,
                to_status=new_status.value,
                transition_reason=reason,
                actor=actor
            )
            return True, current_status, transition
            
        if not self.can_transition(current_status, new_status):
            raise ValueError(f"Invalid state transition from {current_status.value} to {new_status.value}")
            
        transition = HandoffTransition(
            from_status=current_status.value,
            to_status=new_status.value,
            transition_reason=reason,
            actor=actor
        )
        
        return True, new_status, transition
