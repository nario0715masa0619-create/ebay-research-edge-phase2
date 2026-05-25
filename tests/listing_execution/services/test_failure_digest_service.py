import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.listing_execution.services.failure_digest_service import FailureDigestService
from src.listing_execution.models.history_query import HistoryEventView

@pytest.fixture
def mock_dashboard_service():
    with patch("src.listing_execution.services.failure_digest_service.ExecutionDashboardService") as mock:
        yield mock

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def failure_service(mock_dashboard_service, mock_repo):
    return FailureDigestService(repository=mock_repo)

def test_generate_failure_digest(failure_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_top_error_codes.return_value = [("ERR1", 5)]
    instance.get_top_failure_boundaries.return_value = [("Network", 3)]
    instance.get_seller_failure_analysis.return_value = {"seller1": 0.5}
    instance.get_environment_failure_analysis.return_value = {"sandbox": 0.5}
    
    # Mocking get_recent_failures internally used repository
    mock_view = HistoryEventView(
        event_id="e1", attempt_id="a1", listing_id="l1",
        event_type="execution_failed", dry_run=True,
        from_state="", to_state="", error_code="ERR1",
        error_message="msg", details={},
        created_at=datetime.now(timezone.utc), created_by="test"
    )
    
    failure_service.repository.paginate.return_value = {"items": [{"id": 1}]}
    instance.query_service._map_to_view.return_value = mock_view

    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    digest = failure_service.generate_failure_digest(dr, limit=10)
    
    assert digest["top_error_codes"] == [("ERR1", 5)]
    assert digest["top_failure_boundaries"] == [("Network", 3)]
    assert digest["by_seller"] == {"seller1": 0.5}
    assert digest["by_environment"] == {"sandbox": 0.5}
    assert len(digest["recent_failures"]) == 1
    assert digest["recent_failures"][0]["error_code"] == "ERR1"
    assert "date_range" in digest

def test_get_top_error_codes(failure_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_top_error_codes.return_value = [("ERR1", 5)]
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = failure_service.get_top_error_codes(dr, limit=5)
    
    instance.get_top_error_codes.assert_called_once_with(limit=5, date_range=dr)
    assert result == [("ERR1", 5)]

def test_get_top_failure_boundaries(failure_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_top_failure_boundaries.return_value = [("BoundaryA", 2)]
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = failure_service.get_top_failure_boundaries(dr, limit=5)
    
    instance.get_top_failure_boundaries.assert_called_once_with(limit=5, date_range=dr)
    assert result == [("BoundaryA", 2)]

def test_get_recent_failures(failure_service, mock_dashboard_service):
    mock_view = HistoryEventView(
        event_id="e1", attempt_id="a1", listing_id="l1",
        event_type="execution_failed", dry_run=True,
        from_state="", to_state="", error_code="ERR1",
        error_message="msg", details={},
        created_at=datetime.now(timezone.utc), created_by="test"
    )
    
    failure_service.repository.paginate.return_value = {"items": [{"id": 1}]}
    mock_dashboard_service.return_value.query_service._map_to_view.return_value = mock_view
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = failure_service.get_recent_failures(dr, limit=5)
    
    assert len(result) == 1
    assert result[0].error_code == "ERR1"
    failure_service.repository.paginate.assert_called_once()

def test_get_failure_by_seller(failure_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_seller_failure_analysis.return_value = {"seller1": 0.3}
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = failure_service.get_failure_by_seller(dr)
    
    instance.get_seller_failure_analysis.assert_called_once_with(dr)
    assert result == {"seller1": 0.3}

def test_get_failure_by_environment(failure_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_environment_failure_analysis.return_value = {"production": 0.1}
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = failure_service.get_failure_by_environment(dr)
    
    instance.get_environment_failure_analysis.assert_called_once_with(dr)
    assert result == {"production": 0.1}

def test_generate_failure_digest_empty(failure_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_top_error_codes.return_value = []
    instance.get_top_failure_boundaries.return_value = []
    instance.get_seller_failure_analysis.return_value = {}
    instance.get_environment_failure_analysis.return_value = {}
    failure_service.repository.paginate.return_value = {"items": []}

    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    digest = failure_service.generate_failure_digest(dr)
    
    assert digest["top_error_codes"] == []
    assert digest["top_failure_boundaries"] == []
    assert digest["recent_failures"] == []
    assert digest["by_seller"] == {}
    assert digest["by_environment"] == {}
