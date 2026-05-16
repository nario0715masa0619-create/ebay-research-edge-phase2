from typing import List, Optional, Dict, Any
from src.orchestrator.orchestrator import ScheduledOrchestrator
from ..models import CliCommandResult

class SchedulerOpsService:
    def __init__(self, orchestrator: ScheduledOrchestrator):
        self.orchestrator = orchestrator

    def get_status(self) -> Dict[str, Any]:
        engine = self.orchestrator.engine
        jobs = engine.registry.list_enabled_jobs()
        
        return {
            "poll_interval": self.orchestrator.poll_interval,
            "registered_jobs_count": len(jobs),
            "last_cycle_times": {k: v.isoformat() for k, v in engine.last_run_times.items()},
            "is_alive": self.orchestrator._thread.is_alive() if self.orchestrator._thread else False
        }

    def run_once(self, dry_run: bool = True) -> CliCommandResult:
        res = self.orchestrator.run_once(dry_run=dry_run)
        return CliCommandResult(
            command_path="scheduler run-once",
            message="Manual scheduler cycle completed.",
            summary={
                "cycle_id": res.cycle_id,
                "executed": res.executed_job_count,
                "failed": res.failed_job_count,
                "skipped": res.skipped_job_count
            },
            records=[{"job": r.job_name, "status": r.status, "processed": r.processed_count} for r in res.results],
            exit_code=0 if res.success_flag else 4
        )

    def start(self, interval: int = 60) -> str:
        self.orchestrator.start(poll_interval=interval)
        return "Scheduler started."

    def stop(self) -> str:
        self.orchestrator.stop()
        return "Scheduler stopped."
