from typing import List, Optional, Dict, Any
from src.repositories.persistent_monitoring_event_repository import PersistentMonitoringEventRepository
from ..models import CliCommandResult

class EventOpsService:
    def __init__(self, event_repo: PersistentMonitoringEventRepository):
        self.event_repo = event_repo

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        events = self.event_repo.list_recent(limit=limit)
        return [
            {
                "event_id": e.event_id[:8] + "...",
                "sku": e.sku,
                "type": e.event_type,
                "action": e.action_taken,
                "created": e.created_at.strftime("%H:%M")
            }
            for e in events
        ]

    def get_detail(self, event_id: str) -> Optional[Dict[str, Any]]:
        e = self.event_repo.get_by_event_id(event_id)
        if not e:
            return None
        return e.__dict__
