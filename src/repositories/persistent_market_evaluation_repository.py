import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db.models import MarketEvaluationResultModel, MarketEvaluationEvidenceModel
from src.market_eval.models import MarketEvaluationResult, MarketEvaluationEvidence

class PersistentMarketEvaluationRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_result(self, result: MarketEvaluationResult) -> MarketEvaluationResultModel:
        model = MarketEvaluationResultModel(
            market_evaluation_id=result.market_evaluation_id,
            candidate_id=result.candidate_id,
            evaluation_status=result.evaluation_status,
            comparable_count=result.comparable_count,
            comparable_quality_score=result.comparable_quality_score,
            price_low=result.price_low,
            price_median=result.price_median,
            price_high=result.price_high,
            category_alignment_score=result.category_alignment_score,
            condition_alignment_score=result.condition_alignment_score,
            attribute_alignment_score=result.attribute_alignment_score,
            competition_proxy=result.competition_proxy,
            demand_proxy=result.demand_proxy,
            market_confidence=result.market_confidence,
            unsafe_reasons_json=result.unsafe_reasons,
            review_required=result.review_required,
            evidence_summary=result.evidence_summary,
            search_queries_used_json=result.search_queries_used,
            raw_result_count=result.raw_result_count,
            filtered_result_count=result.filtered_result_count,
            created_at=result.created_at,
            updated_at=result.updated_at
        )
        # Using merge allows insert or update
        merged_model = self.db.merge(model)
        self.db.commit()
        return merged_model

    def save_evidence(self, evidence: MarketEvaluationEvidence) -> MarketEvaluationEvidenceModel:
        model = MarketEvaluationEvidenceModel(
            evidence_id=evidence.evidence_id,
            candidate_id=evidence.candidate_id,
            search_request_payload_json=evidence.search_request_payload,
            provider_name=evidence.provider_name,
            comparable_listing_ids_json=evidence.comparable_listing_ids,
            excluded_listing_ids_json=evidence.excluded_listing_ids,
            unsafe_reasons_json=evidence.unsafe_reasons,
            evidence_lines_json=evidence.evidence_lines,
            raw_response_reference=evidence.raw_response_reference,
            created_at=evidence.created_at
        )
        merged_model = self.db.merge(model)
        self.db.commit()
        return merged_model
        
    def get_result_by_candidate_id(self, candidate_id: str) -> Optional[MarketEvaluationResultModel]:
        stmt = select(MarketEvaluationResultModel).where(MarketEvaluationResultModel.candidate_id == candidate_id).order_by(MarketEvaluationResultModel.created_at.desc())
        return self.db.execute(stmt).scalars().first()
