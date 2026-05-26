import pytest
from src.listing_execution.repositories.report_generation_log_repository import ReportGenerationLogRepository
from src.orchestrator.report_jobs import ReportJobs, JobScheduler

@pytest.fixture
def repo():
    return ReportGenerationLogRepository()

@pytest.fixture
def jobs(repo):
    return ReportJobs(repo)

# 1. repo: log_job_start
def test_repo_log_start(repo):
    job_id = repo.log_job_start('test_job', 'orchestrator')
    log = repo.get_job_by_id(job_id)
    assert log is not None
    assert log.status == 'running'
    assert log.trigger_source == 'orchestrator'
    assert log.dry_run is False

# 2. repo: log_job_finish
def test_repo_log_finish(repo):
    job_id = repo.log_job_start('test_job', 'orchestrator')
    repo.log_job_finish(job_id, 'success', None)
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'
    assert log.finished_at is not None

# 3. repo: get_recent_jobs limit
def test_repo_recent_jobs(repo):
    for i in range(5):
        repo.log_job_start(f'job_{i}', 'test')
    recent = repo.get_recent_jobs(limit=3)
    assert len(recent) == 3

# 4. daily_execution_summary_job success
def test_daily_job_success(jobs, repo):
    job_id, result = jobs.daily_execution_summary_job()
    assert result is not None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'
    assert log.job_type == 'daily_execution_summary_job'

# 5. weekly_execution_summary_job success
def test_weekly_job_success(jobs, repo):
    job_id, result = jobs.weekly_execution_summary_job()
    assert result is not None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'
    assert log.job_type == 'weekly_execution_summary_job'

# 6. failure_digest_job success
def test_failure_digest_job_success(jobs, repo):
    job_id, result = jobs.failure_digest_job()
    assert result is not None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'

# 7. seller_health_report_job success
def test_seller_health_job_success(jobs, repo):
    job_id, result = jobs.seller_health_report_job(seller_id='s1')
    assert result is not None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'

# 8. audit_export_job success
def test_audit_export_job_success(jobs, repo):
    job_id, result = jobs.audit_export_job()
    assert result is not None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'

# 9. dry_run mode records properly
def test_job_dry_run_flag(jobs, repo):
    job_id, result = jobs.daily_execution_summary_job(dry_run=True)
    log = repo.get_job_by_id(job_id)
    assert log.dry_run is True

# 10. error handling returns failed status
def test_job_error_handling(jobs, repo):
    # invalid date_range for failure digest -> ValueError in service
    job_id, result = jobs.failure_digest_job(from_date="2023-01-02", to_date="2023-01-01")
    assert result is None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'failed'
    assert 'invalid date_range' in log.error_message

# 11. retry logic all fails
def test_retry_logic_max_fails(jobs, repo):
    calls = 0
    def failing_call():
        nonlocal calls
        calls += 1
        raise Exception("Always fails")
    
    job_id, result = jobs._execute_job('test_retry', failing_call, max_retries=3)
    assert result is None
    assert calls == 3
    log = repo.get_job_by_id(job_id)
    assert log.status == 'failed'

# 12. retry logic success on 2nd attempt
def test_retry_logic_success_eventually(jobs, repo):
    calls = 0
    def eventual_success():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise Exception("Fail first time")
        return "success_data"
    
    job_id, result = jobs._execute_job('test_retry_success', eventual_success, max_retries=3)
    assert result == "success_data"
    assert calls == 2
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success'

# 13. JobScheduler records daily
def test_scheduler_daily(jobs):
    scheduler = JobScheduler(jobs)
    scheduler.schedule_daily_execution_summary()
    assert 'daily' in scheduler.schedules['daily_execution_summary_job']

# 14. JobScheduler records weekly
def test_scheduler_weekly(jobs):
    scheduler = JobScheduler(jobs)
    scheduler.schedule_weekly_execution_summary()
    assert 'Monday' in scheduler.schedules['weekly_execution_summary_job']

# 15. JobScheduler records hourly for failures
def test_scheduler_failure(jobs):
    scheduler = JobScheduler(jobs)
    scheduler.schedule_failure_digest()
    assert 'hourly' in scheduler.schedules['failure_digest_job']

# 16. Trigger source is orchestrator
def test_trigger_source_orchestrator(jobs, repo):
    job_id, _ = jobs.audit_export_job()
    log = repo.get_job_by_id(job_id)
    assert log.trigger_source == 'orchestrator'

# 17. Seller not found gracefully handles (returns None from service)
def test_seller_not_found(jobs, repo):
    job_id, result = jobs.seller_health_report_job(seller_id='unknown')
    # service returns None, but doesn't raise exception
    assert result is None
    log = repo.get_job_by_id(job_id)
    assert log.status == 'success' # The job executed successfully, artifact is just empty/none
