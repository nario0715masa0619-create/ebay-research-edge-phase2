from typing import List, Optional
from src.incident.models.incident import IncidentSeverity
from src.incident.models.sla_policy import IncidentCandidate, IncidentCandidateType

class IncidentDetectionService:
    def __init__(self, mock_repo=None):
        self.repo = mock_repo

    def _get_failure_count(self, seller, environment, time_window):
        if self.repo: return self.repo.get_failure_count(seller, environment, time_window)
        return 0

    def _get_alert_count(self, environment, seller, time_window):
        if self.repo: return self.repo.get_alert_count(environment, seller, time_window)
        return 0

    def _get_guard_rejections(self, environment, seller, time_window):
        if self.repo: return self.repo.get_guard_rejections(environment, seller, time_window)
        return 0

    def _get_credentials_failures(self, seller, time_window):
        if self.repo: return self.repo.get_credentials_failures(seller, time_window)
        return 0

    def _get_retry_loop_duration(self, attempt_pattern):
        if self.repo: return self.repo.get_retry_loop_duration(attempt_pattern)
        return 0

    def _get_seller_failure_rate(self, seller, time_window):
        if self.repo: return self.repo.get_seller_failure_rate(seller, time_window)
        return 0.0

    def _get_dry_run_flags(self, candidate: IncidentCandidate) -> bool:
        if self.repo: return self.repo.are_all_dry_run(candidate.related_entity_ids)
        return False

    def detect_from_failure_spike(self, seller: str, environment: str, time_window: int = 10) -> List[IncidentCandidate]:
        count = self._get_failure_count(seller, environment, time_window)
        if count >= 5:
            cand = IncidentCandidate(
                candidate_type=IncidentCandidateType.HIGH_ERROR_RATE,
                severity=IncidentSeverity.HIGH,
                related_entity_ids=[f"failure_{i}" for i in range(count)],
                confidence_score=0.9,
                reason=f"Failure spike detected: {count} failures in {time_window} mins"
            )
            return [cand]
        return []

    def detect_from_alert_burst(self, time_window: int = 10, environment: str = None, seller: str = None) -> List[IncidentCandidate]:
        count = self._get_alert_count(environment, seller, time_window)
        if count >= 10:
            return [IncidentCandidate(
                candidate_type=IncidentCandidateType.SYSTEM_DOWN,
                severity=IncidentSeverity.CRITICAL,
                related_entity_ids=[f"alert_{i}" for i in range(count)],
                confidence_score=0.95,
                reason=f"Alert burst: {count} alerts in {time_window} mins"
            )]
        return []

    def detect_from_guard_rejection(self, environment: str, time_window: int = 60, seller: str = None) -> List[IncidentCandidate]:
        count = self._get_guard_rejections(environment, seller, time_window)
        if count >= 3:
            return [IncidentCandidate(
                candidate_type=IncidentCandidateType.HIGH_ERROR_RATE,
                severity=IncidentSeverity.MEDIUM,
                related_entity_ids=[f"guard_{i}" for i in range(count)],
                confidence_score=0.8,
                reason=f"Guard rejection spike: {count} rejections in {time_window} mins"
            )]
        return []

    def detect_from_credentials_failure(self, seller: str, time_window: int = 60) -> List[IncidentCandidate]:
        count = self._get_credentials_failures(seller, time_window)
        if count >= 3:
            return [IncidentCandidate(
                candidate_type=IncidentCandidateType.HIGH_ERROR_RATE,
                severity=IncidentSeverity.HIGH,
                related_entity_ids=[f"cred_{i}" for i in range(count)],
                confidence_score=0.9,
                reason=f"Credentials failure: {count} times in {time_window} mins"
            )]
        return []

    def detect_from_retry_loop_risk(self, attempt_pattern: str) -> List[IncidentCandidate]:
        duration_hours = self._get_retry_loop_duration(attempt_pattern)
        if duration_hours > 1:
            return [IncidentCandidate(
                candidate_type=IncidentCandidateType.HIGH_ERROR_RATE,
                severity=IncidentSeverity.MEDIUM,
                related_entity_ids=[attempt_pattern],
                confidence_score=0.85,
                reason=f"Retry loop risk: duration {duration_hours} hours"
            )]
        return []

    def detect_from_seller_health_degradation(self, seller: str, time_window: int = 24) -> List[IncidentCandidate]:
        rate = self._get_seller_failure_rate(seller, time_window)
        if rate > 0.30:
            return [IncidentCandidate(
                candidate_type=IncidentCandidateType.HIGH_ERROR_RATE,
                severity=IncidentSeverity.HIGH,
                related_entity_ids=[seller],
                confidence_score=0.9,
                reason=f"Seller health degradation: failure rate {rate*100}%"
            )]
        return []

    def evaluate_candidate_dry_run_awareness(self, candidate: IncidentCandidate) -> bool:
        return self._get_dry_run_flags(candidate)

    def evaluate_candidate_severity(self, candidate: IncidentCandidate) -> IncidentSeverity:
        severity = candidate.severity
        if self.evaluate_candidate_dry_run_awareness(candidate):
            if severity == IncidentSeverity.CRITICAL:
                severity = IncidentSeverity.HIGH
            elif severity == IncidentSeverity.HIGH:
                severity = IncidentSeverity.MEDIUM
            elif severity == IncidentSeverity.MEDIUM:
                severity = IncidentSeverity.LOW
        return severity
