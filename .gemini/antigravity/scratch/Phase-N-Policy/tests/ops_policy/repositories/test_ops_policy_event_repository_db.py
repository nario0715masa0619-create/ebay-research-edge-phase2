import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, OpsPolicyModel
from src.ops_policy.models.ops_policy_event import OpsPolicyEvent
from src.ops_policy.models.enums import EventType, PolicyStatus
from src.ops_policy.repositories.ops_policy_event_repository_db import OpsPolicyEventRepository

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def repo(session):
    return OpsPolicyEventRepository(session)

def _create_parent_policy(session, pid):
    p = OpsPolicyModel(
        policy_id=pid,
        scope_type="global",
        target_id=None,
        action_type="pause_handoff",
        level="strong",
        status="proposed",
        title="Test",
        reason_summary="R",
        created_by="u",
        priority=50,
        metadata_json={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(p)
    session.commit()

def _create_dummy_event(pid, eid=None, event_type=EventType.CREATED):
    return OpsPolicyEvent(
        event_id=eid or uuid4(),
        policy_id=pid,
        event_type=event_type,
        from_status=None,
        to_status=PolicyStatus.PROPOSED,
        actor_type="user",
        actor_id="u",
        note="Test event",
        details_json={},
        created_at=datetime.utcnow()
    )

def test_create_event_and_retrieve(session, repo):
    pid = uuid4()
    _create_parent_policy(session, pid)
    
    e = _create_dummy_event(pid)
    repo.create_event(e)
    
    events = repo.get_events_by_policy(pid)
    assert len(events) == 1
    assert events[0].event_id == e.event_id

def test_get_events_by_policy_order(session, repo):
    pid = uuid4()
    _create_parent_policy(session, pid)
    
    e1 = _create_dummy_event(pid)
    e1.created_at = datetime.utcnow() - timedelta(days=1)
    
    e2 = _create_dummy_event(pid)
    e2.created_at = datetime.utcnow()
    
    repo.create_event(e2) # insert out of order
    repo.create_event(e1)
    
    events = repo.get_events_by_policy(pid)
    assert len(events) == 2
    assert events[0].event_id == e1.event_id # Older first

def test_list_all_events_order_desc(session, repo):
    pid = uuid4()
    _create_parent_policy(session, pid)
    
    e1 = _create_dummy_event(pid)
    e1.created_at = datetime.utcnow() - timedelta(days=1)
    
    e2 = _create_dummy_event(pid)
    e2.created_at = datetime.utcnow()
    
    repo.create_event(e1)
    repo.create_event(e2)
    
    events, total = repo.list_all_events()
    assert total == 2
    assert events[0].event_id == e2.event_id # Newer first

def test_count_events_by_type(session, repo):
    pid = uuid4()
    _create_parent_policy(session, pid)
    
    repo.create_event(_create_dummy_event(pid, event_type=EventType.CREATED))
    repo.create_event(_create_dummy_event(pid, event_type=EventType.PROPOSED))
    repo.create_event(_create_dummy_event(pid, event_type=EventType.PROPOSED))
    
    counts = repo.count_events_by_type()
    assert counts.get(EventType.CREATED) == 1
    assert counts.get(EventType.PROPOSED) == 2
