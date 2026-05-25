from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

@dataclass
class HistoryQuery:
    attempt_id: Optional[str] = None
    listing_id: Optional[str] = None
    seller_account_id: Optional[str] = None
    environment: Optional[str] = None
    event_type: Optional[str] = None
    status: Optional[str] = None
    dry_run: Optional[bool] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    limit: int = 50
    offset: int = 0

@dataclass
class HistoryEventView:
    event_id: str
    attempt_id: str
    listing_id: str
    event_type: str
    dry_run: bool
    from_state: Optional[str]
    to_state: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: str
