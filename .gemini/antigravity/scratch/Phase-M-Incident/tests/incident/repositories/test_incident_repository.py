import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.incident.models.orm_models import Base, IncidentModel, IncidentEventModel, IncidentLinkModel
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.models.incident_event import IncidentEvent, IncidentEventType
from src.incident.models.incident_link import IncidentLink, IncidentLinkEntityType
from src.incident.repositories.incident_repository_db import IncidentRepositoryDB
from src.incident.repositories.incident_event_repository import IncidentEventRepositoryDB
from src.incident.repositories.incident_link_repository import IncidentLinkRepositoryDB

@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def session(engine, tables):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def repo(session):
    return IncidentRepositoryDB(session)

@pytest.fixture
def event_repo(session):
    return IncidentEventRepositoryDB(session)

@pytest.fixture
def link_repo(session):
    return IncidentLinkRepositoryDB(session)

def make_inc():
    inc = Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=IncidentSeverity.CRITICAL,
        title="DB Test",
        summary="DB Summary",
        incident_status=IncidentStatus.OPEN,
        sla_state=SlaState.WITHIN_SLA,
        seller_account_id="s1",
        environment="prod"
    )
    inc.opened_at = datetime.datetime.utcnow()
    inc.ack_due_at = inc.opened_at + datetime.timedelta(hours=1)
    inc.resolve_due_at = inc.opened_at + datetime.timedelta(hours=4)
    return inc

# --- IncidentRepositoryDB Tests (15 tests) ---

def test_create_incident(repo):
    inc = make_inc()
    uid = repo.create_incident(inc)
    assert uid == inc.incident_id

def test_get_incident_by_id(repo):
    inc = make_inc()
    repo.create_incident(inc)
    fetched = repo.get_incident_by_id(inc.incident_id)
    assert fetched.incident_id == inc.incident_id
    assert fetched.title == "DB Test"

def test_get_incident_not_found(repo):
    with pytest.raises(KeyError):
        repo.get_incident_by_id(uuid.uuid4())

def test_update_incident(repo):
    inc = make_inc()
    repo.create_incident(inc)
    repo.update_incident(inc.incident_id, {"title": "Updated Title", "incident_status": IncidentStatus.ACKNOWLEDGED})
    fetched = repo.get_incident_by_id(inc.incident_id)
    assert fetched.title == "Updated Title"
    assert fetched.incident_status == IncidentStatus.ACKNOWLEDGED

def test_list_incidents_no_filter(repo):
    inc1 = make_inc()
    inc2 = make_inc()
    repo.create_incident(inc1)
    repo.create_incident(inc2)
    incs = repo.list_incidents()
    assert len(incs) >= 2

def test_list_incidents_filter_status(repo):
    inc = make_inc()
    inc.incident_status = IncidentStatus.CLOSED
    repo.create_incident(inc)
    incs = repo.list_incidents(filters={"status": IncidentStatus.CLOSED})
    assert len(incs) >= 1
    assert incs[0].incident_status == IncidentStatus.CLOSED

def test_list_incidents_filter_severity(repo):
    inc = make_inc()
    inc.severity = IncidentSeverity.LOW
    repo.create_incident(inc)
    incs = repo.list_incidents(filters={"severity": IncidentSeverity.LOW})
    assert len(incs) >= 1
    assert incs[0].severity == IncidentSeverity.LOW

def test_list_incidents_filter_seller(repo):
    inc = make_inc()
    inc.seller_account_id = "unique_s_2"
    repo.create_incident(inc)
    incs = repo.list_incidents(filters={"seller_account_id": "unique_s_2"})
    assert len(incs) == 1

def test_list_incidents_filter_env(repo):
    inc = make_inc()
    inc.environment = "sandbox"
    repo.create_incident(inc)
    incs = repo.list_incidents(filters={"environment": "sandbox"})
    assert len(incs) == 1

def test_get_open_incidents(repo):
    inc = make_inc()
    repo.create_incident(inc)
    open_incs = repo.get_open_incidents()
    assert len(open_incs) >= 1

def test_get_overdue_incidents(repo):
    inc = make_inc()
    # Make it overdue
    inc.ack_due_at = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    repo.create_incident(inc)
    overdue = repo.get_overdue_incidents()
    # It should be in overdue since ack_due_at < now and acknowledged_at is None
    assert any(i.incident_id == inc.incident_id for i in overdue)

def test_get_breached_incidents(repo):
    inc = make_inc()
    inc.sla_state = SlaState.BOTH_BREACHED
    repo.create_incident(inc)
    breached = repo.get_breached_incidents()
    assert any(i.incident_id == inc.incident_id for i in breached)

