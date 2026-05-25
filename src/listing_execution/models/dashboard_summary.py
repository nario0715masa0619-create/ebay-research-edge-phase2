from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from src.listing_execution.models.history_query import HistoryEventView

@dataclass
class DashboardSummary:
    total_executions: int
    succeeded: int
    failed: int
    rolled_back: int
    alert_count: int
    success_rate: float
    failure_rate: float
    alert_level_distribution: Dict[str, int]
    top_error_codes: List[Tuple[str, int]]
    top_failure_boundaries: List[Tuple[str, int]]
    dry_run_count: int
    live_count: int
    seller_failure_rates: Dict[str, float]
    environment_failure_rates: Dict[str, float]
    guard_rejection_count: int
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DashboardCard:
    title: str
    metric_value: Any
    label: str
    badge: Optional[str] = None
    recent_events: List[HistoryEventView] = field(default_factory=list)
