import logging
from typing import Dict, Any
from .models import JobDefinition
from .job_registry import JobRegistry
from .lock_manager import JobLockManager
from .engine import SchedulerEngine
from .orchestrator import ScheduledOrchestrator
from .job_definitions import get_standard_job_definitions
from .dummy_runners import SourceCollector, HousekeepingRunner

logger = logging.getLogger(__name__)

class OrchestratorBootstrap:
    @staticmethod
    def bootstrap(
        repositories: Dict[str, Any],
        pipelines: Dict[str, Any],
        gateways: Dict[str, Any]
    ) -> ScheduledOrchestrator:
        """
        Wires together the Orchestrator with all necessary dependencies.
        """
        logger.info("Bootstrapping Scheduled Orchestrator...")
        
        # 1. Registry
        registry = JobRegistry()
        for job_def in get_standard_job_definitions():
            registry.register(job_def)
        
        # 2. Lock Manager
        lock_manager = JobLockManager()
        
        # 3. Runner Map
        # Connect target_runner_name to actual objects
        runner_map = {
            "source_collect_runner": pipelines.get("source_collector") or SourceCollector(),
            "research_candidate_runner": pipelines.get("research"),
            "listing_readiness_runner": pipelines.get("readiness"),
            "listing_execution_runner": gateways.get("listing_execution"),
            "monitoring_revise_runner": pipelines.get("monitoring"),
            "listing_sync_recovery_runner": gateways.get("listing_sync"),
            "housekeeping_runner": pipelines.get("housekeeping") or HousekeepingRunner()
        }
        
        # 4. Engine
        engine = SchedulerEngine(registry, lock_manager, runner_map)
        
        # 5. Orchestrator
        orchestrator = ScheduledOrchestrator(engine)
        
        return orchestrator
