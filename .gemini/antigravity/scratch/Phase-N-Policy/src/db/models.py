from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class OpsPolicyModel(Base):
    __tablename__ = 'ops_policies'

    policy_id = Column(UUID(as_uuid=True), primary_key=True)
    scope_type = Column(String(50), nullable=False)
    target_id = Column(String(255), nullable=True)
    action_type = Column(String(50), nullable=False)
    level = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    reason_summary = Column(Text, nullable=False)
    evidence_summary = Column(Text, nullable=True)
    linked_incident_id = Column(UUID(as_uuid=True), nullable=True)
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)
    review_due_at = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=False)
    approved_by = Column(String(255), nullable=True)
    applied_at = Column(DateTime, nullable=True)
    released_at = Column(DateTime, nullable=True)
    is_expired = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, nullable=False)
    metadata_json = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    events = relationship('OpsPolicyEventModel', back_populates='policy', cascade='all, delete-orphan')


class OpsPolicyEventModel(Base):
    __tablename__ = 'ops_policy_events'

    event_id = Column(UUID(as_uuid=True), primary_key=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey('ops_policies.policy_id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String(50), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(255), nullable=False)
    note = Column(Text, nullable=False)
    details_json = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False)

    policy = relationship('OpsPolicyModel', back_populates='events')
