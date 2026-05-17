import logging
from ..models import NotificationEvent, NotificationDispatchResult
from ..channel_registry import BaseNotifier

logger = logging.getLogger(__name__)

class ConsoleNotifier(BaseNotifier):
    def send(self, event: NotificationEvent) -> NotificationDispatchResult:
        severity_tag = f"[{event.severity.upper()}]"
        print(f"\n--- NOTIFICATION {severity_tag} ---")
        print(f"Title: {event.title}")
        print(f"Summary: {event.summary or '-'}")
        if event.sku: print(f"SKU: {event.sku}")
        if event.source_run_id: print(f"RunID: {event.source_run_id}")
        if event.details: print(f"Details: {event.details}")
        print(f"Occurred: {event.emitted_at.isoformat()}")
        print("---------------------------------\n")
        
        return NotificationDispatchResult(
            event_id=event.event_id,
            channel_name="console",
            dispatch_status="success",
            success_flag=True
        )
