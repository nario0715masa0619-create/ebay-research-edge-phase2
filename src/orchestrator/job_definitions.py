from .models import JobDefinition

def get_standard_job_definitions() -> list[JobDefinition]:
    return [
        JobDefinition(
            job_name="source_collect_job",
            job_group="pipeline",
            schedule_type="interval",
            interval_seconds=3600 * 6, # 6 hours
            target_runner_name="source_collect_runner",
            lock_key="source_collect",
            run_on_startup=True
        ),
        JobDefinition(
            job_name="research_candidate_job",
            job_group="pipeline",
            schedule_type="interval",
            interval_seconds=3600 * 1, # 1 hour
            depends_on=["source_collect_job"],
            target_runner_name="research_candidate_runner",
            lock_key="research_candidate"
        ),
        JobDefinition(
            job_name="listing_readiness_job",
            job_group="pipeline",
            schedule_type="interval",
            interval_seconds=3600 * 1,
            depends_on=["research_candidate_job"],
            target_runner_name="listing_readiness_runner",
            lock_key="listing_readiness"
        ),
        JobDefinition(
            job_name="listing_execution_job",
            job_group="pipeline",
            schedule_type="interval",
            interval_seconds=3600 * 2,
            depends_on=["listing_readiness_job"],
            target_runner_name="listing_execution_runner",
            lock_key="listing_execution"
        ),
        JobDefinition(
            job_name="monitoring_revise_job",
            job_group="maintenance",
            schedule_type="interval",
            interval_seconds=3600 * 4,
            target_runner_name="monitoring_revise_runner",
            lock_key="monitoring_revise"
        ),
        JobDefinition(
            job_name="listing_sync_recovery_job",
            job_group="maintenance",
            schedule_type="interval",
            interval_seconds=3600 * 12,
            target_runner_name="listing_sync_recovery_runner",
            lock_key="listing_sync_recovery"
        ),
        JobDefinition(
            job_name="housekeeping_job",
            job_group="system",
            schedule_type="interval",
            interval_seconds=3600 * 24, # Daily
            target_runner_name="housekeeping_runner",
            lock_key="housekeeping"
        ),
        JobDefinition(
            job_name="escalation_reminder_job",
            job_group="system",
            schedule_type="interval",
            interval_seconds=300, # 5 minutes
            target_runner_name="escalation_reminder_runner",
            lock_key="escalation_reminder_job",
            allow_overlap=False,
            kwargs={"enable_re_escalation": True}
        )
    ]
