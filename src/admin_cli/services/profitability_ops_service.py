import json
from sqlalchemy.orm import Session

from src.db.models import CanonicalProductCandidateModel, MarketEvaluationResultModel
from src.profitability.bootstrap import ProfitabilityBootstrap
from src.profitability.models import ProfitabilityInput, SellerPolicyContext

class ProfitabilityOpsService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.settings = ProfitabilityBootstrap.get_settings()
        self.service = ProfitabilityBootstrap.get_scoring_service()
        self.repo = ProfitabilityBootstrap.get_repository()
        # Ensure repository uses the same session
        self.repo.db = self.db
        
    def run_scoring(self, candidate_id: str):
        candidate = self.db.query(CanonicalProductCandidateModel).filter_by(candidate_id=candidate_id).first()
        if not candidate:
            print(f"Error: Candidate '{candidate_id}' not found.")
            return None
            
        market_eval = self.db.query(MarketEvaluationResultModel).filter_by(candidate_id=candidate_id).order_by(MarketEvaluationResultModel.created_at.desc()).first()
        
        # Build Profitability Input from candidate and market evaluation
        input_data = ProfitabilityInput(
            candidate_id=candidate.candidate_id,
            seller_account_id="admin_cli", # Mock or lookup
            environment="cli",
            source_price=5000.0, # This should ideally come from a SourceItem lookup, using mock for CLI structure demonstration
            source_shipping_cost=0.0,
            review_required=candidate.review_required,
            ambiguity_flags=candidate.ambiguity_flags_json if hasattr(candidate, 'ambiguity_flags_json') else [],
            market_evaluation_id=market_eval.market_evaluation_id if market_eval else None,
            expected_sale_price_low=market_eval.price_low if market_eval else None,
            expected_sale_price_base=market_eval.price_median if market_eval else None,
            expected_sale_price_high=market_eval.price_high if market_eval else None,
            market_confidence=market_eval.market_confidence if market_eval else None,
            comparable_count=market_eval.comparable_count if market_eval else 0,
            competition_proxy=market_eval.competition_proxy if market_eval else None,
            unsafe_reasons=market_eval.unsafe_reasons_json if market_eval else []
        )
        
        print(f"Running Profitability Scoring for Candidate: {candidate_id}")
        result = self.service.evaluate_profitability(input_data)
        
        print("\n--- Result ---")
        print(f"Score ID: {result.profitability_score_id}")
        print(f"Decision: {result.decision_status.value.upper()}")
        print(f"Raw Net Profit: {result.expected_net_profit:.2f}")
        print(f"Margin: {result.expected_margin:.2%} | ROI: {result.expected_roi:.2%}")
        print(f"Confidence Multiplier: {result.confidence_multiplier:.2f}")
        print(f"Adjusted Profit: {result.confidence_adjusted_profit:.2f}")
        print(f"Overall Score: {result.profitability_score:.2f}/100")
        
        print("\n--- Explanation ---")
        for line in result.explanation_lines:
            print(f"- {line}")
            
        print("\nSaving to DB...")
        self.repo.save_score(result)
        print("Done.")
        
        return result
