import logging
from typing import List, Dict, Any
from src.escalation.models import EscalationState, EscalationPolicy
from src.notification.models import NotificationEvent
from src.notification.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)

class EscalationDispatcher:
    def __init__(self, notification_dispatcher: NotificationDispatcher):
        self.notification_dispatcher = notification_dispatcher

    def dispatch(
        self,
        state: EscalationState,
        policy: EscalationPolicy,
        target_level: int,
        target_channels: List[str],
        target_severity: str,
        target_priority: str,
        dry_run: bool = False,
        is_re_escalation: bool = False
    ) -> List[str]:
        event_type = f"{state.source_event_type}_escalation"
        
        prefix = "[RE-ESCALATED]" if is_re_escalation else "[ESCALATED]"
        title = f"{prefix} {state.source_event_type} - {target_severity.upper()} (Level {target_level})"
        summary = f"{prefix} Level {target_level} triggered for unresolved issue: {state.dedupe_key}"
        
        # Build meta to show it is escalation-derived
        meta = {
            "is_escalation_reminder": True,
            "escalation_state_id": state.state_id,
            "original_event_id": state.source_event_id,
            "escalation_level": target_level,
            "policy_id": policy.policy_id
        }
        meta.update(state.meta_json)

        event = NotificationEvent(
            event_type=event_type,
            title=title,
            summary=summary,
            source_layer="escalation",
            source_component="escalation_dispatcher",
            sku=state.sku,
            severity=target_severity,
            priority=target_priority,
            meta_json=meta,
            seller_account_id=state.seller_account_id,
            environment_type=state.environment_type
        )

        logger.info(f"Dispatching escalation alert for state {state.state_id} (Level {target_level}) to channels {target_channels}")
        
        # Bypassing rule-based filters since this is a metered system escalation event
        batch_res = self.notification_dispatcher.notify(event, dry_run=dry_run, bypass_checks=True)
        
        # Gather successful channels
        channels = [r.channel_name for r in batch_res.results if r.success_flag]
        return channels
