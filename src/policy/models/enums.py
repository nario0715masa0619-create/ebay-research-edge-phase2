from enum import Enum

class ScopeType(Enum):
    """ポリシー適用スコープ"""
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    SELLER = "seller"
    EXECUTION_CHANNEL = "execution_channel"


class ActionType(Enum):
    """ポリシーアクション種別"""
    BLOCK_LIVE_EXECUTION = "block_live_execution"
    FORCE_DRY_RUN = "force_dry_run"
    PAUSE_HANDOFF = "pause_handoff"
    SUPPRESS_RETRY = "suppress_retry"
    LIMIT_CONCURRENCY = "limit_concurrency"
    LIMIT_SELLER_THROUGHPUT = "limit_seller_throughput"
    REQUIRE_MANUAL_REVIEW = "require_manual_review"
    BLOCK_LISTING_CREATION = "block_listing_creation"
    ENVIRONMENT_SAFE_MODE = "environment_safe_mode"
    OPERATOR_ATTENTION_REQUIRED = "operator_attention_required"


class PolicyLevel(Enum):
    """ポリシーレベル"""
    STRONG = "strong"
    OVERLAY = "overlay"
    INFORMATIONAL = "informational"


class PolicyStatus(Enum):
    """ポリシーステータス"""
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"
    RELEASED = "released"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class EventType(Enum):
    """ポリシーイベント種別"""
    CREATED = "created"
    PROPOSED = "proposed"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"
    RELEASED = "released"
    EXPIRED = "expired"
    RENEWED = "renewed"
    CANCELLED = "cancelled"


class CandidateType(Enum):
    """ポリシー候補種別"""
    CREDENTIAL_FAILURE_SPIKE = "credential_failure_spike"
    HIGH_SEVERITY_INCIDENT = "high_severity_incident"
    ENVIRONMENT_ANOMALY = "environment_anomaly"
    RETRY_LOOP_RISK = "retry_loop_risk"
    SELLER_HEALTH_DEGRADATION = "seller_health_degradation"
    MANUAL_ALERT = "manual_alert"


class Severity(Enum):
    """重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
