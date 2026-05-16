from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.ebay.models import JobRun
from src.db.models import JobRunModel
from datetime import datetime

class PersistentJobRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def start_run(self, job_name: str, job_scope: str = "all", context: Dict[str, Any] = None) -> JobRun:
        import uuid
        run_id = str(uuid.uuid4())
        run = JobRun(run_id=run_id, job_name=job_name, job_scope=job_scope)
        model = JobRunModel(
            run_id=run.run_id,
            job_name=run.job_name,
            job_scope=run.job_scope,
            status=run.status,
            started_at=run.started_at,
            context_json=context
        )
        self.session.add(model)
        return run

    def append_progress(self, run_id: str, metrics: Dict[str, Any]):
        stmt = update(JobRunModel).where(JobRunModel.run_id == run_id).values(
            processed_count=JobRunModel.processed_count + metrics.get("processed_count", 0),
            success_count=JobRunModel.success_count + metrics.get("success_count", 0),
            excluded_count=JobRunModel.excluded_count + metrics.get("excluded_count", 0),
            review_count=JobRunModel.review_count + metrics.get("review_count", 0),
            candidate_count=JobRunModel.candidate_count + metrics.get("candidate_count", 0),
            ready_count=JobRunModel.ready_count + metrics.get("ready_count", 0),
            blocked_count=JobRunModel.blocked_count + metrics.get("blocked_count", 0),
            skipped_count=JobRunModel.skipped_count + metrics.get("skipped_count", 0),
            retryable_error_count=JobRunModel.retryable_error_count + metrics.get("retryable_error_count", 0),
            review_required_count=JobRunModel.review_required_count + metrics.get("review_required_count", 0),
            fatal_error_count=JobRunModel.fatal_error_count + metrics.get("fatal_error_count", 0),
            keep_count=JobRunModel.keep_count + metrics.get("keep_count", 0),
            revised_count=JobRunModel.revised_count + metrics.get("revised_count", 0),
            zeroed_count=JobRunModel.zeroed_count + metrics.get("zeroed_count", 0),
            withdrawn_count=JobRunModel.withdrawn_count + metrics.get("withdrawn_count", 0),
            error_count=JobRunModel.error_count + metrics.get("error_count", 0)
        )
        self.session.execute(stmt)

    def finish_run(self, run_id: str, status: str, metrics: Dict[str, Any] = None, error_summary: str = None):
        stmt = update(JobRunModel).where(JobRunModel.run_id == run_id).values(
            status=status,
            finished_at=datetime.now(),
            error_summary=error_summary,
            processed_count=metrics.get("processed_count", 0) if metrics else JobRunModel.processed_count,
            success_count=metrics.get("success_count", 0) if metrics else JobRunModel.success_count,
            excluded_count=metrics.get("excluded_count", 0) if metrics else JobRunModel.excluded_count,
            review_count=metrics.get("review_count", 0) if metrics else JobRunModel.review_count,
            candidate_count=metrics.get("candidate_count", 0) if metrics else JobRunModel.candidate_count,
            ready_count=metrics.get("ready_count", 0) if metrics else JobRunModel.ready_count,
            blocked_count=metrics.get("blocked_count", 0) if metrics else JobRunModel.blocked_count,
            skipped_count=metrics.get("skipped_count", 0) if metrics else JobRunModel.skipped_count,
            retryable_error_count=metrics.get("retryable_error_count", 0) if metrics else JobRunModel.retryable_error_count,
            review_required_count=metrics.get("review_required_count", 0) if metrics else JobRunModel.review_required_count,
            fatal_error_count=metrics.get("fatal_error_count", 0) if metrics else JobRunModel.fatal_error_count,
            keep_count=metrics.get("keep_count", 0) if metrics else JobRunModel.keep_count,
            revised_count=metrics.get("revised_count", 0) if metrics else JobRunModel.revised_count,
            zeroed_count=metrics.get("zeroed_count", 0) if metrics else JobRunModel.zeroed_count,
            withdrawn_count=metrics.get("withdrawn_count", 0) if metrics else JobRunModel.withdrawn_count,
            error_count=metrics.get("error_count", 0) if metrics else JobRunModel.error_count
        )
        self.session.execute(stmt)

    def get_by_run_id(self, run_id: str) -> Optional[JobRun]:
        stmt = select(JobRunModel).where(JobRunModel.run_id == run_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return self._to_domain(result)
        return None

    def list_recent(self, limit: int = 10) -> List[JobRun]:
        stmt = select(JobRunModel).order_by(JobRunModel.started_at.desc()).limit(limit)
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]

    def _to_domain(self, model: JobRunModel) -> JobRun:
        return JobRun(
            run_id=model.run_id,
            job_name=model.job_name,
            job_scope=model.job_scope,
            status=model.status,
            processed_count=model.processed_count,
            success_count=model.success_count,
            excluded_count=model.excluded_count,
            review_count=model.review_count,
            candidate_count=model.candidate_count,
            ready_count=model.ready_count,
            blocked_count=model.blocked_count,
            skipped_count=model.skipped_count,
            retryable_error_count=model.retryable_error_count,
            review_required_count=model.review_required_count,
            fatal_error_count=model.fatal_error_count,
            keep_count=model.keep_count,
            revised_count=model.revised_count,
            zeroed_count=model.zeroed_count,
            withdrawn_count=model.withdrawn_count,
            error_count=model.error_count,
            error_summary=model.error_summary,
            started_at=model.started_at,
            finished_at=model.finished_at
        )
