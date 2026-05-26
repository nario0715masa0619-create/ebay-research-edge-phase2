from dataclasses import dataclass
from typing import Optional, List
import datetime
from enum import Enum
from src.incident.models.incident import IncidentSeverity, SlaState

@dataclass
class SlaPolicy:
    severity: IncidentSeverity
    ack_deadline_hours: int
    resolve_deadline_hours: int

@dataclass
class SlaEvaluationResult:
    incident_id: str
    severity: IncidentSeverity
    opened_at: datetime.datetime
    ack_due_at: Optional[datetime.datetime]
    resolve_due_at: Optional[datetime.datetime]
    acknowledged_at: Optional[datetime.datetime]
    resolved_at: Optional[datetime.datetime]
    sla_state: SlaState
    ack_overdue_minutes: Optional[int] = None
    resolve_overdue_minutes: Optional[int] = None

class IncidentCandidateType(str, Enum):
    HIGH_ERROR_RATE = "high_error_rate"
    SYSTEM_DOWN = "system_down"
    SLA_BREACH = "sla_breach"

@dataclass
class IncidentCandidate:
    candidate_type: IncidentCandidateType
    severity: IncidentSeverity
    related_entity_ids: List[str]
    confidence_score: float
    reason: str
