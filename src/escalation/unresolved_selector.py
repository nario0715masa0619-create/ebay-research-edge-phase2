from typing import List, Any
from datetime import datetime
from sqlalchemy import select, and_, or_
from src.escalation.models import EscalationState
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository

class UnresolvedEventSelector:
    def __init__(self, state_repo: PersistentEscalationStateRepository):
        self.state_repo = state_repo

    def process_auto_resolutions(self, db_session: Any) -> int:
        # Check active unresolved states and auto-resolve them if recovery is detected in system tables
        resolved_count = 0
        
        # Get active states that support auto-resolution
        # For simplicity, we can load all non-resolved states
        stmt = self.state_repo.list_unresolved_due_for_reminder(datetime.now())
        
        # We will dynamically check for recovery events
        # 1. For "scheduled_job_failed", check if there is a successful JobRun after last_seen_at
        from src.db.models import JobRunModel, NotificationHistoryModel
        
        for state in stmt:
            if state.source_event_type == "scheduled_job_failed":
                # Find if a success run occurred after last_seen_at for this job
                job_name = state.source_status_snapshot.get("job_name") or state.dedupe_key.split(":")[-1]
                
                query = select(JobRunModel).where(
                    and_(
                        JobRunModel.job_name == job_name,
                        JobRunModel.status == "completed",
                        JobRunModel.finished_at > state.last_seen_at
                    )
                ).limit(1)
                
                success_run = db_session.execute(query).scalar_one_or_none()
                if success_run:
                    self.state_repo.mark_resolved(
                        state.state_id,
                        actor_id="system_resolver",
                        note=f"Auto-resolved: Job '{job_name}' completed successfully at {success_run.finished_at}."
                    )
                    resolved_count += 1
                    
            elif state.source_event_type == "auth_refresh_failed":
                # Check for subsequent successful auth notification or token refresh success after last_seen_at
                query = select(NotificationHistoryModel).where(
                    and_(
                        NotificationHistoryModel.event_type == "auth_refresh_success",
                        NotificationHistoryModel.seller_account_id == state.seller_account_id,
                        NotificationHistoryModel.created_at > state.last_seen_at
                    )
                ).limit(1)
                
                success_auth = db_session.execute(query).scalar_one_or_none()
                if success_auth:
                    self.state_repo.mark_resolved(
                        state.state_id,
                        actor_id="system_resolver",
                        note="Auto-resolved: Auth token refresh succeeded."
                    )
                    resolved_count += 1

            elif state.source_event_type == "listing_drift_detected":
                # Check for subseqent sync repair success
                query = select(NotificationHistoryModel).where(
                    and_(
                        NotificationHistoryModel.event_type == "listing_sync_success",
                        NotificationHistoryModel.seller_account_id == state.seller_account_id,
                        NotificationHistoryModel.created_at > state.last_seen_at
                    )
                ).limit(1)
                
                success_sync = db_session.execute(query).scalar_one_or_none()
                if success_sync:
                    self.state_repo.mark_resolved(
                        state.state_id,
                        actor_id="system_resolver",
                        note="Auto-resolved: Listing drift cleared successfully."
                    )
                    resolved_count += 1

            elif state.source_event_type == "doctor_check_failed":
                # Check for subseqent successful doctor checks
                query = select(NotificationHistoryModel).where(
                    and_(
                        NotificationHistoryModel.event_type == "doctor_check_success",
                        NotificationHistoryModel.created_at > state.last_seen_at
                    )
                ).limit(1)
                
                success_doc = db_session.execute(query).scalar_one_or_none()
                if success_doc:
                    self.state_repo.mark_resolved(
                        state.state_id,
                        actor_id="system_resolver",
                        note="Auto-resolved: Doctor check passed."
                    )
                    resolved_count += 1
                    
        return resolved_count
