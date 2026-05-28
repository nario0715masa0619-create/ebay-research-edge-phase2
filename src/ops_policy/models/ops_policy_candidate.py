from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID

from src.ops_policy.models.enums import CandidateType, ActionType, Severity, ScopeType

@dataclass
class OpsPolicyCandidate:
    """ポリシー候補"""
    candidate_id: UUID
    candidate_type: CandidateType
    recommended_action_type: ActionType
    severity: Severity
    target_scope: ScopeType
    target_id: Optional[str]
    linked_incident_id: Optional[UUID]
    confidence_score: float
    reason_summary: str
    created_at: datetime
