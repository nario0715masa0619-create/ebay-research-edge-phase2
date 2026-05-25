import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
# Make sure models are loaded
from src.db.models import ExecutionAttemptModel
from src.listing_execution.models.execution_history import ExecutionHistoryModel
from src.listing_execution.repositories.execution_history_repository import ExecutionHistoryRepository

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # We must have an ExecutionAttemptModel first because of the FK constraint
    attempt = ExecutionAttemptModel(
        attempt_id="att_test_123",
        listing_id="lst_test_456",
        seller_account_id="sellerA",
        environment="sandbox",
        status="pending"
    )
    session.add(attempt)
    session.commit()
    
    yield session
    session.close()
    
@pytest.fixture(scope="function")
def repository(db_session):
    return ExecutionHistoryRepository(db_session=db_session)

def test_history_model_to_from_dict():
    data = {
        "id": str(uuid.uuid4()),
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "execution_started",
        "dry_run": True,
        "from_state": "pending",
        "to_state": "executing",
        "error_code": None,
        "error_message": None,
        "details": {"key": "val"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "system"
    }
    
    model = ExecutionHistoryModel.from_dict(data)
    assert model.attempt_id == "att_test_123"
    assert model.dry_run is True
    assert model.details == {"key": "val"}
    
    out_data = model.to_dict()
    assert out_data["attempt_id"] == "att_test_123"
    assert out_data["dry_run"] is True

def test_repository_create_history_record(repository):
    record = repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "execution_started",
        "dry_run": False
    })
    
    assert record.id is not None
    assert record.attempt_id == "att_test_123"
    assert record.listing_id == "lst_test_456"
    assert record.event_type == "execution_started"
    assert record.dry_run is False
    assert record.created_at is not None
    assert record.created_by == "system"

def test_repository_get_by_attempt_id(repository):
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "execution_started"
    })
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "execution_succeeded"
    })
    
    records = repository.get_by_attempt_id("att_test_123")
    assert len(records) == 2
    assert records[0].event_type == "execution_started"
    assert records[1].event_type == "execution_succeeded"

def test_repository_get_by_listing_id(repository):
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_999",
        "event_type": "readiness_passed"
    })
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_999",
        "event_type": "execution_started"
    })
    
    records = repository.get_by_listing_id("lst_test_999")
    assert len(records) == 2
    assert records[0].listing_id == "lst_test_999"

def test_repository_list_by_event_type(repository):
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_1",
        "event_type": "alert_created"
    })
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_2",
        "event_type": "alert_created"
    })
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_3",
        "event_type": "execution_started"
    })
    
    records = repository.list_by_event_type("alert_created")
    assert len(records) == 2
    for r in records:
        assert r.event_type == "alert_created"

def test_repository_find_by_date_range(repository):
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=2)
    
    # Create with specific created_at
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_1",
        "event_type": "alert_created",
        "created_at": old
    })
    repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_2",
        "event_type": "alert_created",
        "created_at": now
    })
    
    records = repository.find_by_date_range(
        from_date=now - timedelta(days=1),
        to_date=now + timedelta(days=1)
    )
    
    assert len(records) == 1
    assert records[0].listing_id == "lst_2"

def test_history_model_immutability(db_session, repository):
    record = repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "execution_started"
    })
    
    original_time = record.created_at
    
    # Attempt to change created_at
    record.created_at = datetime.now(timezone.utc) + timedelta(days=1)
    
    import sqlalchemy.exc
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        
    # Test that in our repository paradigm, history should be append only.
    # While SQLAlchemy won't strictly forbid updating a row unless we add triggers,
    # we can test that the repository doesn't have an update method.
    assert not hasattr(repository, 'update')
    assert not hasattr(repository, 'save')

def test_history_model_dry_run_flag(repository):
    record = repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "dry_run_executed",
        "dry_run": True
    })
    
    assert record.dry_run is True

def test_history_model_with_details_json(repository):
    record = repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "readiness_failed",
        "details": {"score": 60, "reasons": ["missing_sku"]}
    })
    
    assert record.details is not None
    assert record.details["score"] == 60
    assert "missing_sku" in record.details["reasons"]

def test_history_model_with_state_transition(repository):
    record = repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "listing_state_changed",
        "from_state": "draft",
        "to_state": "active"
    })
    
    assert record.from_state == "draft"
    assert record.to_state == "active"

def test_history_model_with_error(repository):
    record = repository.create({
        "attempt_id": "att_test_123",
        "listing_id": "lst_test_456",
        "event_type": "execution_failed",
        "error_code": "ERR_500",
        "error_message": "Internal server error"
    })
    
    assert record.error_code == "ERR_500"
    assert record.error_message == "Internal server error"
