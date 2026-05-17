from .models import NotificationEvent

class NotificationTemplateRenderer:
    def render_plain(self, event: NotificationEvent) -> str:
        body = f"[{event.severity.upper()}] {event.title}\n"
        if event.summary:
            body += f"Summary: {event.summary}\n"
        if event.sku:
            body += f"SKU: {event.sku}\n"
        if event.source_run_id:
            body += f"RunID: {event.source_run_id}\n"
        if event.details:
            body += f"\nDetails:\n{event.details}\n"
        
        body += f"\nTime: {event.emitted_at.isoformat()}\n"
        body += f"Source: {event.source_layer}.{event.source_component or 'unknown'}"
        return body

    def render_html(self, event: NotificationEvent) -> str:
        # Placeholder for HTML rendering
        return f"<h3>{event.title}</h3><p>{event.summary}</p>"
