from typing import Optional, List, Tuple, Dict
from datetime import datetime
from uuid import UUID, uuid4

from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, PolicyLevel, EventType
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.models.ops_policy_event import OpsPolicyEvent
from src.ops_policy.models.ops_policy_candidate import OpsPolicyCandidate
from src.ops_policy.services.incident_to_policy_candidate_service import IncidentToPolicyCandidateService

class OpsPolicyManagementService:
    """ポリシー管理（CRUD + lifecycle）"""

    def __init__(self):
        # Dummy in-memory stores for Wave 3, replaced by DB in Wave 6
        self.policies: Dict[UUID, OpsPolicy] = {}
        self.events: List[OpsPolicyEvent] = []

    def create_policy_from_candidate(self, candidate: OpsPolicyCandidate, created_by: str) -> OpsPolicy:
        """candidate → policy 作成（proposed status）。Returns: OpsPolicy"""
        candidate_svc = IncidentToPolicyCandidateService()
        level = candidate_svc.assess_policy_level(str(candidate.severity.name).lower(), candidate.recommended_action_type)
        review_due_at = candidate_svc.extract_review_due_date(str(candidate.severity.name).lower())
        
        policy = OpsPolicy(
            policy_id=uuid4(),
            scope_type=candidate.target_scope,
            target_id=candidate.target_id,
            action_type=candidate.recommended_action_type,
            level=level,
            status=PolicyStatus.PROPOSED,
            title=f"Policy from {candidate.candidate_type.name}",
            reason_summary=candidate.reason_summary,
            evidence_summary="Auto-generated evidence from candidate",
            linked_incident_id=candidate.linked_incident_id,
            effective_from=datetime.utcnow(),
            effective_until=None,
            review_due_at=review_due_at,
            created_by=created_by,
            approved_by=None,
            applied_at=None,
            released_at=None,
            is_expired=False,
            priority=int(candidate.confidence_score),
            metadata_json={"candidate_id": str(candidate.candidate_id)}
        )
        self.policies[policy.policy_id] = policy
        return policy

    def create_manual_policy(self, scope_type: ScopeType, target_id: Optional[str], action_type: ActionType, title: str, reason: str, created_by: str) -> OpsPolicy:
        """手動 policy 作成。Returns: OpsPolicy"""
        candidate_svc = IncidentToPolicyCandidateService()
        level = candidate_svc.assess_policy_level("medium", action_type) # Defaulting to medium severity logic for manual
        
        policy = OpsPolicy(
            policy_id=uuid4(),
            scope_type=scope_type,
            target_id=target_id,
            action_type=action_type,
            level=level,
            status=PolicyStatus.PROPOSED,
            title=title,
            reason_summary=reason,
            evidence_summary="Manually created",
            linked_incident_id=None,
            effective_from=datetime.utcnow(),
            effective_until=None,
            review_due_at=None,
            created_by=created_by,
            approved_by=None,
            applied_at=None,
            released_at=None,
            is_expired=False,
            priority=50,
            metadata_json={}
        )
        self.policies[policy.policy_id] = policy
        return policy

    def list_policies(self, scope_type: Optional[ScopeType] = None, status: Optional[PolicyStatus] = None, seller_account_id: Optional[str] = None, environment: Optional[str] = None, limit: int = 100, offset: int = 0) -> Tuple[List[OpsPolicy], int]:
        """ポリシー一覧（フィルタ対応）。Returns: ([policies], total_count)"""
        filtered = list(self.policies.values())
        
        if scope_type:
            filtered = [p for p in filtered if p.scope_type == scope_type]
        if status:
            filtered = [p for p in filtered if p.status == status]
        if seller_account_id:
            filtered = [p for p in filtered if p.scope_type == ScopeType.SELLER and p.target_id == seller_account_id]
        if environment:
            filtered = [p for p in filtered if p.scope_type == ScopeType.ENVIRONMENT and p.target_id == environment]
            
        total_count = len(filtered)
        # Sort to ensure consistent pagination (descending by created time effectively)
        filtered.sort(key=lambda x: x.effective_from, reverse=True)
        return filtered[offset:offset+limit], total_count

    def get_policy_by_id(self, policy_id: UUID) -> Optional[OpsPolicy]:
        """ポリシー取得。Returns: OpsPolicy or None"""
        return self.policies.get(policy_id)

    def get_active_policies(self, seller_account_id: Optional[str] = None, environment: Optional[str] = None) -> List[OpsPolicy]:
        """アクティブポリシー一覧。Returns: [OpsPolicy]"""
        # Get base active ones
        actives = [p for p in self.policies.values() if p.status == PolicyStatus.ACTIVE]
        
        filtered = []
        for p in actives:
            if p.scope_type == ScopeType.GLOBAL:
                filtered.append(p)
            elif seller_account_id and p.scope_type == ScopeType.SELLER and p.target_id == seller_account_id:
                filtered.append(p)
            elif environment and p.scope_type == ScopeType.ENVIRONMENT and p.target_id == environment:
                filtered.append(p)
            # EXECUTION_CHANNEL ignored for basic active match unless explicitly requested (mocked for now)
            
        return filtered

    def link_policy_to_incident(self, policy_id: UUID, incident_id: UUID) -> OpsPolicy:
        """policy を incident にリンク。Returns: 更新済み policy"""
        policy = self.get_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
            
        policy.linked_incident_id = incident_id
        
        # event creation
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy.policy_id,
            event_type=EventType.CREATED, # fallback, typically LINKED but use existing enum
            from_status=policy.status,
            to_status=policy.status,
            actor_type="system",
            actor_id="system",
            note=f"Linked to incident {incident_id}",
            details_json={"incident_id": str(incident_id)},
            created_at=datetime.utcnow()
        )
        self.events.append(event)
        
        return policy

    def add_policy_note(self, policy_id: UUID, note: str, actor_id: str) -> OpsPolicyEvent:
        """policy にノート追加（audit）。Returns: event"""
        policy = self.get_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
            
        event = OpsPolicyEvent(
            event_id=uuid4(),
            policy_id=policy_id,
            event_type=EventType.CREATED, # use CREATED as note event type fallback
            from_status=policy.status,
            to_status=policy.status,
            actor_type="user",
            actor_id=actor_id,
            note=note,
            details_json={},
            created_at=datetime.utcnow()
        )
        self.events.append(event)
        return event

    def list_policy_events(self, policy_id: UUID, limit: int = 50) -> List[OpsPolicyEvent]:
        """policy の event 一覧。Returns: [OpsPolicyEvent]"""
        filtered = [e for e in self.events if e.policy_id == policy_id]
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[:limit]

    def count_policies_by_status(self) -> Dict[PolicyStatus, int]:
        """ステータス別 count。Returns: {status: count}"""
        counts = {status: 0 for status in PolicyStatus}
        for p in self.policies.values():
            counts[p.status] += 1
        return counts
