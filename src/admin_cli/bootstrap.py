from typing import Any, Dict
from src.db.session import SessionManager
from src.auth.token_service import EbayTokenService
from src.auth.config import AuthConfig
from src.auth.credentials import EbayOAuthCredentialProvider
from src.auth.token_cache import InMemoryTokenCache
from src.repositories.persistent_product_candidate_repository import PersistentProductCandidateRepository
from src.repositories.persistent_ebay_listing_repository import PersistentEbayListingRepository
from src.repositories.persistent_job_run_repository import PersistentJobRunRepository
from src.repositories.persistent_candidate_evidence_repository import PersistentCandidateEvidenceRepository
from src.orchestrator.bootstrap import OrchestratorBootstrap
from src.listing_sync.gateway import ListingSyncRecoveryGateway
from src.notification.bootstrap import NotificationBootstrap
from src.repositories.persistent_monitoring_event_repository import PersistentMonitoringEventRepository
from src.repositories.persistent_notification_history_repository import PersistentNotificationHistoryRepository
from src.seller_env.bootstrap import SellerEnvironmentBootstrap
from src.repositories.persistent_seller_profile_repository import PersistentSellerProfileRepository
from src.repositories.persistent_environment_profile_repository import PersistentEnvironmentProfileRepository
from src.repositories.persistent_seller_environment_binding_repository import PersistentSellerEnvironmentBindingRepository
from src.repositories.persistent_seller_policy_snapshot_repository import PersistentSellerPolicySnapshotRepository
from src.repositories.persistent_seller_location_snapshot_repository import PersistentSellerLocationSnapshotRepository
from src.repositories.persistent_escalation_state_repository import PersistentEscalationStateRepository, PersistentEscalationPolicyRepository
from .services.job_ops_service import JobOpsService
from .services.scheduler_ops_service import SchedulerOpsService
from .services.candidate_ops_service import CandidateOpsService
from .services.escalation_ops_service import EscalationOpsService
from .services.listing_ops_service import ListingOpsService
from .services.review_ops_service import ReviewOpsService
from .services.event_ops_service import EventOpsService
from .services.jobrun_ops_service import JobRunOpsService
from .services.evidence_ops_service import EvidenceOpsService
from .services.config_validation_service import ConfigValidationService
from .services.doctor_service import DoctorService
from .services.seller_ops_service import SellerOpsService
from .services.seller_doctor_service import SellerDoctorService
from .services.seller_snapshot_ops_service import SellerSnapshotOpsService
from .services.notification_ops_service import NotificationOpsService
from .services.notification_ops_service import NotificationOpsService
from .services.notification_history_query_service import NotificationHistoryQueryService
from .services.notification_resend_service import NotificationResendService
from .services.notification_test_service import NotificationTestService
from .services.notification_rule_inspect_service import NotificationRuleInspectService
from .services.notification_channel_inspect_service import NotificationChannelInspectService
from .services.notification_stats_service import NotificationStatsService

