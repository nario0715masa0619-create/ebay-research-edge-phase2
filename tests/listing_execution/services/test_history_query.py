import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.db.models import ExecutionAttemptModel
from src.listing_execution.models.history_query import HistoryQuery
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.services.execution_history_query_service import ExecutionHistoryQueryService
from src.listing_execution.services.execution_audit_timeline_service import ExecutionAuditTimelineService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def repo(db_session: Session):
    return ExecutionHistoryRepository(db_session)

@pytest.fixture
def query_service(repo):
    return ExecutionHistoryQueryService(repo)

@pytest.fixture
def timeline_service(repo):
    return ExecutionAuditTimelineService(repo)

@pytest.fixture
def seed_data(db_session: Session):
    # Create attempts
    att1 = ExecutionAttemptModel(attempt_id="att_101", listing_id="lst_1", seller_account_id="sel_A", environment="US", status="success")
    att2 = ExecutionAttemptModel(attempt_id="att_102", listing_id="lst_1", seller_account_id="sel_A", environment="US", status="failed")
    att3 = ExecutionAttemptModel(attempt_id="att_201", listing_id="lst_2", seller_account_id="sel_B", environment="UK", status="success")
    db_session.add_all([att1, att2, att3])
    
    # Create history events
    now = datetime.now(timezone.utc)
    h1 = ExecutionHistoryModel(attempt_id="att_101", listing_id="lst_1", event_type="readiness_passed", dry_run=False, created_at=now - timedelta(days=2))
    h2 = ExecutionHistoryModel(attempt_id="att_101", listing_id="lst_1", event_type="execution_started", dry_run=False, created_at=now - timedelta(days=2))
    h3 = ExecutionHistoryModel(attempt_id="att_101", listing_id="lst_1", event_type="execution_succeeded", dry_run=False, created_at=now - timedelta(days=2))
    
    h4 = ExecutionHistoryModel(attempt_id="att_102", listing_id="lst_1", event_type="readiness_passed", dry_run=False, created_at=now - timedelta(days=1))
    h5 = ExecutionHistoryModel(attempt_id="att_102", listing_id="lst_1", event_type="execution_failed", dry_run=False, created_at=now - timedelta(days=1))
    h6 = ExecutionHistoryModel(attempt_id="att_102", listing_id="lst_1", event_type="alert_created", dry_run=False, created_at=now - timedelta(days=1))
    h7 = ExecutionHistoryModel(attempt_id="att_102", listing_id="lst_1", event_type="retry_scheduled", dry_run=False, created_at=now - timedelta(days=1))
    
    h8 = ExecutionHistoryModel(attempt_id="att_201", listing_id="lst_2", event_type="readiness_failed", dry_run=True, created_at=now)
    h9 = ExecutionHistoryModel(attempt_id="att_201", listing_id="lst_2", event_type="guard_rejected", dry_run=True, created_at=now)
    
    db_session.add_all([h1, h2, h3, h4, h5, h6, h7, h8, h9])
    db_session.commit()
    return now

def test_query_service_find_by_attempt_id(query_service, seed_data):
    results = query_service.find_by_attempt_id("att_101")
    assert len(results) == 3
    assert all(r.attempt_id == "att_101" for r in results)

def test_query_service_find_by_listing_id(query_service, seed_data):
    results = query_service.find_by_listing_id("lst_1")
    assert len(results) == 7
    assert all(r.listing_id == "lst_1" for r in results)

def test_query_service_find_by_seller_account_id(query_service, seed_data):
    results = query_service.find_by_seller_account_id("sel_B")
    assert len(results) == 2
    assert all(r.attempt_id == "att_201" for r in results)

def test_query_service_find_by_event_type(query_service, seed_data):
    results = query_service.find_by_event_type("execution_failed")
    assert len(results) == 1
    assert results[0].attempt_id == "att_102"

def test_query_service_find_by_date_range(query_service, seed_data):
    now = seed_data
    results = query_service.find_by_date_range(now - timedelta(hours=1), now + timedelta(hours=1))
    assert len(results) == 2 # att_201 events

def test_query_service_find_recent(query_service, seed_data):
    results = query_service.find_recent(limit=5)
    assert len(results) == 5

def test_query_service_find_failed_recent(query_service, seed_data):
    results = query_service.find_failed_recent()
    assert len(results) == 1
    assert results[0].event_type == "execution_failed"

def test_query_service_apply_filters_pagination(query_service, seed_data):
    query = HistoryQuery(listing_id="lst_1", limit=2, offset=1)
    result = query_service.apply_filters(query)
    assert result["total"] == 7
    assert len(result["items"]) == 2
    assert result["limit"] == 2
    assert result["offset"] == 1

def test_query_service_apply_filters_dry_run(query_service, seed_data):
    query = HistoryQuery(dry_run=True)
    result = query_service.apply_filters(query)
    assert result["total"] == 2

def test_query_service_apply_filters_environment(query_service, seed_data):
    query = HistoryQuery(environment="US")
    result = query_service.apply_filters(query)
    assert result["total"] == 7

def test_timeline_service_build_attempt_timeline(timeline_service, seed_data):
    timeline = timeline_service.build_attempt_timeline("att_101")
    assert len(timeline) == 3
    # Check asc order
    assert timeline[0].event_type == "readiness_passed"
    assert timeline[-1].event_type == "execution_succeeded"

def test_timeline_service_build_listing_timeline(timeline_service, seed_data):
    timeline = timeline_service.build_listing_timeline("lst_1")
    assert len(timeline) == 7
    assert timeline[0].attempt_id == "att_101"
    assert timeline[-1].attempt_id == "att_102"

def test_timeline_service_extract_state_transitions(timeline_service, seed_data):
    timeline = timeline_service.build_listing_timeline("lst_1")
    states = timeline_service.extract_state_transitions(timeline)
    assert len(states) == 3
    events = {s.event_type for s in states}
    assert events == {"execution_started", "execution_succeeded", "execution_failed"}

def test_timeline_service_filter_critical_events(timeline_service, seed_data):
    timeline = timeline_service.build_listing_timeline("lst_1")
    critical = timeline_service.filter_critical_events(timeline)
    assert len(critical) == 2
    events = {c.event_type for c in critical}
    assert events == {"execution_failed", "alert_created"}

def test_repository_get_event_counts(repo, seed_data):
    query = HistoryQuery(listing_id="lst_1")
    counts = repo.get_event_counts(query)
    assert counts.get("readiness_passed") == 2
    assert counts.get("execution_failed") == 1
    assert "guard_rejected" not in counts
