from src.db.session import SessionManager
from src.repositories.persistent_seller_profile_repository import PersistentSellerProfileRepository
from src.repositories.persistent_environment_profile_repository import PersistentEnvironmentProfileRepository
from src.repositories.persistent_seller_environment_binding_repository import PersistentSellerEnvironmentBindingRepository
from src.repositories.persistent_seller_policy_snapshot_repository import PersistentSellerPolicySnapshotRepository
from src.repositories.persistent_seller_location_snapshot_repository import PersistentSellerLocationSnapshotRepository
from src.seller_env.config_resolver import SellerConfigResolver
from src.seller_env.environment_guard import EnvironmentGuard
from src.seller_env.context_manager import SellerContextManager

class SellerEnvironmentBootstrap:
    @staticmethod
    def bootstrap(session=None):
        if not session:
            session = SessionManager().get_session()
            
        seller_repo = PersistentSellerProfileRepository(session)
        env_repo = PersistentEnvironmentProfileRepository(session)
        binding_repo = PersistentSellerEnvironmentBindingRepository(session)
        policy_repo = PersistentSellerPolicySnapshotRepository(session)
        location_repo = PersistentSellerLocationSnapshotRepository(session)
        
        resolver = SellerConfigResolver(seller_repo, env_repo, binding_repo)
        guard = EnvironmentGuard()
        context_manager = SellerContextManager()
        
        return {
            "seller_repo": seller_repo,
            "env_repo": env_repo,
            "binding_repo": binding_repo,
            "policy_repo": policy_repo,
            "location_repo": location_repo,
            "resolver": resolver,
            "guard": guard,
            "context_manager": context_manager
        }
