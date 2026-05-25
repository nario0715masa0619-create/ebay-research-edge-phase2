import pytest
from datetime import datetime, timezone
from src.listing_sync.models.listing_state import ListingState
from src.listing_execution.gateways.execution_gateway import ExecutionResult
from src.listing_execution.services.listing_sync_service import ListingSyncService, StateConflictError

@pytest.fixture
def sync_service():
    return ListingSyncService()

@pytest.fixture
def success_result():
    return ExecutionResult(
        status="success",
        listing_id="lst_123",
        attempt_id="att_123",
        executed_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def failed_result():
    return ExecutionResult(
        status="failed",
        listing_id="lst_123",
        attempt_id="att_123",
        error_reason="Timeout",
        executed_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def rollback_result():
    return ExecutionResult(
        status="rolled_back",
        listing_id="lst_123",
        attempt_id="att_123",
        executed_at=datetime.now(timezone.utc)
    )

def test_sync_execution_success(sync_service, success_result):
    new_state = sync_service.sync_execution_to_listing(success_result, "lst_123")
    assert new_state == ListingState.active
    assert sync_service._get_current_state("lst_123") == ListingState.active
    assert len(sync_service._audit_logs) == 1
    assert sync_service._audit_logs[0]["to_state"] == "active"

def test_sync_execution_failed(sync_service, failed_result):
    new_state = sync_service.sync_execution_to_listing(failed_result, "lst_123")
    assert new_state == ListingState.pending_retry
    assert sync_service._get_current_state("lst_123") == ListingState.pending_retry
    assert sync_service._audit_logs[0]["to_state"] == "pending_retry"

def test_sync_execution_rolled_back(sync_service, rollback_result):
    new_state = sync_service.sync_execution_to_listing(rollback_result, "lst_123")
    assert new_state == ListingState.rolled_back
    assert sync_service._get_current_state("lst_123") == ListingState.rolled_back

def test_sync_dry_run(sync_service, success_result):
    sync_service._mock_db["lst_123"] = ListingState.pending
    new_state = sync_service.sync_execution_to_listing(success_result, "lst_123", dry_run=True)
    assert new_state == ListingState.pending # state not changed
    assert sync_service._get_current_state("lst_123") == ListingState.pending
    assert len(sync_service._audit_logs) == 1
    assert sync_service._audit_logs[0]["is_dry_run"] is True

def test_detect_state_conflict(sync_service, failed_result):
    # If currently active, applying a failed result is a conflict
    conflict = sync_service.detect_state_conflict(ListingState.active, failed_result)
    assert conflict is True
    
    # If currently pending, applying a failed result is fine
    conflict = sync_service.detect_state_conflict(ListingState.pending, failed_result)
    assert conflict is False

def test_sync_execution_conflict_raises(sync_service, failed_result):
    sync_service._mock_db["lst_123"] = ListingState.active
    with pytest.raises(StateConflictError):
        sync_service.sync_execution_to_listing(failed_result, "lst_123")

def test_handle_execution_failure(sync_service, failed_result):
    new_state = sync_service.handle_execution_failure(failed_result, "lst_123")
    assert new_state == ListingState.pending_retry

def test_handle_execution_failure_dry_run(sync_service, failed_result):
    sync_service._mock_db["lst_123"] = ListingState.pending
    new_state = sync_service.handle_execution_failure(failed_result, "lst_123", dry_run=True)
    assert new_state == ListingState.pending
    assert sync_service._audit_logs[0]["is_dry_run"] is True

def test_handle_rollback(sync_service):
    sync_service._mock_db["lst_123"] = ListingState.active
    new_state = sync_service.handle_rollback("att_123", "lst_123")
    assert new_state == ListingState.rolled_back

def test_handle_rollback_dry_run(sync_service):
    sync_service._mock_db["lst_123"] = ListingState.active
    new_state = sync_service.handle_rollback("att_123", "lst_123", dry_run=True)
    assert new_state == ListingState.active
    assert sync_service._audit_logs[0]["is_dry_run"] is True

def test_idempotency(sync_service, success_result):
    # Idempotency conceptually means applying it twice yields same result.
    state1 = sync_service.sync_execution_to_listing(success_result, "lst_123")
    state2 = sync_service.sync_execution_to_listing(success_result, "lst_123")
    assert state1 == state2 == ListingState.active
    # Since success applied to active is not a conflict in our rules, it just logs again.
    assert len(sync_service._audit_logs) == 2

def test_audit_log_format(sync_service, success_result):
    sync_service.sync_execution_to_listing(success_result, "lst_123")
    log = sync_service._audit_logs[0]
    assert "listing_id" in log
    assert "attempt_id" in log
    assert "from_state" in log
    assert "to_state" in log
    assert "reason" in log
    assert log["attempt_id"] == "att_123"

def test_sync_no_op_for_unknown_status(sync_service):
    unknown_result = ExecutionResult(
        status="unknown",
        listing_id="lst_123",
        attempt_id="att_123",
        executed_at=datetime.now(timezone.utc)
    )
    sync_service._mock_db["lst_123"] = ListingState.pending
    new_state = sync_service.sync_execution_to_listing(unknown_result, "lst_123")
    assert new_state == ListingState.pending

def test_detect_state_conflict_success_on_active(sync_service, success_result):
    # Applying success on active is not a conflict
    conflict = sync_service.detect_state_conflict(ListingState.active, success_result)
    assert conflict is False

def test_handle_rollback_logs(sync_service):
    sync_service.handle_rollback("att_999", "lst_999")
    assert sync_service._audit_logs[0]["attempt_id"] == "att_999"
    assert sync_service._audit_logs[0]["to_state"] == "rolled_back"
