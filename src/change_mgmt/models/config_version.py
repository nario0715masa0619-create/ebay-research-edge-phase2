from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from src.change_mgmt.models.change_proposal import ChangeScopeType

@dataclass
class ConfigVersion:
    config_version_id: UUID
    component_name: str
    scope_type: ChangeScopeType
    scope_target_id: Optional[str]
    version_number: int
    config_snapshot: Dict[str, Any]
    derived_from_change_proposal_id: Optional[UUID]
    effective_from: datetime
    effective_until: Optional[datetime]
    is_active: bool
    supersedes_config_version_id: Optional[UUID]
    created_by: str
    created_at: datetime
