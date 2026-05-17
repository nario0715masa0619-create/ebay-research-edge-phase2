from typing import Dict, Any
from src.notification.dispatcher import NotificationDispatcher
from src.notification.models import NotificationEvent

class NotificationTestService:
    def __init__(self, dispatcher: NotificationDispatcher):
        self.dispatcher = dispatcher

    def send_test_notification(self, channel: str, title: str = "Test Notification", summary: str = "This is a test notification from CLI.", dry_run: bool = False) -> Dict[str, Any]:
        event = NotificationEvent(
            event_type="test_notification",
            title=title,
            summary=summary,
            source_layer="admin_cli",
            source_component="NotificationTestService",
            severity="info",
            priority="normal"
        )
        
        # We need to ensure the dispatcher uses the specified channel for this test event.
        # For v0.1 we can either rely on rules or manually trigger the channel.
        # For testing, we usually want to bypass rules and hit the channel directly.
        
        # Let's see if we can find a rule that matches or manually dispatch.
        # For simplicity in v0.1, we'll use dispatcher.notify and assume there's a rule for 'test_notification' 
        # OR we can manually call the notifier from the registry.
        
        notifier = self.dispatcher.channel_registry.get_notifier(channel)
        if not notifier:
            return {"status": "error", "message": f"Channel '{channel}' not found or not registered."}
            
        if dry_run:
            return {"status": "dry_run", "message": f"Would send test notification to {channel}."}
            
        res = notifier.send(event)
        # Record history if possible
        if self.dispatcher.history_repo:
            self.dispatcher.history_repo.save_dispatch(event, res)
            
        return {
            "status": "success" if res.success_flag else "failed",
            "channel": channel,
            "error": res.error_summary
        }
