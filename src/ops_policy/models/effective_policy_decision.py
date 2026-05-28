from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from src.ops_policy.models.enums import ScopeType

@dataclass
class EffectivePolicyDecision:
    """有効なポリシー決定"""
    policy_id: UUID
    scope_type: ScopeType
    target_id: Optional[str]
    live_execution_allowed: bool
    force_dry_run: bool
    handoff_paused: bool
    retry_allowed: bool
    concurrency_limit: Optional[int]
    seller_throughput_limit: Optional[float]
    require_manual_review: bool
    block_listing_creation: bool
    environment_safe_mode: bool
    operator_attention: bool
    reason_summary: str
    contributing_policies: List[UUID]
    evaluated_at: datetime
