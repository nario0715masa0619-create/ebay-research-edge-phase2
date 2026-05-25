from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
from datetime import datetime

@dataclass
class SellerHealthReport:
    seller_id: str
    date_range: Tuple[str, str]
    execution_volume: int
    failure_rate: float
    guard_rejection_count: int
    retry_rollback_count: int
    major_error_patterns: List[Tuple[str, int]]
    generated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class EnvironmentHealthReport:
    environment: str
    date_range: Tuple[str, str]
    execution_volume: int
    failure_rate: float
    guard_rejection_count: int
    alert_concentration: Dict[str, int]
    dry_run_ratio: float
    generated_at: datetime = field(default_factory=datetime.utcnow)
