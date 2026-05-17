import logging
from typing import Optional
from src.seller_env.models import SellerContext, SellerProfile, EnvironmentProfile, SellerEnvironmentBinding

logger = logging.getLogger(__name__)

class SellerConfigResolver:
    def __init__(self, seller_repo, env_repo, binding_repo):
        self.seller_repo = seller_repo
        self.env_repo = env_repo
        self.binding_repo = binding_repo

    def resolve_context(self, seller_account_id: str = None, environment_type: str = None) -> SellerContext:
        """
        Resolves the full context for a given seller and environment.
        If not specified, uses the system default active binding.
        """
        if not seller_account_id:
            # Try to find an active binding globally (first one for v0.1)
            bindings = self.binding_repo.list_all_active() # Need this method
            if not bindings:
                raise ValueError("No active seller binding found and no seller specified.")
            binding = bindings[0]
            seller_account_id = binding.seller_account_id
        else:
            if environment_type:
                # Find specific binding for this env type
                binding = self._find_binding_by_type(seller_account_id, environment_type)
            else:
                binding = self.binding_repo.get_active_for_seller(seller_account_id)
        
        if not binding:
            raise ValueError(f"No valid binding found for seller {seller_account_id}")

        seller = self.seller_repo.get_by_id(seller_account_id)
        env = self.env_repo.get_by_id(binding.environment_id)
        
        if not seller or not env:
            raise ValueError(f"Seller or Environment profile missing for binding {binding.binding_id}")

        if not seller.enabled:
            raise ValueError(f"Seller {seller_account_id} is disabled.")

        return SellerContext(
            seller_account_id=seller.seller_account_id,
            seller_label=seller.seller_label,
            environment_type=env.environment_type,
            marketplace_id=binding.marketplace_id,
            currency=binding.currency,
            merchant_location_key=binding.merchant_location_key,
            fulfillment_policy_id=binding.fulfillment_policy_id,
            payment_policy_id=binding.payment_policy_id,
            return_policy_id=binding.return_policy_id,
            auth_profile_ref=seller.auth_profile_ref,
            notification_profile_ref=seller.notification_profile_ref,
            dry_run_default=False,
            publish_enabled=env.supports_live_publish,
            monitoring_enabled=True,
            sync_enabled=True
        )

    def _find_binding_by_type(self, seller_account_id: str, env_type: str) -> Optional[SellerEnvironmentBinding]:
        bindings = self.binding_repo.list_by_seller(seller_account_id)
        for b in bindings:
            env = self.env_repo.get_by_id(b.environment_id)
            if env and env.environment_type == env_type:
                return b
        return None
