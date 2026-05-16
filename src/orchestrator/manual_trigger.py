from typing import Optional, Dict, Any, List
from .orchestrator import ScheduledOrchestrator
from .models import ScheduledJobResult

class ManualTrigger:
    def __init__(self, orchestrator: ScheduledOrchestrator):
        self.orchestrator = orchestrator

    def trigger(self, 
                job_name: str, 
                dry_run: bool = False, 
                limit: Optional[int] = None, 
                force_recheck: bool = False,
                include_dependencies: bool = False,
                **kwargs) -> List[ScheduledJobResult]:
        """
        Manually triggers a job.
        If include_dependencies is True, it runs the DAG up to this job.
        """
        if not include_dependencies:
            # Single job execution
            # We override the job definition kwargs with provided ones
            job_def = self.orchestrator.engine.registry.get_job(job_name)
            if not job_def:
                raise ValueError(f"Job '{job_name}' not found.")
            
            # Temporarily override
            original_limit = job_def.default_limit
            original_kwargs = job_def.default_kwargs
            
            job_def.default_limit = limit if limit is not None else original_limit
            job_def.default_kwargs.update(kwargs)
            
            try:
                res = self.orchestrator.trigger_job(job_name, dry_run=dry_run)
                return [res] if res else []
            finally:
                job_def.default_limit = original_limit
                job_def.default_kwargs = original_kwargs
        else:
            # Run the cycle with force_jobs
            # This will resolve dependencies
            cycle_res = self.orchestrator.engine.run_cycle(force_jobs=[job_name], dry_run=dry_run)
            return cycle_res.results
