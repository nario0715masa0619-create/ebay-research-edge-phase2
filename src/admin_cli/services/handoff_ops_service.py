import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from src.handoff.bootstrap import bootstrap_handoff_layer
from src.handoff.models import HandoffInput, HandoffResult
from src.repositories.persistent_ranking_decision_repository import PersistentRankingDecisionRepository

logger = logging.getLogger(__name__)

class HandoffOpsService:
    def __init__(self, session: Session):
        self.session = session
        self.service, self.repo = bootstrap_handoff_layer(session)
        self.ranking_repo = PersistentRankingDecisionRepository(session)

    def run_handoff(self, candidate_id: str, seller_account_id: str, environment: str) -> Optional[HandoffResult]:
        ranking_decision = self.ranking_repo.get_by_candidate_seller_env(candidate_id, seller_account_id, environment)
        
        if not ranking_decision:
            logger.error(f"No ranking decision found for {candidate_id}")
            return None
            
        input_data = HandoffInput(
            ranking_decision_id=ranking_decision.ranking_decision_id,
            candidate_id=ranking_decision.candidate_id,
            seller_account_id=ranking_decision.seller_account_id,
            environment=ranking_decision.environment,
            decision_class=ranking_decision.decision_class,
            ranking_score=ranking_decision.ranking_score,
            queue_type=ranking_decision.queue_type,
            execution_blocked=ranking_decision.execution_blocked,
            recheck_required=ranking_decision.recheck_required,
            stale_flag=ranking_decision.stale_flag
        )
        
        existing = self.repo.find_recent_by_candidate(candidate_id, seller_account_id, environment)
        run_count = 0 # Simulated for ops context
        active_count = self.repo.get_seller_active_execution_count(seller_account_id, environment)
        
        result = self.service.process_handoff(
            input_data=input_data,
            existing_handoffs=existing,
            run_handoff_count=run_count,
            seller_active_execution_count=active_count
        )
        
        self.repo.upsert_handoff(result)
        return result

    def get_handoff_by_id(self, handoff_id: str) -> Optional[HandoffResult]:
        return self.repo.get_by_id(handoff_id)
        
    def get_recent_by_candidate(self, candidate_id: str, seller_account_id: str, environment: str) -> List[HandoffResult]:
        return self.repo.find_recent_by_candidate(candidate_id, seller_account_id, environment)
