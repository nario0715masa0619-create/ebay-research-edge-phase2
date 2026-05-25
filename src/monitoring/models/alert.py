from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import uuid

class AlertLevel(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class Alert:
    listing_id: str
    attempt_id: str
    failure_boundary: str
    alert_level: AlertLevel
    message: str
    reason: str
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    alert_sent_at: Optional[datetime] = None
