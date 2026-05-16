from typing import Any, Dict
from src.db.session import SessionManager
from src.auth.token_service import EbayTokenService
from src.repositories.persistent_product_candidate_repository import PersistentProductCandidateRepository
from src.repositories.persistent_ebay_listing_repository import PersistentEbayListingRepository
from src.repositories.persistent_job_run_repository import PersistentJobRunRepository
from src.repositories.persistent_candidate_evidence_repository import PersistentCandidateEvidenceRepository
from src.orchestrator.bootstrap import OrchestratorBootstrap
from src.listing_sync.gateway import ListingSyncRecoveryGateway

from .services.job_ops_service import JobOpsService
from .services.scheduler_ops_service import SchedulerOpsService
from .services.candidate_ops_service import CandidateOpsService
from .services.listing_ops_service import ListingOpsService
from .services.review_ops_service import ReviewOpsService
from .services.event_ops_service import EventOpsService
from .services.jobrun_ops_service import JobRunOpsService
from .services.evidence_ops_service import EvidenceOpsService
from .services.config_validation_service import ConfigValidationService
from .services.doctor_service import DoctorService

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
        
        # 2. Auth
        token_service = EbayTokenService() # Assumes config is set via env
        
        # 3. Gateways & Pipelines (simplified for CLI)
        # In a real app, we'd use a more robust registry or DI container
        api_client = None # Will be created by gateways if needed
        sync_gateway = ListingSyncRecoveryGateway(cand_repo, evidence_repo, job_repo, listing_repo)
        
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
        orchestrator = OrchestratorBootstrap.bootstrap(repositories, pipelines, gateways)
        
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
        doctor_service = DoctorService(session_manager, token_service, orchestrator)
        
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
            doctor_service=doctor_service
        )
