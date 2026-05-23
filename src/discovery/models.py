from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum

class VariationDecisionClass(str, Enum):
    EXACT = "exact"
    COMPATIBLE = "compatible"
    AMBIGUOUS = "ambiguous"
    CONFLICT = "conflict"

class BundleDecisionClass(str, Enum):
    SINGLE = "single"
    SET = "set"
    BUNDLE = "bundle"
    LOT = "lot"
    CONFLICT = "conflict"

@dataclass
class VariationDecision:
    decision_class: VariationDecisionClass
    penalty_score: float = 0.0
    extracted_keys: Dict[str, str] = field(default_factory=dict)
    conflict_reasons: List[str] = field(default_factory=list)

@dataclass
class BundleDecision:
    decision_class: BundleDecisionClass
    penalty_score: float = 0.0
    extracted_flags: List[str] = field(default_factory=list)
    conflict_reasons: List[str] = field(default_factory=list)

@dataclass
class RawSourceItem:
    """Raw item fetched from external source marketplaces."""
    source_item_id: str
    source_platform: str
    source_url: str
    raw_title: str
    
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None
    raw_description: Optional[str] = None
    raw_price: Optional[Decimal] = None
    raw_shipping_price: Optional[Decimal] = None
    raw_condition_text: Optional[str] = None
    raw_quantity_text: Optional[str] = None
    raw_brand: Optional[str] = None
    raw_model: Optional[str] = None
    raw_mpn: Optional[str] = None
    raw_gtin: Optional[str] = None
    raw_category: Optional[str] = None
    
    raw_attributes: Dict[str, Any] = field(default_factory=dict)
    image_urls: List[str] = field(default_factory=list)
    seller_meta: Dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class NormalizedSourceItem:
    """A cleaned up source item ready for matching."""
    normalized_item_id: str
    source_item_id: str
    normalized_title: str
    
    normalized_brand: Optional[str] = None
    normalized_model: Optional[str] = None
    normalized_mpn: Optional[str] = None
    
    strict_gtins: List[str] = field(default_factory=list)
    loose_gtins: List[str] = field(default_factory=list)
    
    normalized_condition: Optional[str] = None
    normalized_quantity: Optional[int] = None
    
    variation_keys: Dict[str, str] = field(default_factory=dict)
    bundle_flags: List[str] = field(default_factory=list)
    parsed_attributes: Dict[str, Any] = field(default_factory=dict)
    
    identity_signals: Dict[str, Any] = field(default_factory=dict)
    normalization_flags: List[str] = field(default_factory=list)
    
    review_required: bool = False
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ProductIdentity:
    """Canonical identity attributes used for clustering."""
    brand: Optional[str] = None
    model: Optional[str] = None
    mpn: Optional[str] = None
    gtins: List[str] = field(default_factory=list)
    product_line: Optional[str] = None
    variation_signature: Optional[str] = None
    bundle_signature: Optional[str] = None
    condition_family: Optional[str] = None

@dataclass
class MatchEvidence:
    """Record explaining why a NormalizedItem matched (or didn't) to a Candidate."""
    evidence_id: str
    normalized_item_id: str
    candidate_id: Optional[str] = None
    
    identifier_hits: Dict[str, bool] = field(default_factory=dict)
    title_similarity_score: float = 0.0
    brand_match_score: float = 0.0
    model_match_score: float = 0.0
    mpn_match_score: float = 0.0
    
    variation_penalty: float = 0.0
    bundle_penalty: float = 0.0
    condition_penalty: float = 0.0
    
    ambiguity_flags: List[str] = field(default_factory=list)
    explanation_lines: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class CanonicalProductCandidate:
    """The canonical object representing a clustered market product."""
    candidate_id: str
    canonical_title: str
    
    canonical_brand: Optional[str] = None
    canonical_model: Optional[str] = None
    canonical_mpn: Optional[str] = None
    canonical_gtins: List[str] = field(default_factory=list)
    canonical_condition_family: Optional[str] = None
    
    variation_signature: Optional[str] = None
    bundle_signature: Optional[str] = None
    
    source_count: int = 0
    matched_source_item_ids: List[str] = field(default_factory=list)
    
    match_confidence: float = 0.0
    ambiguity_flags: List[str] = field(default_factory=list)
    review_required: bool = False
    
    category_candidates: List[str] = field(default_factory=list)
    feature_payload: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class NormalizationResult:
    """The outcome of passing a raw item through the normalizer."""
    source_item_id: str
    normalized_item: NormalizedSourceItem
    candidate: Optional[CanonicalProductCandidate] = None
    evidence: Optional[MatchEvidence] = None
    status: str = "success"
    
    # Phase B Primary Outputs
    variation_decision: Optional[VariationDecision] = None
    bundle_decision: Optional[BundleDecision] = None
    ambiguity_flags: List[str] = field(default_factory=list)
    review_required: bool = False
    refined_match_confidence: float = 0.0
    explanation_lines: List[str] = field(default_factory=list)
    
    errors: List[str] = field(default_factory=list)
