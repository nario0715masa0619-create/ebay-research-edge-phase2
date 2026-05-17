from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Float, Integer, DateTime, JSON, ForeignKey, Boolean, Text, Index
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
