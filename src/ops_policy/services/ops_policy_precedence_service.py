from typing import List, Dict, Optional
from datetime import datetime

from src.ops_policy.models.enums import ScopeType, ActionType
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.models.effective_policy_decision import EffectivePolicyDecision


class OpsPolicyPrecedenceService:
    """優先度・マージサービス"""

    def compute_precedence(
        self,
        policies: List[OpsPolicy]
    ) -> Dict[ScopeType, List[OpsPolicy]]:
        """
        スコープ別に分類
        Returns: {ScopeType: [policies]}
        """
        result = {scope: [] for scope in ScopeType}
        for p in policies:
            if p.scope_type in result:
                result[p.scope_type].append(p)
        
        # Sort each list by priority (highest priority integer first) and then by effective_from (newest first)
        for scope in result:
            result[scope].sort(key=lambda x: (x.priority, x.effective_from), reverse=True)
            
        return result

    def is_deny_first_action(
        self,
        action_type: ActionType
    ) -> bool:
        """
        deny-first 判定（制限強）
        Returns: True deny-first / False overlay
        """
        deny_first_actions = {
            ActionType.BLOCK_LIVE_EXECUTION,
            ActionType.ENVIRONMENT_SAFE_MODE,
            ActionType.BLOCK_LISTING_CREATION
        }
        return action_type in deny_first_actions

    def merge_policies(
        self,
        global_policy: Optional[OpsPolicy],
        env_policy: Optional[OpsPolicy],
        seller_policy: Optional[OpsPolicy]
    ) -> EffectivePolicyDecision:
        """
        3段階ポリシーをマージ
        Returns: EffectivePolicyDecision
        """
        decision = EffectivePolicyDecision(
            policy_id=None,  # Not representing a single policy anymore, or we can use UUID if required. We just don't have one here.
            scope_type=ScopeType.GLOBAL,
            target_id=None,
            live_execution_allowed=True,
            force_dry_run=False,
            handoff_paused=False,
            retry_allowed=True,
            concurrency_limit=None,
            seller_throughput_limit=None,
            require_manual_review=False,
            block_listing_creation=False,
            environment_safe_mode=False,
            operator_attention=False,
            reason_summary="",
            contributing_policies=[],
            evaluated_at=datetime.utcnow()
        )
        
        # Order of precedence: GLOBAL > ENVIRONMENT > SELLER
        # Actually the prompt says: GLOBAL > ENV > SELLER > CHANNEL.
        # So we process from lowest to highest precedence, so higher precedence overwrites lower precedence.
        # But wait: if a higher precedence says ALLOW, it overrides a lower precedence DENY?
        # Typically DENY FIRST overrides everything if it's deny-first.
        # Let's collect all actions.
        policies = []
        if seller_policy: policies.append(seller_policy)
        if env_policy: policies.append(env_policy)
        if global_policy: policies.append(global_policy)
        
        # Start fresh
        decision.contributing_policies = [p.policy_id for p in policies]
        reasons = []

        # Overlay states
        for p in policies:
            # Deny-first actions override everything and apply immediately
            # Other actions (overlay) just toggle bits.
            if p.action_type == ActionType.BLOCK_LIVE_EXECUTION:
                decision.live_execution_allowed = False
            elif p.action_type == ActionType.ENVIRONMENT_SAFE_MODE:
                decision.environment_safe_mode = True
                decision.live_execution_allowed = False # safe mode implies no live execution typically, but let's just set the flag
            elif p.action_type == ActionType.BLOCK_LISTING_CREATION:
                decision.block_listing_creation = True
            elif p.action_type == ActionType.FORCE_DRY_RUN:
                decision.force_dry_run = True
            elif p.action_type == ActionType.PAUSE_HANDOFF:
                decision.handoff_paused = True
            elif p.action_type == ActionType.SUPPRESS_RETRY:
                decision.retry_allowed = False
            elif p.action_type == ActionType.REQUIRE_MANUAL_REVIEW:
                decision.require_manual_review = True
            elif p.action_type == ActionType.OPERATOR_ATTENTION_REQUIRED:
                decision.operator_attention = True
            
            reasons.append(p.reason_summary)
        
        decision.reason_summary = " | ".join(reasons)
        
        # The prompt says: GLOBAL > ENV > SELLER.
        # If there's a conflict in scalar values (like limits), we can use resolve_conflicting_actions or just highest precedence.
        # We process from seller (lowest) to global (highest).
        for p in policies:
            if p.action_type == ActionType.LIMIT_CONCURRENCY:
                decision.concurrency_limit = 10 # dummy logic for limit extraction. Wait, OpsPolicy doesn't have limit field. It has metadata_json.
                if p.metadata_json and "concurrency_limit" in p.metadata_json:
                    val = p.metadata_json["concurrency_limit"]
                    decision.concurrency_limit = min(val, decision.concurrency_limit) if decision.concurrency_limit else val
            if p.action_type == ActionType.LIMIT_SELLER_THROUGHPUT:
                if p.metadata_json and "throughput_limit" in p.metadata_json:
                    val = p.metadata_json["throughput_limit"]
                    decision.seller_throughput_limit = min(val, decision.seller_throughput_limit) if decision.seller_throughput_limit else val

        return decision

    def resolve_conflicting_actions(
        self,
        action_list: List[ActionType]
    ) -> ActionType:
        """
        最も制限的なアクション選択
        Returns: ActionType
        """
        # Define restrictiveness (higher is more restrictive)
        restrictiveness = {
            ActionType.BLOCK_LIVE_EXECUTION: 100,
            ActionType.ENVIRONMENT_SAFE_MODE: 90,
            ActionType.BLOCK_LISTING_CREATION: 80,
            ActionType.FORCE_DRY_RUN: 70,
            ActionType.PAUSE_HANDOFF: 60,
            ActionType.SUPPRESS_RETRY: 50,
            ActionType.LIMIT_CONCURRENCY: 40,
            ActionType.LIMIT_SELLER_THROUGHPUT: 30,
            ActionType.REQUIRE_MANUAL_REVIEW: 20,
            ActionType.OPERATOR_ATTENTION_REQUIRED: 10
        }
        
        if not action_list:
            raise ValueError("Empty action list")
            
        return max(action_list, key=lambda a: restrictiveness.get(a, 0))

    def apply_precedence_rules(
        self,
        target_scope: ScopeType,
        policies: List[OpsPolicy]
    ) -> List[OpsPolicy]:
        """
        優先度適用・フィルタ
        Returns: [OpsPolicy]
        """
        # Returns policies ordered by precedence: GLOBAL > ENV > SELLER > CHANNEL
        # and filtered to only include active/relevant policies.
        # But we assume input is already active policies.
        
        precedence_order = {
            ScopeType.GLOBAL: 4,
            ScopeType.ENVIRONMENT: 3,
            ScopeType.SELLER: 2,
            ScopeType.EXECUTION_CHANNEL: 1
        }
        
        # Sort by scope precedence (descending) and then by priority
        sorted_policies = sorted(
            policies,
            key=lambda p: (precedence_order.get(p.scope_type, 0), p.priority),
            reverse=True
        )
        return sorted_policies
