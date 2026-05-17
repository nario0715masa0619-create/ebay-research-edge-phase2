from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DashboardSummaryView(BaseModel):
    active_seller_id: str
    active_environment: str
    active_marketplace: str
    failed_jobs_count: int = 0
    review_queue_count: int = 0
    recent_notifications_count: int = 0
    recent_drifts_count: int = 0
    recent_jobruns: List[Dict[str, Any]] = []
    recent_notifications: List[Dict[str, Any]] = []
    doctor_alert: Optional[str] = None

class SellerSummaryView(BaseModel):
    seller_account_id: str
    seller_name: str
    seller_label: str
    enabled: bool
    environment_mode: str
    default_marketplace_id: str
    has_policy_setup: bool
    has_location_setup: bool
    latest_doctor_status: str = "unknown"

class JobDefinitionView(BaseModel):
    job_name: str
    enabled: bool
    schedule_type: str
    last_run_status: str = "never_run"
    last_run_started_at: Optional[str] = None
    last_run_finished_at: Optional[str] = None
    failure_reason: Optional[str] = None

class CandidateSummaryView(BaseModel):
    sku: str
    title: str
    status: str
    decision_type: str
    listing_readiness_status: str
    standard_score: float = 0.0
    expected_profit_jpy: float = 0.0
    seller_account_id: str
    environment_type: str

class ListingSummaryView(BaseModel):
    sku: str
    listing_status: str
    offer_status: str
    marketplace_id: str
    price: float = 0.0
    quantity: int = 0
    last_synced_at: Optional[str] = None
    seller_account_id: str
    environment_type: str

class ReviewItemView(BaseModel):
    candidate_id: str
    sku: str
    source_platform: str
    review_reason: str
    severity: str
    created_at: str
    seller_account_id: str
    environment_type: str

class NotificationHistoryView(BaseModel):
    history_id: str
    event_type: str
    severity: str
    channel: str
    status: str
    provider_message_id: Optional[str] = None
    created_at: str
    sku: Optional[str] = None
    seller_account_id: Optional[str] = None
    environment_type: Optional[str] = None

class DoctorCheckView(BaseModel):
    db_status: str = "ok"
    auth_status: str = "ok"
    scheduler_status: str = "ok"
    notification_status: str = "ok"
    seller_env_consistency: str = "consistent"
    policy_completeness: str = "complete"
    read_only_mode: bool = False
