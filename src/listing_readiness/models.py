from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ListingReadinessRequest:
    candidate_id: str
    run_id: Optional[str] = None
    force_recheck: bool = False
    marketplace_id: str = "EBAY_US"
    category_tree_id: Optional[str] = None
    strictness: str = "balanced"
    allow_default_policy_reference: bool = True
    allow_incomplete_recommended_aspects: bool = True
    title_max_length: int = 80
    description_template_version: str = "v1"

@dataclass
class ListingReadinessResult:
    candidate_id: str
    sku: str
    listing_readiness_status: str  # not_checked, checking, blocked, review_required, ready
    publish_readiness: bool
    ebay_category_id: Optional[str] = None
    ebay_condition: Optional[str] = None
    ebay_aspects_json: Dict[str, Any] = field(default_factory=dict)
    missing_required_aspects: List[str] = field(default_factory=list)
    missing_recommended_aspects: List[str] = field(default_factory=list)
    listing_blockers: List[str] = field(default_factory=list)
    readiness_reason_codes: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    inventory_item_draft: Dict[str, Any] = field(default_factory=dict)
    offer_draft: Dict[str, Any] = field(default_factory=dict)
    success_flag: bool = False

@dataclass
class ListingReadinessBatchResult:
    run_id: str
    processed_count: int = 0
    ready_count: int = 0
    blocked_count: int = 0
    review_count: int = 0
    error_count: int = 0
    error_summary: List[str] = field(default_factory=list)
