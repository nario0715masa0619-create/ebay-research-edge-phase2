import pytest
from datetime import datetime, date, timezone
from unittest.mock import MagicMock, patch

from src.listing_execution.services.execution_summary_service import ExecutionSummaryService

@pytest.fixture
def mock_dashboard_service():
    with patch("src.listing_execution.services.execution_summary_service.ExecutionDashboardService") as mock:
        yield mock

@pytest.fixture
def summary_service(mock_dashboard_service):
    # Mocking repository directly to avoid real DB connections
    mock_repo = MagicMock()
    mock_repo._session = MagicMock()
    
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.all.return_value = [("execution_succeeded", 5), ("execution_failed", 2), ("alert_created", 1)]
    mock_repo._session.query.return_value = mock_query
    
    return ExecutionSummaryService(repository=mock_repo)

def test_generate_daily_summary(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_success_failure_ratio.return_value = (5, 2, 0.71)
    instance.get_execution_counts.return_value = {"alert_created": 1}

    dt = date(2026, 5, 25)
    result = summary_service.generate_daily_summary("seller_1", "sandbox", dt)
    assert result["seller"] == "seller_1"
    assert result["environment"] == "sandbox"
    assert result["succeeded"] == 5
    assert result["failed"] == 2
    assert result["total_executed"] == 0 # Mock didn't return execution_started
    assert result["alert_count"] == 1
    assert "date_range" in result

def test_generate_weekly_summary(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_success_failure_ratio.return_value = (5, 2, 0.71)

    dt = date(2026, 5, 25)
    result = summary_service.generate_weekly_summary(None, None, dt)
    assert result["seller"] is None
    assert result["environment"] is None
    assert result["succeeded"] == 5
    assert result["failed"] == 2

def test_generate_monthly_summary(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_success_failure_ratio.return_value = (5, 2, 0.71)

    result = summary_service.generate_monthly_summary("seller_1", "production", 2026, 5)
    assert result["seller"] == "seller_1"
    assert result["environment"] == "production"
    assert result["succeeded"] == 5

def test_get_execution_stats(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_execution_counts.return_value = {"execution_started": 10}
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    stats = summary_service.get_execution_stats(dr)
    
    instance.get_execution_counts.assert_called_once_with(dr)
    assert stats["execution_started"] == 10

def test_get_success_failure_ratio(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_success_failure_ratio.return_value = (8, 2, 0.8)
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    s, f, r = summary_service.get_success_failure_ratio(dr)
    
    instance.get_success_failure_ratio.assert_called_once_with(dr)
    assert s == 8
    assert f == 2
    assert r == 0.8

def test_get_alert_count(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_execution_counts.return_value = {"alert_created": 3}
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    count = summary_service.get_alert_count(dr)
    
    assert count == 3

def test_build_summary_success_rate(summary_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_success_failure_ratio.return_value = (8, 2, 0.8)
    
    # Test internal logic of rate
    summary_service.repository._session.query.return_value.all.return_value = [
        ("execution_succeeded", 8),
        ("execution_failed", 2)
    ]
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = summary_service._build_summary(None, None, dr)
    
    assert result["success_rate"] == 0.8
