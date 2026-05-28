import uuid
import datetime
from typing import Optional, List
from src.incident.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus, SlaState
from src.incident.models.incident_event import IncidentEvent, IncidentEventType
from src.incident.models.sla_policy import IncidentCandidate

class IncidentManagementService:
    def __init__(self, state_machine, sla_service, dedupe_service, linking_service, incident_repo, event_repo):
        self.state_machine = state_machine
        self.sla_service = sla_service
        self.dedupe_service = dedupe_service
        self.linking_service = linking_service
        self.incident_repo = incident_repo
        self.event_repo = event_repo

    def _create_event(self, incident_id: uuid.UUID, event_type: IncidentEventType, note: str, actor: str, from_status: Optional[IncidentStatus] = None, to_status: Optional[IncidentStatus] = None) -> IncidentEvent:
        event = IncidentEvent(
            event_id=uuid.uuid4(),
            incident_id=incident_id,
            event_type=event_type,
            note=note,
            actor_type="user" if actor != "system" else "system",
            actor_id=actor,
            from_status=from_status,
            to_status=to_status
        )
        if self.event_repo:
            self.event_repo.save_event(event)
        return event

    def create_incident_from_candidate(self, candidate: IncidentCandidate, actor: str, trigger_source: str) -> Incident:
        # 1. Map candidate to incident type (simplified logic here)
        inc_type = IncidentType.SYSTEM_ERROR
        if candidate.candidate_type.value == "high_error_rate":
            inc_type = IncidentType.LISTING_FAILURE

        # 2. Extract seller/env (simplified)
        seller = candidate.related_entity_ids[0] if candidate.related_entity_ids else None
        
        # 3. Dedupe check
        existing_id = self.dedupe_service.check_duplicate_exists(inc_type, seller, None, candidate.reason)
        if existing_id:
            self.dedupe_service.add_event_to_existing(existing_id, IncidentEventType.DUPLICATE_MARKED, {"reason": candidate.reason})
            return self.incident_repo.get_incident(existing_id) if self.incident_repo else None

        # 4. Create new incident
        incident = Incident(
            incident_id=uuid.uuid4(),
            incident_type=inc_type,
            severity=candidate.severity,
            title=f"Auto-generated from {candidate.candidate_type.value}",
            summary=candidate.reason,
            incident_status=IncidentStatus.OPEN,
            sla_state=SlaState.WITHIN_SLA,
            seller_account_id=seller,
            created_by=actor
        )
        
        self.state_machine.open(incident)
        
        # Calculate SLAs
        incident.ack_due_at, incident.resolve_due_at = self.sla_service.calculate_due_times(incident.opened_at, incident.severity)
        
        if self.incident_repo:
            self.incident_repo.save_incident(incident)
            
        self._create_event(incident.incident_id, IncidentEventType.CREATED, "Incident created from candidate", actor, None, IncidentStatus.OPEN)
        
        return incident

    def acknowledge_incident(self, incident_id: uuid.UUID, actor: str, note: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.acknowledge(incident, actor)
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.ACK, note, actor, from_status, incident.incident_status)
        return incident

    def assign_incident(self, incident_id: uuid.UUID, owner: str, actor: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        incident.assigned_to = owner
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.ASSIGNED, f"Assigned to {owner}", actor, incident.incident_status, incident.incident_status)
        return incident

    def start_investigation(self, incident_id: uuid.UUID, actor: str, note: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.investigate(incident, actor)
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.STATUS_CHANGED, note, actor, from_status, incident.incident_status)
        return incident

    def mitigate_incident(self, incident_id: uuid.UUID, actor: str, root_cause_code: str, note: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.mitigate(incident, actor, root_cause_code)
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.STATUS_CHANGED, note, actor, from_status, incident.incident_status)
        return incident

    def resolve_incident(self, incident_id: uuid.UUID, actor: str, note: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.resolve(incident, actor)
        
        # Evaluate SLA before resolving
        eval_result = self.sla_service.evaluate_sla_state(incident)
        if eval_result.sla_state in [SlaState.ACK_BREACHED, SlaState.RESOLVE_BREACHED, SlaState.BOTH_BREACHED]:
            self.sla_service.record_sla_breach_event(incident)

        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.RESOLVED, note, actor, from_status, incident.incident_status)
        return incident

    def close_incident(self, incident_id: uuid.UUID, actor: str, note: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.close(incident, actor)
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.CLOSED, note, actor, from_status, incident.incident_status)
        return incident

    def reopen_incident(self, incident_id: uuid.UUID, actor: str, reason: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.reopen(incident, actor, reason)
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.REOPENED, reason, actor, from_status, incident.incident_status)
        return incident

    def cancel_incident(self, incident_id: uuid.UUID, actor: str, reason: str) -> Incident:
        incident = self.incident_repo.get_incident(incident_id)
        from_status = incident.incident_status
        self.state_machine.cancel(incident, actor, reason)
        self.incident_repo.save_incident(incident)
        self._create_event(incident_id, IncidentEventType.STATUS_CHANGED, reason, actor, from_status, incident.incident_status)
        return incident
