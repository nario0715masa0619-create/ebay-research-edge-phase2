from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from src.ops_policy.models.enums import ScopeType, ActionType, PolicyLevel, PolicyStatus

@dataclass
class OpsPolicy:
    """運用制御ポリシー"""
    policy_id: UUID
    scope_type: ScopeType
    target_id: Optional[str]
    action_type: ActionType
    level: PolicyLevel
    status: PolicyStatus
    title: str
    reason_summary: str
    evidence_summary: str
    linked_incident_id: Optional[UUID]
    effective_from: datetime
    effective_until: Optional[datetime]
    review_due_at: Optional[datetime]
    created_by: str
    approved_by: Optional[str]
    applied_at: Optional[datetime]
    released_at: Optional[datetime]
    is_expired: bool
    priority: int
    metadata_json: Dict[str, Any]
