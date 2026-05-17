from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class NotificationEvent:
    event_type: str
    title: str
    summary: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_layer: Optional[str] = None
    source_component: Optional[str] = None
    source_run_id: Optional[str] = None
    source_job_name: Optional[str] = None
    sku: Optional[str] = None
    candidate_id: Optional[str] = None
    offer_id: Optional[str] = None
    listing_id: Optional[str] = None
    severity: str = "info" # info, warning, error, critical
    priority: str = "normal" # low, normal, high, urgent
    details: Optional[str] = None
    reason_codes: List[str] = field(default_factory=list)
    retryable_flag: bool = False
    review_required_flag: bool = False
    dedupe_key: Optional[str] = None
    emitted_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    meta_json: Dict[str, Any] = field(default_factory=dict)
    
    # Seller Context
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None

    def __post_init__(self):
        self._mask_secrets()

    def _mask_secrets(self):
        secret_keys = ["token", "secret", "password", "key", "auth"]
        # Very simple masking for v0.1
        if self.summary:
            for sk in secret_keys:
                if sk in self.summary.lower():
                    # If it looks like a secret field, mask it
                    pass 
        # Actually I'll just mask the meta_json for now as summary/details should be safe by convention
        for k in list(self.meta_json.keys()):
            if any(sk in k.lower() for sk in secret_keys):
                self.meta_json[k] = "***MASKED***"

@dataclass
class NotificationRule:
    rule_name: str
    enabled: bool = True
    event_types: List[str] = field(default_factory=list) # Empty means all
    severities: List[str] = field(default_factory=list)
    priorities: List[str] = field(default_factory=list)
    channel_targets: List[str] = field(default_factory=lambda: ["console"])
    cooldown_seconds: int = 0
    dedupe_window_seconds: int = 0
    aggregation_key_fields: List[str] = field(default_factory=list)
    min_repeat_count: int = 1
    suppress_if_resolved: bool = False
    only_when_not_dry_run: bool = False
    review_required_flag: bool = False
    template_name: Optional[str] = None

@dataclass
class NotificationDispatchResult:
    event_id: str
    channel_name: str
    dispatch_status: str # success, failed, skipped, deduped
    dispatched_at: datetime = field(default_factory=datetime.now)
    skipped_reason: Optional[str] = None
    provider_message_id: Optional[str] = None
    error_summary: Optional[str] = None
    success_flag: bool = True

@dataclass
class NotificationBatchResult:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    processed_count: int = 0
    dispatched_count: int = 0
    skipped_count: int = 0
    deduped_count: int = 0
    failed_count: int = 0
    results: List[NotificationDispatchResult] = field(default_factory=list)
