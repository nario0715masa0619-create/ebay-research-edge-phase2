from typing import List, Dict, Any
from src.repositories.persistent_seller_profile_repository import PersistentSellerProfileRepository
from src.repositories.persistent_environment_profile_repository import PersistentEnvironmentProfileRepository
from src.repositories.persistent_seller_environment_binding_repository import PersistentSellerEnvironmentBindingRepository
from src.seller_env.models import SellerProfile, EnvironmentProfile, SellerEnvironmentBinding

class SellerOpsService:
    def __init__(self, seller_repo, env_repo, binding_repo):
        self.seller_repo = seller_repo
        self.env_repo = env_repo
        self.binding_repo = binding_repo

    def list_sellers(self) -> List[Dict[str, Any]]:
        sellers = self.seller_repo.list_all()
        return [self._profile_to_dict(s) for s in sellers]

    def list_environments(self) -> List[Dict[str, Any]]:
        envs = self.env_repo.list_all()
        return [self._env_to_dict(e) for e in envs]

    def list_bindings(self, seller_account_id: str = None) -> List[Dict[str, Any]]:
        if seller_account_id:
            bindings = self.binding_repo.list_by_seller(seller_account_id)
        else:
            # We need a list_all for bindings
            bindings = self.binding_repo.list_all_active() # For v0.1
        return [self._binding_to_dict(b) for b in bindings]

    def activate_binding(self, seller_account_id: str, environment_id: str) -> bool:
        # Deactivate others for this seller
        bindings = self.binding_repo.list_by_seller(seller_account_id)
        for b in bindings:
            if b.environment_id == environment_id:
                b.active_flag = True
            else:
                b.active_flag = False
            self.binding_repo.save(b)
        return True

    def _profile_to_dict(self, s: SellerProfile) -> Dict[str, Any]:
        return {
            "seller_account_id": s.seller_account_id,
            "label": s.seller_label,
            "enabled": s.enabled,
            "mode": s.environment_mode,
            "marketplace": s.default_marketplace_id
        }

    def _env_to_dict(self, e: EnvironmentProfile) -> Dict[str, Any]:
        return {
            "environment_id": e.environment_id,
            "type": e.environment_type,
            "enabled": e.enabled,
            "base_url": e.ebay_api_base_url
        }

    def _binding_to_dict(self, b: SellerEnvironmentBinding) -> Dict[str, Any]:
        return {
            "binding_id": b.binding_id,
            "seller_id": b.seller_account_id,
            "env_id": b.environment_id,
            "active": b.active_flag,
            "marketplace": b.marketplace_id
        }