def test_query_by_seller(repo):
    inc = make_inc()
    inc.seller_account_id = "query_sell"
    repo.create_incident(inc)
    res = repo.query_by_seller("query_sell")
    assert len(res) == 1

def test_query_by_environment(repo):
    inc = make_inc()
    inc.environment = "query_env"
    repo.create_incident(inc)
    res = repo.query_by_environment("query_env")
    assert len(res) == 1

def test_query_by_status(repo):
    inc = make_inc()
    inc.incident_status = IncidentStatus.CANCELLED
    repo.create_incident(inc)
    res = repo.query_by_status(IncidentStatus.CANCELLED)
    assert len(res) >= 1

# --- IncidentEventRepositoryDB Tests (5 tests) ---

def test_create_event(repo, event_repo):
    inc = make_inc()
    repo.create_incident(inc)
    
    ev = IncidentEvent(
        event_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        event_type=IncidentEventType.CREATED,
        note="test note",
        actor_type="system",
        actor_id="sys1",
        created_at=datetime.datetime.utcnow()
    )
    uid = event_repo.create_event(ev)
    assert uid == ev.event_id

def test_get_events_by_incident(repo, event_repo):
    inc = make_inc()
    repo.create_incident(inc)
    ev = IncidentEvent(
        event_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        event_type=IncidentEventType.CREATED,
        actor_type="system",
        actor_id="sys1",
        created_at=datetime.datetime.utcnow()
    )
    event_repo.create_event(ev)
    events = event_repo.get_events_by_incident(inc.incident_id)
    assert len(events) == 1
    assert events[0].event_id == ev.event_id

def test_get_events_empty(event_repo):
    events = event_repo.get_events_by_incident(uuid.uuid4())
    assert len(events) == 0

def test_list_all_events_asc(repo, event_repo):
    inc = make_inc()
    repo.create_incident(inc)
    ev = IncidentEvent(
        event_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        event_type=IncidentEventType.CREATED,
        actor_type="system",
        actor_id="sys1",
        created_at=datetime.datetime.utcnow()
    )
    event_repo.create_event(ev)
    all_evs = event_repo.list_all_events(sort='ASC')
    assert len(all_evs) >= 1

def test_list_all_events_desc(repo, event_repo):
    inc = make_inc()
    repo.create_incident(inc)
    ev = IncidentEvent(
        event_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        event_type=IncidentEventType.CREATED,
        actor_type="system",
        actor_id="sys1",
        created_at=datetime.datetime.utcnow()
    )
    event_repo.create_event(ev)
    all_evs = event_repo.list_all_events(sort='DESC')
    assert len(all_evs) >= 1

# --- IncidentLinkRepositoryDB Tests (5 tests) ---

def test_create_link(repo, link_repo):
    inc = make_inc()
    repo.create_incident(inc)
    lk = IncidentLink(
        link_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        entity_type=IncidentLinkEntityType.SELLER,
        entity_id="s123",
        created_at=datetime.datetime.utcnow()
    )
    uid = link_repo.create_link(lk)
    assert uid == lk.link_id

def test_get_links_by_incident(repo, link_repo):
    inc = make_inc()
    repo.create_incident(inc)
    lk = IncidentLink(
        link_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        entity_type=IncidentLinkEntityType.SELLER,
        entity_id="s123",
        created_at=datetime.datetime.utcnow()
    )
    link_repo.create_link(lk)
    links = link_repo.get_links_by_incident(inc.incident_id)
    assert len(links) == 1

def test_get_links_by_entity(repo, link_repo):
    inc = make_inc()
    repo.create_incident(inc)
    lk = IncidentLink(
        link_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        entity_type=IncidentLinkEntityType.ALERT,
        entity_id="a999",
        created_at=datetime.datetime.utcnow()
    )
    link_repo.create_link(lk)
    links = link_repo.get_links_by_entity(IncidentLinkEntityType.ALERT, "a999")
    assert len(links) == 1
    assert links[0].incident_id == inc.incident_id

def test_get_links_empty(link_repo):
    links = link_repo.get_links_by_entity(IncidentLinkEntityType.REPORT, "none")
    assert len(links) == 0

def test_delete_link(repo, link_repo):
    inc = make_inc()
    repo.create_incident(inc)
    lk = IncidentLink(
        link_id=uuid.uuid4(),
        incident_id=inc.incident_id,
        entity_type=IncidentLinkEntityType.SELLER,
        entity_id="s123",
        created_at=datetime.datetime.utcnow()
    )
    link_repo.create_link(lk)
    link_repo.delete_link(lk.link_id)
    links = link_repo.get_links_by_incident(inc.incident_id)
    assert len(links) == 0
