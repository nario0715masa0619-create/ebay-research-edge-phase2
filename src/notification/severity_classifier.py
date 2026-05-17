from .models import NotificationEvent

class NotificationSeverityClassifier:
    def classify(self, event: NotificationEvent):
        # Default mapping based on event_type prefixes or specific types
        etype = event.event_type.lower()
        
        if "critical" in etype or "fatal" in etype or "auth_refresh_failed" in etype:
            event.severity = "critical"
            event.priority = "urgent"
        elif "failed" in etype or "error" in etype:
            event.severity = "error"
            event.priority = "high"
        elif "warning" in etype or "retryable" in etype or "drift" in etype:
            event.severity = "warning"
            event.priority = "normal"
        elif "completed" in etype or "created" in etype:
            event.severity = "info"
            event.priority = "low"
        
        # Override if specific flags are set
        if event.review_required_flag:
            event.severity = "warning"
            if event.priority == "low":
                event.priority = "normal"
        
        if event.retryable_flag and event.severity == "error":
            event.severity = "warning" # Downgrade to warning if it's retryable
