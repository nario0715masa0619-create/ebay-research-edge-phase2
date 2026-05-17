import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
from src.db.models import (
    SellerProfileModel, EnvironmentProfileModel, SellerEnvironmentBindingModel,
    SellerPolicySnapshotModel, SellerLocationSnapshotModel
)
from src.seller_env.models import (
    SellerProfile, EnvironmentProfile, SellerEnvironmentBinding, 
    SellerPolicySnapshot, SellerLocationSnapshot
)
from src.seller_env.bootstrap import SellerEnvironmentBootstrap
from src.seller_env.environment_guard import EnvironmentGuard
from src.admin_cli.services.seller_doctor_service import SellerDoctorService
from src.admin_cli.services.seller_ops_service import SellerOpsService
from src.admin_cli.services.seller_snapshot_ops_service import SellerSnapshotOpsService
from src.admin_cli.commands.sellers import SellerCommands
from src.admin_cli.models import CliExecutionContext

@pytest.fixture(scope="module")
def test_engine():
    db_url = "sqlite:///test_seller_env.db"
    if os.path.exists("test_seller_env.db"):
        os.remove("test_seller_env.db")
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    if os.path.exists("test_seller_env.db"):
        try: os.remove("test_seller_env.db")
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
    sess.query(SellerPolicySnapshotModel).delete()
    sess.query(SellerLocationSnapshotModel).delete()
    sess.commit()
    sess.close()

def test_seller_profile_persistence(session):
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    
    profile = SellerProfile(
        seller_account_id="seller_123",
        seller_name="Test Seller",
        seller_label="Test Label",
        default_marketplace_id="EBAY_US",
        default_currency="USD"
    )
    seller_repo.save(profile)
    session.commit()
    
    saved = seller_repo.get_by_id("seller_123")
    assert saved is not None
    assert saved.seller_name == "Test Seller"
    assert saved.seller_label == "Test Label"

def test_environment_profile_persistence(session):
    components = SellerEnvironmentBootstrap.bootstrap(session)
    env_repo = components["env_repo"]
    
    env = EnvironmentProfile(
        environment_id="sandbox_env",
        environment_name="eBay Sandbox",
        environment_type="sandbox",
        ebay_api_base_url="https://api.sandbox.ebay.com",
        ebay_oauth_base_url="https://api.sandbox.ebay.com/identity",
        supports_live_publish=False
    )
    env_repo.save(env)
    session.commit()
    
    saved = env_repo.get_by_id("sandbox_env")
    assert saved is not None
    assert saved.environment_name == "eBay Sandbox"
    assert saved.environment_type == "sandbox"
    assert saved.supports_live_publish is False

def test_seller_context_resolution(session):
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    env_repo = components["env_repo"]
    binding_repo = components["binding_repo"]
    resolver = components["resolver"]
    
    seller = SellerProfile(
        seller_account_id="seller_abc",
        seller_name="Seller ABC",
        seller_label="ABC-Label",
        default_marketplace_id="EBAY_US",
        default_currency="USD"
    )
    seller_repo.save(seller)
    
    env = EnvironmentProfile(
        environment_id="sandbox",
        environment_name="eBay Sandbox",
        environment_type="sandbox",
        ebay_api_base_url="https://api.sandbox.ebay.com",
        ebay_oauth_base_url="https://api.sandbox.ebay.com/identity",
        supports_live_publish=False
    )
    env_repo.save(env)
    
    binding = SellerEnvironmentBinding(
        binding_id="bind_abc_sandbox",
        seller_account_id="seller_abc",
        environment_id="sandbox",
        active_flag=True,
        marketplace_id="EBAY_GB",
        currency="GBP",
        fulfillment_policy_id="fulfill_1",
        payment_policy_id="pay_1",
        return_policy_id="return_1",
        merchant_location_key="loc_1"
    )
    binding_repo.save(binding)
    session.commit()
    
    ctx = resolver.resolve_context()
    assert ctx.seller_account_id == "seller_abc"
    assert ctx.environment_type == "sandbox"
    assert ctx.marketplace_id == "EBAY_GB"
    assert ctx.currency == "GBP"

def test_environment_guard_mismatch():
    guard = EnvironmentGuard()
    
    from src.seller_env.models import SellerContext
    sandbox_ctx = SellerContext(
        seller_account_id="seller_123",
        seller_label="Label",
        environment_type="sandbox",
        marketplace_id="EBAY_US",
        currency="USD"
    )
    
    with pytest.raises(RuntimeError) as exc:
        guard.check_auth_integration(sandbox_ctx, "https://api.ebay.com/identity")
    assert "Environment mismatch detected" in str(exc.value)
    
    guard.check_auth_integration(sandbox_ctx, "https://api.sandbox.ebay.com/identity")

