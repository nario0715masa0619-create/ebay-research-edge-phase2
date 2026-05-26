from sqlalchemy.orm import Session
from src.incident.models.orm_models import IncidentLinkModel
from src.incident.models.incident_link import IncidentLink, IncidentLinkEntityType
import uuid

class IncidentLinkRepositoryDB:
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model: IncidentLinkModel) -> IncidentLink:
        return IncidentLink(
            link_id=model.link_id,
            incident_id=model.incident_id,
            entity_type=IncidentLinkEntityType(model.entity_type),
            entity_id=model.entity_id,
            created_at=model.created_at
        )

    def _to_model(self, entity: IncidentLink) -> IncidentLinkModel:
        return IncidentLinkModel(
            link_id=entity.link_id,
            incident_id=entity.incident_id,
            entity_type=entity.entity_type.value,
            entity_id=entity.entity_id,
            created_at=entity.created_at
        )

    def create_link(self, link: IncidentLink) -> uuid.UUID:
        model = self._to_model(link)
        self.session.add(model)
        self.session.commit()
        return model.link_id

    def get_links_by_incident(self, incident_id: uuid.UUID):
        models = self.session.query(IncidentLinkModel).filter_by(incident_id=incident_id).all()
        return [self._to_entity(m) for m in models]

    def get_links_by_entity(self, entity_type: IncidentLinkEntityType, entity_id: str):
        models = self.session.query(IncidentLinkModel).filter_by(
            entity_type=entity_type.value,
            entity_id=entity_id
        ).all()
        return [self._to_entity(m) for m in models]

    def delete_link(self, link_id: uuid.UUID):
        model = self.session.query(IncidentLinkModel).filter_by(link_id=link_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()
