from typing import List, Tuple
from src.incident.models.incident import Incident, IncidentStatus
import datetime

class InvalidStateTransitionError(Exception):
    pass

class IncidentStateMachine:
    def __init__(self):
        # Maps from_status -> list of allowed to_status
        self.allowed_transitions = {
            IncidentStatus.OPEN: [IncidentStatus.ACKNOWLEDGED, IncidentStatus.CLOSED, IncidentStatus.CANCELLED],
            IncidentStatus.ACKNOWLEDGED: [IncidentStatus.INVESTIGATING, IncidentStatus.MITIGATED, IncidentStatus.RESOLVED, IncidentStatus.CANCELLED],
            IncidentStatus.INVESTIGATING: [IncidentStatus.MITIGATED, IncidentStatus.RESOLVED, IncidentStatus.CANCELLED],
            IncidentStatus.MITIGATED: [IncidentStatus.RESOLVED, IncidentStatus.INVESTIGATING, IncidentStatus.CANCELLED],
            IncidentStatus.RESOLVED: [IncidentStatus.CLOSED, IncidentStatus.OPEN], # OPEN for reopen
            IncidentStatus.CLOSED: [],
            IncidentStatus.CANCELLED: []
        }

    def validate_transition(self, from_status: IncidentStatus, to_status: IncidentStatus) -> bool:
        allowed = self.allowed_transitions.get(from_status, [])
        return to_status in allowed

    def get_allowed_transitions(self, current_status: IncidentStatus) -> List[IncidentStatus]:
        return self.allowed_transitions.get(current_status, [])

    def _transition(self, incident: Incident, to_status: IncidentStatus, actor: str, **kwargs):
        if not self.validate_transition(incident.incident_status, to_status):
            raise InvalidStateTransitionError(f"Cannot transition from {incident.incident_status} to {to_status}")
        incident.incident_status = to_status
        # In a real system, we'd also record an IncidentEvent here. For now, the service manages state updates.

    def open(self, incident: Incident):
        # Setting initial state
        incident.incident_status = IncidentStatus.OPEN
        incident.opened_at = datetime.datetime.utcnow()

    def acknowledge(self, incident: Incident, actor: str):
        self._transition(incident, IncidentStatus.ACKNOWLEDGED, actor)
        incident.acknowledged_at = datetime.datetime.utcnow()

    def investigate(self, incident: Incident, actor: str):
        self._transition(incident, IncidentStatus.INVESTIGATING, actor)

    def mitigate(self, incident: Incident, actor: str, root_cause_code: str = None):
        self._transition(incident, IncidentStatus.MITIGATED, actor)
        if root_cause_code:
            incident.root_cause_code = root_cause_code

    def resolve(self, incident: Incident, actor: str):
        self._transition(incident, IncidentStatus.RESOLVED, actor)
        incident.resolved_at = datetime.datetime.utcnow()

    def close(self, incident: Incident, actor: str):
        self._transition(incident, IncidentStatus.CLOSED, actor)
        incident.closed_at = datetime.datetime.utcnow()

    def cancel(self, incident: Incident, actor: str, reason: str):
        self._transition(incident, IncidentStatus.CANCELLED, actor)
        incident.closed_at = datetime.datetime.utcnow()

    def reopen(self, incident: Incident, actor: str, reason: str):
        if incident.incident_status != IncidentStatus.RESOLVED:
            raise InvalidStateTransitionError("Can only reopen from RESOLVED status")
        self._transition(incident, IncidentStatus.OPEN, actor)
        incident.is_reopened = True
        # Clear timestamps that indicate resolution
        incident.resolved_at = None
