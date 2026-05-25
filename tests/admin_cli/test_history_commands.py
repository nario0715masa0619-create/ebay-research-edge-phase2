import pytest
import sys
import json
from unittest.mock import patch, MagicMock
from src.admin_cli.history_commands import main
from src.listing_execution.models.history_query import HistoryEventView

@patch('src.admin_cli.history_commands.ExecutionHistoryQueryService')
def test_history_recent(mock_service, capsys):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {
        "items": [
            HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="started", dry_run=True, from_state="", to_state="", error_code="", error_message="", details={}, created_at="2026-05-25", created_by="")
        ]
    }
    
    main(["--format", "json", "recent", "--limit", "1"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["event_type"] == "started"

@patch('src.admin_cli.history_commands.ExecutionAuditTimelineService')
def test_history_show(mock_service, capsys):
    instance = mock_service.return_value
    instance.build_attempt_timeline.return_value = [
        HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="execution_failed", dry_run=True, from_state="", to_state="", error_code="ERR_1", error_message="", details={}, created_at="2026-05-25", created_by="")
    ]
    
    main(["--format", "json", "show", "--attempt-id", "a1"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["error"] == "ERR_1"

@patch('src.admin_cli.history_commands.ExecutionAuditTimelineService')
def test_history_show_not_found(mock_service, capsys):
    instance = mock_service.return_value
    instance.build_attempt_timeline.return_value = []
    
    main(["show", "--attempt-id", "a1"])
    captured = capsys.readouterr()
    assert "not found" in captured.out

@patch('src.admin_cli.history_commands.ExecutionHistoryQueryService')
def test_history_list(mock_service, capsys):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {
        "items": [
            HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="execution_failed", dry_run=True, from_state="", to_state="", error_code="ERR_1", error_message="", details={}, created_at="2026-05-25", created_by="")
        ]
    }
    
    main(["--format", "json", "list", "--seller", "S1"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["listing_id"] == "l1"

def test_history_list_validation_error(capsys):
    with pytest.raises(SystemExit):
        main(["list", "--from-date", "2026-05-26", "--to-date", "2026-05-25"])
    captured = capsys.readouterr()
    assert "validation error" in captured.err

def test_history_list_invalid_env(capsys):
    with pytest.raises(SystemExit):
        main(["list", "--environment", "INVALID"])
    captured = capsys.readouterr()
    assert "reject: invalid environment" in captured.err

@patch('src.admin_cli.history_commands.ExecutionHistoryQueryService')
def test_history_recent_csv(mock_service, capsys):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {
        "items": [
            HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="started", dry_run=True, from_state="", to_state="", error_code="", error_message="", details={}, created_at="2026-05-25", created_by="")
        ]
    }
    main(["--format", "csv", "recent", "--limit", "1"])
    captured = capsys.readouterr()
    assert "event_type,attempt_id,listing_id" in captured.out

@patch('src.admin_cli.history_commands.ExecutionHistoryQueryService')
def test_history_recent_table(mock_service, capsys):
    instance = mock_service.return_value
    instance.apply_filters.return_value = {
        "items": [
            HistoryEventView(event_id="e1", attempt_id="a1", listing_id="l1", event_type="started", dry_run=True, from_state="", to_state="", error_code="", error_message="", details={}, created_at="2026-05-25", created_by="")
        ]
    }
    main(["--format", "table", "recent", "--limit", "1"])
    captured = capsys.readouterr()
    assert "event_type           | attempt_id" in captured.out
