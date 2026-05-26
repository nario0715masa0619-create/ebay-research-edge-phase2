from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from src.ops_policy.models.enums import EventType, PolicyStatus

@dataclass
class OpsPolicyEvent:
    """ポリシーイベント（監査ログ）"""
    event_id: UUID
    policy_id: UUID
    event_type: EventType
    from_status: Optional[PolicyStatus]
    to_status: PolicyStatus
    actor_type: str
    actor_id: str
    note: str
    details_json: Dict[str, Any]
    created_at: datetime
