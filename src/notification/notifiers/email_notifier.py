import logging
from ..models import NotificationEvent, NotificationDispatchResult
from ..channel_registry import BaseNotifier
from ..template_renderer import NotificationTemplateRenderer

logger = logging.getLogger(__name__)

class EmailNotifier(BaseNotifier):
    def __init__(self, from_email: str, to_emails: list):
        self.from_email = from_email
        self.to_emails = to_emails
        self.renderer = NotificationTemplateRenderer()

    def send(self, event: NotificationEvent) -> NotificationDispatchResult:
        if not self.to_emails:
            return NotificationDispatchResult(
                event_id=event.event_id,
                channel_name="email",
                dispatch_status="skipped",
                skipped_reason="No recipients configured",
                success_flag=True
            )
            
        body = self.renderer.render_plain(event)
        
        # In v0.1 we just log
        logger.info(f"EMAIL NOTIFICATION (Simulated): From: {self.from_email}, To: {self.to_emails}\nSubject: {event.title}\n{body}")
        
        return NotificationDispatchResult(
            event_id=event.event_id,
            channel_name="email",
            dispatch_status="success",
            success_flag=True
        )
