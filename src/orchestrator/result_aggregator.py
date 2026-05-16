from typing import Any, Dict
from datetime import datetime
from .models import ScheduledJobResult, JobExecutionContext

class JobResultAggregator:
    def aggregate(self, job_name: str, context: JobExecutionContext, raw_result: Any) -> ScheduledJobResult:
        """
        Translates various pipeline results into a unified ScheduledJobResult.
        """
        res = ScheduledJobResult(
            job_name=job_name,
            run_id=getattr(raw_result, "run_id", "unknown"),
            scheduler_run_id=context.scheduler_run_id,
            started_at=context.requested_at,
            finished_at=datetime.now()
        )
        
        # Calculate duration
        res.duration_seconds = (res.finished_at - res.started_at).total_seconds()

        # Extract metrics if available
        # Most of our results are objects like ResearchBatchResult, ListingExecutionBatchResult, etc.
        if hasattr(raw_result, "processed_count"):
            res.processed_count = raw_result.processed_count
        if hasattr(raw_result, "success_count"):
            res.success_count = raw_result.success_count
        if hasattr(raw_result, "skipped_count"):
            res.skipped_count = raw_result.skipped_count
        if hasattr(raw_result, "review_count"):
            res.review_count = raw_result.review_count
        elif hasattr(raw_result, "review_required_count"):
            res.review_count = raw_result.review_required_count

        if hasattr(raw_result, "fatal_error_count"):
            res.fatal_error_count = raw_result.fatal_error_count
        if hasattr(raw_result, "retryable_error_count"):
            res.retryable_error_count = raw_result.retryable_error_count

        # Success flag
        if hasattr(raw_result, "success_flag"):
            res.success_flag = raw_result.success_flag
        else:
            # Fallback
            res.success_flag = (res.fatal_error_count == 0)

        res.status = "completed" if res.success_flag else "failed"
        
        return res
