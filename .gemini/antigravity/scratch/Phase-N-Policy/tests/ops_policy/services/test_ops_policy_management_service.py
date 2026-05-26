import pytest
from uuid import uuid4
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, Severity, CandidateType
from src.ops_policy.models.ops_policy_candidate import OpsPolicyCandidate
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from datetime import datetime

@pytest.fixture
def service():
    return OpsPolicyManagementService()

def test_create_from_candidate(service):
    cand = OpsPolicyCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.HIGH_SEVERITY_INCIDENT,
        recommended_action_type=ActionType.BLOCK_LIVE_EXECUTION,
        severity=Severity.CRITICAL,
        target_scope=ScopeType.SELLER,
        target_id="s1",
        linked_incident_id=uuid4(),
        confidence_score=90.0,
        reason_summary="Test cand",
        created_at=datetime.utcnow()
    )
    p = service.create_policy_from_candidate(cand, "sys")
    assert p.status == PolicyStatus.PROPOSED
    assert p.linked_incident_id == cand.linked_incident_id
    assert p.policy_id in service.policies

def test_create_manual(service):
    p = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "Title", "Reason", "user1")
    assert p.status == PolicyStatus.PROPOSED
    assert p.created_by == "user1"
    assert p.policy_id in service.policies

def test_list_policies_filter_by_scope(service):
    service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T", "R", "u")
    res, count = service.list_policies(scope_type=ScopeType.GLOBAL)
    assert count == 1
    assert res[0].scope_type == ScopeType.GLOBAL

def test_list_policies_filter_by_status(service):
    p1 = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T", "R", "u")
    
    res, count = service.list_policies(status=PolicyStatus.ACTIVE)
    assert count == 1
    assert res[0].status == PolicyStatus.ACTIVE

def test_list_policies_pagination(service):
    for i in range(5):
        service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, f"T{i}", "R", "u")
    res, count = service.list_policies(limit=2, offset=1)
    assert count == 5
    assert len(res) == 2

def test_get_policy_by_id_found(service):
    p = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    found = service.get_policy_by_id(p.policy_id)
    assert found is not None
    assert found.policy_id == p.policy_id

def test_get_policy_by_id_not_found(service):
    found = service.get_policy_by_id(uuid4())
    assert found is None

def test_get_active_policies_filter_active(service):
    p1 = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    p2 = service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p2.status = PolicyStatus.ACTIVE
    
    actives = service.get_active_policies(seller_account_id="s1")
    assert len(actives) == 2 # 1 global + 1 matching seller

def test_link_policy_to_incident(service):
    p = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    inc_id = uuid4()
    updated = service.link_policy_to_incident(p.policy_id, inc_id)
    assert updated.linked_incident_id == inc_id
    assert len(service.events) == 1

def test_add_policy_note(service):
    p = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    event = service.add_policy_note(p.policy_id, "Some note", "u")
    assert event.note == "Some note"
    assert len(service.events) == 1

def test_list_policy_events(service):
    p = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    service.add_policy_note(p.policy_id, "N1", "u")
    service.add_policy_note(p.policy_id, "N2", "u")
    events = service.list_policy_events(p.policy_id)
    assert len(events) == 2

def test_count_policies_by_status(service):
    p1 = service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p2 = service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T", "R", "u")
    p2.status = PolicyStatus.ACTIVE
    
    counts = service.count_policies_by_status()
    assert counts[PolicyStatus.PROPOSED] == 1
    assert counts[PolicyStatus.ACTIVE] == 1
    assert counts[PolicyStatus.RELEASED] == 0

def test_list_policies_filter_by_seller(service):
    service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    service.create_manual_policy(ScopeType.SELLER, "s2", ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    res, count = service.list_policies(seller_account_id="s1")
    assert count == 1
    assert res[0].target_id == "s1"

def test_list_policies_filter_by_environment(service):
    service.create_manual_policy(ScopeType.ENVIRONMENT, "prod", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    service.create_manual_policy(ScopeType.ENVIRONMENT, "sandbox", ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    res, count = service.list_policies(environment="prod")
    assert count == 1
    assert res[0].target_id == "prod"

def test_link_policy_to_incident_not_found(service):
    import pytest
    from uuid import uuid4
    with pytest.raises(ValueError):
        service.link_policy_to_incident(uuid4(), uuid4())

def test_add_policy_note_not_found(service):
    import pytest
    from uuid import uuid4
    with pytest.raises(ValueError):
        service.add_policy_note(uuid4(), "Note", "u")
