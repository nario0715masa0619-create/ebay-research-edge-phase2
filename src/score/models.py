from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class StandardScoreResolutionStatus(Enum):
    RESOLVED = "resolved"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"

class StandardScoreConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class StandardScoreProfile(Enum):
    BALANCED = "balanced"
    PROFIT_FIRST = "profit_first"
    SAFETY_FIRST = "safety_first"
    VELOCITY_FIRST = "velocity_first"

@dataclass
class StandardScoreResult:
    # Aggregated Score
    standard_score: float = 0.0
    score_grade: str = "E"
    scoring_profile: str = "balanced"
    strictness: str = "balanced"
    resolution_status: StandardScoreResolutionStatus = StandardScoreResolutionStatus.UNRESOLVED
    confidence: StandardScoreConfidence = StandardScoreConfidence.NONE

    # Financial Sub-scores
    profit_score: float = 0.0
    margin_score: float = 0.0
    roi_score: float = 0.0

    # Quality Sub-scores
    confidence_score: float = 0.0
    stability_score: float = 0.0
    resolution_quality_score: float = 0.0

    # Penalties
    fallback_penalty: float = 0.0
    partial_penalty: float = 0.0
    unresolved_penalty: float = 0.0
    risk_penalty: float = 0.0
    negative_profit_penalty: float = 0.0

    # Source metrics (mirrored from TotalCostResult)
    final_profit_after_all_costs: Optional[float] = None
    estimated_margin_rate: Optional[float] = None
    estimated_roi: Optional[float] = None

    # Explanation Metadata
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    applied_weight_map: Dict[str, float] = field(default_factory=dict)
    unresolved_components: List[str] = field(default_factory=list)
    fallback_components: List[str] = field(default_factory=list)
    partial_components: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def add_note(self, note: str):
        self.notes.append(note)
