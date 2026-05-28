from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class RootCauseCategory(Enum):
    CREDENTIALS_CONFIGURATION = "credentials_configuration"
    ENVIRONMENT_INSTABILITY = "environment_instability"
    SELLER_SPECIFIC_DATA_QUALITY = "seller_specific_data_quality"
    POLICY_MISCONFIGURATION = "policy_misconfiguration"
    THRESHOLD_TUNING_GAP = "threshold_tuning_gap"
    DETECTION_FALSE_POSITIVE = "detection_false_positive"
    DETECTION_FALSE_NEGATIVE = "detection_false_negative"
    RETRY_LOOP_BEHAVIOR = "retry_loop_behavior"
    GUARD_RULE_CONFLICT = "guard_rule_conflict"
    EXTERNAL_DEPENDENCY_FAILURE = "external_dependency_failure"
    OPERATOR_PROCESS_GAP = "operator_process_gap"
    UNKNOWN_PENDING_ANALYSIS = "unknown_pending_analysis"

class ImpactScope(Enum):
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    SELLER = "seller"
    LISTING_CLUSTER = "listing_cluster"
    INCIDENT_FAMILY = "incident_family"
    EXECUTION_CHANNEL = "execution_channel"

class EffectivenessRating(Enum):
    INEFFECTIVE = "ineffective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    EFFECTIVE = "effective"
    HIGHLY_EFFECTIVE = "highly_effective"
    UNKNOWN = "unknown"

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class LearningRecordStatus(Enum):
    OPEN = "open"
    UNDER_ANALYSIS = "under_analysis"
    RECOMMENDATION_READY = "recommendation_ready"
    CLOSED = "closed"
    ARCHIVED = "archived"

@dataclass
class LearningRecord:
    learning_record_id: UUID
    title: str
    summary: str
    root_cause_category: RootCauseCategory
    root_cause_subcategory: Optional[str]
    impact_scope: ImpactScope
    seller_account_id: Optional[str]
    environment: Optional[str]
    linked_incident_id: Optional[UUID]
    linked_policy_id: Optional[UUID]
    linked_report_id: Optional[UUID]
    is_false_positive: bool
    is_false_negative: bool
    is_near_miss: bool
    effectiveness_rating: EffectivenessRating
    confidence_level: ConfidenceLevel
    recommended_action_type: Optional[str]
    recommended_change_scope: Optional[str]
    status: LearningRecordStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    metadata_json: Dict[str, Any]
