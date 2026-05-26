import pytest
from uuid import uuid4
from datetime import datetime
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyLevel, PolicyStatus
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.services.ops_policy_precedence_service import OpsPolicyPrecedenceService
from src.ops_policy.services.effective_policy_service import EffectivePolicyService

class MockAttempt:
    def __init__(self, seller_account_id, environment):
        self.seller_account_id = seller_account_id
        self.environment = environment

@pytest.fixture
def service():
    prec_service = OpsPolicyPrecedenceService()
    return EffectivePolicyService(prec_service)

def create_policy(scope_type, action_type, target_id=None, priority=100, metadata_json=None):
    return OpsPolicy(
        policy_id=uuid4(),
        scope_type=scope_type,
        target_id=target_id,
        action_type=action_type,
        level=PolicyLevel.STRONG,
        status=PolicyStatus.ACTIVE,
        title="Test Policy",
        reason_summary=f"Reason {scope_type.value}",
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
        priority=priority,
        metadata_json=metadata_json or {}
    )

def test_single_policy_decision(service):
    p1 = create_policy(ScopeType.GLOBAL, ActionType.BLOCK_LIVE_EXECUTION)
    service.active_policies = [p1]
    
    decision = service.compute_effective_policy("seller1", "prod")
    assert decision.live_execution_allowed is False
    assert decision.contributing_policies == [p1.policy_id]

def test_multiple_policies_merge(service):
    p1 = create_policy(ScopeType.GLOBAL, ActionType.PAUSE_HANDOFF)
    p2 = create_policy(ScopeType.SELLER, ActionType.BLOCK_LIVE_EXECUTION, target_id="seller1")
    service.active_policies = [p1, p2]
    
    decision = service.compute_effective_policy("seller1", "prod")
    assert decision.live_execution_allowed is False
    assert decision.handoff_paused is True
    assert p1.policy_id in decision.contributing_policies
    assert p2.policy_id in decision.contributing_policies

def test_is_live_execution_allowed_blocked(service):
    p1 = create_policy(ScopeType.ENVIRONMENT, ActionType.BLOCK_LIVE_EXECUTION, target_id="prod")
    service.active_policies = [p1]
    assert service.is_live_execution_allowed("seller1", "prod") is False

def test_is_live_execution_allowed_allowed(service):
    p1 = create_policy(ScopeType.ENVIRONMENT, ActionType.PAUSE_HANDOFF, target_id="prod")
    service.active_policies = [p1]
    assert service.is_live_execution_allowed("seller1", "prod") is True

def test_review_level_none(service):
    p1 = create_policy(ScopeType.ENVIRONMENT, ActionType.PAUSE_HANDOFF, target_id="prod")
    service.active_policies = [p1]
    assert service.get_required_review_level("seller1", "prod") == "NONE"

def test_review_level_standard(service):
    p1 = create_policy(ScopeType.ENVIRONMENT, ActionType.REQUIRE_MANUAL_REVIEW, target_id="prod")
    service.active_policies = [p1]
    assert service.get_required_review_level("seller1", "prod") == "STANDARD"

def test_review_level_escalated(service):
    p1 = create_policy(ScopeType.ENVIRONMENT, ActionType.REQUIRE_MANUAL_REVIEW, target_id="prod")
    p2 = create_policy(ScopeType.GLOBAL, ActionType.OPERATOR_ATTENTION_REQUIRED)
    service.active_policies = [p1, p2]
    assert service.get_required_review_level("seller1", "prod") == "ESCALATED"

def test_attempt_extract(service):
    p1 = create_policy(ScopeType.SELLER, ActionType.BLOCK_LIVE_EXECUTION, target_id="seller1")
    service.active_policies = [p1]
    
    attempt = MockAttempt("seller1", "prod")
    decision = service.compute_effective_policy_for_attempt(attempt)
    assert decision.live_execution_allowed is False

def test_decision_includes_contributing_policies(service):
    p1 = create_policy(ScopeType.SELLER, ActionType.PAUSE_HANDOFF, target_id="seller1")
    service.active_policies = [p1]
    
    decision = service.compute_effective_policy("seller1", "prod")
    assert len(decision.contributing_policies) == 1
    assert decision.contributing_policies[0] == p1.policy_id

def test_ignore_other_seller_policies(service):
    p1 = create_policy(ScopeType.SELLER, ActionType.BLOCK_LIVE_EXECUTION, target_id="seller_OTHER")
    service.active_policies = [p1]
    
    decision = service.compute_effective_policy("seller1", "prod")
    assert decision.live_execution_allowed is True
    assert len(decision.contributing_policies) == 0

def test_ignore_other_env_policies(service):
    p1 = create_policy(ScopeType.ENVIRONMENT, ActionType.BLOCK_LIVE_EXECUTION, target_id="sandbox")
    service.active_policies = [p1]
    
    decision = service.compute_effective_policy("seller1", "prod")
    assert decision.live_execution_allowed is True
    assert len(decision.contributing_policies) == 0
