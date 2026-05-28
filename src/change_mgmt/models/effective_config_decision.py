from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from src.change_mgmt.models.change_proposal import ChangeScopeType

@dataclass
class EffectiveConfigDecision:
    component_name: str
    scope_type: ChangeScopeType
    scope_target_id: Optional[str]
    effective_config_snapshot: Dict[str, Any]
    effective_config_version_id: UUID
    explanation_lines: List[str]
    evaluated_at: datetime
    has_pending_changes: bool
    next_scheduled_change_id: Optional[UUID]
