from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import SellerEnvironmentBindingModel
from src.seller_env.models import SellerEnvironmentBinding

class PersistentSellerEnvironmentBindingRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, binding: SellerEnvironmentBinding):
        model = self.session.execute(
            select(SellerEnvironmentBindingModel).where(SellerEnvironmentBindingModel.binding_id == binding.binding_id)
        ).scalar_one_or_none()
        
        if not model:
            model = SellerEnvironmentBindingModel(binding_id=binding.binding_id)
            self.session.add(model)
            
        model.seller_account_id = binding.seller_account_id
        model.environment_id = binding.environment_id
        model.active_flag = binding.active_flag
        model.marketplace_id = binding.marketplace_id
        model.currency = binding.currency
        model.merchant_location_key = binding.merchant_location_key
        model.fulfillment_policy_id = binding.fulfillment_policy_id
        model.payment_policy_id = binding.payment_policy_id
        model.return_policy_id = binding.return_policy_id
        model.refresh_token_ref = binding.refresh_token_ref
        model.auth_scope_profile = binding.auth_scope_profile
        model.notification_channel_profile = binding.notification_channel_profile
        model.updated_at = binding.updated_at
        
        self.session.flush()

    def get_by_id(self, binding_id: str) -> Optional[SellerEnvironmentBinding]:
        model = self.session.execute(
            select(SellerEnvironmentBindingModel).where(SellerEnvironmentBindingModel.binding_id == binding_id)
        ).scalar_one_or_none()
        if not model: return None
        return self._to_domain(model)

    def get_active_for_seller(self, seller_account_id: str) -> Optional[SellerEnvironmentBinding]:
        stmt = select(SellerEnvironmentBindingModel).where(
            SellerEnvironmentBindingModel.seller_account_id == seller_account_id,
            SellerEnvironmentBindingModel.active_flag == True
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model: return None
        return self._to_domain(model)

    def list_all_active(self) -> List[SellerEnvironmentBinding]:
        stmt = select(SellerEnvironmentBindingModel).where(SellerEnvironmentBindingModel.active_flag == True)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_by_seller(self, seller_account_id: str) -> List[SellerEnvironmentBinding]:
        stmt = select(SellerEnvironmentBindingModel).where(SellerEnvironmentBindingModel.seller_account_id == seller_account_id)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: SellerEnvironmentBindingModel) -> SellerEnvironmentBinding:
        return SellerEnvironmentBinding(
            binding_id=model.binding_id,
            seller_account_id=model.seller_account_id,
            environment_id=model.environment_id,
            active_flag=model.active_flag,
            marketplace_id=model.marketplace_id,
            currency=model.currency,
            merchant_location_key=model.merchant_location_key,
            fulfillment_policy_id=model.fulfillment_policy_id,
            payment_policy_id=model.payment_policy_id,
            return_policy_id=model.return_policy_id,
            refresh_token_ref=model.refresh_token_ref,
            auth_scope_profile=model.auth_scope_profile,
            notification_channel_profile=model.notification_channel_profile,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
