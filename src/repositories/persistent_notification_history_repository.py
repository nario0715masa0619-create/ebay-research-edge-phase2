from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.notification.models import NotificationEvent, NotificationDispatchResult
from src.db.models import NotificationHistoryModel

class PersistentNotificationHistoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_dispatch(self, event: NotificationEvent, res: NotificationDispatchResult):
        model = NotificationHistoryModel(
            event_id=event.event_id,
            event_type=event.event_type,
            source_layer=event.source_layer,
            source_run_id=event.source_run_id,
            sku=event.sku,
            severity=event.severity,
            priority=event.priority,
            channel_name=res.channel_name,
            dispatch_status=res.dispatch_status,
            dedupe_key=event.dedupe_key,
            title=event.title,
            summary=event.summary,
            meta_json=event.meta_json,
            provider_message_id=res.provider_message_id,
            error_summary=res.error_summary,
            created_at=res.dispatched_at
        )
        self.session.add(model)
        # Flush or commit depends on caller (UoW)

    def list_recent(self, limit: int = 50, severity: str = None, channel_name: str = None, event_type: str = None, dispatch_status: str = None) -> List[NotificationHistoryModel]:
        stmt = select(NotificationHistoryModel).order_by(NotificationHistoryModel.created_at.desc())
        if severity:
            stmt = stmt.where(NotificationHistoryModel.severity == severity)
        if channel_name:
            stmt = stmt.where(NotificationHistoryModel.channel_name == channel_name)
        if event_type:
            stmt = stmt.where(NotificationHistoryModel.event_type == event_type)
        if dispatch_status:
            stmt = stmt.where(NotificationHistoryModel.dispatch_status == dispatch_status)
        stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_failed(self, limit: int = 50, channel_name: str = None, event_type: str = None) -> List[NotificationHistoryModel]:
        return self.list_recent(limit=limit, channel_name=channel_name, event_type=event_type, dispatch_status="failed")

    def get_by_history_id(self, history_id: int) -> Optional[NotificationHistoryModel]:
        stmt = select(NotificationHistoryModel).where(NotificationHistoryModel.id == history_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_event_id(self, event_id: str) -> List[NotificationHistoryModel]:
        stmt = select(NotificationHistoryModel).where(NotificationHistoryModel.event_id == event_id)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_sku(self, sku: str, limit: int = 50) -> List[NotificationHistoryModel]:
        stmt = select(NotificationHistoryModel).where(NotificationHistoryModel.sku == sku).order_by(NotificationHistoryModel.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_event_type(self, event_type: str, limit: int = 50) -> List[NotificationHistoryModel]:
        stmt = select(NotificationHistoryModel).where(NotificationHistoryModel.event_type == event_type).order_by(NotificationHistoryModel.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_stats(self, since_hours: int = 24, event_type: str = None):
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=since_hours)
        stmt = select(NotificationHistoryModel).where(NotificationHistoryModel.created_at >= cutoff)
        if event_type:
            stmt = stmt.where(NotificationHistoryModel.event_type == event_type)
        return list(self.session.execute(stmt).scalars().all())

    def list_recent_failed_resendable(self, limit: int = 50) -> List[NotificationHistoryModel]:
        stmt = select(NotificationHistoryModel).where(
            NotificationHistoryModel.dispatch_status.in_(["failed", "skipped"])
        ).order_by(NotificationHistoryModel.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
