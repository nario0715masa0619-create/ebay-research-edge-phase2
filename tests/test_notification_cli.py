import pytest
from unittest.mock import MagicMock
from src.admin_cli.models import CliExecutionContext
from src.admin_cli.commands.notifications import NotificationCommands

@pytest.fixture
def mock_service():
    return MagicMock()

@pytest.fixture
def cmd(mock_service):
    return NotificationCommands(mock_service)

@pytest.fixture
def context():
    return CliExecutionContext(command_path="test", confirm=True)

def test_recent_command(cmd, mock_service, context):
    mock_service.get_recent.return_value = [{"history_id": "NTFH-0001"}]
    res = cmd.recent(context)
    assert res.status == "success"
    assert res.records[0]["history_id"] == "NTFH-0001"
    mock_service.get_recent.assert_called_once()

def test_failed_command(cmd, mock_service, context):
    mock_service.get_failed.return_value = []
    res = cmd.failed(context)
    assert res.status == "success"
    mock_service.get_failed.assert_called_once()

def test_show_command_not_found(cmd, mock_service, context):
    mock_service.get_details.return_value = None
    res = cmd.show(context, "NTFH-9999")
    assert res.status == "error"
    assert res.exit_code == 2

def test_resend_command_safety_guard(cmd, mock_service):
    safe_context = CliExecutionContext(command_path="test", confirm=False, dry_run=False)
    res = cmd.resend(safe_context, history_id="NTFH-0001")
    assert res.status == "error"
    assert res.exit_code == 6

def test_resend_command_success(cmd, mock_service, context):
    mock_service.resend_notification.return_value = {"status": "success"}
    res = cmd.resend(context, history_id="NTFH-0001")
    assert res.status == "success"
    mock_service.resend_notification.assert_called_once()

def test_by_sku_command(cmd, mock_service, context):
    mock_service.get_by_sku.return_value = []
    res = cmd.by_sku(context, sku="SKU-1")
    assert res.status == "success"
    mock_service.get_by_sku.assert_called_once_with("SKU-1", limit=20)

def test_rules_for_event_command(cmd, mock_service, context):
    mock_service.rule.find_rules_for_event.return_value = []
    res = cmd.rules_for_event(context, event_type="test")
    assert res.status == "success"
    mock_service.rule.find_rules_for_event.assert_called_once_with("test", severity="info")
