from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class EbayApiItemSummary:
    item_id: str
    title: str
    price: Dict[str, str]  # {"value": "100.00", "currency": "USD"}
    shipping_options: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EbayApiItemDetail:
    item_id: str
    title: str
    price: Dict[str, str]
    shipping_options: List[Dict[str, Any]] = field(default_factory=list)
    taxes: List[Dict[str, Any]] = field(default_factory=list)
    return_terms: Dict[str, Any] = field(default_factory=dict)
    estimated_import_costs: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SourceItem:
    source_item_id: str
    source_platform: str
    source_url: str
    source_title: str
    source_price_jpy: float
    source_shipping_jpy: float = 0.0
    source_stock_status: str = "in_stock"
    source_purchase_type: str = "buy_now"
    source_image_urls: List[str] = field(default_factory=list)
    source_raw_json: Dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

@dataclass
class ProductCandidate:
    candidate_id: str
    source_item_id: str
    source_platform: str
    sku: str
    
    # Platform Info
    source_url: str
    source_title: str
    source_price_jpy: float
    source_shipping_jpy: float = 0.0
    source_stock_status: str = "in_stock"
    source_purchase_type: str = "buy_now"
    image_urls: List[str] = field(default_factory=list)
    condition_source: str = "new"
    
    # Classification
    pipeline_type: str = "auto"  # auto, manual_preban, manual_review
    decision_type: str = "excluded"  # candidate, excluded, review_required, listing_ready
    status: str = "collected"  # collected, normalized, researched, candidate, listed, etc.
    
    # Normalized Data
    normalized_title: str = ""
    brand: str = ""
    series: str = ""
    character: str = ""
    product_type: str = ""
    ebay_title_candidate: str = ""
    
    # Marketplace Metadata
    ebay_category_id: Optional[str] = None
    category_tree_id: Optional[str] = None
    category_tree_version: Optional[str] = None
    category_confidence: float = 0.0
    
    ebay_condition: Optional[str] = None
    condition_descriptor_json: Dict[str, Any] = field(default_factory=dict)
    condition_confidence: float = 0.0
    
    ebay_aspects_json: Dict[str, Any] = field(default_factory=dict)
    missing_required_aspects: List[str] = field(default_factory=list)
    missing_recommended_aspects: List[str] = field(default_factory=list)
    
    listing_readiness_status: str = "not_checked"
    listing_blockers: List[str] = field(default_factory=list)
    publish_readiness: bool = False
    
    inventory_item_draft_json: Dict[str, Any] = field(default_factory=dict)
    offer_draft_json: Dict[str, Any] = field(default_factory=dict)
    
    # Financials
    expected_sale_price_usd: float = 0.0
    expected_sale_price_jpy: float = 0.0
    expected_profit_jpy: float = 0.0
    expected_profit_rate: float = 0.0
    standard_score: float = 0.0
    score_grade: str = "E"
    
    # Decisions
    auto_listable: bool = False
    exclude_reason: Optional[str] = None
    review_reason: Optional[str] = None
    decision_reason_codes: List[str] = field(default_factory=list)
    
    # Metadata
    evidence_json: Dict[str, Any] = field(default_factory=dict)
    scoring_json: Dict[str, Any] = field(default_factory=dict)
    last_rule_version: str = "v1"
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_checked_at: Optional[datetime] = None
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None
    marketplace_id: Optional[str] = None

@dataclass
class CandidateEvidence:
    evidence_id: str
    candidate_id: str
    evidence_type: str  # normalization, pricing, shipping, total_cost, score, etc.
    evidence_payload: Dict[str, Any]
    rule_version: str = "v1"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class JobRun:
    run_id: str
    job_name: str
    job_scope: str = "all"
    status: str = "running"  # running, completed, failed
    context: Dict[str, Any] = field(default_factory=dict)
    
    processed_count: int = 0
    success_count: int = 0
    excluded_count: int = 0
    review_count: int = 0
    candidate_count: int = 0
    ready_count: int = 0
    blocked_count: int = 0
    
    # Execution Specific
    skipped_count: int = 0
    retryable_error_count: int = 0
    review_required_count: int = 0
    fatal_error_count: int = 0
    
    # Monitoring Specific
    keep_count: int = 0
    revised_count: int = 0
    zeroed_count: int = 0
    withdrawn_count: int = 0
    
    error_count: int = 0
    error_summary: Optional[str] = None
    
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None
    marketplace_id: Optional[str] = None

@dataclass
class MonitoringEvent:
    event_id: str
    candidate_id: str
    sku: str
    event_scope: str # source, marketplace, internal
    event_type: str # price_change, stock_change, url_dead, etc.
    before_value: str
    after_value: str
    action_taken: str # keep, revise, withdraw, etc.
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EbayListing:
    sku: str
    candidate_id: str
    marketplace_id: str
    
    inventory_item_status: str = "not_created" # not_created, created, updated, failed
    offer_id: Optional[str] = None
    offer_status: str = "not_created" # not_created, created, published, failed
    listing_id: Optional[str] = None
    listing_status: Optional[str] = None # ACTIVE, ENDED, OUT_OF_STOCK
    
    listing_price_usd: float = 0.0
    quantity: int = 1
    
    merchant_location_key: Optional[str] = None
    fulfillment_policy_id: Optional[str] = None
    payment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    
    last_publish_attempt_at: Optional[datetime] = None
    last_publish_error: Optional[str] = None
    last_revise_error: Optional[str] = None
    
    listed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None
