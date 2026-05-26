from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
from src.learning.models.learning_record import RootCauseCategory, ImpactScope

class CandidateSource(Enum):
    RESOLVED_INCIDENT = "resolved_incident"
    REPEATED_PATTERN = "repeated_pattern"
    FALSE_POSITIVE_DETECTED = "false_positive_detected"
    RECURRING_ERROR_FAMILY = "recurring_error_family"
    POLICY_INEFFECTIVE = "policy_ineffective"
    REPORT_THRESHOLD_DRIFT = "report_threshold_drift"
    MANUAL_OPERATOR_INPUT = "manual_operator_input"

@dataclass
class LearningCandidate:
    candidate_id: UUID
    candidate_source: CandidateSource
    title: str
    summary: str
    suggested_root_cause_category: RootCauseCategory
    suggested_impact_scope: ImpactScope
    seller_account_id: Optional[str]
    environment: Optional[str]
    linked_incident_id: Optional[UUID]
    linked_policy_id: Optional[UUID]
    confidence_score: float  # 0.0-1.0
    created_at: datetime
