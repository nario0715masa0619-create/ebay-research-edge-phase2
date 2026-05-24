from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DecisionClass(str, Enum):
    AUTO_LAUNCH = "auto_launch"
    MANUAL_REVIEW = "manual_review"
    WATCHLIST = "watchlist"
    REJECT = "reject"

class QueueType(str, Enum):
    AUTO_LAUNCH_QUEUE = "auto_launch_queue"
    REVIEW_QUEUE = "review_queue"
    WATCH_QUEUE = "watch_queue"
    REJECT_ARCHIVE = "reject_archive"

class LaunchPriorityBucket(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    DEFERRED = "deferred"

class ReviewPriorityBucket(str, Enum):
    CRITICAL_REVIEW = "critical_review"
    HIGH_REVIEW = "high_review"
    NORMAL_REVIEW = "normal_review"
    LOW_REVIEW = "low_review"

@dataclass
class RankingInput:
    # 1. Candidate Info
    candidate_id: str
    seller_account_id: str
    environment: str
    review_required: bool = False
    ambiguity_flags: List[str] = field(default_factory=list)
    
    # 2. Market Evaluation Info
    market_evaluation_id: Optional[str] = None
    market_evaluation_status: str = "success"
    market_confidence: float = 0.0
    comparable_count: int = 0
    competition_proxy: str = "medium"
    demand_proxy: str = "medium"
    market_unsafe_reasons: List[str] = field(default_factory=list)
    market_created_at: Optional[datetime] = None
    
    # 3. Profitability Info
    profitability_score_id: Optional[str] = None
    profitability_scoring_status: str = "success"
    expected_net_profit: float = 0.0
    expected_margin: float = 0.0
    expected_roi: float = 0.0
    confidence_adjusted_profit: float = 0.0
    profitability_score: float = 0.0
    profitability_decision_status: str = "watch"
    profitability_unsafe_reasons: List[str] = field(default_factory=list)
    profitability_created_at: Optional[datetime] = None
    
    # 4. Operational / Policy Info (from external or configs)
    seller_capacity_full: bool = False
    execution_blocked_by_seller: bool = False
    blacklisted: bool = False

@dataclass
class RankingComponents:
    profitability_component: float = 0.0
    margin_component: float = 0.0
    roi_component: float = 0.0
    market_confidence_component: float = 0.0
    demand_component: float = 0.0
    competition_component: float = 0.0
    review_penalty: float = 0.0
    unsafe_penalty: float = 0.0
    staleness_penalty: float = 0.0
    capacity_penalty: float = 0.0

@dataclass
class ListingDecisionResult:
    ranking_decision_id: str
    candidate_id: str
    seller_account_id: str
    environment: str
    
    ranking_score: float
    decision_class: DecisionClass
    decision_reason: str
    
    queue_type: QueueType
    queue_rank: int = 0
    
    launch_priority_bucket: Optional[LaunchPriorityBucket] = None
    review_priority_bucket: Optional[ReviewPriorityBucket] = None
    
    execution_blocked: bool = False
    block_reasons: List[str] = field(default_factory=list)
    recheck_required: bool = False
    stale_flag: bool = False
    
    explanation_lines: List[str] = field(default_factory=list)
    ranking_components: RankingComponents = field(default_factory=RankingComponents)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
