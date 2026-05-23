from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    HOLD = "hold"

@dataclass
class ReviewDecisionRecord:
    """Audit log entry for a review decision."""
    decision_id: str
    candidate_id: str
    actor: str
    action: str  # e.g., 'approve', 'reject', 'hold', 'reopen', 'note', 'alias_add'
    reason: Optional[str] = None
    target_alias: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ReviewQueueItem:
    """Represents a summary view of a candidate in the Review Queue."""
    candidate_id: str
    canonical_title: str
    source_count: int
    review_status: ReviewStatus
    ambiguity_severity: float # e.g. Max penalty score from its matches
    updated_at: datetime
    
    brand: Optional[str] = None
    model: Optional[str] = None
    
    ambiguity_flags: List[str] = field(default_factory=list)
    pending_sources_count: int = 0 # Number of sources currently flagged for review

@dataclass
class SourceCompareItem:
    """Details of a specific source item linked to a candidate for comparison."""
    source_item_id: str
    normalized_title: str
    raw_title: str
    match_confidence: float
    variation_penalty: float
    bundle_penalty: float
    ambiguity_flags: List[str] = field(default_factory=list)
    explanation_lines: List[str] = field(default_factory=list)
    
    # Context
    variation_keys: Dict[str, str] = field(default_factory=dict)
    bundle_flags: List[str] = field(default_factory=list)

@dataclass
class CandidateCompareView:
    """Detailed view for resolving a review item."""
    candidate_id: str
    canonical_title: str
    review_status: ReviewStatus
    canonical_brand: Optional[str] = None
    canonical_model: Optional[str] = None
    canonical_mpn: Optional[str] = None
    
    candidate_variation_signature: Optional[str] = None
    candidate_bundle_signature: Optional[str] = None
    
    sources: List[SourceCompareItem] = field(default_factory=list)
    audit_history: List[ReviewDecisionRecord] = field(default_factory=list)
    
    # Recommendations for merge/split (auxiliary info only)
    split_recommended: bool = False
    split_reason: Optional[str] = None
