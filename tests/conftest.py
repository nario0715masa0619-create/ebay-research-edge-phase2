import os
import pytest
from sqlalchemy import create_engine
from src.db.base import Base
import src.db.models  # ensure models are registered before create_all

# Set DATABASE_URL to a clean test DB before any module imports the app
test_db_path = "test_web_interface.db"
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Remove existing test db
    if os.path.exists(test_db_path):
        try: os.remove(test_db_path)
        except: pass
        
    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(engine)
    
    # Let's seed default config profiles
    # We can seed seller profiles, environment profiles, and binding so context manager works cleanly
    from sqlalchemy.orm import sessionmaker
    from src.db.models import (
        SellerProfileModel, EnvironmentProfileModel, SellerEnvironmentBindingModel,
        ProductCandidateModel, EbayListingModel, JobRunModel, NotificationHistoryModel
    )
    import datetime
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. Active Binding setup
    seller = SellerProfileModel(
        seller_account_id="TEST-SELLER",
        seller_name="Test Seller",
        seller_label="Test Label",
        default_marketplace_id="EBAY_US",
        default_currency="USD",
        enabled=True
    )
    session.add(seller)
    
    env = EnvironmentProfileModel(
        environment_id="sandbox",
        environment_name="eBay Sandbox",
        environment_type="sandbox",
        ebay_api_base_url="https://api.sandbox.ebay.com",
        ebay_oauth_base_url="https://api.sandbox.ebay.com/identity",
        supports_live_publish=False,
        enabled=True
    )
    session.add(env)
    
    env_prod = EnvironmentProfileModel(
        environment_id="production",
        environment_name="eBay Production",
        environment_type="production",
        ebay_api_base_url="https://api.ebay.com",
        ebay_oauth_base_url="https://api.ebay.com/identity",
        supports_live_publish=True,
        enabled=True
    )
    session.add(env_prod)
    
    binding = SellerEnvironmentBindingModel(
        binding_id="bind_test_sandbox",
        seller_account_id="TEST-SELLER",
        environment_id="sandbox",
        active_flag=True,
        marketplace_id="EBAY_US",
        currency="USD",
        fulfillment_policy_id="fulfill_test",
        payment_policy_id="pay_test",
        return_policy_id="return_test",
        merchant_location_key="loc_test",
        refresh_token_ref="REFRESH_MOCK"
    )
    session.add(binding)
    
    binding_prod = SellerEnvironmentBindingModel(
        binding_id="bind_test_prod",
        seller_account_id="TEST-SELLER",
        environment_id="production",
        active_flag=False,
        marketplace_id="EBAY_US",
        currency="USD",
        fulfillment_policy_id="fulfill_test_prod",
        payment_policy_id="pay_test_prod",
        return_policy_id="return_test_prod",
        merchant_location_key="loc_test_prod",
        refresh_token_ref="REFRESH_MOCK_PROD"
    )
    session.add(binding_prod)
    
    # 2. Product Candidates setup
    candidate = ProductCandidateModel(
        candidate_id="cand_1",
        source_item_id="MOCK-SOURCE-ITEM-ID",
        sku="SKU-TEST-WEB",
        source_url="https://item.fril.jp/mock_item",
        source_title="Mock Source Title",
        source_platform="Yahoo! Flea Market",
        source_price_jpy=1500.0,
        seller_account_id="TEST-SELLER",
        status="failed",
        listing_readiness_status="failed",
        listing_blockers_json=["PROFIT_THRESHOLD_NOT_MET", "MISSING_WEIGHT"],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )
    session.add(candidate)
    
    # 3. Active Listings setup
    listing = EbayListingModel(
        sku="SKU-TEST-WEB",
        candidate_id="cand_1",
        marketplace_id="EBAY_US",
        listing_id="123456789012",
        seller_account_id="TEST-SELLER",
        listing_status="active",
        offer_status="active",
        listed_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )
    session.add(listing)
    
    # 4. Job Runs setup
    job_run = JobRunModel(
        run_id="run_1",
        job_name="monitoring",
        status="completed",
        started_at=datetime.datetime.now(),
        finished_at=datetime.datetime.now()
    )
    session.add(job_run)
    
    # 5. Notification History setup
    notif = NotificationHistoryModel(
        id=1,
        event_id="EVT-001",
        event_type="test_alert",
        severity="info",
        priority="normal",
        sku="SKU-TEST-WEB",
        seller_account_id="TEST-SELLER",
        channel_name="email",
        dispatch_status="success",
        meta_json={"test_key": "test_val"},
        title="Test Title",
        created_at=datetime.datetime.now()
    )
    session.add(notif)
    
    session.commit()
    session.close()
    
    yield
    
    engine.dispose()
    if os.path.exists(test_db_path):
        try: os.remove(test_db_path)
        except: pass
