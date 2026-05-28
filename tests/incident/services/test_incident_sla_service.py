import pytest
import uuid
import datetime
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.services.incident_sla_service import IncidentSlaService
from src.incident.models.incident_event import IncidentEventType

@pytest.fixture
def service():
    return IncidentSlaService()

@pytest.fixture
def incident():
    return Incident(
        incident_id=uuid.uuid4(),
        incident_type=IncidentType.SYSTEM_ERROR,
        severity=IncidentSeverity.HIGH,
        title="SLA Test Incident",
        summary="Test",
        incident_status=IncidentStatus.OPEN,
        sla_state=SlaState.WITHIN_SLA,
        opened_at=datetime.datetime(2023, 1, 1, 12, 0, 0)
    )

# 16. Test get_sla_policy default values
def test_get_sla_policy_critical(service):
    policy = service.get_sla_policy(IncidentSeverity.CRITICAL)
    assert policy.ack_deadline_hours == 1
    assert policy.resolve_deadline_hours == 4

# 17. Test calculate_due_times HIGH severity (4h ack, 24h resolve)
def test_calculate_due_times(service, incident):
    ack_due, res_due = service.calculate_due_times(incident.opened_at, incident.severity)
    assert ack_due == datetime.datetime(2023, 1, 1, 16, 0, 0)
    assert res_due == datetime.datetime(2023, 1, 2, 12, 0, 0)

# 18. Test check_ack_overdue returns False when within time
def test_check_ack_overdue_false(service, incident):
    incident.ack_due_at = datetime.datetime(2023, 1, 1, 16, 0, 0)
    # Check at 15:00
    current_time = datetime.datetime(2023, 1, 1, 15, 0, 0)
    assert service.check_ack_overdue(incident, current_time) is False

# 19. Test check_ack_overdue returns True when overdue
def test_check_ack_overdue_true(service, incident):
    incident.ack_due_at = datetime.datetime(2023, 1, 1, 16, 0, 0)
    # Check at 17:00
    current_time = datetime.datetime(2023, 1, 1, 17, 0, 0)
    assert service.check_ack_overdue(incident, current_time) is True

# 20. Test check_resolve_overdue returns False
def test_check_resolve_overdue_false(service, incident):
    incident.resolve_due_at = datetime.datetime(2023, 1, 2, 12, 0, 0)
    current_time = datetime.datetime(2023, 1, 2, 11, 0, 0)
    assert service.check_resolve_overdue(incident, current_time) is False

# 21. Test check_resolve_overdue returns True
def test_check_resolve_overdue_true(service, incident):
    incident.resolve_due_at = datetime.datetime(2023, 1, 2, 12, 0, 0)
    current_time = datetime.datetime(2023, 1, 2, 13, 0, 0)
    assert service.check_resolve_overdue(incident, current_time) is True

# 22. Test get_overdue_minutes exact
def test_get_overdue_minutes(service):
    due_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    current_time = datetime.datetime(2023, 1, 1, 12, 30, 0)
    assert service.get_overdue_minutes(current_time, due_time) == 30

# 23. Test evaluate_sla_state within SLA
def test_evaluate_sla_state_within(service, incident):
    current_time = datetime.datetime(2023, 1, 1, 13, 0, 0)
    res = service.evaluate_sla_state(incident, current_time)
    assert res.sla_state == SlaState.WITHIN_SLA
    assert incident.sla_state == SlaState.WITHIN_SLA

# 24. Test evaluate_sla_state both breached
def test_evaluate_sla_state_both_breached(service, incident):
    current_time = datetime.datetime(2023, 1, 3, 12, 0, 0) # Past both deadlines
    res = service.evaluate_sla_state(incident, current_time)
    assert res.sla_state == SlaState.BOTH_BREACHED
    assert res.ack_overdue_minutes > 0
    assert res.resolve_overdue_minutes > 0

# 25. Test record_sla_breach_event
def test_record_sla_breach_event(service, incident):
    incident.sla_state = SlaState.ACK_BREACHED
    event = service.record_sla_breach_event(incident)
    assert event.event_type == IncidentEventType.SLA_BREACHED
    assert event.incident_id == incident.incident_id
    assert "ack_breached" in event.note

# 26. Test evaluate calculates due times if missing
def test_evaluate_calculates_missing_due_times(service, incident):
    incident.ack_due_at = None
    incident.resolve_due_at = None
    res = service.evaluate_sla_state(incident, datetime.datetime(2023, 1, 1, 13, 0, 0))
    assert res.ack_due_at is not None
    assert incident.ack_due_at is not None

# 27. Test get_overdue_minutes not overdue returns 0
def test_get_overdue_minutes_not_overdue(service):
    due_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    current_time = datetime.datetime(2023, 1, 1, 11, 30, 0)
    assert service.get_overdue_minutes(current_time, due_time) == 0
