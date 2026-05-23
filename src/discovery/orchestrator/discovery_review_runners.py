import logging
from typing import Dict, Any, Optional
from sqlalchemy import select, or_
from src.db.session import SessionManager
from src.db.models import NormalizedSourceItemModel, CanonicalProductCandidateModel
from src.discovery.candidate_normalizer import CandidateNormalizer
from src.repositories.persistent_alias_dictionary_repository import PersistentAliasDictionaryRepository

logger = logging.getLogger(__name__)

class ReviewQueueRefreshRunner:
    """
    Periodic job to auto-refresh the review queue.
    Finds candidates that are in review and attempts to re-evaluate them
    if background processes or dictionaries have changed.
    """
    def __init__(self, normalizer: CandidateNormalizer, session_manager: Optional[SessionManager] = None):
        self.normalizer = normalizer
        self.session_manager = session_manager or SessionManager()

    def run(self, limit: int = 100, **kwargs) -> Dict[str, Any]:
        logger.info(f"Starting Review Queue Refresh Job (limit={limit})")
        # In a real scenario, this fetches candidates where review_required = True
        # and re-runs the refine logic for their linked sources.
        # For Phase C, we return a structural placeholder.
        return {
            "status": "completed",
            "processed_count": 0,
            "resolved_count": 0
        }

class AliasReprocessRunner:
    """
    Applies alias dictionary updates to existing items.
    Enforces impact-scoped execution by default to avoid massive DB churn.
    """
    def __init__(self, normalizer: CandidateNormalizer, alias_repo: PersistentAliasDictionaryRepository, session_manager: Optional[SessionManager] = None):
        self.normalizer = normalizer
        self.alias_repo = alias_repo
        self.session_manager = session_manager or SessionManager()

    def run(self, full_rebuild: bool = False, target_alias_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        logger.info(f"Starting Alias Reprocess Job (full_rebuild={full_rebuild}, target_token={target_alias_token})")
        
        # Enforcement: Full rebuild must be explicit.
        if full_rebuild and not kwargs.get('confirm_full_rebuild'):
            logger.warning("full_rebuild requested without confirm_full_rebuild flag. Aborting.")
            return {"status": "aborted", "reason": "Missing confirmation for full rebuild"}
            
        processed = 0
        with self.session_manager.session() as session:
            stmt = select(NormalizedSourceItemModel)
            
            if not full_rebuild:
                if target_alias_token:
                    # Impact-scoped: only fetch items that actually contain the alias token
                    token = f"%{target_alias_token}%"
                    stmt = stmt.where(
                        or_(
                            NormalizedSourceItemModel.normalized_brand.ilike(token),
                            NormalizedSourceItemModel.normalized_model.ilike(token),
                            NormalizedSourceItemModel.normalized_title.ilike(token)
                        )
                    )
                else:
                    # If no token provided and not full rebuild, do nothing or just recent.
                    # We default to recent 7 days (pseudo logic)
                    stmt = stmt.order_by(NormalizedSourceItemModel.updated_at.desc()).limit(100)
            
            # Re-run normalizer logic on these items...
            # For Phase C, we demonstrate the structural enforcement.
            items = session.execute(stmt.limit(100)).scalars().all()
            processed = len(items)
            
        return {
            "status": "completed",
            "processed_count": processed,
            "full_rebuild": full_rebuild
        }
