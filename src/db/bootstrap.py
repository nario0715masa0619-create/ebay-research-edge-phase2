import logging
from alembic.config import Config
from alembic import command
from .engine import create_engine_from_config
from .base import Base
from .config import DatabaseConfig

logger = logging.getLogger(__name__)

def bootstrap_database(auto_upgrade: bool = DatabaseConfig.ALEMBIC_AUTO_UPGRADE_ON_BOOT):
    engine = create_engine_from_config()
    
    if auto_upgrade:
        logger.info("Auto-upgrading database schema via Alembic...")
        try:
            # In a real setup, we would point to alembic.ini
            # Since paths might be tricky, we can also use create_all as a baseline
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            logger.warning(f"Alembic upgrade failed: {e}. Falling back to Base.metadata.create_all.")
            Base.metadata.create_all(engine)
    else:
        # Fallback for MVP
        logger.info("Creating tables via Base.metadata.create_all...")
        Base.metadata.create_all(engine)
    
    logger.info("Database bootstrap completed.")

def get_repository_provider(session_factory, backend: str = "sqlite"):
    # This will be used to inject repositories into pipelines
    from src.repositories.persistent_source_item_repository import PersistentSourceItemRepository
    from src.repositories.persistent_product_candidate_repository import PersistentProductCandidateRepository
    from src.repositories.persistent_candidate_evidence_repository import PersistentCandidateEvidenceRepository
    from src.repositories.persistent_ebay_listing_repository import PersistentEbayListingRepository
    from src.repositories.persistent_monitoring_event_repository import PersistentMonitoringEventRepository
    from src.repositories.persistent_job_run_repository import PersistentJobRunRepository
    
    session = session_factory()
    return {
        "source_item": PersistentSourceItemRepository(session),
        "candidate": PersistentProductCandidateRepository(session),
        "evidence": PersistentCandidateEvidenceRepository(session),
        "listing": PersistentEbayListingRepository(session),
        "event": PersistentMonitoringEventRepository(session),
        "job": PersistentJobRunRepository(session),
        "session": session
    }
