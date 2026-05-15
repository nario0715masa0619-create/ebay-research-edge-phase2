from typing import Optional, Dict, Any
from datetime import datetime
from src.ebay.models import JobRun

class JobRunRepository:
    def __init__(self):
        self._runs = {}  # {run_id: JobRun}

    def start_run(self, job_name: str, job_scope: str = "all", context: Dict[str, Any] = None) -> JobRun:
        import uuid
        run_id = str(uuid.uuid4())
        run = JobRun(
            run_id=run_id,
            job_name=job_name,
            job_scope=job_scope,
            context=context or {}
        )
        self._runs[run_id] = run
        return run

    def finish_run(self, run_id: str, status: str, metrics: Dict[str, int], error_summary: Optional[str] = None):
        run = self._runs.get(run_id)
        if run:
            run.status = status
            run.processed_count = metrics.get("processed_count", 0)
            run.success_count = metrics.get("success_count", 0)
            run.excluded_count = metrics.get("excluded_count", 0)
            run.review_count = metrics.get("review_count", 0)
            run.candidate_count = metrics.get("candidate_count", 0)
            run.ready_count = metrics.get("ready_count", 0)
            run.blocked_count = metrics.get("blocked_count", 0)
            run.skipped_count = metrics.get("skipped_count", 0)
            run.retryable_error_count = metrics.get("retryable_error_count", 0)
            run.review_required_count = metrics.get("review_required_count", 0)
            run.fatal_error_count = metrics.get("fatal_error_count", 0)
            run.keep_count = metrics.get("keep_count", 0)
            run.revised_count = metrics.get("revised_count", 0)
            run.zeroed_count = metrics.get("zeroed_count", 0)
            run.withdrawn_count = metrics.get("withdrawn_count", 0)
            run.error_count = metrics.get("error_count", 0)
            run.error_summary = error_summary
            run.finished_at = datetime.now()

    def append_progress(self, run_id: str, delta_metrics: Dict[str, int]):
        run = self._runs.get(run_id)
        if run:
            run.processed_count += delta_metrics.get("processed_count", 0)
            run.success_count += delta_metrics.get("success_count", 0)
            run.excluded_count += delta_metrics.get("excluded_count", 0)
            run.review_count += delta_metrics.get("review_count", 0)
            run.candidate_count += delta_metrics.get("candidate_count", 0)
            run.ready_count += delta_metrics.get("ready_count", 0)
            run.blocked_count += delta_metrics.get("blocked_count", 0)
            run.skipped_count += delta_metrics.get("skipped_count", 0)
            run.retryable_error_count += delta_metrics.get("retryable_error_count", 0)
            run.review_required_count += delta_metrics.get("review_required_count", 0)
            run.fatal_error_count += delta_metrics.get("fatal_error_count", 0)
            run.keep_count += delta_metrics.get("keep_count", 0)
            run.revised_count += delta_metrics.get("revised_count", 0)
            run.zeroed_count += delta_metrics.get("zeroed_count", 0)
            run.withdrawn_count += delta_metrics.get("withdrawn_count", 0)
            run.error_count += delta_metrics.get("error_count", 0)

    def get_run(self, run_id: str) -> Optional[JobRun]:
        return self._runs.get(run_id)
