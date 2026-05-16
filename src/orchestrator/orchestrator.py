import time
import threading
import logging
from typing import List, Dict, Any, Optional
from .models import SchedulerCycleResult, ScheduledJobResult
from .engine import SchedulerEngine
from .job_registry import JobRegistry

logger = logging.getLogger(__name__)

class ScheduledOrchestrator:
    def __init__(self, engine: SchedulerEngine):
        self.engine = engine
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.poll_interval = 60 # seconds

    def start(self, poll_interval: int = 60):
        if self._thread and self._thread.is_alive():
            logger.warning("Orchestrator is already running.")
            return

        self.poll_interval = poll_interval
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="OrchestratorLoop", daemon=True)
        self._thread.start()
        logger.info(f"Scheduled Orchestrator started with poll_interval={poll_interval}s")

    def stop(self):
        logger.info("Stopping Scheduled Orchestrator...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Scheduled Orchestrator stopped.")

    def run_once(self, force_jobs: List[str] = None, dry_run: bool = False) -> SchedulerCycleResult:
        """Executes one cycle manually."""
        logger.info("Triggering manual scheduler cycle...")
        return self.engine.run_cycle(force_jobs=force_jobs, dry_run=dry_run)

    def trigger_job(self, job_name: str, dry_run: bool = False) -> Optional[ScheduledJobResult]:
        """Triggers a single job manually."""
        res = self.engine.run_cycle(force_jobs=[job_name], dry_run=dry_run)
        if res.results:
            return res.results[0]
        return None

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                res = self.engine.run_cycle()
                if res.executed_job_count > 0 or res.failed_job_count > 0:
                    logger.info(f"Cycle completed: executed={res.executed_job_count}, failed={res.failed_job_count}, skipped={res.skipped_job_count}")
            except Exception as e:
                logger.exception(f"Error in Orchestrator loop: {e}")
            
            # Wait for next poll
            self._stop_event.wait(self.poll_interval)
