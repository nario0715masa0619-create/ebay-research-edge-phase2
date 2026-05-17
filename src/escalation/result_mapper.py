import logging
from datetime import datetime
from src.escalation.models import (
    EscalationState,
    ReminderExecutionResult,
    EscalationExecutionResult
)
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository

logger = logging.getLogger(__name__)

class EscalationResultMapper:
    def __init__(self, state_repo: PersistentEscalationStateRepository):
        self.state_repo = state_repo

    def map_reminder_result(
        self,
        state: EscalationState,
        result: ReminderExecutionResult,
        now: datetime
    ) -> None:
        if result.decision != "remind":
            return

        logger.info(f"Persisting reminder result for state {state.state_id}. New count: {result.reminder_count_after}")
        
        self.state_repo.increment_reminder_count(
            state_id=state.state_id,
            new_count=result.reminder_count_after,
            last_notified_at=now
        )
        
        # Append an audit log of transition for reminder
        self.state_repo.append_transition(
            state_id=state.state_id,
            action_type="reminder_sent",
            previous_status=state.current_status,
            new_status=state.current_status,
            actor_type="system",
            actor_id="escalation_runner",
            note=f"Issued reminder #{result.reminder_count_after} to channels: {', '.join(result.dispatched_channels)}"
        )

    def map_escalation_result(
        self,
        state: EscalationState,
        result: EscalationExecutionResult,
        target_severity: str,
        target_priority: str,
        now: datetime
    ) -> None:
        if result.decision != "escalate":
            return

        logger.info(f"Persisting escalation result for state {state.state_id}. New level: {result.escalation_level_after}")

        self.state_repo.set_escalation_level(
            state_id=state.state_id,
            new_level=result.escalation_level_after,
            last_escalated_at=now,
            target_severity=target_severity,
            target_priority=target_priority
        )
