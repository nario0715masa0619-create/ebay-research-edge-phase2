from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from src.ranking.models import DecisionClass, QueueType

class HandoffStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    VALIDATED = "validated"
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class HandoffDecision(str, Enum):
    DISPATCH_NOW = "dispatch_now"
    DEFER = "defer"
    REJECT_HANDOFF = "reject_handoff"
    CANCEL = "cancel"
    RETRY_LATER = "retry_later"

class DispatchTarget(str, Enum):
    MOCK = "mock"
    LIVE_READINESS = "live_readiness"

class FailureClassification(str, Enum):
    NONE = "none"
    TRANSIENT = "transient"
    NON_RETRYABLE = "non_retryable"
    RATE_LIMIT = "rate_limit"

@dataclass
class HandoffInput:
    # Phase F Ranking Input (Reference)
    ranking_decision_id: str
    candidate_id: str
    seller_account_id: str
    environment: str
    decision_class: DecisionClass
    ranking_score: float
    queue_type: QueueType
    
    # State flags from ranking layer
    execution_blocked: bool = False
    recheck_required: bool = False
    stale_flag: bool = False
    
    # Payload validity flags (mocked inputs for eligibility check)
    has_valid_readiness_payload: bool = True
    operator_hold: bool = False
    
    # Candidate Context
    canonical_title: str = ""
    market_evaluation_id: Optional[str] = None
    profitability_score_id: Optional[str] = None

@dataclass
class HandoffValidationResult:
    is_valid: bool = True
    is_stale: bool = False
    is_blocked: bool = False
    should_defer: bool = False
    block_reasons: List[str] = field(default_factory=list)
    defer_reasons: List[str] = field(default_factory=list)

@dataclass
class DuplicateCheckResult:
    is_duplicate: bool = False
    duplicate_suppressed: bool = False
    duplicate_reason: str = ""
    existing_handoff_ref: Optional[str] = None

@dataclass
class HandoffAttempt:
    attempt_id: str
    handoff_id: str
    attempt_number: int
    attempt_status: str
    error_code: str = ""
    error_summary: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

@dataclass
class HandoffTransition:
    from_status: str
    to_status: str
    transition_reason: str
    actor: str = "system"
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HandoffResult:
    handoff_id: str
    candidate_id: str
    ranking_decision_id: str
    seller_account_id: str
    environment: str
    
    handoff_status: HandoffStatus
    handoff_decision: HandoffDecision
    execution_allowed: bool = False
    
    dispatch_target: DispatchTarget = DispatchTarget.MOCK
    batch_id: Optional[str] = None
    idempotency_key: str = ""
    
    duplicate_suppressed: bool = False
    deferred: bool = False
    retryable: bool = False
    
    block_reasons: List[str] = field(default_factory=list)
    failure_reason: str = ""
    next_retry_at: Optional[datetime] = None
    
    explanation_lines: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
