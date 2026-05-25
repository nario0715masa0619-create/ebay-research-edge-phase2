import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.listing_execution.services.environment_health_analysis_service import EnvironmentHealthAnalysisService
from src.listing_execution.models.health_report import EnvironmentHealthReport

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query
    
    repo._session = MagicMock()
    repo._session.query.return_value = mock_query
    return repo

@pytest.fixture
def env_service(mock_repo):
    return EnvironmentHealthAnalysisService(repository=mock_repo)

def test_analyze_environment_health(env_service):
    env_service.get_environment_execution_volume = MagicMock(return_value=200)
    env_service.get_environment_failure_rate = MagicMock(return_value=0.01)
    env_service.get_environment_guard_rejection_count = MagicMock(return_value=5)
    env_service.get_environment_alert_concentration = MagicMock(return_value={"ERROR": 2})
    env_service.get_environment_dry_run_ratio = MagicMock(return_value=0.5)
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    report = env_service.analyze_environment_health("production", dr)
    
    assert isinstance(report, EnvironmentHealthReport)
    assert report.environment == "production"
    assert report.execution_volume == 200
    assert report.failure_rate == 0.01
    assert report.guard_rejection_count == 5
    assert report.alert_concentration == {"ERROR": 2}
    assert report.dry_run_ratio == 0.5

def test_get_environment_execution_volume(env_service):
    env_service.repository._session.query.return_value.scalar.return_value = 150
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    vol = env_service.get_environment_execution_volume("sandbox", dr)
    assert vol == 150

def test_get_environment_failure_rate(env_service):
    env_service.repository._session.query.return_value.first.return_value = (10, 1000)
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    rate = env_service.get_environment_failure_rate("production", dr)
    assert rate == 0.01

def test_get_environment_guard_rejection_count(env_service):
    env_service.repository._session.query.return_value.scalar.return_value = 7
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    count = env_service.get_environment_guard_rejection_count("sandbox", dr)
    assert count == 7

def test_get_environment_alert_concentration(env_service):
    env_service.repository._session.query.return_value.all.return_value = [
        ({"alert_level": "WARNING"},),
        ({"alert_level": "WARNING"},),
        ({"alert_level": "ERROR"},)
    ]
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    conc = env_service.get_environment_alert_concentration("production", dr)
    assert conc == {"WARNING": 2, "ERROR": 1}

def test_get_environment_dry_run_ratio(env_service):
    env_service.repository._session.query.return_value.first.return_value = (50, 200)
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    ratio = env_service.get_environment_dry_run_ratio("sandbox", dr)
    assert ratio == 0.25

def test_get_environment_dry_run_ratio_zero(env_service):
    env_service.repository._session.query.return_value.first.return_value = (0, 0)
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    ratio = env_service.get_environment_dry_run_ratio("sandbox", dr)
    assert ratio == 0.0
