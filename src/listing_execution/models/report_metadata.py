from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class ReportMetadata:
    report_id: str
    report_type: str
    format: str
    generated_at: datetime
    generated_by: str
    filter_snapshot: Dict[str, Any]
    row_count: int
    applied_filters: Dict[str, Any]
