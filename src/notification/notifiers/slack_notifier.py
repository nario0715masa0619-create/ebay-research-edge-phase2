import logging
import json
from ..models import NotificationEvent, NotificationDispatchResult
from ..channel_registry import BaseNotifier

logger = logging.getLogger(__name__)

class SlackNotifier(BaseNotifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, event: NotificationEvent) -> NotificationDispatchResult:
        if not self.webhook_url:
            return NotificationDispatchResult(
                event_id=event.event_id,
                channel_name="slack",
                dispatch_status="failed",
                error_summary="Webhook URL not configured",
                success_flag=False
            )
            
        # Simplified Slack payload
        payload = {
            "text": f"*{event.severity.upper()}*: {event.title}\n{event.summary or ''}\n_RunID: {event.source_run_id or '-'}_"
        }
        
        # In v0.1 we might use requests if available, or just log for now
        logger.info(f"SLACK NOTIFICATION (Simulated): {json.dumps(payload)}")
        
        return NotificationDispatchResult(
            event_id=event.event_id,
            channel_name="slack",
            dispatch_status="success",
            success_flag=True
        )
