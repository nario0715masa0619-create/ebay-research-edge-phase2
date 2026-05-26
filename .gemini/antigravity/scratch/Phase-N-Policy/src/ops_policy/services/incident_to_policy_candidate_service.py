from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

from src.ops_policy.models.enums import CandidateType, ActionType, PolicyLevel, ScopeType, Severity
from src.ops_policy.models.ops_policy_candidate import OpsPolicyCandidate

class IncidentToPolicyCandidateService:
    """incident → policy candidate 変換"""

    def generate_candidate_from_incident(self, incident) -> Optional[OpsPolicyCandidate]:
        """incident → OpsPolicyCandidate 変換。high/critical only。Returns: OpsPolicyCandidate or None"""
        if getattr(incident, "severity", None) in ["critical", "high"]: # string comparison for incident module depending on how it's defined
            # actually incident.severity is likely an Enum. Let's handle both
            sev_val = incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity).lower()
            if sev_val not in ["critical", "high"]:
                return None
        else:
            if str(incident.severity).lower() not in ["critical", "high"]:
                return None
                
        # we found high/critical
        sev_enum = Severity.CRITICAL if str(incident.severity).lower() == "critical" else Severity.HIGH
        action_type = self.map_incident_severity_to_policy_action(
            str(incident.incident_type), sev_enum.value, incident.seller_account_id, incident.environment
        )
        scope_type, target_id = self.map_incident_to_scope(incident.seller_account_id, incident.environment)
        
        return OpsPolicyCandidate(
            candidate_id=uuid4(),
            candidate_type=CandidateType.HIGH_SEVERITY_INCIDENT,
            recommended_action_type=action_type,
            severity=sev_enum,
            target_scope=scope_type,
            target_id=target_id,
            linked_incident_id=incident.incident_id,
            confidence_score=90.0,
            reason_summary=f"Auto-generated from {sev_enum.value} incident",
            created_at=datetime.utcnow()
        )

    def generate_candidates_from_incidents(self, incidents: List) -> List[OpsPolicyCandidate]:
        """複数 incident → candidates リスト。Returns: [OpsPolicyCandidate]"""
        candidates = []
        for inc in incidents:
            cand = self.generate_candidate_from_incident(inc)
            if cand:
                candidates.append(cand)
        return candidates

    def map_incident_severity_to_policy_action(self, incident_type: str, incident_severity: str, seller_account_id: str, environment: str) -> ActionType:
        """incident 属性 → ActionType マップ。Returns: ActionType"""
        inc_type_lower = incident_type.lower()
        sev_lower = incident_severity.lower()
        if sev_lower == "critical":
            if "system" in inc_type_lower or "environment" in inc_type_lower:
                return ActionType.ENVIRONMENT_SAFE_MODE
            return ActionType.BLOCK_LIVE_EXECUTION
        if sev_lower == "high":
            if "auth" in inc_type_lower or "credential" in inc_type_lower:
                return ActionType.BLOCK_LIVE_EXECUTION
            if "retry" in inc_type_lower:
                return ActionType.SUPPRESS_RETRY
            return ActionType.PAUSE_HANDOFF
        return ActionType.REQUIRE_MANUAL_REVIEW

    def map_incident_to_scope(self, seller_account_id: str, environment: str) -> Tuple[ScopeType, Optional[str]]:
        """seller/env → (scope_type, target_id)。Returns: (ScopeType, Optional[str])"""
        if seller_account_id:
            return ScopeType.SELLER, seller_account_id
        if environment:
            return ScopeType.ENVIRONMENT, environment
        return ScopeType.GLOBAL, None

    def assess_policy_level(self, incident_severity: str, action_type: ActionType) -> PolicyLevel:
        """severity + action → policy level 判定。critical action → strong。Returns: PolicyLevel"""
        sev_lower = incident_severity.lower()
        if sev_lower == "critical":
            return PolicyLevel.STRONG
        
        strong_actions = {
            ActionType.BLOCK_LIVE_EXECUTION,
            ActionType.ENVIRONMENT_SAFE_MODE,
            ActionType.BLOCK_LISTING_CREATION
        }
        if action_type in strong_actions:
            return PolicyLevel.STRONG
        return PolicyLevel.OVERLAY

    def extract_review_due_date(self, incident_severity: str) -> Optional[datetime]:
        """severity → review_due_at 計算。critical → 1h / high → 4h / others → None。Returns: Optional[datetime]"""
        sev_lower = incident_severity.lower()
        if sev_lower == "critical":
            return datetime.utcnow() + timedelta(hours=1)
        elif sev_lower == "high":
            return datetime.utcnow() + timedelta(hours=4)
        return None
