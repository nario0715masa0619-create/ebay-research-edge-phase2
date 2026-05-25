import pytest
import sys
import json
from unittest.mock import patch, MagicMock
from src.admin_cli.dashboard_commands import main
from src.listing_execution.models.dashboard_summary import DashboardSummary

@patch('src.admin_cli.dashboard_commands.ExecutionDashboardService')
def test_dashboard_overview(mock_service, capsys):
    instance = mock_service.return_value
    instance.get_overview_summary.return_value = DashboardSummary(
        total_executions=10,
        succeeded=8,
        failed=2,
        rolled_back=0,
        alert_count=1,
        success_rate=0.8,
        failure_rate=0.2,
        alert_level_distribution={},
        top_error_codes=[],
        top_failure_boundaries=[],
        dry_run_count=5,
        live_count=5,
        seller_failure_rates={},
        environment_failure_rates={},
        guard_rejection_count=0
    )
    
    main(["--format", "json", "overview"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["total"] == 10
    assert data[0]["success_rate"] == 0.8

@patch('src.admin_cli.dashboard_commands.ExecutionDashboardService')
def test_dashboard_sellers(mock_service, capsys):
    instance = mock_service.return_value
    instance.get_seller_failure_analysis.return_value = {"S1": 0.5, "S2": 0.0}
    
    main(["--format", "json", "sellers"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    assert data[0]["seller"] == "S1"
    assert data[0]["failure_rate"] == 0.5

@patch('src.admin_cli.dashboard_commands.ExecutionDashboardService')
def test_dashboard_errors(mock_service, capsys):
    instance = mock_service.return_value
    instance.get_top_error_codes.return_value = [("ERR_1", 5), ("ERR_2", 3)]
    
    main(["--format", "json", "errors"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    assert data[0]["error_code"] == "ERR_1"
    assert data[0]["count"] == 5

def test_dashboard_invalid_date(capsys):
    with pytest.raises(SystemExit):
        main(["overview", "--from-date", "2026-05-26", "--to-date", "2026-05-25"])
    captured = capsys.readouterr()
    assert "validation error" in captured.err

@patch('src.admin_cli.dashboard_commands.ExecutionDashboardService')
def test_dashboard_overview_table(mock_service, capsys):
    instance = mock_service.return_value
    instance.get_overview_summary.return_value = DashboardSummary(
        total_executions=10,
        succeeded=8,
        failed=2,
        rolled_back=0,
        alert_count=1,
        success_rate=0.8,
        failure_rate=0.2,
        alert_level_distribution={},
        top_error_codes=[],
        top_failure_boundaries=[],
        dry_run_count=5,
        live_count=5,
        seller_failure_rates={},
        environment_failure_rates={},
        guard_rejection_count=0
    )
    main(["--format", "table", "overview"])
    captured = capsys.readouterr()
    assert "total                | success_rate" in captured.out

@patch('src.admin_cli.dashboard_commands.ExecutionDashboardService')
def test_dashboard_overview_csv(mock_service, capsys):
    instance = mock_service.return_value
    instance.get_overview_summary.return_value = DashboardSummary(
        total_executions=10,
        succeeded=8,
        failed=2,
        rolled_back=0,
        alert_count=1,
        success_rate=0.8,
        failure_rate=0.2,
        alert_level_distribution={},
        top_error_codes=[],
        top_failure_boundaries=[],
        dry_run_count=5,
        live_count=5,
        seller_failure_rates={},
        environment_failure_rates={},
        guard_rejection_count=0
    )
    main(["--format", "csv", "overview"])
    captured = capsys.readouterr()
    assert "total,success_rate,failure_count" in captured.out

@patch('src.admin_cli.dashboard_commands.ExecutionDashboardService')
def test_dashboard_empty_csv(mock_service, capsys):
    instance = mock_service.return_value
    instance.get_seller_failure_analysis.return_value = {}
    main(["--format", "csv", "sellers"])
    captured = capsys.readouterr()
    assert captured.out == ""
