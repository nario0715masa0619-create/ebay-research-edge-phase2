import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyLevel, PolicyStatus
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.services.ops_policy_precedence_service import OpsPolicyPrecedenceService

@pytest.fixture
def service():
    return OpsPolicyPrecedenceService()

def create_policy(scope_type, action_type, priority=100, effective_from=None):
    return OpsPolicy(
        policy_id=uuid4(),
        scope_type=scope_type,
        target_id=None,
        action_type=action_type,
        level=PolicyLevel.STRONG,
        status=PolicyStatus.ACTIVE,
        title="Test Policy",
        reason_summary=f"Reason {scope_type.value}",
        evidence_summary="Test Evidence",
        linked_incident_id=None,
        effective_from=effective_from or datetime.utcnow(),
        effective_until=None,
        review_due_at=None,
        created_by="user1",
        approved_by=None,
        applied_at=None,
        released_at=None,
        is_expired=False,
        priority=priority,
        metadata_json={}
    )

def test_precedence_order(service):
    p1 = create_policy(ScopeType.SELLER, ActionType.PAUSE_HANDOFF, priority=10)
    p2 = create_policy(ScopeType.GLOBAL, ActionType.PAUSE_HANDOFF, priority=5)
    p3 = create_policy(ScopeType.ENVIRONMENT, ActionType.PAUSE_HANDOFF, priority=20)
    p4 = create_policy(ScopeType.EXECUTION_CHANNEL, ActionType.PAUSE_HANDOFF, priority=30)
    
    sorted_policies = service.apply_precedence_rules(ScopeType.EXECUTION_CHANNEL, [p1, p2, p3, p4])
    assert sorted_policies[0].scope_type == ScopeType.GLOBAL
    assert sorted_policies[1].scope_type == ScopeType.ENVIRONMENT
    assert sorted_policies[2].scope_type == ScopeType.SELLER
    assert sorted_policies[3].scope_type == ScopeType.EXECUTION_CHANNEL

def test_deny_first_block_live(service):
    assert service.is_deny_first_action(ActionType.BLOCK_LIVE_EXECUTION) is True

def test_deny_first_force_dry_run(service):
    assert service.is_deny_first_action(ActionType.FORCE_DRY_RUN) is False

def test_merge_global_override_env(service):
    global_p = create_policy(ScopeType.GLOBAL, ActionType.BLOCK_LIVE_EXECUTION)
    env_p = create_policy(ScopeType.ENVIRONMENT, ActionType.FORCE_DRY_RUN)
    
    decision = service.merge_policies(global_policy=global_p, env_policy=env_p, seller_policy=None)
    assert decision.live_execution_allowed is False
    assert decision.force_dry_run is True

def test_merge_deny_first_override_overlay(service):
    seller_p = create_policy(ScopeType.SELLER, ActionType.BLOCK_LIVE_EXECUTION) # Deny-first
    env_p = create_policy(ScopeType.ENVIRONMENT, ActionType.PAUSE_HANDOFF) # Overlay
    
    decision = service.merge_policies(global_policy=None, env_policy=env_p, seller_policy=seller_p)
    assert decision.live_execution_allowed is False
    assert decision.handoff_paused is True

def test_conflict_resolution_most_restrictive(service):
    actions = [ActionType.LIMIT_CONCURRENCY, ActionType.BLOCK_LIVE_EXECUTION, ActionType.PAUSE_HANDOFF]
    res = service.resolve_conflicting_actions(actions)
    assert res == ActionType.BLOCK_LIVE_EXECUTION

def test_apply_rules_filter_correct(service):
    # Testing apply_precedence_rules which sorts and filters
    p1 = create_policy(ScopeType.GLOBAL, ActionType.PAUSE_HANDOFF, priority=10)
    p2 = create_policy(ScopeType.GLOBAL, ActionType.PAUSE_HANDOFF, priority=20)
    
    sorted_policies = service.apply_precedence_rules(ScopeType.GLOBAL, [p1, p2])
    # Priority 20 should come before priority 10
    assert sorted_policies[0].priority == 20
    assert sorted_policies[1].priority == 10

def test_compute_precedence(service):
    now = datetime.utcnow()
    p1 = create_policy(ScopeType.GLOBAL, ActionType.PAUSE_HANDOFF, priority=10, effective_from=now)
    p2 = create_policy(ScopeType.GLOBAL, ActionType.PAUSE_HANDOFF, priority=10, effective_from=now + timedelta(seconds=1))
    
    prec = service.compute_precedence([p1, p2])
    assert len(prec[ScopeType.GLOBAL]) == 2
    # p2 is newer, so it should be first
    assert prec[ScopeType.GLOBAL][0] == p2
    assert prec[ScopeType.GLOBAL][1] == p1
