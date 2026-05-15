from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class MonitoringReviseRequest:
    candidate_id: str
    run_id: Optional[str] = None
    sku: Optional[str] = None
    offer_id: Optional[str] = None
    listing_id: Optional[str] = None
    marketplace_id: str = "EBAY_US"
    dry_run: bool = False
    force_recheck: bool = False
    allow_quantity_zero: bool = True
    allow_withdraw: bool = True
    strictness: str = "balanced"
    max_retry: int = 1
    timeout_seconds: int = 30
    monitor_reason: str = "scheduled"

@dataclass
class MonitoringReviseResult:
    candidate_id: str
    sku: str
    monitoring_status: str = "not_started"  # not_started, running, kept, revised, quantity_zeroed, withdrawn, review_required, retryable_error, failed, skipped
    source_state_status: str = "unknown"
    marketplace_state_status: str = "unknown"
    profit_recalculation_status: str = "unknown"
    revise_action: str = "keep"  # keep, revise_price, revise_quantity, revise_price_quantity, set_quantity_zero, withdraw_offer, review_required
    revise_status: str = "not_needed" # not_needed, updated, failed, skipped
    withdraw_status: str = "not_needed" # not_needed, withdrawn, failed, skipped
    retryable_flag: bool = False
    review_required_flag: bool = False
    monitoring_reason_codes: List[str] = field(default_factory=list)
    error_summary: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    success_flag: bool = False

@dataclass
class MonitoringReviseBatchResult:
    run_id: str
    processed_count: int = 0
    keep_count: int = 0
    revised_count: int = 0
    zeroed_count: int = 0
    withdrawn_count: int = 0
    review_count: int = 0
    retryable_error_count: int = 0
    fatal_error_count: int = 0
    error_summary: Optional[str] = None
