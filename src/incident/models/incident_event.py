from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import datetime
import uuid
from enum import Enum
from src.incident.models.incident import IncidentStatus

class IncidentEventType(str, Enum):
    CREATED = "created"
    ACK = "ack"
    ASSIGNED = "assigned"
    ESCALATED = "escalated"
    SEVERITY_CHANGED = "severity_changed"
    NOTE_ADDED = "note_added"
    STATUS_CHANGED = "status_changed"
    LINKED_ENTITY_ADDED = "linked_entity_added"
    DUPLICATE_MARKED = "duplicate_marked"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    SLA_BREACHED = "sla_breached"

@dataclass
class IncidentEvent:
    event_id: uuid.UUID
    incident_id: uuid.UUID
    event_type: IncidentEventType
    note: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    from_status: Optional[IncidentStatus] = None
    to_status: Optional[IncidentStatus] = None
    details_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
