import pytest
from uuid import uuid4
from src.change_mgmt.services.change_proposal_service import ChangeProposalService
from src.change_mgmt.models.change_proposal import (
    ChangeType, ChangeScopeType, RiskLevel, ProposalStatus, ValidationStatus
)

@pytest.fixture
def service():
    return ChangeProposalService()

def test_create_from_recommendation(service):
    rec_id = uuid4()
    p = service.create_proposal_from_recommendation(
        recommendation_id=rec_id, title="T", summary="S",
        change_type=ChangeType.INCIDENT_THRESHOLD_CHANGE,
        target_component="C", scope_type=ChangeScopeType.GLOBAL,
        scope_target_id=None, risk_level=RiskLevel.MEDIUM, created_by="u"
    )
    assert p.source_recommendation_id == rec_id
    assert p.proposal_status == ProposalStatus.PROPOSED
    assert service.get_proposal_by_id(p.change_proposal_id) == p

def test_create_manual(service):
    p = service.create_manual_proposal(
        title="T", summary="S", change_type=ChangeType.POLICY_CANDIDATE_RULE_CHANGE,
        target_component="C", scope_type=ChangeScopeType.SELLER,
        scope_target_id="s1", risk_level=RiskLevel.HIGH,
        validation_strategy="V", rollback_strategy="R", created_by="u"
    )
    assert p.source_recommendation_id is None
    assert p.change_type == ChangeType.POLICY_CANDIDATE_RULE_CHANGE
    assert service.get_proposal_by_id(p.change_proposal_id) == p

def test_get_proposal_by_id_not_found(service):
    assert service.get_proposal_by_id(uuid4()) is None

def test_list_proposals_all(service):
    service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    props, total = service.list_proposals()
    assert total == 2
    assert len(props) == 2

def test_list_proposals_filter_by_status(service):
    p1 = service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    service.update_proposal_status(p1.change_proposal_id, ProposalStatus.ACTIVE, "u")
    service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    
    props, total = service.list_proposals(status=ProposalStatus.ACTIVE)
    assert total == 1
    assert props[0].proposal_status == ProposalStatus.ACTIVE

def test_list_proposals_filter_by_change_type(service):
    service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    service.create_manual_proposal("T", "S", ChangeType.INCIDENT_THRESHOLD_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    props, total = service.list_proposals(change_type=ChangeType.INCIDENT_THRESHOLD_CHANGE)
    assert total == 1

def test_list_proposals_filter_by_risk_level(service):
    service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.CRITICAL, "V", "R", "u")
    props, total = service.list_proposals(risk_level=RiskLevel.CRITICAL)
    assert total == 1

def test_list_proposals_pagination(service):
    for _ in range(5):
        service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    props, total = service.list_proposals(limit=2)
    assert total == 5
    assert len(props) == 2

def test_update_status(service):
    p1 = service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    prop, event = service.update_proposal_status(p1.change_proposal_id, ProposalStatus.UNDER_REVIEW, "u")
    assert prop.proposal_status == ProposalStatus.UNDER_REVIEW
    assert event["new_status"] == ProposalStatus.UNDER_REVIEW.value

def test_approve_proposal(service):
    p1 = service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    prop, event = service.approve_proposal(p1.change_proposal_id, "u2")
    assert prop.proposal_status == ProposalStatus.APPROVED
    assert prop.approved_by == "u2"

def test_reject_proposal(service):
    p1 = service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    prop, event = service.reject_proposal(p1.change_proposal_id, "u2", "bad idea")
    assert prop.proposal_status == ProposalStatus.REJECTED
    assert prop.rejected_by == "u2"

def test_count_by_status(service):
    p1 = service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    service.approve_proposal(p1.change_proposal_id, "u")
    service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    counts = service.count_proposals_by_status()
    assert counts.get(ProposalStatus.APPROVED) == 1
    assert counts.get(ProposalStatus.PROPOSED) == 1

def test_invalid_transition(service):
    p1 = service.create_manual_proposal("T", "S", ChangeType.GUARD_RULE_CHANGE, "C", ChangeScopeType.GLOBAL, None, RiskLevel.LOW, "V", "R", "u")
    service.reject_proposal(p1.change_proposal_id, "u", "bad")
    with pytest.raises(ValueError):
        service.update_proposal_status(p1.change_proposal_id, ProposalStatus.ACTIVE, "u")
