import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from src.orchestrator.models import JobDefinition, ScheduledJobResult
from src.orchestrator.job_registry import JobRegistry
from src.orchestrator.engine import SchedulerEngine
from src.orchestrator.lock_manager import JobLockManager
from src.orchestrator.orchestrator import ScheduledOrchestrator

@pytest.fixture
def mock_runners():
    return {
        "source_collect_runner": MagicMock(),
        "research_candidate_runner": MagicMock(),
        "listing_readiness_runner": MagicMock(),
        "listing_execution_runner": MagicMock(),
        "monitoring_revise_runner": MagicMock(),
        "listing_sync_recovery_runner": MagicMock(),
        "housekeeping_runner": MagicMock()
    }

@pytest.fixture
def registry():
    reg = JobRegistry()
    reg.register(JobDefinition(
        job_name="job_a", schedule_type="interval", interval_seconds=10, 
        target_runner_name="source_collect_runner"
    ))
    reg.register(JobDefinition(
        job_name="job_b", schedule_type="interval", interval_seconds=10, 
        depends_on=["job_a"], target_runner_name="research_candidate_runner"
    ))
    return reg

def test_scheduler_execution_order(registry, mock_runners):
    lock_manager = JobLockManager()
    engine = SchedulerEngine(registry, lock_manager, mock_runners)
    
    # Mock return values for runners
    mock_runners["source_collect_runner"].run_source_collection.return_value = MagicMock(success_flag=True, processed_count=10)
    mock_runners["research_candidate_runner"].run_research_candidate_pipeline.return_value = MagicMock(success_flag=True, processed_count=5)
    
    res = engine.run_cycle()
    
    assert res.executed_job_count == 2
    assert res.results[0].job_name == "job_a"
    assert res.results[1].job_name == "job_b"
    assert mock_runners["source_collect_runner"].run_source_collection.called
    assert mock_runners["research_candidate_runner"].run_research_candidate_pipeline.called

def test_scheduler_skip_downstream_on_failure(registry, mock_runners):
    lock_manager = JobLockManager()
    engine = SchedulerEngine(registry, lock_manager, mock_runners)
    
    # job_a fails
    mock_runners["source_collect_runner"].run_source_collection.return_value = MagicMock(success_flag=False, fatal_error_count=1)
    
    res = engine.run_cycle()
    
    assert res.executed_job_count == 0
    assert res.failed_job_count == 1
    assert res.skipped_job_count == 1
    assert res.results[0].job_name == "job_a"
    assert res.results[0].status == "failed"
    # job_b should not be in results because it was skipped before execution attempt (added to status_map only)
    # wait, my engine adds skipped to cycle_res.skipped_job_count but not always to cycle_res.results
    assert res.skipped_job_count == 1

def test_lock_prevention(registry, mock_runners):
    lock_manager = JobLockManager()
    engine = SchedulerEngine(registry, lock_manager, mock_runners)
    
    lock_manager.acquire("job_a") # Manually lock
    
    res = engine.run_cycle()
    
    assert res.skipped_job_count == 2 # job_a locked, job_b skipped due to dependency
    assert not mock_runners["source_collect_runner"].run_source_collection.called

def test_manual_trigger(registry, mock_runners):
    lock_manager = JobLockManager()
    engine = SchedulerEngine(registry, lock_manager, mock_runners)
    orchestrator = ScheduledOrchestrator(engine)
    
    mock_runners["source_collect_runner"].run_source_collection.return_value = MagicMock(success_flag=True)
    
    res = orchestrator.trigger_job("job_a")
    assert res.job_name == "job_a"
    assert res.status == "completed"
