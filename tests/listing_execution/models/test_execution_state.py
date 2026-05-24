import pytest
from datetime import datetime, timezone
from src.listing_execution.models.execution_state import (
    ExecutionState, 
    InvalidStateTransitionError, 
    ReadinessThresholdNotMetError
)
from src.listing_execution.services.execution_state_machine import ExecutionStateMachine
from src.listing_readiness.services.readiness_checker import ReadinessResult
from src.listing_execution.models.results import ExecutionResult

@pytest.fixture
def state_machine():
    return ExecutionStateMachine()

@pytest.fixture
def valid_readiness():
    return ReadinessResult(is_ready=True, readiness_score=100.0, readiness_reasons=[])

@pytest.fixture
def invalid_readiness():
    return ReadinessResult(is_ready=False, readiness_score=60.0, readiness_reasons=["sku_missing"])

@pytest.fixture
def success_execution():
    return ExecutionResult(
        status="success", 
        listing_id="list_123", 
        attempt_id="att_1", 
        executed_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def failed_execution():
    return ExecutionResult(
        status="timeout", 
        listing_id="list_123", 
        attempt_id="att_1", 
        executed_at=datetime.now(timezone.utc),
        error_reason="Connection timeout"
    )

# --- 1. Transition Pattern Tests (5 tests) ---

def test_transition_ready_to_executing(state_machine, valid_readiness):
    assert state_machine.current_state == ExecutionState.ready_for_execution
    new_state = state_machine.initiate(valid_readiness)
    assert new_state == ExecutionState.executing
    assert state_machine.current_state == ExecutionState.executing

def test_transition_executing_to_executed(state_machine, valid_readiness, success_execution):
    state_machine.initiate(valid_readiness)
    new_state = state_machine.complete(success_execution)
    assert new_state == ExecutionState.executed

def test_transition_executing_to_failed(state_machine, valid_readiness, failed_execution):
    state_machine.initiate(valid_readiness)
    new_state = state_machine.complete(failed_execution)
    assert new_state == ExecutionState.failed

def test_transition_executed_to_rolled_back(state_machine, valid_readiness, success_execution):
    state_machine.initiate(valid_readiness)
    state_machine.complete(success_execution)
    new_state = state_machine.rollback("User requested rollback")
    assert new_state == ExecutionState.rolled_back

def test_transition_failed_to_rolled_back(state_machine, valid_readiness, failed_execution):
    state_machine.initiate(valid_readiness)
    state_machine.complete(failed_execution)
    new_state = state_machine.rollback("Cleaning up failed attempt")
    assert new_state == ExecutionState.rolled_back

# --- 2. Invalid Transition Rejection (4 tests) ---

def test_invalid_transition_ready_to_executed(state_machine, success_execution):
    # Cannot complete() from ready_for_execution
    with pytest.raises(InvalidStateTransitionError):
        state_machine.complete(success_execution)

def test_invalid_transition_ready_to_rolled_back(state_machine):
    # Cannot rollback() from ready_for_execution
    with pytest.raises(InvalidStateTransitionError):
        state_machine.rollback("Direct rollback")

def test_invalid_transition_executing_to_rolled_back(state_machine, valid_readiness):
    # Valid transitions from executing are executed/failed. Rollback is not directly allowed.
    state_machine.initiate(valid_readiness)
    with pytest.raises(InvalidStateTransitionError):
        state_machine.rollback("Cancel execution")

def test_invalid_transition_executed_to_executing(state_machine, valid_readiness, success_execution):
    state_machine.initiate(valid_readiness)
    state_machine.complete(success_execution)
    # Cannot initiate() again from executed
    with pytest.raises(InvalidStateTransitionError):
        state_machine.initiate(valid_readiness)

# --- 3. State Machine Flow / Guard Tests (4 tests) ---

def test_flow_readiness_rejection_keeps_state(state_machine, invalid_readiness):
    assert state_machine.current_state == ExecutionState.ready_for_execution
    
    with pytest.raises(ReadinessThresholdNotMetError) as exc:
        state_machine.initiate(invalid_readiness)
        
    assert "does not meet threshold" in str(exc.value)
    # State should remain completely unchanged
    assert state_machine.current_state == ExecutionState.ready_for_execution
    assert len(state_machine.get_transition_history()) == 0

def test_flow_readiness_pass_edge_case(state_machine):
    # Score is exactly 80. Should pass.
    readiness = ReadinessResult(is_ready=False, readiness_score=80.0, readiness_reasons=["some_minor_issue"])
    new_state = state_machine.initiate(readiness)
    assert new_state == ExecutionState.executing

def test_flow_validate_transition_method_directly(state_machine):
    assert state_machine.validate_transition(ExecutionState.ready_for_execution, ExecutionState.executing) is True
    assert state_machine.validate_transition(ExecutionState.failed, ExecutionState.rolled_back) is True
    assert state_machine.validate_transition(ExecutionState.executed, ExecutionState.failed) is False
    assert state_machine.validate_transition(ExecutionState.rolled_back, ExecutionState.ready_for_execution) is False

def test_flow_full_successful_lifecycle(state_machine, valid_readiness, success_execution):
    state_machine.initiate(valid_readiness)
    assert state_machine.current_state == ExecutionState.executing
    state_machine.complete(success_execution)
    assert state_machine.current_state == ExecutionState.executed
    state_machine.rollback("Reverting")
    assert state_machine.current_state == ExecutionState.rolled_back

# --- 4. Audit Log Tests (2 tests) ---

def test_audit_log_records_transitions(state_machine, valid_readiness, success_execution):
    state_machine.initiate(valid_readiness, initiated_by="test_user")
    state_machine.complete(success_execution, initiated_by="system")
    
    history = state_machine.get_transition_history()
    assert len(history) == 2
    
    t1 = history[0]
    assert t1.from_state == ExecutionState.ready_for_execution
    assert t1.to_state == ExecutionState.executing
    assert t1.initiated_by == "test_user"
    assert "score=100.0" in t1.reason
    assert t1.timestamp is not None
    
    t2 = history[1]
    assert t2.from_state == ExecutionState.executing
    assert t2.to_state == ExecutionState.executed
    assert t2.initiated_by == "system"
    assert "succeed" in t2.reason

def test_audit_log_immutability(state_machine, valid_readiness):
    state_machine.initiate(valid_readiness)
    history = state_machine.get_transition_history()
    assert len(history) == 1
    
    # Mutating the returned list should not affect the internal audit log
    history.pop()
    internal_history = state_machine.get_transition_history()
    assert len(internal_history) == 1
