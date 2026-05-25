import pytest
import json
import csv
import io
import os
from src.admin_cli.report_commands import main

def test_summary_daily(capsys):
    main(['summary', '--period', 'daily'])
    captured = capsys.readouterr()
    assert 'total_executions' in captured.out
    assert 'daily' in captured.out

def test_summary_weekly(capsys):
    main(['summary', '--period', 'weekly'])
    captured = capsys.readouterr()
    assert 'weekly' in captured.out

def test_summary_monthly(capsys):
    main(['summary', '--period', 'monthly'])
    captured = capsys.readouterr()
    assert 'monthly' in captured.out

def test_failure_digest(capsys):
    main(['failure-digest'])
    captured = capsys.readouterr()
    assert 'timeout' in captured.out

def test_alert_digest(capsys):
    main(['alert-digest'])
    captured = capsys.readouterr()
    assert 'high_cpu' in captured.out

def test_seller_health(capsys):
    main(['seller-health', '--seller', 'seller1'])
    captured = capsys.readouterr()
    assert 'seller1' in captured.out
    assert 'healthy' in captured.out

def test_env_health(capsys):
    main(['env-health', '--environment', 'prod'])
    captured = capsys.readouterr()
    assert 'prod' in captured.out
    assert 'stable' in captured.out

def test_audit_export_csv(capsys):
    main(['audit-export', '--format', 'csv'])
    captured = capsys.readouterr()
    assert 'audit_id,action' in captured.out
    assert '1,login' in captured.out

def test_audit_export_json(capsys):
    main(['audit-export', '--format', 'json'])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data[0]['action'] == 'login'

def test_artifacts_list(capsys):
    main(['artifacts'])
    captured = capsys.readouterr()
    assert 'art-1' in captured.out

def test_show_report(capsys):
    main(['show', '--report-id', 'r1'])
    captured = capsys.readouterr()
    assert 'r1' in captured.out

def test_format_json(capsys):
    main(['summary', '--period', 'daily', '--format', 'json'])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data[0]['metric'] == 'total_executions'

def test_format_csv(capsys):
    main(['summary', '--period', 'daily', '--format', 'csv'])
    captured = capsys.readouterr()
    reader = csv.DictReader(io.StringIO(captured.out))
    row = next(reader)
    assert row['metric'] == 'total_executions'

def test_file_export(tmp_path, capsys):
    out_file = tmp_path / "out.txt"
    main(['summary', '--period', 'daily', '--output-file', str(out_file)])
    captured = capsys.readouterr()
    assert f'Saved to: {str(out_file)}' in captured.out
    assert out_file.exists()
    content = out_file.read_text(encoding='utf-8')
    assert 'total_executions' in content

def test_error_handling_invalid_date_range(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['failure-digest', '--from-date', '2023-01-02', '--to-date', '2023-01-01'])
    captured = capsys.readouterr()
    assert 'validation error' in captured.out
    assert excinfo.value.code == 1

def test_error_handling_unsupported_report_type(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['artifacts', '--report-type', 'unknown'])
    captured = capsys.readouterr()
    assert 'unsupported report type' in captured.out
    assert excinfo.value.code == 1

def test_error_handling_seller_not_found(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['seller-health', '--seller', 'unknown'])
    captured = capsys.readouterr()
    assert 'not found' in captured.out
    assert excinfo.value.code == 1

def test_error_handling_env_not_found(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['env-health', '--environment', 'unknown'])
    captured = capsys.readouterr()
    assert 'not found' in captured.out
    assert excinfo.value.code == 1

def test_error_handling_report_not_found(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['show', '--report-id', 'unknown'])
    captured = capsys.readouterr()
    assert 'not found' in captured.out
    assert excinfo.value.code == 1

def test_missing_required_arg_period(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['summary'])
    assert excinfo.value.code == 2

def test_missing_required_arg_seller(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['seller-health'])
    assert excinfo.value.code == 2

def test_missing_required_arg_env(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['env-health'])
    assert excinfo.value.code == 2
