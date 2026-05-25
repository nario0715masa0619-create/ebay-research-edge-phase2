import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.listing_execution.services.seller_health_analysis_service import SellerHealthAnalysisService
from src.listing_execution.models.health_report import SellerHealthReport

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    # Mocking sqlalchemy query internally
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.group_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    
    repo._session = MagicMock()
    repo._session.query.return_value = mock_query
    return repo

@pytest.fixture
def seller_service(mock_repo):
    return SellerHealthAnalysisService(repository=mock_repo)

def test_analyze_seller_health(seller_service):
    # Mock internal methods to avoid testing DB logic here
    seller_service.get_seller_execution_volume = MagicMock(return_value=100)
    seller_service.get_seller_failure_rate = MagicMock(return_value=0.05)
    seller_service.get_seller_guard_rejection_count = MagicMock(return_value=2)
    seller_service.get_seller_retry_rollback_count = MagicMock(return_value=1)
    seller_service.get_seller_major_error_patterns = MagicMock(return_value=[("ERR1", 3)])
    
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    report = seller_service.analyze_seller_health("seller_1", dr)
    
    assert isinstance(report, SellerHealthReport)
    assert report.seller_id == "seller_1"
    assert report.execution_volume == 100
    assert report.failure_rate == 0.05
    assert report.guard_rejection_count == 2
    assert report.retry_rollback_count == 1
    assert report.major_error_patterns == [("ERR1", 3)]

def test_get_seller_execution_volume(seller_service):
    seller_service.repository._session.query.return_value.scalar.return_value = 50
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    vol = seller_service.get_seller_execution_volume("seller_1", dr)
    assert vol == 50

def test_get_seller_failure_rate(seller_service):
    seller_service.repository._session.query.return_value.first.return_value = (5, 100)
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    rate = seller_service.get_seller_failure_rate("seller_1", dr)
    assert rate == 0.05

def test_get_seller_failure_rate_zero(seller_service):
    seller_service.repository._session.query.return_value.first.return_value = (0, 0)
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    rate = seller_service.get_seller_failure_rate("seller_1", dr)
    assert rate == 0.0

def test_get_seller_guard_rejection_count(seller_service):
    seller_service.repository._session.query.return_value.scalar.return_value = 12
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    count = seller_service.get_seller_guard_rejection_count("seller_1", dr)
    assert count == 12

def test_get_seller_retry_rollback_count(seller_service):
    seller_service.repository._session.query.return_value.scalar.return_value = 3
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    count = seller_service.get_seller_retry_rollback_count("seller_1", dr)
    assert count == 3

def test_get_seller_major_error_patterns(seller_service):
    seller_service.repository._session.query.return_value.all.return_value = [("E1", 10), ("E2", 5)]
    dr = (datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 5, 31, tzinfo=timezone.utc))
    patterns = seller_service.get_seller_major_error_patterns("seller_1", dr)
    assert patterns == [("E1", 10), ("E2", 5)]
