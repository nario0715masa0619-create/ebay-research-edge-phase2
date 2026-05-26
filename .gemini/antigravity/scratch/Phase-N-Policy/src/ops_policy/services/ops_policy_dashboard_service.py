from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta

from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService

class OpsPolicyDashboardService:
    """ポリシー dashboard & 統計"""

    def __init__(self, management_service: OpsPolicyManagementService):
        self.mgmt = management_service

    def get_policy_summary(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """policy 集計サマリー。Returns: {total, active, proposed, by_scope, by_action, etc}"""
        policies = list(self.mgmt.policies.values())
        if date_range:
            start, end = date_range
            policies = [p for p in policies if p.effective_from and start <= p.effective_from <= end]
            
        summary = {
            "total_count": len(policies),
            "active_count": sum(1 for p in policies if p.status == PolicyStatus.ACTIVE),
            "proposed_count": sum(1 for p in policies if p.status == PolicyStatus.PROPOSED),
            "released_count": sum(1 for p in policies if p.status == PolicyStatus.RELEASED),
            "expired_count": sum(1 for p in policies if p.status == PolicyStatus.EXPIRED),
            "cancelled_count": sum(1 for p in policies if p.status == PolicyStatus.CANCELLED),
            "by_scope_type": {},
            "by_action_type": {},
            "created_last_24h": sum(1 for p in policies if p.effective_from and (datetime.utcnow() - p.effective_from) <= timedelta(hours=24))
        }
        
        for p in policies:
            summary["by_scope_type"][p.scope_type] = summary["by_scope_type"].get(p.scope_type, 0) + 1
            summary["by_action_type"][p.action_type] = summary["by_action_type"].get(p.action_type, 0) + 1
            
        return summary

    def get_active_policy_count(self) -> int:
        """active policy 数。Returns: int"""
        return sum(1 for p in self.mgmt.policies.values() if p.status == PolicyStatus.ACTIVE)

    def get_policies_by_action_type(self) -> Dict[ActionType, int]:
        """action_type 別 count。Returns: {action_type: count}"""
        counts = {action: 0 for action in ActionType}
        for p in self.mgmt.policies.values():
            counts[p.action_type] += 1
        return counts

    def get_policies_by_scope(self) -> Dict[ScopeType, int]:
        """scope 別 count。Returns: {scope_type: count}"""
        counts = {scope: 0 for scope in ScopeType}
        for p in self.mgmt.policies.values():
            counts[p.scope_type] += 1
        return counts

    def get_seller_policies(self, seller_account_id: str) -> List[OpsPolicy]:
        """seller の全 policy。Returns: [OpsPolicy]"""
        return [p for p in self.mgmt.policies.values() if p.scope_type == ScopeType.SELLER and p.target_id == seller_account_id]

    def get_environment_policies(self, environment: str) -> List[OpsPolicy]:
        """environment の全 policy。Returns: [OpsPolicy]"""
        return [p for p in self.mgmt.policies.values() if p.scope_type == ScopeType.ENVIRONMENT and p.target_id == environment]

    def get_policy_application_rate(self) -> float:
        """policy 適用率（active / total）。Returns: float 0.0-1.0"""
        total = len(self.mgmt.policies)
        if total == 0:
            return 0.0
        active = self.get_active_policy_count()
        return float(active) / total

    def get_top_affected_sellers(self, limit: int = 10) -> List[Tuple[str, int]]:
        """最も多くの policy が適用されている seller。Returns: [(seller_id, policy_count)]"""
        counts = {}
        for p in self.mgmt.policies.values():
            if p.scope_type == ScopeType.SELLER and p.target_id:
                counts[p.target_id] = counts.get(p.target_id, 0) + 1
        
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:limit]
