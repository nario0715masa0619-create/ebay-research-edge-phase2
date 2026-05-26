from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta

from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService

class OpsPolicyDigestService:
    """ポリシー digest / レポート生成"""

    def __init__(self, management_service: OpsPolicyManagementService):
        self.mgmt = management_service

    def _format_policy(self, p: OpsPolicy) -> str:
        return f"- **{p.title}** ({p.policy_id})\n  - Scope: {p.scope_type.value} ({p.target_id or 'all'})\n  - Action: {p.action_type.value}\n  - Reason: {p.reason_summary}"

    def generate_active_policy_digest(self) -> str:
        """アクティブ policy 一覧 digest（markdown）。Returns: str"""
        actives = [p for p in self.mgmt.policies.values() if p.status == PolicyStatus.ACTIVE]
        
        digest = [f"# Active Operations Policies Digest"]
        digest.append(f"Generated at: {datetime.utcnow().isoformat()}Z\n")
        
        if not actives:
            digest.append("No active policies found.")
            return "\n".join(digest)
            
        digest.append("## By Action Type")
        for action in ActionType:
            action_policies = [p for p in actives if p.action_type == action]
            if action_policies:
                digest.append(f"\n### {action.value}")
                for p in action_policies:
                    digest.append(self._format_policy(p))
                    
        return "\n".join(digest)

    def generate_policy_action_digest(self, action_type: ActionType) -> str:
        """特定 action の policy digest。Returns: str"""
        policies = [p for p in self.mgmt.policies.values() if p.action_type == action_type]
        digest = [f"# Policy Digest: {action_type.value}"]
        digest.append(f"Generated at: {datetime.utcnow().isoformat()}Z\n")
        
        if not policies:
            digest.append("No policies found for this action type.")
            return "\n".join(digest)
            
        for p in policies:
            digest.append(self._format_policy(p))
            
        return "\n".join(digest)

    def generate_seller_policy_digest(self, seller_account_id: str) -> str:
        """seller の policy digest。Returns: str"""
        policies = [p for p in self.mgmt.policies.values() if p.scope_type == ScopeType.SELLER and p.target_id == seller_account_id]
        digest = [f"# Seller Policy Digest: {seller_account_id}"]
        digest.append(f"Generated at: {datetime.utcnow().isoformat()}Z\n")
        
        if not policies:
            digest.append("No policies found for this seller.")
            return "\n".join(digest)
            
        for p in policies:
            digest.append(self._format_policy(p))
            
        return "\n".join(digest)

    def generate_environment_policy_digest(self, environment: str) -> str:
        """environment の policy digest。Returns: str"""
        policies = [p for p in self.mgmt.policies.values() if p.scope_type == ScopeType.ENVIRONMENT and p.target_id == environment]
        digest = [f"# Environment Policy Digest: {environment}"]
        digest.append(f"Generated at: {datetime.utcnow().isoformat()}Z\n")
        
        if not policies:
            digest.append("No policies found for this environment.")
            return "\n".join(digest)
            
        for p in policies:
            digest.append(self._format_policy(p))
            
        return "\n".join(digest)

    def generate_daily_policy_summary_digest(self, date: datetime) -> str:
        """日次 policy summary digest。Returns: str"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        created = 0
        released = 0
        
        for p in self.mgmt.policies.values():
            if p.effective_from and start_of_day <= p.effective_from < end_of_day:
                created += 1
            if p.released_at and start_of_day <= p.released_at < end_of_day:
                released += 1
                
        digest = [f"# Daily Policy Summary: {start_of_day.strftime('%Y-%m-%d')}"]
        digest.append(f"Generated at: {datetime.utcnow().isoformat()}Z\n")
        digest.append(f"- **New Policies Created**: {created}")
        digest.append(f"- **Policies Released**: {released}")
        
        return "\n".join(digest)
