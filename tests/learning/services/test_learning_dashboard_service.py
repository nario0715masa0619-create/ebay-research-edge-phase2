import pytest
from src.learning.services.learning_dashboard_service import LearningDashboardService

@pytest.fixture
def service():
    return LearningDashboardService()

def test_get_learning_summary(service):
    res = service.get_learning_summary()
    assert "total_records" in res

def test_get_top_root_causes(service):
    res = service.get_top_root_causes()
    assert len(res) > 0

def test_get_recurring_issue_summary(service):
    res = service.get_recurring_issue_summary()
    assert len(res) > 0

def test_get_false_signal_summary(service):
    res = service.get_false_signal_summary()
    assert "fp_rate" in res

def test_get_seller_learning_profile(service):
    res = service.get_seller_learning_profile("s1")
    assert "recurring_issues" in res

def test_get_environment_learning_profile(service):
    res = service.get_environment_learning_profile("e1")
    assert "weak_points" in res

def test_get_recommendation_queue(service):
    res = service.get_recommendation_queue()
    assert isinstance(res, list)

def test_get_stale_learning_backlog(service):
    res = service.get_stale_learning_backlog()
    assert isinstance(res, list)
