import pytest
from unittest.mock import MagicMock
from src.admin_cli.services.notification_history_query_service import NotificationHistoryQueryService
from src.admin_cli.services.notification_resend_service import NotificationResendService
from src.admin_cli.services.notification_test_service import NotificationTestService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_dispatcher():
    return MagicMock()

def test_query_list_recent(mock_repo):
    service = NotificationHistoryQueryService(mock_repo)
    mock_model = MagicMock()
    mock_model.id = 1
    mock_model.event_type = "test"
    mock_model.created_at.isoformat.return_value = "2026-05-16T00:00:00"
    mock_repo.list_recent.return_value = [mock_model]
    
    res = service.list_recent()
    assert len(res) == 1
    assert res[0]["history_id"] == "NTFH-0001"

def test_resend_by_history_id(mock_repo, mock_dispatcher):
    service = NotificationResendService(mock_repo, mock_dispatcher)
    mock_model = MagicMock()
    mock_model.id = 1
    mock_model.event_type = "failed_job"
    mock_repo.get_by_history_id.return_value = mock_model
    mock_dispatcher.notify.return_value = MagicMock(dispatched_count=1, failed_count=0, results=[])
    
    res = service.resend_by_history_id(1)
    assert res["status"] == "success"
    assert res["dispatched_count"] == 1
    mock_dispatcher.notify.assert_called_once()

def test_test_notification_success(mock_dispatcher):
    service = NotificationTestService(mock_dispatcher)
    mock_notifier = MagicMock()
    mock_notifier.send.return_value = MagicMock(success_flag=True, error_summary=None)
    mock_dispatcher.channel_registry.get_notifier.return_value = mock_notifier
    
    res = service.send_test_notification("console")
    assert res["status"] == "success"
    mock_notifier.send.assert_called_once()
