from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ListingExecutionRequest:
    candidate_id: str
    run_id: Optional[str] = None
    marketplace_id: str = "EBAY_US"
    dry_run: bool = False
    force_republish: bool = False
    create_location_if_missing: bool = False
    strictness: str = "balanced"
    max_retry: int = 1
    timeout_seconds: int = 30

@dataclass
class ListingExecutionResult:
    candidate_id: str
    sku: str
    execution_status: str = "not_started"  # not_started, running, succeeded, partial_success, retryable_error, review_required, failed, skipped
    inventory_item_status: str = "not_created"
    offer_status: str = "not_created"
    publish_status: str = "not_published"
    offer_id: Optional[str] = None
    listing_id: Optional[str] = None
    execution_reason_codes: List[str] = field(default_factory=list)
    retryable_flag: bool = False
    review_required_flag: bool = False
    error_summary: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    success_flag: bool = False

@dataclass
class ListingExecutionBatchResult:
    run_id: str
    processed_count: int = 0
    success_count: int = 0
    skipped_count: int = 0
    retryable_error_count: int = 0
    review_required_count: int = 0
    fatal_error_count: int = 0
    error_summary: Optional[str] = None
