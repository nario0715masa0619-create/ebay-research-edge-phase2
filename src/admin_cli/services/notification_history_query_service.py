from typing import List, Optional, Dict, Any
from src.repositories.persistent_notification_history_repository import PersistentNotificationHistoryRepository
from src.db.models import NotificationHistoryModel
from ..notification_masker import NotificationCliMasker

class NotificationHistoryQueryService:
    def __init__(self, repository: PersistentNotificationHistoryRepository):
        self.repository = repository
        self.masker = NotificationCliMasker()

    def list_recent(self, limit: int = 50, severity: str = None, channel: str = None, event_type: str = None) -> List[Dict[str, Any]]:
        models = self.repository.list_recent(limit=limit, severity=severity, channel_name=channel, event_type=event_type)
        return [self._to_view(m) for m in models]

    def list_failed(self, limit: int = 50, channel: str = None, event_type: str = None) -> List[Dict[str, Any]]:
        models = self.repository.list_failed(limit=limit, channel_name=channel, event_type=event_type)
        return [self._to_view(m) for m in models]

    def get_details(self, history_id: int) -> Optional[Dict[str, Any]]:
        model = self.repository.get_by_history_id(history_id)
        return self._to_view(model, include_meta=True) if model else None

    def get_by_event_id(self, event_id: str) -> List[Dict[str, Any]]:
        models = self.repository.get_by_event_id(event_id)
        return [self._to_view(m, include_meta=True) for m in models]

    def list_by_sku(self, sku: str, limit: int = 50) -> List[Dict[str, Any]]:
        models = self.repository.list_by_sku(sku, limit=limit)
        return [self._to_view(m) for m in models]

    def list_by_event_type(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        models = self.repository.list_by_event_type(event_type, limit=limit)
        return [self._to_view(m) for m in models]

    def _to_view(self, model: NotificationHistoryModel, include_meta: bool = False) -> Dict[str, Any]:
        view = {
            "history_id": f"NTFH-{model.id:04d}",
            "id": model.id,
            "event_id": model.event_id,
            "event_type": model.event_type,
            "severity": model.severity,
            "priority": model.priority,
            "channel": model.channel_name,
            "status": model.dispatch_status,
            "source": model.source_layer,
            "sku": model.sku or "-",
            "title": model.title,
            "summary": model.summary or "-",
            "created_at": model.created_at.isoformat(),
            "error": model.error_summary or "-"
        }
        if include_meta:
            view["meta"] = self.masker.mask_dict(model.meta_json or {})
            view["dedupe_key"] = model.dedupe_key
            view["provider_msg_id"] = model.provider_message_id
        return view
