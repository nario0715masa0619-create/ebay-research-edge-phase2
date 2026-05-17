import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, or_

from src.db.models import NotificationHistoryModel, JobRunModel
from src.escalation.models import (
    EscalationState,
    EscalationBatchResult,
    ReminderExecutionResult,
    EscalationExecutionResult
)
from src.escalation.event_normalizer import NormalizedEscalationEvent, EscalationEventNormalizer
from src.escalation.unresolved_selector import UnresolvedEventSelector
from src.escalation.policy_resolver import SellerEnvPolicyResolver
from src.escalation.reminder_decision_engine import ReminderDecisionEngine
from src.escalation.escalation_decision_engine import EscalationDecisionEngine
from src.escalation.reminder_dispatcher import ReminderDispatcher
from src.escalation.escalation_dispatcher import EscalationDispatcher
from src.escalation.result_mapper import EscalationResultMapper
from src.escalation.maintenance_window_service import MaintenanceWindowService
from src.escalation.route_resolver import RouteResolver
from src.escalation.re_escalation_decision_engine import ReEscalationDecisionEngine
from src.escalation.aging import calculate_aging_bucket
from src.escalation.sla import evaluate_sla_breach
from src.repositories.persistent_escalation_state_repository import (
    PersistentEscalationStateRepository,
    PersistentEscalationPolicyRepository
)

logger = logging.getLogger(__name__)

