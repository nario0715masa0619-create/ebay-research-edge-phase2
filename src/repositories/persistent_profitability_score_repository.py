import json
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db.models import ProfitabilityScoreModel
from src.profitability.models import ProfitabilityResult, DecisionStatus, ScoringStatus, ProfitabilityComponentBreakdown

class PersistentProfitabilityScoreRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_score(self, result: ProfitabilityResult) -> ProfitabilityScoreModel:
        components_dict = {
            "effective_source_cost": result.components.effective_source_cost,
            "marketplace_fee": result.components.marketplace_fee,
            "payment_cost": result.components.payment_cost,
            "outbound_shipping": result.components.outbound_shipping,
            "packaging_cost": result.components.packaging_cost,
            "handling_cost": result.components.handling_cost,
            "risk_penalty_total": result.components.risk_penalty_total,
            "competition_penalty": result.components.competition_penalty,
            "ambiguity_penalty": result.components.ambiguity_penalty
        }
        
        model = ProfitabilityScoreModel(
            profitability_score_id=result.profitability_score_id,
            candidate_id=result.candidate_id,
            market_evaluation_id=result.market_evaluation_id,
            scoring_status=result.scoring_status.value,
            decision_status=result.decision_status.value,
            review_required=result.review_required,
            expected_sale_price_low=result.expected_sale_price_low,
            expected_sale_price_base=result.expected_sale_price_base,
            expected_sale_price_high=result.expected_sale_price_high,
            expected_net_profit=result.expected_net_profit,
            expected_margin=result.expected_margin,
            expected_roi=result.expected_roi,
            confidence_multiplier=result.confidence_multiplier,
            confidence_adjusted_profit=result.confidence_adjusted_profit,
            profitability_score=result.profitability_score,
            decision_reason=result.decision_reason,
            unsafe_reasons_json=result.unsafe_reasons,
            explanation_lines_json=result.explanation_lines,
            components_json=components_dict,
            created_at=result.created_at,
            updated_at=result.updated_at
        )
        
        merged_model = self.db.merge(model)
        self.db.commit()
        return merged_model
        
    def get_latest_by_candidate_id(self, candidate_id: str) -> Optional[ProfitabilityScoreModel]:
        stmt = select(ProfitabilityScoreModel).where(
            ProfitabilityScoreModel.candidate_id == candidate_id
        ).order_by(ProfitabilityScoreModel.created_at.desc())
        return self.db.execute(stmt).scalars().first()
        
    def get_by_score_id(self, score_id: str) -> Optional[ProfitabilityScoreModel]:
        return self.db.query(ProfitabilityScoreModel).filter_by(profitability_score_id=score_id).first()
        
    def list_recent(self, limit: int = 50) -> List[ProfitabilityScoreModel]:
        stmt = select(ProfitabilityScoreModel).order_by(ProfitabilityScoreModel.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
        
    def list_top_opportunities(self, limit: int = 50) -> List[ProfitabilityScoreModel]:
        stmt = select(ProfitabilityScoreModel).where(
            ProfitabilityScoreModel.decision_status == DecisionStatus.LAUNCH_NOW.value
        ).order_by(ProfitabilityScoreModel.confidence_adjusted_profit.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
