from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.ebay.models import MonitoringEvent
from src.db.models import MonitoringEventModel

class PersistentMonitoringEventRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, event: MonitoringEvent):
        model = MonitoringEventModel(
            event_id=event.event_id,
            candidate_id=event.candidate_id,
            sku=event.sku,
            event_scope=event.event_scope,
            event_type=event.event_type,
            before_value=event.before_value,
            after_value=event.after_value,
            action_taken=event.action_taken,
            created_at=event.created_at
        )
        self.session.add(model)

    def list_by_sku(self, sku: str, limit: Optional[int] = None) -> List[MonitoringEvent]:
        stmt = select(MonitoringEventModel).where(MonitoringEventModel.sku == sku).order_by(MonitoringEventModel.created_at.desc())
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def list_recent(self, limit: Optional[int] = 100) -> List[MonitoringEvent]:
        stmt = select(MonitoringEventModel).order_by(MonitoringEventModel.created_at.desc())
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def _to_domain(self, model: MonitoringEventModel) -> MonitoringEvent:
        return MonitoringEvent(
            event_id=model.event_id,
            candidate_id=model.candidate_id,
            sku=model.sku,
            event_scope=model.event_scope,
            event_type=model.event_type,
            before_value=model.before_value or "",
            after_value=model.after_value or "",
            action_taken=model.action_taken,
            created_at=model.created_at
        )
