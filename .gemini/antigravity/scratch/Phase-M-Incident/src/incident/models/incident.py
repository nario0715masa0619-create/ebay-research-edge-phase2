from dataclasses import dataclass, field
from typing import Optional, List
import datetime
from enum import Enum
import uuid

class IncidentType(str, Enum):
    LISTING_FAILURE = "listing_failure"
    ALERT = "alert"
    SYSTEM_ERROR = "system_error"
    SELLER_ISSUE = "seller_issue"

class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IncidentStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class SlaState(str, Enum):
    WITHIN_SLA = "within_sla"
    ACK_BREACHED = "ack_breached"
    RESOLVE_BREACHED = "resolve_breached"
    BOTH_BREACHED = "both_breached"

@dataclass
class Incident:
    incident_id: uuid.UUID
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str
    summary: str
    incident_status: IncidentStatus
    sla_state: SlaState
    seller_account_id: Optional[str] = None
    environment: Optional[str] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    opened_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    ack_due_at: Optional[datetime.datetime] = None
    resolve_due_at: Optional[datetime.datetime] = None
    acknowledged_at: Optional[datetime.datetime] = None
    resolved_at: Optional[datetime.datetime] = None
    closed_at: Optional[datetime.datetime] = None
    duplicate_of_incident_id: Optional[uuid.UUID] = None
    root_cause_code: Optional[str] = None
    is_reopened: bool = False
