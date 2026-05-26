import pytest
import uuid
from src.incident.services.incident_deduplication_service import IncidentDeduplicationService
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.models.incident_event import IncidentEvent, IncidentEventType

class MockIncidentRepo:
    def __init__(self, incidents):
        self.incidents = incidents
    def get_recent_incidents(self, since):
        return self.incidents

class MockEventRepo:
    def __init__(self):
        self.events = []
    def save_event(self, event):
        self.events.append(event)

def make_incident(status, inc_type, seller, env, err):
    inc = Incident(
        incident_id=uuid.uuid4(),
        incident_type=inc_type,
        severity=IncidentSeverity.HIGH,
        title="Test",
        summary="Test",
        incident_status=status,
        sla_state=SlaState.WITHIN_SLA,
        seller_account_id=seller,
        environment=env
    )
    inc.root_cause_code = err
    return inc

# 14. Dedupe candidate check
def test_is_dedupe_candidate():
    svc = IncidentDeduplicationService()
    assert svc.is_dedupe_candidate(make_incident(IncidentStatus.OPEN, IncidentType.SYSTEM_ERROR, None, None, None))
    assert svc.is_dedupe_candidate(make_incident(IncidentStatus.ACKNOWLEDGED, IncidentType.SYSTEM_ERROR, None, None, None))
    assert not svc.is_dedupe_candidate(make_incident(IncidentStatus.CLOSED, IncidentType.SYSTEM_ERROR, None, None, None))
    assert not svc.is_dedupe_candidate(make_incident(IncidentStatus.RESOLVED, IncidentType.SYSTEM_ERROR, None, None, None))

# 15. check_duplicate_exists finds match
def test_check_duplicate_exists_found():
    inc1 = make_incident(IncidentStatus.OPEN, IncidentType.LISTING_FAILURE, "s1", "env1", "err1")
    repo = MockIncidentRepo([inc1])
    svc = IncidentDeduplicationService(repo)
    dup_id = svc.check_duplicate_exists(IncidentType.LISTING_FAILURE, "s1", "env1", "err1")
    assert dup_id == inc1.incident_id

# 16. check_duplicate_exists no match due to different error
def test_check_duplicate_exists_no_match_error():
    inc1 = make_incident(IncidentStatus.OPEN, IncidentType.LISTING_FAILURE, "s1", "env1", "err1")
    repo = MockIncidentRepo([inc1])
    svc = IncidentDeduplicationService(repo)
    dup_id = svc.check_duplicate_exists(IncidentType.LISTING_FAILURE, "s1", "env1", "err2")
    assert dup_id is None

# 17. mark_as_duplicate
def test_mark_as_duplicate():
    svc = IncidentDeduplicationService()
    new_inc = make_incident(IncidentStatus.OPEN, IncidentType.LISTING_FAILURE, "s1", "env1", "err1")
    dup_id = uuid.uuid4()
    svc.mark_as_duplicate(new_inc, dup_id)
    assert new_inc.incident_status == IncidentStatus.CANCELLED
    assert new_inc.duplicate_of_incident_id == dup_id
    assert new_inc.closed_at is not None

# 18. add_event_to_existing
def test_add_event_to_existing():
    ev_repo = MockEventRepo()
    svc = IncidentDeduplicationService(event_repo=ev_repo)
    inc_id = uuid.uuid4()
    res = svc.add_event_to_existing(inc_id, IncidentEventType.DUPLICATE_MARKED, {"foo": "bar"})
    assert res is True
    assert len(ev_repo.events) == 1
    assert ev_repo.events[0].incident_id == inc_id
    assert ev_repo.events[0].details_json == {"foo": "bar"}
