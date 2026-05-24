from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db.models import ListingDecisionModel
from src.ranking.models import ListingDecisionResult, DecisionClass, QueueType

class PersistentRankingDecisionRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_decision(self, result: ListingDecisionResult) -> ListingDecisionModel:
        # Check if exists for this candidate
        stmt = select(ListingDecisionModel).where(ListingDecisionModel.candidate_id == result.candidate_id)
        existing = self.db.execute(stmt).scalars().first()
        
        components_dict = {
            "profitability_component": result.ranking_components.profitability_component,
            "margin_component": result.ranking_components.margin_component,
            "roi_component": result.ranking_components.roi_component,
            "market_confidence_component": result.ranking_components.market_confidence_component,
            "demand_component": result.ranking_components.demand_component,
            "competition_component": result.ranking_components.competition_component,
            "review_penalty": result.ranking_components.review_penalty,
            "unsafe_penalty": result.ranking_components.unsafe_penalty,
            "staleness_penalty": result.ranking_components.staleness_penalty,
            "capacity_penalty": result.ranking_components.capacity_penalty,
        }
        
        if existing:
            # Upsert latest decision
            existing.ranking_decision_id = result.ranking_decision_id
            existing.ranking_score = result.ranking_score
            existing.decision_class = result.decision_class.value
            existing.decision_reason = result.decision_reason
            existing.queue_type = result.queue_type.value
            existing.queue_rank = result.queue_rank
            existing.launch_priority_bucket = result.launch_priority_bucket.value if result.launch_priority_bucket else None
            existing.review_priority_bucket = result.review_priority_bucket.value if result.review_priority_bucket else None
            existing.execution_blocked = result.execution_blocked
            existing.block_reasons_json = result.block_reasons
            existing.recheck_required = result.recheck_required
            existing.stale_flag = result.stale_flag
            existing.explanation_lines_json = result.explanation_lines
            existing.ranking_components_json = components_dict
            existing.updated_at = result.updated_at
            
            self.db.commit()
            return existing
        else:
            model = ListingDecisionModel(
                ranking_decision_id=result.ranking_decision_id,
                candidate_id=result.candidate_id,
                seller_account_id=result.seller_account_id,
                environment=result.environment,
                ranking_score=result.ranking_score,
                decision_class=result.decision_class.value,
                decision_reason=result.decision_reason,
                queue_type=result.queue_type.value,
                queue_rank=result.queue_rank,
                launch_priority_bucket=result.launch_priority_bucket.value if result.launch_priority_bucket else None,
                review_priority_bucket=result.review_priority_bucket.value if result.review_priority_bucket else None,
                execution_blocked=result.execution_blocked,
                block_reasons_json=result.block_reasons,
                recheck_required=result.recheck_required,
                stale_flag=result.stale_flag,
                explanation_lines_json=result.explanation_lines,
                ranking_components_json=components_dict,
                created_at=result.created_at,
                updated_at=result.updated_at
            )
            self.db.add(model)
            self.db.commit()
            return model
            
    def get_by_candidate_id(self, candidate_id: str) -> Optional[ListingDecisionModel]:
        stmt = select(ListingDecisionModel).where(ListingDecisionModel.candidate_id == candidate_id)
        return self.db.execute(stmt).scalars().first()
        
    def list_by_queue_type(self, queue_type: QueueType, seller_account_id: Optional[str] = None, limit: int = 50) -> List[ListingDecisionModel]:
        stmt = select(ListingDecisionModel).where(ListingDecisionModel.queue_type == queue_type.value)
        if seller_account_id:
            stmt = stmt.where(ListingDecisionModel.seller_account_id == seller_account_id)
            
        stmt = stmt.order_by(ListingDecisionModel.queue_rank.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
