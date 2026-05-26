import pytest
from uuid import uuid4
from src.learning.services.learning_effectiveness_service import LearningEffectivenessService
from src.learning.models.learning_record import RootCauseCategory

@pytest.fixture
def service():
    return LearningEffectivenessService()

def test_evaluate_remediation_effectiveness(service):
    res = service.evaluate_remediation_effectiveness(uuid4(), [uuid4()])
    assert res is not None

def test_calculate_effectiveness_score(service):
    # Critical + long res + recurrence -> low
    score1 = service.calculate_effectiveness_score(uuid4(), "critical", 48.0, 5)
    assert score1 < 0.5
    
    # Low severity + fast res + no recurrence -> high
    score2 = service.calculate_effectiveness_score(uuid4(), "low", 2.0, 100)
    assert score2 > 0.8

def test_get_most_effective_remediation_types(service):
    res = service.get_most_effective_remediation_types(RootCauseCategory.ENVIRONMENT_INSTABILITY)
    assert len(res) > 0

def test_assess_policy_effectiveness_for_seller(service):
    res = service.assess_policy_effectiveness_for_seller("s1", uuid4())
    assert "effectiveness" in res

def test_compare_remediation_approaches(service):
    res = service.compare_remediation_approaches("auth")
    assert "automated_policy" in res

def test_track_resolution_timeline(service):
    res = service.track_resolution_timeline(uuid4())
    assert len(res) > 0

def test_identify_ineffective_policies(service):
    res = service.identify_ineffective_policies(0.4)
    assert isinstance(res, list)
