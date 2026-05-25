import pytest
from datetime import datetime, timezone, timedelta
from src.listing_execution.gateways.execution_gateway import ExecutionResult
from src.monitoring.models.alert import Alert, AlertLevel
from src.monitoring.services.execution_monitor import ExecutionMonitor

@pytest.fixture
def monitor():
    return ExecutionMonitor()

@pytest.fixture
def failed_result():
    return ExecutionResult(
        status="failed",
        listing_id="lst_123",
        attempt_id="att_123",
        error_reason="Timeout from API",
        executed_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def success_result():
    return ExecutionResult(
        status="success",
        listing_id="lst_123",
        attempt_id="att_123",
        executed_at=datetime.now(timezone.utc)
    )

def test_classify_failure_state_conflict(monitor):
    assert monitor.classify_failure("STATE_CONFLICT", 0) == AlertLevel.CRITICAL

def test_classify_failure_max_attempts(monitor):
    assert monitor.classify_failure("TIMEOUT", 3, max_attempts=3) == AlertLevel.CRITICAL

def test_classify_failure_seller_limit(monitor):
    assert monitor.classify_failure("SELLER_LIMIT", 0) == AlertLevel.WARNING

def test_classify_failure_timeout(monitor):
    assert monitor.classify_failure("TIMEOUT", 0) == AlertLevel.INFO
    assert monitor.classify_failure("NETWORK_ERROR", 0) == AlertLevel.INFO

def test_classify_failure_unknown(monitor):
    assert monitor.classify_failure("UNKNOWN", 0) == AlertLevel.WARNING

def test_should_alert_success_is_false(monitor, success_result):
    assert monitor.should_alert(success_result) is False

def test_should_alert_idempotency(monitor, failed_result):
    assert monitor.should_alert(failed_result) is True
    monitor._alert_history.add(failed_result.attempt_id)
    assert monitor.should_alert(failed_result) is False

def test_detect_failure_retry_message(monitor, failed_result):
    next_retry = datetime.now(timezone.utc) + timedelta(minutes=5)
    history = {"failure_boundary": "TIMEOUT", "next_retry_at": next_retry.isoformat()}
    alert = monitor.detect_failure(failed_result, "lst_123", history)
    assert alert.alert_level == AlertLevel.INFO
    assert "Will retry at" in alert.message

def test_detect_failure_defer_message(monitor, failed_result):
    deferred = datetime.now(timezone.utc) + timedelta(days=1)
    history = {"failure_boundary": "SELLER_LIMIT", "deferred_until": deferred.isoformat()}
    alert = monitor.detect_failure(failed_result, "lst_123", history)
    assert alert.alert_level == AlertLevel.WARNING
    assert "Deferred until" in alert.message

def test_detect_failure_cancel_message(monitor, failed_result):
    history = {"failure_boundary": "STATE_CONFLICT", "is_cancelled": True}
    alert = monitor.detect_failure(failed_result, "lst_123", history)
    assert alert.alert_level == AlertLevel.CRITICAL
    assert "Cancelling execution" in alert.message

def test_detect_failure_max_attempts_message(monitor, failed_result):
    history = {"failure_boundary": "TIMEOUT", "retry_count": 3, "max_attempts": 3}
    alert = monitor.detect_failure(failed_result, "lst_123", history)
    assert alert.alert_level == AlertLevel.CRITICAL
    assert "Cancelling execution" in alert.message

def test_log_alert_dry_run(monitor):
    alert = Alert(listing_id="l1", attempt_id="a1", failure_boundary="UNKNOWN", alert_level=AlertLevel.INFO, message="msg", reason="rsn")
    monitor.log_alert(alert, dry_run=True)
    assert alert.alert_sent_at is None
    assert len(monitor._audit_logs) == 1
    assert monitor._audit_logs[0]["action"] == "skip"
    # Dry run should not record in history to prevent blocking actual run later
    assert "a1" not in monitor._alert_history

def test_log_alert_actual(monitor):
    alert = Alert(listing_id="l1", attempt_id="a1", failure_boundary="UNKNOWN", alert_level=AlertLevel.INFO, message="msg", reason="rsn")
    monitor.log_alert(alert, dry_run=False)
    assert alert.alert_sent_at is not None
    assert len(monitor._audit_logs) == 1
    assert monitor._audit_logs[0]["action"] == "sent"
    assert "a1" in monitor._alert_history

def test_process_execution_result_integration(monitor, failed_result):
    alert = monitor.process_execution_result(failed_result, "lst_123", attempt_history={"failure_boundary": "TIMEOUT"})
    assert alert is not None
    assert alert.alert_level == AlertLevel.INFO
    assert alert.alert_sent_at is not None
    
    # Idempotency check: should return None the second time
    alert2 = monitor.process_execution_result(failed_result, "lst_123", attempt_history={"failure_boundary": "TIMEOUT"})
    assert alert2 is None

def test_process_execution_result_no_alert_on_success(monitor, success_result):
    alert = monitor.process_execution_result(success_result, "lst_123")
    assert alert is None
    assert len(monitor._audit_logs) == 0

from unittest.mock import MagicMock
def test_log_alert_with_repository_mock():
    repo = MagicMock()
    mon = ExecutionMonitor(repository=repo)
    alert = Alert(listing_id="l1", attempt_id="a1", failure_boundary="UNKNOWN", alert_level=AlertLevel.INFO, message="msg", reason="rsn")
    mon.log_alert(alert, dry_run=False)
    repo.save_alert.assert_called_once_with(alert)
    repo.append_audit_log.assert_called_once()
