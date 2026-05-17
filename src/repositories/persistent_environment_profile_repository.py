from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import EnvironmentProfileModel
from src.seller_env.models import EnvironmentProfile

class PersistentEnvironmentProfileRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, profile: EnvironmentProfile):
        model = self.session.execute(
            select(EnvironmentProfileModel).where(EnvironmentProfileModel.environment_id == profile.environment_id)
        ).scalar_one_or_none()
        
        if not model:
            model = EnvironmentProfileModel(environment_id=profile.environment_id)
            self.session.add(model)
            
        model.environment_name = profile.environment_name
        model.environment_type = profile.environment_type
        model.enabled = profile.enabled
        model.ebay_api_base_url = profile.ebay_api_base_url
        model.ebay_oauth_base_url = profile.ebay_oauth_base_url
        model.application_keyset_ref = profile.application_keyset_ref
        model.supports_live_publish = profile.supports_live_publish
        model.supports_test_users = profile.supports_test_users
        model.notes = profile.notes
        model.updated_at = profile.updated_at
        
        self.session.flush()

    def get_by_id(self, environment_id: str) -> Optional[EnvironmentProfile]:
        model = self.session.execute(
            select(EnvironmentProfileModel).where(EnvironmentProfileModel.environment_id == environment_id)
        ).scalar_one_or_none()
        if not model: return None
        return self._to_domain(model)

    def list_all(self, enabled_only: bool = False) -> List[EnvironmentProfile]:
        stmt = select(EnvironmentProfileModel)
        if enabled_only:
            stmt = stmt.where(EnvironmentProfileModel.enabled == True)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: EnvironmentProfileModel) -> EnvironmentProfile:
        return EnvironmentProfile(
            environment_id=model.environment_id,
            environment_name=model.environment_name,
            environment_type=model.environment_type,
            enabled=model.enabled,
            ebay_api_base_url=model.ebay_api_base_url,
            ebay_oauth_base_url=model.ebay_oauth_base_url,
            application_keyset_ref=model.application_keyset_ref,
            supports_live_publish=model.supports_live_publish,
            supports_test_users=model.supports_test_users,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
