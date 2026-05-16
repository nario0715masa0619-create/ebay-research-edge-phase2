from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class JobDefinition:
    job_name: str
    job_group: str = "default"
    enabled: bool = True
    schedule_type: str = "manual_only" # interval, cron, manual_only, startup_once
    cron_expr: Optional[str] = None
    interval_seconds: Optional[int] = None
    run_on_startup: bool = False
    max_concurrency: int = 1
    allow_overlap: bool = False
    depends_on: List[str] = field(default_factory=list)
    retry_policy_name: str = "standard"
    timeout_seconds: int = 3600
    default_limit: Optional[int] = None
    default_kwargs: Dict[str, Any] = field(default_factory=dict)
    target_runner_name: str = ""
    lock_key: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class JobExecutionContext:
    scheduler_run_id: str
    job_name: str
    trigger_type: str = "scheduled" # scheduled, manual, retry
    manual_triggered_by: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    dry_run: bool = False
    force_recheck: bool = False
    limit: Optional[int] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

@dataclass
class ScheduledJobResult:
    job_name: str
    run_id: str
    scheduler_run_id: str
    status: str = "pending" # pending, running, completed, skipped, failed, timed_out
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    processed_count: int = 0
    success_count: int = 0
    skipped_count: int = 0
    review_count: int = 0
    retryable_error_count: int = 0
    fatal_error_count: int = 0
    downstream_triggered_jobs: List[str] = field(default_factory=list)
    error_summary: Optional[str] = None
    success_flag: bool = False

@dataclass
class SchedulerCycleResult:
    cycle_id: str
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    scheduled_job_count: int = 0
    executed_job_count: int = 0
    skipped_job_count: int = 0
    failed_job_count: int = 0
    results: List[ScheduledJobResult] = field(default_factory=list)
    success_flag: bool = True
