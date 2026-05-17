import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.orm import Session

from src.db.models import MaintenanceWindowModel
from src.escalation.models import MaintenanceWindow

class PersistentMaintenanceWindowRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, window: MaintenanceWindow) -> MaintenanceWindow:
        model = MaintenanceWindowModel(
            window_id=window.window_id or str(uuid.uuid4()),
            seller_account_id=window.seller_account_id,
            environment_type=window.environment_type,
            event_type=window.event_type,
            enabled=window.enabled,
            starts_at=window.starts_at,
            ends_at=window.ends_at,
            action=window.action,
            reason=window.reason,
            created_by=window.created_by,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(model)
        self.session.commit()
        return self._to_domain(model)

    def list_active(self, now: datetime) -> List[MaintenanceWindow]:
        stmt = select(MaintenanceWindowModel).where(
            and_(
                MaintenanceWindowModel.enabled == True,
                MaintenanceWindowModel.starts_at <= now,
                MaintenanceWindowModel.ends_at > now
            )
        )
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def list_all(self, limit: int = 100) -> List[MaintenanceWindow]:
        stmt = select(MaintenanceWindowModel).order_by(MaintenanceWindowModel.created_at.desc()).limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def remove(self, window_id: str) -> bool:
        stmt = delete(MaintenanceWindowModel).where(MaintenanceWindowModel.window_id == window_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def resolve_applicable_windows(
        self, 
        now: datetime, 
        seller_account_id: Optional[str], 
        environment_type: Optional[str], 
        event_type: str
    ) -> List[MaintenanceWindow]:
        active_windows = self.list_active(now)
        applicable = []
        for w in active_windows:
            if w.seller_account_id and w.seller_account_id != seller_account_id:
                continue
            if w.environment_type and w.environment_type != environment_type:
                continue
            if w.event_type and w.event_type != event_type:
                continue
            applicable.append(w)
        return applicable

    def _to_domain(self, model: MaintenanceWindowModel) -> MaintenanceWindow:
        return MaintenanceWindow(
            window_id=model.window_id,
            seller_account_id=model.seller_account_id,
            environment_type=model.environment_type,
            event_type=model.event_type,
            enabled=model.enabled,
            starts_at=model.starts_at,
            ends_at=model.ends_at,
            action=model.action,
            reason=model.reason,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
