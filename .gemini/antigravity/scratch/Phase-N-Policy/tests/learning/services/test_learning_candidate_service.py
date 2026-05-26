import pytest
from uuid import uuid4
from src.learning.services.learning_candidate_service import LearningCandidateService
from src.learning.models.learning_candidate import CandidateSource
from src.learning.models.learning_record import RootCauseCategory

@pytest.fixture
def service():
    return LearningCandidateService()

def test_generate_candidate_from_resolved_incident(service):
    iid = uuid4()
    c = service.generate_candidate_from_resolved_incident(iid)
    assert c is not None
    assert c.linked_incident_id == iid
    assert c.candidate_source == CandidateSource.RESOLVED_INCIDENT

def test_generate_candidates_from_incidents(service):
    iids = [uuid4(), uuid4()]
    cs = service.generate_candidates_from_incidents(iids)
    assert len(cs) == 2

def test_detect_repeated_pattern(service):
    c = service.detect_repeated_pattern(RootCauseCategory.ENVIRONMENT_INSTABILITY)
    assert c is not None
    assert c.candidate_source == CandidateSource.REPEATED_PATTERN

def test_detect_false_positive_cluster(service):
    c = service.detect_false_positive_cluster("auth_error")
    assert c is not None
    assert c.candidate_source == CandidateSource.FALSE_POSITIVE_DETECTED

def test_detect_recurring_error_family(service):
    c = service.detect_recurring_error_family("db_error")
    assert c is not None
    assert c.candidate_source == CandidateSource.RECURRING_ERROR_FAMILY

def test_detect_policy_ineffectiveness(service):
    pid = uuid4()
    c = service.detect_policy_ineffectiveness(pid)
    assert c is not None
    assert c.candidate_source == CandidateSource.POLICY_INEFFECTIVE
    assert c.linked_policy_id == pid

def test_scan_all_candidates(service):
    service.detect_false_positive_cluster("e1")
    service.detect_recurring_error_family("e2")
    service.detect_policy_ineffectiveness(uuid4())
    
    cs = service.scan_all_candidates()
    assert len(cs) == 3

def test_assess_candidate_priority(service):
    c_fp = service.detect_false_positive_cluster("e1")
    c_pi = service.detect_policy_ineffectiveness(uuid4())
    
    score_fp = service.assess_candidate_priority(c_fp)
    score_pi = service.assess_candidate_priority(c_pi)
    
    # FP has +5, PI has +10, assuming base scores based on confidences
    assert score_pi > score_fp
