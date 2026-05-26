from dataclasses import dataclass, field
import datetime
import uuid
from enum import Enum

class IncidentLinkEntityType(str, Enum):
    ATTEMPT = "attempt"
    LISTING = "listing"
    ALERT = "alert"
    REPORT = "report"
    SELLER = "seller"
    ENVIRONMENT = "environment"

@dataclass
class IncidentLink:
    link_id: uuid.UUID
    incident_id: uuid.UUID
    entity_type: IncidentLinkEntityType
    entity_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
