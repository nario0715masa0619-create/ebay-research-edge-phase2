import pytest
from src.learning.services.recurring_issue_analysis_service import RecurringIssueAnalysisService
from src.learning.models.learning_record import RootCauseCategory

@pytest.fixture
def service():
    return RecurringIssueAnalysisService()

def test_detect_recurring_clusters(service):
    res = service.detect_recurring_clusters()
    assert len(res) > 0
    assert "cluster_id" in res[0]

def test_cluster_by_root_cause(service):
    res = service.cluster_by_root_cause(RootCauseCategory.ENVIRONMENT_INSTABILITY)
    assert "seller1" in res

def test_cluster_by_seller(service):
    res = service.cluster_by_seller("s1")
    assert len(res) > 0

def test_cluster_by_environment(service):
    res = service.cluster_by_environment("env1")
    assert len(res) > 0

def test_identify_high_impact_clusters(service):
    res = service.identify_high_impact_clusters(2)
    assert len(res) > 0

def test_predict_recurrence_risk(service):
    risk_high = service.predict_recurrence_risk("s1", "e1", "HighRisk")
    risk_low = service.predict_recurrence_risk("s1", "e1", "LowRisk")
    assert risk_high > risk_low
