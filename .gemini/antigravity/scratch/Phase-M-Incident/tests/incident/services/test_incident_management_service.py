import pytest
import uuid
from src.incident.services.incident_management_service import IncidentManagementService
from src.incident.services.incident_state_machine import IncidentStateMachine
from src.incident.services.incident_sla_service import IncidentSlaService
from src.incident.services.incident_deduplication_service import IncidentDeduplicationService
from src.incident.services.incident_linking_service import IncidentLinkingService
from src.incident.models.sla_policy import IncidentCandidate, IncidentCandidateType
from src.incident.models.incident import Incident, IncidentSeverity, IncidentStatus, IncidentType, SlaState

class MockIncidentRepo:
    def __init__(self):
        self.incidents = {}
    def save_incident(self, incident):
        self.incidents[incident.incident_id] = incident
    def get_incident(self, incident_id):
        return self.incidents[incident_id]

class MockEventRepo:
    def __init__(self):
        self.events = []
    def save_event(self, event):
        self.events.append(event)

@pytest.fixture
def service():
    sm = IncidentStateMachine()
    sla = IncidentSlaService()
    dedupe = IncidentDeduplicationService()
    linking = IncidentLinkingService()
    irepo = MockIncidentRepo()
    erepo = MockEventRepo()
    return IncidentManagementService(sm, sla, dedupe, linking, irepo, erepo)

# 1. create_incident_from_candidate success
def test_create_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    assert inc is not None
    assert inc.incident_status == IncidentStatus.OPEN
    assert inc.severity == IncidentSeverity.CRITICAL
    assert service.event_repo.events[0].actor_id == "system"

# 2. create_incident dedupe
def test_create_incident_dedupe(service, monkeypatch):
    existing_id = uuid.uuid4()
    # add existing to repo so get_incident doesn't fail
    service.incident_repo.incidents[existing_id] = Incident(existing_id, IncidentType.SYSTEM_ERROR, IncidentSeverity.CRITICAL, "t", "s", IncidentStatus.OPEN, SlaState.WITHIN_SLA)
    monkeypatch.setattr(service.dedupe_service, "check_duplicate_exists", lambda *args, **kwargs: existing_id)
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    assert inc is not None
    assert inc.incident_id == existing_id

# 3. acknowledge_incident
def test_acknowledge_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    inc2 = service.acknowledge_incident(inc.incident_id, "user1", "ack note")
    assert inc2.incident_status == IncidentStatus.ACKNOWLEDGED
    assert inc2.acknowledged_at is not None

# 4. assign_incident
def test_assign_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    inc2 = service.assign_incident(inc.incident_id, "owner1", "user1")
    assert inc2.assigned_to == "owner1"

# 5. start_investigation
def test_start_investigation(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    service.acknowledge_incident(inc.incident_id, "user1", "")
    inc2 = service.start_investigation(inc.incident_id, "user1", "")
    assert inc2.incident_status == IncidentStatus.INVESTIGATING

# 6. mitigate_incident
def test_mitigate_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    service.acknowledge_incident(inc.incident_id, "user1", "")
    service.start_investigation(inc.incident_id, "user1", "")
    inc2 = service.mitigate_incident(inc.incident_id, "user1", "RC1", "mitigated")
    assert inc2.incident_status == IncidentStatus.MITIGATED
    assert inc2.root_cause_code == "RC1"

# 7. resolve_incident
def test_resolve_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    service.acknowledge_incident(inc.incident_id, "user1", "")
    service.start_investigation(inc.incident_id, "user1", "")
    inc2 = service.resolve_incident(inc.incident_id, "user1", "resolved")
    assert inc2.incident_status == IncidentStatus.RESOLVED

# 8. close_incident
def test_close_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    service.acknowledge_incident(inc.incident_id, "user1", "")
    service.start_investigation(inc.incident_id, "user1", "")
    service.resolve_incident(inc.incident_id, "user1", "resolved")
    inc2 = service.close_incident(inc.incident_id, "user1", "closed")
    assert inc2.incident_status == IncidentStatus.CLOSED

# 9. reopen_incident
def test_reopen_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    service.acknowledge_incident(inc.incident_id, "user1", "")
    service.resolve_incident(inc.incident_id, "user1", "resolved")
    inc2 = service.reopen_incident(inc.incident_id, "user1", "reopen")
    assert inc2.incident_status == IncidentStatus.OPEN
    assert inc2.is_reopened is True

# 10. cancel_incident
def test_cancel_incident(service):
    cand = IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["seller1"], 1.0, "reason")
    inc = service.create_incident_from_candidate(cand, "system", "auto")
    inc2 = service.cancel_incident(inc.incident_id, "user1", "duplicate")
    assert inc2.incident_status == IncidentStatus.CANCELLED
