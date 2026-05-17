import pytest
import os
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
from src.db.models import *
from src.seller_env.models import SellerProfile, EnvironmentProfile, SellerEnvironmentBinding, SellerContext
from src.seller_env.bootstrap import SellerEnvironmentBootstrap
from src.seller_env.notification_resolver import SellerNotificationRouteResolver
from src.auth.bootstrap import bootstrap_auth_layer
from src.orchestrator.models import JobDefinition, JobExecutionContext
from src.orchestrator.engine import SchedulerEngine
from src.orchestrator.lock_manager import JobLockManager
from src.orchestrator.job_registry import JobRegistry
from src.notification.models import NotificationEvent
from src.notification.bootstrap import NotificationBootstrap
from src.admin_cli.bootstrap import AdminCliBootstrap

@pytest.fixture(scope="module")
def test_engine():
    db_url = "sqlite:///test_seller_integration.db"
    if os.path.exists("test_seller_integration.db"):
        os.remove("test_seller_integration.db")
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    if os.path.exists("test_seller_integration.db"):
        try: os.remove("test_seller_integration.db")
        except: pass

@pytest.fixture
def session(test_engine):
    Session = sessionmaker(bind=test_engine)
    sess = Session()
    yield sess
    sess.rollback()
    sess.query(SellerEnvironmentBindingModel).delete()
    sess.query(SellerProfileModel).delete()
    sess.query(EnvironmentProfileModel).delete()
    sess.commit()
    sess.close()

def test_auth_bootstrap_with_seller_context(session):
    # Test Case 6: Auth bootstrap receives seller context
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    env_repo = components["env_repo"]
    binding_repo = components["binding_repo"]
    
    # Save a seller profile
    seller = SellerProfile(
        seller_account_id="seller_123",
        seller_name="Seller One",
        seller_label="S1",
        default_marketplace_id="EBAY_US",
        default_currency="USD"
    )
    seller_repo.save(seller)
    
    # Save a sandbox environment profile
    env = EnvironmentProfile(
        environment_id="sandbox",
        environment_name="Sandbox",
        environment_type="sandbox",
        ebay_api_base_url="https://api.sandbox.ebay.com",
        ebay_oauth_base_url="https://api.sandbox.ebay.com/identity"
    )
    env_repo.save(env)
    
    # Save a binding
    binding = SellerEnvironmentBinding(
        binding_id="bind_123_sandbox",
        seller_account_id="seller_123",
        environment_id="sandbox",
        active_flag=True
    )
    binding_repo.save(binding)
    session.commit()
    
    # Bootstrap Auth Layer with seller_resolver
    auth = bootstrap_auth_layer(seller_resolver=components["resolver"])
    cred_provider = auth["token_service"].credential_provider
    
    # Resolve client credentials using context
    creds = cred_provider.get_client_credentials(seller_account_id="seller_123", environment_type="sandbox")
    assert creds is not None
    assert "client_id" in creds

def test_orchestrator_job_context_propagation():
    # Test Case 7: Orchestrator job context propagates seller_account_id
    reg = JobRegistry()
    reg.register(JobDefinition(
        job_name="mock_job",
        schedule_type="interval",
        interval_seconds=10,
        target_runner_name="source_collect_runner"
    ))
    
    lock_manager = JobLockManager()
    
    # Mock runner
    mock_runner = MagicMock()
    runners = {"source_collect_runner": mock_runner}
    
    engine = SchedulerEngine(reg, lock_manager, runners)
    
    # Execute job with a seller context
    context = SellerContext(
        seller_account_id="seller_123",
        seller_label="S1",
        environment_type="production",
        marketplace_id="EBAY_US",
        currency="USD"
    )
    
    mock_runner.run_source_collection.return_value = MagicMock(success_flag=True, processed_count=1)
    
    engine.run_cycle(force_jobs=["mock_job"], seller_context=context)
    
    # Verify the runner was called with the context values
    args, kwargs = mock_runner.run_source_collection.call_args
    assert kwargs["seller_account_id"] == "seller_123"
    assert kwargs["environment_type"] == "production"
    assert kwargs["marketplace_id"] == "EBAY_US"

def test_notification_routing_by_seller_and_env(session):
    # Test Case 8: Notification routing resolves channels dynamically by seller / env
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    env_repo = components["env_repo"]
    binding_repo = components["binding_repo"]
    
    # 1. Setup Sandbox binding (restricted to console notification profile)
    seller = SellerProfile(
        seller_account_id="seller_1", seller_name="Seller 1", seller_label="S1"
    )
    seller_repo.save(seller)
    
    env_sandbox = EnvironmentProfile(
        environment_id="sandbox", environment_name="Sandbox", environment_type="sandbox"
    )
    env_repo.save(env_sandbox)
    
    binding_sandbox = SellerEnvironmentBinding(
        binding_id="bind_s1_sandbox",
        seller_account_id="seller_1",
        environment_id="sandbox",
        active_flag=True,
        notification_channel_profile="console" # sandbox only console
    )
    binding_repo.save(binding_sandbox)
    session.commit()
    
    # 2. Setup dynamic notification routing resolver
    resolver = components["resolver"]
    route_resolver = SellerNotificationRouteResolver(resolver)
    
    sandbox_event = NotificationEvent(
        event_type="scheduled_job_failed",
        title="Job Failed",
        seller_account_id="seller_1",
        environment_type="sandbox",
        severity="error"
    )
    
    channels = route_resolver.resolve_channels(sandbox_event, ["console", "slack"])
    assert channels == ["console"] # Restricted by binding notification profile

def test_disabled_seller_excluded_from_job_runs(session):
    # Test Case 14: Disabled seller is blocked/excluded
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    env_repo = components["env_repo"]
    binding_repo = components["binding_repo"]
    resolver = components["resolver"]
    
    seller = SellerProfile(
        seller_account_id="disabled_seller",
        seller_name="Disabled",
        seller_label="Disabled",
        enabled=False # Disabled!
    )
    seller_repo.save(seller)
    
    env = EnvironmentProfile(
        environment_id="production",
        environment_name="Prod",
        environment_type="production"
    )
    env_repo.save(env)
    
    binding = SellerEnvironmentBinding(
        binding_id="bind_disabled_prod",
        seller_account_id="disabled_seller",
        environment_id="production",
        active_flag=True
    )
    binding_repo.save(binding)
    session.commit()
    
    # Resolving context should raise ValueError
    with pytest.raises(ValueError) as exc:
        resolver.resolve_context(seller_account_id="disabled_seller")
    assert "is disabled" in str(exc.value)

def test_cli_bootstrap_builds_seller_aware_container(session):
    # Test Case 16: CLI / bootstrap constructs seller-aware services
    with patch("src.db.session.SessionManager.get_session", return_value=session):
        container = AdminCliBootstrap.bootstrap()
        
        assert container.seller_ops is not None
        assert container.seller_doctor is not None
        assert container.seller_snapshot_ops is not None
        assert container.seller_context_manager is not None
