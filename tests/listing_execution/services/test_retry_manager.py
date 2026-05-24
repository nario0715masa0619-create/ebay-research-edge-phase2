import pytest
from datetime import datetime, timezone
from src.listing_execution.services.retry_manager import ExecutionRetryManager, FailureBoundary, RetryAction
from src.listing_execution.services.execution_state_machine import ExecutionStateMachine
from src.listing_readiness.services.readiness_checker import ReadinessResult
from src.listing_execution.models.results import ExecutionResult

@pytest.fixture
def retry_manager():
    return ExecutionRetryManager()

@pytest.fixture
def state_machine():
    return ExecutionStateMachine()

# --- 1. Failure Boundary Classification Tests ---

def test_classify_timeout(retry_manager):
    assert retry_manager.classify_failure("API Timeout occurred") == FailureBoundary.TIMEOUT

def test_classify_network(retry_manager):
    assert retry_manager.classify_failure("Connection lost") == FailureBoundary.NETWORK_ERROR
    assert retry_manager.classify_failure("Network unreachable") == FailureBoundary.NETWORK_ERROR

def test_classify_seller_limit(retry_manager):
    assert retry_manager.classify_failure("Seller limit exceeded") == FailureBoundary.SELLER_LIMIT
    assert retry_manager.classify_failure("Capacity full") == FailureBoundary.SELLER_LIMIT

def test_classify_state_conflict(retry_manager):
    assert retry_manager.classify_failure("Duplicate listing found") == FailureBoundary.STATE_CONFLICT
    assert retry_manager.classify_failure("Invalid state for item") == FailureBoundary.STATE_CONFLICT

def test_classify_unknown(retry_manager):
    assert retry_manager.classify_failure("Server returned 500 internal error") == FailureBoundary.UNKNOWN

# --- 2. Retry Evaluation Tests ---

def test_evaluate_timeout_retryable(retry_manager):
    decision = retry_manager.evaluate_failure("API Timeout occurred", attempt_number=1)
    assert decision.action == RetryAction.RETRY_LATER
    assert decision.next_attempt_number == 2
    assert decision.next_retry_at is not None

def test_evaluate_network_retryable(retry_manager):
    decision = retry_manager.evaluate_failure("Connection lost", attempt_number=2)
    assert decision.action == RetryAction.RETRY_LATER
    assert decision.next_attempt_number == 3
    # Backoff for attempt 2 should be 1.0 * (2^1) = 2.0 seconds from now
    diff = (decision.next_retry_at - datetime.now(timezone.utc)).total_seconds()
    assert 1.0 < diff < 3.0  # Roughly 2 seconds

def test_evaluate_unknown_retryable(retry_manager):
    decision = retry_manager.evaluate_failure("500 internal error", attempt_number=1)
    assert decision.action == RetryAction.RETRY_LATER
    assert decision.next_attempt_number == 2

def test_evaluate_seller_limit_defers(retry_manager):
    decision = retry_manager.evaluate_failure("Seller limit exceeded", attempt_number=1)
    assert decision.action == RetryAction.DEFER
    assert decision.next_retry_at is None
    assert decision.next_attempt_number is None

def test_evaluate_state_conflict_cancels(retry_manager):
    decision = retry_manager.evaluate_failure("Duplicate listing found", attempt_number=1)
    assert decision.action == RetryAction.CANCEL
    assert decision.next_retry_at is None

def test_evaluate_max_attempts_reached(retry_manager):
    decision = retry_manager.evaluate_failure("API Timeout occurred", attempt_number=3)
    # Even if retryable, hitting max attempts (3) should cancel
    assert decision.action == RetryAction.CANCEL
    assert "exhausted" in decision.reason.lower()
    assert decision.next_retry_at is None

# --- 3. Backoff Logic Tests ---

def test_backoff_calculation_attempt_1(retry_manager):
    now = datetime.now(timezone.utc)
    decision = retry_manager.evaluate_failure("Timeout", attempt_number=1)
    # 1 * 2^0 = 1 sec
    diff = (decision.next_retry_at - now).total_seconds()
    assert 0.9 < diff < 1.5

def test_backoff_calculation_attempt_2(retry_manager):
    now = datetime.now(timezone.utc)
    decision = retry_manager.evaluate_failure("Timeout", attempt_number=2)
    # 1 * 2^1 = 2 sec
    diff = (decision.next_retry_at - now).total_seconds()
    assert 1.9 < diff < 2.5

# --- 4. Attempt Identity / Execution Scope Tests ---

def test_prepare_next_attempt_generates_new_id(retry_manager):
    new_id = retry_manager.prepare_next_attempt("LST-123", "LST-123_att_1", 2)
    assert new_id != "LST-123_att_1"
    assert new_id == "LST-123_att_2"

def test_safely_rollback_execution_scope(retry_manager, state_machine):
    readiness = ReadinessResult(is_ready=True, readiness_score=100.0, readiness_reasons=[])
    state_machine.initiate(readiness)
    
    execution = ExecutionResult(status="timeout", listing_id="LST-123", attempt_id="LST-123_att_1", executed_at=datetime.now(timezone.utc))
    state_machine.complete(execution)
    
    # We are in 'failed' state. We want to roll back the attempt safely.
    retry_manager.safely_rollback_execution_scope(state_machine, "LST-123_att_1", "Rolling back failed execution scope before retry.")
    
    assert state_machine.current_state.value == "rolled_back"
    
    # Audit log should have recorded it
    history = state_machine.get_transition_history()
    last_transition = history[-1]
    assert last_transition.to_state.value == "rolled_back"
    assert "LST-123_att_1" in last_transition.reason
    assert "Rolling back failed" in last_transition.reason