def test_environment_guard_publish_failures():
    guard = EnvironmentGuard()
    from src.seller_env.models import SellerContext
    
    incomplete_ctx = SellerContext(
        seller_account_id="seller_123",
        seller_label="Label",
        environment_type="sandbox",
        marketplace_id="EBAY_US",
        currency="USD",
        publish_enabled=True
    )
    
    with pytest.raises(ValueError) as exc:
        guard.validate_execution(incomplete_ctx, action_type="publish")
    assert "Missing required policy or location IDs for publish" in str(exc.value)
    
    sandbox_no_publish_ctx = SellerContext(
        seller_account_id="seller_123",
        seller_label="Label",
        environment_type="sandbox",
        marketplace_id="EBAY_US",
        currency="USD",
        fulfillment_policy_id="fulfill_1",
        payment_policy_id="pay_1",
        return_policy_id="return_1",
        merchant_location_key="loc_1",
        publish_enabled=False
    )
    with pytest.raises(PermissionError) as exc:
        guard.validate_execution(sandbox_no_publish_ctx, action_type="publish")
    assert "Publish is not enabled for environment sandbox" in str(exc.value)

def test_policy_and_location_snapshots(session):
    components = SellerEnvironmentBootstrap.bootstrap(session)
    policy_repo = components["policy_repo"]
    location_repo = components["location_repo"]
    
    policy_snap = SellerPolicySnapshot(
        snapshot_id="policy_snap_1",
        seller_account_id="seller_1",
        environment_id="sandbox",
        marketplace_id="EBAY_US",
        fulfillment_policy_id="f_1",
        payment_policy_id="p_1",
        return_policy_id="r_1",
        payload={"raw": "data"}
    )
    policy_repo.save(policy_snap)
    
    loc_snap = SellerLocationSnapshot(
        snapshot_id="loc_snap_1",
        seller_account_id="seller_1",
        environment_id="sandbox",
        merchant_location_key="loc_key_1",
        payload={"raw": "loc_data"}
    )
    location_repo.save(loc_snap)
    session.commit()
    
    saved_policy = policy_repo.get_latest("seller_1", "EBAY_US")
    assert saved_policy is not None
    assert saved_policy.fulfillment_policy_id == "f_1"
    assert saved_policy.payload == {"raw": "data"}
    
    saved_loc = location_repo.get_latest("seller_1", "loc_key_1")
    assert saved_loc is not None
    assert saved_loc.merchant_location_key == "loc_key_1"
    assert saved_loc.payload == {"raw": "loc_data"}

def test_doctor_missing_refresh_token(session):
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    env_repo = components["env_repo"]
    binding_repo = components["binding_repo"]
    resolver = components["resolver"]
    guard = components["guard"]
    
    seller = SellerProfile(
        seller_account_id="seller_no_token",
        seller_name="No Token Seller",
        seller_label="NoToken"
    )
    seller_repo.save(seller)
    
    env = EnvironmentProfile(
        environment_id="sandbox",
        environment_name="Sandbox",
        environment_type="sandbox"
    )
    env_repo.save(env)
    
    binding = SellerEnvironmentBinding(
        binding_id="bind_no_token",
        seller_account_id="seller_no_token",
        environment_id="sandbox",
        active_flag=True,
        refresh_token_ref=None
    )
    binding_repo.save(binding)
    session.commit()
    
    doctor = SellerDoctorService(resolver, guard)
    report = doctor.diagnose_seller("seller_no_token")
    
    assert report["status"] == "fail"
    check_names = [c["name"] for c in report["checks"]]
    assert "refresh_token_config" in check_names
    failed_check = next(c for c in report["checks"] if c["name"] == "refresh_token_config")
    assert failed_check["status"] == "fail"
    assert "Missing refresh token reference" in failed_check["message"]

def test_active_seller_switch_confirm(session):
    components = SellerEnvironmentBootstrap.bootstrap(session)
    seller_repo = components["seller_repo"]
    env_repo = components["env_repo"]
    binding_repo = components["binding_repo"]
    
    seller_ops = SellerOpsService(seller_repo, env_repo, binding_repo)
    seller_doctor = SellerDoctorService(components["resolver"], components["guard"])
    seller_snapshot_ops = SellerSnapshotOpsService(components["policy_repo"], components["location_repo"])
    
    cmds = SellerCommands(seller_ops, seller_doctor, seller_snapshot_ops)
    
    ctx_no_confirm = CliExecutionContext(command_path="ops sellers activate", confirm=False)
    res = cmds.activate_binding(ctx_no_confirm, "seller_1", "production")
    
    assert res.status == "confirmation_required"
    assert res.exit_code == 6
