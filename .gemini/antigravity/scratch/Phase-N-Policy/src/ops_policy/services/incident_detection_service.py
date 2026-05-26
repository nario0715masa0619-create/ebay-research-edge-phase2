from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from src.ops_policy.models.enums import CandidateType, ActionType, Severity, ScopeType
from src.ops_policy.models.ops_policy_candidate import OpsPolicyCandidate

class IncidentDetectionService:
    """異常検知 → candidate 生成"""

    def _get_auth_failures(self, seller_account_id, environment, time_window_minutes): return 0
    def _get_env_failure_rate(self, environment, time_window_minutes): return 0.0
    def _get_cumulative_retry(self, seller_account_id, listing_id, time_window_minutes): return 0
    def _get_daily_failure_rate(self, seller_account_id, time_window_hours): return 0.0
    def _get_guard_rejections(self, seller_account_id, environment, time_window_minutes): return 0

    def detect_credential_failure_spike(self, seller_account_id: str, environment: str, time_window_minutes: int = 60) -> Optional[OpsPolicyCandidate]:
        """credential failure ≥3 in time_window。Returns: OpsPolicyCandidate or None"""
        fails = self._get_auth_failures(seller_account_id, environment, time_window_minutes)
        if fails >= 3:
            return OpsPolicyCandidate(
                candidate_id=uuid4(),
                candidate_type=CandidateType.CREDENTIAL_FAILURE_SPIKE,
                recommended_action_type=ActionType.BLOCK_LIVE_EXECUTION,
                severity=Severity.CRITICAL,
                target_scope=ScopeType.SELLER,
                target_id=seller_account_id,
                linked_incident_id=None,
                confidence_score=95.0,
                reason_summary=f"Detected {fails} auth failures in {time_window_minutes}m",
                created_at=datetime.utcnow()
            )
        return None

    def detect_high_severity_incident(self, incident) -> Optional[OpsPolicyCandidate]:
        """incident severity ≥ HIGH。Returns: OpsPolicyCandidate or None"""
        sev = str(getattr(incident, 'severity', '')).lower()
        if 'critical' in sev or 'high' in sev:
            from src.ops_policy.services.incident_to_policy_candidate_service import IncidentToPolicyCandidateService
            svc = IncidentToPolicyCandidateService()
            return svc.generate_candidate_from_incident(incident)
        return None

    def detect_environment_anomaly(self, environment: str, time_window_minutes: int = 60) -> Optional[OpsPolicyCandidate]:
        """environment failure_rate > 30% in window。Returns: OpsPolicyCandidate or None"""
        rate = self._get_env_failure_rate(environment, time_window_minutes)
        if rate > 0.3:
            return OpsPolicyCandidate(
                candidate_id=uuid4(),
                candidate_type=CandidateType.ENVIRONMENT_ANOMALY,
                recommended_action_type=ActionType.ENVIRONMENT_SAFE_MODE,
                severity=Severity.HIGH,
                target_scope=ScopeType.ENVIRONMENT,
                target_id=environment,
                linked_incident_id=None,
                confidence_score=85.0,
                reason_summary=f"Environment failure rate {rate*100}% > 30%",
                created_at=datetime.utcnow()
            )
        return None

    def detect_retry_loop_risk(self, seller_account_id: str, listing_id: str, time_window_minutes: int = 120) -> Optional[OpsPolicyCandidate]:
        """cumulative retry time > 1h same pattern。Returns: OpsPolicyCandidate or None"""
        retries = self._get_cumulative_retry(seller_account_id, listing_id, time_window_minutes)
        if retries >= 60:
            return OpsPolicyCandidate(
                candidate_id=uuid4(),
                candidate_type=CandidateType.RETRY_LOOP_RISK,
                recommended_action_type=ActionType.SUPPRESS_RETRY,
                severity=Severity.HIGH,
                target_scope=ScopeType.SELLER,
                target_id=seller_account_id,
                linked_incident_id=None,
                confidence_score=80.0,
                reason_summary=f"Cumulative retry {retries}m >= 60m",
                created_at=datetime.utcnow()
            )
        return None

    def detect_seller_health_degradation(self, seller_account_id: str, time_window_hours: int = 24) -> Optional[OpsPolicyCandidate]:
        """daily failure_rate > 30%。Returns: OpsPolicyCandidate or None"""
        rate = self._get_daily_failure_rate(seller_account_id, time_window_hours)
        if rate > 0.3:
            return OpsPolicyCandidate(
                candidate_id=uuid4(),
                candidate_type=CandidateType.SELLER_HEALTH_DEGRADATION,
                recommended_action_type=ActionType.PAUSE_HANDOFF,
                severity=Severity.HIGH,
                target_scope=ScopeType.SELLER,
                target_id=seller_account_id,
                linked_incident_id=None,
                confidence_score=75.0,
                reason_summary=f"Daily failure rate {rate*100}% > 30%",
                created_at=datetime.utcnow()
            )
        return None

    def detect_guard_rejection_spike(self, seller_account_id: str, environment: str, time_window_minutes: int = 60) -> Optional[OpsPolicyCandidate]:
        """guard_rejected count ≥ 3 in window。Returns: OpsPolicyCandidate or None"""
        rejections = self._get_guard_rejections(seller_account_id, environment, time_window_minutes)
        if rejections >= 3:
            return OpsPolicyCandidate(
                candidate_id=uuid4(),
                candidate_type=CandidateType.MANUAL_ALERT, # Use closest CandidateType available in enum
                recommended_action_type=ActionType.REQUIRE_MANUAL_REVIEW,
                severity=Severity.MEDIUM,
                target_scope=ScopeType.SELLER,
                target_id=seller_account_id,
                linked_incident_id=None,
                confidence_score=70.0,
                reason_summary=f"Guard rejections {rejections} >= 3",
                created_at=datetime.utcnow()
            )
        return None

    def scan_all_candidates(self, limit: int = 100) -> List[OpsPolicyCandidate]:
        """全アクティブ incident/alert/report scan。Returns: [OpsPolicyCandidate]"""
        return []

    def evaluate_candidate_priority(self, candidate: OpsPolicyCandidate) -> int:
        """candidate priority スコア計算 (1-100)。Returns: int"""
        score = 50
        if candidate.severity == Severity.CRITICAL:
            score += 40
        elif candidate.severity == Severity.HIGH:
            score += 20
            
        if candidate.recommended_action_type in [
            ActionType.BLOCK_LIVE_EXECUTION,
            ActionType.ENVIRONMENT_SAFE_MODE,
            ActionType.BLOCK_LISTING_CREATION
        ]:
            score += 10
            
        return min(score, 100)
