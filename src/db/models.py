from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Float, Integer, DateTime, JSON, ForeignKey, Boolean, Text, Index, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class SourceItemModel(Base):
    __tablename__ = "source_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    source_item_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_platform: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str] = mapped_column(String(1024))
    source_title: Mapped[str] = mapped_column(String(512))
    source_price_jpy: Mapped[float] = mapped_column(Float)
    source_shipping_jpy: Mapped[float] = mapped_column(Float, default=0.0)
    source_stock_status: Mapped[str] = mapped_column(String(50), default="in_stock")
    source_purchase_type: Mapped[str] = mapped_column(String(50), default="buy_now")
    image_urls_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    raw_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_source_platform_url", "source_platform", "source_url", unique=True),
    )

class ProductCandidateModel(Base):
    __tablename__ = "product_candidates"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_item_id: Mapped[str] = mapped_column(String(255), ForeignKey("source_items.source_item_id"))
    source_platform: Mapped[str] = mapped_column(String(50))
    sku: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    marketplace_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    source_url: Mapped[str] = mapped_column(String(1024))
    source_title: Mapped[str] = mapped_column(String(512))
    source_price_jpy: Mapped[float] = mapped_column(Float)
    source_shipping_jpy: Mapped[float] = mapped_column(Float, default=0.0)
    source_stock_status: Mapped[str] = mapped_column(String(50), default="in_stock")
    source_purchase_type: Mapped[str] = mapped_column(String(50), default="buy_now")
    image_urls_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    condition_source: Mapped[str] = mapped_column(String(50), default="new")
    
    pipeline_type: Mapped[str] = mapped_column(String(50), default="auto")
    decision_type: Mapped[str] = mapped_column(String(50), default="excluded")
    status: Mapped[str] = mapped_column(String(50), index=True)
    
    brand: Mapped[Optional[str]] = mapped_column(String(255))
    series: Mapped[Optional[str]] = mapped_column(String(255))
    character: Mapped[Optional[str]] = mapped_column(String(255))
    product_type: Mapped[Optional[str]] = mapped_column(String(255))
    ebay_title_candidate: Mapped[Optional[str]] = mapped_column(String(255))
    
    ebay_category_id: Mapped[Optional[str]] = mapped_column(String(50))
    ebay_condition: Mapped[Optional[str]] = mapped_column(String(50))
    ebay_aspects_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    missing_required_aspects_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    listing_readiness_status: Mapped[str] = mapped_column(String(50), default="not_checked", index=True)
    publish_readiness: Mapped[bool] = mapped_column(Boolean, default=False)
    listing_blockers_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    inventory_item_draft_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    offer_draft_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    expected_sale_price_usd: Mapped[float] = mapped_column(Float, default=0.0)
    expected_profit_jpy: Mapped[float] = mapped_column(Float, default=0.0)
    expected_profit_rate: Mapped[float] = mapped_column(Float, default=0.0)
    standard_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    auto_listable: Mapped[bool] = mapped_column(Boolean, default=False)
    exclude_reason: Mapped[Optional[str]] = mapped_column(String(255))
    review_reason: Mapped[Optional[str]] = mapped_column(String(255))
    decision_reason_codes_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    last_rule_version: Mapped[str] = mapped_column(String(50), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

class CandidateEvidenceModel(Base):
    __tablename__ = "candidate_evidences"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey("product_candidates.candidate_id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), index=True)
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    evidence_payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    rule_version: Mapped[str] = mapped_column(String(50), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class EbayListingModel(Base):
    __tablename__ = "ebay_listings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey("product_candidates.candidate_id"))
    marketplace_id: Mapped[str] = mapped_column(String(50))
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    inventory_item_status: Mapped[str] = mapped_column(String(50), default="not_created")
    offer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    offer_status: Mapped[str] = mapped_column(String(50), default="not_created")
    listing_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    listing_status: Mapped[Optional[str]] = mapped_column(String(50))
    
    listing_price_usd: Mapped[float] = mapped_column(Float, default=0.0)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    merchant_location_key: Mapped[Optional[str]] = mapped_column(String(255))
    fulfillment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    payment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    return_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    last_publish_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_publish_error: Mapped[Optional[str]] = mapped_column(Text)
    last_revise_error: Mapped[Optional[str]] = mapped_column(Text)
    
    listed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class MonitoringEventModel(Base):
    __tablename__ = "monitoring_events"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey("product_candidates.candidate_id"))
    sku: Mapped[str] = mapped_column(String(255), index=True)
    event_scope: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(String(50))
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    before_value: Mapped[Optional[str]] = mapped_column(Text)
    after_value: Mapped[Optional[str]] = mapped_column(Text)
    action_taken: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class JobRunModel(Base):
    __tablename__ = "job_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    job_name: Mapped[str] = mapped_column(String(255), index=True)
    job_scope: Mapped[str] = mapped_column(String(50), default="all")
    status: Mapped[str] = mapped_column(String(50), default="running")
    context_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    marketplace_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    excluded_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    ready_count: Mapped[int] = mapped_column(Integer, default=0)
    blocked_count: Mapped[int] = mapped_column(Integer, default=0)
    
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    retryable_error_count: Mapped[int] = mapped_column(Integer, default=0)
    review_required_count: Mapped[int] = mapped_column(Integer, default=0)
    fatal_error_count: Mapped[int] = mapped_column(Integer, default=0)
    
    keep_count: Mapped[int] = mapped_column(Integer, default=0)
    revised_count: Mapped[int] = mapped_column(Integer, default=0)
    zeroed_count: Mapped[int] = mapped_column(Integer, default=0)
    withdrawn_count: Mapped[int] = mapped_column(Integer, default=0)
    
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class NotificationHistoryModel(Base):
    __tablename__ = "notification_histories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    source_layer: Mapped[Optional[str]] = mapped_column(String(100))
    source_run_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    priority: Mapped[str] = mapped_column(String(20))
    channel_name: Mapped[str] = mapped_column(String(50), index=True)
    dispatch_status: Mapped[str] = mapped_column(String(20)) # success, failed, skipped
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    meta_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255))
    error_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

