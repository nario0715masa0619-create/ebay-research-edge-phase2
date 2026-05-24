import pytest
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.db.models import Base, ExecutionAttemptModel
from src.listing_execution.repositories.execution_attempt_repository import ExecutionAttemptRepository

@pytest.fixture(scope="function")
def session():
    """Provides a clean in-memory SQLite session for testing"""
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
def valid_attempt_data():
    return {
        "attempt_id": "att_001",
        "listing_id": "lst_001",
        "seller_account_id": "seller_A",
        "environment": "sandbox",
        "status": "pending",
        "payload_json": {"test": "data"}
    }

def test_create_attempt(repo, valid_attempt_data):
    model = repo.create_attempt(valid_attempt_data)
    assert model.attempt_id == "att_001"
    assert model.status == "pending"
    assert json.loads(model.payload_json) == {"test": "data"}
    assert model.created_at is not None

def test_get_by_id(repo, valid_attempt_data):
    repo.create_attempt(valid_attempt_data)
    model = repo.get_by_id("att_001")
    assert model is not None
    assert model.listing_id == "lst_001"

def test_get_by_id_not_found(repo):
    assert repo.get_by_id("non_existent") is None

def test_get_by_listing_id(repo, valid_attempt_data):
    repo.create_attempt(valid_attempt_data)
    
    # Create second attempt for same listing
    valid_attempt_data["attempt_id"] = "att_002"
    repo.create_attempt(valid_attempt_data)
    
    # Create attempt for different listing
    valid_attempt_data["attempt_id"] = "att_003"
    valid_attempt_data["listing_id"] = "lst_002"
    repo.create_attempt(valid_attempt_data)
    
    attempts = repo.get_by_listing_id("lst_001")
    assert len(attempts) == 2
    assert attempts[0].attempt_id == "att_001"
    assert attempts[1].attempt_id == "att_002"

def test_attempt_id_unique_constraint(repo, valid_attempt_data, session):
    repo.create_attempt(valid_attempt_data)
    
    with pytest.raises(IntegrityError):
        # Attempt to create with same attempt_id
        valid_attempt_data["listing_id"] = "another_listing"
        repo.create_attempt(valid_attempt_data)

def test_update_status(repo, valid_attempt_data):
    repo.create_attempt(valid_attempt_data)
    
    now = datetime.now(timezone.utc)
    updated = repo.update_status(
        attempt_id="att_001",
        status="failed",
        error_code="ERR123",
        error_message="Test Error",
        failure_boundary="TIMEOUT",
        finished_at=now
    )
    
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_code == "ERR123"
    assert updated.error_message == "Test Error"
    assert updated.failure_boundary == "TIMEOUT"
    assert updated.finished_at.replace(tzinfo=timezone.utc) == now

def test_update_status_not_found(repo):
    updated = repo.update_status("non_existent", "failed")
    assert updated is None

def test_payload_saving_as_text(repo, valid_attempt_data):
    # Test saving raw text instead of dict
    valid_attempt_data["payload_json"] = '{"raw": "string"}'
    model = repo.create_attempt(valid_attempt_data)
    assert model.payload_json == '{"raw": "string"}'

def test_optional_fields(repo):
    data = {
        "attempt_id": "att_min",
        "listing_id": "lst_min",
        "seller_account_id": "sel_min",
        "environment": "prod"
    }
    model = repo.create_attempt(data)
    # Check defaults applied by python/SQLAlchemy layer
    assert model.status == "pending"
    assert model.retry_count == 0
    assert model.payload_json is None
    assert model.error_code is None

def test_multiple_attempts_same_listing(repo, valid_attempt_data):
    repo.create_attempt(valid_attempt_data)
    
    att2_data = valid_attempt_data.copy()
    att2_data["attempt_id"] = "att_002"
    att2_data["retry_count"] = 1
    
    repo.create_attempt(att2_data)
    
    lst = repo.get_by_listing_id("lst_001")
    assert len(lst) == 2
    assert lst[1].retry_count == 1

def test_sqlite_repository_compatibility(repo, valid_attempt_data):
    # Just validating the standard operations complete without dialect errors
    repo.create_attempt(valid_attempt_data)
    repo.update_status("att_001", "executed")
    res = repo.get_by_listing_id("lst_001")
    assert len(res) == 1
    assert res[0].status == "executed"
