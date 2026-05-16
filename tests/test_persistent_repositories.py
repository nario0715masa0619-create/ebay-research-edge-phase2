import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
from src.db.config import DatabaseConfig
from src.db.bootstrap import bootstrap_database, get_repository_provider
from src.db.session import create_session_factory
from src.db.models import *
from src.ebay.models import SourceItem, ProductCandidate, EbayListing, MonitoringEvent
from src.db.unit_of_work import UnitOfWork

# Use file SQLite for testing to avoid connection-specific memory DB issues
TEST_DB_URL = "sqlite:///test_shared.db"

@pytest.fixture(scope="module")
def engine():
    if os.path.exists("test_shared.db"):
        os.remove("test_shared.db")
        
    # Use file DB for persistence
    db_url = "sqlite:///test_shared.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    
    # Ensure models are registered on this thread
    from src.db import models
    Base.metadata.create_all(engine)
    
    yield engine
    
    engine.dispose()
    if os.path.exists("test_shared.db"):
        try:
            os.remove("test_shared.db")
        except:
            pass

@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine)

@pytest.fixture
def repos(session_factory):
    return get_repository_provider(session_factory)

# 1. SourceItem upsert
def test_source_item_upsert(repos):
    repo = repos["source_item"]
    item = SourceItem(
        source_item_id="SRC-001",
        source_platform="mercari",
        source_url="http://test.com/1",
        source_title="Test Item",
        source_price_jpy=1000.0
    )
    repo.upsert(item)
    repos["session"].commit()
    
    saved = repo.get_by_id("SRC-001")
    assert saved.source_title == "Test Item"
    
    # Update
    item.source_title = "Updated Item"
    repo.upsert(item)
    repos["session"].commit()
    
    saved = repo.get_by_id("SRC-001")
    assert saved.source_title == "Updated Item"

# 2. ProductCandidate save / get_by_sku
def test_candidate_persistence(repos):
    repo = repos["candidate"]
    c = ProductCandidate(
        candidate_id="CAND-001",
        source_item_id="SRC-001",
        source_platform="mercari",
        sku="SKU-001",
        source_url="http://test.com/1",
        source_title="Test Candidate",
        source_price_jpy=1000.0,
        status="collected"
    )
    repo.save(c)
    repos["session"].commit()
    
    saved = repo.get_by_sku("SKU-001")
    assert saved.candidate_id == "CAND-001"
    assert saved.status == "collected"

# 3. UnitOfWork rollback
def test_uow_rollback(session_factory, repos):
    uow = UnitOfWork(session_factory)
    with uow:
        repo = get_repository_provider(lambda: uow.session)["candidate"]
        c = ProductCandidate(
            candidate_id="CAND-ROLLBACK",
            source_item_id="SRC-001",
            source_platform="mercari",
            sku="SKU-ROLLBACK",
            source_url="http://test.com/rollback",
            source_title="Rollback Item",
            source_price_jpy=1000.0,
            status="collected"
        )
        repo.save(c)
        # No commit here
        uow.rollback()
        
    # Verify not saved
    saved = repos["candidate"].get_by_candidate_id("CAND-ROLLBACK")
    assert saved is None

# 4. EbayListing upsert
def test_ebay_listing_persistence(repos):
    repo = repos["listing"]
    l = EbayListing(
        sku="SKU-001",
        candidate_id="CAND-001",
        marketplace_id="EBAY_US",
        offer_id="OFFER-001",
        offer_status="published"
    )
    repo.upsert(l)
    repos["session"].commit()
    
    saved = repo.get_by_offer_id("OFFER-001")
    assert saved.sku == "SKU-001"
    assert saved.offer_status == "published"

# 5. MonitoringEvent persistence
def test_monitoring_event_persistence(repos):
    repo = repos["event"]
    e = MonitoringEvent(
        event_id="EVT-001",
        candidate_id="CAND-001",
        sku="SKU-001",
        event_scope="source",
        event_type="price_change",
        before_value="1000",
        after_value="1200",
        action_taken="revise"
    )
    repo.save(e)
    repos["session"].commit()
    
    events = repo.list_by_sku("SKU-001")
    assert len(events) == 1
    assert events[0].after_value == "1200"

# 6. JobRun tracking
def test_job_run_persistence(repos):
    repo = repos["job"]
    run = repo.start_run("test_job")
    run_id = run.run_id
    repos["session"].commit()
    
    repo.finish_run(run_id, "completed", {"processed_count": 5, "success_count": 3})
    repos["session"].commit()
    
    saved = repo.get_by_run_id(run_id)
    assert saved.status == "completed"
    assert saved.processed_count == 5
    assert saved.success_count == 3

def test_job_run_append_progress(repos):
    repo = repos["job"]
    run = repo.start_run("append_test")
    run_id = run.run_id
    repos["session"].commit()
    
    repo.append_progress(run_id, {"processed_count": 1, "success_count": 1})
    repo.append_progress(run_id, {"processed_count": 1, "excluded_count": 1})
    repos["session"].commit()
    
    saved = repo.get_by_run_id(run_id)
    assert saved.processed_count == 2
    assert saved.success_count == 1
    assert saved.excluded_count == 1

def test_listed_status_protection(repos):
    repo = repos["candidate"]
    c = ProductCandidate(
        candidate_id="CAND-P01",
        source_item_id="SRC-P01",
        source_platform="mercari",
        sku="SKU-P01",
        source_url="http://test.com/p1",
        source_title="Protected Item",
        source_price_jpy=1000.0,
        status="listed"
    )
    repo.save(c)
    repos["session"].commit()
    
    # Try to downgrade
    c.status = "collected"
    repo.upsert(c)
    repos["session"].commit()
    
    saved = repo.get_by_candidate_id("CAND-P01")
    assert saved.status == "listed" # Protected
