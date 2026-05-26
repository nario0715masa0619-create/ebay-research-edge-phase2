from typing import Tuple
from uuid import UUID, uuid4
from datetime import datetime

from src.ops_policy.models.enums import EventType, PolicyStatus, PolicyLevel
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.models.ops_policy_event import OpsPolicyEvent


class InvalidStateTransitionError(Exception):
    """状態遷移エラー"""
    pass


class OpsPolicyStateMachine:
    """ポリシー状態機械"""

    def propose_policy(
        self,
        policy: OpsPolicy
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        ポリシー作成（proposed 状態）
        Returns: (更新済みポリシー, イベント)
        """
        if policy.status != PolicyStatus.PROPOSED:
            raise InvalidStateTransitionError(f"Cannot propose a policy not in PROPOSED state.")
            
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.PROPOSED,
            from_status=None,
            to_status=PolicyStatus.PROPOSED,
            actor_type="user",
            actor_id=policy.created_by,
            note="Policy proposed",
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def approve_policy(
        self,
        policy: OpsPolicy,
        approved_by: str
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        提案→承認（strong は review_due_at 必須）
        Raises: InvalidStateTransitionError
        Returns: (更新済みポリシー, イベント)
        """
        if not self.validate_transition(policy.status, PolicyStatus.APPROVED):
            raise InvalidStateTransitionError(f"Cannot transition from {policy.status} to {PolicyStatus.APPROVED}")
            
        if policy.level == PolicyLevel.STRONG:
            if not approved_by:
                raise ValueError("STRONG policy requires approved_by")
            if not policy.review_due_at:
                raise ValueError("STRONG policy requires review_due_at")

        from_status = policy.status
        policy.status = PolicyStatus.APPROVED
        policy.approved_by = approved_by
        
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.APPROVED,
            from_status=from_status,
            to_status=PolicyStatus.APPROVED,
            actor_type="user",
            actor_id=approved_by,
            note="Policy approved",
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def activate_policy(
        self,
        policy: OpsPolicy
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        承認→有効化（applied_at セット）
        Raises: InvalidStateTransitionError
        Returns: (更新済みポリシー, イベント)
        """
        if not self.validate_transition(policy.status, PolicyStatus.ACTIVE):
            raise InvalidStateTransitionError(f"Cannot transition from {policy.status} to {PolicyStatus.ACTIVE}")

        from_status = policy.status
        policy.status = PolicyStatus.ACTIVE
        policy.applied_at = datetime.utcnow()
        
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.APPLIED,
            from_status=from_status,
            to_status=PolicyStatus.ACTIVE,
            actor_type="system",
            actor_id="system",
            note="Policy activated",
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def reject_policy(
        self,
        policy: OpsPolicy,
        reason: str,
        actor_id: str
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        提案→却下
        Raises: InvalidStateTransitionError
        Returns: (更新済みポリシー, イベント)
        """
        if not self.validate_transition(policy.status, PolicyStatus.REJECTED):
            raise InvalidStateTransitionError(f"Cannot transition from {policy.status} to {PolicyStatus.REJECTED}")

        from_status = policy.status
        policy.status = PolicyStatus.REJECTED
        
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.REJECTED,
            from_status=from_status,
            to_status=PolicyStatus.REJECTED,
            actor_type="user",
            actor_id=actor_id,
            note=reason,
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def release_policy(
        self,
        policy: OpsPolicy,
        actor_id: str
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        有効→解放（released_at セット）
        Raises: InvalidStateTransitionError
        Returns: (更新済みポリシー, イベント)
        """
        if not self.validate_transition(policy.status, PolicyStatus.RELEASED):
            raise InvalidStateTransitionError(f"Cannot transition from {policy.status} to {PolicyStatus.RELEASED}")

        from_status = policy.status
        policy.status = PolicyStatus.RELEASED
        policy.released_at = datetime.utcnow()
        
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.RELEASED,
            from_status=from_status,
            to_status=PolicyStatus.RELEASED,
            actor_type="user",
            actor_id=actor_id,
            note="Policy released",
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def expire_policy(
        self,
        policy: OpsPolicy
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        有効→期限切れ（is_expired=True）
        Raises: InvalidStateTransitionError
        Returns: (更新済みポリシー, イベント)
        """
        if not self.validate_transition(policy.status, PolicyStatus.EXPIRED):
            raise InvalidStateTransitionError(f"Cannot transition from {policy.status} to {PolicyStatus.EXPIRED}")

        from_status = policy.status
        policy.status = PolicyStatus.EXPIRED
        policy.is_expired = True
        
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.EXPIRED,
            from_status=from_status,
            to_status=PolicyStatus.EXPIRED,
            actor_type="system",
            actor_id="system",
            note="Policy expired automatically",
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def cancel_policy(
        self,
        policy: OpsPolicy,
        reason: str,
        actor_id: str
    ) -> Tuple[OpsPolicy, OpsPolicyEvent]:
        """
        提案/承認/有効→キャンセル
        Raises: InvalidStateTransitionError
        Returns: (更新済みポリシー, イベント)
        """
        if not self.validate_transition(policy.status, PolicyStatus.CANCELLED):
            raise InvalidStateTransitionError(f"Cannot transition from {policy.status} to {PolicyStatus.CANCELLED}")

        from_status = policy.status
        policy.status = PolicyStatus.CANCELLED
        
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.CANCELLED,
            from_status=from_status,
            to_status=PolicyStatus.CANCELLED,
            actor_type="user",
            actor_id=actor_id,
            note=reason,
            details_json={},
            created_at=datetime.utcnow()
        )
        return policy, event

    def validate_transition(
        self,
        from_status: PolicyStatus,
        to_status: PolicyStatus
    ) -> bool:
        """
        遷移妥当性チェック
        Returns: True 許可 / False 拒否
        """
        valid_transitions = {
            PolicyStatus.PROPOSED: [PolicyStatus.APPROVED, PolicyStatus.REJECTED, PolicyStatus.CANCELLED],
            PolicyStatus.APPROVED: [PolicyStatus.ACTIVE, PolicyStatus.CANCELLED],
            PolicyStatus.ACTIVE: [PolicyStatus.RELEASED, PolicyStatus.EXPIRED, PolicyStatus.CANCELLED],
            PolicyStatus.RELEASED: [],
            PolicyStatus.EXPIRED: [],
            PolicyStatus.CANCELLED: [],
            PolicyStatus.REJECTED: [],
        }
        return to_status in valid_transitions.get(from_status, [])
