import pytest
from datetime import datetime, timedelta
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from src.ops_policy.services.ops_policy_dashboard_service import OpsPolicyDashboardService

@pytest.fixture
def mgmt_service():
    return OpsPolicyManagementService()

@pytest.fixture
def service(mgmt_service):
    return OpsPolicyDashboardService(mgmt_service)

def test_get_policy_summary(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    p2 = mgmt_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.BLOCK_LIVE_EXECUTION, "T2", "R", "u")
    
    summary = service.get_policy_summary()
    assert summary["total_count"] == 2
    assert summary["active_count"] == 1
    assert summary["proposed_count"] == 1
    assert summary["by_scope_type"][ScopeType.GLOBAL] == 1
    assert summary["by_scope_type"][ScopeType.SELLER] == 1
    assert summary["by_action_type"][ActionType.PAUSE_HANDOFF] == 1
    assert summary["created_last_24h"] == 2

def test_get_active_policy_count(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    
    assert service.get_active_policy_count() == 1

def test_get_policies_by_action_type(service, mgmt_service):
    mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.BLOCK_LIVE_EXECUTION, "T2", "R", "u")
    
    counts = service.get_policies_by_action_type()
    assert counts[ActionType.PAUSE_HANDOFF] == 1
    assert counts[ActionType.BLOCK_LIVE_EXECUTION] == 1
    assert counts[ActionType.SUPPRESS_RETRY] == 0

def test_get_policies_by_scope(service, mgmt_service):
    mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    mgmt_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    
    counts = service.get_policies_by_scope()
    assert counts[ScopeType.GLOBAL] == 1
    assert counts[ScopeType.SELLER] == 1

def test_get_seller_policies(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    mgmt_service.create_manual_policy(ScopeType.SELLER, "s2", ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    
    s1_policies = service.get_seller_policies("s1")
    assert len(s1_policies) == 1
    assert s1_policies[0].policy_id == p1.policy_id

def test_get_environment_policies(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.ENVIRONMENT, "prod", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    mgmt_service.create_manual_policy(ScopeType.ENVIRONMENT, "sandbox", ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    
    prod_policies = service.get_environment_policies("prod")
    assert len(prod_policies) == 1
    assert prod_policies[0].policy_id == p1.policy_id

def test_get_policy_application_rate(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T2", "R", "u")
    
    assert service.get_policy_application_rate() == 0.5 # 1 active out of 2

def test_get_top_affected_sellers(service, mgmt_service):
    mgmt_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    mgmt_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.BLOCK_LIVE_EXECUTION, "T2", "R", "u")
    mgmt_service.create_manual_policy(ScopeType.SELLER, "s2", ActionType.PAUSE_HANDOFF, "T3", "R", "u")
    
    top = service.get_top_affected_sellers()
    assert len(top) == 2
    assert top[0] == ("s1", 2)
    assert top[1] == ("s2", 1)
