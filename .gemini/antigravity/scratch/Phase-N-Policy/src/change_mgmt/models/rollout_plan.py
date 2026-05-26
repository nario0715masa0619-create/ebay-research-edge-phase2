from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

@dataclass
class RolloutPlan:
    rollout_plan_id: UUID
    change_proposal_id: UUID
    rollout_strategy: str
    rollout_scope: str
    activation_stage: int
    validation_window_minutes: int
    rollback_trigger_rules: Dict[str, Any]
    rollout_status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    rolled_back_at: Optional[datetime]
    created_at: datetime
