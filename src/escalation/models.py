from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class EscalationStep:
    step_index: int
    after_seconds: int
    min_repeat_count: int
    target_severity: str
    target_priority: str
    target_channels: List[str]
    cooldown_seconds: int = 0
    require_unacked: bool = False
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "after_seconds": self.after_seconds,
            "min_repeat_count": self.min_repeat_count,
            "target_severity": self.target_severity,
            "target_priority": self.target_priority,
            "target_channels": self.target_channels,
            "cooldown_seconds": self.cooldown_seconds,
            "require_unacked": self.require_unacked,
            "note": self.note
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscalationStep":
        return cls(
            step_index=data["step_index"],
            after_seconds=data["after_seconds"],
            min_repeat_count=data["min_repeat_count"],
            target_severity=data["target_severity"],
            target_priority=data["target_priority"],
            target_channels=data["target_channels"],
            cooldown_seconds=data.get("cooldown_seconds", 0),
            require_unacked=data.get("require_unacked", False),
            note=data.get("note")
        )

@dataclass
class EscalationPolicy:
    policy_id: str
    name: str
    enabled: bool
    seller_account_id: Optional[str]
    environment_type: Optional[str]
    event_type: str
    base_severity: str
    reminder_enabled: bool
    reminder_interval_seconds: int
    reminder_max_count: Optional[int]
    allow_reminder_after_ack: bool
    silence_respected: bool
    auto_resolve_on_source_recovery: bool
    escalation_enabled: bool
    escalation_steps: List[EscalationStep] = field(default_factory=list)
    dedupe_scope: str = "default"
    
    # v0.2 Extensions
    policy_version: int = 1
    re_escalation_enabled: bool = False
    re_escalation_interval_seconds: Optional[int] = None
    re_escalation_max_count: Optional[int] = None
    sla_target_seconds: Optional[int] = None
    sla_breach_severity: Optional[str] = None
    sla_breach_priority: Optional[str] = None
    maintenance_window_respected: bool = True
    bulk_action_enabled: bool = True
    route_override_key: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EscalationState:
    state_id: str
    source_event_id: str
    source_history_id: Optional[str]
    source_event_type: str
    seller_account_id: Optional[str]
    environment_type: Optional[str]
    sku: Optional[str]
    dedupe_key: str
    current_status: str
    current_severity: str
    current_priority: str
    reminder_count: int = 0
    escalation_level: int = 0
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)
    last_notified_at: Optional[datetime] = None
    last_reminded_at: Optional[datetime] = None
    last_escalated_at: Optional[datetime] = None
    acked_at: Optional[datetime] = None
    acked_by: Optional[str] = None
    silenced_until: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None
    source_status_snapshot: Dict[str, Any] = field(default_factory=dict)
    meta_json: Dict[str, Any] = field(default_factory=dict)
    
    # v0.2 Extensions
    aging_seconds: Optional[int] = None
    aging_bucket: Optional[str] = None
    sla_target_seconds: Optional[int] = None
    sla_breached_at: Optional[datetime] = None
    sla_breach_count: int = 0
    re_escalation_count: int = 0
    last_re_escalated_at: Optional[datetime] = None
    maintenance_suppressed_until: Optional[datetime] = None
    latest_note_at: Optional[datetime] = None
    latest_note_by: Optional[str] = None
    route_snapshot_json: Optional[Dict[str, Any]] = None
    incident_key: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EscalationStateTransition:
    transition_id: str
    state_id: str
    action_type: str
    previous_status: Optional[str]
    new_status: str
    actor_type: str
    actor_id: Optional[str]
    note: Optional[str] = None
    meta_json: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ReminderExecutionResult:
    state_id: str
    decision: str  # 'remind', 'skip', 'silenced', 'no_policy'
    dispatched_channels: List[str] = field(default_factory=list)
    skipped_reason: Optional[str] = None
    reminder_count_after: int = 0
    next_due_at: Optional[datetime] = None

@dataclass
class EscalationExecutionResult:
    state_id: str
    decision: str  # 'escalate', 'skip', 'no_policy'
    escalation_level_after: int = 0
    dispatched_channels: List[str] = field(default_factory=list)
    skipped_reason: Optional[str] = None
    next_due_at: Optional[datetime] = None

@dataclass
class EscalationBatchResult:
    run_id: str
    processed_count: int = 0
    reminder_sent_count: int = 0
    escalation_sent_count: int = 0
    skipped_count: int = 0
    resolved_count: int = 0
    silenced_count: int = 0
    acked_count: int = 0
    review_required_count: int = 0
    fatal_count: int = 0
    
    # v0.2 Extensions
    re_escalation_sent_count: int = 0
    breach_count: int = 0
    maintenance_suppressed_count: int = 0
    
    errors: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class EscalationNote:
    note_id: str
    state_id: str
    author_id: str
    author_type: str
    body: str
    is_internal: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MaintenanceWindow:
    window_id: str
    seller_account_id: Optional[str]
    environment_type: Optional[str]
    event_type: Optional[str]
    enabled: bool
    starts_at: datetime
    ends_at: datetime
    action: str = "suppress_all"
    reason: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EscalationTimelineItem:
    item_type: str # 'created', 'reminded', 'escalated', 're_escalated', 'acked', 'resolved', 'silenced', 'note', 'sla_breached', 'maintenance_suppressed'
    timestamp: datetime
    actor: str
    description: str
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EscalationStatsSnapshot:
    unresolved_total: int
    breached_total: int
    re_escalation_total: int
    aging_bucket_counts: Dict[str, int]
    seller_counts: Dict[str, int]
    environment_counts: Dict[str, int]
    event_type_counts: Dict[str, int]
    avg_time_to_ack_seconds: float
    avg_time_to_resolve_seconds: float
