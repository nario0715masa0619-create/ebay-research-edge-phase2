import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.ops_policy.models.ops_policy import OpsPolicy
from src.ops_policy.models.enums import ScopeType, ActionType, PolicyStatus, PolicyLevel
from src.ops_policy.repositories.ops_policy_repository_db import OpsPolicyRepository

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def repo(session):
    return OpsPolicyRepository(session)

def _create_dummy_policy(pid=None, scope=ScopeType.GLOBAL, target=None, status=PolicyStatus.PROPOSED, action=ActionType.PAUSE_HANDOFF):
    return OpsPolicy(
        policy_id=pid or uuid4(),
        scope_type=scope,
        target_id=target,
        action_type=action,
        level=PolicyLevel.STRONG,
        status=status,
        title="Test",
        reason_summary="R",
        evidence_summary="E",
        linked_incident_id=None,
        effective_from=datetime.utcnow(),
        effective_until=None,
        review_due_at=None,
        created_by="u",
        approved_by=None,
        applied_at=None,
        released_at=None,
        is_expired=False,
        priority=50,
        metadata_json={}
    )

def test_create_policy_and_retrieve(repo):
    p = _create_dummy_policy()
    repo.create_policy(p)
    retrieved = repo.get_policy_by_id(p.policy_id)
    assert retrieved is not None
    assert retrieved.policy_id == p.policy_id
    assert retrieved.title == "Test"

def test_get_policy_by_id_not_found(repo):
    assert repo.get_policy_by_id(uuid4()) is None

def test_update_policy(repo):
    p = _create_dummy_policy()
    repo.create_policy(p)
    
    p.status = PolicyStatus.APPROVED
    p.approved_by = "admin"
    repo.update_policy(p)
    
    retrieved = repo.get_policy_by_id(p.policy_id)
    assert retrieved.status == PolicyStatus.APPROVED
    assert retrieved.approved_by == "admin"

def test_list_policies_all(repo):
    repo.create_policy(_create_dummy_policy())
    repo.create_policy(_create_dummy_policy())
    
    policies, total = repo.list_policies()
    assert total == 2
    assert len(policies) == 2

def test_list_policies_filter_by_status(repo):
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.PROPOSED))
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.ACTIVE))
    
    policies, total = repo.list_policies(status=PolicyStatus.ACTIVE)
    assert total == 1
    assert policies[0].status == PolicyStatus.ACTIVE

def test_list_policies_filter_by_scope_type(repo):
    repo.create_policy(_create_dummy_policy(scope=ScopeType.GLOBAL))
    repo.create_policy(_create_dummy_policy(scope=ScopeType.SELLER, target="s1"))
    
    policies, total = repo.list_policies(scope_type=ScopeType.SELLER)
    assert total == 1
    assert policies[0].scope_type == ScopeType.SELLER

def test_list_policies_filter_by_seller(repo):
    repo.create_policy(_create_dummy_policy(scope=ScopeType.SELLER, target="s1"))
    repo.create_policy(_create_dummy_policy(scope=ScopeType.SELLER, target="s2"))
    
    policies, total = repo.list_policies(seller_account_id="s1")
    assert total == 1
    assert policies[0].target_id == "s1"

def test_list_policies_filter_by_environment(repo):
    repo.create_policy(_create_dummy_policy(scope=ScopeType.ENVIRONMENT, target="env1"))
    repo.create_policy(_create_dummy_policy(scope=ScopeType.ENVIRONMENT, target="env2"))
    
    policies, total = repo.list_policies(environment="env2")
    assert total == 1
    assert policies[0].target_id == "env2"

def test_list_policies_pagination(repo):
    for _ in range(5):
        repo.create_policy(_create_dummy_policy())
    policies, total = repo.list_policies(limit=2, offset=0)
    assert total == 5
    assert len(policies) == 2

def test_get_active_policies(repo):
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.ACTIVE))
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.PROPOSED))
    
    active = repo.get_active_policies()
    assert len(active) == 1
    assert active[0].status == PolicyStatus.ACTIVE

def test_count_policies_by_status(repo):
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.ACTIVE))
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.ACTIVE))
    repo.create_policy(_create_dummy_policy(status=PolicyStatus.PROPOSED))
    
    counts = repo.count_policies_by_status()
    assert counts.get(PolicyStatus.ACTIVE) == 2
    assert counts.get(PolicyStatus.PROPOSED) == 1

def test_get_policies_by_scope_type(repo):
    repo.create_policy(_create_dummy_policy(scope=ScopeType.GLOBAL))
    assert len(repo.get_policies_by_scope_type(ScopeType.GLOBAL)) == 1

def test_get_policies_by_action_type(repo):
    repo.create_policy(_create_dummy_policy(action=ActionType.FORCE_DRY_RUN))
    assert len(repo.get_policies_by_action_type(ActionType.FORCE_DRY_RUN)) == 1

def test_get_seller_policies(repo):
    repo.create_policy(_create_dummy_policy(scope=ScopeType.SELLER, target="s3"))
    assert len(repo.get_seller_policies("s3")) == 1

def test_get_environment_policies(repo):
    repo.create_policy(_create_dummy_policy(scope=ScopeType.ENVIRONMENT, target="prod"))
    assert len(repo.get_environment_policies("prod")) == 1
