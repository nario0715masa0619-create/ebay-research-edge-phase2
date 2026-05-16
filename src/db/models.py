from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Float, Integer, DateTime, JSON, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class SourceItemModel(Base):
    __tablename__ = "source_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    source_item_id: Mapped[str] = mapped_column(String(255), index=True)
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
    evidence_payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    rule_version: Mapped[str] = mapped_column(String(50), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class EbayListingModel(Base):
    __tablename__ = "ebay_listings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(255), ForeignKey("product_candidates.candidate_id"))
    marketplace_id: Mapped[str] = mapped_column(String(50))
    
    inventory_item_status: Mapped[str] = mapped_column(String(50), default="not_created")
    offer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    offer_status: Mapped[str] = mapped_column(String(50), default="not_created")
    listing_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    
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
