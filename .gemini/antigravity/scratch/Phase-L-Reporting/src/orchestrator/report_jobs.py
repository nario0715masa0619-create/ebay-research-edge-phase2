from typing import Callable, Any, Optional
from src.listing_execution.repositories.report_generation_log_repository import ReportGenerationLogRepository
from src.services.report_services import (
    ExecutionSummaryService,
    FailureDigestService,
    SellerHealthAnalysisService,
    ReportExportService
)

class ReportJobs:
    def __init__(self, log_repo: ReportGenerationLogRepository):
        self.log_repo = log_repo

    def _execute_job(self, job_type: str, service_call: Callable[[], Any], dry_run: bool = False, max_retries: int = 3):
        job_id = self.log_repo.log_job_start(job_type, trigger_source='orchestrator', dry_run=dry_run)
        
        last_error = None
        for attempt in range(max_retries):
            try:
                result = service_call()
                # If not dry run, in real implementation we would persist the artifact here
                self.log_repo.log_job_finish(job_id, status='success')
                return job_id, result
            except Exception as e:
                last_error = str(e)
                if attempt == max_retries - 1:
                    break
        
        # All retries failed
        self.log_repo.log_job_finish(job_id, status='failed', error_message=last_error)
        return job_id, None

    def daily_execution_summary_job(self, date: Optional[str] = None, seller_filter: Optional[str] = None, environment_filter: Optional[str] = None, dry_run: bool = False):
        def call():
            # Returns ReportDTO which serves as ReportMetadata for now
            return ExecutionSummaryService().get_summary('daily', seller_filter, environment_filter, date)
        return self._execute_job('daily_execution_summary_job', call, dry_run=dry_run)

    def weekly_execution_summary_job(self, week: Optional[str] = None, seller_filter: Optional[str] = None, environment_filter: Optional[str] = None, dry_run: bool = False):
        def call():
            return ExecutionSummaryService().get_summary('weekly', seller_filter, environment_filter, week)
        return self._execute_job('weekly_execution_summary_job', call, dry_run=dry_run)

    def failure_digest_job(self, from_date: Optional[str] = None, to_date: Optional[str] = None, limit: int = 50, dry_run: bool = False):
        def call():
            return FailureDigestService().get_digest(from_date, to_date, limit)
        return self._execute_job('failure_digest_job', call, dry_run=dry_run)

    def seller_health_report_job(self, seller_id: str, from_date: Optional[str] = None, to_date: Optional[str] = None, dry_run: bool = False):
        def call():
            return SellerHealthAnalysisService().analyze(seller_id, from_date, to_date)
        return self._execute_job('seller_health_report_job', call, dry_run=dry_run)

    def audit_export_job(self, from_date: Optional[str] = None, to_date: Optional[str] = None, seller_filter: Optional[str] = None, format: str = 'csv', dry_run: bool = False):
        def call():
            return ReportExportService().export_audit(seller_filter, from_date, to_date)
        return self._execute_job('audit_export_job', call, dry_run=dry_run)

# Mock Scheduler Integration (Just for tests / tracking schedules as per Wave 5 reqs)
class JobScheduler:
    def __init__(self, report_jobs: ReportJobs):
        self.report_jobs = report_jobs
        self.schedules = {}

    def schedule_daily_execution_summary(self):
        # recommended: daily 00:00 UTC
        self.schedules['daily_execution_summary_job'] = '00:00 UTC daily'
        
    def schedule_weekly_execution_summary(self):
        # recommended: weekly Monday 00:00 UTC
        self.schedules['weekly_execution_summary_job'] = '00:00 UTC every Monday'

    def schedule_failure_digest(self):
        # recommended: hourly
        self.schedules['failure_digest_job'] = 'hourly'

    def schedule_seller_health(self):
        # recommended: daily
        self.schedules['seller_health_report_job'] = 'daily'

    def schedule_audit_export(self):
        # recommended: manual or weekly
        self.schedules['audit_export_job'] = 'weekly or manual'
