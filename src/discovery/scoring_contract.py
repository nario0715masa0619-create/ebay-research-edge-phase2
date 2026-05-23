from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class MarketSearchSeed:
    """Safe eBay search seed generated from canonical candidates."""
    keyword_seed: str
    brand_seed: Optional[str] = None
    model_seed: Optional[str] = None
    mpn_seed: Optional[str] = None
    gtin_seeds: List[str] = field(default_factory=list)
    category_candidate_seeds: List[str] = field(default_factory=list)
    item_aspects_candidate_seed: Dict[str, str] = field(default_factory=dict)
    
    # Ensures search safety by explicitly identifying what MUST NOT be searched
    excluded_keywords: List[str] = field(default_factory=list)

@dataclass
class ProfitabilityScoringInputPayload:
    """
    Fixed schema contract for the Profitability Scoring Layer.
    Ensures Review Required status, ambiguity, and explanation lines are not lost.
    """
    candidate_id: str
    
    # Financial Base
    source_cost_total_jpy: float
    source_shipping_cost_jpy: float
    
    # Classification Base
    condition_family: str  # e.g., 'new', 'used'
    category_candidates: List[str] = field(default_factory=list)
    category_confidence: float = 0.0
    
    # Discovery Confidence & Ambiguity
    match_confidence: float = 0.0
    refined_match_confidence: float = 0.0
    review_required: bool = False
    ambiguity_flags: List[str] = field(default_factory=list)
    
    # Signature Context
    variation_signature: Optional[str] = None
    bundle_signature: Optional[str] = None
    identity_strength: float = 0.0
    source_count: int = 1
    
    # Signals
    seller_quality_signals: Dict[str, float] = field(default_factory=dict)
    risk_flags: List[str] = field(default_factory=list)
    
    # Market Bridge
    market_search_seed: Optional[MarketSearchSeed] = None
    
    # Additional Payloads
    attribute_payload: Dict[str, Any] = field(default_factory=dict)
    explanation_lines: List[str] = field(default_factory=list)
