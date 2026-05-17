import logging
from alembic.config import Config
from alembic import command
from .engine import create_engine_from_config
from .base import Base
from .config import DatabaseConfig
# Import models here to ensure they are registered with Base.metadata
from . import models

logger = logging.getLogger(__name__)

def bootstrap_database(auto_upgrade: bool = DatabaseConfig.ALEMBIC_AUTO_UPGRADE_ON_BOOT):
    engine = create_engine_from_config()
    if auto_upgrade:
        logger.info("Auto-upgrading database schema via Alembic...")
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            logger.warning(f"Alembic upgrade failed: {e}. Falling back to Base.metadata.create_all.")
            with engine.begin() as conn:
                Base.metadata.create_all(conn)
    else:
        # Fallback for MVP
        logger.info("Creating tables via Base.metadata.create_all...")
        with engine.begin() as conn:
            Base.metadata.create_all(conn)
    
    engine.dispose()
    
    logger.info("Database bootstrap completed.")

def get_repository_provider(session_factory, backend: str = "sqlite"):
    # This will be used to inject repositories into pipelines
    from src.repositories.persistent_source_item_repository import PersistentSourceItemRepository
    from src.repositories.persistent_product_candidate_repository import PersistentProductCandidateRepository
    from src.repositories.persistent_candidate_evidence_repository import PersistentCandidateEvidenceRepository
    from src.repositories.persistent_ebay_listing_repository import PersistentEbayListingRepository
    from src.repositories.persistent_monitoring_event_repository import PersistentMonitoringEventRepository
    from src.repositories.persistent_job_run_repository import PersistentJobRunRepository
    from src.repositories.persistent_notification_history_repository import PersistentNotificationHistoryRepository
    
    session = session_factory()
    return {
        "source_item": PersistentSourceItemRepository(session),
        "candidate": PersistentProductCandidateRepository(session),
        "evidence": PersistentCandidateEvidenceRepository(session),
        "listing": PersistentEbayListingRepository(session),
        "event": PersistentMonitoringEventRepository(session),
        "job": PersistentJobRunRepository(session),
        "notification": PersistentNotificationHistoryRepository(session),
        "session": session
    }
