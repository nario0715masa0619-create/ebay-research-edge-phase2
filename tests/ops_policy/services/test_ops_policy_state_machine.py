import pytest
from uuid import uuid4
from datetime import datetime
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyLevel, PolicyStatus, EventType
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.services.ops_policy_state_machine import OpsPolicyStateMachine, InvalidStateTransitionError

@pytest.fixture
def state_machine():
    return OpsPolicyStateMachine()

def create_policy(status=PolicyStatus.PROPOSED, level=PolicyLevel.STRONG):
    return OpsPolicy(
        policy_id=uuid4(),
        scope_type=ScopeType.GLOBAL,
        target_id=None,
        action_type=ActionType.BLOCK_LIVE_EXECUTION,
        level=level,
        status=status,
        title="Test Policy",
        reason_summary="Test Reason",
        evidence_summary="Test Evidence",
        linked_incident_id=None,
        effective_from=datetime.utcnow(),
        effective_until=None,
        review_due_at=None,
        created_by="user1",
        approved_by=None,
        applied_at=None,
        released_at=None,
        is_expired=False,
        priority=100,
        metadata_json={}
    )

def test_propose_policy(state_machine):
    policy = create_policy(status=PolicyStatus.PROPOSED)
    p, event = state_machine.propose_policy(policy)
    assert p.status == PolicyStatus.PROPOSED
    assert event.event_type == EventType.PROPOSED
    assert event.from_status is None
    assert event.to_status == PolicyStatus.PROPOSED

def test_approve_policy_strong(state_machine):
    policy = create_policy(status=PolicyStatus.PROPOSED, level=PolicyLevel.STRONG)
    policy.review_due_at = datetime.utcnow()
    p, event = state_machine.approve_policy(policy, "approver_1")
    assert p.status == PolicyStatus.APPROVED
    assert p.approved_by == "approver_1"
    assert event.event_type == EventType.APPROVED

def test_approve_policy_strong_missing_review_due(state_machine):
    policy = create_policy(status=PolicyStatus.PROPOSED, level=PolicyLevel.STRONG)
    with pytest.raises(ValueError, match="review_due_at"):
        state_machine.approve_policy(policy, "approver_1")

def test_activate_policy(state_machine):
    policy = create_policy(status=PolicyStatus.APPROVED)
    p, event = state_machine.activate_policy(policy)
    assert p.status == PolicyStatus.ACTIVE
    assert p.applied_at is not None
    assert event.event_type == EventType.APPLIED

def test_reject_policy(state_machine):
    policy = create_policy(status=PolicyStatus.PROPOSED)
    p, event = state_machine.reject_policy(policy, "No need", "approver_1")
    assert p.status == PolicyStatus.REJECTED
    assert event.event_type == EventType.REJECTED

def test_release_policy(state_machine):
    policy = create_policy(status=PolicyStatus.ACTIVE)
    p, event = state_machine.release_policy(policy, "user1")
    assert p.status == PolicyStatus.RELEASED
    assert p.released_at is not None
    assert event.event_type == EventType.RELEASED

def test_expire_policy(state_machine):
    policy = create_policy(status=PolicyStatus.ACTIVE)
    p, event = state_machine.expire_policy(policy)
    assert p.status == PolicyStatus.EXPIRED
    assert p.is_expired is True
    assert event.event_type == EventType.EXPIRED

def test_cancel_policy(state_machine):
    policy = create_policy(status=PolicyStatus.APPROVED)
    p, event = state_machine.cancel_policy(policy, "Changed mind", "user1")
    assert p.status == PolicyStatus.CANCELLED
    assert event.event_type == EventType.CANCELLED

def test_validate_transition(state_machine):
    assert state_machine.validate_transition(PolicyStatus.PROPOSED, PolicyStatus.APPROVED) is True
    assert state_machine.validate_transition(PolicyStatus.APPROVED, PolicyStatus.ACTIVE) is True
    assert state_machine.validate_transition(PolicyStatus.ACTIVE, PolicyStatus.RELEASED) is True
    assert state_machine.validate_transition(PolicyStatus.PROPOSED, PolicyStatus.ACTIVE) is False
    assert state_machine.validate_transition(PolicyStatus.RELEASED, PolicyStatus.ACTIVE) is False

def test_invalid_transition_raises(state_machine):
    policy = create_policy(status=PolicyStatus.RELEASED)
    with pytest.raises(InvalidStateTransitionError):
        state_machine.activate_policy(policy)

def test_terminal_state_no_reactivation(state_machine):
    for status in [PolicyStatus.RELEASED, PolicyStatus.EXPIRED, PolicyStatus.CANCELLED, PolicyStatus.REJECTED]:
        policy = create_policy(status=status)
        with pytest.raises(InvalidStateTransitionError):
            state_machine.approve_policy(policy, "approver_1")

def test_event_append_only(state_machine):
    # Just asserting the event is created correctly as a new instance with a new uuid
    policy = create_policy(status=PolicyStatus.PROPOSED)
    _, event = state_machine.reject_policy(policy, "reason", "user")
    assert event.event_id is not None
    assert event.created_at is not None

def test_metadata_preserved(state_machine):
    policy = create_policy(status=PolicyStatus.PROPOSED)
    policy.metadata_json = {"key": "value"}
    policy.review_due_at = datetime.utcnow()
    p, _ = state_machine.approve_policy(policy, "approver")
    assert p.metadata_json == {"key": "value"}
