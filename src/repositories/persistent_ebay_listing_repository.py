from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.ebay.models import EbayListing
from src.db.models import EbayListingModel

class PersistentEbayListingRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, listing: EbayListing):
        model = self._to_model(listing)
        self.session.add(model)

    def upsert(self, listing: EbayListing):
        existing = self.get_by_sku(listing.sku)
        if existing:
            model_data = self._to_dict(listing)
            stmt = update(EbayListingModel).where(EbayListingModel.sku == listing.sku).values(**model_data)
            self.session.execute(stmt)
        else:
            self.save(listing)

    def get_by_sku(self, sku: str) -> Optional[EbayListing]:
        stmt = select(EbayListingModel).where(EbayListingModel.sku == sku)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def get_by_candidate_id(self, candidate_id: str) -> Optional[EbayListing]:
        stmt = select(EbayListingModel).where(EbayListingModel.candidate_id == candidate_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def get_by_offer_id(self, offer_id: str) -> Optional[EbayListing]:
        stmt = select(EbayListingModel).where(EbayListingModel.offer_id == offer_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def list_active(self, limit: Optional[int] = None) -> List[EbayListing]:
        stmt = select(EbayListingModel).where(EbayListingModel.offer_status == "published")
        if limit:
            stmt = stmt.limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def _to_model(self, listing: EbayListing) -> EbayListingModel:
        return EbayListingModel(**self._to_dict(listing))

    def _to_dict(self, listing: EbayListing) -> dict:
        return {
            "sku": listing.sku,
            "candidate_id": listing.candidate_id,
            "marketplace_id": listing.marketplace_id,
            "inventory_item_status": listing.inventory_item_status,
            "offer_id": listing.offer_id,
            "offer_status": listing.offer_status,
            "listing_id": listing.listing_id,
            "listing_price_usd": listing.listing_price_usd,
            "quantity": listing.quantity,
            "merchant_location_key": listing.merchant_location_key,
            "fulfillment_policy_id": listing.fulfillment_policy_id,
            "payment_policy_id": listing.payment_policy_id,
            "return_policy_id": listing.return_policy_id,
            "last_publish_attempt_at": listing.last_publish_attempt_at,
            "last_publish_error": listing.last_publish_error,
            "last_revise_error": listing.last_revise_error,
            "listed_at": listing.listed_at
        }

    def _to_domain(self, model: EbayListingModel) -> EbayListing:
        return EbayListing(
            sku=model.sku,
            candidate_id=model.candidate_id,
            marketplace_id=model.marketplace_id,
            inventory_item_status=model.inventory_item_status,
            offer_id=model.offer_id,
            offer_status=model.offer_status,
            listing_id=model.listing_id,
            listing_price_usd=model.listing_price_usd,
            quantity=model.quantity,
            merchant_location_key=model.merchant_location_key,
            fulfillment_policy_id=model.fulfillment_policy_id,
            payment_policy_id=model.payment_policy_id,
            return_policy_id=model.return_policy_id,
            last_publish_attempt_at=model.last_publish_attempt_at,
            last_publish_error=model.last_publish_error,
            last_revise_error=model.last_revise_error,
            listed_at=model.listed_at,
            updated_at=model.updated_at
        )
