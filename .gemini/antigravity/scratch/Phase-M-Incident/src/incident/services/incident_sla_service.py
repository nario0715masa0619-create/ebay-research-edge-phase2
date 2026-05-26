import datetime
import uuid
from typing import Tuple, Optional
from src.incident.models.incident import Incident, IncidentSeverity, SlaState
from src.incident.models.sla_policy import SlaPolicy, SlaEvaluationResult
from src.incident.models.incident_event import IncidentEvent, IncidentEventType

class IncidentSlaService:
    def __init__(self):
        # Default SLA policies as per requirements/standard practices
        self.policies = {
            IncidentSeverity.CRITICAL: SlaPolicy(IncidentSeverity.CRITICAL, ack_deadline_hours=1, resolve_deadline_hours=4),
            IncidentSeverity.HIGH: SlaPolicy(IncidentSeverity.HIGH, ack_deadline_hours=4, resolve_deadline_hours=24),
            IncidentSeverity.MEDIUM: SlaPolicy(IncidentSeverity.MEDIUM, ack_deadline_hours=24, resolve_deadline_hours=72),
            IncidentSeverity.LOW: SlaPolicy(IncidentSeverity.LOW, ack_deadline_hours=72, resolve_deadline_hours=168), # 1 week
        }

    def get_sla_policy(self, severity: IncidentSeverity) -> SlaPolicy:
        return self.policies[severity]

    def calculate_due_times(self, opened_at: datetime.datetime, severity: IncidentSeverity) -> Tuple[datetime.datetime, datetime.datetime]:
        policy = self.get_sla_policy(severity)
        ack_due_at = opened_at + datetime.timedelta(hours=policy.ack_deadline_hours)
        resolve_due_at = opened_at + datetime.timedelta(hours=policy.resolve_deadline_hours)
        return ack_due_at, resolve_due_at

    def get_overdue_minutes(self, current_time: datetime.datetime, due_time: Optional[datetime.datetime]) -> Optional[int]:
        if not due_time:
            return None
        if current_time > due_time:
            delta = current_time - due_time
            return int(delta.total_seconds() // 60)
        return 0

    def check_ack_overdue(self, incident: Incident, current_time: Optional[datetime.datetime] = None) -> bool:
        if incident.acknowledged_at:
            return incident.acknowledged_at > incident.ack_due_at
        current_time = current_time or datetime.datetime.utcnow()
        return current_time > incident.ack_due_at

    def check_resolve_overdue(self, incident: Incident, current_time: Optional[datetime.datetime] = None) -> bool:
        if incident.resolved_at:
            return incident.resolved_at > incident.resolve_due_at
        current_time = current_time or datetime.datetime.utcnow()
        return current_time > incident.resolve_due_at

    def evaluate_sla_state(self, incident: Incident, current_time: Optional[datetime.datetime] = None) -> SlaEvaluationResult:
        current_time = current_time or datetime.datetime.utcnow()
        
        # Recalculate due times if they are missing (safety)
        if not incident.ack_due_at or not incident.resolve_due_at:
            incident.ack_due_at, incident.resolve_due_at = self.calculate_due_times(incident.opened_at, incident.severity)

        ack_overdue = self.check_ack_overdue(incident, current_time)
        resolve_overdue = self.check_resolve_overdue(incident, current_time)

        if ack_overdue and resolve_overdue:
            sla_state = SlaState.BOTH_BREACHED
        elif ack_overdue:
            sla_state = SlaState.ACK_BREACHED
        elif resolve_overdue:
            sla_state = SlaState.RESOLVE_BREACHED
        else:
            sla_state = SlaState.WITHIN_SLA
            
        incident.sla_state = sla_state

        eval_time_ack = incident.acknowledged_at or current_time
        eval_time_res = incident.resolved_at or current_time

        ack_overdue_mins = self.get_overdue_minutes(eval_time_ack, incident.ack_due_at)
        res_overdue_mins = self.get_overdue_minutes(eval_time_res, incident.resolve_due_at)

        return SlaEvaluationResult(
            incident_id=str(incident.incident_id),
            severity=incident.severity,
            opened_at=incident.opened_at,
            ack_due_at=incident.ack_due_at,
            resolve_due_at=incident.resolve_due_at,
            acknowledged_at=incident.acknowledged_at,
            resolved_at=incident.resolved_at,
            sla_state=sla_state,
            ack_overdue_minutes=ack_overdue_mins if ack_overdue else 0,
            resolve_overdue_minutes=res_overdue_mins if resolve_overdue else 0
        )

    def record_sla_breach_event(self, incident: Incident) -> IncidentEvent:
        return IncidentEvent(
            event_id=uuid.uuid4(),
            incident_id=incident.incident_id,
            event_type=IncidentEventType.SLA_BREACHED,
            note=f"SLA Breached. Current SLA State: {incident.sla_state.value}",
            actor_type="system",
            actor_id="sla_evaluator",
            from_status=incident.incident_status,
            to_status=incident.incident_status,
            details_json={"sla_state": incident.sla_state.value}
        )
