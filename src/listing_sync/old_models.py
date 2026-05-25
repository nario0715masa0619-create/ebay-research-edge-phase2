from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class ListingSyncRequest:
    candidate_id: str
    sku: str
    run_id: Optional[str] = None
    offer_id: Optional[str] = None
    listing_id: Optional[str] = None
    marketplace_id: str = "EBAY_US"
    dry_run: bool = False
    force_recheck: bool = False
    allow_recover_offer: bool = True
    allow_recover_inventory: bool = True
    allow_repair_db_state: bool = True
    allow_zero_quantity_reconcile: bool = True
    allow_withdraw_reconcile: bool = True
    strictness: str = "balanced"
    max_retry: int = 1
    sync_reason: str = "scheduled"

@dataclass
class ListingSyncResult:
    candidate_id: str
    sku: str
    sync_status: str = "pending" # 'synced', 'repaired', 'unchanged', 'review_required', 'failed'
    recovery_status: str = "none"
    ebay_offer_found: bool = False
    ebay_inventory_found: bool = False
    db_state_status: str = "unknown"
    ebay_state_status: str = "unknown"
    detected_drift_types: List[str] = field(default_factory=list)
    recovery_action: str = "none"
    recovery_applied_flag: bool = False
    review_required_flag: bool = False
    retryable_flag: bool = False
    offer_id: Optional[str] = None
    listing_id: Optional[str] = None
    remote_price: Optional[float] = None
    remote_quantity: Optional[int] = None
    remote_listing_status: Optional[str] = None
    remote_offer_status: Optional[str] = None
    error_summary: Optional[str] = None
    reason_codes: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    success_flag: bool = False

@dataclass
class ListingSyncBatchResult:
    run_id: str
    processed_count: int = 0
    synced_count: int = 0
    repaired_count: int = 0
    unchanged_count: int = 0
    review_count: int = 0
    retryable_error_count: int = 0
    fatal_error_count: int = 0
    skipped_count: int = 0
    error_summary: List[str] = field(default_factory=list)
