import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.config import DatabaseConfig

@pytest.fixture(autouse=True)
def disable_foreign_keys():
    original = DatabaseConfig.DB_ENABLE_FOREIGN_KEYS
    DatabaseConfig.DB_ENABLE_FOREIGN_KEYS = False
    yield
    DatabaseConfig.DB_ENABLE_FOREIGN_KEYS = original

from src.db.models import Base
from src.listing_execution.services.application_service import ExecutionApplicationService
from src.listing_execution.gateways.execution_gateway import ExecutionResult, ValidationResult
from src.listing_execution.executors.mock_executor import MockExecutor
from src.listing_readiness.services.readiness_checker import ReadinessChecker, ReadinessResult
from src.listing_execution.repositories.execution_attempt_repository import ExecutionAttemptRepository
from src.listing_execution.models.execution_payload import ExecutionPayload

@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def repo(session):
    return ExecutionAttemptRepository(session)

@pytest.fixture
def app_service(repo):
    gateway = MockExecutor(
        allowed_environments=["sandbox", "production"], 
        allowed_sellers=["seller_A", "seller_B"], 
        fixture_rules={
            "sku_success": "success",
            "sku_timeout": "timeout",
            "sku_limit": "seller_limit"
        }
    )
    readiness_checker = ReadinessChecker()
    return ExecutionApplicationService(
        gateway=gateway,
        readiness_checker=readiness_checker,
        repository=repo
    )

@pytest.fixture
def valid_payload():
    return ExecutionPayload(
        attempt_id="att_001",
        listing_id="lst_001",
        seller="seller_A",
        sku="sku_success",
        bundle_state="none",
        market_eval={},
        profitability_score=100.0,
        environment="sandbox",
        dry_run=False
    )

@pytest.fixture
def candidate_data():
    return {"title": "Test Item", "price": 100, "sku": "sku_success", "profitability_score": 100.0}

@pytest.fixture
def seller_data():
    return {"is_active": True}

@pytest.fixture
def handoff_data():
    return {"handoff_status": "ready"}

def test_app_service_readiness(app_service):
    res = app_service.check_readiness({"title": "A", "price": 100, "sku": "sku_success", "profitability_score": 100.0}, {"is_active": True}, {"handoff_status": "ready"})
    assert res.is_ready is True
    assert res.readiness_score == 100.0

