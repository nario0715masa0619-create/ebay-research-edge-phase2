import pytest
from datetime import datetime, timedelta
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus
from src.ops_policy.services.ops_policy_management_service import OpsPolicyManagementService
from src.ops_policy.services.ops_policy_digest_service import OpsPolicyDigestService

@pytest.fixture
def mgmt_service():
    return OpsPolicyManagementService()

@pytest.fixture
def service(mgmt_service):
    return OpsPolicyDigestService(mgmt_service)

def test_generate_active_digest(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    p1.status = PolicyStatus.ACTIVE
    
    digest = service.generate_active_policy_digest()
    assert "# Active Operations Policies Digest" in digest
    assert "pause_handoff" in digest
    assert "T1" in digest

def test_generate_active_digest_empty(service):
    digest = service.generate_active_policy_digest()
    assert "No active policies found" in digest

def test_generate_action_digest(service, mgmt_service):
    mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.BLOCK_LIVE_EXECUTION, "T1", "R", "u")
    
    digest = service.generate_policy_action_digest(ActionType.BLOCK_LIVE_EXECUTION)
    assert "# Policy Digest: block_live_execution" in digest
    assert "T1" in digest

def test_generate_seller_digest(service, mgmt_service):
    mgmt_service.create_manual_policy(ScopeType.SELLER, "s1", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    
    digest = service.generate_seller_policy_digest("s1")
    assert "# Seller Policy Digest: s1" in digest
    assert "T1" in digest

def test_generate_environment_digest(service, mgmt_service):
    mgmt_service.create_manual_policy(ScopeType.ENVIRONMENT, "prod", ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    
    digest = service.generate_environment_policy_digest("prod")
    assert "# Environment Policy Digest: prod" in digest
    assert "T1" in digest

def test_generate_daily_digest(service, mgmt_service):
    p1 = mgmt_service.create_manual_policy(ScopeType.GLOBAL, None, ActionType.PAUSE_HANDOFF, "T1", "R", "u")
    # Make it active and released today
    p1.status = PolicyStatus.RELEASED
    p1.released_at = datetime.utcnow()
    
    digest = service.generate_daily_policy_summary_digest(datetime.utcnow())
    assert "Daily Policy Summary:" in digest
    assert "**New Policies Created**: 1" in digest
    assert "**Policies Released**: 1" in digest
