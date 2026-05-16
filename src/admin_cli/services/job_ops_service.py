from typing import List, Optional, Dict, Any
from src.orchestrator.orchestrator import ScheduledOrchestrator
from src.orchestrator.models import JobDefinition
from ..models import CliCommandResult

class JobOpsService:
    def __init__(self, orchestrator: ScheduledOrchestrator):
        self.orchestrator = orchestrator

    def list_jobs(self) -> List[Dict[str, Any]]:
        jobs = self.orchestrator.engine.registry.list_enabled_jobs()
        return [
            {
                "job_name": j.job_name,
                "group": j.job_group,
                "schedule": j.schedule_type,
                "interval": j.interval_seconds,
                "depends_on": ", ".join(j.depends_on) if j.depends_on else "-",
                "runner": j.target_runner_name
            }
            for j in jobs
        ]

    def run_job(self, job_name: str, limit: Optional[int] = None, dry_run: bool = True) -> CliCommandResult:
        job_def = self.orchestrator.engine.registry.get_job(job_name)
        if not job_def:
            return CliCommandResult(command_path="jobs run", status="error", errors=[f"Job '{job_name}' not found."], exit_code=2)
        
        # We use the orchestrator's trigger_job (via engine run_cycle)
        # Note: manual_trigger.py could also be used here.
        # For simplicity in CLI, we'll use a slightly more direct approach or the manual trigger if available.
        
        # Save original defaults
        orig_limit = job_def.default_limit
        job_def.default_limit = limit if limit is not None else orig_limit
        
        try:
            res = self.orchestrator.trigger_job(job_name, dry_run=dry_run)
            if not res:
                return CliCommandResult(command_path="jobs run", status="error", errors=["Job execution failed to start."], exit_code=5)
            
            return CliCommandResult(
                command_path="jobs run",
                message=f"Job '{job_name}' executed.",
                summary={
                    "run_id": res.run_id,
                    "status": res.status,
                    "processed": res.processed_count,
                    "success": res.success_count,
                    "skipped": res.skipped_count,
                    "errors": res.fatal_error_count
                },
                exit_code=0 if res.success_flag else 4
            )
        finally:
            job_def.default_limit = orig_limit
