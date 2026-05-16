from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.ebay.models import ProductCandidate
from src.db.models import ProductCandidateModel

class PersistentProductCandidateRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, candidate: ProductCandidate):
        model = self._to_model(candidate)
        self.session.add(model)

    def upsert(self, candidate: ProductCandidate):
        existing = self.get_by_candidate_id(candidate.candidate_id)
        if existing:
            # Simplified update: replace most fields
            model_data = self._to_dict(candidate)
            stmt = update(ProductCandidateModel).where(ProductCandidateModel.candidate_id == candidate.candidate_id).values(**model_data)
            self.session.execute(stmt)
        else:
            self.save(candidate)

    def get_by_candidate_id(self, candidate_id: str) -> Optional[ProductCandidate]:
        stmt = select(ProductCandidateModel).where(ProductCandidateModel.candidate_id == candidate_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def get_by_source_key(self, platform: str, source_item_id: str) -> Optional[ProductCandidate]:
        stmt = select(ProductCandidateModel).where(ProductCandidateModel.source_platform == platform, ProductCandidateModel.source_item_id == source_item_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def get_by_sku(self, sku: str) -> Optional[ProductCandidate]:
        stmt = select(ProductCandidateModel).where(ProductCandidateModel.sku == sku)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def list_by_status(self, status: str, limit: Optional[int] = None) -> List[ProductCandidate]:
        stmt = select(ProductCandidateModel).where(ProductCandidateModel.status == status)
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def list_listing_ready(self, limit: Optional[int] = None) -> List[ProductCandidate]:
        stmt = select(ProductCandidateModel).where(ProductCandidateModel.listing_readiness_status == "ready")
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def list_listed(self, limit: Optional[int] = None) -> List[ProductCandidate]:
        stmt = select(ProductCandidateModel).where(ProductCandidateModel.status == "listed")
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def _to_model(self, candidate: ProductCandidate) -> ProductCandidateModel:
        return ProductCandidateModel(**self._to_dict(candidate))

    def _to_dict(self, candidate: ProductCandidate) -> dict:
        return {
            "candidate_id": candidate.candidate_id,
            "source_item_id": candidate.source_item_id,
            "source_platform": candidate.source_platform,
            "sku": candidate.sku,
            "source_url": candidate.source_url,
            "source_title": candidate.source_title,
            "source_price_jpy": candidate.source_price_jpy,
            "source_shipping_jpy": candidate.source_shipping_jpy,
            "source_stock_status": candidate.source_stock_status,
            "source_purchase_type": candidate.source_purchase_type,
            "image_urls_json": candidate.image_urls,
            "condition_source": candidate.condition_source,
            "pipeline_type": candidate.pipeline_type,
            "decision_type": candidate.decision_type,
            "status": candidate.status,
            "brand": candidate.brand,
            "series": candidate.series,
            "character": candidate.character,
            "product_type": candidate.product_type,
            "ebay_title_candidate": candidate.ebay_title_candidate,
            "ebay_category_id": candidate.ebay_category_id,
            "ebay_condition": candidate.ebay_condition,
            "ebay_aspects_json": candidate.ebay_aspects_json,
            "missing_required_aspects_json": candidate.missing_required_aspects,
            "listing_readiness_status": candidate.listing_readiness_status,
            "publish_readiness": candidate.publish_readiness,
            "listing_blockers_json": candidate.listing_blockers,
            "inventory_item_draft_json": candidate.inventory_item_draft_json,
            "offer_draft_json": candidate.offer_draft_json,
            "expected_sale_price_usd": candidate.expected_sale_price_usd,
            "expected_profit_jpy": candidate.expected_profit_jpy,
            "expected_profit_rate": candidate.expected_profit_rate,
            "standard_score": candidate.standard_score,
            "auto_listable": candidate.auto_listable,
            "exclude_reason": candidate.exclude_reason,
            "review_reason": candidate.review_reason,
            "decision_reason_codes_json": candidate.decision_reason_codes,
            "last_rule_version": candidate.last_rule_version,
            "last_checked_at": candidate.last_checked_at
        }

    def _to_domain(self, model: ProductCandidateModel) -> ProductCandidate:
        return ProductCandidate(
            candidate_id=model.candidate_id,
            source_item_id=model.source_item_id,
            source_platform=model.source_platform,
            sku=model.sku,
            source_url=model.source_url,
            source_title=model.source_title,
            source_price_jpy=model.source_price_jpy,
            source_shipping_jpy=model.source_shipping_jpy,
            source_stock_status=model.source_stock_status,
            source_purchase_type=model.source_purchase_type,
            image_urls=model.image_urls_json or [],
            condition_source=model.condition_source,
            pipeline_type=model.pipeline_type,
            decision_type=model.decision_type,
            status=model.status,
            brand=model.brand,
            series=model.series,
            character=model.character,
            product_type=model.product_type,
            ebay_title_candidate=model.ebay_title_candidate,
            ebay_category_id=model.ebay_category_id,
            ebay_condition=model.ebay_condition,
            ebay_aspects_json=model.ebay_aspects_json or {},
            missing_required_aspects=model.missing_required_aspects_json or [],
            listing_readiness_status=model.listing_readiness_status,
            publish_readiness=model.publish_readiness,
            listing_blockers=model.listing_blockers_json or [],
            inventory_item_draft_json=model.inventory_item_draft_json or {},
            offer_draft_json=model.offer_draft_json or {},
            expected_sale_price_usd=model.expected_sale_price_usd,
            expected_profit_jpy=model.expected_profit_jpy,
            expected_profit_rate=model.expected_profit_rate,
            standard_score=model.standard_score,
            auto_listable=model.auto_listable,
            exclude_reason=model.exclude_reason,
            review_reason=model.review_reason,
            decision_reason_codes=model.decision_reason_codes_json or [],
            last_rule_version=model.last_rule_version,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_checked_at=model.last_checked_at
        )
