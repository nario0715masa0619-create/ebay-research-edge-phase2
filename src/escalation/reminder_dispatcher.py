import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.escalation.models import EscalationState, EscalationPolicy
from src.notification.models import NotificationEvent
from src.notification.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)

class ReminderDispatcher:
    def __init__(self, notification_dispatcher: NotificationDispatcher):
        self.notification_dispatcher = notification_dispatcher

    def dispatch(
        self,
        state: EscalationState,
        policy: EscalationPolicy,
        dry_run: bool = False
    ) -> List[str]:
        event_type = f"{state.source_event_type}_reminder"
        title = f"[REMINDER] {state.source_event_type} - {state.current_severity.upper()}"
        summary = f"Reminder #{state.reminder_count + 1} for unresolved issue: {state.dedupe_key}"
        
        # Build meta to show it is reminder-derived
        meta = {
            "is_escalation_reminder": True,
            "escalation_state_id": state.state_id,
            "original_event_id": state.source_event_id,
            "reminder_count": state.reminder_count + 1,
            "policy_id": policy.policy_id
        }
        meta.update(state.meta_json)

        event = NotificationEvent(
            event_type=event_type,
            title=title,
            summary=summary,
            source_layer="escalation",
            source_component="reminder_dispatcher",
            sku=state.sku,
            severity=state.current_severity,
            priority=state.current_priority,
            meta_json=meta,
            seller_account_id=state.seller_account_id,
            environment_type=state.environment_type
        )

        logger.info(f"Dispatching reminder alert for state {state.state_id} (Dedupe: {state.dedupe_key})")
        
        # Bypassing rule-based dedupe/cooldown filters to ensure reminder reaches the operator
        batch_res = self.notification_dispatcher.notify(event, dry_run=dry_run, bypass_checks=True)
        
        # Gather successful channels
        channels = [r.channel_name for r in batch_res.results if r.success_flag]
        return channels
