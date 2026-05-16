from typing import List, Optional, Dict, Any
from src.repositories.persistent_job_run_repository import PersistentJobRunRepository
from ..models import CliCommandResult

class JobRunOpsService:
    def __init__(self, job_run_repo: PersistentJobRunRepository):
        self.job_run_repo = job_run_repo

    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        runs = self.job_run_repo.list_recent(limit=limit)
        return [
            {
                "run_id": r.run_id[:8] + "...",
                "job_name": r.job_name,
                "status": r.status,
                "processed": r.processed_count,
                "success": r.success_count,
                "errors": r.fatal_error_count,
                "started": r.started_at.strftime("%H:%M:%S")
            }
            for r in runs
        ]

    def get_detail(self, run_id: str) -> Optional[Dict[str, Any]]:
        r = self.job_run_repo.get_by_run_id(run_id)
        if not r:
            return None
        return r.__dict__