class SellerProfileModel(Base):
    __tablename__ = "seller_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    seller_account_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    seller_name: Mapped[str] = mapped_column(String(255))
    seller_label: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    environment_mode: Mapped[str] = mapped_column(String(50), default="mixed") # sandbox, production, mixed
    default_marketplace_id: Mapped[str] = mapped_column(String(50))
    default_currency: Mapped[str] = mapped_column(String(10))
    
    default_merchant_location_key: Mapped[Optional[str]] = mapped_column(String(255))
    default_fulfillment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    default_payment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    default_return_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    auth_profile_ref: Mapped[Optional[str]] = mapped_column(String(255))
    notification_profile_ref: Mapped[Optional[str]] = mapped_column(String(255))
    scheduling_profile_ref: Mapped[Optional[str]] = mapped_column(String(255))
    
    tags_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class EnvironmentProfileModel(Base):
    __tablename__ = "environment_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    environment_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    environment_name: Mapped[str] = mapped_column(String(255))
    environment_type: Mapped[str] = mapped_column(String(50), index=True) # sandbox, production
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    ebay_api_base_url: Mapped[str] = mapped_column(String(255))
    ebay_oauth_base_url: Mapped[str] = mapped_column(String(255))
    application_keyset_ref: Mapped[Optional[str]] = mapped_column(String(255))
    
    supports_live_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_test_users: Mapped[bool] = mapped_column(Boolean, default=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class SellerEnvironmentBindingModel(Base):
    __tablename__ = "seller_environment_bindings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    binding_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    seller_account_id: Mapped[str] = mapped_column(String(255), ForeignKey("seller_profiles.seller_account_id"), index=True)
    environment_id: Mapped[str] = mapped_column(String(50), ForeignKey("environment_profiles.environment_id"), index=True)
    
    active_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    marketplace_id: Mapped[str] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10))
    merchant_location_key: Mapped[Optional[str]] = mapped_column(String(255))
    fulfillment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    payment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    return_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    refresh_token_ref: Mapped[Optional[str]] = mapped_column(String(255))
    auth_scope_profile: Mapped[Optional[str]] = mapped_column(String(255))
    notification_channel_profile: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_seller_env_unique", "seller_account_id", "environment_id", unique=True),
    )

