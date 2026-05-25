import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.listing_execution.services.alert_digest_service import AlertDigestService
from src.listing_execution.models.history_query import HistoryEventView

@pytest.fixture
def mock_dashboard_service():
    with patch("src.listing_execution.services.alert_digest_service.ExecutionDashboardService") as mock:
        yield mock

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    # Mocking sqlalchemy query internally
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.join.return_value = mock_query
    repo._session = MagicMock()
    repo._session.query.return_value = mock_query
    return repo

@pytest.fixture
def alert_service(mock_dashboard_service, mock_repo):
    return AlertDigestService(repository=mock_repo)

def test_generate_alert_digest(alert_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_alert_distribution.return_value = {"ERROR": 5, "WARNING": 2}
    
    mock_view = HistoryEventView(
        event_id="e1", attempt_id="a1", listing_id="l1",
        event_type="alert_created", dry_run=True,
        from_state="", to_state="", error_code="",
        error_message="", details={"alert_level": "ERROR"},
        created_at=datetime.now(timezone.utc), created_by="test"
    )
    
    alert_service.repository.paginate.return_value = {"items": [{"id": 1}]}
    instance.query_service._map_to_view.return_value = mock_view
    
    alert_service.repository._session.query.return_value.all.return_value = [("seller1", 5)]

    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    digest = alert_service.generate_alert_digest(dr)
    
    assert digest["alert_count_by_level"] == {"ERROR": 5, "WARNING": 2}
    assert len(digest["recent_alerts"]) == 1
    assert digest["by_seller"] == {"seller1": 5}
    assert digest["by_environment"] == {"seller1": 5}
    assert "date_range" in digest

def test_get_alert_count_by_level(alert_service, mock_dashboard_service):
    instance = mock_dashboard_service.return_value
    instance.get_alert_distribution.return_value = {"ERROR": 5}
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = alert_service.get_alert_count_by_level(dr)
    
    instance.get_alert_distribution.assert_called_once_with(dr)
    assert result == {"ERROR": 5}

def test_get_recent_alerts(alert_service, mock_dashboard_service):
    mock_view = HistoryEventView(
        event_id="e1", attempt_id="a1", listing_id="l1",
        event_type="alert_created", dry_run=True,
        from_state="", to_state="", error_code="",
        error_message="", details={"alert_level": "WARNING"},
        created_at=datetime.now(timezone.utc), created_by="test"
    )
    
    alert_service.repository.paginate.return_value = {"items": [{"id": 1}]}
    mock_dashboard_service.return_value.query_service._map_to_view.return_value = mock_view
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = alert_service.get_recent_alerts(dr, limit=5)
    
    assert len(result) == 1
    assert result[0].details["alert_level"] == "WARNING"
    alert_service.repository.paginate.assert_called_once()

def test_get_alert_by_seller(alert_service):
    alert_service.repository._session.query.return_value.all.return_value = [("seller1", 2), ("seller2", 1)]
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = alert_service.get_alert_by_seller(dr)
    
    assert result == {"seller1": 2, "seller2": 1}

def test_get_alert_by_environment(alert_service):
    alert_service.repository._session.query.return_value.all.return_value = [("sandbox", 2), ("production", 1)]
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = alert_service.get_alert_by_environment(dr)
    
    assert result == {"sandbox": 2, "production": 1}

def test_get_alert_by_dimension_empty(alert_service):
    alert_service.repository._session.query.return_value.all.return_value = []
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    result = alert_service._get_alert_count_by_dimension(None, dr)
    
    assert result == {}
