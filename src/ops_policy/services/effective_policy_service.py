from typing import Optional, List
from src.ops_policy.models.enums import ScopeType
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.models.effective_policy_decision import EffectivePolicyDecision
from src.ops_policy.services.ops_policy_precedence_service import OpsPolicyPrecedenceService

class EffectivePolicyService:
    """有効ポリシー計算"""

    def __init__(self, precedence_service: OpsPolicyPrecedenceService):
        self.precedence_service = precedence_service
        # In a real implementation, we would have a repository to fetch active policies.
        # We will mock the fetching in our tests.
        self.active_policies: List[OpsPolicy] = []

    def compute_effective_policy(
        self,
        seller_account_id: str,
        environment: str
    ) -> EffectivePolicyDecision:
        """
        seller+environment の有効ポリシー計算
        Returns: EffectivePolicyDecision
        """
        # Get active policies that match
        global_policy = None
        env_policy = None
        seller_policy = None

        for p in self.active_policies:
            if p.scope_type == ScopeType.GLOBAL:
                if not global_policy or p.priority > global_policy.priority:
                    global_policy = p
            elif p.scope_type == ScopeType.ENVIRONMENT and p.target_id == environment:
                if not env_policy or p.priority > env_policy.priority:
                    env_policy = p
            elif p.scope_type == ScopeType.SELLER and p.target_id == seller_account_id:
                if not seller_policy or p.priority > seller_policy.priority:
                    seller_policy = p

        decision = self.precedence_service.merge_policies(
            global_policy=global_policy,
            env_policy=env_policy,
            seller_policy=seller_policy
        )
        return decision

    def compute_effective_policy_for_attempt(
        self,
        attempt
    ) -> EffectivePolicyDecision:
        """
        attempt から seller/environment 抽出→計算
        Returns: EffectivePolicyDecision
        """
        # Assume attempt has seller_account_id and environment
        seller_id = getattr(attempt, 'seller_account_id', 'unknown')
        env = getattr(attempt, 'environment', 'unknown')
        return self.compute_effective_policy(seller_id, env)

    def is_live_execution_allowed(
        self,
        seller_account_id: str,
        environment: str
    ) -> bool:
        """
        ライブ実行許可判定
        Returns: True 許可 / False 禁止
        """
        decision = self.compute_effective_policy(seller_account_id, environment)
        return decision.live_execution_allowed

    def get_required_review_level(
        self,
        seller_account_id: str,
        environment: str
    ) -> str:
        """
        レビューレベル取得
        Returns: "NONE" / "STANDARD" / "ESCALATED"
        """
        decision = self.compute_effective_policy(seller_account_id, environment)
        if decision.require_manual_review:
            # Maybe check operator attention or safe mode for escalated?
            if decision.operator_attention or decision.environment_safe_mode:
                return "ESCALATED"
            return "STANDARD"
        return "NONE"