class SellerPolicySnapshotModel(Base):
    __tablename__ = "seller_policy_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    seller_account_id: Mapped[str] = mapped_column(String(255), index=True)
    environment_id: Mapped[str] = mapped_column(String(50), index=True)
    marketplace_id: Mapped[str] = mapped_column(String(50), index=True)
    
    fulfillment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    payment_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    return_policy_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

class SellerLocationSnapshotModel(Base):
    __tablename__ = "seller_location_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    seller_account_id: Mapped[str] = mapped_column(String(255), index=True)
    environment_id: Mapped[str] = mapped_column(String(50), index=True)
    
    merchant_location_key: Mapped[str] = mapped_column(String(255), index=True)
    payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class EscalationStateModel(Base):
    __tablename__ = "escalation_states"
    
    state_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_event_id: Mapped[str] = mapped_column(String(255), index=True)
    source_history_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_event_type: Mapped[str] = mapped_column(String(100), index=True)
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    
    current_status: Mapped[str] = mapped_column(String(50), index=True)
    current_severity: Mapped[str] = mapped_column(String(50))
    current_priority: Mapped[str] = mapped_column(String(50))
    
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_reminded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    acked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acked_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    silenced_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # v0.2 Extensions
    aging_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aging_bucket: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sla_target_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sla_breached_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sla_breach_count: Mapped[int] = mapped_column(Integer, default=0)
    re_escalation_count: Mapped[int] = mapped_column(Integer, default=0)
    last_re_escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    maintenance_suppressed_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latest_note_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latest_note_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    route_snapshot_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    incident_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    source_status_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    meta_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_esc_aging_status", "aging_bucket", "current_status"),
        Index("idx_esc_sla_status", "sla_breached_at", "current_status"),
        Index("idx_esc_re_esc_status", "re_escalation_count", "current_status"),
    )


class EscalationStateTransitionModel(Base):
    __tablename__ = "escalation_state_transitions"
    
    transition_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    state_id: Mapped[str] = mapped_column(String(255), index=True)
    action_type: Mapped[str] = mapped_column(String(50))
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50))
    actor_type: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    meta_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class EscalationPolicyModel(Base):
    __tablename__ = "escalation_policies"
    
    policy_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    base_severity: Mapped[str] = mapped_column(String(50))
    
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    reminder_max_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allow_reminder_after_ack: Mapped[bool] = mapped_column(Boolean, default=False)
    silence_respected: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_resolve_on_source_recovery: Mapped[bool] = mapped_column(Boolean, default=True)
    
    escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    escalation_steps_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    dedupe_scope: Mapped[str] = mapped_column(String(100))
    
    # v0.2 Extensions
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    re_escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    re_escalation_interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    re_escalation_max_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sla_target_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sla_breach_severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sla_breach_priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    maintenance_window_respected: Mapped[bool] = mapped_column(Boolean, default=True)
    bulk_action_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    route_override_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_esc_policy_version_enabled", "policy_version", "enabled"),
    )

class EscalationNoteModel(Base):
    __tablename__ = "escalation_notes"
    
    note_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    state_id: Mapped[str] = mapped_column(String(255), index=True)
    author_id: Mapped[str] = mapped_column(String(255))
    author_type: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_esc_note_state_created", "state_id", "created_at"),
    )

class MaintenanceWindowModel(Base):
    __tablename__ = "maintenance_windows"
    
    window_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    seller_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    
    action: Mapped[str] = mapped_column(String(50), default="suppress_all") # suppress_reminder, suppress_escalation, suppress_all, downgrade_to_info
    reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_maint_enabled_times", "enabled", "starts_at", "ends_at"),
        Index("idx_maint_scope", "seller_account_id", "environment_type", "event_type"),
    )

class NormalizedSourceItemModel(Base):
    __tablename__ = "normalized_source_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_item_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source_item_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    normalized_title: Mapped[str] = mapped_column(Text)
    
    normalized_brand: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    normalized_model: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    normalized_mpn: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    strict_gtins_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    loose_gtins_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    normalized_condition: Mapped[Optional[str]] = mapped_column(String(50))
    normalized_quantity: Mapped[Optional[int]] = mapped_column(Integer)
    
    variation_keys_json: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    bundle_flags_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    parsed_attributes_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    identity_signals_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    normalization_flags_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CanonicalProductCandidateModel(Base):
    __tablename__ = "canonical_product_candidates"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    canonical_title: Mapped[str] = mapped_column(Text)
    
    canonical_brand: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    canonical_model: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    canonical_mpn: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    canonical_gtins_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    canonical_condition_family: Mapped[Optional[str]] = mapped_column(String(50))
    
    variation_signature: Mapped[Optional[str]] = mapped_column(String(500), index=True)
    bundle_signature: Mapped[Optional[str]] = mapped_column(String(500))
    
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_source_item_ids_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    match_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ambiguity_flags_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    category_candidates_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    feature_payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_canonical_brand_mpn", "canonical_brand", "canonical_mpn"),
        Index("idx_canonical_brand_model", "canonical_brand", "canonical_model"),
    )

