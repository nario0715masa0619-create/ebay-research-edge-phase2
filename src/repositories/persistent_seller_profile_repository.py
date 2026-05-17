from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import SellerProfileModel
from src.seller_env.models import SellerProfile

class PersistentSellerProfileRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, profile: SellerProfile):
        model = self.session.execute(
            select(SellerProfileModel).where(SellerProfileModel.seller_account_id == profile.seller_account_id)
        ).scalar_one_or_none()
        
        if not model:
            model = SellerProfileModel(seller_account_id=profile.seller_account_id)
            self.session.add(model)
            
        model.seller_name = profile.seller_name
        model.seller_label = profile.seller_label
        model.enabled = profile.enabled
        model.environment_mode = profile.environment_mode
        model.default_marketplace_id = profile.default_marketplace_id
        model.default_currency = profile.default_currency
        model.default_merchant_location_key = profile.default_merchant_location_key
        model.default_fulfillment_policy_id = profile.default_fulfillment_policy_id
        model.default_payment_policy_id = profile.default_payment_policy_id
        model.default_return_policy_id = profile.default_return_policy_id
        model.auth_profile_ref = profile.auth_profile_ref
        model.notification_profile_ref = profile.notification_profile_ref
        model.scheduling_profile_ref = profile.scheduling_profile_ref
        model.tags_json = profile.tags
        model.updated_at = profile.updated_at
        
        self.session.flush()

    def get_by_id(self, seller_account_id: str) -> Optional[SellerProfile]:
        model = self.session.execute(
            select(SellerProfileModel).where(SellerProfileModel.seller_account_id == seller_account_id)
        ).scalar_one_or_none()
        if not model: return None
        return self._to_domain(model)

    def list_all(self, enabled_only: bool = False) -> List[SellerProfile]:
        stmt = select(SellerProfileModel)
        if enabled_only:
            stmt = stmt.where(SellerProfileModel.enabled == True)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: SellerProfileModel) -> SellerProfile:
        return SellerProfile(
            seller_account_id=model.seller_account_id,
            seller_name=model.seller_name,
            seller_label=model.seller_label,
            enabled=model.enabled,
            environment_mode=model.environment_mode,
            default_marketplace_id=model.default_marketplace_id,
            default_currency=model.default_currency,
            default_merchant_location_key=model.default_merchant_location_key,
            default_fulfillment_policy_id=model.default_fulfillment_policy_id,
            default_payment_policy_id=model.default_payment_policy_id,
            default_return_policy_id=model.default_return_policy_id,
            auth_profile_ref=model.auth_profile_ref,
            notification_profile_ref=model.notification_profile_ref,
            scheduling_profile_ref=model.scheduling_profile_ref,
            tags=model.tags_json or [],
            created_at=model.created_at,
            updated_at=model.updated_at
        )
