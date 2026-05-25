import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base

from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.db.models import ExecutionAttemptModel
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository
from src.listing_execution.services.execution_dashboard_service import ExecutionDashboardService

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def repo(db_session):
    return ExecutionHistoryRepository(db_session)

@pytest.fixture
def dashboard_service(repo):
    return ExecutionDashboardService(repo)

@pytest.fixture
def seed_dashboard_data(db_session):
    now = datetime.now(timezone.utc)
    # Attempts
    att1 = ExecutionAttemptModel(attempt_id="d_att_1", listing_id="l_1", seller_account_id="S1", environment="US", status="succeeded", failure_boundary=None, created_at=now)
    att2 = ExecutionAttemptModel(attempt_id="d_att_2", listing_id="l_2", seller_account_id="S1", environment="US", status="failed", failure_boundary="TIMEOUT", created_at=now)
    att3 = ExecutionAttemptModel(attempt_id="d_att_3", listing_id="l_3", seller_account_id="S2", environment="UK", status="failed", failure_boundary="SELLER_LIMIT", created_at=now)
    db_session.add_all([att1, att2, att3])
    
    # Events
    events = [
        # Att 1 (succeeded, live)
        ExecutionHistoryModel(attempt_id="d_att_1", listing_id="l_1", event_type="execution_started", dry_run=False, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_1", listing_id="l_1", event_type="execution_succeeded", dry_run=False, created_at=now),
        
        # Att 2 (failed, dry_run, alert created)
        ExecutionHistoryModel(attempt_id="d_att_2", listing_id="l_2", event_type="execution_started", dry_run=True, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_2", listing_id="l_2", event_type="execution_failed", error_code="ERR_T1", dry_run=True, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_2", listing_id="l_2", event_type="alert_created", details={"alert_level": "WARNING"}, dry_run=True, created_at=now),
        
        # Att 3 (failed, live, guard rejected, alert created)
        ExecutionHistoryModel(attempt_id="d_att_3", listing_id="l_3", event_type="guard_rejected", error_message="Limit Exceeded", dry_run=False, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_3", listing_id="l_3", event_type="execution_started", dry_run=False, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_3", listing_id="l_3", event_type="execution_failed", error_code="ERR_L1", dry_run=False, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_3", listing_id="l_3", event_type="alert_created", details={"alert_level": "CRITICAL"}, dry_run=False, created_at=now),
        ExecutionHistoryModel(attempt_id="d_att_3", listing_id="l_3", event_type="rollback_executed", dry_run=False, created_at=now),
    ]
    db_session.add_all(events)
    db_session.commit()
    return now

def test_dashboard_get_overview_summary(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    dr = (now - timedelta(days=1), now + timedelta(days=1))
    summary = dashboard_service.get_overview_summary(dr)
    
    assert summary.total_executions == 3
    assert summary.succeeded == 1
    assert summary.failed == 2
    assert summary.rolled_back == 1
    assert summary.alert_count == 2
    assert summary.dry_run_count == 1
    assert summary.live_count == 2

def test_dashboard_get_execution_counts(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    counts = dashboard_service.get_execution_counts((now - timedelta(days=1), now + timedelta(days=1)))
    assert counts.get("execution_started") == 3
    assert counts.get("execution_failed") == 2
    assert counts.get("guard_rejected") == 1

def test_dashboard_get_success_failure_ratio(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    s, f, rate = dashboard_service.get_success_failure_ratio((now - timedelta(days=1), now + timedelta(days=1)))
    assert s == 1
    assert f == 2
    assert abs(rate - 0.333) < 0.01

def test_dashboard_get_top_error_codes(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    top = dashboard_service.get_top_error_codes(limit=5, date_range=(now - timedelta(days=1), now + timedelta(days=1)))
    # ERR_T1 and ERR_L1, 1 each
    codes = {t[0]: t[1] for t in top}
    assert codes.get("ERR_T1") == 1
    assert codes.get("ERR_L1") == 1

def test_dashboard_get_top_failure_boundaries(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    top = dashboard_service.get_top_failure_boundaries(limit=5, date_range=(now - timedelta(days=1), now + timedelta(days=1)))
    boundaries = {t[0]: t[1] for t in top}
    assert boundaries.get("TIMEOUT") == 1
    assert boundaries.get("SELLER_LIMIT") == 1

def test_dashboard_get_alert_distribution(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    dist = dashboard_service.get_alert_distribution((now - timedelta(days=1), now + timedelta(days=1)))
    assert dist.get("WARNING") == 1
    assert dist.get("CRITICAL") == 1

def test_dashboard_get_dry_run_vs_live_split(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    split = dashboard_service.get_dry_run_vs_live_split((now - timedelta(days=1), now + timedelta(days=1)))
    assert split.get("dry_run") == 1
    assert split.get("live") == 2

def test_dashboard_get_seller_failure_analysis(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    rates = dashboard_service.get_seller_failure_analysis((now - timedelta(days=1), now + timedelta(days=1)))
    # S1 has 1 success, 1 failure => rate 0.5
    # S2 has 1 failure => rate 1.0
    assert abs(rates["S1"] - 0.5) < 0.01
    assert abs(rates["S2"] - 1.0) < 0.01

def test_dashboard_get_environment_failure_analysis(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    rates = dashboard_service.get_environment_failure_analysis((now - timedelta(days=1), now + timedelta(days=1)))
    # US has 1 success, 1 failure => 0.5
    # UK has 1 failure => 1.0
    assert abs(rates["US"] - 0.5) < 0.01
    assert abs(rates["UK"] - 1.0) < 0.01

def test_dashboard_get_recent_failures(dashboard_service, seed_dashboard_data):
    failures = dashboard_service.get_recent_failures(limit=10)
    assert len(failures) == 2
    assert all(f.event_type == "execution_failed" for f in failures)

def test_dashboard_get_recent_alerts(dashboard_service, seed_dashboard_data):
    alerts = dashboard_service.get_recent_alerts(limit=10)
    assert len(alerts) == 2
    assert all(a.event_type == "alert_created" for a in alerts)

def test_dashboard_get_state_transition_summary(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    summary = dashboard_service.get_state_transition_summary((now - timedelta(days=1), now + timedelta(days=1)))
    assert summary["started"] == 3
    assert summary["succeeded"] == 1
    assert summary["failed"] == 2
    assert summary["rolled_back"] == 1

def test_dashboard_get_guard_rejection_summary(dashboard_service, seed_dashboard_data):
    now = seed_dashboard_data
    summary = dashboard_service.get_guard_rejection_summary((now - timedelta(days=1), now + timedelta(days=1)))
    assert summary.get("Limit Exceeded") == 1

def test_dashboard_top_errors_no_date_range(dashboard_service, seed_dashboard_data):
    top = dashboard_service.get_top_error_codes()
    assert len(top) == 2

def test_dashboard_top_boundaries_no_date_range(dashboard_service, seed_dashboard_data):
    top = dashboard_service.get_top_failure_boundaries()
    assert len(top) == 2
