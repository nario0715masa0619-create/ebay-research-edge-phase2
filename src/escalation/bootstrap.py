import logging
from typing import Any
from sqlalchemy.orm import Session
from src.repositories.persistent_escalation_state_repository import (
    PersistentEscalationStateRepository,
    PersistentEscalationPolicyRepository
)
from src.repositories.persistent_escalation_note_repository import PersistentEscalationNoteRepository
from src.repositories.persistent_maintenance_window_repository import PersistentMaintenanceWindowRepository

from src.escalation.policies import DEFAULT_POLICIES
from src.escalation.maintenance_window_service import MaintenanceWindowService
from src.escalation.route_resolver import RouteResolver
from src.escalation.re_escalation_decision_engine import ReEscalationDecisionEngine
from src.escalation.bulk_action_service import BulkActionService
from src.escalation.note_service import NoteService
from src.escalation.timeline_builder import TimelineBuilder
from src.escalation.metrics_service import MetricsService
from src.escalation.policy_resolver import SellerEnvPolicyResolver
from src.escalation.reminder_decision_engine import ReminderDecisionEngine
from src.escalation.escalation_decision_engine import EscalationDecisionEngine
from src.escalation.reminder_dispatcher import ReminderDispatcher
from src.escalation.escalation_dispatcher import EscalationDispatcher
from src.escalation.result_mapper import EscalationResultMapper
from src.escalation.unresolved_selector import UnresolvedEventSelector
from src.escalation.ack_resolve_service import AckResolveService
from src.escalation.runner import EscalationRunner

logger = logging.getLogger(__name__)

class EscalationBootstrap:
    @staticmethod
    def bootstrap(session: Session, notification_dispatcher: Any = None):
        # 1. Instantiate repositories
        state_repo = PersistentEscalationStateRepository(session)
        policy_repo = PersistentEscalationPolicyRepository(session)
        note_repo = PersistentEscalationNoteRepository(session)
        maintenance_repo = PersistentMaintenanceWindowRepository(session)

        # Seed default policies if table is empty
        try:
            enabled_policies = policy_repo.list_enabled()
            if not enabled_policies:
                logger.info("No active escalation policies found. Seeding default system policies...")
                for policy in DEFAULT_POLICIES:
                    policy_repo.upsert(policy)
        except Exception as e:
            logger.warning(f"Failed to seed default escalation policies during bootstrap: {e}")

        # 2. Instantiate engines, resolvers, and services
        policy_resolver = SellerEnvPolicyResolver(policy_repo)
        reminder_engine = ReminderDecisionEngine()
        escalation_engine = EscalationDecisionEngine()
        
        # Dispatchers (Notification Layer Integration)
        from src.notification.bootstrap import NotificationBootstrap
        if notification_dispatcher is None:
            # Fallback bootstrap if not explicitly passed
            notif_components = NotificationBootstrap.bootstrap(session)
            notification_dispatcher = notif_components["dispatcher"]

        reminder_dispatcher = ReminderDispatcher(notification_dispatcher)
        escalation_dispatcher = EscalationDispatcher(notification_dispatcher)
        
        result_mapper = EscalationResultMapper(state_repo)
        unresolved_selector = UnresolvedEventSelector(state_repo)
        
        ack_resolve_service = AckResolveService(state_repo)
        
        # v0.2 Services
        maintenance_service = MaintenanceWindowService(maintenance_repo)
        route_resolver = RouteResolver()
        re_escalation_engine = ReEscalationDecisionEngine()
        bulk_action_service = BulkActionService(state_repo)
        note_service = NoteService(note_repo)
        timeline_builder = TimelineBuilder(state_repo, note_repo)
        metrics_service = MetricsService(session)
        
        runner = EscalationRunner(
            state_repo=state_repo,
            policy_repo=policy_repo,
            policy_resolver=policy_resolver,
            reminder_engine=reminder_engine,
            escalation_engine=escalation_engine,
            reminder_dispatcher=reminder_dispatcher,
            escalation_dispatcher=escalation_dispatcher,
            result_mapper=result_mapper,
            unresolved_selector=unresolved_selector,
            maintenance_service=maintenance_service,
            route_resolver=route_resolver,
            re_escalation_engine=re_escalation_engine
        )

        return {
            "state_repo": state_repo,
            "policy_repo": policy_repo,
            "note_repo": note_repo,
            "maintenance_repo": maintenance_repo,
            "policy_resolver": policy_resolver,
            "reminder_engine": reminder_engine,
            "escalation_engine": escalation_engine,
            "reminder_dispatcher": reminder_dispatcher,
            "escalation_dispatcher": escalation_dispatcher,
            "result_mapper": result_mapper,
            "unresolved_selector": unresolved_selector,
            "ack_resolve_service": ack_resolve_service,
            "maintenance_service": maintenance_service,
            "route_resolver": route_resolver,
            "re_escalation_engine": re_escalation_engine,
            "bulk_action_service": bulk_action_service,
            "note_service": note_service,
            "timeline_builder": timeline_builder,
            "metrics_service": metrics_service,
            "runner": runner
        }
