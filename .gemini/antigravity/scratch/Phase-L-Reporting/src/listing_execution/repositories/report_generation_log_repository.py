import uuid
import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ReportGenerationLog:
    job_id: str
    job_type: str
    trigger_source: str
    status: str
    error_message: Optional[str]
    started_at: datetime.datetime
    finished_at: Optional[datetime.datetime]
    dry_run: bool = False

class ReportGenerationLogRepository:
    def __init__(self):
        self._store = {}

    def log_job_start(self, job_type: str, trigger_source: str, dry_run: bool = False) -> str:
        job_id = str(uuid.uuid4())
        log = ReportGenerationLog(
            job_id=job_id,
            job_type=job_type,
            trigger_source=trigger_source,
            status='running',
            error_message=None,
            started_at=datetime.datetime.utcnow(),
            finished_at=None,
            dry_run=dry_run
        )
        self._store[job_id] = log
        return job_id

    def log_job_finish(self, job_id: str, status: str, error_message: Optional[str] = None):
        if job_id in self._store:
            log = self._store[job_id]
            log.status = status
            log.error_message = error_message
            log.finished_at = datetime.datetime.utcnow()

    def get_recent_jobs(self, limit: int = 20) -> List[ReportGenerationLog]:
        logs = list(self._store.values())
        logs.sort(key=lambda x: x.started_at, reverse=True)
        return logs[:limit]

    def get_job_by_id(self, job_id: str) -> Optional[ReportGenerationLog]:
        return self._store.get(job_id)
