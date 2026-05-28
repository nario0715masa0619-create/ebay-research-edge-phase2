from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class ChangeType(Enum):
    INCIDENT_THRESHOLD_CHANGE = "incident_threshold_change"
    POLICY_CANDIDATE_RULE_CHANGE = "policy_candidate_rule_change"
    REPORTING_GROUPING_CHANGE = "reporting_grouping_change"
    GUARD_RULE_CHANGE = "guard_rule_change"
    SELLER_OVERRIDE_CHANGE = "seller_override_change"
    ENVIRONMENT_SAFE_MODE_TUNING = "environment_safe_mode_tuning"
    RETRY_PARAMETER_TUNING = "retry_parameter_tuning"
    MANUAL_REVIEW_RULE_CHANGE = "manual_review_rule_change"
    DIGEST_RULE_CHANGE = "digest_rule_change"
    EFFECTIVE_POLICY_RESOLUTION_CHANGE = "effective_policy_resolution_change"

class ChangeScopeType(Enum):
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    SELLER = "seller"
    CHANNEL = "channel"
    LISTING_CLUSTER = "listing_cluster"

class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ProposalStatus(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    VALIDATED = "validated"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class ValidationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"

@dataclass
class ChangeProposal:
    change_proposal_id: UUID
    source_recommendation_id: Optional[UUID]
    title: str
    summary: str
    target_phase: str
    target_component: str
    change_type: ChangeType
    change_scope_type: ChangeScopeType
    scope_target_id: Optional[str]
    risk_level: RiskLevel
    proposal_status: ProposalStatus
    validation_status: ValidationStatus
    rollout_status: str
    validation_strategy: str
    rollback_strategy: str
    created_by: str
    created_at: datetime
    review_due_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    metadata_json: Dict[str, Any]