class EscalationRunner:
    def __init__(
        self,
        state_repo: PersistentEscalationStateRepository,
        policy_repo: PersistentEscalationPolicyRepository,
        policy_resolver: SellerEnvPolicyResolver,
        reminder_engine: ReminderDecisionEngine,
        escalation_engine: EscalationDecisionEngine,
        reminder_dispatcher: ReminderDispatcher,
        escalation_dispatcher: EscalationDispatcher,
        result_mapper: EscalationResultMapper,
        unresolved_selector: UnresolvedEventSelector,
        maintenance_service: MaintenanceWindowService,
        route_resolver: RouteResolver,
        re_escalation_engine: ReEscalationDecisionEngine
    ):
        self.state_repo = state_repo
        self.policy_repo = policy_repo
        self.policy_resolver = policy_resolver
        self.reminder_engine = reminder_engine
        self.escalation_engine = escalation_engine
        self.reminder_dispatcher = reminder_dispatcher
        self.escalation_dispatcher = escalation_dispatcher
        self.result_mapper = result_mapper
        self.unresolved_selector = unresolved_selector
        self.maintenance_service = maintenance_service
        self.route_resolver = route_resolver
        self.re_escalation_engine = re_escalation_engine

    def run(
        self,
        db_session: Any,
        dry_run: bool = False,
        seller_account_id: Optional[str] = None,
        environment_type: Optional[str] = None,
        lookback_hours: int = 24,
        enable_re_escalation: bool = True
    ) -> EscalationBatchResult:
        run_id = str(uuid.uuid4())
        logger.info(f"Starting Escalation / Reminder batch run {run_id} (dry_run: {dry_run})")
        
        batch_result = EscalationBatchResult(run_id=run_id)
        now = datetime.now()

        # Step 1: Query raw source logs and ingest into escalation states
        since = now - timedelta(hours=lookback_hours)
        
        # 1a. Load failed/warning notifications
        notif_stmt = select(NotificationHistoryModel).where(
            and_(
                NotificationHistoryModel.created_at >= since,
                NotificationHistoryModel.severity.in_(["warning", "error", "critical"])
            )
        )
        if seller_account_id:
            notif_stmt = notif_stmt.where(NotificationHistoryModel.seller_account_id == seller_account_id)
        if environment_type:
            notif_stmt = notif_stmt.where(NotificationHistoryModel.environment_type == environment_type)
            
        notifications = db_session.execute(notif_stmt).scalars().all()
        for history in notifications:
            try:
                norm_event = EscalationEventNormalizer.normalize_notification_history(history)
                self._ingest_normalized_event(norm_event, dry_run)
                batch_result.processed_count += 1
            except Exception as e:
                logger.error(f"Failed to ingest notification {history.event_id}: {e}")
                batch_result.errors.append({"event_id": history.event_id, "error": str(e)})
                batch_result.fatal_count += 1

        # 1b. Load failed scheduled jobs
        job_stmt = select(JobRunModel).where(
            and_(
                JobRunModel.started_at >= since,
                JobRunModel.status == "failed"
            )
        )
        if seller_account_id:
            job_stmt = job_stmt.where(JobRunModel.seller_account_id == seller_account_id)
        if environment_type:
            job_stmt = job_stmt.where(JobRunModel.environment_type == environment_type)

        failed_jobs = db_session.execute(job_stmt).scalars().all()
        for job_run in failed_jobs:
            try:
                norm_event = EscalationEventNormalizer.normalize_job_run(job_run)
                self._ingest_normalized_event(norm_event, dry_run)
                batch_result.processed_count += 1
            except Exception as e:
                logger.error(f"Failed to ingest failed job run {job_run.run_id}: {e}")
                batch_result.errors.append({"run_id": job_run.run_id, "error": str(e)})
                batch_result.fatal_count += 1

        # Step 2: Auto-resolve recovered states (source recovery check)
        if not dry_run:
            auto_resolved = self.unresolved_selector.process_auto_resolutions(db_session)
            batch_result.resolved_count += auto_resolved

        # Step 3: Load active unresolved states for reminder & escalation evaluation
        unresolved_states = self.state_repo.list_unresolved_due_for_reminder(
            now=now,
            seller_account_id=seller_account_id,
            environment_type=environment_type
        )

        for state in unresolved_states:
            try:
                policy = self.policy_resolver.resolve(
                    seller_account_id=state.seller_account_id,
                    environment_type=state.environment_type,
                    event_type=state.source_event_type,
                    severity=state.current_severity
                )

                # --- v0.2 Aging & SLA Evaluation ---
                aging_seconds = int((now - state.first_seen_at).total_seconds())
                state.aging_seconds = aging_seconds
                state.aging_bucket = calculate_aging_bucket(aging_seconds)
                
                is_breached, target_sev, target_pri = evaluate_sla_breach(state, policy, now)
                if is_breached and not dry_run and not state.sla_breached_at:
                    self.state_repo.mark_sla_breached(state.state_id, now, target_sev, target_pri)
                    state.sla_breached_at = now
                    state.current_severity = target_sev or state.current_severity
                    state.current_priority = target_pri or state.current_priority

                if state.sla_breached_at:
                    batch_result.breach_count += 1

                # --- v0.2 Maintenance Window Check ---
                active_window = None
                if policy.maintenance_window_respected:
                    active_window = self.maintenance_service.evaluate_suppression(state, now)
                    if active_window and active_window.action in ("suppress_all", "suppress_escalation", "suppress_reminder"):
                        if not dry_run:
                            # Update aging info but skip dispatch
                            self.state_repo.upsert_open_state(state)
                        batch_result.maintenance_suppressed_count += 1
                        batch_result.skipped_count += 1
                        continue

                # Try Escalation first
                esc_result = self.escalation_engine.evaluate(state, policy, now)
                if esc_result.decision == "escalate":
                    # Determine step index configuration
                    step = next(s for s in policy.escalation_steps if s.step_index == esc_result.escalation_level_after)
                    
                    # Resolve overriding routes
                    channels = self.route_resolver.resolve(state, policy, esc_result.dispatched_channels)
                    
                    # Dispatch
                    channels = self.escalation_dispatcher.dispatch(
                        state=state,
                        policy=policy,
                        target_level=esc_result.escalation_level_after,
                        target_channels=esc_result.dispatched_channels,
                        target_severity=step.target_severity,
                        target_priority=step.target_priority,
                        dry_run=dry_run
                    )
                    
                    esc_result.dispatched_channels = channels
                    
                    if not dry_run:
                        self.result_mapper.map_escalation_result(
                            state=state,
                            result=esc_result,
                            target_severity=step.target_severity,
                            target_priority=step.target_priority,
                            now=now
                        )
                    
                    batch_result.escalation_sent_count += 1
                    continue

                # Try Re-Escalation (v0.2)
                if enable_re_escalation and policy.re_escalation_enabled:
                    re_esc_decision = self.re_escalation_engine.evaluate(state, policy, now)
                    if re_esc_decision == "re_escalate":
                        # Assume sending to the last escalated channels or default
                        channels = self.route_resolver.resolve(state, policy, ["email_critical"])
                        
                        if not dry_run:
                            self.escalation_dispatcher.dispatch(
                                state=state,
                                policy=policy,
                                target_level=state.escalation_level,
                                target_channels=channels,
                                target_severity=state.current_severity,
                                target_priority=state.current_priority,
                                dry_run=False,
                                is_re_escalation=True
                            )
                            self.state_repo.increment_re_escalation_count(state.state_id, state.re_escalation_count + 1, now)
                            self.state_repo.append_transition(
                                state_id=state.state_id,
                                action_type="re_escalate",
                                previous_status=state.current_status,
                                new_status=state.current_status,
                                actor_type="system",
                                actor_id="escalation_engine",
                                note=f"Re-escalated issue (Count: {state.re_escalation_count + 1})"
                            )
                        batch_result.re_escalation_sent_count += 1
                        continue

                # Try Reminder next
                rem_result = self.reminder_engine.evaluate(state, policy, now)
                if rem_result.decision == "remind":
                    # Resolve overriding routes
                    channels = self.route_resolver.resolve(state, policy, rem_result.dispatched_channels)
                    
                    # Dispatch
                    self.reminder_dispatcher.dispatch(
                        state=state,
                        policy=policy,
                        dry_run=dry_run
                    )
                    
                    rem_result.dispatched_channels = channels
                    
                    if not dry_run:
                        self.result_mapper.map_reminder_result(
                            state=state,
                            result=rem_result,
                            now=now
                        )
                    
                    batch_result.reminder_sent_count += 1
                    continue

                # If neither triggered, touch last seen and save any computed aging changes
                if not dry_run:
                    self.state_repo.upsert_open_state(state)
                    self.state_repo.touch_last_seen(state.state_id)
                batch_result.skipped_count += 1

                # Track other statuses
                if state.current_status == "acknowledged":
                    batch_result.acked_count += 1
                elif state.current_status == "silenced":
                    batch_result.silenced_count += 1

            except Exception as e:
                logger.error(f"Failed to process escalation state {state.state_id}: {e}")
                batch_result.errors.append({"state_id": state.state_id, "error": str(e)})
                batch_result.fatal_count += 1

        logger.info(f"Escalation runner finished: processed={batch_result.processed_count}, reminders={batch_result.reminder_sent_count}, escalations={batch_result.escalation_sent_count}")
        return batch_result

    def _ingest_normalized_event(self, event: NormalizedEscalationEvent, dry_run: bool) -> None:
        if dry_run:
            return

        domain_state = EscalationState(
            state_id=None,  # let repository generate
            source_event_id=event.source_event_id,
            source_history_id=event.source_history_id,
            source_event_type=event.source_event_type,
            seller_account_id=event.seller_account_id,
            environment_type=event.environment_type,
            sku=event.sku,
            dedupe_key=event.dedupe_key,
            current_status="open",
            current_severity=event.severity,
            current_priority=event.priority,
            source_status_snapshot=event.payload
        )

        self.state_repo.upsert_open_state(domain_state)
