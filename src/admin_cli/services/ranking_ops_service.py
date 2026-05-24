import json
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.models import CanonicalProductCandidateModel, MarketEvaluationResultModel, ProfitabilityScoreModel
from src.ranking.bootstrap import RankingBootstrap
from src.ranking.models import RankingInput

class RankingOpsService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = RankingBootstrap.get_settings()
        self.service = RankingBootstrap.get_scoring_service()
        self.repo = RankingBootstrap.get_repository()
        # Ensure repository uses the same session
        self.repo.db = self.db
        
    def run_ranking(self, candidate_id: str):
        candidate = self.db.query(CanonicalProductCandidateModel).filter_by(candidate_id=candidate_id).first()
        if not candidate:
            print(f"Error: Candidate '{candidate_id}' not found.")
            return None
            
        market_eval = self.db.query(MarketEvaluationResultModel).filter_by(candidate_id=candidate_id).order_by(MarketEvaluationResultModel.created_at.desc()).first()
        profit_score = self.db.query(ProfitabilityScoreModel).filter_by(candidate_id=candidate_id).order_by(ProfitabilityScoreModel.created_at.desc()).first()
        
        # Build Ranking Input
        input_data = RankingInput(
            candidate_id=candidate.candidate_id,
            seller_account_id="admin_cli", 
            environment="cli",
            review_required=candidate.review_required,
            ambiguity_flags=candidate.ambiguity_flags_json if hasattr(candidate, 'ambiguity_flags_json') else [],
            
            market_evaluation_id=market_eval.market_evaluation_id if market_eval else None,
            market_evaluation_status=market_eval.evaluation_status if market_eval else "not_found",
            market_confidence=market_eval.market_confidence if market_eval else 0.0,
            comparable_count=market_eval.comparable_count if market_eval else 0,
            competition_proxy=market_eval.competition_proxy if market_eval else "high",
            demand_proxy=market_eval.demand_proxy if market_eval else "low",
            market_unsafe_reasons=market_eval.unsafe_reasons_json if market_eval else [],
            market_created_at=market_eval.created_at if market_eval else None,
            
            profitability_score_id=profit_score.profitability_score_id if profit_score else None,
            profitability_scoring_status=profit_score.scoring_status if profit_score else "not_found",
            expected_net_profit=profit_score.expected_net_profit if profit_score else 0.0,
            expected_margin=profit_score.expected_margin if profit_score else 0.0,
            expected_roi=profit_score.expected_roi if profit_score else 0.0,
            confidence_adjusted_profit=profit_score.confidence_adjusted_profit if profit_score else 0.0,
            profitability_score=profit_score.profitability_score if profit_score else 0.0,
            profitability_decision_status=profit_score.decision_status if profit_score else "reject",
            profitability_unsafe_reasons=profit_score.unsafe_reasons_json if profit_score else [],
            profitability_created_at=profit_score.created_at if profit_score else None
        )
        
        print(f"Running Listing Decision & Ranking for Candidate: {candidate_id}")
        result = self.service.evaluate(input_data)
        
        print("\n--- Result ---")
        print(f"Decision ID: {result.ranking_decision_id}")
        print(f"Decision: {result.decision_class.value.upper()}")
        print(f"Queue Type: {result.queue_type.value}")
        if result.launch_priority_bucket:
            print(f"Launch Bucket: {result.launch_priority_bucket.value}")
        if result.review_priority_bucket:
            print(f"Review Bucket: {result.review_priority_bucket.value}")
        print(f"Ranking Score: {result.ranking_score:.2f}")
        
        print("\n--- Blockers & Status ---")
        print(f"Execution Blocked: {result.execution_blocked}")
        print(f"Recheck Required (Stale): {result.recheck_required}")
        for b in result.block_reasons:
            print(f" [BLOCK] {b}")
            
        print("\n--- Explanation ---")
        for line in result.explanation_lines:
            print(f"- {line}")
            
        print("\nSaving to DB...")
        self.repo.save_decision(result)
        print("Done.")
        
        return result
