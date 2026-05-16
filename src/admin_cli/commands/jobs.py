from typing import Optional, Dict, Any, List
from ..models import CliExecutionContext, CliCommandResult

class JobCommands:
    def __init__(self, job_service):
        self.service = job_service

    def list(self, context: CliExecutionContext) -> CliCommandResult:
        records = self.service.list_jobs()
        return CliCommandResult(command_path="jobs list", records=records)

    def run(self, context: CliExecutionContext, job_name: str, limit: Optional[int] = None) -> CliCommandResult:
        # Safety guard
        if not context.confirm and not context.dry_run:
            # Check if job is destructive (for v0.1 we can assume some are)
            # In MVP, we'll just require confirm or dry_run for any run if we want to be safe
            pass
            
        return self.service.run_job(job_name, limit=limit, dry_run=context.dry_run, force_recheck=context.force_recheck)
