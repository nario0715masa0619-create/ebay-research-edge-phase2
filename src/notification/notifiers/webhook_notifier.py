import logging
import json
from ..models import NotificationEvent, NotificationDispatchResult
from ..channel_registry import BaseNotifier

logger = logging.getLogger(__name__)

class WebhookNotifier(BaseNotifier):
    def __init__(self, url: str):
        self.url = url

    def send(self, event: NotificationEvent) -> NotificationDispatchResult:
        if not self.url:
            return NotificationDispatchResult(
                event_id=event.event_id,
                channel_name="webhook",
                dispatch_status="skipped",
                skipped_reason="URL not configured",
                success_flag=True
            )
            
        payload = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "severity": event.severity,
            "title": event.title,
            "summary": event.summary,
            "sku": event.sku,
            "timestamp": event.emitted_at.isoformat()
        }
        
        # In v0.1 we just log
        logger.info(f"WEBHOOK NOTIFICATION (Simulated): POST {self.url}\nPayload: {json.dumps(payload)}")
        
        return NotificationDispatchResult(
            event_id=event.event_id,
            channel_name="webhook",
            dispatch_status="success",
            success_flag=True
        )
