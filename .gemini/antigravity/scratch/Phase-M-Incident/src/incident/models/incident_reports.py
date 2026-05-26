from dataclasses import dataclass, field
from typing import Dict, List, Any
import datetime

@dataclass
class IncidentSummary:
    total_open: int = 0
    total_ack: int = 0
    total_investigating: int = 0
    total_resolved: int = 0
    total_closed: int = 0
    total_cancelled: int = 0
    open_count: int = 0
    overdue_count: int = 0
    breached_count: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_seller: Dict[str, int] = field(default_factory=dict)
    by_environment: Dict[str, int] = field(default_factory=dict)
    mean_ack_time_hours: float = 0.0
    mean_resolve_time_hours: float = 0.0

@dataclass
class IncidentDigestReport:
    period: str
    report_type: str
    incident_count: int = 0
    open_count: int = 0
    resolved_count: int = 0
    closed_count: int = 0
    overdue_count: int = 0
    breached_count: int = 0
    top_issues: Dict[str, Any] = field(default_factory=dict)
    recent_incidents: List[Any] = field(default_factory=list)
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
