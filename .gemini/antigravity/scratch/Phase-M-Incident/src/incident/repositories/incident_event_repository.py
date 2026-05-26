from sqlalchemy.orm import Session
from src.incident.models.orm_models import IncidentEventModel
from src.incident.models.incident_event import IncidentEvent, IncidentEventType
from src.incident.models.incident import IncidentStatus
import uuid

class IncidentEventRepositoryDB:
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: IncidentEventModel) -> IncidentEvent:
        ev = IncidentEvent(
            event_id=model.event_id,
            incident_id=model.incident_id,
            event_type=IncidentEventType(model.event_type),
            note=model.note,
            actor_type=model.actor_type,
            actor_id=model.actor_id,
            from_status=IncidentStatus(model.from_status) if model.from_status else None,
            to_status=IncidentStatus(model.to_status) if model.to_status else None,
            details_json=model.details_json,
            created_at=model.created_at
        )
        return ev

    def _to_model(self, entity: IncidentEvent) -> IncidentEventModel:
        return IncidentEventModel(
            event_id=entity.event_id,
            incident_id=entity.incident_id,
            event_type=entity.event_type.value,
            note=entity.note,
            actor_type=entity.actor_type,
            actor_id=entity.actor_id,
            from_status=entity.from_status.value if entity.from_status else None,
            to_status=entity.to_status.value if entity.to_status else None,
            details_json=entity.details_json,
            created_at=entity.created_at
        )

    def create_event(self, event: IncidentEvent) -> uuid.UUID:
        model = self._to_model(event)
        self.session.add(model)
        self.session.commit()
        return model.event_id

    def get_events_by_incident(self, incident_id: uuid.UUID):
        models = self.session.query(IncidentEventModel).filter_by(incident_id=incident_id).order_by(IncidentEventModel.created_at.asc()).all()
        return [self._to_entity(m) for m in models]

    def list_all_events(self, sort='ASC'):
        q = self.session.query(IncidentEventModel)
        if sort == 'ASC':
            q = q.order_by(IncidentEventModel.created_at.asc())
        else:
            q = q.order_by(IncidentEventModel.created_at.desc())
        models = q.all()
        return [self._to_entity(m) for m in models]
