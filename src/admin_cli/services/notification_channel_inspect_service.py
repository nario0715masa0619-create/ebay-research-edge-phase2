import os
from typing import List, Dict, Any
from src.notification.channel_registry import NotificationChannelRegistry

class NotificationChannelInspectService:
    def __init__(self, registry: NotificationChannelRegistry):
        self.registry = registry

    def list_channels(self) -> List[Dict[str, Any]]:
        channels = ["console", "slack", "email", "webhook"]
        results = []
        for c in channels:
            notifier = self.registry.get_notifier(c)
            results.append({
                "channel": c,
                "status": "enabled" if notifier else "disabled",
                "configured": self._is_configured(c),
                "type": notifier.__class__.__name__ if notifier else "N/A"
            })
        return results

    def _is_configured(self, channel: str) -> bool:
        if channel == "console":
            return True
        if channel == "slack":
            return bool(os.environ.get("NOTIFICATION_SLACK_WEBHOOK_URL"))
        if channel == "webhook":
            return bool(os.environ.get("NOTIFICATION_WEBHOOK_URL"))
        if channel == "email":
            return bool(os.environ.get("NOTIFICATION_EMAIL_TO"))
        return False
