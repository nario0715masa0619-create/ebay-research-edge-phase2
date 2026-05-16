import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .models import JobDefinition, JobExecutionContext, ScheduledJobResult, SchedulerCycleResult
from .job_registry import JobRegistry
from .dependency_resolver import JobDependencyResolver
from .lock_manager import JobLockManager
from .result_aggregator import JobResultAggregator

logger = logging.getLogger(__name__)

class SchedulerEngine:
    def __init__(self, registry: JobRegistry, lock_manager: JobLockManager, runner_map: Dict[str, Any]):
        self.registry = registry
        self.lock_manager = lock_manager
        self.runner_map = runner_map
        self.resolver = JobDependencyResolver()
        self.aggregator = JobResultAggregator()
        self.last_run_times: Dict[str, datetime] = {}

    def run_cycle(self, force_jobs: List[str] = None, dry_run: bool = False) -> SchedulerCycleResult:
        cycle_id = str(uuid.uuid4())
        cycle_res = SchedulerCycleResult(cycle_id=cycle_id, started_at=datetime.now())
        
        # 1. Identify due jobs
        due_jobs = self._identify_due_jobs(force_jobs)
        cycle_res.scheduled_job_count = len(due_jobs)
        
        if not due_jobs:
            cycle_res.finished_at = datetime.now()
            return cycle_res

        # 2. Resolve execution order
        ordered_jobs = self.resolver.resolve_execution_order(due_jobs)
        
        # 3. Execute in order
        job_status_map: Dict[str, str] = {} # job_name -> status

        for job_def in ordered_jobs:
            # Check dependencies
            if not self._can_run(job_def, job_status_map):
                logger.info(f"Skipping job '{job_def.job_name}' due to failed dependency.")
                job_status_map[job_def.job_name] = "skipped"
                cycle_res.skipped_job_count += 1
                continue

            # Lock
            lock_key = job_def.lock_key or job_def.job_name
            if not self.lock_manager.acquire(lock_key):
                logger.warning(f"Job '{job_def.job_name}' is already running (locked). Skipping.")
                job_status_map[job_def.job_name] = "skipped"
                cycle_res.skipped_job_count += 1
                continue

            try:
                # Dispatch
                result = self._execute_job(job_def, cycle_id, dry_run)
                cycle_res.results.append(result)
                job_status_map[job_def.job_name] = result.status
                self.last_run_times[job_def.job_name] = datetime.now()
                
                if result.status == "completed":
                    cycle_res.executed_job_count += 1
                else:
                    cycle_res.failed_job_count += 1
            finally:
                self.lock_manager.release(lock_key)

        cycle_res.finished_at = datetime.now()
        cycle_res.success_flag = (cycle_res.failed_job_count == 0)
        return cycle_res

    def _identify_due_jobs(self, force_jobs: List[str]) -> List[JobDefinition]:
        all_jobs = self.registry.list_enabled_jobs()
        if force_jobs:
            return [j for j in all_jobs if j.job_name in force_jobs]
        
        due = []
        now = datetime.now()
        for job in all_jobs:
            if job.schedule_type == "manual_only":
                continue
            
            last_run = self.last_run_times.get(job.job_name)
            if not last_run:
                # First time run (or startup_once)
                due.append(job)
                continue
            
            if job.schedule_type == "interval" and job.interval_seconds:
                if now >= last_run + timedelta(seconds=job.interval_seconds):
                    due.append(job)
            
            # Cron would go here
            
        return due

    def _can_run(self, job: JobDefinition, status_map: Dict[str, str]) -> bool:
        for dep in job.depends_on:
            # We only care about dependencies within the SAME cycle usually, 
            # or we assume cross-cycle dependencies are handled by state check in pipelines.
            if dep in status_map:
                if status_map[dep] not in ["completed"]:
                    return False
        return True

    def _execute_job(self, job_def: JobDefinition, cycle_id: str, dry_run: bool) -> ScheduledJobResult:
        context = JobExecutionContext(
            scheduler_run_id=cycle_id,
            job_name=job_def.job_name,
            dry_run=dry_run,
            limit=job_def.default_limit,
            kwargs=job_def.default_kwargs.copy()
        )
        
        runner = self.runner_map.get(job_def.target_runner_name)
        if not runner:
            return ScheduledJobResult(
                job_name=job_def.job_name,
                run_id="n/a",
                scheduler_run_id=cycle_id,
                status="failed",
                error_summary=f"Runner '{job_def.target_runner_name}' not found.",
                success_flag=False
            )

        try:
            logger.info(f"Executing job '{job_def.job_name}' via '{job_def.target_runner_name}'...")
            # All our runners are expected to have a method like run_xxx or execute_xxx
            # We'll use a standard interface or dispatch by name
            raw_result = self._dispatch_call(runner, job_def, context)
            return self.aggregator.aggregate(job_def.job_name, context, raw_result)
        except Exception as e:
            logger.exception(f"Error executing job '{job_def.job_name}': {e}")
            return ScheduledJobResult(
                job_name=job_def.job_name,
                run_id="error",
                scheduler_run_id=cycle_id,
                status="failed",
                error_summary=str(e),
                success_flag=False
            )

    def _dispatch_call(self, runner: Any, job_def: JobDefinition, context: JobExecutionContext) -> Any:
        # Map runner names to methods
        method_map = {
            "source_collect_runner": "run_source_collection",
            "research_candidate_runner": "run_research_candidate_pipeline",
            "listing_readiness_runner": "run_listing_readiness_pipeline",
            "listing_execution_runner": "run_listing_execution_gateway",
            "monitoring_revise_runner": "run_monitoring_revise_pipeline",
            "listing_sync_recovery_runner": "run_listing_sync_recovery_gateway",
            "housekeeping_runner": "run_housekeeping"
        }
        
        method_name = method_map.get(job_def.target_runner_name)
        if not method_name or not hasattr(runner, method_name):
            raise AttributeError(f"Runner {runner} does not have method {method_name}")
            
        method = getattr(runner, method_name)
        # Call with kwargs if needed
        # Most of our methods take (limit, dry_run, etc.)
        kwargs = context.kwargs
        if context.limit: kwargs["limit"] = context.limit
        kwargs["dry_run"] = context.dry_run
        kwargs["scheduler_run_id"] = context.scheduler_run_id
        
        return method(**kwargs)
