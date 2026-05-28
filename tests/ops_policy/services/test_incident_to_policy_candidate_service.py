import pytest
from datetime import datetime
from src.ops_policy.models.enums import CandidateType, ActionType, PolicyLevel, ScopeType, Severity
from src.ops_policy.services.incident_to_policy_candidate_service import IncidentToPolicyCandidateService

class MockIncident:
    def __init__(self, incident_id, severity, incident_type, seller_account_id, environment):
        self.incident_id = incident_id
        self.severity = severity
        self.incident_type = incident_type
        self.seller_account_id = seller_account_id
        self.environment = environment

@pytest.fixture
def service():
    return IncidentToPolicyCandidateService()

def test_generate_candidate_high_severity(service):
    inc = MockIncident("uuid1", "HIGH", "retry_loop", "s1", "prod")
    cand = service.generate_candidate_from_incident(inc)
    assert cand is not None
    assert cand.candidate_type == CandidateType.HIGH_SEVERITY_INCIDENT
    assert cand.severity == Severity.HIGH
    assert cand.recommended_action_type == ActionType.SUPPRESS_RETRY

def test_generate_candidate_low_severity(service):
    inc = MockIncident("uuid1", "LOW", "some_issue", "s1", "prod")
    cand = service.generate_candidate_from_incident(inc)
    assert cand is None

def test_generate_candidates_list_convert(service):
    inc1 = MockIncident("uuid1", "HIGH", "retry_loop", "s1", "prod")
    inc2 = MockIncident("uuid2", "LOW", "issue", "s2", "prod")
    inc3 = MockIncident("uuid3", "CRITICAL", "system_down", None, "prod")
    
    candidates = service.generate_candidates_from_incidents([inc1, inc2, inc3])
    assert len(candidates) == 2
    assert candidates[0].severity == Severity.HIGH
    assert candidates[1].severity == Severity.CRITICAL

def test_map_incident_severity_to_action(service):
    # Critical + system -> ENV_SAFE_MODE
    assert service.map_incident_severity_to_policy_action("system_error", "critical", "s1", "env") == ActionType.ENVIRONMENT_SAFE_MODE
    # Critical + other -> BLOCK_LIVE_EXECUTION
    assert service.map_incident_severity_to_policy_action("some_error", "critical", "s1", "env") == ActionType.BLOCK_LIVE_EXECUTION
    # High + auth -> BLOCK_LIVE_EXECUTION
    assert service.map_incident_severity_to_policy_action("auth_error", "high", "s1", "env") == ActionType.BLOCK_LIVE_EXECUTION
    # High + retry -> SUPPRESS_RETRY
    assert service.map_incident_severity_to_policy_action("retry_loop", "high", "s1", "env") == ActionType.SUPPRESS_RETRY
    # High + other -> PAUSE_HANDOFF
    assert service.map_incident_severity_to_policy_action("other_error", "high", "s1", "env") == ActionType.PAUSE_HANDOFF
    # Others -> REQUIRE_MANUAL_REVIEW
    assert service.map_incident_severity_to_policy_action("other_error", "medium", "s1", "env") == ActionType.REQUIRE_MANUAL_REVIEW

def test_map_incident_to_scope(service):
    assert service.map_incident_to_scope("s1", "prod") == (ScopeType.SELLER, "s1")
    assert service.map_incident_to_scope(None, "prod") == (ScopeType.ENVIRONMENT, "prod")
    assert service.map_incident_to_scope(None, None) == (ScopeType.GLOBAL, None)

def test_assess_policy_level_critical(service):
    assert service.assess_policy_level("critical", ActionType.PAUSE_HANDOFF) == PolicyLevel.STRONG

def test_assess_policy_level_medium_overlay(service):
    assert service.assess_policy_level("medium", ActionType.PAUSE_HANDOFF) == PolicyLevel.OVERLAY

def test_assess_policy_level_strong_action(service):
    assert service.assess_policy_level("medium", ActionType.BLOCK_LIVE_EXECUTION) == PolicyLevel.STRONG

def test_extract_review_due_critical(service):
    now = datetime.utcnow()
    due = service.extract_review_due_date("critical")
    assert due is not None
    # 1 hour approx
    assert 3500 < (due - now).total_seconds() < 3700

def test_extract_review_due_low(service):
    assert service.extract_review_due_date("low") is None
