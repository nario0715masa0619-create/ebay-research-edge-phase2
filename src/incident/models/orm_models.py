import uuid
import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class IncidentModel(Base):
    __tablename__ = 'incidents'
    
    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    incident_status = Column(String, nullable=False)
    sla_state = Column(String, nullable=False)
    seller_account_id = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    opened_at = Column(DateTime, nullable=False)
    ack_due_at = Column(DateTime, nullable=True)
    resolve_due_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    duplicate_of_incident_id = Column(UUID(as_uuid=True), nullable=True)
    root_cause_code = Column(String, nullable=True)
    is_reopened = Column(Boolean, default=False)
    trigger_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    events = relationship("IncidentEventModel", back_populates="incident", order_by="IncidentEventModel.created_at")
    links = relationship("IncidentLinkModel", back_populates="incident", order_by="IncidentLinkModel.created_at")

    __table_args__ = (
        Index('idx_incidents_opened_at', opened_at.desc()),
        Index('idx_incidents_seller', seller_account_id),
        Index('idx_incidents_env', environment),
        Index('idx_incidents_status', incident_status),
        Index('idx_incidents_sla', sla_state),
        Index('idx_incidents_created_at', created_at.desc()),
    )

class IncidentEventModel(Base):
    __tablename__ = 'incident_events'
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey('incidents.incident_id'), nullable=False)
    event_type = Column(String, nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    actor_type = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    details_json = Column(JSON, nullable=True)
    
    incident = relationship("IncidentModel", back_populates="events")

    __table_args__ = (
        Index('idx_incident_events_created_at', created_at.asc()),
    )

class IncidentLinkModel(Base):
    __tablename__ = 'incident_links'
    
    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey('incidents.incident_id'), nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    incident = relationship("IncidentModel", back_populates="links")

    __table_args__ = (
        Index('idx_incident_links_entity', entity_type, entity_id),
    )
