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

class LearningRecordModel(Base):
    __tablename__ = 'learning_records'

    learning_record_id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    root_cause_category = Column(String(50), nullable=False)
    root_cause_subcategory = Column(String(255), nullable=True)
    impact_scope = Column(String(50), nullable=False)
    seller_account_id = Column(String(255), nullable=True)
    environment = Column(String(255), nullable=True)
    linked_incident_id = Column(String(36), nullable=True)
    linked_policy_id = Column(String(36), nullable=True)
    linked_report_id = Column(String(36), nullable=True)
    is_false_positive = Column(Boolean, default=False, nullable=False)
    is_false_negative = Column(Boolean, default=False, nullable=False)
    is_near_miss = Column(Boolean, default=False, nullable=False)
    effectiveness_rating = Column(String(50), nullable=False)
    confidence_level = Column(String(50), nullable=False)
    recommended_action_type = Column(String(255), nullable=True)
    recommended_change_scope = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    rcas = relationship('RootCauseAnalysisModel', back_populates='learning_record', cascade='all, delete-orphan')
    recommendations = relationship('LearningRecommendationModel', back_populates='learning_record', cascade='all, delete-orphan')

class RootCauseAnalysisModel(Base):
    __tablename__ = 'root_cause_analyses'

    rca_id = Column(String(36), primary_key=True)
    learning_record_id = Column(String(36), ForeignKey('learning_records.learning_record_id'), nullable=False)
    problem_statement = Column(Text, nullable=False)
    observed_symptoms = Column(Text, nullable=False)
    primary_cause = Column(Text, nullable=False)
    contributing_factors = Column(Text, nullable=False)
    detection_gap = Column(Text, nullable=True)
    mitigation_taken = Column(Text, nullable=False)
    resolution_summary = Column(Text, nullable=False)
    prevention_proposal = Column(Text, nullable=True)
    evidence_snapshot = Column(JSON, nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)

    learning_record = relationship('LearningRecordModel', back_populates='rcas')

class LearningRecommendationModel(Base):
    __tablename__ = 'learning_recommendations'

    recommendation_id = Column(String(36), primary_key=True)
    learning_record_id = Column(String(36), ForeignKey('learning_records.learning_record_id'), nullable=False)
    recommendation_type = Column(String(50), nullable=False)
    target_phase = Column(String(50), nullable=False)
    target_scope = Column(String(255), nullable=True)
    proposal_summary = Column(Text, nullable=False)
    proposal_details = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False)
    recommendation_status = Column(String(50), nullable=False)
    review_due_at = Column(DateTime, nullable=False)
    approved_by = Column(String(255), nullable=True)
    implemented_in_phase = Column(String(50), nullable=True)
    implemented_commit_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    learning_record = relationship('LearningRecordModel', back_populates='recommendations')
