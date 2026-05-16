from typing import Dict, List, Optional
from .models import JobDefinition

class JobRegistry:
    def __init__(self):
        self._jobs: Dict[str, JobDefinition] = {}

    def register(self, job_def: JobDefinition):
        if job_def.job_name in self._jobs:
            raise ValueError(f"Job '{job_def.job_name}' is already registered.")
        
        # Simple circular dependency check for immediate self-dependency
        if job_def.job_name in job_def.depends_on:
            raise ValueError(f"Job '{job_def.job_name}' cannot depend on itself.")
            
        self._jobs[job_def.job_name] = job_def

    def get_job(self, job_name: str) -> Optional[JobDefinition]:
        return self._jobs.get(job_name)

    def list_enabled_jobs(self) -> List[JobDefinition]:
        return [j for j in self._jobs.values() if j.enabled]

    def list_by_group(self, group_name: str) -> List[JobDefinition]:
        return [j for j in self._jobs.values() if j.job_group == group_name]

    def validate_all_dependencies(self):
        """Ensures all depends_on jobs exist in the registry."""
        for job in self._jobs.values():
            for dep in job.depends_on:
                if dep not in self._jobs:
                    raise ValueError(f"Job '{job.job_name}' depends on unregistered job '{dep}'.")
