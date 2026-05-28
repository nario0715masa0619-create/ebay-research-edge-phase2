import pytest
from src.incident.services.incident_detection_service import IncidentDetectionService
from src.incident.models.sla_policy import IncidentCandidate, IncidentCandidateType
from src.incident.models.incident import IncidentSeverity

class MockRepo:
    def __init__(self, failure_count=0, alert_count=0, guard_rejections=0, cred_failures=0, retry_duration=0, seller_rate=0.0, dry_run=False):
        self.failure_count = failure_count
        self.alert_count = alert_count
        self.guard_rejections = guard_rejections
        self.cred_failures = cred_failures
        self.retry_duration = retry_duration
        self.seller_rate = seller_rate
        self.dry_run = dry_run

    def get_failure_count(self, seller, env, window): return self.failure_count
    def get_alert_count(self, env, seller, window): return self.alert_count
    def get_guard_rejections(self, env, seller, window): return self.guard_rejections
    def get_credentials_failures(self, seller, window): return self.cred_failures
    def get_retry_loop_duration(self, pattern): return self.retry_duration
    def get_seller_failure_rate(self, seller, window): return self.seller_rate
    def are_all_dry_run(self, entity_ids): return self.dry_run

# 1. detect_from_failure_spike triggered
def test_detect_failure_spike_triggered():
    svc = IncidentDetectionService(MockRepo(failure_count=5))
    cands = svc.detect_from_failure_spike("s1", "env1")
    assert len(cands) == 1
    assert cands[0].candidate_type == IncidentCandidateType.HIGH_ERROR_RATE
    assert cands[0].severity == IncidentSeverity.HIGH
    assert len(cands[0].related_entity_ids) == 5

# 2. detect_from_failure_spike not triggered
def test_detect_failure_spike_not_triggered():
    svc = IncidentDetectionService(MockRepo(failure_count=4))
    assert len(svc.detect_from_failure_spike("s1", "env1")) == 0

# 3. detect_from_alert_burst triggered
def test_detect_alert_burst_triggered():
    svc = IncidentDetectionService(MockRepo(alert_count=10))
    cands = svc.detect_from_alert_burst()
    assert len(cands) == 1
    assert cands[0].candidate_type == IncidentCandidateType.SYSTEM_DOWN
    assert cands[0].severity == IncidentSeverity.CRITICAL

# 4. detect_from_alert_burst not triggered
def test_detect_alert_burst_not_triggered():
    svc = IncidentDetectionService(MockRepo(alert_count=9))
    assert len(svc.detect_from_alert_burst()) == 0

# 5. detect_from_guard_rejection triggered
def test_detect_guard_rejection_triggered():
    svc = IncidentDetectionService(MockRepo(guard_rejections=3))
    cands = svc.detect_from_guard_rejection("env1")
    assert len(cands) == 1
    assert cands[0].severity == IncidentSeverity.MEDIUM

# 6. detect_from_guard_rejection not triggered
def test_detect_guard_rejection_not_triggered():
    svc = IncidentDetectionService(MockRepo(guard_rejections=2))
    assert len(svc.detect_from_guard_rejection("env1")) == 0

# 7. detect_from_credentials_failure triggered
def test_detect_credentials_failure_triggered():
    svc = IncidentDetectionService(MockRepo(cred_failures=3))
    cands = svc.detect_from_credentials_failure("s1")
    assert len(cands) == 1
    assert cands[0].severity == IncidentSeverity.HIGH

# 8. detect_from_retry_loop_risk triggered
def test_detect_retry_loop_risk_triggered():
    svc = IncidentDetectionService(MockRepo(retry_duration=2)) # >1 hr
    cands = svc.detect_from_retry_loop_risk("pat1")
    assert len(cands) == 1
    assert cands[0].severity == IncidentSeverity.MEDIUM

# 9. detect_from_seller_health_degradation triggered
def test_detect_seller_health_degradation_triggered():
    svc = IncidentDetectionService(MockRepo(seller_rate=0.31))
    cands = svc.detect_from_seller_health_degradation("s1")
    assert len(cands) == 1
    assert cands[0].severity == IncidentSeverity.HIGH

# 10. dry_run evaluation lowers severity from CRITICAL to HIGH
def test_dry_run_downgrades_critical():
    svc = IncidentDetectionService(MockRepo(dry_run=True))
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, [], 1.0, "")
    new_sev = svc.evaluate_candidate_severity(cand)
    assert new_sev == IncidentSeverity.HIGH

# 11. dry_run evaluation lowers severity from HIGH to MEDIUM
def test_dry_run_downgrades_high():
    svc = IncidentDetectionService(MockRepo(dry_run=True))
    cand = IncidentCandidate(IncidentCandidateType.HIGH_ERROR_RATE, IncidentSeverity.HIGH, [], 1.0, "")
    new_sev = svc.evaluate_candidate_severity(cand)
    assert new_sev == IncidentSeverity.MEDIUM

# 12. dry_run evaluation lowers severity from MEDIUM to LOW
def test_dry_run_downgrades_medium():
    svc = IncidentDetectionService(MockRepo(dry_run=True))
    cand = IncidentCandidate(IncidentCandidateType.HIGH_ERROR_RATE, IncidentSeverity.MEDIUM, [], 1.0, "")
    new_sev = svc.evaluate_candidate_severity(cand)
    assert new_sev == IncidentSeverity.LOW

# 13. no dry_run maintains severity
def test_no_dry_run_maintains_severity():
    svc = IncidentDetectionService(MockRepo(dry_run=False))
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, [], 1.0, "")
    new_sev = svc.evaluate_candidate_severity(cand)
    assert new_sev == IncidentSeverity.CRITICAL