class AdminCliAppContainer:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class AdminCliBootstrap:
    @staticmethod
    def bootstrap() -> AdminCliAppContainer:
        # 1. DB & Repos
        session_manager = SessionManager()
        session = session_manager.get_session() # For v0.1 we might need to handle session lifecycle better
        
        cand_repo = PersistentProductCandidateRepository(session)
        listing_repo = PersistentEbayListingRepository(session)
        job_repo = PersistentJobRunRepository(session)
        evidence_repo = PersistentCandidateEvidenceRepository(session)
        notification_repo = PersistentNotificationHistoryRepository(session)
        escalation_state_repo = PersistentEscalationStateRepository(session)
        escalation_policy_repo = PersistentEscalationPolicyRepository(session)
        
        # 2. Seller & Environment
        seller_env = SellerEnvironmentBootstrap.bootstrap(session)
        seller_repo = seller_env["seller_repo"]
        env_repo = seller_env["env_repo"]
        binding_repo = seller_env["binding_repo"]
        policy_repo = seller_env["policy_repo"]
        location_repo = seller_env["location_repo"]
        seller_resolver = seller_env["resolver"]
        seller_guard = seller_env["guard"]
        seller_context_manager = seller_env["context_manager"]
        
        # 2. Notification
        notification_dispatcher = NotificationBootstrap.bootstrap(history_repo=notification_repo, seller_resolver=seller_resolver)
        
        # 3. Auth
        from src.auth.bootstrap import bootstrap_auth_layer
        auth_config = AuthConfig()
        auth_components = bootstrap_auth_layer(config=auth_config, seller_resolver=seller_resolver)
        token_service = auth_components["token_service"]
        api_client = auth_components["api_client"]
        
        # 3. Gateways & Pipelines (simplified for CLI)
        # In a real app, we'd use a more robust registry or DI container
        sync_gateway = ListingSyncRecoveryGateway(cand_repo, evidence_repo, job_repo, listing_repo, api_client=api_client)
        
        # 4. Orchestrator
        # We need a full bootstrap of orchestrator here
        # For simplicity, we'll pass minimal objects or use the real OrchestratorBootstrap
        pipelines = {
            "research": None, # Fill if needed
            "readiness": None,
            "monitoring": None
        }
        gateways = {
            "listing_execution": None,
            "listing_sync": sync_gateway
        }
        repositories = {
            "job_run": job_repo
        }
        orchestrator = OrchestratorBootstrap.bootstrap(repositories, pipelines, gateways, notification_dispatcher=notification_dispatcher)
        
        # 5. Services
        job_service = JobOpsService(orchestrator)
        scheduler_service = SchedulerOpsService(orchestrator)
        candidate_service = CandidateOpsService(cand_repo)
        listing_service = ListingOpsService(listing_repo, sync_gateway)
        review_service = ReviewOpsService(cand_repo)
        event_service = EventOpsService(PersistentMonitoringEventRepository(session))
        jobrun_service = JobRunOpsService(job_repo)
        evidence_service = EvidenceOpsService(evidence_repo)
        config_service = ConfigValidationService()
        doctor_service = DoctorService(session_manager, token_service, orchestrator, notification_dispatcher=notification_dispatcher)
        
        seller_ops = SellerOpsService(seller_repo, env_repo, binding_repo)
        seller_doctor = SellerDoctorService(seller_resolver, seller_guard)
        seller_snapshot_ops = SellerSnapshotOpsService(policy_repo, location_repo)
        
        # 6. Notification Admin Services
        ntf_query = NotificationHistoryQueryService(notification_repo)
        ntf_resend = NotificationResendService(notification_repo, notification_dispatcher)
        ntf_test = NotificationTestService(notification_dispatcher)
        ntf_rule = NotificationRuleInspectService(notification_dispatcher.rule_engine)
        ntf_channel = NotificationChannelInspectService(notification_dispatcher.channel_registry)
        ntf_stats = NotificationStatsService(notification_repo)
        
        notification_service = NotificationOpsService(
            ntf_query, ntf_resend, ntf_test, ntf_rule, ntf_channel, ntf_stats
        )
        
        # Bootstrapping full escalation layer to get v0.2 components
        from src.escalation.bootstrap import EscalationBootstrap
        esc_components = EscalationBootstrap.bootstrap(session, notification_dispatcher)
        escalation_service = EscalationOpsService(
            state_repo=esc_components["state_repo"],
            policy_repo=esc_components["policy_repo"],
            bulk_action_service=esc_components.get("bulk_action_service"),
            note_service=esc_components.get("note_service"),
            timeline_builder=esc_components.get("timeline_builder"),
            metrics_service=esc_components.get("metrics_service"),
            maintenance_service=esc_components.get("maintenance_service")
        )
        
        return AdminCliAppContainer(
            job_service=job_service,
            scheduler_service=scheduler_service,
            candidate_service=candidate_service,
            listing_service=listing_service,
            review_service=review_service,
            event_service=event_service,
            jobrun_service=jobrun_service,
            evidence_service=evidence_service,
            config_service=config_service,
            doctor_service=doctor_service,
            notification_service=notification_service,
            escalation_service=escalation_service,
            seller_ops=seller_ops,
            seller_doctor=seller_doctor,
            seller_snapshot_ops=seller_snapshot_ops,
            seller_context_manager=seller_context_manager
        )