def test_app_service_execute_success(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    result = app_service.execute_listing(valid_payload, candidate_data, seller_data, handoff_data)
    
    assert result["status"] == "success"
    assert result["state"] == "executed"
    
    db_attempt = repo.get_by_id("att_001")
    assert db_attempt is not None
    assert db_attempt.status == "executed"

def test_app_service_execute_readiness_rejected(app_service, valid_payload, repo, seller_data, handoff_data):
    # Missing required data makes readiness score drop below 80
    invalid_candidate = {}
    result = app_service.execute_listing(valid_payload, invalid_candidate, seller_data, handoff_data)
    
    assert result["status"] == "rejected"
    assert "error_reason" in result
    
    # DB attempt should NOT be created since it was rejected before initiation
    db_attempt = repo.get_by_id("att_001")
    assert db_attempt is None

def test_app_service_execute_guard_rejected(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.seller = "invalid_seller"
    result = app_service.execute_listing(valid_payload, candidate_data, seller_data, handoff_data)
    
    assert result["status"] == "failed"
    assert result["action"] == "CANCEL"
    assert "Validation Failed" in result["retry_decision"]
    
    db_attempt = repo.get_by_id("att_001")
    assert db_attempt is not None
    assert db_attempt.status == "failed"

def test_app_service_execute_timeout_retryable(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.sku = "sku_timeout"
    result = app_service.execute_listing(valid_payload, candidate_data, seller_data, handoff_data)
    
    assert result["status"] == "failed"
    assert result["action"] == "RETRY_LATER"
    assert result["next_attempt_number"] == 2
    
    db_attempt = repo.get_by_id("att_001")
    # Timeout is retryable, so the ExecutionScope is rolled_back to allow retry safely
    assert db_attempt.status == "rolled_back"
    assert db_attempt.failure_boundary == "TIMEOUT"

def test_app_service_execute_seller_limit_defers(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.sku = "sku_limit"
    result = app_service.execute_listing(valid_payload, candidate_data, seller_data, handoff_data)
    
    assert result["status"] == "failed"
    assert result["action"] == "DEFER"
    
    db_attempt = repo.get_by_id("att_001")
    assert db_attempt.status == "rolled_back"
    assert db_attempt.failure_boundary == "SELLER_LIMIT"

def test_app_service_dry_run_no_side_effects(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.dry_run = True
    result = app_service.execute_listing(valid_payload, candidate_data, seller_data, handoff_data)
    
    assert result["status"] == "success"
    
    # In dry run, it shouldn't persist to the repository
    db_attempt = repo.get_by_id("att_001")
    assert db_attempt is None

def test_app_service_manual_rollback(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    app_service.execute_listing(valid_payload, candidate_data, seller_data, handoff_data)
    
    res = app_service.rollback_execution("att_001", "User testing rollback")
    assert res["status"] == "rolled_back"
    
    db_attempt = repo.get_by_id("att_001")
    assert db_attempt.status == "rolled_back"
    assert "User testing rollback" in db_attempt.error_message

def test_execute_with_live_gateway_dry_run_uses_mock(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.dry_run = True
    valid_payload.sku = "sku_success"
    
    result = app_service.execute_with_live_gateway(
        payload=valid_payload, 
        credentials=None,
        candidate_data=candidate_data, 
        seller_data=seller_data, 
        handoff_data=handoff_data
    )
    print("DEBUG result: ", result)
    assert result["status"] == "success"
    assert result["dry_run"] is True
    
    # DB unchanged
    assert repo.get_by_id("att_001") is None
    
    # Audit log from sync service / monitor
    assert len(app_service.monitor._audit_logs) == 0  # No alert generated on success

def test_execute_with_live_gateway_live_no_credentials_fails(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.dry_run = False
    
    result = app_service.execute_with_live_gateway(
        payload=valid_payload, 
        credentials=None,
        candidate_data=candidate_data, 
        seller_data=seller_data, 
        handoff_data=handoff_data
    )
    
    assert result["status"] == "failed"
    assert result["action"] == "CANCEL"
    assert "Missing credentials" in result["error_reason"]

def test_execute_with_live_gateway_sync_conflict(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.dry_run = False
    valid_payload.sku = "sku_success"
    
    # Create fake active listing to cause conflict when success mock returns!
    from src.listing_sync.models.listing_state import ListingState
    # Let's mock the sync service to raise an exception
    import pytest
    def mock_sync(*args, **kwargs):
        raise Exception("StateConflictError: listing already active")
    app_service.sync_service.sync_execution_to_listing = mock_sync
    
    result = app_service.execute_with_live_gateway(
        payload=valid_payload, 
        credentials={"auth_token": "foo"},
        candidate_data=candidate_data, 
        seller_data=seller_data, 
        handoff_data=handoff_data
    )
    
    assert result["status"] == "failed"
    assert "StateConflictError" in result["error_reason"]
    
    # Monitor should have logged this!
    assert len(app_service.monitor._audit_logs) >= 1
    assert app_service.monitor._audit_logs[0]["alert_level"] == "CRITICAL"

def test_execute_with_live_gateway_failure_monitor_alerts(app_service, valid_payload, repo, candidate_data, seller_data, handoff_data):
    valid_payload.dry_run = False
    valid_payload.sku = "sku_timeout" # Will use MockExecutor to fail with timeout
    
    # In live flow, unless dry_run, it uses LiveExecutor if credentials are provided
    # Let's mock LiveExecutor.execute
    from unittest.mock import patch
    with patch("src.listing_execution.executors.live_executor.LiveExecutor.execute") as mock_exec:
        from src.listing_execution.gateways.execution_gateway import ExecutionResult
        mock_exec.return_value = ExecutionResult(
            status="failed", listing_id="lst_001", attempt_id="att_001",
            error_reason="Connection Timeout", executed_at=datetime.now(timezone.utc)
        )
        # Also need to mock validate
        with patch("src.listing_execution.executors.live_executor.LiveExecutor.validate") as mock_val:
            from src.listing_execution.gateways.execution_gateway import ValidationResult
            mock_val.return_value = ValidationResult(is_valid=True, error_messages=[])

            result = app_service.execute_with_live_gateway(
                payload=valid_payload, 
                credentials={"auth_token": "foo"},
                candidate_data=candidate_data, 
                seller_data=seller_data, 
                handoff_data=handoff_data
            )
            
            assert result["status"] == "failed"
            # Connection Timeout gets UNKNOWN boundary if not parsed, let's see
            # alert history
            assert len(app_service.monitor._audit_logs) >= 1
