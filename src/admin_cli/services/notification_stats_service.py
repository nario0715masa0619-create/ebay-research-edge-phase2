from typing import Dict, Any
from src.repositories.persistent_notification_history_repository import PersistentNotificationHistoryRepository

class NotificationStatsService:
    def __init__(self, repository: PersistentNotificationHistoryRepository):
        self.repository = repository

    def get_stats(self, since_hours: int = 24, event_type: str = None) -> Dict[str, Any]:
        models = self.repository.list_stats(since_hours=since_hours, event_type=event_type)
        
        stats = {
            "total_count": len(models),
            "by_status": {},
            "by_severity": {},
            "by_channel": {},
            "by_event_type": {}
        }
        
        for m in models:
            stats["by_status"][m.dispatch_status] = stats["by_status"].get(m.dispatch_status, 0) + 1
            stats["by_severity"][m.severity] = stats["by_severity"].get(m.severity, 0) + 1
            stats["by_channel"][m.channel_name] = stats["by_channel"].get(m.channel_name, 0) + 1
            stats["by_event_type"][m.event_type] = stats["by_event_type"].get(m.event_type, 0) + 1
            
        return stats
