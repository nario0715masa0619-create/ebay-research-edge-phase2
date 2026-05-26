import pytest
from src.ops_policy.models.enums import CandidateType, ActionType, Severity
from src.ops_policy.services.incident_detection_service import IncidentDetectionService
from tests.ops_policy.services.test_incident_to_policy_candidate_service import MockIncident

class MockDetectionService(IncidentDetectionService):
    def __init__(self, auth_fails=0, env_rate=0.0, retry_cum=0, daily_rate=0.0, guards=0):
        self.auth_fails = auth_fails
        self.env_rate = env_rate
        self.retry_cum = retry_cum
        self.daily_rate = daily_rate
        self.guards = guards

    def _get_auth_failures(self, s, e, t): return self.auth_fails
    def _get_env_failure_rate(self, e, t): return self.env_rate
    def _get_cumulative_retry(self, s, l, t): return self.retry_cum
    def _get_daily_failure_rate(self, s, t): return self.daily_rate
    def _get_guard_rejections(self, s, e, t): return self.guards


def test_credential_spike_ge_3():
    svc = MockDetectionService(auth_fails=3)
    cand = svc.detect_credential_failure_spike("s1", "prod")
    assert cand is not None
    assert cand.candidate_type == CandidateType.CREDENTIAL_FAILURE_SPIKE
    assert cand.recommended_action_type == ActionType.BLOCK_LIVE_EXECUTION

def test_credential_spike_lt_3():
    svc = MockDetectionService(auth_fails=2)
    cand = svc.detect_credential_failure_spike("s1", "prod")
    assert cand is None

def test_high_severity_incident_high():
    svc = MockDetectionService()
    inc = MockIncident("uuid1", "HIGH", "retry_loop", "s1", "prod")
    cand = svc.detect_high_severity_incident(inc)
    assert cand is not None
    assert cand.severity == Severity.HIGH

def test_high_severity_incident_low():
    svc = MockDetectionService()
    inc = MockIncident("uuid1", "LOW", "retry_loop", "s1", "prod")
    cand = svc.detect_high_severity_incident(inc)
    assert cand is None

def test_environment_anomaly_gt_30():
    svc = MockDetectionService(env_rate=0.35)
    cand = svc.detect_environment_anomaly("prod")
    assert cand is not None
    assert cand.candidate_type == CandidateType.ENVIRONMENT_ANOMALY
    assert cand.recommended_action_type == ActionType.ENVIRONMENT_SAFE_MODE

def test_environment_anomaly_lt_30():
    svc = MockDetectionService(env_rate=0.20)
    cand = svc.detect_environment_anomaly("prod")
    assert cand is None

def test_retry_loop_gt_1h():
    svc = MockDetectionService(retry_cum=65)
    cand = svc.detect_retry_loop_risk("s1", "l1")
    assert cand is not None
    assert cand.candidate_type == CandidateType.RETRY_LOOP_RISK
    assert cand.recommended_action_type == ActionType.SUPPRESS_RETRY

def test_retry_loop_lt_1h():
    svc = MockDetectionService(retry_cum=45)
    cand = svc.detect_retry_loop_risk("s1", "l1")
    assert cand is None

def test_seller_health_gt_30():
    svc = MockDetectionService(daily_rate=0.40)
    cand = svc.detect_seller_health_degradation("s1")
    assert cand is not None
    assert cand.candidate_type == CandidateType.SELLER_HEALTH_DEGRADATION
    assert cand.recommended_action_type == ActionType.PAUSE_HANDOFF

def test_seller_health_lt_30():
    svc = MockDetectionService(daily_rate=0.20)
    cand = svc.detect_seller_health_degradation("s1")
    assert cand is None

def test_guard_rejection_ge_3():
    svc = MockDetectionService(guards=4)
    cand = svc.detect_guard_rejection_spike("s1", "prod")
    assert cand is not None
    assert cand.candidate_type == CandidateType.MANUAL_ALERT
    assert cand.recommended_action_type == ActionType.REQUIRE_MANUAL_REVIEW

def test_guard_rejection_lt_3():
    svc = MockDetectionService(guards=1)
    cand = svc.detect_guard_rejection_spike("s1", "prod")
    assert cand is None

def test_scan_all():
    svc = MockDetectionService()
    cands = svc.scan_all_candidates()
    assert isinstance(cands, list)

def test_evaluate_priority():
    svc = MockDetectionService(auth_fails=3)
    cand = svc.detect_credential_failure_spike("s1", "prod")
    # cand has Severity=CRITICAL (+40), Action=BLOCK_LIVE_EXECUTION (+10), Base=50 -> 100
    score = svc.evaluate_candidate_priority(cand)
    assert score == 100

def test_dry_run_candidates():
    # evaluate priority for medium severity / no strong action
    svc = MockDetectionService(guards=3)
    cand = svc.detect_guard_rejection_spike("s1", "prod")
    # Severity=MEDIUM (+0), Action=REQUIRE_MANUAL_REVIEW (+0), Base=50 -> 50
    score = svc.evaluate_candidate_priority(cand)
    assert score == 50
