import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
