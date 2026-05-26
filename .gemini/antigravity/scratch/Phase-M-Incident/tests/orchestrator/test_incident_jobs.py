import pytest
import uuid
import datetime
from src.orchestrator.incident_jobs import incident_detection_job, incident_sla_evaluation_job, incident_overdue_digest_job
from src.incident.models.sla_policy import IncidentCandidate, IncidentCandidateType
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState

class MockDetectionService:
    def detect_from_alert_burst(self):
        return [
            IncidentCandidate(IncidentCandidateType.SYSTEM_DOWN, IncidentSeverity.CRITICAL, ["a1"], 1.0, "reason1")
        ]

class MockStateMachine:
    def to_status(self, inc, status):
        pass

class MockManagementService:
    def __init__(self):
        self._state_machine = MockStateMachine()
        self.created = []

    def create_incident_from_candidate(self, candidate, actor, trigger_source):
        inc = Incident(
            incident_id=uuid.uuid4(),
            incident_type=IncidentType.SYSTEM_ERROR,
            severity=candidate.severity,
            title="Test", summary="Test",
            incident_status=IncidentStatus.OPEN,
            sla_state=SlaState.WITHIN_SLA,
            seller_account_id=None,
            environment=None
        )
        self.created.append(inc)
        return inc

class MockIncidentRepo:
    def __init__(self, incs):
        self.incs = incs
        self.updates = []

    def get_open_incidents(self):
        return self.incs

    def update_incident(self, uid, updates):
        self.updates.append((uid, updates))

class MockSlaService:
    def evaluate_sla_state(self, incident):
        if incident.incident_status == IncidentStatus.OPEN:
            incident.sla_state = SlaState.ACK_BREACHED
            return True
        return False

class MockDigestReport:
    def __init__(self, period):
        self.period = period

class MockDigestService:
    def generate_overdue_digest(self, current_time):
        return MockDigestReport("Daily")

def test_incident_detection_job():
    ds = MockDetectionService()
    ms = MockManagementService()
    res = incident_detection_job(ds, ms)
    assert len(res) == 1
    assert len(ms.created) == 1

def test_incident_sla_evaluation_job():
    inc1 = Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=IncidentSeverity.CRITICAL,
        title="Test", summary="Test",
        incident_status=IncidentStatus.OPEN,
        sla_state=SlaState.WITHIN_SLA,
        seller_account_id=None,
        environment=None
    )
    repo = MockIncidentRepo([inc1])
    ms = MockManagementService()
    sla = MockSlaService()
    
    breached_count = incident_sla_evaluation_job(ms, repo, sla)
    assert breached_count == 1
    assert len(repo.updates) == 1
    assert repo.updates[0][1]['sla_state'] == SlaState.ACK_BREACHED

def test_incident_overdue_digest_job():
    ds = MockDigestService()
    report = incident_overdue_digest_job(ds)
    assert report.period == "Daily"
