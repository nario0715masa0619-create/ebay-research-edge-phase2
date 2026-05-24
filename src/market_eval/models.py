from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

@dataclass
class MarketSearchSeed:
    """Represents the search parameters derived from a CanonicalProductCandidate."""
    candidate_id: str
    keyword_query: str
    excluded_keywords: List[str] = field(default_factory=list)
    brand: Optional[str] = None
    model: Optional[str] = None
    mpn: Optional[str] = None
    gtins: List[str] = field(default_factory=list)
    category_candidates: List[str] = field(default_factory=list)
    variation_signature: Optional[str] = None
    bundle_signature: Optional[str] = None
    condition_family: str = "used"
    risk_flags: List[str] = field(default_factory=list)

@dataclass
class MarketSearchRequest:
    """Represents the actual request sent to the provider (RapidAPI or Mock)."""
    query: str
    excluded_keywords: List[str] = field(default_factory=list)
    marketplace_id: str = "EBAY_US"
    category_id: Optional[str] = None
    filters: Dict[str, str] = field(default_factory=dict)
    limit: int = 50
    sort: str = "BestMatch"
    seller_account_id: Optional[str] = None
    environment_type: str = "sandbox"

@dataclass
class MarketListingSnapshot:
    """Normalized representation of a single item returned by the provider."""
    listing_id: str
    title: str
    price: float
    currency: str
    shipping_price: float = 0.0
    is_sold: bool = True
    condition: Optional[str] = None
    category_path: Optional[str] = None
    item_specifics: Dict[str, str] = field(default_factory=dict)
    seller_feedback_hint: Optional[str] = None
    listing_url: Optional[str] = None
    image_url: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None

@dataclass
class ComparableEvaluation:
    """Result of evaluating a single snapshot against the seed/candidate."""
    listing_id: str
    included: bool
    comparable_score: float = 0.0
    category_alignment_score: float = 0.0
    condition_alignment_score: float = 0.0
    attribute_alignment_score: float = 0.0
    variation_conflict_flags: List[str] = field(default_factory=list)
    bundle_conflict_flags: List[str] = field(default_factory=list)
    exclusion_reason: Optional[str] = None

@dataclass
class MarketEvaluationResult:
    """The final market evaluation output for the candidate."""
    market_evaluation_id: str
    candidate_id: str
    evaluation_status: str  # e.g., "success", "unsafe", "error"
    comparable_count: int
    comparable_quality_score: float
    price_low: Optional[float]
    price_median: Optional[float]
    price_high: Optional[float]
    category_alignment_score: float
    condition_alignment_score: float
    attribute_alignment_score: float
    competition_proxy: Optional[str]  # e.g., "low", "medium", "high", or numeric
    demand_proxy: Optional[str]
    market_confidence: float
    unsafe_reasons: List[str] = field(default_factory=list)
    review_required: bool = False
    evidence_summary: str = ""
    search_queries_used: List[str] = field(default_factory=list)
    raw_result_count: int = 0
    filtered_result_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class MarketEvaluationEvidence:
    """Detailed evidence log of how the evaluation was performed."""
    evidence_id: str
    candidate_id: str
    search_request_payload: Dict[str, Any]
    provider_name: str
    comparable_listing_ids: List[str]
    excluded_listing_ids: List[str]
    unsafe_reasons: List[str]
    evidence_lines: List[str]
    raw_response_reference: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
