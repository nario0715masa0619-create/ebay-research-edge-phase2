import pytest
from unittest.mock import MagicMock
from src.admin_cli.services.job_ops_service import JobOpsService
from src.admin_cli.services.candidate_ops_service import CandidateOpsService
from src.orchestrator.models import JobDefinition, ScheduledJobResult

@pytest.fixture
def mock_orchestrator():
    orchestrator = MagicMock()
    # Mock registry
    job_a = JobDefinition(job_name="job_a", job_group="test", target_runner_name="runner_a")
    orchestrator.engine.registry.list_enabled_jobs.return_value = [job_a]
    orchestrator.engine.registry.get_job.return_value = job_a
    return orchestrator

def test_job_ops_list(mock_orchestrator):
    service = JobOpsService(mock_orchestrator)
    jobs = service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["job_name"] == "job_a"

def test_job_ops_run_success(mock_orchestrator):
    service = JobOpsService(mock_orchestrator)
    mock_orchestrator.trigger_job.return_value = ScheduledJobResult(
        job_name="job_a", run_id="run-123", scheduler_run_id="cycle-1", 
        success_flag=True, status="completed"
    )
    
    result = service.run_job("job_a")
    assert result.exit_code == 0
    assert result.summary["run_id"] == "run-123"

def test_candidate_ops_list():
    repo = MagicMock()
    cand = MagicMock()
    cand.sku = "SKU-1"
    cand.source_title = "Title 1"
    cand.status = "approved"
    cand.listing_readiness_status = "ready"
    cand.standard_score = 4.5
    cand.expected_profit_jpy = 1000
    repo.list_all.return_value = [cand]
    
    service = CandidateOpsService(repo)
    items = service.list_candidates()
    assert len(items) == 1
    assert items[0]["sku"] == "SKU-1"
