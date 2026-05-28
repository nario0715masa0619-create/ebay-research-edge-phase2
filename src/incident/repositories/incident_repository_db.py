from sqlalchemy.orm import Session
from src.incident.models.orm_models import IncidentModel
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
import uuid

class IncidentRepositoryDB:
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: IncidentModel) -> Incident:
        inc = Incident(
            incident_id=model.incident_id,
            incident_type=IncidentType(model.incident_type),
            severity=IncidentSeverity(model.severity),
            title=model.title,
            summary=model.summary,
            incident_status=IncidentStatus(model.incident_status),
            sla_state=SlaState(model.sla_state),
            seller_account_id=model.seller_account_id,
            environment=model.environment
        )
        inc.assigned_to = model.assigned_to
        inc.created_by = model.created_by
        inc.opened_at = model.opened_at
        inc.ack_due_at = model.ack_due_at
        inc.resolve_due_at = model.resolve_due_at
        inc.acknowledged_at = model.acknowledged_at
        inc.resolved_at = model.resolved_at
        inc.closed_at = model.closed_at
        inc.duplicate_of_incident_id = model.duplicate_of_incident_id
        inc.root_cause_code = model.root_cause_code
        inc.is_reopened = model.is_reopened
        return inc

    def _to_model(self, entity: Incident) -> IncidentModel:
        return IncidentModel(
            incident_id=entity.incident_id,
            incident_type=entity.incident_type.value,
            severity=entity.severity.value,
            title=entity.title,
            summary=entity.summary,
            incident_status=entity.incident_status.value,
            sla_state=entity.sla_state.value,
            seller_account_id=entity.seller_account_id,
            environment=entity.environment,
            assigned_to=entity.assigned_to,
            created_by=entity.created_by,
            opened_at=entity.opened_at,
            ack_due_at=entity.ack_due_at,
            resolve_due_at=entity.resolve_due_at,
            acknowledged_at=entity.acknowledged_at,
            resolved_at=entity.resolved_at,
            closed_at=entity.closed_at,
            duplicate_of_incident_id=entity.duplicate_of_incident_id,
            root_cause_code=entity.root_cause_code,
            is_reopened=entity.is_reopened
        )

    def create_incident(self, incident: Incident) -> uuid.UUID:
        model = self._to_model(incident)
        self.session.add(model)
        self.session.commit()
        return model.incident_id

    def get_incident_by_id(self, incident_id: uuid.UUID) -> Incident:
        model = self.session.query(IncidentModel).filter_by(incident_id=incident_id).first()
        if not model:
            raise KeyError(f"Incident {incident_id} not found")
        return self._to_entity(model)

    def update_incident(self, incident_id: uuid.UUID, updates: dict):
        # Allow passing updates as dict, or we can just fetch and update
        model = self.session.query(IncidentModel).filter_by(incident_id=incident_id).first()
        if not model:
            raise KeyError(f"Incident {incident_id} not found")
        
        for k, v in updates.items():
            if hasattr(model, k):
                # handle enums if present in updates dict
                if hasattr(v, 'value'):
                    v = v.value
                setattr(model, k, v)
        self.session.commit()

    def list_incidents(self, filters=None, sort=None, limit=100, offset=0):
        q = self.session.query(IncidentModel)
        if filters:
            if 'status' in filters:
                q = q.filter(IncidentModel.incident_status == filters['status'].value)
            if 'severity' in filters:
                q = q.filter(IncidentModel.severity == filters['severity'].value)
            if 'seller_account_id' in filters:
                q = q.filter(IncidentModel.seller_account_id == filters['seller_account_id'])
            if 'environment' in filters:
                q = q.filter(IncidentModel.environment == filters['environment'])
        
        if sort == 'opened_at_desc':
            q = q.order_by(IncidentModel.opened_at.desc())
            
        models = q.limit(limit).offset(offset).all()
        return [self._to_entity(m) for m in models]

    def get_open_incidents(self):
        models = self.session.query(IncidentModel).filter(
            IncidentModel.incident_status.in_(['open', 'acknowledged', 'investigating', 'mitigated'])
        ).all()
        return [self._to_entity(m) for m in models]

    def get_overdue_incidents(self):
        # We can implement python-side or DB-side.
        # DB-side:
        import datetime
        now = datetime.datetime.utcnow()
        # ack overdue OR resolve overdue
        # For simplicity, we just fetch open and filter in python, or use or_
        from sqlalchemy import or_, and_
        models = self.session.query(IncidentModel).filter(
            IncidentModel.incident_status.in_(['open', 'acknowledged', 'investigating', 'mitigated']),
            or_(
                and_(IncidentModel.acknowledged_at == None, IncidentModel.ack_due_at != None, IncidentModel.ack_due_at < now),
                and_(IncidentModel.resolved_at == None, IncidentModel.resolve_due_at != None, IncidentModel.resolve_due_at < now)
            )
        ).all()
        return [self._to_entity(m) for m in models]

    def get_breached_incidents(self):
        models = self.session.query(IncidentModel).filter(
            IncidentModel.sla_state.in_(['ack_breached', 'resolve_breached', 'both_breached'])
        ).all()
        return [self._to_entity(m) for m in models]

    def query_by_seller(self, seller_id: str):
        models = self.session.query(IncidentModel).filter_by(seller_account_id=seller_id).all()
        return [self._to_entity(m) for m in models]

    def query_by_environment(self, environment: str):
        models = self.session.query(IncidentModel).filter_by(environment=environment).all()
        return [self._to_entity(m) for m in models]

    def query_by_status(self, status: IncidentStatus):
        models = self.session.query(IncidentModel).filter_by(incident_status=status.value).all()
        return [self._to_entity(m) for m in models]
