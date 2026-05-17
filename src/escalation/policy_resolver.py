from typing import Optional
from src.escalation.models import EscalationPolicy
from src.escalation.policies import get_system_default_policy, DEFAULT_POLICIES
from src.repositories.persistent_escalation_state_repository import PersistentEscalationPolicyRepository

class SellerEnvPolicyResolver:
    def __init__(self, policy_repo: PersistentEscalationPolicyRepository):
        self.policy_repo = policy_repo

    def resolve(
        self,
        seller_account_id: Optional[str],
        environment_type: Optional[str],
        event_type: str,
        severity: str = "warning"
    ) -> EscalationPolicy:
        # 1. Query the repository for the best active policy matching context
        policy = self.policy_repo.resolve_best_policy(
            seller_account_id=seller_account_id,
            environment_type=environment_type,
            event_type=event_type,
            severity=severity
        )
        if policy:
            return policy

        # 2. Match from pre-populated system defaults memory list
        for p in DEFAULT_POLICIES:
            if p.event_type == event_type and p.enabled:
                # Approximate context check
                if p.seller_account_id == seller_account_id or not p.seller_account_id:
                    if p.environment_type == environment_type or not p.environment_type:
                        return p

        # 3. Fallback to system default policy generator
        return get_system_default_policy(event_type, severity)