class MatchEvidenceModel(Base):
    __tablename__ = "match_evidences"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    normalized_item_id: Mapped[str] = mapped_column(String(255), index=True)
    candidate_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    identifier_hits_json: Mapped[Optional[Dict[str, bool]]] = mapped_column(JSON)
    title_similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    brand_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    model_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    mpn_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    variation_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    bundle_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    condition_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    
    ambiguity_flags_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    explanation_lines_json: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AliasDictionaryModel(Base):
    __tablename__ = 'alias_dictionaries'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    alias_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    alias_type: Mapped[str] = mapped_column(String(50), index=True) # brand, model, mpn_rule, noise
    token: Mapped[str] = mapped_column(String(255), index=True)
    resolution: Mapped[str] = mapped_column(String(255))
    
    source_platform: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class ReviewAuditLogModel(Base):
    __tablename__ = 'review_audit_logs'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(50), index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    target_alias: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)



class MarketEvaluationResultModel(Base):
    __tablename__ = 'market_evaluation_results'

    id: Mapped[int] = mapped_column(primary_key=True)
    market_evaluation_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey('canonical_product_candidates.candidate_id'), index=True)
    evaluation_status: Mapped[str] = mapped_column(String(50), index=True)
    comparable_count: Mapped[int] = mapped_column(Integer, default=0)
    comparable_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    price_low: Mapped[Optional[float]] = mapped_column(Float)
    price_median: Mapped[Optional[float]] = mapped_column(Float)
    price_high: Mapped[Optional[float]] = mapped_column(Float)
    
    category_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    condition_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    attribute_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    competition_proxy: Mapped[Optional[str]] = mapped_column(String(50))
    demand_proxy: Mapped[Optional[str]] = mapped_column(String(50))
    market_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    unsafe_reasons_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    evidence_summary: Mapped[str] = mapped_column(Text, default='')
    
    search_queries_used_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    raw_result_count: Mapped[int] = mapped_column(Integer, default=0)
    filtered_result_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketEvaluationEvidenceModel(Base):
    __tablename__ = 'market_evaluation_evidences'

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey('canonical_product_candidates.candidate_id'), index=True)
    
    search_request_payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    provider_name: Mapped[str] = mapped_column(String(50))
    
    comparable_listing_ids_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    excluded_listing_ids_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    unsafe_reasons_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    evidence_lines_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    raw_response_reference: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class ProfitabilityScoreModel(Base):
    __tablename__ = 'profitability_scores'

    id: Mapped[int] = mapped_column(primary_key=True)
    profitability_score_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey('canonical_product_candidates.candidate_id'), index=True)
    market_evaluation_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey('market_evaluation_results.market_evaluation_id'), index=True)
    
    scoring_status: Mapped[str] = mapped_column(String(50), index=True)
    decision_status: Mapped[str] = mapped_column(String(50), index=True)
    review_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    expected_sale_price_low: Mapped[Optional[float]] = mapped_column(Float)
    expected_sale_price_base: Mapped[Optional[float]] = mapped_column(Float)
    expected_sale_price_high: Mapped[Optional[float]] = mapped_column(Float)
    
    expected_net_profit: Mapped[float] = mapped_column(Float, default=0.0)
    expected_margin: Mapped[float] = mapped_column(Float, default=0.0)
    expected_roi: Mapped[float] = mapped_column(Float, default=0.0)
    
    confidence_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    confidence_adjusted_profit: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    profitability_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    
    decision_reason: Mapped[str] = mapped_column(Text, default='')
    unsafe_reasons_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    explanation_lines_json: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    components_json: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

