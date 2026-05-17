import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.escalation.models import EscalationPolicy
from src.escalation.policies import get_system_default_policy
from src.repositories.persistent_escalation_state_repository import PersistentEscalationPolicyRepository
from src.escalation.policy_resolver import SellerEnvPolicyResolver

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()

def test_resolve_best_policy_hierarchy(db_session):
    policy_repo = PersistentEscalationPolicyRepository(db_session)
    resolver = SellerEnvPolicyResolver(policy_repo)

    # 1. Standard system default fallback
    p_fallback = resolver.resolve("SELLER-A", "production", "auth_refresh_failed")
    assert p_fallback.policy_id == "default_auth_refresh_failed"  # From seeded defaults in memory list

    # 2. Generic Event Policy
    policy_generic = EscalationPolicy(
        policy_id="generic_policy",
        name="Generic Policy",
        enabled=True,
        seller_account_id=None,
        environment_type=None,
        event_type="test_event",
        base_severity="warning",
        reminder_enabled=True,
        reminder_interval_seconds=600,
        reminder_max_count=2,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=False
    )
    policy_repo.upsert(policy_generic)

    res = resolver.resolve("SELLER-A", "production", "test_event")
    assert res.policy_id == "generic_policy"

    # 3. Environment Specific Policy (production test_event)
    policy_env = EscalationPolicy(
        policy_id="env_policy",
        name="Env Policy",
        enabled=True,
        seller_account_id=None,
        environment_type="production",
        event_type="test_event",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=300,
        reminder_max_count=5,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=False
    )
    policy_repo.upsert(policy_env)

    # Production should match environment policy
    res_prod = resolver.resolve("SELLER-A", "production", "test_event")
    assert res_prod.policy_id == "env_policy"

    # Sandbox should fallback to generic policy
    res_sand = resolver.resolve("SELLER-A", "sandbox", "test_event")
    assert res_sand.policy_id == "generic_policy"

    # 4. Seller Specific Policy (SELLER-A test_event)
    policy_seller = EscalationPolicy(
        policy_id="seller_policy",
        name="Seller Policy",
        enabled=True,
        seller_account_id="SELLER-A",
        environment_type=None,
        event_type="test_event",
        base_severity="error",
        reminder_enabled=True,
        reminder_interval_seconds=120,
        reminder_max_count=10,
        allow_reminder_after_ack=False,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=False
    )
    policy_repo.upsert(policy_seller)

    # SELLER-A + Sandbox should match seller specific
    res_seller_sand = resolver.resolve("SELLER-A", "sandbox", "test_event")
    assert res_seller_sand.policy_id == "seller_policy"

    # 5. Exact match: seller_account_id + environment_type + event_type
    policy_exact = EscalationPolicy(
        policy_id="exact_policy",
        name="Exact Policy",
        enabled=True,
        seller_account_id="SELLER-A",
        environment_type="production",
        event_type="test_event",
        base_severity="critical",
        reminder_enabled=True,
        reminder_interval_seconds=60,
        reminder_max_count=20,
        allow_reminder_after_ack=True,
        silence_respected=True,
        auto_resolve_on_source_recovery=True,
        escalation_enabled=True
    )
    policy_repo.upsert(policy_exact)

    res_exact = resolver.resolve("SELLER-A", "production", "test_event")
    assert res_exact.policy_id == "exact_policy"
