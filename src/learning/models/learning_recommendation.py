from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class RecommendationType(Enum):
    ADJUST_INCIDENT_THRESHOLD = "adjust_incident_threshold"
    ADJUST_POLICY_CANDIDATE_RULE = "adjust_policy_candidate_rule"
    ADJUST_REPORTING_GROUPING = "adjust_reporting_grouping"
    ADD_GUARD_EXCEPTION_RULE = "add_guard_exception_rule"
    TIGHTEN_GUARD_RULE = "tighten_guard_rule"
    SELLER_SPECIFIC_OVERRIDE_NEEDED = "seller_specific_override_needed"
    ENVIRONMENT_SAFE_MODE_REFINEMENT = "environment_safe_mode_refinement"
    RETRY_STRATEGY_REVIEW = "retry_strategy_review"
    OPERATOR_RUNBOOK_UPDATE = "operator_runbook_update"
    MANUAL_REVIEW_REQUIRED_PATTERN = "manual_review_required_pattern"

class RecommendationStatus(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class LearningRecommendation:
    recommendation_id: UUID
    learning_record_id: UUID
    recommendation_type: RecommendationType
    target_phase: str  # e.g., "Phase M", "Phase N", "Phase L"
    target_scope: str  # e.g., "detection_threshold", "policy_candidate"
    proposal_summary: str
    proposal_details: str
    priority: int  # 1-100
    recommendation_status: RecommendationStatus
    review_due_at: datetime
    approved_by: Optional[str]
    implemented_in_phase: Optional[str]
    implemented_commit_ref: Optional[str]
    created_at: datetime
    updated_at: datetime
