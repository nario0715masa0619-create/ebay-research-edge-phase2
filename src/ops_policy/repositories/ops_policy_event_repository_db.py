from typing import Optional, List, Tuple, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.ops_policy.models.ops_policy_event import OpsPolicyEvent
from src.ops_policy.models.enums import EventType, PolicyStatus
from src.db.models import OpsPolicyEventModel
from datetime import datetime

class OpsPolicyEventRepository:
    """DB-backed event repository"""

    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: OpsPolicyEventModel) -> OpsPolicyEvent:
        return OpsPolicyEvent(
            event_id=model.event_id,
            policy_id=model.policy_id,
            event_type=EventType(model.event_type),
            from_status=PolicyStatus(model.from_status) if model.from_status else None,
            to_status=PolicyStatus(model.to_status),
            actor_type=model.actor_type,
            actor_id=model.actor_id,
            note=model.note,
            details_json=model.details_json,
            created_at=model.created_at
        )

    def _to_model(self, entity: OpsPolicyEvent) -> OpsPolicyEventModel:
        return OpsPolicyEventModel(
            event_id=entity.event_id,
            policy_id=entity.policy_id,
            event_type=entity.event_type.value,
            from_status=entity.from_status.value if entity.from_status else None,
            to_status=entity.to_status.value,
            actor_type=entity.actor_type,
            actor_id=entity.actor_id,
            note=entity.note,
            details_json=entity.details_json,
            created_at=entity.created_at
        )

    def create_event(self, event: OpsPolicyEvent) -> OpsPolicyEvent:
        model = self._to_model(event)
        self.session.add(model)
        self.session.commit()
        return event

    def get_events_by_policy(self, policy_id: UUID, limit: int = 50) -> List[OpsPolicyEvent]:
        models = self.session.query(OpsPolicyEventModel).filter(
            OpsPolicyEventModel.policy_id == policy_id
        ).order_by(OpsPolicyEventModel.created_at.asc()).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def list_all_events(self, limit: int = 100, offset: int = 0) -> Tuple[List[OpsPolicyEvent], int]:
        q = self.session.query(OpsPolicyEventModel)
        total = q.count()
        models = q.order_by(OpsPolicyEventModel.created_at.desc()).offset(offset).limit(limit).all()
        return [self._to_entity(m) for m in models], total

    def count_events_by_type(self) -> Dict[EventType, int]:
        rows = self.session.query(OpsPolicyEventModel.event_type, func.count(OpsPolicyEventModel.event_id)).group_by(OpsPolicyEventModel.event_type).all()
        return {EventType(event_type): count for event_type, count in rows}
