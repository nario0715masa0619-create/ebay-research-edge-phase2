import pytest
import uuid
import datetime
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.services.incident_state_machine import IncidentStateMachine, InvalidStateTransitionError

@pytest.fixture
def machine():
    return IncidentStateMachine()

@pytest.fixture
def new_incident():
    return Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=IncidentSeverity.HIGH,
        title="Test Incident",
        summary="Test",
        incident_status=IncidentStatus.OPEN,
        sla_state=SlaState.WITHIN_SLA
    )

# 1. Open sets status to OPEN
def test_open_incident(machine, new_incident):
    machine.open(new_incident)
    assert new_incident.incident_status == IncidentStatus.OPEN
    assert new_incident.opened_at is not None

# 2. Open to Ack success
def test_open_to_ack(machine, new_incident):
    machine.open(new_incident)
    machine.acknowledge(new_incident, "actor1")
    assert new_incident.incident_status == IncidentStatus.ACKNOWLEDGED
    assert new_incident.acknowledged_at is not None

# 3. Ack to Investigating success
def test_ack_to_investigating(machine, new_incident):
    machine.open(new_incident)
    machine.acknowledge(new_incident, "actor1")
    machine.investigate(new_incident, "actor1")
    assert new_incident.incident_status == IncidentStatus.INVESTIGATING

# 4. Investigating to Mitigated
def test_investigating_to_mitigated(machine, new_incident):
    new_incident.incident_status = IncidentStatus.INVESTIGATING
    machine.mitigate(new_incident, "actor1", "RC1")
    assert new_incident.incident_status == IncidentStatus.MITIGATED
    assert new_incident.root_cause_code == "RC1"

# 5. Mitigated to Resolved
def test_mitigated_to_resolved(machine, new_incident):
    new_incident.incident_status = IncidentStatus.MITIGATED
    machine.resolve(new_incident, "actor1")
    assert new_incident.incident_status == IncidentStatus.RESOLVED
    assert new_incident.resolved_at is not None

# 6. Resolved to Closed
def test_resolved_to_closed(machine, new_incident):
    new_incident.incident_status = IncidentStatus.RESOLVED
    machine.close(new_incident, "actor1")
    assert new_incident.incident_status == IncidentStatus.CLOSED
    assert new_incident.closed_at is not None

# 7. Cancel from Open
def test_cancel_from_open(machine, new_incident):
    machine.open(new_incident)
    machine.cancel(new_incident, "actor1", "duplicate")
    assert new_incident.incident_status == IncidentStatus.CANCELLED
    assert new_incident.closed_at is not None

# 8. Invalid transition: Open to Resolved
def test_invalid_open_to_resolved(machine, new_incident):
    machine.open(new_incident)
    with pytest.raises(InvalidStateTransitionError):
        machine.resolve(new_incident, "actor1")

# 9. Invalid transition: Closed to Ack
def test_invalid_closed_to_ack(machine, new_incident):
    new_incident.incident_status = IncidentStatus.CLOSED
    with pytest.raises(InvalidStateTransitionError):
        machine.acknowledge(new_incident, "actor1")

# 10. Reopen from Resolved success
def test_reopen_from_resolved(machine, new_incident):
    new_incident.incident_status = IncidentStatus.RESOLVED
    new_incident.resolved_at = datetime.datetime.utcnow()
    machine.reopen(new_incident, "actor1", "issue persists")
    assert new_incident.incident_status == IncidentStatus.OPEN
    assert new_incident.is_reopened is True
    assert new_incident.resolved_at is None

# 11. Reopen from Closed should fail
def test_reopen_from_closed(machine, new_incident):
    new_incident.incident_status = IncidentStatus.CLOSED
    with pytest.raises(InvalidStateTransitionError):
        machine.reopen(new_incident, "actor1", "issue persists")

# 12. Validate transition helper true
def test_validate_transition_true(machine):
    assert machine.validate_transition(IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED) is True

# 13. Validate transition helper false
def test_validate_transition_false(machine):
    assert machine.validate_transition(IncidentStatus.OPEN, IncidentStatus.RESOLVED) is False

# 14. Get allowed transitions
def test_get_allowed_transitions(machine):
    allowed = machine.get_allowed_transitions(IncidentStatus.OPEN)
    assert set(allowed) == {IncidentStatus.ACKNOWLEDGED, IncidentStatus.CLOSED, IncidentStatus.CANCELLED}

# 15. Mitigated to Investigating (rollback)
def test_mitigated_to_investigating(machine, new_incident):
    new_incident.incident_status = IncidentStatus.MITIGATED
    machine.investigate(new_incident, "actor1")
    assert new_incident.incident_status == IncidentStatus.INVESTIGATING
