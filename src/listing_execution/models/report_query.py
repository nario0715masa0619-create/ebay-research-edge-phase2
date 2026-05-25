from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ReportFilter:
    """フィルタ条件の汎用表現（スナップショット用）"""
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReportQuery:
    report_type: str
    seller_account_id: Optional[str] = None
    environment: Optional[str] = None
    listing_id: Optional[str] = None
    attempt_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    group_by: Optional[str] = None
